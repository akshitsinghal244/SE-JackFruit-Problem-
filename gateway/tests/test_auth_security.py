"""TC-13 (SEC-03, SEC-04), TC-15 (SEC-02, SEC-06), TC-16 (SEC-01, SEC-08).

Input-injection, token/role and password-storage cases from STP Appendix A.
Missing/tampered tokens and admin RBAC are covered in tests/test_api.py; this file
adds the expired-token, plaintext-password and lockout-duration checks.
"""
import datetime as dt
import os

import jwt
from sqlalchemy import func, select

from app import db
from app.config import settings
from app.models import Prediction, User

from .conftest import GOOD, A, register_login


def fresh_settings():
    """Settings built without the test overrides, to check the *production* defaults."""
    from app.config import Settings

    saved = os.environ.pop("BCRYPT_COST", None)
    try:
        return Settings()
    finally:
        if saved is not None:
            os.environ["BCRYPT_COST"] = saved


# ------------------------------------------------------------------------- TC-13
SQLI = ["' OR 1=1 --", "1'; DROP TABLE users; --", "admin'--", "\" OR \"\"=\""]
XSS = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "javascript:alert(1)"]


def test_login_with_sqli_and_xss_payloads_never_authenticates(client, user_h):
    for payload in SQLI + XSS:                                   # FR-02/SEC-03: generic failure only
        r = client.post(f"{A}/auth/login", json={"email": payload, "password": "Passw0rdA"})
        assert r.status_code in (401, 422), (payload, r.status_code)
        assert "DROP" not in r.text and "script" not in r.text   # nothing echoed back


def test_register_rejects_injection_in_email_and_username(client):
    for body in ({"username": "a' OR '1'='1", "email": "ok@x.com"},
                 {"username": "<script>", "email": "ok2@x.com"},
                 {"username": "goodname", "email": "x' OR '1'='1@x.com"}):
        r = client.post(f"{A}/auth/register", json={**body, "password": "Passw0rdA"})
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR", body


def test_injection_in_prediction_fields_is_422_and_tables_are_untouched(client, user_h):
    s = db.SessionLocal()
    users, preds = s.scalar(select(func.count(User.id))), s.scalar(select(func.count(Prediction.id)))
    s.close()
    for patch in ({"store_id": "1; DROP TABLE users"},
                  {"item_id": "<script>alert(1)</script>"},
                  {"prev_sales": ["1; DELETE FROM predictions"] + [1] * 6},
                  {"date": "2017-09-15' OR '1'='1"}):
        r = client.post(f"{A}/predict", json={**GOOD, **patch}, headers=user_h)
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR", patch
    s = db.SessionLocal()                                        # SEC-04: parameterised queries -> no effect
    assert s.scalar(select(func.count(User.id))) == users
    assert s.scalar(select(func.count(Prediction.id))) == preds
    s.close()


def test_extra_unknown_fields_are_rejected(client, user_h):
    """SEC-03: whitelist, so unexpected fields cannot smuggle data into the models."""
    r = client.post(f"{A}/predict", json={**GOOD, "is_admin": True}, headers=user_h)
    assert r.status_code == 422
    assert client.post(f"{A}/auth/register", json={"username": "abcdef", "email": "f@x.com",
                                                   "password": "Passw0rdA", "role": "admin"}).status_code == 422


# ------------------------------------------------------------------------- TC-15
def test_expired_token_returns_401_token_expired(client, user_h):
    uid = client.get(f"{A}/auth/me", headers=user_h).json()["id"]
    exp = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
    old = jwt.encode({"sub": str(uid), "role": "user", "exp": exp}, settings.jwt_secret, algorithm="HS256")
    r = client.get(f"{A}/auth/me", headers={"Authorization": f"Bearer {old}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "TOKEN_EXPIRED"     # SEC-02: 15-min tokens
    assert client.post(f"{A}/predict", json=GOOD, headers={"Authorization": f"Bearer {old}"}).status_code == 401


def test_token_signed_with_another_secret_is_rejected(client, user_h):
    uid = client.get(f"{A}/auth/me", headers=user_h).json()["id"]
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)
    forged = jwt.encode({"sub": str(uid), "role": "admin", "exp": exp}, "not-the-server-secret", algorithm="HS256")
    r = client.get(f"{A}/admin/users", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "AUTH_INVALID"


def test_admin_endpoints_reject_non_admin_tokens(client, user_h):
    for path in (f"{A}/admin/users", f"{A}/admin/health", f"{A}/admin/audit"):
        assert client.get(path, headers=user_h).status_code == 403               # SEC-06


def test_user_cannot_read_another_users_prediction(client, user_h):
    other = register_login(client, "eve", "eve@x.com")
    pid = client.post(f"{A}/predict", json=GOOD, headers=user_h).json()["id"]
    assert client.get(f"{A}/history/{pid}", headers=other).status_code == 404    # IDOR looks like "not found"


# ------------------------------------------------------------------------- TC-16
def test_password_is_stored_as_bcrypt_only(client):
    from app.security import verify_password

    assert fresh_settings().bcrypt_cost >= 12                                       # SEC-01 default
    client.post(f"{A}/auth/register", json={"username": "hashme", "email": "hashme@x.com", "password": "Passw0rdA"})
    s = db.SessionLocal()
    u = s.scalar(select(User).where(User.email == "hashme@x.com"))
    s.close()
    assert u.password_hash.startswith("$2b$") and f"${settings.bcrypt_cost:02d}$" in u.password_hash
    assert "Passw0rdA" not in u.password_hash and u.password_hash != "Passw0rdA"
    assert verify_password("Passw0rdA", u.password_hash) and not verify_password("wrong", u.password_hash)


def test_lockout_last_15_minutes_and_blocks_the_right_password(client):
    register_login(client, "lockme", "lockme@x.com", "Passw0rdA")
    for _ in range(5):                                                             # SEC-08: 5 failures
        assert client.post(f"{A}/auth/login", json={"email": "lockme@x.com", "password": "wrong"}).status_code == 401
    s = db.SessionLocal()
    u = s.scalar(select(User).where(User.email == "lockme@x.com"))
    minutes = (u.locked_until - db.utcnow()).total_seconds() / 60
    assert 14 <= minutes <= 15.5, minutes                                          # locked for ~15 min
    s.close()
    r = client.post(f"{A}/auth/login", json={"email": "lockme@x.com", "password": "Passw0rdA"})
    assert r.status_code == 423 and r.json()["error"]["code"] == "ACCOUNT_LOCKED"  # correct pwd still refused


def test_successful_login_clears_the_failure_counter(client):
    register_login(client, "ana", "ana@x.com", "Passw0rdA")
    client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "wrong"})
    assert client.post(f"{A}/auth/login", json={"email": "ana@x.com", "password": "Passw0rdA"}).status_code == 200
    s = db.SessionLocal()
    u = s.scalar(select(User).where(User.email == "ana@x.com"))
    assert u.failed_attempts == 0 and u.locked_until is None
    s.close()
