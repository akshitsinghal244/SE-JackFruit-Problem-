"""FastAPI app factory: the SAME /predict, /health, /model-info for ML, DL and QML.

Implements SADS 3.3.2 (internal microservice API) and the parts of 3.4 / 2.8
that belong to a model service:
  * X-API-Key check (SEC-05)           - constant-time compare, fail closed
  * Pydantic whitelist validation      - 422 with details[] (SEC-03)
  * uniform error body                 - {error:{code,message,details,request_id}}
  * model loaded once at start-up      - SADS 3.6
  * no stack traces in responses       - SADS 3.4
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from .config import MAX_DAILY_SALES, WINDOW
from .predictor import BasePredictor, build_result

log = logging.getLogger("rdcp.service")


# ----------------------------------------------------------------- schemas
class PredictRequest(BaseModel):
    model_config = {"extra": "forbid"}  # whitelist: unknown fields are rejected

    store_id: int = Field(ge=1, le=10_000)
    item_id: int = Field(ge=1, le=100_000)
    date: dt.date
    prev_sales: list[int] = Field(min_length=WINDOW, max_length=WINDOW)

    @field_validator("prev_sales")
    @classmethod
    def _sales_range(cls, v: list[int]) -> list[int]:
        for x in v:
            if x < 0 or x > MAX_DAILY_SALES:
                raise ValueError(f"each value must be between 0 and {MAX_DAILY_SALES}")
        return v


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: list | None = None):
        self.status, self.code, self.message, self.details = status, code, message, details or []


def _error(status: int, code: str, message: str, request_id: str, details: list | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or [], "request_id": request_id}},
    )


def _rid(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


# ----------------------------------------------------------------- factory
def create_app(service_name: str, predictor_factory: Callable[[str], BasePredictor]) -> FastAPI:
    model_dir = os.environ.get("MODEL_DIR", "/models")
    api_key = os.environ.get("SERVICE_API_KEY", "")
    allow_no_key = os.environ.get("RDCP_ALLOW_NO_KEY") == "1"  # local dev only
    state: dict = {"predictor": None, "load_error": None}

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if not api_key and not allow_no_key:
            raise RuntimeError("SERVICE_API_KEY is not set (set RDCP_ALLOW_NO_KEY=1 only for local dev)")
        try:
            state["predictor"] = predictor_factory(model_dir)
            log.info("%s model loaded from %s", service_name, model_dir)
        except Exception as exc:  # service stays up and reports DOWN on /health
            state["load_error"] = type(exc).__name__
            log.exception("Failed to load %s model from %s", service_name, model_dir)
        yield

    app = FastAPI(title=f"RDCP {service_name.upper()} service", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    # -- request id on every request
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    # -- uniform errors
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return _error(exc.status, exc.code, exc.message, _rid(request), exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "reason": e["msg"]} for e in exc.errors()]
        return _error(422, "VALIDATION_ERROR", "Invalid input", _rid(request), details)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("Unhandled error request_id=%s", _rid(request))
        return _error(500, "INTERNAL_ERROR", "Internal error", _rid(request))

    # -- auth
    async def require_key(x_api_key: str | None = Header(default=None)):
        if allow_no_key and not api_key:
            return
        if not x_api_key or not secrets.compare_digest(x_api_key, api_key):
            raise ApiError(401, "AUTH_INVALID", "Invalid or missing API key")

    def get_predictor() -> BasePredictor:
        p = state["predictor"]
        if p is None:
            raise ApiError(503, "SVC_UNAVAILABLE", "Model not loaded")
        return p

    # -- routes
    @app.get("/health", dependencies=[Depends(require_key)])
    async def health():
        loaded = state["predictor"] is not None
        body = {"status": "UP" if loaded else "DOWN", "model_loaded": loaded}
        return JSONResponse(status_code=200 if loaded else 503, content=body)

    @app.get("/model-info", dependencies=[Depends(require_key)])
    async def model_info(p: BasePredictor = Depends(get_predictor)):
        return p.model_info()

    @app.post("/predict", dependencies=[Depends(require_key)])
    def predict(req: PredictRequest, p: BasePredictor = Depends(get_predictor)):
        # plain `def` -> FastAPI runs it in a thread pool, so CPU-bound inference
        # does not block the event loop.
        problems = []
        if req.store_id not in p.known_stores:
            problems.append({"field": "store_id", "reason": "unknown store"})
        if req.item_id not in p.known_items:
            problems.append({"field": "item_id", "reason": "unknown item"})
        if problems:
            raise ApiError(422, "VALIDATION_ERROR", "Invalid input", problems)

        t0 = time.perf_counter()
        probs = p.predict_proba(req.store_id, req.item_id, req.date, [float(x) for x in req.prev_sales])
        latency = 1000 * (time.perf_counter() - t0)
        return build_result(service_name, probs, p.model_info()["accuracy"], latency)

    return app
