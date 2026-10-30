import datetime as dt
import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

log = logging.getLogger("rdcp.db")


class Base(DeclarativeBase):
    pass


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


engine = None
SessionLocal = None


def init_engine(url: str | None = None):
    global engine, SessionLocal
    url = url or settings.database_url
    kw = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    engine = create_engine(url, **kw)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return engine


def create_schema(retries: int = 30, delay: float = 2.0) -> None:
    """Wait for the database (Postgres pod may start later) and create tables. Safe with several pods starting at once."""
    from . import models  # noqa: F401
    for i in range(retries):
        try:
            Base.metadata.create_all(engine)
            return
        except Exception as exc:  # another pod may be creating tables right now, or DB not up yet
            log.warning("DB not ready (%s), retry %d/%d", type(exc).__name__, i + 1, retries)
            time.sleep(delay)
    raise RuntimeError("database unavailable")


def ping() -> bool:
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
