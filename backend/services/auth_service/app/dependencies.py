from __future__ import annotations

from fastapi import Header

from services.auth_service.app.security import (
    AuthSecurityError,
    decode_access_token,
)


class AuthDependencyError(RuntimeError):
    pass


def get_current_user_id(
    authorization: str | None = Header(default=None),
) -> str:
    if not authorization:
        raise AuthDependencyError("Authorization header is required")

    if not authorization.lower().startswith("bearer "):
        raise AuthDependencyError("Authorization header must use Bearer token")

    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = decode_access_token(token)
    except AuthSecurityError as exc:
        raise AuthDependencyError(str(exc)) from exc

    user_id = payload.get("sub")

    if not user_id:
        raise AuthDependencyError("Invalid token subject")

    return str(user_id)