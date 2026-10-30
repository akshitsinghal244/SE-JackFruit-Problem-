from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db, ratelimit
from .errors import ApiError
from .models import AuditLog, User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_db():
    s = db.SessionLocal()
    try:
        yield s
    finally:
        s.close()


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    return (xff.split(",")[0].strip() if xff else (request.client.host if request.client else ""))[:64]


def audit(s, request: Request, action: str, outcome: str, user_id: int | None = None) -> None:
    """SEC-09: user, action, timestamp (default), IP, outcome."""
    s.add(AuditLog(user_id=user_id, action=action, ip=client_ip(request), outcome=outcome))
    s.commit()


def current_user(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(bearer), s=Depends(get_db)) -> User:
    if creds is None:
        raise ApiError(401, "AUTH_INVALID", "Invalid or missing credentials")
    payload = decode_token(creds.credentials)
    user = s.get(User, int(payload["sub"]))
    if user is None:
        raise ApiError(401, "AUTH_INVALID", "Invalid or missing credentials")
    if not user.is_active:
        raise ApiError(403, "ACCOUNT_DISABLED", "This account is disabled")
    ok, retry = ratelimit.allow(f"u{user.id}")
    if not ok:
        raise ApiError(429, "RATE_LIMITED", "Too many requests", headers={"Retry-After": str(retry)})
    request.state.user = user
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":                                   # SEC-06
        raise ApiError(403, "FORBIDDEN", "Not allowed")
    return user
