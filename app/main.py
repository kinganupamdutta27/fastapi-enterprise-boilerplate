"""
FastAPI application entry point.

Sets up:
- Structured logging
- Async lifespan for pool init / teardown
- Global exception handlers
- CORS middleware
- Prometheus middleware & /metrics endpoint
- Versioned API routers
- Pool gauge background task
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.pool import close_pool, get_pool, init_pool
from app.observability.metrics import DB_POOL_FREE_SIZE, DB_POOL_SIZE
from app.observability.middleware import PrometheusMiddleware, RequestIDMiddleware

setup_logging()
logger = logging.getLogger(__name__)

_pool_gauge_task: asyncio.Task | None = None


async def _update_pool_gauges() -> None:
    """Periodically update Prometheus gauges for the DB pool."""
    while True:
        try:
            pool = get_pool()
            DB_POOL_SIZE.set(pool.get_size())
            DB_POOL_FREE_SIZE.set(pool.get_idle_size())
        except RuntimeError:
            pass
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: init pool -> yield -> close pool."""
    global _pool_gauge_task

    # ── Startup ────────────────────────────────────────────────────
    await init_pool()
    _pool_gauge_task = asyncio.create_task(_update_pool_gauges())
    logger.info("Application started  env=%s", settings.app_env)

    yield

    # ── Shutdown ───────────────────────────────────────────────────
    if _pool_gauge_task:
        _pool_gauge_task.cancel()
    await close_pool()
    logger.info("Application shut down")


app = FastAPI(
    title=settings.app_name,
    description="Production-ready async FastAPI template with PostgreSQL, "
    "circuit breakers, RabbitMQ, Kafka, ELK, and LangChain/LangGraph support.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# ── Global Exception Handlers ──────────────────────────────────────────
register_exception_handlers(app)

# ── Middleware (order matters: outermost first) ────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PrometheusMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────
app.include_router(v1_router)


# ── Prometheus metrics endpoint ────────────────────────────────────────
@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
