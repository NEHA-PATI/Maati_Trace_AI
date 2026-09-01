from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from services.crop_observation_service.app.errors import CropObservationError
from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    PrincipalLookupError,
    load_current_user,
)


class AuthPrincipal(BaseModel):
    user_id: UUID
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    role: str
    is_active: bool = True
    is_verified: bool = False
    onboarding_status: str | None = None


def get_current_user(
    authorization: str | None,
    *,
    correlation_id: str,
) -> AuthPrincipal:
    if not authorization:
        raise CropObservationError(
            "UNAUTHORIZED",
            "Missing Authorization header.",
            401,
        )

    try:
        payload = load_current_user(authorization)
    except (InvalidAccessTokenError, CurrentUserUnavailableError) as exc:
        raise CropObservationError(
            "UNAUTHORIZED",
            "Invalid or expired bearer token.",
            401,
        ) from exc
    except MissingAuthorizationError as exc:
        raise CropObservationError(
            "UNAUTHORIZED",
            "Missing Authorization header.",
            401,
        ) from exc
    except PrincipalLookupError as exc:
        raise CropObservationError(
            "AUTH_SERVICE_UNAVAILABLE",
            "Authentication is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    try:
        return AuthPrincipal.model_validate(payload)
    except Exception as exc:
        raise CropObservationError(
            "INVALID_AUTH_RESPONSE",
            "Authentication response could not be read.",
            503,
            internal_message=str(exc),
        ) from exc
