from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

_correlation_id: ContextVar[str] = ContextVar(
    "farm_registry_correlation_id",
    default="",
)


def get_correlation_id() -> str:
    value = _correlation_id.get()
    if value:
        return value
    generated = str(uuid4())
    _correlation_id.set(generated)
    return generated


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or str(uuid4())
        )
        token = _correlation_id.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            _correlation_id.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response
