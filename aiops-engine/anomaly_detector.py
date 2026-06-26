"""
Isolation Forest anomaly detection engine.

Core idea: anomalies are rare and different, so they get isolated
by random tree splits faster than normal points do. The average
number of splits needed to isolate a point becomes its anomaly score.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List
import sys
sys.path.insert(0, '.')
from config.config import config


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_names = [
            'cpu_usage', 'memory_bytes', 'error_rate',
            'latency_p99', 'pod_restarts'
        ]

    def train(self, training_data: np.ndarray = None):
        """
        Train on baseline 'normal' data.
        If no real data is provided, generates a synthetic baseline
        based on typical Kubernetes workload ranges — this is what
        you would replace with real 7-30 day Prometheus history
        once the platform has been running long enough to collect it.
        """
        if training_data is None:
            training_data = self._generate_synthetic_baseline()

        self.scaler = StandardScaler()
        # StandardScaler is essential here: memory_bytes is in the
        # hundreds of millions, cpu_usage is a fraction between 0
        # and 1. Without scaling, memory_bytes would dominate every
        # distance calculation and the model would effectively become
        # a memory-only anomaly detector, ignoring the other 4 features
        X_scaled = self.scaler.fit_transform(training_data)

        self.model = IsolationForest(
            n_estimators=config.n_estimators,
            contamination=config.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        print(f"Model trained on {len(training_data)} samples")

    def predict(self, features: np.ndarray) -> Dict:
        """
        Score a single observation.
        Returns score, whether it's anomalous, and which features
        contributed most to the anomaly (via z-score).
        """
        if not self.is_trained:
            self.train()

        features_scaled = self.scaler.transform(features.reshape(1, -1))
        score = float(self.model.score_samples(features_scaled)[0])
        is_anomaly = score < config.anomaly_threshold

        # Identify which specific features deviate most from normal —
        # this is what lets the remediation engine choose the right
        # action tomorrow (high CPU -> scale out, high memory -> restart)
        z_scores = np.abs((features - self.scaler.mean_) / (self.scaler.scale_ + 1e-10))
        contributors = [
            name for name, z in sorted(
                zip(self.feature_names, z_scores), key=lambda x: -x[1]
            ) if z > 2.0
        ]

        return {
            'score': score,
            'is_anomaly': is_anomaly,
            'contributing_features': contributors,
            'features': dict(zip(self.feature_names, features.tolist()))
        }

    def _generate_synthetic_baseline(self, n: int = 500) -> np.ndarray:
        """Synthetic 'normal operation' data based on typical ranges."""
        rng = np.random.default_rng(seed=42)
        return np.column_stack([
            rng.normal(0.30, 0.08, n),
            rng.normal(50e6, 15e6, n),
            np.abs(rng.normal(0.005, 0.003, n)),
            np.abs(rng.normal(0.10, 0.03, n)),
            rng.poisson(0.1, n).astype(float)
        ])


if __name__ == '__main__':
    detector = AnomalyDetector()
    detector.train()

    print("\n--- Testing with a NORMAL reading ---")
    normal = np.array([0.30, 50e6, 0.005, 0.10, 0.0])
    result = detector.predict(normal)
    print(result)

    print("\n--- Testing with an ANOMALOUS reading (high CPU + errors) ---")
    anomaly = np.array([0.95, 50e6, 0.25, 3.5, 5.0])
    result = detector.predict(anomaly)
    print(result)
