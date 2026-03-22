"""
Resilience utilities: circuit breaker + retry with exponential backoff +
transaction support + asyncpg-to-AppException error mapping.

The call chain for every DB operation is:

    route -> service -> repository -> execute_query -> [retry -> circuit_breaker -> asyncpg]
                                                              -> error_mapper
                                                              -> prometheus timing

For multi-statement atomicity use ``transaction()`` context manager.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from aiobreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    DatabaseError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.db.pool import get_pool
from app.observability.metrics import (
    DB_CIRCUIT_BREAKER_STATE,
    DB_QUERY_DURATION,
    DB_QUERY_ERRORS_TOTAL,
    DB_RETRY_TOTAL,
)

logger = logging.getLogger(__name__)

# ── Circuit Breaker ────────────────────────────────────────────────────

db_circuit_breaker = CircuitBreaker(
    fail_max=settings.cb_fail_max,
    timeout_duration=settings.cb_timeout_duration,
    name="postgresql",
)


def get_circuit_breaker_state() -> str:
    """Return current CB state: 'closed', 'open', or 'half-open'."""
    state_class = type(db_circuit_breaker.state).__name__
    mapping = {
        "CircuitClosedState": "closed",
        "CircuitOpenState": "open",
        "CircuitHalfOpenState": "half-open",
    }
    return mapping.get(state_class, "unknown")


# ── Retry configuration ───────────────────────────────────────────────

_TRANSIENT_EXCEPTIONS = (
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    ConnectionRefusedError,
    OSError,
)


def _on_retry(retry_state: RetryCallState) -> None:
    """Log every retry attempt and bump Prometheus counter."""
    DB_RETRY_TOTAL.inc()
    logger.warning(
        "DB query retry  attempt=%d  wait=%.2fs  exc=%s",
        retry_state.attempt_number,
        retry_state.outcome.result() if retry_state.outcome else 0,
        retry_state.outcome.exception() if retry_state.outcome else "N/A",
    )


db_retry = retry(
    retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
    stop=stop_after_attempt(settings.db_retry_attempts),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    reraise=True,
    before_sleep=_on_retry,
)


# ── asyncpg → AppException mapping ────────────────────────────────────

def _map_asyncpg_error(exc: Exception) -> Exception:
    """Convert asyncpg exceptions into the application exception hierarchy."""
    if isinstance(exc, asyncpg.UniqueViolationError):
        return ConflictError(
            message="A record with the given unique key already exists",
            detail={"pg_detail": str(exc)},
        )
    if isinstance(exc, asyncpg.ForeignKeyViolationError):
        return BadRequestError(
            message="Referenced record does not exist",
            detail={"pg_detail": str(exc)},
        )
    if isinstance(exc, asyncpg.NotNullViolationError):
        return BadRequestError(
            message="A required field was null",
            detail={"pg_detail": str(exc)},
        )
    if isinstance(exc, asyncpg.CheckViolationError):
        return BadRequestError(
            message="A check constraint was violated",
            detail={"pg_detail": str(exc)},
        )
    if isinstance(exc, asyncpg.DataError):
        return BadRequestError(
            message="Invalid data format",
            detail={"pg_detail": str(exc)},
        )
    if isinstance(exc, CircuitBreakerError):
        _update_cb_gauge()
        return ServiceUnavailableError(
            message="Database circuit breaker is open — service temporarily unavailable"
        )
    if isinstance(exc, _TRANSIENT_EXCEPTIONS):
        return DatabaseError(
            message="Database is temporarily unreachable",
            detail={"pg_detail": str(exc)},
        )
    return DatabaseError(message=str(exc))


def _update_cb_gauge() -> None:
    state_map = {"closed": 0, "half-open": 1, "open": 2}
    DB_CIRCUIT_BREAKER_STATE.set(state_map.get(get_circuit_breaker_state(), -1))


# ── Combined query helper ─────────────────────────────────────────────

@db_retry
@db_circuit_breaker
async def execute_query(
    query: str,
    *args: Any,
    fetch_one: bool = False,
    fetch_all: bool = False,
    fetch_val: bool = False,
) -> Any:
    """Execute a query with retry + circuit breaker + Prometheus timing.

    Parameters
    ----------
    query : SQL with ``$1, $2, …`` placeholders.
    *args : Positional bind parameters.
    fetch_one : Return a single ``asyncpg.Record`` or ``None``.
    fetch_all : Return ``list[asyncpg.Record]``.
    fetch_val : Return a scalar value (first column of first row).
    """
    pool = get_pool()
    start = time.perf_counter()

    try:
        async with pool.acquire() as conn:
            if fetch_val:
                result = await conn.fetchval(query, *args)
            elif fetch_one:
                result = await conn.fetchrow(query, *args)
            elif fetch_all:
                result = await conn.fetch(query, *args)
            else:
                result = await conn.execute(query, *args)
            _update_cb_gauge()
            return result
    except Exception as exc:
        DB_QUERY_ERRORS_TOTAL.labels(
            error_type=type(exc).__name__
        ).inc()
        logger.exception("Query failed: %s", query[:120])
        raise _map_asyncpg_error(exc) from exc
    finally:
        elapsed = time.perf_counter() - start
        DB_QUERY_DURATION.observe(elapsed)


# ── Transaction context manager ────────────────────────────────────────

@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]:
    """Acquire a connection and wrap it in a DB transaction.

    Usage::

        async with transaction() as conn:
            await conn.execute("INSERT INTO ...")
            await conn.execute("UPDATE ...")
            # auto-COMMIT on success, ROLLBACK on exception

    The connection goes through the pool but NOT through the circuit
    breaker / retry (you manage retries at the service layer for
    multi-statement transactions).
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn
