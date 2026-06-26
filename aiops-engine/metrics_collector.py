"""
Collects the five-dimensional feature vector from Prometheus.
Metric names verified against actual /api/v1/label/__name__/values output.
prometheus-flask-exporter prefixes everything with flask_ and uses
singular 'request', not 'requests'.
"""
import numpy as np
from prometheus_api_client import PrometheusConnect
from typing import Optional
import sys
sys.path.insert(0, '.')
from config.config import config


class MetricsCollector:
    def __init__(self):
        self.prom = PrometheusConnect(url=config.prometheus_url, disable_ssl=True)
        self.feature_names = [
            'cpu_usage', 'memory_bytes', 'error_rate',
            'latency_p99', 'pod_restarts'
        ]

    def _query(self, promql: str) -> float:
        try:
            result = self.prom.custom_query(query=promql)
            if result and len(result) > 0:
                return float(result[0]['value'][1])
            return 0.0
        except Exception as e:
            print(f"Query failed: {promql[:60]}... — {e}")
            return 0.0

    def collect(self) -> Optional[np.ndarray]:
        ns = config.namespace

        queries = {
            'cpu_usage': f'avg(rate(container_cpu_usage_seconds_total{{namespace="{ns}"}}[5m])) or vector(0)',
            'memory_bytes': f'avg(container_memory_working_set_bytes{{namespace="{ns}"}}) or vector(0)',
            # FIXED: flask_http_request_total, not http_requests_total
            'error_rate': f'sum(rate(flask_http_request_total{{namespace="{ns}",status=~"5.."}}[5m])) or vector(0)',
            # FIXED: flask_http_request_duration_seconds_bucket, not http_request_duration_seconds_bucket
            'latency_p99': f'histogram_quantile(0.99, sum(rate(flask_http_request_duration_seconds_bucket{{namespace="{ns}"}}[5m])) by (le)) or vector(0)',
            'pod_restarts': f'sum(increase(kube_pod_container_status_restarts_total{{namespace="{ns}"}}[15m])) or vector(0)'
        }

        values = {}
        for name, query in queries.items():
            values[name] = self._query(query)

        print(f"Collected: {values}")
        return np.array([values[f] for f in self.feature_names])


if __name__ == '__main__':
    collector = MetricsCollector()
    features = collector.collect()
    print(f"\nFeature vector: {features}")
