import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from . import db, errors, services
from .config import settings
from .models import AuditLog, User
from .routers import admin, auth, history, predict
from .security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("rdcp")


def seed_admin() -> None:
    if not (settings.admin_email and settings.admin_password):
        return
    s = db.SessionLocal()
    try:
        if s.scalar(select(User).where(User.email == settings.admin_email.lower())) is None:
            s.add(User(username="admin", email=settings.admin_email.lower(), password_hash=hash_password(settings.admin_password), role="admin"))
            s.commit()
            log.info("admin account created")
    except IntegrityError:          # another pod created it first
        s.rollback()
    finally:
        s.close()


def purge_audit(days: int = 90) -> int:
    """SEC-09: audit entries are kept for 90 days, then deleted."""
    from datetime import timedelta
    s = db.SessionLocal()
    try:
        n = s.execute(delete(AuditLog).where(AuditLog.created_at < db.utcnow() - timedelta(days=days))).rowcount
        s.commit()
        return n or 0
    finally:
        s.close()


async def retention_loop() -> None:
    while True:
        try:
            n = await asyncio.to_thread(purge_audit)
            if n:
                log.info("purged %d audit rows older than 90 days", n)
        except Exception:
            log.exception("audit purge failed")
        await asyncio.sleep(24 * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.jwt_secret:
        if settings.dev:
            settings.jwt_secret = "dev-only-secret-change-me-0123456789"
        else:
            raise RuntimeError("JWT_SECRET is not set")
    if db.engine is None:
        db.init_engine()
    await asyncio.to_thread(db.create_schema)
    await asyncio.to_thread(seed_admin)
    tasks = [asyncio.create_task(services.health_loop()), asyncio.create_task(retention_loop())]
    yield
    for t in tasks:
        t.cancel()


def create_app() -> FastAPI:
    app = FastAPI(title="RDCP web server", version="1.0", lifespan=lifespan, docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json", redoc_url=None)
    errors.install(app)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors, allow_methods=["GET", "POST", "PATCH"],
                       allow_headers=["Authorization", "Content-Type"], expose_headers=["Content-Disposition", "Retry-After"])
    for r in (auth.router, predict.router, history.router, admin.router):
        app.include_router(r, prefix="/api/v1")

    @app.get("/api/v1/health")
    def api_health():
        import os
        return {"status": "ok", "served_by": os.environ.get("HOSTNAME", "local")}

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz():
        ok = db.ping()
        return JSONResponse(status_code=200 if ok else 503, content={"status": "ready" if ok else "db-unavailable"})

    return app


app = create_app()
