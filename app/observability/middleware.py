"""
Starlette middleware that instruments every HTTP request with Prometheus
metrics and injects a correlation / request ID.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS_TOTAL


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Record request count and latency for every HTTP request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        status = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=status).inc()
        HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(elapsed)

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID header for distributed tracing / log correlation."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
