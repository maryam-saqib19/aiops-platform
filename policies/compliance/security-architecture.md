# Security Architecture — AIOps Platform

## Defence in Depth

This platform implements security at four distinct layers, so that
a failure at any single layer does not result in a breach.

### Layer 1: Prevention — Stop bad things being created

- OPA Gatekeeper: blocks non-compliant pods at admission time
- Pod Security Standards: enforces restricted security profile
- Trivy: blocks images with CRITICAL CVEs in CI pipeline

### Layer 2: Protection — Secure what exists

- HashiCorp Vault: dynamic secrets, no static passwords in code
- RBAC: least privilege service accounts, no wildcard permissions
- Network Policies: default-deny, explicit allow rules only
- KMS encryption: Kubernetes Secrets encrypted at rest

### Layer 3: Detection — Find what bypasses the above

- Falco: real-time kernel-level syscall monitoring
- Prometheus alerts: anomaly detection via ML model
- Loki: centralised log aggregation with structured search

### Layer 4: Response — Fix what is detected

- Autonomous remediation: scale, restart, rollback without human
- ArgoCD selfHeal: revert unauthorised manual changes
- Alert routing: Alertmanager sends to right team immediately

## Zero Trust Principles Applied

**Never trust, always verify:**

- Every pod has its own Service Account — no shared identities
- Network policies require explicit allow rules — no implicit trust
- Vault requires authentication for every secret retrieval
- RBAC requires explicit permission for every API call

**Assume breach:**

- Falco monitors inside running containers — assumes code may be compromised
- Network policies limit lateral movement even if one pod is breached
- readOnlyRootFilesystem prevents malware installation
- capabilities.drop: ALL prevents privilege escalation post-breach

## Secrets Management

No secret is ever hardcoded in any file in this repository.

| Secret type | Storage | Lifecycle |
|---|---|---|
| Application passwords | HashiCorp Vault | 1 hour TTL, auto-rotated |
| Kubernetes API credentials | Service Account tokens | Auto-rotated by Kubernetes |
| Docker registry credentials | Kubernetes Secret (Vault-injected) | Rotated on deployment |
| ArgoCD admin password | Initial Secret, replace with SSO | Manual rotation documented |

## Incident Response Flow

Falco detects suspicious syscall

↓

Alert sent to Loki (structured log)

↓

Prometheus alert fires (AIOps anomaly)

↓

Remediation engine evaluates action

↓

Human notified via alert_only or autonomous action taken with audit log

↓

Post-incident: Git commit to fix root cause

↓

ArgoCD deploys fix automatically
