"""Shared test fixtures."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.pool import close_pool, init_pool
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for all session-scoped async fixtures."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _db_pool():
    """Initialise and tear down the DB pool once per test session."""
    await init_pool()
    yield
    await close_pool()


@pytest.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
