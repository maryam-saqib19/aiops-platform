
## Multi-node Minikube CNI issue (Day 4)

**Symptom:** Worker nodes added to a Minikube cluster with `--cni=bridge`
remained `NotReady` indefinitely with error:
`network plugin is not ready: cni config uninitialized`

**Root cause:** The `bridge` CNI plugin on Minikube's docker driver only
correctly writes its configuration file to the control-plane node. Worker
nodes joining afterward never receive a valid CNI config, so kubelet
cannot mark them Ready.

**Fix:** Recreate the cluster using `--cni=kindnet` instead of `--cni=bridge`.
kindnet is the CNI Minikube uses for genuine multi-node Docker-driver
clusters and correctly propagates configuration to every node.

```bash
minikube delete --profile aws-eks
minikube start --profile aws-eks --cpus=2 --memory=2200 \
  --driver=docker --cni=kindnet --nodes=3 --wait=all
```

**Verification:** `kubectl get nodes` showed all 3 nodes Ready within
4 minutes, with no further CNI errors on rollout.

## Metrics Server missing on Minikube (Day 4)

**Symptom:** `kubectl get hpa` showed `cpu: <unknown>/70%` indefinitely.
HPA object was correctly configured but had no live metrics to read.

**Root cause:** Minikube does not install the Kubernetes Metrics Server
by default. The HPA controller requires it to read pod CPU/memory usage.

**Fix:**
```bash
minikube addons enable metrics-server --profile aws-eks
```

**Verification:** After ~60 seconds, `kubectl get hpa` showed real
percentage values instead of `<unknown>`.

## Rollout deadlock from anti-affinity + maxUnavailable:0 (Day 7)

**Symptom:** Jenkins-triggered deployment of v1.0.6 stuck in
`ProgressDeadlineExceeded` for 16+ minutes. New pod stuck `Pending`
indefinitely with no node assigned.

**Root cause:** Hard pod anti-affinity (one aiops-app pod per node)
combined with exactly 3 nodes and 3 replicas left zero spare capacity.
`maxUnavailable: 0` prevented removing any old pod until the new pod
was ready — but the new pod could never schedule because all 3 nodes
already held an old pod and anti-affinity blocked sharing.

**Fix:** Changed `maxUnavailable` from 0 to 1 in deployment.yaml,
allowing one old pod to terminate first and free a node for the new
pod to land on.

**Secondary issue:** After the deadlock cleared, one pod showed
`ImagePullBackOff` because the new image had not been loaded onto
that specific node's image cache. Fixed with:
```bash
minikube image load aiops-app:v1.0.6 --profile aws-eks
kubectl delete pod -n production -l app=aiops-app --field-selector=status.phase!=Running
```

**Lesson:** True zero-downtime rolling updates with strict pod
anti-affinity require N+1 nodes relative to replica count, not just N.
