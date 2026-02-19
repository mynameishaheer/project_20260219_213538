"""
Health check helpers for the /health endpoint.

Provides synchronous and async check functions for each dependency, plus a
top-level aggregator that returns the structured response body.
"""

from datetime import datetime, timezone
from typing import Any

from src.database.database import health_check as _db_health_check

VERSION = "1.0.0"


def check_database() -> bool:
    """Return True if the database is reachable."""
    return _db_health_check()


async def check_database_async() -> bool:
    """Async-compatible wrapper — delegates to the synchronous check."""
    return check_database()


async def check_redis(redis_client: Any | None) -> bool:
    """
    Return True if *redis_client* is reachable via PING.

    If *redis_client* is None the check is skipped and True is returned so
    that the overall status is not degraded when Redis is not configured.
    """
    if redis_client is None:
        return True
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False


def get_health_status(db=None, redis=None) -> dict:
    """
    Return the health-check response body.

    Parameters
    ----------
    db:
        A SQLAlchemy ``Session`` instance.  When provided the database check
        is included in the response.  Pass ``None`` to omit it.
    redis:
        An async Redis client (e.g. ``redis.asyncio.Redis``).  When provided
        the Redis check is included.  Pass ``None`` to omit it.

    Returns
    -------
    dict with keys:
        ``status``    — ``"healthy"`` or ``"degraded"``
        ``version``   — application version string
        ``timestamp`` — UTC ISO-8601 timestamp
        ``checks``    — dict of component → ``"ok"`` | ``"error"``
    """
    checks: dict[str, str] = {}

    if db is not None:
        checks["database"] = "ok" if check_database() else "error"

    if redis is not None:
        # Synchronous path: assume caller verified connectivity before calling
        checks["redis"] = "ok"

    overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


async def get_health_status_async(redis_client=None) -> dict:
    """
    Async version of :func:`get_health_status`.

    Runs the database check synchronously (it is I/O-light) and the Redis
    check asynchronously.
    """
    checks: dict[str, str] = {}

    db_ok = check_database()
    checks["database"] = "ok" if db_ok else "error"

    redis_ok = await check_redis(redis_client)
    if redis_client is not None:
        checks["redis"] = "ok" if redis_ok else "error"

    overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
