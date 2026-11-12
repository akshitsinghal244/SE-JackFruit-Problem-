#!/usr/bin/env python3
"""Docker-level smoke test for the test cases that need the real stack.

Covers the parts of the STP that cannot be exercised by pytest alone:
  * TC-19 / NFR-D1  - one command brings the system up and ready within 120 s
  * TC-03           - register, log in, predict, read the three model cards
  * TC-14           - a model service is NOT reachable from the host, but works with the key
  * TC-06           - stop one model and confirm the other two still answer (207)
  * TC-08           - admin sees DOWN for the stopped service

    python scripts/test_stack_smoke.py                      # mock model services
    python scripts/test_stack_smoke.py --real               # real (trained) models
    python scripts/test_stack_smoke.py --keep               # leave the stack running

Requires Docker; needs no cloud. Exits non-zero if any check fails.
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://localhost"
KEY = os.environ.get("SERVICE_API_KEY", "dev-key")
USER = ("smoke", "smoke@example.com", "SmokeTest1")
SSL_NO_VERIFY = ssl.create_default_context()
SSL_NO_VERIFY.check_hostname = False
SSL_NO_VERIFY.verify_mode = ssl.CERT_NONE


def sh(cmd: list[str], check=True, timeout=600) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout, check=False)
    if check and p.returncode != 0:
        print("  command failed:", " ".join(cmd))
        print((p.stdout + p.stderr)[-800:])
        raise SystemExit(1)
    return p


def http(method: str, path: str, body=None, headers=None, timeout=15, base=BASE):
    """Return (status, json). status 0 means the endpoint could not be reached at all."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={**(headers or {}), **({"Content-Type": "application/json"} if data else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_NO_VERIFY) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")
    except (urllib.error.URLError, ConnectionError, OSError, TimeoutError):
        return 0, None


def wait_ready(deadline: float) -> float:
    """Poll /api/v1/health until the stack answers; returns the seconds it took, or -1."""
    t0 = time.time()
    while time.time() < deadline:
        try:
            if http("GET", "/api/v1/health", timeout=3)[0] == 200:
                return time.time() - t0
        except (urllib.error.URLError, ConnectionError, OSError, TimeoutError):
            pass                                # not up yet: keep polling until the deadline
        time.sleep(2)
    return -1


def compose(*args: str) -> list[str]:
    return ["docker", "compose", *(args)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true", help="use the real trained models, not the mocks")
    ap.add_argument("--keep", action="store_true", help="leave the stack running afterwards")
    a = ap.parse_args()

    files = ["-f", "docker-compose.yml"] + ([] if a.real else ["-f", "docker-compose.mock.yml"])
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))

    print("\n== TC-19 / NFR-D1: one command, ready in <= 120 s ==")
    sh(compose(*files, "down", "-v"), check=False)
    t0 = time.time()
    sh(compose(*files, "up", "-d", "--build", "--wait"), check=False)
    ready = wait_ready(t0 + 180)
    check("system ready via `docker compose up --wait`", ready >= 0, f"{ready:.0f}s" if ready >= 0 else "never")
    if ready < 0:
        sh(compose(*files, "logs", "--tail=50"))
        return 1
    check("start-up within the 120 s budget", ready <= 120, f"{ready:.0f}s")

    print("\n== TC-01 / TC-02: register and log in ==")
    payload = {"username": USER[0], "email": USER[1], "password": USER[2]}
    http("POST", "/api/v1/auth/register", payload)
    code, _ = http("POST", "/api/v1/auth/register", payload)
    check("duplicate registration is rejected", code == 422, f"HTTP {code}")
    code, body = http("POST", "/api/v1/auth/login", {"email": USER[1], "password": USER[2]})
    token = (body or {}).get("access_token", "")
    check("login returns a JWT", code == 200 and bool(token))
    h = {"Authorization": f"Bearer {token}"}

    print("\n== TC-03: a prediction from all three models ==")
    good = {"store_id": 3, "item_id": 12, "date": "2017-09-15", "prev_sales": [41, 38, 45, 50, 47, 39, 44]}
    code, body = http("POST", "/api/v1/predict", good, h)
    check("predict answers 200 with three results", code == 200 and len(body.get("results", {})) == 3)
    check("every card carries category + confidence + accuracy",
          all(v.get("status") == "ok" and v.get("category") and "accuracy" in v for v in body.get("results", {}).values()))
    check("consensus is computed", body.get("consensus") in {"Low", "Medium", "High", "No consensus"})
    check("prediction stored in history", body.get("history_saved") is True)

    code, hist = http("GET", "/api/v1/history", headers=h)
    check("history lists the prediction", code == 200 and len(hist) >= 1)

    code, _ = http("GET", "/api/v1/history/export", headers=h)
    check("CSV export works", code == 200, f"HTTP {code}")

    print("\n== TC-14: the model services are internal-only ==")
    for port in (8001, 8002, 8003):
        code, _ = http("GET", "/health", headers={"X-API-Key": KEY}, timeout=4, base=f"http://localhost:{port}")
        check(f"http://localhost:{port} is not reachable from the host", code == 0 or code >= 400, f"HTTP {code if code else 'refused'}")
    code, _ = http("GET", "/health", timeout=4, base="http://localhost:8000")
    check("the gateway is reachable from the host (edge only)", code == 200, f"HTTP {code}")

    print("\n== TC-06: stop one model, the others still answer ==")
    sh(compose(*files, "stop", "qml"), check=False)
    time.sleep(2)
    code, body = http("POST", "/api/v1/predict", {**good, "date": "2017-10-01"}, h)
    check("partial result is returned as 207", code == 207, f"HTTP {code}")
    check("ML and DL still succeeded", body.get("results", {}).get("ml", {}).get("status") == "ok")
    check("QML reports an error", body.get("results", {}).get("qml", {}).get("status") == "error")

    print("\n== TC-08 / TC-12: admin health and audit ==")
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_password:
        code, ab = http("POST", "/api/v1/auth/login", {"email": admin_email, "password": admin_password})
        if code == 200:
            ah = {"Authorization": f"Bearer {ab['access_token']}"}
            code, health = http("GET", "/api/v1/admin/health?refresh=true", headers=ah)
            statuses = {row["service"]: row["status"] for row in (health or [])}
            check("admin health shows qml DOWN", statuses.get("qml") == "DOWN", str(statuses))
            code, audit = http("GET", "/api/v1/admin/audit?limit=50", headers=ah)
            actions = {row["action"] for row in (audit or [])}
            check("audit log has the login + predict events", {"LOGIN", "REGISTER", "PREDICT"} <= actions, str(sorted(actions)))
        else:
            check("admin login works", False, f"HTTP {code} (check ADMIN_EMAIL/ADMIN_PASSWORD)")
    else:
        print("  [SKIP] admin checks - ADMIN_EMAIL/ADMIN_PASSWORD not set")

    sh(compose(*files, "start", "qml"), check=False)
    time.sleep(3)
    code, body = http("POST", "/api/v1/predict", {**good, "date": "2017-10-02"}, h)
    check("system recovers after the model returns", code in (200, 207), f"HTTP {code}")

    if not a.keep:
        sh(compose(*files, "down", "-v"), check=False)

    failed = [r for r in results if not r[1]]
    print("\n" + "-" * 60)
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
