from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from .. import services
from ..deps import admin_user, audit, get_db
from ..errors import ApiError, rid
from ..models import AuditLog, User
from ..schemas import UserPatch

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health(request: Request, refresh: bool = False, admin: User = Depends(admin_user)):
    if refresh or len(services.health_cache) < len(services.NAMES):
        return await services.poll_health(rid(request))
    return [services.health_cache[n] for n in services.NAMES]


@router.get("/users")
def users(admin: User = Depends(admin_user), s=Depends(get_db)):
    rows = s.scalars(select(User).order_by(User.id)).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role, "is_active": u.is_active,
             "created_at": u.created_at.isoformat(timespec="seconds") + "Z"} for u in rows]


@router.patch("/users/{user_id}")
def patch_user(user_id: int, body: UserPatch, request: Request, admin: User = Depends(admin_user), s=Depends(get_db)):
    u = s.get(User, user_id)
    if u is None:
        raise ApiError(404, "NOT_FOUND", "Not found")
    if u.id == admin.id and not body.is_active:
        raise ApiError(422, "VALIDATION_ERROR", "Invalid input", [{"field": "is_active", "reason": "you cannot disable your own account"}])
    u.is_active = body.is_active
    s.commit()
    audit(s, request, "ADMIN_ENABLE" if body.is_active else "ADMIN_DISABLE", "success", admin.id)
    return {"id": u.id, "is_active": u.is_active}


@router.get("/audit")
def audit_log(limit: int = Query(50, ge=1, le=200), admin: User = Depends(admin_user), s=Depends(get_db)):
    rows = s.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).all()
    return [{"id": a.id, "user_id": a.user_id, "action": a.action, "ip": a.ip, "outcome": a.outcome,
             "created_at": a.created_at.isoformat(timespec="seconds") + "Z"} for a in rows]
