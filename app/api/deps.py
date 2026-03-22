"""
Shared FastAPI dependencies used across API versions.

Each dependency is a callable that can be injected via Depends().
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass
class PaginationParams:
    """Standard pagination query parameters."""

    limit: int = 50
    offset: int = 0


def get_pagination(
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)
