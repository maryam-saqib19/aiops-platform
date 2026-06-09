"""
Unit tests for the AIOps application.

These tests run automatically in the CI/CD pipeline.
If any test fails, the pipeline stops and does not deploy broken code.

Think of these like a quality control checklist that runs itself.
"""
import pytest
import json
import sys
import os

# Add the app folder to the Python path so we can import app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app


@pytest.fixture
def client():
    """
    Creates a test version of the app.
    No real server needed - pytest handles everything internally.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ── Test 1: Health endpoint ──────────────────────────────────
def test_health_returns_200(client):
    """Health endpoint must return status code 200 (means OK)."""
    response = client.get('/health')
    assert response.status_code == 200, \
        f"Expected 200 but got {response.status_code}"


def test_health_returns_json(client):
    """Health endpoint must return valid JSON."""
    response = client.get('/health')
    data = json.loads(response.data)
    assert isinstance(data, dict), "Response must be a JSON object"


def test_health_contains_status(client):
    """Health response must contain a status field saying healthy."""
    response = client.get('/health')
    data = json.loads(response.data)
    assert 'status' in data, "Response missing 'status' field"
    assert data['status'] == 'healthy', \
        f"Expected 'healthy' but got '{data['status']}'"


def test_health_contains_timestamp(client):
    """Health response must include a timestamp."""
    response = client.get('/health')
    data = json.loads(response.data)
    assert 'timestamp' in data, "Response missing 'timestamp' field"
    assert isinstance(data['timestamp'], float), \
        "Timestamp must be a number"


# ── Test 2: Metrics endpoint ─────────────────────────────────
def test_metrics_returns_200(client):
    """Prometheus metrics endpoint must be reachable."""
    response = client.get('/metrics')
    assert response.status_code == 200


def test_metrics_returns_text(client):
    """Prometheus expects plain text format, not JSON."""
    response = client.get('/metrics')
    content_type = response.content_type
    assert 'text/plain' in content_type, \
        f"Expected text/plain but got {content_type}"


# ── Test 3: Metrics demo endpoint ───────────────────────────
def test_metrics_demo_returns_200(client):
    """Metrics demo endpoint must respond successfully."""
    response = client.get('/metrics-demo')
    assert response.status_code == 200


def test_metrics_demo_contains_latency(client):
    """Response must contain latency_ms field for AIOps analysis."""
    response = client.get('/metrics-demo')
    data = json.loads(response.data)
    assert 'latency_ms' in data, "Response missing 'latency_ms' field"
    assert data['latency_ms'] > 0, "Latency must be positive"


def test_metrics_demo_contains_anomaly_flag(client):
    """Response must say whether this was an injected anomaly."""
    response = client.get('/metrics-demo')
    data = json.loads(response.data)
    assert 'injected_anomaly' in data, \
        "Response missing 'injected_anomaly' field"
    assert isinstance(data['injected_anomaly'], bool), \
        "injected_anomaly must be true or false"


# ── Test 4: Simulate anomaly endpoint ───────────────────────
def test_simulate_anomaly_returns_200(client):
    """Simulate anomaly endpoint must respond successfully."""
    response = client.get('/simulate-anomaly?score=0.95')
    assert response.status_code == 200


def test_simulate_anomaly_sets_score(client):
    """The score we send must be reflected in the response."""
    response = client.get('/simulate-anomaly?score=0.75')
    data = json.loads(response.data)
    assert 'anomaly_score' in data
    assert data['anomaly_score'] == 0.75, \
        f"Expected 0.75 but got {data['anomaly_score']}"


def test_simulate_anomaly_score_capped_at_one(client):
    """Score must never exceed 1.0 even if a higher value is sent."""
    response = client.get('/simulate-anomaly?score=999')
    data = json.loads(response.data)
    assert data['anomaly_score'] <= 1.0, \
        "Score must be capped at 1.0"


# ── Test 5: Unknown endpoint ─────────────────────────────────
def test_unknown_endpoint_returns_404(client):
    """Visiting a non-existent page must return 404, not 200 or 500."""
    response = client.get('/this-does-not-exist')
    assert response.status_code == 404, \
        f"Expected 404 but got {response.status_code}"
