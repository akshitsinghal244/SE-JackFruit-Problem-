# Sprint plan vs repository (what is implemented, what is process work)

"Code" = in this repo. "Process" = done in Jira/GitHub/DockerHub by the team (cannot be generated).

| Story | Result | Where |
|---|---|---|
| US-01 Repo, branching, Jira link | Files ready; **process:** create repo, apply protection (`scripts/protect-main.sh`), install GitHub for Jira, set real usernames in `.github/CODEOWNERS` | `.github/`, `CONTRIBUTING.md` |
| US-02 CI | Code | `.github/workflows/ci.yml` |
| US-03 Docker + compose | Code | `*/Dockerfile`, `docker-compose.yml` |
| US-04..07 data + ML/DL/QML | Code (teammate's models, 22 tests pass); **process:** download Kaggle data, train, fill `services/artifacts/*` | `services/` |
| US-08 gateway skeleton, US-09 auth, US-10 orchestrator | Code | `gateway/` |
| US-11..13 client scaffold, form, cards | Code | `client/` |
| US-14 demo video, tag v0.1.0 | **Process** (script in `docs/demo/README.md`) | |
| US-15/16 model evaluation | **Process:** train; `python scripts/make_models_md.py` writes `docs/models.md` | `scripts/make_models_md.py` |
| US-17 resilience | Code + tests (207, 502/504, breaker, one connect-retry, `history_saved`) | `gateway/app/services.py` |
| US-18 consensus, charts, model info | Code | `gateway`, `client` |
| US-19 history + CSV | Code (incl. other-user record -> 404) | `gateway/app/routers/history.py` |
| US-20 RBAC, lockout, rate limit | Code + tests (rate limit shared via Redis) | `gateway` |
| US-21 audit, CORS, headers, API key | Code (90-day purge implemented) | `gateway`, `services/shared/service.py` |
| US-22 admin health + users | Code | `gateway`, `client/src/pages/Admin.jsx` |
| US-23 TLS | Code: `scripts/gen-cert.sh`, `nginx/edge.conf`; test: `curl -k https://localhost/api/v1/health` | |
| US-24 responsive, dark mode | Code; **process:** browser smoke test + 5-user trial (`docs/usability.md`) | `client` |
| US-25 CD to DockerHub | Workflow ready; **process:** DockerHub repos + `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` secrets | `.github/workflows/cd.yml` |
| US-26 Kubernetes manifests | Code (+ dry-run job in CI) | `k8s/` |
| US-27 deploy from DockerHub | Scripts ready: `k8s/deploy-dockerhub.sh <user>`; **process:** run on kind, record self-heal demo | `k8s/` |
| US-28 coverage + load test | Coverage enforced in CI (gateway 92 %, services 90 % without torch tests); Locust script ready; **process:** run 10 min and fill `docs/perf/` | `loadtest/` |
| US-29 documentation | README, user guide, OpenAPI export, deviation log, architecture; **process:** screenshots | `docs/` |
| US-30 release | **Process:** tag v1.0.0, freeze (`scripts/protect-main.sh <repo> --freeze`), video | |
