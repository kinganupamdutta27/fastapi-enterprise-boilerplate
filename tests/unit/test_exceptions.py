"""Unit tests for the global exception handler system."""

from __future__ import annotations

from app.core.exceptions import (
    AppException,
    BadRequestError,
    NotFoundError,
    UnauthorizedError,
)


def test_app_exception_defaults():
    exc = AppException()
    assert exc.status_code == 500
    assert exc.error_code == "INTERNAL_ERROR"


def test_not_found_error():
    exc = NotFoundError(message="Item 123 not found")
    assert exc.status_code == 404
    assert exc.error_code == "RESOURCE_NOT_FOUND"
    assert "123" in exc.message


def test_bad_request_error():
    exc = BadRequestError(detail={"field": "name"})
    assert exc.status_code == 400
    assert exc.detail == {"field": "name"}


def test_unauthorized_error():
    exc = UnauthorizedError()
    assert exc.status_code == 401
