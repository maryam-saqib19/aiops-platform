import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from anomaly_detector import AnomalyDetector


@pytest.fixture
def trained_detector():
    d = AnomalyDetector()
    d.train()
    return d


def test_model_trains_successfully():
    d = AnomalyDetector()
    d.train()
    assert d.is_trained is True


def test_normal_reading_not_flagged(trained_detector):
    normal = np.array([0.30, 50e6, 0.005, 0.10, 0.0])
    result = trained_detector.predict(normal)
    assert result['is_anomaly'] is False


def test_extreme_cpu_flagged_as_anomaly(trained_detector):
    anomaly = np.array([0.98, 50e6, 0.005, 0.10, 0.0])
    result = trained_detector.predict(anomaly)
    assert result['is_anomaly'] is True


def test_contributing_features_identified(trained_detector):
    anomaly = np.array([0.98, 50e6, 0.005, 0.10, 0.0])
    result = trained_detector.predict(anomaly)
    assert 'cpu_usage' in result['contributing_features']


def test_combined_anomaly_scores_lower_than_single(trained_detector):
    single = trained_detector.predict(np.array([0.95, 50e6, 0.005, 0.10, 0.0]))
    combined = trained_detector.predict(np.array([0.95, 80e6, 0.25, 3.0, 5.0]))
    assert combined['score'] < single['score']
