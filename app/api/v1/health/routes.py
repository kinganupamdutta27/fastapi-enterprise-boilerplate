"""
Health check endpoints — Kubernetes-ready probes.

- ``/health/live``    → Liveness  (always 200 if process is running)
- ``/health/ready``   → Readiness (200 if DB reachable, else 503)
- ``/health/startup`` → Startup   (200 once pool initialised, else 503)

K8s uses different probes for different purposes:
- Liveness  → restart the pod if this fails
- Readiness → stop routing traffic if this fails
- Startup   → don't check liveness/readiness until this succeeds
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.pool import get_pool
from app.db.resilience import get_circuit_breaker_state

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/live")
@router.get("/")
async def liveness():
    """Liveness probe — always 200 if the process is running."""
    return {"status": "ok", "version": settings.app_version, "env": settings.app_env}


@router.get("/ready")
async def readiness():
    """Readiness probe — returns 200 only when DB is reachable and CB is not open."""
    checks: dict = {
        "database": "disconnected",
        "circuit_breaker": get_circuit_breaker_state(),
    }

    db_ok = False
    try:
        pool = get_pool()
        async with pool.acquire(timeout=2) as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = "connected"
        checks["pool_size"] = pool.get_size()
        checks["pool_free"] = pool.get_idle_size()
        db_ok = True
    except Exception:
        logger.warning("Readiness check failed — database unreachable")

    cb_ok = checks["circuit_breaker"] != "open"
    is_ready = db_ok and cb_ok
    payload = {"status": "ok" if is_ready else "degraded", **checks}

    if not is_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return payload


@router.get("/startup")
async def startup():
    """Startup probe — returns 200 once the DB pool has been initialised."""
    try:
        pool = get_pool()
        async with pool.acquire(timeout=5) as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception:
        logger.warning("Startup check failed — pool not ready")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "starting"},
        )
