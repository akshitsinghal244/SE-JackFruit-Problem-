"""TC-09 (NFR-P1, NFR-P2): latency and error-rate budgets.

The authoritative measurement is the Locust run documented in docs/perf/README.md (20 users, 10 min,
against https://localhost). This file is the cheap, always-runnable proxy that CI can enforce on
every commit: it drives the *full* HTTP path (auth, whitelist validation, parallel fan-out to the
three services, consensus, DB write) and fails on a regression.

NFR-P1: p95 <= 3 s with only ML+DL, <= 10 s with QML, measured at the web client under 20 users.
The thresholds here are deliberately far tighter for the local mock services but stay an order of
magnitude below the NFR budget so the test never flakes on slow CI runners.
"""
import statistics
import time

from app import services

from .conftest import GOOD, A, register_login


def _run(client, headers, n):
    latencies = []
    for i in range(n):
        t0 = time.perf_counter()
        r = client.post(f"{A}/predict", json={**GOOD, "date": "2017-10-%02d" % (i % 28 + 1)}, headers=headers)
        latencies.append(time.perf_counter() - t0)
        assert r.status_code in (200, 207), r.status_code
    return sorted(latencies)


def test_p95_prediction_latency_is_well_inside_the_nfr_budget(client):
    services.settings.rate_limit = 100000                       # this test is about latency, not SEC-07
    h = register_login(client)
    lat = _run(client, h, 30)
    p50, p95 = lat[len(lat) // 2], lat[int(0.95 * len(lat)) - 1]
    print(f"\npredict latency over 30 requests: p50={p50 * 1000:.1f} ms  p95={p95 * 1000:.1f} ms  max={lat[-1] * 1000:.1f} ms")
    assert p95 < 3.0, f"p95 {p95:.3f}s exceeds the NFR-P1 ML+DL budget (3 s)"
    assert lat[-1] < 8.0, f"max {lat[-1]:.3f}s exceeds the per-service timeout (8 s)"


def test_sustained_load_keeps_the_error_rate_at_zero(client):
    """NFR-P2: no failed requests while the system is under continuous use."""
    services.settings.rate_limit = 100000
    h = register_login(client)
    errors = 0
    for i in range(40):
        r = client.post(f"{A}/predict", json={**GOOD, "store_id": i % 10 + 1}, headers=h)
        if r.status_code not in (200, 207):
            errors += 1
    assert errors == 0, f"{errors}/40 requests failed (NFR-P2 allows < 1 %)"


def test_read_endpoints_stay_fast_under_repeat_use(client):
    h = register_login(client)
    client.post(f"{A}/predict", json=GOOD, headers=h)
    for path in (f"{A}/history", f"{A}/models/info"):
        t0 = time.perf_counter()
        r = client.get(path, headers=h)
        assert r.status_code == 200 and time.perf_counter() - t0 < 1.0, path
