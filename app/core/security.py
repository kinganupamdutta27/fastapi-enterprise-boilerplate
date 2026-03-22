"""
Security utilities: API key validation, JWT helpers.
Extend as needed for OAuth2, RBAC, etc.
"""

from __future__ import annotations

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Dependency that validates the X-API-Key header."""
    if not api_key or api_key != settings.secret_key:
        raise UnauthorizedError(message="Invalid or missing API key")
    return api_key
