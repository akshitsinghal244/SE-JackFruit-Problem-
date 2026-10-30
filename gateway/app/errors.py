"""Uniform error body (SADS 3.4): {error:{code,message,details,request_id}}. Never leaks stack traces."""
import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("rdcp.server")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: list | None = None, headers: dict | None = None):
        self.status, self.code, self.message, self.details, self.headers = status, code, message, details or [], headers or {}


def rid(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def body(status: int, code: str, message: str, request_id: str, details=None, headers=None) -> JSONResponse:
    return JSONResponse(status_code=status, headers=headers,
                        content={"error": {"code": code, "message": message, "details": details or [], "request_id": request_id}})


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_and_headers(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        # SEC-10: security headers
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return body(exc.status, exc.code, exc.message, rid(request), exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _val(request: Request, exc: RequestValidationError):
        errs = exc.errors()
        if any(e.get("type") == "json_invalid" for e in errs):
            return body(400, "BAD_REQUEST", "Invalid request", rid(request))
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "reason": e["msg"].removeprefix("Value error, ")} for e in errs]
        return body(422, "VALIDATION_ERROR", "Invalid input", rid(request), details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST"
        return body(exc.status_code, code, "Not found" if exc.status_code == 404 else "Request not allowed", rid(request))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("Unhandled error request_id=%s", rid(request))
        return body(500, "INTERNAL_ERROR", "Internal error", rid(request))
