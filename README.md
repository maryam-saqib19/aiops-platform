# GitOps-Driven Multi-Cloud AIOps Platform

**EduQual Level 6 — Enterprise Architecture Project**

A self-healing, intelligently monitored, and policy-enforced platform
that deploys software across three cloud providers, detects problems
using machine learning, and remediates them autonomously.

---

## The problem this solves

Modern enterprises run hundreds of microservices across multiple clouds.
Human operators cannot watch every service simultaneously — a platform
running 500 services generating 25,000 metrics per second needs machine
intelligence, not human dashboards. This platform implements the AIOps
(Artificial Intelligence for IT Operations) pattern: ML-driven anomaly
detection feeding into autonomous remediation, with full audit trails
for compliance governance.

---

## Architecture overview

```
Developer pushes code
        ↓
Jenkins CI (test → scan → build → push)
        ↓
Git manifest updated (GitOps handoff)
        ↓
ArgoCD detects change → deploys to Kubernetes
        ↓
Prometheus collects 5 metrics every 15s
        ↓
Isolation Forest ML model scores the observation
        ↓
Anomaly detected → RemediationEngine acts
        ↓
Kubernetes API called → scale/restart/rollback
        ↓
Audit log recorded → compliance satisfied
```

---

## Tech stack

| Layer | Tools |
|-------|-------|
| GitOps | ArgoCD, GitHub |
| IaC | Terraform (AWS EKS, Azure AKS, GCP GKE) |
| Containers | Docker, Kubernetes, Helm |
| CI/CD | Jenkins (8-stage pipeline) |
| Monitoring | Prometheus, Grafana, Loki, Falco |
| AIOps | Python, Scikit-learn (Isolation Forest), MLflow |
| Security | OPA Gatekeeper, HashiCorp Vault, Trivy, Falco |
| Clouds | AWS EKS (primary), Azure AKS (DR), GCP GKE (ML) |

---

## Repository structure

```
aiops-platform/
├── app/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_app.py
│
├── aiops-engine/
│   ├── metrics_collector.py
│   ├── anomaly_detector.py
│   ├── remediation_engine.py
│   ├── full_pipeline.py
│   ├── config/
│   │   └── config.py
│   └── tests/
│
├── kubernetes/
│   ├── apps/
│   ├── namespaces/
│   ├── rbac/
│   ├── network-policies/
│   ├── resource-management/
│   ├── monitoring/
│   └── argocd/
│
├── terraform/
│   ├── aws/
│   ├── azure/
│   ├── gcp/
│   └── modules/
│       └── vpc/
│
├── ci-cd/
│   └── Jenkinsfile
│
├── policies/
│   ├── opa/
│   ├── falco/
│   │   └── custom-rules.yaml
│   └── compliance/
│
├── docs/
│   ├── runbooks/
│   ├── screenshots/
│   └── integration-test/
│
└── README.md
```

---

## Key technical decisions

### Why Isolation Forest for anomaly detection?

Unsupervised learning requires no labelled training data.
It detects multidimensional anomalies across CPU, memory,
latency and error rate that simple threshold alerts miss.
The model trains in under one second using a 500-sample baseline.

### Why ArgoCD instead of manual kubectl?

GitOps uses a pull-based deployment model where the cluster
continuously reconciles itself with Git. Self-healing restores
unauthorised changes automatically, ensuring every deployment
is auditable and reversible.

### Why OPA Gatekeeper with Pod Security Standards?

Pod Security Standards provide predefined enforcement levels,
while OPA enables custom organisational policies such as
required labels, approved registries and naming conventions.

### Why Terraform?

Terraform provides one language for AWS, Azure and GCP.
Plans can be reviewed before deployment, ensuring predictable,
repeatable infrastructure changes.

---

## Compliance mapping

| Standard | Controls Implemented |
|----------|----------------------|
| ISO 27001 | RBAC, audit logging, KMS encryption |
| NIST 800-53 | Least privilege, network policies, image scanning |
| ISO/IEC 42001 | AI transparency, auditability, human oversight |
| GDPR | Metrics only, no PII processed |

---

## Terraform validation status

| Cloud | terraform validate | terraform plan |
|-------|--------------------|----------------|
| AWS | ✅ Passing | ✅ 29 resources calculated |
| Azure | ✅ Passing | Requires live Azure authentication |
| GCP | ✅ Passing | Requires live Google Cloud authentication |

---

## Real troubleshooting documented

This project encountered and resolved several production-style issues:

- Minikube CNI bug fixed using `--cni=kindnet`
- Kubernetes rollout deadlock resolved with `maxUnavailable:1`
- PromQL metric name mismatch identified through API testing
- cAdvisor label filtering corrected
- Isolation Forest threshold calibrated from `-0.15` to `-0.40`

Complete root cause analyses are available in `docs/runbooks/`.

---

## Running the platform locally

### Prerequisites

- WSL2 Ubuntu 22.04
- Docker
- kubectl
- Minikube
- Helm
- Terraform
- Python 3.10+

### Start clusters

    minikube start --profile aws-eks --cpus=2 --memory=2200 --driver=docker --cni=kindnet --nodes=3
    minikube start --profile azure-aks --driver=docker
    minikube start --profile gcp-gke --driver=docker

### Deploy application

    bash scripts/deploy-all-clusters.sh

### Start monitoring

    kubectl port-forward svc/prometheus-stack-prometheus 9090:9090 -n monitoring &
    kubectl port-forward svc/prometheus-stack-grafana 3000:80 -n monitoring &
    kubectl port-forward svc/argocd-server 8090:443 -n argocd &

### Run the AIOps engine

    cd aiops-engine
    python3 full_pipeline.py

---

## Standards

- EduQual Level 6 Enterprise Architecture
- ISO 27001:2022 Information Security Management
- NIST SP 800-53 Rev.5 Security Controls
- ISO/IEC 42001:2023 AI Management System
- GDPR Data Protection

