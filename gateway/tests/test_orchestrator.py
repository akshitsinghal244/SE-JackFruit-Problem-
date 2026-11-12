"""TC-05 (FR-08) and TC-03 (FR-05, FR-06, FR-07, FR-09).

Unit-level checks of the orchestrator that do not need HTTP, plus one parallel-call
timing proof for FR-05 ("invoke the ML, DL and QML microservices in parallel").
"""
import time

from app import services

from .conftest import GOOD, A, register_login

ok = lambda cat: {"status": "ok", "category": cat}          # noqa: E731
bad = {"status": "error", "code": "SVC_TIMEOUT"}


def test_consensus_is_a_majority_vote_of_the_models_that_answered():
    assert services.consensus({"ml": ok("Low"), "dl": ok("Low"), "qml": ok("High")}) == "Low"      # 2 of 3
    assert services.consensus({"ml": ok("High"), "dl": ok("High"), "qml": ok("Medium")}) == "High"
    assert services.consensus({"ml": ok("Low"), "dl": ok("Medium"), "qml": ok("High")}) == "No consensus"
    assert services.consensus({"ml": ok("Medium"), "dl": ok("Medium"), "qml": ok("Medium")}) == "Medium"
    # a failed model is not a vote: 2 survivors agreeing is still a consensus
    assert services.consensus({"ml": ok("High"), "dl": bad, "qml": ok("High")}) == "High"
    assert services.consensus({"ml": ok("High"), "dl": bad, "qml": bad}) == "No consensus"
    assert services.consensus({"ml": bad, "dl": bad, "qml": bad}) == "No consensus"


def test_three_services_are_called_in_parallel(client):
    """FR-05/NFR-P1: latency is the slowest service, not the sum of the three."""
    import asyncio

    import httpx

    from app import services

    calls = {"ml": 0, "dl": 0, "qml": 0}
    started = {}

    class Slow(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            host = request.url.host
            calls[host] += 1
            started.setdefault(host, time.perf_counter())
            await asyncio.sleep(0.3)                       # each service is "slow"
            return httpx.Response(200, json={"category": "Low", "probabilities": {}})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Slow()))
    try:
        t0 = time.perf_counter()
        out = asyncio.run(services.predict(GOOD, "rid-par"))
        elapsed = time.perf_counter() - t0
    finally:
        services.set_client(None)

    assert set(out) == {"ml", "dl", "qml"} and all(v["status"] == "ok" for v in out.values())
    assert calls == {"ml": 1, "dl": 1, "qml": 1}          # each service called exactly once
    # 3 x 0.3 s = 0.9 s if serial; allow generous slack for the test runner, still far below the sum
    assert elapsed < 0.8, f"services did not run in parallel: {elapsed:.3f}s for 3 x 0.3 s"


def test_each_result_carries_the_model_contract(client, user_h):
    """FR-06/FR-07: category + confidence + accuracy per model, one card each."""
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 200
    for name, res in r.json()["results"].items():
        assert res["model"] == name
        assert res["category"] in {"Low", "Medium", "High"}
        assert 0 <= res["confidence"] <= 100
        assert set(res["probabilities"]) == {"low", "medium", "high"}
        assert abs(sum(res["probabilities"].values()) - 1) < 0.01     # probabilities normalised
        assert "accuracy" in res and "latency_ms" in res


def test_predict_records_a_row_in_history(client, user_h):
    """FR-10: a successful prediction is stored with its inputs, outputs and consensus."""
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    pid = r.json()["id"]
    row = client.get(f"{A}/history/{pid}", headers=user_h).json()
    assert row["store_id"] == 3 and row["item_id"] == 12 and row["date"] == "2017-09-15"
    assert row["prev_sales"] == GOOD["prev_sales"]
    assert set(row["results"]) == {"ml", "dl", "qml"}
    assert row["consensus"] == r.json()["consensus"]


def test_all_services_unavailable_together_is_not_a_partial_result(client, user_h):
    """US-17: when every service fails the request must fail loudly, not return an empty result."""
    import asyncio

    import httpx

    from app import services

    class Dead(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            return httpx.Response(503, json={})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Dead()))
    try:
        out = asyncio.run(services.predict(GOOD, "rid-all-down"))
    finally:
        services.set_client(None)
    assert all(v["status"] == "error" for v in out.values())
