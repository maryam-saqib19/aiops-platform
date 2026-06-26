"""
Configuration for the AIOps anomaly detection engine.
All values come from environment variables with sensible defaults,
so the same code runs in local testing and inside Kubernetes
without any code changes — only the environment differs.
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    prometheus_url: str = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')

    # Isolation Forest hyperparameters
    n_estimators: int = int(os.getenv('IF_N_ESTIMATORS', '100'))
    contamination: float = float(os.getenv('IF_CONTAMINATION', '0.05'))
    # 0.05 = we expect roughly 5% of observations to be anomalous
    # This is a conservative, commonly used default

    anomaly_threshold: float = float(os.getenv('ANOMALY_THRESHOLD', '-0.40'))
    # Isolation Forest score_samples() returns negative values
    # More negative = more anomalous. -0.15 is a deliberately
    # conservative cutoff to reduce false positives

    confidence_window: int = int(os.getenv('CONFIDENCE_WINDOW', '3'))
    # Require 3 consecutive anomalous readings before declaring
    # a genuine anomaly — protects against single-spike false positives

    detection_interval: int = int(os.getenv('DETECTION_INTERVAL', '60'))
    # How often (seconds) the engine checks Prometheus

    namespace: str = os.getenv('TARGET_NAMESPACE', 'production')


config = Config() 
