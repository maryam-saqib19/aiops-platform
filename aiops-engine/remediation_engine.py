"""
Autonomous Remediation Engine

Takes the output of the AnomalyDetector and executes the appropriate
Kubernetes action to resolve the issue automatically.

Design principles:
  1. Least disruptive action first — scale before restart, restart before rollback
  2. Every action is logged with full context for audit purposes
  3. Cooldown period prevents remediation loops
  4. Humans can always override by setting REMEDIATION_ENABLED=false
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

import sys
sys.path.insert(0, '.')
from config.config import config


class RemediationEngine:

    def __init__(self):
        # Load Kubernetes credentials
        # Tries in-cluster first (when running inside a pod),
        # falls back to your local kubeconfig for development
        try:
            k8s_config.load_incluster_config()
            print("Kubernetes: using in-cluster config")
        except k8s_config.ConfigException:
            k8s_config.load_kube_config()
            print("Kubernetes: using local kubeconfig")

        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()

        # Audit trail — every action recorded here
        self.audit_log: List[Dict] = []

        # Cooldown tracking — prevents acting too frequently
        self.last_remediation_time: Optional[float] = None
        self.cooldown_seconds: int = 300  # 5 minutes between actions

    def is_in_cooldown(self) -> bool:
        if self.last_remediation_time is None:
            return False
        elapsed = time.time() - self.last_remediation_time
        remaining = self.cooldown_seconds - elapsed
        if remaining > 0:
            print(f"Cooldown active — {int(remaining)}s remaining before next action")
            return True
        return False

    def determine_action(self, detection_result: Dict) -> str:
        """
        Rule-based action selection using the contributing features
        identified by the AnomalyDetector's z-score analysis.

        Ordered by impact — we prefer the least disruptive action
        that is likely to resolve the specific problem detected.
        """
        features = detection_result.get('features', {})
        contributors = detection_result.get('contributing_features', [])

        pod_restarts = features.get('pod_restarts', 0)
        cpu_usage = features.get('cpu_usage', 0)
        memory_bytes = features.get('memory_bytes', 0)
        error_rate = features.get('error_rate', 0)

        # Decision tree — most severe/specific condition wins
        if pod_restarts > 3:
            return 'rolling_restart'
        elif cpu_usage > 0.80:
            return 'scale_out'
        elif memory_bytes > 400_000_000:  # 400MB
            return 'rolling_restart'
        elif error_rate > 0.10:
            return 'alert_only'
        elif contributors:
            return 'alert_only'
        else:
            return 'alert_only'

    def remediate(self,
                  detection_result: Dict,
                  deployment_name: str = 'aiops-app',
                  namespace: str = None) -> Dict:
        """
        Main entry point — called when AnomalyDetector confirms an anomaly.
        """
        namespace = namespace or config.namespace

        # Check if remediation is globally enabled
        import os
        if os.getenv('REMEDIATION_ENABLED', 'true').lower() != 'true':
            print("Remediation disabled via REMEDIATION_ENABLED=false")
            return {'action': 'disabled', 'result': 'skipped'}

        # Check cooldown
        if self.is_in_cooldown():
            return {'action': 'cooldown', 'result': 'skipped'}

        # Determine what action to take
        action = self.determine_action(detection_result)

        print(f"\nRemediation triggered:")
        print(f"  Action:     {action}")
        print(f"  Namespace:  {namespace}")
        print(f"  Deployment: {deployment_name}")
        print(f"  Score:      {detection_result.get('score', 'N/A'):.3f}")
        print(f"  Cause:      {detection_result.get('contributing_features', [])}")

        # Execute the chosen action
        if action == 'scale_out':
            result = self._scale_out(namespace, deployment_name)
        elif action == 'rolling_restart':
            result = self._rolling_restart(namespace, deployment_name)
        elif action == 'alert_only':
            result = self._alert_only(detection_result)
        else:
            result = 'unknown action'

        # Record in audit log
        audit_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'namespace': namespace,
            'deployment': deployment_name,
            'anomaly_score': detection_result.get('score'),
            'contributing_features': detection_result.get('contributing_features'),
            'result': result,
            'actor': 'aiops-autonomous-engine'
        }
        self.audit_log.append(audit_entry)

        # Start cooldown after a real action
        if action not in ('alert_only', 'disabled', 'cooldown'):
            self.last_remediation_time = time.time()

        print(f"  Result:     {result}")
        return audit_entry

    def _scale_out(self, namespace: str, deployment_name: str) -> str:
        """Add 2 replicas (up to a maximum of 10)."""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=namespace
            )
            current = deployment.spec.replicas or 1
            new_count = min(current + 2, 10)

            deployment.spec.replicas = new_count
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            return f"Scaled {deployment_name} from {current} to {new_count} replicas"
        except ApiException as e:
            return f"Scale-out failed: {e.reason}"

    def _rolling_restart(self, namespace: str, deployment_name: str) -> str:
        """
        Trigger a rolling restart by patching the pod template annotation.
        Kubernetes sees the annotation change and replaces pods one by one,
        maintaining availability throughout the restart.
        """
        try:
            patch = {
                'spec': {
                    'template': {
                        'metadata': {
                            'annotations': {
                                'kubectl.kubernetes.io/restartedAt':
                                    datetime.now(timezone.utc).isoformat(),
                                'aiops.io/restart-reason': 'autonomous-remediation'
                            }
                        }
                    }
                }
            }
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=patch
            )
            return f"Rolling restart triggered for {deployment_name}"
        except ApiException as e:
            return f"Rolling restart failed: {e.reason}"

    def _alert_only(self, detection_result: Dict) -> str:
        """
        No automated action — generate an alert for human review.
        Used when the cause is ambiguous or the error rate is high
        (suggesting an upstream dependency problem that restarting
        our pods will not fix).
        """
        score = detection_result.get('score', 0)
        contributors = detection_result.get('contributing_features', [])
        msg = (f"Anomaly alert raised — score={score:.3f}, "
               f"contributors={contributors}. Human review required.")
        print(f"  {msg}")
        return msg

    def get_audit_log(self) -> List[Dict]:
        """Returns the full remediation history for compliance queries."""
        return self.audit_log


if __name__ == '__main__':
    # Quick standalone test — verifies Kubernetes API connectivity
    # and runs through the decision logic with a synthetic anomaly
    engine = RemediationEngine()

    print("\n--- Test 1: CPU anomaly (should trigger scale_out) ---")
    cpu_anomaly = {
        'score': -0.42,
        'is_anomaly': True,
        'contributing_features': ['cpu_usage'],
        'features': {
            'cpu_usage': 0.92,
            'memory_bytes': 50_000_000,
            'error_rate': 0.001,
            'latency_p99': 0.10,
            'pod_restarts': 0.0
        }
    }
    result = engine.remediate(cpu_anomaly)
    print(f"Audit entry: {result}")

    print("\n--- Test 2: Error rate anomaly (should trigger alert_only) ---")
    error_anomaly = {
        'score': -0.45,
        'is_anomaly': True,
        'contributing_features': ['error_rate'],
        'features': {
            'cpu_usage': 0.30,
            'memory_bytes': 50_000_000,
            'error_rate': 0.25,
            'latency_p99': 0.10,
            'pod_restarts': 0.0
        }
    }
    result = engine.remediate(error_anomaly)
    print(f"Audit entry: {result}")

    print("\n--- Full audit log ---")
    for entry in engine.get_audit_log():
        print(entry)

