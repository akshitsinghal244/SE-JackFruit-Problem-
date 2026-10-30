import os

from app import ratelimit
from app.config import settings

from .conftest import GOOD, register_login

A = "/api/v1"


def test_register_login_and_policy(client):
    r = client.post(f"{A}/auth/register", json={"username": "bob", "email": "bob@x.com", "password": "weak"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    h = register_login(client)
    assert client.get(f"{A}/auth/me", headers=h).json()["email"] == "ana@x.com"
    dup = client.post(f"{A}/auth/register", json={"username": "ana2", "email": "ana@x.com", "password": "Passw0rdA"})
    assert dup.status_code == 422


def test_login_generic_error_and_lockout(client, user_h):
    bad = client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "nope"})
    unknown = client.post(f"{A}/auth/login", json={"email": "ghost@x.com", "password": "nope"})
    assert bad.status_code == unknown.status_code == 401 and bad.json()["error"]["message"] == unknown.json()["error"]["message"]
    for _ in range(4):
        client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "nope"})
    locked = client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "Passw0rdA"})
    assert locked.status_code == 423 and locked.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_auth_required_and_tampered_token(client, user_h):
    assert client.post(f"{A}/predict", json=GOOD).status_code == 401
    r = client.post(f"{A}/predict", json=GOOD, headers={"Authorization": "Bearer " + user_h["Authorization"][7:-3] + "abc"})
    assert r.status_code == 401


def test_predict_ok_all_three_and_consensus(client, user_h):
    r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert set(j["results"]) == {"ml", "dl", "qml"} and all(v["status"] == "ok" and "accuracy" in v for v in j["results"].values())
    assert j["consensus"] in {"Low", "Medium", "High", "No consensus"} and j["history_saved"]


def test_validation_boundaries(client, user_h):
    cases = [dict(GOOD, store_id=0), dict(GOOD, store_id=11), dict(GOOD, item_id=51), dict(GOOD, date="2031-01-01"),
             dict(GOOD, prev_sales=[-1, 1, 1, 1, 1, 1, 1]), dict(GOOD, prev_sales=[501] + [1] * 6), dict(GOOD, prev_sales=["abc"] + [1] * 6),
             dict(GOOD, prev_sales=[1] * 6), dict(GOOD, extra="x"), dict(GOOD, store_id="1; DROP TABLE users")]
    for c in cases:
        r = client.post(f"{A}/predict", json=c, headers=user_h)
        assert r.status_code == 422 and r.json()["error"]["details"], c
    assert client.post(f"{A}/predict", content="{bad", headers={**user_h, "Content-Type": "application/json"}).status_code == 400


def test_partial_failure_returns_207(client, user_h):
    try:
        from app import services
        orig = services._call

        async def flaky(name, *a, **k):
            if name == "qml":
                return services._err("SVC_TIMEOUT", "Model service timed out")
            return await orig(name, *a, **k)
        services._call = flaky
        r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    finally:
        services._call = orig
        os.environ["MOCK_FAIL"] = "none"
    assert r.status_code == 207
    j = r.json()
    assert j["results"]["qml"]["code"] == "SVC_TIMEOUT" and j["results"]["ml"]["status"] == "ok"


def test_all_services_down_502(client, user_h):
    os.environ["MOCK_FAIL"] = "down"
    try:
        r = client.post(f"{A}/predict", json=GOOD, headers=user_h)
    finally:
        os.environ["MOCK_FAIL"] = "none"
    assert r.status_code == 502 and r.json()["error"]["code"] == "ALL_SERVICES_DOWN"


def test_unknown_store_item_from_models_is_422(client, user_h):
    # server allows 1-10/1-50, so force the models' own check through the orchestrator
    import asyncio

    from app import services
    res = asyncio.run(services.predict(dict(GOOD, store_id=99), "t"))
    assert all(v["code"] == "VALIDATION_ERROR" for v in res.values())


def test_history_own_only_and_csv(client, user_h):
    other = register_login(client, "eve", "eve@x.com")
    client.post(f"{A}/predict", json=GOOD, headers=user_h)
    client.post(f"{A}/predict", json=GOOD, headers=user_h)
    client.post(f"{A}/predict", json=dict(GOOD, store_id=4), headers=other)
    h = client.get(f"{A}/history", headers=user_h).json()
    assert len(h) == 2 and h[0]["id"] > h[1]["id"]
    csv_ = client.get(f"{A}/history/export", headers=user_h)
    assert csv_.headers["content-type"].startswith("text/csv") and csv_.text.count("\n") == 3


