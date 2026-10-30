import datetime as dt
import re

import bcrypt
import jwt

from .config import settings
from .errors import ApiError

_DUMMY = None


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=settings.bcrypt_cost)).decode()


def verify_password(pw: str, hashed: str | None) -> bool:
    """Always does a bcrypt check (even for unknown users) so response time does not reveal which emails exist."""
    global _DUMMY
    if hashed is None:
        _DUMMY = _DUMMY or hash_password("dummy-password")
        bcrypt.checkpw(pw.encode(), _DUMMY.encode())
        return False
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except ValueError:
        return False


def check_password_policy(pw: str) -> str | None:
    if len(pw) < 8 or len(pw) > 72:
        return "must be 8-72 characters"
    if not re.search(r"\d", pw) or not re.search(r"[A-Z]", pw):
        return "must contain at least 1 digit and 1 uppercase letter"
    return None


def create_token(user) -> tuple[str, int]:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.jwt_minutes)
    tok = jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, settings.jwt_secret, algorithm="HS256")
    return tok, settings.jwt_minutes * 60


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "Session expired, please log in again")
    except jwt.PyJWTError:
        raise ApiError(401, "AUTH_INVALID", "Invalid or missing credentials")
