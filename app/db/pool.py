"""
Async connection pool management using asyncpg.

Design choices:
- Small application-side pool (2-10) because PgBouncer handles multiplexing.
- max_inactive_connection_lifetime evicts idle connections quickly.
- command_timeout protects against hung queries at the driver level.
- server_settings apply statement_timeout and idle_in_transaction_session_timeout
  on every connection opened by the pool.
- Graceful init with retry so the app can survive a brief DB outage at startup.
"""

from __future__ import annotations

import logging

import asyncpg
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

_STARTUP_RETRYABLE = (
    ConnectionRefusedError,
    OSError,
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
)


@retry(
    retry=retry_if_exception_type(_STARTUP_RETRYABLE),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=15),
    reraise=True,
)
async def init_pool() -> asyncpg.Pool:
    """Create the asyncpg pool with production-grade settings.

    Retries up to 5 times with exponential backoff so the app can
    survive a brief database / PgBouncer startup delay.
    """
    global _pool

    if _pool is not None:
        return _pool

    logger.info(
        "Creating asyncpg pool  host=%s  port=%s  db=%s  min=%d  max=%d  cmd_timeout=%ss",
        settings.database_host,
        settings.database_port,
        settings.database_name,
        settings.db_pool_min_size,
        settings.db_pool_max_size,
        settings.db_command_timeout,
    )

    async def _connection_init(conn: asyncpg.Connection) -> None:
        """Apply per-connection session settings after creation."""
        await conn.execute(
            f"SET statement_timeout = {settings.db_statement_timeout}"
        )
        await conn.execute(
            f"SET idle_in_transaction_session_timeout = {settings.db_idle_in_transaction_timeout}"
        )

    _pool = await asyncpg.create_pool(
        host=settings.database_host,
        port=settings.database_port,
        user=settings.database_user,
        password=settings.database_password,
        database=settings.database_name,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        max_inactive_connection_lifetime=settings.db_pool_max_inactive_lifetime,
        command_timeout=settings.db_command_timeout,
        init=_connection_init,
    )

    # Validate the pool is actually usable (catches auth errors early)
    async with _pool.acquire() as conn:
        await conn.fetchval("SELECT 1")

    logger.info("asyncpg pool created and validated")
    return _pool


async def close_pool() -> None:
    """Gracefully close the asyncpg connection pool."""
    global _pool

    if _pool is not None:
        logger.info("Closing asyncpg pool")
        await _pool.close()
        _pool = None
        logger.info("asyncpg pool closed")


def get_pool() -> asyncpg.Pool:
    """Return the current pool instance.  Raises if not initialised."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Call init_pool() first.")
    return _pool
