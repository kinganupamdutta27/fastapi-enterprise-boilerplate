"""
Standard response envelopes for consistent API contracts.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    error: bool = True
    code: str
    message: str
    detail: dict[str, Any] | None = None
