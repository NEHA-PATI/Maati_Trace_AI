from __future__ import annotations

import logging
import re
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.logging_context import (
    get_logger,
    log_event,
    new_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


logger = get_logger(__name__)
_CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("X-Correlation-ID", "").strip()
        correlation_id = supplied if _CORRELATION_PATTERN.fullmatch(supplied) else new_correlation_id()
        token = set_correlation_id(correlation_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        except Exception:
            logger.exception(
                "Unhandled request failure",
                extra={
                    "event_data": {
                        "event": "request_unhandled_failure",
                        "correlation_id": correlation_id,
                        "method": request.method,
                        "path": request.url.path,
                    }
                },
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            log_event(
                logger,
                logging.INFO,
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else None,
            )
            reset_correlation_id(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        config = get_auth_config()
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers[
            "Content-Security-Policy"
        ] = (
            "default-src 'self'; "
            "script-src 'self' https://accounts.google.com/gsi/client; "
            "frame-src https://accounts.google.com/gsi/; "
            "connect-src 'self' https://accounts.google.com/gsi/; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if config.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.url.path.startswith("/v1/auth"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response