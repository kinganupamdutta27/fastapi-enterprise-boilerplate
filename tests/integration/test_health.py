"""Integration tests for health endpoints.

These tests hit the real FastAPI app via ASGI transport.
DB-dependent tests will report 'degraded' unless a database is available.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient):
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_without_db(client: AsyncClient):
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
