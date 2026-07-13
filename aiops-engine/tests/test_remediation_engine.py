import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from remediation_engine import RemediationEngine


@pytest.fixture
def engine():
    return RemediationEngine()


def test_cpu_anomaly_triggers_scale_out(engine):
    result = engine.determine_action({
        'features': {'cpu_usage': 0.92, 'memory_bytes': 50e6,
                     'error_rate': 0.001, 'latency_p99': 0.1,
                     'pod_restarts': 0.0},
        'contributing_features': ['cpu_usage']
    })
    assert result == 'scale_out'


def test_pod_restarts_triggers_rolling_restart(engine):
    result = engine.determine_action({
        'features': {'cpu_usage': 0.30, 'memory_bytes': 50e6,
                     'error_rate': 0.001, 'latency_p99': 0.1,
                     'pod_restarts': 5.0},
        'contributing_features': ['pod_restarts']
    })
    assert result == 'rolling_restart'


def test_error_rate_triggers_alert_only(engine):
    result = engine.determine_action({
        'features': {'cpu_usage': 0.30, 'memory_bytes': 50e6,
                     'error_rate': 0.25, 'latency_p99': 0.1,
                     'pod_restarts': 0.0},
        'contributing_features': ['error_rate']
    })
    assert result == 'alert_only'


def test_cooldown_prevents_immediate_second_action(engine):
    import time
    engine.last_remediation_time = time.time()
    assert engine.is_in_cooldown() is True


def test_audit_log_records_actions(engine):
    detection = {
        'score': -0.45,
        'is_anomaly': True,
        'contributing_features': ['error_rate'],
        'features': {'cpu_usage': 0.30, 'memory_bytes': 50e6,
                     'error_rate': 0.25, 'latency_p99': 0.1,
                     'pod_restarts': 0.0}
    }
    engine.remediate(detection)
    assert len(engine.audit_log) == 1
    assert engine.audit_log[0]['action'] == 'alert_only'
    assert 'timestamp' in engine.audit_log[0]
    assert engine.audit_log[0]['actor'] == 'aiops-autonomous-engine'

