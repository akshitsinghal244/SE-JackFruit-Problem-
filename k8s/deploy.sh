#!/usr/bin/env bash
# Local build + deploy (images loaded straight into kind/minikube).  For DockerHub images use deploy-dockerhub.sh.
#   ./k8s/deploy.sh --mock  [--cluster kind|minikube]     # demo with mock model services
#   ./k8s/deploy.sh         [--cluster kind|minikube]     # real models: services/artifacts/{ml,dl,qml} must be trained
set -euo pipefail
cd "$(dirname "$0")/.."
MOCK=0; CLUSTER=kind
while [[ $# -gt 0 ]]; do case $1 in --mock) MOCK=1;; --cluster) CLUSTER=$2; shift;; *) echo "unknown arg $1"; exit 1;; esac; shift; done
load() { case $CLUSTER in kind) kind load docker-image --name rdcp "$1";; minikube) minikube image load "$1";; *) echo "unknown cluster $CLUSTER"; exit 1;; esac; }

echo "==> building images"
docker build -t rdcp-gateway:1.0 gateway
docker build -t rdcp-client:1.0 client
IMAGES=(rdcp-gateway:1.0 rdcp-client:1.0)
if [[ $MOCK == 1 ]]; then
  docker build -t rdcp-mock-models:1.0 mock-models; IMAGES+=(rdcp-mock-models:1.0); OVERLAY=k8s/overlays/mock
else
  for s in ml dl qml; do
    [[ -f services/artifacts/$s/metadata.json ]] || { echo "missing services/artifacts/$s/metadata.json - train the $s model first, or use --mock"; exit 1; }
    docker build -f "services/${s}_service/Dockerfile" -t "rdcp-$s:1.0" services; IMAGES+=("rdcp-$s:1.0")
  done
  OVERLAY=k8s/base
fi
echo "==> loading images into $CLUSTER"; for i in "${IMAGES[@]}"; do load "$i"; done
source "$(dirname "$0")/common.sh"; create_secret; apply_and_wait "$OVERLAY"
