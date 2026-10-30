# Performance evidence (US-28, NFR-P1, NFR-P2, NFR-D1)

```bash
# 1. start-up time (target <= 120 s)
scripts/measure_startup.sh                         # real models;  add: -f docker-compose.yml -f docker-compose.mock.yml  for mocks
# 2. load: 20 users, 10 minutes, error rate < 1 %, p95 <= 10 s with QML (<= 3 s ML+DL)
pip install locust
locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 10m --host https://localhost --csv docs/perf/run --html docs/perf/run.html
```

| Measure | Target | Result | Date |
|---|---|---|---|
| `docker compose up -d --wait` | <= 120 s | _fill_ | |
| Error rate (10 min, 20 users) | < 1 % | _fill_ | |
| p95 `/predict` (with QML) | <= 10 s | _fill_ | |
| p95 `/predict` (ML+DL only: stop qml first) | <= 3 s | _fill_ | |

A 207 (partial result) counts as success in the test because the system is designed to degrade (FR-14).
Smoke run of the script against mock models (25 s, 20 users): 218 requests, 0 failures, `/predict` p95 56 ms.
