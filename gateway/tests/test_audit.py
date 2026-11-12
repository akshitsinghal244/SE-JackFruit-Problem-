"""TC-18 (SEC-09, SEC-10): audit rows for every security-relevant action, CORS allow-list, security headers."""
from app import db
from app.config import settings

from .conftest import GOOD, A, register_login


def actions(rows):
    return {r["action"] for r in rows}


def test_audit_rows_cover_login_failure_predict_export_and_admin(client, user_h, admin_h):
    client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "nope"})      # failed login
    client.post(f"{A}/predict", json=GOOD, headers=user_h)                                # predict
    client.get(f"{A}/history/export", headers=user_h)                                     # export
    other = register_login(client, "eve", "eve@x.com")
    me = client.get(f"{A}/auth/me", headers=other).json()["id"]
    client.patch(f"{A}/admin/users/{me}", json={"is_active": False}, headers=admin_h)     # admin action
    rows = client.get(f"{A}/admin/audit", headers=admin_h).json()

    assert rows, "audit log is empty"
    for r in rows:                                        # SEC-09: user, action, timestamp, IP, outcome
        assert r["action"] and r["outcome"] and r["ip"] != "" and r["created_at"]
        assert r["created_at"].endswith("Z")
    assert {"REGISTER", "LOGIN", "PREDICT", "EXPORT", "ADMIN_DISABLE"} <= actions(rows)
    assert any(r["action"] == "LOGIN" and r["outcome"] == "failure" for r in rows)
    assert any(r["action"] == "LOGIN" and r["outcome"] == "success" for r in rows)


def test_audit_rows_are_attributed_to_the_acting_user(client, user_h, admin_h):
    me = client.get(f"{A}/auth/me", headers=user_h).json()
    client.post(f"{A}/predict", json=GOOD, headers=user_h)
    rows = client.get(f"{A}/admin/audit?limit=50", headers=admin_h).json()
    mine = [r for r in rows if r["action"] == "PREDICT"]
    assert mine and all(r["user_id"] == me["id"] for r in mine)


def test_security_headers_are_present(client):
    """SEC-10: HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy."""
    r = client.get(f"{A}/health")
    h = r.headers
    assert h["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in h["content-security-policy"]
    assert h["x-request-id"]                                          # request correlation


def test_cors_allow_list_blocks_foreign_origins(client):
    allowed = settings.cors[0]
    ok = client.get(f"{A}/health", headers={"Origin": allowed})
    assert ok.headers.get("access-control-allow-origin") == allowed
    evil = client.get(f"{A}/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in evil.headers
    # pre-flight from a foreign origin is not allowed either
    pre = client.options(f"{A}/predict", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in pre.headers


def test_options_preflight_from_the_client_origin_is_allowed(client):
    r = client.options(f"{A}/predict", headers={"Origin": settings.cors[0],
                                               "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == settings.cors[0]


def test_error_bodies_never_leak_internals(client, user_h):
    """SADS 3.4: no stack traces, SQL or hostnames in any response."""
    r = client.post(f"{A}/predict", content="{not json", headers={**user_h, "Content-Type": "application/json"})
    assert r.status_code == 400
    body = r.text.lower()
    for leak in ("traceback", "sqlalchemy", "sqlite", "http://ml", "hostname"):
        assert leak not in body
    err = r.json()["error"]
    assert err["code"] and err["request_id"]
