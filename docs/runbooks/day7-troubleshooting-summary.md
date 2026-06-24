# Day 7 — Complete Troubleshooting Summary

11 distinct problems were diagnosed and resolved while building the
Jenkins CI/CD pipeline and connecting it to ArgoCD's GitOps deployment.

## 1. Jenkins could not find the test files
**Problem:** Unit tests failed — pytest ran from the repo root instead
of the `app/` subdirectory where `tests/` actually lives.
**Fix:** Updated the Jenkinsfile's Unit Tests stage to `cd app` first.

## 2. Python package installation issues in the pipeline
**Problem:** `pip install` hit compatibility/permission issues on a
fresh Jenkins agent.
**Fix:** Used `--break-system-packages` consistently and pinned
install order (requirements.txt before pytest).

## 3. Git push conflicts between Jenkins and local work
**Problem:** Jenkins's automated commits and local commits diverged,
causing rejected pushes ("fetch first").
**Fix:** Standardised on merge strategy (not rebase) before every push:
```bash
git config pull.rebase false
git pull origin main --no-edit
git push origin main
```

## 4. Jenkins denied permission reading Minikube certificates
**Problem:** Verify Deployment stage failed with permission denied —
Jenkins runs as its own system user, not as the user owning the
Minikube cert files.
**Fix:** Copied kubeconfig and `.minikube/profiles` into Jenkins's
home directory and `chown`'d both to the `jenkins` user.

## 5. ArgoCD CLI connection error: TLS handshake mismatch
**Problem:** `argocd app get` failed with "tls: first record does not
look like a TLS handshake" — caused by a stale or conflicting
port-forward.
**Fix:** Killed stale port-forwards, restarted cleanly on a dedicated
port (8090, since Jenkins occupies 8080), re-authenticated with
`--insecure` for the local self-signed cert.

## 6. ArgoCD stuck on an old Git revision
**Problem:** ArgoCD did not pick up Jenkins's new commits within the
expected reconciliation window.
**Fix:** Forced a hard refresh and manual sync:
```bash
kubectl annotate application aiops-platform -n argocd \
  argocd.argoproj.io/refresh=hard --overwrite
argocd app sync aiops-platform
```

## 7. ArgoCD's own components entered ImagePullBackOff
**Problem:** Core ArgoCD pods (repo-server, redis, dex-server) all
failed to start simultaneously.
**Fix attempt:** Restarted pods individually, inspected events/logs —
revealed repeated image pull failures pointing to a deeper networking
issue rather than a config mistake.

## 8. Root cause: Minikube nodes had no real internet access
**Problem:** DNS resolution worked (`nslookup quay.io` succeeded) but
HTTPS connections hung indefinitely from inside the Minikube containers
— while the WSL2 host itself had full internet access. This explained
both #7 and the later application ImagePullBackOff.
**Fix:** Cycled the Minikube node network stack:
```bash
minikube -p aws-eks stop
minikube -p aws-eks start
```
Verified before trusting it:
```bash
docker exec aws-eks ping -c 4 8.8.8.8
docker exec aws-eks curl -I https://quay.io
```
Both succeeded after restart — confirmed real connectivity restored.

## 9. ArgoCD pods needed a forced restart even after networking was fixed
**Problem:** Some pods stayed in their old failed state rather than
automatically retrying.
**Fix:** Deleted all ArgoCD pods at once (safe — all stateless,
managed by Deployments/StatefulSets):
```bash
kubectl delete pod -n argocd --all
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=180s
```

## 10. Kubernetes rollout deadlock: anti-affinity vs maxUnavailable:0
**Problem:** Deploying Jenkins's new build (v1.0.6) stalled with
`ProgressDeadlineExceeded`. New pod stayed `Pending` 16+ minutes, no
node ever assigned.
**Root cause:** Hard pod anti-affinity (one pod per node) + exactly
3 nodes + 3 replicas = zero spare capacity. `maxUnavailable: 0`
prevented removing any old pod until the new one was ready — a true
deadlock with no path forward.
**Fix:** Changed `maxUnavailable` from 0 to 1 — both as a live patch
to unblock immediately, and committed permanently to deployment.yaml
so ArgoCD's selfHeal would not recreate the same deadlock later:
```bash
kubectl patch deployment aiops-app -n production \
  -p '{"spec":{"strategy":{"rollingUpdate":{"maxUnavailable":1}}}}'
```

## 11. ImagePullBackOff on the newly-scheduled pod
**Problem:** Once the deadlock cleared and the new pod scheduled
successfully, it hit ImagePullBackOff — v1.0.6 was not in that node's
local image cache.
**Fix:** Reloaded the image explicitly and forced only the non-Running
pods to retry:
```bash
minikube image load aiops-app:v1.0.6 --profile aws-eks
kubectl delete pod -n production -l app=aiops-app \
  --field-selector=status.phase!=Running
```

## Final Outcome
Jenkins pipeline worked end to end: tests passed, image built, Trivy
scanned it, GitHub manifest updated automatically. ArgoCD detected the
change, recovered from a real Minikube networking outage, and
successfully deployed v1.0.6 across all 3 nodes. Final state verified:
`Sync Status: Synced`, `Health Status: Healthy`, all 3 pods Running.

**One sentence summary:** Day 7 required diagnosing and fixing eleven
distinct issues spanning pipeline configuration, Git synchronization,
Kubernetes RBAC, a full Minikube network outage, a scheduling deadlock,
and a stale image cache — ending with a fully verified, self-healing,
end-to-end pipeline from a single `git push` to a running pod.

