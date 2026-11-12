"""MOCK model service with the SAME contract as rdcp-models (ml/dl/qml).
Use it to run and demo the whole stack before the real models are trained.
  MODEL_NAME=ml|dl|qml   SERVICE_API_KEY=...   MOCK_FAIL=down|timeout|none (failure injection for demos/tests)
"""
import datetime as dt
import hashlib
import os
import secrets
import time
import uuid

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictInt

NAME = os.environ.get("MODEL_NAME", "ml")
KEY = os.environ.get("SERVICE_API_KEY", "dev-key")
INFO = {
    "ml": {"algorithm": "Random Forest (MOCK)", "accuracy": 81.2, "macro_f1": 0.79},
    "dl": {"algorithm": "LSTM (MOCK)", "accuracy": 79.6, "macro_f1": 0.77},
    "qml": {"algorithm": "VQC 4 qubits (MOCK)", "accuracy": 63.1, "macro_f1": 0.58},
}[NAME]
CLASSES = ["Low", "Medium", "High"]
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class Req(BaseModel):
    model_config = {"extra": "forbid"}
    store_id: int = Field(ge=1, le=10_000)
    item_id: int = Field(ge=1, le=100_000)
    date: dt.date
    prev_sales: list[StrictInt] = Field(min_length=7, max_length=7)


def err(status, code, msg, rid, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": msg, "details": details or [], "request_id": rid}})


@app.middleware("http")
async def rid_mw(request: Request, call_next):
    request.state.rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    r = await call_next(request)
    r.headers["X-Request-ID"] = request.state.rid
    return r


@app.exception_handler(RequestValidationError)
async def _v(request, exc):
    d = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "reason": e["msg"]} for e in exc.errors()]
    return err(422, "VALIDATION_ERROR", "Invalid input", request.state.rid, d)


async def auth(request: Request, x_api_key: str | None = Header(default=None)):
    if not x_api_key or not secrets.compare_digest(x_api_key, KEY):
        raise PermissionError


@app.exception_handler(PermissionError)
async def _p(request, exc):
    return err(401, "AUTH_INVALID", "Invalid or missing API key", request.state.rid)


def failure():
    mode = os.environ.get("MOCK_FAIL", "none")
    if mode == "timeout":
        time.sleep(30)
    return mode == "down"


@app.get("/health", dependencies=[Depends(auth)])
def health():
    if failure():
        return JSONResponse(status_code=503, content={"status": "DOWN", "model_loaded": False})
    return {"status": "UP", "model_loaded": True}


@app.get("/model-info", dependencies=[Depends(auth)])
def info(request: Request):
    if failure():
        return err(503, "SVC_UNAVAILABLE", "Model not loaded", request.state.rid)
    return {**INFO, "version": f"{NAME}-mock", "trained_on": "2026-10-01"}


@app.post("/predict", dependencies=[Depends(auth)])
def predict(req: Req, request: Request):
    if failure():
        return err(503, "SVC_UNAVAILABLE", "Model not loaded", request.state.rid)
    bad = []
    if req.store_id > 10:
        bad.append({"field": "store_id", "reason": "unknown store"})
    if req.item_id > 50:
        bad.append({"field": "item_id", "reason": "unknown item"})
    if bad:
        return err(422, "VALIDATION_ERROR", "Invalid input", request.state.rid, bad)
    t0 = time.perf_counter()
    # deterministic pseudo-prediction: recent level vs typical level, each model slightly different
    s = req.prev_sales
    recent, typical = sum(s[-3:]) / 3, sum(s) / 7
    score = (recent - typical) / max(typical, 1) + (0.15 if req.date.weekday() >= 5 else 0)
    h = int(hashlib.sha256(f"{NAME}{req.store_id}{req.item_id}{req.date}{s}".encode()).hexdigest(), 16)
    score += ((h % 100) - 50) / 800 * (3 if NAME == "qml" else 1)
    p = [0.2, 0.6, 0.2]
    p[2] += max(0, score) * 2
    p[0] += max(0, -score) * 2
    p[1] += 0.2 - abs(score)
    p = [max(x, 0.02) for x in p]
    tot = sum(p)
    p = [x / tot for x in p]
    k = max(range(3), key=lambda i: p[i])
    return {"model": NAME, "category": CLASSES[k], "confidence": round(100 * p[k], 1),
            "probabilities": {"low": round(p[0], 4), "medium": round(p[1], 4), "high": round(p[2], 4)},
            "accuracy": INFO["accuracy"], "latency_ms": round(1000 * (time.perf_counter() - t0) + (40 if NAME == "dl" else 380 if NAME == "qml" else 5), 1)}
