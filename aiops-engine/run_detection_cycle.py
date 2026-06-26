"""
One complete detection cycle using REAL live Prometheus data.
This proves the full chain: cluster -> Prometheus -> AIOps engine.
"""
from metrics_collector import MetricsCollector
from anomaly_detector import AnomalyDetector

collector = MetricsCollector()
detector = AnomalyDetector()
detector.train()

print("Collecting live metrics from your actual cluster...")
features = collector.collect()

print("\nRunning anomaly detection...")
result = detector.predict(features)

print(f"\nResult: {result}")
print(f"\nAnomaly score: {result['score']:.3f}")
print(f"Is anomaly: {result['is_anomaly']}")
