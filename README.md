# RDCP - Retail Demand Category Predictor

Three-tier system: **web client** (React) -> **web server / gateway** (FastAPI) -> **ML, DL, QML microservices**. Enter a store, item, date and the last 7 days of sales; three independent models predict Low / Medium / High demand, shown side by side with their accuracy and a consensus.

```
client/        React SPA (nginx)            gateway/    FastAPI: auth, validation, orchestrator, history, admin, audit
services/      ML / DL / QML model services (+ training code, tests)               mock-models/  same API, for demos
k8s/           Kubernetes manifests + deploy scripts     nginx/ scripts/ loadtest/    TLS edge, helpers, Locust
docs/          user guide, deviations, OpenAPI, perf, demo      .github/   CI, CD, PR template, CODEOWNERS
```
Details: `docs/architecture.md`, `docs/plan-status.md` (sprint-plan coverage), `services/README.md` (training the models).

## 1. Run with Docker Compose
```bash
./scripts/gen-cert.sh                 # self-signed certificate for https://localhost
cp .env.example .env                  # change the secrets
docker compose up -d --build --wait   # real models: needs services/artifacts/{ml,dl,qml} (train first, see services/README.md)
# no trained models yet? use mock services (same API):
docker compose -f docker-compose.yml -f docker-compose.mock.yml up -d --build --wait
```
Open **https://localhost** (accept the certificate warning). Admin: `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`.
Only `edge` publishes ports; models, database and Redis are on the internal network. `scripts/measure_startup.sh` measures time to ready (target <= 120 s).

## 2. Run on Kubernetes (multiple pods)
Replicas: client 2, gateway 3 (HPA 3-8), ml/dl/qml 2 each, postgres 1, redis 1.
```bash
mkdir -p services/artifacts/{ml,dl,qml}
kind create cluster --name rdcp --config k8s/kind-cluster.yaml      # 3 nodes; install Calico + ingress-nginx
./k8s/deploy.sh --mock --cluster kind                               # local images, mock models
./k8s/deploy.sh --cluster kind                                      # local images, real models
./k8s/deploy-dockerhub.sh <dockerhub-user> [tag]                    # images pushed by CD
kubectl -n rdcp port-forward svc/client 8080:80                     # http://localhost:8080  (or Ingress: rdcp.local)
```
Demo: `kubectl -n rdcp get pods -o wide` | `kubectl -n rdcp delete pod -l app=ml` (partial result, pod self-heals) | `kubectl -n rdcp scale deploy/gateway --replicas=5` | mock only: `kubectl -n rdcp set env deploy/qml MOCK_FAIL=down`. The Predict page footer shows which gateway pod served the request.
NetworkPolicies need a CNI that enforces them (Calico/Cilium).

## 3. Develop and test
```bash
cd gateway  && pip install -r requirements-dev.txt && ruff check . && pytest        # 18 tests, coverage >= 70 % enforced
cd services && pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements/dev.txt && pytest -q
cd client   && npm ci && npm run lint && npm run build && npm run dev              # http://localhost:5173 (proxies /api to :8000)
python scripts/export_openapi.py                                                    # refresh docs/openapi.json
```
Local without Docker: run mock models on 8001-8003 (`MODEL_NAME=ml SERVICE_API_KEY=dev-key uvicorn app:app --port 8001` in `mock-models/`, same for dl/qml) and the gateway with `RDCP_DEV=1 SERVICE_API_KEY=dev-key uvicorn app.main:app` in `gateway/` (SQLite).

## 4. CI / CD
- **CI** (`.github/workflows/ci.yml`, every PR and push to main): lint + tests + coverage for gateway and services, client lint + build, docker build of all 5 images, Kubernetes dry-run, compose config.
- **CD** (`cd.yml`): after CI is green on main and on `v*` tags, pushes `<user>/rdcp-{client,gateway,ml,dl,qml}:<sha|latest|tag>` to DockerHub. Needs secrets `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
- Branch protection: `scripts/protect-main.sh <owner/repo>`; freeze at release: add `--freeze`.

## 5. Load test
`pip install locust && locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 10m --host https://localhost --csv docs/perf/run` (see `docs/perf/README.md`).
