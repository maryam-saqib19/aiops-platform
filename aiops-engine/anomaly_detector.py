"""
Isolation Forest anomaly detection engine.

Core idea: anomalies are rare and different, so they get isolated
by random tree splits faster than normal points do. The average
number of splits needed to isolate a point becomes its anomaly score.

Integrated with MLflow for experiment tracking.
"""

import mlflow
import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict
import sys

sys.path.insert(0, '.')

from config.config import config


class AnomalyDetector:

    def __init__(self):

        self.model = None
        self.scaler = None
        self.is_trained = False

        self.feature_names = [
            'cpu_usage',
            'memory_bytes',
            'error_rate',
            'latency_p99',
            'pod_restarts'
        ]

        # Connect to MLflow server
        mlflow.set_tracking_uri(
            os.getenv(
                "MLFLOW_TRACKING_URI",
                "http://localhost:5000"
            )
        )

        mlflow.set_experiment(
            "aiops-anomaly-detection"
        )


    def train(self, training_data: np.ndarray = None, run_name="anomaly-training"):

        """
        Train Isolation Forest model and log experiment details to MLflow.
        """

        if training_data is None:
            training_data = self._generate_synthetic_baseline()


        with mlflow.start_run(run_name=run_name):

            self.scaler = StandardScaler()

            X_scaled = self.scaler.fit_transform(training_data)


            self.model = IsolationForest(

                n_estimators=config.n_estimators,

                contamination=config.contamination,

                random_state=42,

                n_jobs=-1
            )


            self.model.fit(X_scaled)


            self.is_trained = True


            # -----------------------------
            # MLflow logging
            # -----------------------------

            mlflow.log_param(
                "algorithm",
                "Isolation Forest"
            )

            mlflow.log_param(
                "n_estimators",
                config.n_estimators
            )

            mlflow.log_param(
                "contamination",
                config.contamination
            )

            mlflow.log_param(
                "features",
                ",".join(self.feature_names)
            )


            mlflow.log_metric(
                "training_samples",
                len(training_data)
            )


            # Average model decision score
            scores = self.model.score_samples(X_scaled)

            mlflow.log_metric(
                "average_training_score",
                float(np.mean(scores))
            )


            print(
                f"MLflow run completed: {run_name}"
            )


            print(
                f"Model trained on {len(training_data)} samples"
            )


    def predict(self, features: np.ndarray) -> Dict:

        """
        Score a single observation.
        """

        if not self.is_trained:
            self.train()


        features_scaled = self.scaler.transform(
            features.reshape(1, -1)
        )


        score = float(
            self.model.score_samples(features_scaled)[0]
        )


        is_anomaly = (
            score < config.anomaly_threshold
        )


        z_scores = np.abs(
            (
                features - self.scaler.mean_
            )
            /
            (
                self.scaler.scale_ + 1e-10
            )
        )


        contributors = [

            name

            for name, z in sorted(
                zip(
                    self.feature_names,
                    z_scores
                ),
                key=lambda x: -x[1]
            )

            if z > 2.0

        ]


        return {

            "score": score,

            "is_anomaly": is_anomaly,

            "contributing_features": contributors,

            "features": dict(
                zip(
                    self.feature_names,
                    features.tolist()
                )
            )

        }



    def _generate_synthetic_baseline(self, n=500):

        """
        Generate normal Kubernetes workload data.
        """

        rng = np.random.default_rng(seed=42)

        return np.column_stack([

            rng.normal(
                0.30,
                0.08,
                n
            ),

            rng.normal(
                50e6,
                15e6,
                n
            ),

            np.abs(
                rng.normal(
                    0.005,
                    0.003,
                    n
                )
            ),

            np.abs(
                rng.normal(
                    0.10,
                    0.03,
                    n
                )
            ),

            rng.poisson(
                0.1,
                n
            ).astype(float)

        ])



if __name__ == "__main__":


    detector = AnomalyDetector()


    detector.train(
        run_name="kubernetes-persistent-mlflow-run"
    )


    print("\n--- Testing NORMAL reading ---")


    normal = np.array(
        [
            0.30,
            50e6,
            0.005,
            0.10,
            0.0
        ]
    )


    print(
        detector.predict(normal)
    )



    print("\n--- Testing ANOMALY reading ---")


    anomaly = np.array(
        [
            0.95,
            50e6,
            0.25,
            3.5,
            5.0
        ]
    )


    print(
        detector.predict(anomaly)
    )
