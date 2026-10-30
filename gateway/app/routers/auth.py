import datetime as dt

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..db import utcnow
from ..deps import audit, current_user, get_db
from ..errors import ApiError
from ..models import User
from ..schemas import LoginIn, RegisterIn
from ..security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterIn, request: Request, s=Depends(get_db)):
    taken = s.scalar(select(User).where(or_(User.email == body.email, User.username == body.username)))
    if taken:
        raise ApiError(422, "VALIDATION_ERROR", "Invalid input", [{"field": "email", "reason": "email or username already registered"}])
    user = User(username=body.username, email=body.email, password_hash=hash_password(body.password))
    s.add(user)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        raise ApiError(422, "VALIDATION_ERROR", "Invalid input", [{"field": "email", "reason": "email or username already registered"}])
    audit(s, request, "REGISTER", "success", user.id)
    return {"id": user.id, "username": user.username}


@router.post("/login")
def login(body: LoginIn, request: Request, s=Depends(get_db)):
    user = s.scalar(select(User).where(User.email == body.email.strip().lower()))
    now = utcnow()
    if user and user.locked_until and user.locked_until > now:                # SEC-08
        audit(s, request, "LOGIN", "locked", user.id)
        mins = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise ApiError(423, "ACCOUNT_LOCKED", f"Too many failed attempts. Try again in {mins} minutes")
    ok = verify_password(body.password, user.password_hash if user else None)
    if not ok:
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= settings.lock_after:
                user.locked_until = now + dt.timedelta(minutes=settings.lock_minutes)
                user.failed_attempts = 0
            s.commit()
        audit(s, request, "LOGIN", "failure", user.id if user else None)
        raise ApiError(401, "AUTH_INVALID", "Invalid credentials")            # FR-02: never say which field is wrong
    if not user.is_active:
        audit(s, request, "LOGIN", "disabled", user.id)
        raise ApiError(403, "ACCOUNT_DISABLED", "This account is disabled")
    user.failed_attempts, user.locked_until = 0, None
    s.commit()
    token, ttl = create_token(user)
    audit(s, request, "LOGIN", "success", user.id)
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl, "role": user.role, "username": user.username}


@router.post("/logout", status_code=204)
def logout(request: Request, user: User = Depends(current_user), s=Depends(get_db)):
    audit(s, request, "LOGOUT", "success", user.id)
    return Response(status_code=204)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