def test_rbac_and_admin_functions(client, user_h, admin_h):
    assert client.get(f"{A}/admin/users", headers=user_h).status_code == 403
    assert client.get(f"{A}/admin/health", headers=user_h).status_code == 403
    health = client.get(f"{A}/admin/health?refresh=true", headers=admin_h).json()
    assert {h["service"]: h["status"] for h in health} == {"ml": "UP", "dl": "UP", "qml": "UP"}
    users = client.get(f"{A}/admin/users", headers=admin_h).json()
    uid = next(u["id"] for u in users if u["email"] == "ana@x.com")
    assert client.patch(f"{A}/admin/users/{uid}", json={"is_active": False}, headers=admin_h).json()["is_active"] is False
    assert client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "Passw0rdA"}).json()["error"]["code"] == "ACCOUNT_DISABLED"
    me = next(u["id"] for u in users if u["role"] == "admin")
    assert client.patch(f"{A}/admin/users/{me}", json={"is_active": False}, headers=admin_h).status_code == 422
    actions = {a["action"] for a in client.get(f"{A}/admin/audit", headers=admin_h).json()}
    assert {"LOGIN", "REGISTER", "ADMIN_DISABLE"} <= actions


def test_rate_limit_429(client, user_h):
    settings.rate_limit = 5
    ratelimit.reset()
    codes = [client.get(f"{A}/auth/me", headers=user_h).status_code for _ in range(7)]
    assert codes[:5] == [200] * 5 and codes[5] == 429
    r = client.get(f"{A}/auth/me", headers=user_h)
    assert "retry-after" in r.headers


def test_security_headers_and_cors(client):
    r = client.get("/healthz", headers={"Origin": "http://evil.example"})
    assert r.headers["x-content-type-options"] == "nosniff" and "strict-transport-security" in r.headers
    assert "access-control-allow-origin" not in r.headers
    assert client.get("/readyz").status_code == 200
    assert client.get("/nope").json()["error"]["code"] == "NOT_FOUND"


def test_models_info(client, user_h):
    info = client.get(f"{A}/models/info", headers=user_h).json()
    assert [m["model"] for m in info] == ["ml", "dl", "qml"] and all("accuracy" in m for m in info)


def test_history_item_ownership_404(client, user_h):
    other = register_login(client, "eve", "eve@x.com")
    pid = client.post(f"{A}/predict", json=GOOD, headers=user_h).json()["id"]
    assert client.get(f"{A}/history/{pid}", headers=user_h).json()["id"] == pid
    assert client.get(f"{A}/history/{pid}", headers=other).status_code == 404       # other user's record
    assert client.get(f"{A}/history/99999", headers=user_h).status_code == 404
    assert client.get(f"{A}/history/export", headers=user_h).status_code == 200        # route order: export is not an id


def test_public_health_and_openapi(client):
    assert client.get(f"{A}/health").json()["status"] == "ok"
    spec = client.get(f"{A}/openapi.json").json()
    assert "/api/v1/predict" in spec["paths"]


def test_audit_retention_purges_old_rows(client, user_h):
    import datetime as dt

    from app import db
    from app.main import purge_audit
    from app.models import AuditLog
    s = db.SessionLocal()
    s.add(AuditLog(user_id=1, action="OLD", ip="", outcome="x", created_at=db.utcnow() - dt.timedelta(days=91)))
    s.add(AuditLog(user_id=1, action="NEW", ip="", outcome="x", created_at=db.utcnow() - dt.timedelta(days=89)))
    s.commit()
    assert purge_audit() == 1
    left = {a.action for a in s.query(AuditLog).all()}
    s.close()
    assert "OLD" not in left and "NEW" in left


def test_connect_error_retried_once_but_timeout_not(client):
    import asyncio

    import httpx

    from app import services

    calls = {"n": 0}

    class Flaky(httpx.AsyncBaseTransport):
        def __init__(self, exc, ok_after):
            self.exc, self.ok_after = exc, ok_after

        async def handle_async_request(self, request):
            calls["n"] += 1
            if calls["n"] <= self.ok_after:
                raise self.exc
            return httpx.Response(200, json={"category": "Low"})

    services.set_client(httpx.AsyncClient(transport=Flaky(httpx.ConnectError("boom"), 1)))
    r = asyncio.run(services._call("ml", "POST", "/predict", "t", json={}))
    assert r["status"] == "ok" and calls["n"] == 2                                  # failed once, retried, succeeded
    calls["n"] = 0
    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Flaky(httpx.ReadTimeout("slow"), 5)))
    r = asyncio.run(services._call("ml", "POST", "/predict", "t", json={}))
    assert r["code"] == "SVC_TIMEOUT" and calls["n"] == 1                           # timeouts are never retried


def test_circuit_breaker_opens_after_three_failures(client):
    import asyncio

    import httpx

    from app import services
    hits = {"n": 0}

    class Dead(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            hits["n"] += 1
            return httpx.Response(503, json={})

    services.reset_breakers()
    services.set_client(httpx.AsyncClient(transport=Dead()))
    for _ in range(3):
        asyncio.run(services._call("dl", "POST", "/predict", "t", json={}))
    before = hits["n"]
    r = asyncio.run(services._call("dl", "POST", "/predict", "t", json={}))
    assert r["code"] == "SVC_UNAVAILABLE" and hits["n"] == before                    # skipped while breaker is open
