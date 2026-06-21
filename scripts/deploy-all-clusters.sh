#!/bin/bash
# ============================================================
# Deploy to all three clusters in sequence
# Proves the GitOps principle: one source of truth, identical
# deployments everywhere
# ============================================================
set -e
# set -e means: stop immediately if any command fails

MANIFESTS_DIR="$HOME/aiops-platform/kubernetes"
CLUSTERS=("aws-eks" "azure-aks" "gcp-gke")

echo "========================================"
echo "AIOps Platform — Multi-Cloud Deployment"
echo "========================================"

for ctx in "${CLUSTERS[@]}"; do
  echo ""
  echo "--- Deploying to: $ctx ---"
  kubectl config use-context $ctx

  # Make sure the image is loaded
  if ! minikube image ls --profile $ctx 2>/dev/null | grep -q aiops-app; then
    echo "Loading image into $ctx..."
    minikube image load aiops-app:v1.0.0 --profile $ctx
  fi

  # Apply pod security standard first
  kubectl apply -f $MANIFESTS_DIR/namespaces/pod-security.yaml

  # Deploy the application
  kubectl apply -f $MANIFESTS_DIR/apps/deployment.yaml
  kubectl apply -f $MANIFESTS_DIR/apps/service.yaml

  echo "--- Waiting for $ctx rollout ---"
  kubectl rollout status deployment/aiops-app \
    --namespace production \
    --timeout=120s

  echo "--- $ctx: Pod status ---"
  kubectl get pods --namespace production -o wide \
    --no-headers | grep aiops-app
done

echo ""
echo "========================================"
echo "Deployment complete across all clusters"
echo "========================================"

for ctx in "${CLUSTERS[@]}"; do
  kubectl config use-context $ctx
  RUNNING=$(kubectl get pods -n production \
    -l app=aiops-app \
    --field-selector=status.phase=Running \
    --no-headers 2>/dev/null | wc -l)
  echo "$ctx: $RUNNING/3 pods running"
done
