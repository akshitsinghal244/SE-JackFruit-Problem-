"""TC-06 (FR-14, NFR-R1): partial failure handling.

Each mock model service exposes a `failure()` hook (MOCK_FAIL), so a real container stop can be
simulated in-process: the orchestrator must answer 207 with the two surviving models, still
compute a consensus, still store the prediction - and must not block on the dead one.
"""
import time

from .conftest import GOOD, A, register_login


def down(name):
    """Make one in-process mock service fail like a stopped container would."""
    def failure():
        return True
    failure.__name__ = f"{name}_down"
    return failure


def test_one_service_down_still_returns_the_other_two(client, user_h):
    client.mocks["qml"].failure = down("qml")
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 207                                    # multi-status: partial result
    j = r.json()
    assert j["results"]["qml"]["status"] == "error"
    assert j["results"]["qml"]["code"] == "SVC_UNAVAILABLE"
    assert j["results"]["ml"]["status"] == j["results"]["dl"]["status"] == "ok"
    assert j["consensus"] in {"Low", "Medium", "High", "No consensus"}   # consensus of the survivors
    assert j["history_saved"]                                      # FR-14: prediction is still recorded
    assert client.get(f"{A}/history/{j['id']}", headers=user_h).status_code == 200


def test_two_services_down_leaves_one_valid_card(client, user_h):
    client.mocks["dl"].failure = down("dl")
    client.mocks["qml"].failure = down("qml")
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 207
    ok = [n for n, v in r.json()["results"].items() if v["status"] == "ok"]
    assert ok == ["ml"]
    assert r.json()["consensus"] in {"Low", "Medium", "High", "No consensus"}


def test_all_services_down_is_502_not_an_empty_result(client, user_h):
    for m in client.mocks.values():
        m.failure = down("all")
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "ALL_SERVICES_DOWN"


def test_all_services_timing_out_is_504(client, user_h):
    """All three exceed the 8 s budget -> 504 (a hang is worse than a refusal)."""
    import asyncio

    import httpx

    from app import services

    class Hanging(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            await asyncio.sleep(0.05)
            raise httpx.ReadTimeout("service is too slow")

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Hanging()))
    try:
        r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    finally:
        services.set_client(None)
    assert r.status_code == 504 and r.json()["error"]["code"] == "ALL_SERVICES_DOWN"


def test_one_service_timing_out_is_a_card_error_not_a_page_error(client, user_h):
    import asyncio

    import httpx

    from app import services

    from .conftest import HostRouter

    class Slow(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            if request.url.host == "qml":                       # only QML is over budget
                await asyncio.sleep(0.05)
                raise httpx.ReadTimeout("qml too slow")
            return await self._inner.handle_async_request(request)

    mods = client.mocks
    inner = HostRouter({n: m.app for n, m in mods.items()})
    slow = Slow()
    slow._inner = inner
    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=slow))
    try:
        r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    finally:
        services.set_client(None)
    assert r.status_code == 207
    assert r.json()["results"]["qml"]["code"] == "SVC_TIMEOUT"
    assert r.json()["results"]["ml"]["status"] == "ok"


def test_dead_service_does_not_block_the_live_ones(client, user_h):
    """FR-05/NFR-P1: the dead service's 8 s budget must not add to the caller's latency."""
    client.mocks["qml"].failure = down("qml")
    t0 = time.perf_counter()
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 207
    assert time.perf_counter() - t0 < 3.0, "a dead service blocked the prediction"


def test_breaker_stays_open_for_its_cooldown_then_recovers(client, user_h):
    import httpx

    from app import services

    class Dead(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(503, json={})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Dead()))
    import asyncio

    try:
        for _ in range(3):                                        # 3 consecutive failures -> open
            asyncio.run(services._call("ml", "POST", "/predict", "r", json={}))

        class Alive(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return httpx.Response(200, json={"category": "Low"})

        services.set_client(httpx.AsyncClient(transport=Alive()))
        r = asyncio.run(services._call("ml", "POST", "/predict", "r", json={}))
        assert r["code"] == "SVC_UNAVAILABLE"                     # still skipped during cooldown
        services._breaker["ml"]["open_until"] = 0.0               # cooldown elapsed
        r = asyncio.run(services._call("ml", "POST", "/predict", "r", json={}))
        assert r["status"] == "ok" and services._breaker["ml"]["fails"] == 0
    finally:
        services.set_client(None)


def test_validation_error_from_a_service_is_not_a_service_failure(client, user_h):
    """A 422 from the models means the input was rejected; it must not open the breaker."""
    import asyncio

    import httpx

    from app import services

    class Reject(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(422, json={"error": {"details": [{"field": "store_id", "reason": "unknown store"}]}})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Reject()))
    try:
        for _ in range(5):
            r = asyncio.run(services._call("ml", "POST", "/predict", "r", json={}))
            assert r["code"] == "VALIDATION_ERROR"
        assert services._breaker["ml"]["fails"] == 0 and services._breaker["ml"]["open_until"] == 0.0
    finally:
        services.set_client(None)


def test_connect_error_is_retried_but_a_timeout_never_is(client):
    """US-17/SADS 3.4.1: exactly one retry, and only for connection errors."""
    import asyncio

    import httpx

    from app import services

    calls = {"n": 0}

    class Flaky(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            calls["n"] += 1
            if calls["n"] == 1:
                raise httpx.ConnectError("connection refused")
            return httpx.Response(200, json={"category": "Low"})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Flaky()))
    try:
        r = asyncio.run(services._call("ml", "POST", "/predict", "r", json={}))
        assert r["status"] == "ok" and calls["n"] == 2                       # one retry, then success
    finally:
        services.set_client(None)
