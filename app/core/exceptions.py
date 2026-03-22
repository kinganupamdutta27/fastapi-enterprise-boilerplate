"""
Global exception hierarchy and FastAPI exception handlers.

All domain/application exceptions inherit from AppException so that the
global handler produces a consistent JSON envelope:

    {
        "error": true,
        "code": "RESOURCE_NOT_FOUND",
        "message": "Item with id 123 not found",
        "detail": { ... }      // optional extra context
    }
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ── Base Exception ─────────────────────────────────────────────────────

class AppException(Exception):
    """Base exception for all application-specific errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        if message:
            self.message = message
        if detail:
            self.detail = detail
        else:
            self.detail = {}
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)


# ── Concrete Exceptions ───────────────────────────────────────────────

class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "RESOURCE_CONFLICT"
    message = "Resource already exists or conflicts with current state"


class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "The request was invalid"


class UnauthorizedError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication is required"


class ForbiddenError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"


class RateLimitError(AppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests"


class ServiceUnavailableError(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
    message = "Service is temporarily unavailable"


class DatabaseError(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "DATABASE_ERROR"
    message = "A database error occurred"


class ExternalServiceError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "An external service returned an error"


class MessageBrokerError(AppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "MESSAGE_BROKER_ERROR"
    message = "Message broker is unavailable"


# ── Error Response Builder ────────────────────────────────────────────

def _build_error_response(
    status_code: int,
    error_code: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": True,
        "code": error_code,
        "message": message,
    }
    if detail:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


# ── Handler Registration ─────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException: code=%s message=%s", exc.error_code, exc.message
        )
        return _build_error_response(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail if exc.detail else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })
        return _build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            detail={"errors": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _build_error_response(
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        from app.core.config import settings

        logger.exception("Unhandled exception: %s", exc)
        return _build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_ERROR",
            message="An unexpected internal error occurred"
            if settings.is_production
            else str(exc),
        )
