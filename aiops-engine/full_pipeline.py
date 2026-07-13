"""
Complete AIOps Pipeline — one full detection and remediation cycle.

Proves the entire chain:
  Prometheus -> MetricsCollector -> IsolationForest -> RemediationEngine
"""
from metrics_collector import MetricsCollector
from anomaly_detector import AnomalyDetector
from remediation_engine import RemediationEngine

print("=" * 50)
print("AIOps Platform — Full Pipeline Test")
print("=" * 50)

# Step 1 — collect real metrics
print("\n[1] Collecting live metrics from Prometheus...")
collector = MetricsCollector()
features = collector.collect()

# Step 2 — train model and predict
print("\n[2] Running anomaly detection...")
detector = AnomalyDetector()
detector.train()
result = detector.predict(features)
print(f"    Score: {result['score']:.3f}")
print(f"    Is anomaly: {result['is_anomaly']}")
print(f"    Contributors: {result['contributing_features']}")

# Step 3 — remediate if needed
print("\n[3] Evaluating remediation...")
remediator = RemediationEngine()
if result['is_anomaly']:
    audit = remediator.remediate(result)
    print(f"    Action taken: {audit['action']}")
    print(f"    Result: {audit['result']}")
else:
    print("    No anomaly detected — no action needed")

print("\n[4] Audit log:")
for entry in remediator.get_audit_log():
    print(f"    {entry.get('timestamp')} | {entry.get('action')} | {entry.get('result')}")

print("\n" + "=" * 50)
print("Pipeline complete")
print("=" * 50)

