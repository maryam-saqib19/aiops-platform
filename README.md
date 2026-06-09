# GitOps-Driven Multi-Cloud AIOps Platform
### EduQual Level 6 — Enterprise Architecture Project

## What this platform does
A self-healing, automatically monitored, and policy-enforced system that deploys
software across three cloud providers (AWS, Azure, GCP), detects problems using
machine learning, and fixes them autonomously without human intervention.

## Architecture summary
- **GitOps layer**: ArgoCD watches GitHub and keeps all clusters in sync
- **Infrastructure**: Terraform provisions EKS, AKS, and GKE clusters
- **Containers**: Docker + Kubernetes with full security hardening
- **Observability**: Prometheus (metrics) + Loki (logs) + Jaeger (traces) + Grafana
- **AIOps**: Isolation Forest ML model detects anomalies from 5 Prometheus metrics
- **Remediation**: Autonomous scale-out, restart, rollback via Kubernetes API
- **Security**: OPA Gatekeeper + HashiCorp Vault + Falco + Trivy
- **Compliance**: ISO 27001, NIST 800-53, ISO/IEC 42001, GDPR

## Tech stack
| Layer | Tools |
|---|---|
| GitOps | ArgoCD, GitHub |
| IaC | Terraform |
| Containers | Docker, Kubernetes, Helm |
| CI/CD | Jenkins, GitLab CI |
| Monitoring | Prometheus, Grafana, Loki, Jaeger, OpenTelemetry |
| AIOps | Python, Scikit-learn, MLflow |
| Security | OPA, Vault, Falco, Trivy |
| Clouds | AWS EKS, Azure AKS, GCP GKE |

## Repository structure
- `terraform/` — Infrastructure as Code for all three clouds
- `kubernetes/` — All Kubernetes manifests
- `aiops-engine/` — Python ML anomaly detection and remediation code
- `ci-cd/` — Jenkins and GitLab CI pipeline definitions
- `policies/` — OPA Rego policies and compliance mappings
- `docs/` — Architecture diagrams, screenshots, runbooks
- `app/` — Application source code

## Standards compliance
- ISO 27001 — information security management
- NIST 800-53 — security and privacy controls
- ISO/IEC 42001 — AI management system
- GDPR — data protection and privacy
