"""
AIOps Platform Application
This is the main application that:
- Serves web requests
- Exposes metrics for Prometheus to collect
- Simulates anomalies for the AIOps engine to detect
"""

from flask import Flask, jsonify, request, Response
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import random
import time
import logging
import os

# Create the Flask application
app = Flask(__name__)

# Set up logging so we can see what is happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# ── Prometheus metrics ───────────────────────────────────────
# These are the numbers Prometheus will collect every 15 seconds
# Think of them like counters on a dashboard

# PrometheusMetrics automatically tracks every web request
metrics = PrometheusMetrics(app, path=None)

# Info metric — tells Prometheus basic facts about this app
metrics.info(
    'aiops_app_info',
    'AIOps application information',
    version=os.getenv('VERSION', '1.0.0')
)

# Anomaly score — this number goes up when the AIOps engine
# detects something wrong. 0 = all normal, 1 = big problem
ANOMALY_SCORE = Gauge(
    'aiops_anomaly_score',
    'Current anomaly score from ML model (0=normal, 1=anomaly)'
)

# Remediation counter — counts how many times the system
# automatically fixed itself
REMEDIATION_COUNTER = Counter(
    'aiops_remediations_total',
    'Total number of autonomous remediations triggered',
    ['action', 'result']
)

# Request latency histogram — records how long each request took
# This is what the AIOps engine analyses to detect slow responses
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'How long HTTP requests take in seconds',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# ── Web endpoints (routes) ───────────────────────────────────

@app.route('/health')
def health():
    """
    Health check endpoint.
    Kubernetes uses this to know if the app is alive.
    If this stops responding, Kubernetes restarts the pod.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": os.getenv('VERSION', '1.0.0'),
        "pod": os.getenv('POD_NAME', 'local')
    })


@app.route('/metrics')
def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    Prometheus visits this URL every 15 seconds and reads all the numbers.
    Like a meter reader coming to check your electricity usage.
    """
    return Response(generate_latest(), mimetype='text/plain')


@app.route('/metrics-demo')
def metrics_demo():
    """
    Simulates varying response times.
    Most of the time it is fast (around 100ms).
    5% of the time it is very slow (500ms to 2000ms) to simulate a problem.
    The AIOps engine watches these times and detects when they are too slow.
    """
    start_time = time.time()

    # 5% chance of simulating a slow response (anomaly)
    if random.random() < 0.05:
        latency_ms = random.uniform(500, 2000)
        is_anomaly = True
        logger.warning(f"Simulated slow response: {latency_ms:.0f}ms")
    else:
        # Normal response time with small random variation
        latency_ms = max(10, random.gauss(100, 20))
        is_anomaly = False

    # Actually wait that long before responding
    time.sleep(latency_ms / 1000)

    # Record this in the Prometheus histogram
    REQUEST_LATENCY.labels(
        method='GET',
        endpoint='/metrics-demo',
        status='200'
    ).observe(time.time() - start_time)

    return jsonify({
        "latency_ms": round(latency_ms, 2),
        "injected_anomaly": is_anomaly,
        "message": "Anomaly injected!" if is_anomaly else "Normal response"
    })


@app.route('/simulate-anomaly')
def simulate_anomaly():
    """
    Manually set the anomaly score.
    Use this during your presentation to show the AIOps engine detecting a problem.
    Visit: http://localhost:8080/simulate-anomaly?score=0.95
    """
    # Get the score from the URL, default to 0.95 if not provided
    score = float(request.args.get('score', 0.95))

    # Make sure score stays between 0 and 1
    score = max(0.0, min(1.0, score))

    # Update the Prometheus gauge
    ANOMALY_SCORE.set(score)

    logger.warning(f"Anomaly score manually set to {score}")

    return jsonify({
        "anomaly_score": score,
        "message": f"Anomaly score set to {score}",
        "threshold": 0.8,
        "will_trigger_remediation": score > 0.8
    })


@app.route('/simulate-remediation')
def simulate_remediation():
    """
    Records a fake remediation action.
    Use this during your presentation to demonstrate the audit trail.
    """
    action = request.args.get('action', 'scale_out')

    REMEDIATION_COUNTER.labels(
        action=action,
        result='success'
    ).inc()

    logger.info(f"Remediation action recorded: {action}")

    return jsonify({
        "action": action,
        "result": "success",
        "message": f"Remediation '{action}' recorded in audit log"
    })


# Start the application when this file is run directly
if __name__ == '__main__':
    logger.info("AIOps application starting on port 8080")
    app.run(host='0.0.0.0', port=8080)

