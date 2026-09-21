from __future__ import annotations

from typing import Any

from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.config.settings import settings
from shared.db.postgres import engine


class MissingAuthorizationError(ValueError):
    pass


class InvalidAccessTokenError(ValueError):
    pass


class CurrentUserUnavailableError(ValueError):
    pass


class PrincipalLookupError(RuntimeError):
    pass


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise MissingAuthorizationError("Authentication is required")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise InvalidAccessTokenError("Invalid bearer token")
    return token.strip()


def decode_access_token(authorization: str | None) -> dict[str, Any]:
    token = _bearer_token(authorization)
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
            },
        )
    except JWTError as exc:
        raise InvalidAccessTokenError("Invalid or expired access token") from exc

    if payload.get("type") != "access":
        raise InvalidAccessTokenError("Invalid token type")
    if not payload.get("sub") or not payload.get("session_id"):
        raise InvalidAccessTokenError("Invalid token subject or session")
    return payload


def load_current_user(authorization: str | None) -> dict[str, Any]:
    payload = decode_access_token(authorization)

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT
                        u.user_id,
                        u.full_name,
                        u.email,
                        u.phone_number,
                        u.role,
                        u.is_active,
                        COALESCE(u.is_verified, FALSE) AS is_verified,
                        u.onboarding_status,
                        u.profile_image_url
                    FROM public.users u
                    WHERE u.user_id = :user_id
                    LIMIT 1;
                    """
                ),
                {"user_id": str(payload["sub"])},
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise PrincipalLookupError("Authenticated user lookup failed") from exc

    if row is None or not row.get("is_active"):
        raise CurrentUserUnavailableError("The current user is not available")

    user = dict(row)
    user["full_name"] = (
        user.get("full_name")
        or user.get("email")
        or "MaatiTrace User"
    )
    user["is_active"] = bool(user.get("is_active"))
    user["is_verified"] = bool(user.get("is_verified"))
    return user
