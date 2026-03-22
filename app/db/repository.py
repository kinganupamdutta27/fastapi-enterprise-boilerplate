"""
Base repository pattern for DB access.

Provides:
- Standard CRUD helpers that route through the resilience layer.
- ``fetch_val`` for scalar queries (COUNT, EXISTS, etc.).
- ``transactional`` context manager for multi-statement atomicity.

Concrete feature repositories (e.g. items) live in their own API modules
and inherit from this class.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from app.db.resilience import execute_query, transaction

logger = logging.getLogger(__name__)


class BaseRepository:
    """Thin wrapper around the resilience layer with convenience methods."""

    # ── Single-query operations (circuit breaker + retry) ──────────────

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        row = await execute_query(query, *args, fetch_one=True)
        return dict(row) if row else None

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        rows = await execute_query(query, *args, fetch_all=True)
        return [dict(r) for r in rows]

    async def fetch_val(self, query: str, *args: Any) -> Any:
        """Return a single scalar value (first column of first row)."""
        return await execute_query(query, *args, fetch_val=True)

    async def execute(self, query: str, *args: Any) -> str:
        return await execute_query(query, *args)

    # ── Transaction support (bypasses CB — retry at the service layer) ─

    @asynccontextmanager
    async def transactional(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection inside a DB transaction.

        Usage inside a repository method::

            async with self.transactional() as conn:
                await conn.execute("INSERT INTO orders ...")
                await conn.execute("UPDATE inventory ...")
        """
        async with transaction() as conn:
            yield conn
