# Compliance Mapping — AIOps Platform

Every security control in this platform is mapped to one or more
compliance standards. This document exists so auditors can trace
any compliance requirement to its technical implementation.

## ISO 27001 Mapping

| Control | Requirement | Implementation |
|---|---|---|
| A.9.1 | Access control policy | RBAC roles (developer, sre, aiops-engine) with least privilege |
| A.9.4 | System and application access | OPA Gatekeeper blocks non-compliant pods at admission |
| A.10.1 | Cryptographic controls | KMS key rotation enabled, Vault secret encryption at rest |
| A.12.1 | Operational procedures | GitOps via ArgoCD — all changes documented in Git history |
| A.12.4 | Event logging | Prometheus metrics, Loki logs, remediation audit log |
| A.12.6 | Vulnerability management | Trivy scans every image in CI pipeline before deployment |
| A.14.2 | Security in development | Pod Security Standards restricted, no root containers |

## NIST 800-53 Mapping

| Control | Requirement | Implementation |
|---|---|---|
| AC-2 | Account management | Kubernetes RBAC with named service accounts |
| AC-6 | Least privilege | Roles grant minimum permissions, automount disabled |
| AU-2 | Audit events | Kubernetes audit logging, Loki log aggregation |
| AU-9 | Protection of audit info | Logs stored in separate monitoring namespace |
| CM-2 | Baseline configuration | Terraform IaC, GitOps declarative state |
| SC-7 | Boundary protection | Network policies default-deny, explicit allow rules |
| SI-3 | Malware protection | Trivy image scanning, OPA admission control |
| SI-7 | Software integrity | ArgoCD verifies manifests match Git state |

## ISO/IEC 42001 Mapping (AI Governance)

| Requirement | Implementation |
|---|---|
| Transparency | Isolation Forest contributing features explain each decision |
| Accountability | Remediation audit log — timestamp, action, actor, reason |
| Risk management | Confidence window (3 detections), cooldown (5 minutes) |
| Human oversight | REMEDIATION_ENABLED flag, alert_only for ambiguous cases |
| Data governance | Metrics only — no personal data processed by ML model |

## GDPR Mapping

| Article | Requirement | Implementation |
|---|---|---|
| Art. 5 | Data minimisation | AIOps processes only operational metrics, no PII |
| Art. 25 | Privacy by design | No personal data ever enters the ML pipeline |
| Art. 32 | Security of processing | Vault secrets, TLS, encrypted volumes |
