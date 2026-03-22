"""
V1 API router aggregator.

Each feature module registers its own sub-router here.
New feature teams add a single include_router line — no merge conflicts.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health.routes import router as health_router
from app.api.v1.items.routes import router as items_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health_router)
v1_router.include_router(items_router)
