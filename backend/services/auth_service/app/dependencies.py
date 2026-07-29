from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, Header, Request

from services.auth_service.app.audit import record_audit_event
from services.auth_service.app.config_validation import get_auth_config
from services.auth_service.app.errors import AuthError
from services.auth_service.app.security import (
    AuthSecurityError,
    decode_access_token,
    hash_device_id,
    hash_user_agent,
    secure_equals,
)


@dataclass(frozen=True, slots=True)
class RequestContext:
    ip_address: str | None
    device_id_hash: str | None
    user_agent_hash: str | None


def get_request_context(
    request: Request,
    x_device_id: str | None = Header(default=None, alias="X-Device-ID"),
) -> RequestContext:
    user_agent = request.headers.get("User-Agent")
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        device_id_hash=hash_device_id(x_device_id),
        user_agent_hash=hash_user_agent(user_agent),
    )


def get_current_principal(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("AUTH_REQUIRED", "Authentication is required.", 401)
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except AuthSecurityError as exc:
        raise AuthError("INVALID_ACCESS_TOKEN", "Your session is invalid or expired.", 401) from exc
    return {
        "user_id": str(payload["sub"]),
        "role": str(payload.get("role") or ""),
        "session_id": str(payload["session_id"]),
    }


def require_roles(*allowed_roles: str) -> Callable[[dict[str, str]], dict[str, str]]:
    def dependency(
        principal: dict[str, str] = Depends(get_current_principal),
        context: RequestContext = Depends(get_request_context),
    ) -> dict[str, str]:
        if principal.get("role") not in allowed_roles:
            record_audit_event(
                event_type="authorization_denied",
                outcome="forbidden",
                user_id=principal.get("user_id"),
                auth_session_id=principal.get("session_id"),
                ip_address=context.ip_address,
                device_id_hash=context.device_id_hash,
                user_agent_hash=context.user_agent_hash,
                metadata={"required_roles": list(allowed_roles), "actual_role": principal.get("role")},
            )
            raise AuthError("FORBIDDEN", "You do not have permission to perform this action.", 403)
        return principal

    return dependency


def validate_cookie_request(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> str:
    config = get_auth_config()
    origin = request.headers.get("Origin")
    if origin:
        if origin not in config.cors_allowed_origins:
            raise AuthError("INVALID_ORIGIN", "The request origin is not allowed.", 403)
    elif config.app_env == "production":
        raise AuthError("INVALID_ORIGIN", "The request origin is required.", 403)

    csrf_cookie = request.cookies.get(config.csrf_cookie_name)
    if not secure_equals(csrf_cookie, x_csrf_token):
        raise AuthError("CSRF_VALIDATION_FAILED", "Security validation failed.", 403)

    refresh_token = request.cookies.get(config.refresh_cookie_name)
    if not refresh_token:
        raise AuthError("REFRESH_REQUIRED", "Your session is invalid or expired.", 401)
    return refresh_token