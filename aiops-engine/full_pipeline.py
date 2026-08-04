"""xo

Complete AIOps Pipeline — one full detection and remediation cycle.

Proves the entire chain:
  Prometheus -> MetricsCollector -> IsolationForest -> RemediationEngine
"""
from metrics_collector import MetricsCollector
from anomaly_detector import AnomalyDetector
from remediation_engine import RemediationEngine
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# -------------------------------
# OpenTelemetry Configuration
# -------------------------------

resource = Resource.create({
    "service.name": "aiops-engine"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True,
)

span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
print("=" * 50)
print("AIOps Platform — Full Pipeline Test")
print("=" * 50)

# Step 1 — collect real metrics
with tracer.start_as_current_span("Collect Metrics"):
    print("\n[1] Collecting live metrics from Prometheus...")
    collector = MetricsCollector()
    features = collector.collect()

# Step 2 — train model and predict
with tracer.start_as_current_span("Anomaly Detection"):
    print("\n[2] Running anomaly detection...")
    detector = AnomalyDetector()
    detector.train()
    result = detector.predict(features)
    print(f"    Score: {result['score']:.3f}")
    print(f"    Is anomaly: {result['is_anomaly']}")
    print(f"    Contributors: {result['contributing_features']}")

# Step 3 — remediate if needed
with tracer.start_as_current_span("Remediation"):
    print("\n[3] Evaluating remediation...")
    remediator = RemediationEngine()
    if result['is_anomaly']:
        audit = remediator.remediate(result)
        print(f"    Action taken: {audit['action']}")
        print(f"    Result: {audit['result']}")
    else:
        print("    No anomaly detected — no action needed")

# Step 4 — audit log
print("\n[4] Audit log:")
for entry in remediator.get_audit_log():
    print(f"    {entry.get('timestamp')} | {entry.get('action')} | {entry.get('result')}")

print("\n" + "=" * 50)
print("Pipeline complete")
print("=" * 50)

