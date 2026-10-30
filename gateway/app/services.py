"""Prediction Orchestrator + Health Monitor (SADS 2.4, 3.2, 3.4.1).

* scatter-gather: calls ML, DL, QML concurrently, each with an 8 s timeout (FR-05, NFR-P1)
* partial failure: a dead service never blocks the other two (FR-14)
* circuit breaker: 3 consecutive failures -> skip that service for 30 s
"""
import asyncio
import datetime as dt
import logging
import time
from collections import Counter

import httpx

from .config import settings

log = logging.getLogger("rdcp.services")
NAMES = ["ml", "dl", "qml"]
_client: httpx.AsyncClient | None = None
_breaker = {n: {"fails": 0, "open_until": 0.0} for n in NAMES}
health_cache: dict[str, dict] = {}


def set_client(c: httpx.AsyncClient | None) -> None:
    global _client
    _client = c


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=settings.timeout)
    return _client


def reset_breakers() -> None:
    for b in _breaker.values():
        b.update(fails=0, open_until=0.0)
    health_cache.clear()


def _err(code: str, message: str, details=None) -> dict:
    return {"status": "error", "code": code, "message": message, "details": details or []}


def _record(name: str, ok: bool) -> None:
    b = _breaker[name]
    if ok:
        b["fails"] = 0
        return
    b["fails"] += 1
    if b["fails"] >= settings.breaker_failures:
        b["open_until"] = time.monotonic() + settings.breaker_cooldown


async def _call(name: str, method: str, path: str, rid: str, json=None, use_breaker=True) -> dict:
    if use_breaker and time.monotonic() < _breaker[name]["open_until"]:
        return _err("SVC_UNAVAILABLE", "Service temporarily unavailable")
    url = settings.service_urls[name] + path
    headers = {"X-API-Key": settings.service_api_key, "X-Request-ID": rid}
    try:
        try:
            r = await get_client().request(method, url, json=json, headers=headers, timeout=settings.timeout)
        except httpx.ConnectError:                      # one retry for connection errors only - never for timeouts (US-17)
            r = await get_client().request(method, url, json=json, headers=headers, timeout=settings.timeout)
    except httpx.TimeoutException:
        _record(name, False)
        return _err("SVC_TIMEOUT", "Model service timed out")
    except httpx.HTTPError:
        _record(name, False)
        return _err("SVC_UNAVAILABLE", "Model service unavailable")
    if r.status_code == 200:
        _record(name, True)
        return {**r.json(), "status": "ok"}
    if r.status_code == 422:                                   # bad input is not a service failure
        try:
            details = r.json()["error"]["details"]
        except Exception:
            details = []
        return _err("VALIDATION_ERROR", "Input rejected by model service", details)
    _record(name, False)
    return _err("SVC_UNAVAILABLE" if r.status_code in (401, 503) else "SVC_ERROR", "Model service error")


def consensus(results: dict) -> str:
    cats = [r["category"] for r in results.values() if r.get("status") == "ok"]
    if not cats:
        return "No consensus"
    cat, n = Counter(cats).most_common(1)[0]
    return cat if n >= 2 else "No consensus"


async def predict(payload: dict, rid: str) -> dict:
    out = await asyncio.gather(*[_call(n, "POST", "/predict", rid, json=payload) for n in NAMES])
    return dict(zip(NAMES, out))


async def model_info(rid: str) -> list[dict]:
    out = await asyncio.gather(*[_call(n, "GET", "/model-info", rid, use_breaker=False) for n in NAMES])
    return [{"model": n, **o} for n, o in zip(NAMES, out)]


async def poll_health(rid: str = "health") -> list[dict]:
    out = await asyncio.gather(*[_call(n, "GET", "/health", rid, use_breaker=False) for n in NAMES])
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for n, o in zip(NAMES, out):
        health_cache[n] = {"service": n, "status": "UP" if o.get("status") == "ok" else "DOWN", "checked_at": now}
    return [health_cache[n] for n in NAMES]


async def health_loop() -> None:
    while True:
        try:
            await poll_health()
        except Exception:
            log.exception("health poll failed")
        await asyncio.sleep(settings.health_interval)
