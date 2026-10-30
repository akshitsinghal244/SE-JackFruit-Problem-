"""SEC-07: 60 requests/min/user. Uses Redis when REDIS_URL is set so the limit is shared by ALL server pods;
falls back to an in-process counter (fine for a single replica / tests)."""
import logging
import time

from .config import settings

log = logging.getLogger("rdcp.ratelimit")
_mem: dict[str, tuple[int, int]] = {}
_redis = None


def _get_redis():
    global _redis
    if _redis is None and settings.redis_url:
        import redis
        _redis = redis.Redis.from_url(settings.redis_url, socket_timeout=0.5, socket_connect_timeout=0.5)
    return _redis


def reset() -> None:
    _mem.clear()


def allow(key: str) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). Fixed 60 s window."""
    window = int(time.time() // 60)
    retry = 60 - int(time.time() % 60)
    r = _get_redis()
    if r is not None:
        try:
            k = f"rl:{key}:{window}"
            n = r.incr(k)
            if n == 1:
                r.expire(k, 65)
            return n <= settings.rate_limit, retry
        except Exception as exc:  # fail open: never block users because Redis is down
            log.warning("redis unavailable (%s); using local limiter", type(exc).__name__)
    w, n = _mem.get(key, (window, 0))
    n = n + 1 if w == window else 1
    _mem[key] = (window, n)
    return n <= settings.rate_limit, retry
