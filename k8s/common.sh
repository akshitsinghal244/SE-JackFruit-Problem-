# shared helpers for deploy.sh / deploy-dockerhub.sh
create_secret() {
  kubectl apply -f k8s/base/namespace.yaml
  if ! kubectl -n rdcp get secret rdcp-secrets >/dev/null 2>&1; then
    ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -hex 6)Aa1}"
    kubectl -n rdcp create secret generic rdcp-secrets \
      --from-literal=JWT_SECRET="$(openssl rand -hex 32)" --from-literal=SERVICE_API_KEY="$(openssl rand -hex 32)" \
      --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 16)" --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD"
    echo "    admin login: admin@rdcp.local / $ADMIN_PASSWORD   (save it - shown only now)"
  fi
}
apply_and_wait() {
  echo "==> applying $1"; kubectl apply -k "$1"
  for d in ml dl qml gateway client; do kubectl -n rdcp rollout status deploy/$d --timeout=300s; done
  kubectl -n rdcp rollout status statefulset/postgres --timeout=300s
  echo; kubectl -n rdcp get pods,svc -o wide
  cat <<MSG

Open the app:
  * Ingress:      add '127.0.0.1 rdcp.local' to your hosts file -> http://rdcp.local   (needs ingress-nginx)
  * No ingress:   kubectl -n rdcp port-forward svc/client 8080:80   ->  http://localhost:8080
MSG
}
