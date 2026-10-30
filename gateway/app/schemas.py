import datetime as dt
import re

from pydantic import BaseModel, Field, StrictInt, field_validator

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


class RegisterIn(BaseModel):
    model_config = {"extra": "forbid"}
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(max_length=254)
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("must be a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str) -> str:
        from .security import check_password_policy
        msg = check_password_policy(v)
        if msg:
            raise ValueError(msg)
        return v


class LoginIn(BaseModel):
    model_config = {"extra": "forbid"}
    email: str = Field(max_length=254)
    password: str = Field(max_length=72)


class PredictIn(BaseModel):
    """FR-03 / SEC-03: whitelist validation. prev_sales order: OLDEST -> NEWEST (last value = yesterday)."""
    model_config = {"extra": "forbid"}
    store_id: int = Field(ge=1, le=10, strict=True)
    item_id: int = Field(ge=1, le=50, strict=True)
    date: dt.date
    prev_sales: list[StrictInt] = Field(min_length=7, max_length=7)

    @field_validator("date")
    @classmethod
    def _date(cls, v: dt.date) -> dt.date:
        if not (dt.date(2013, 1, 1) <= v <= dt.date(2030, 12, 31)):
            raise ValueError("must be between 2013-01-01 and 2030-12-31")
        return v

    @field_validator("prev_sales")
    @classmethod
    def _sales(cls, v: list[int]) -> list[int]:
        if any(x < 0 or x > 500 for x in v):
            raise ValueError("each value must be between 0 and 500")
        return v


class UserPatch(BaseModel):
    model_config = {"extra": "forbid"}
    is_active: bool
