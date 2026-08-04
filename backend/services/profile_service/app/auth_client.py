from __future__ import annotations

from starlette.concurrency import run_in_threadpool

from services.profile_service.app.errors import ProfileError
from services.profile_service.app.schemas import (
    AuthenticatedUser,
)
from shared.security.local_auth import (
    CurrentUserUnavailableError,
    InvalidAccessTokenError,
    MissingAuthorizationError,
    PrincipalLookupError,
    load_current_user,
)


async def get_current_user_from_auth_service(
    authorization: str | None,
) -> AuthenticatedUser:
    if not authorization:
        raise ProfileError(
            "AUTH_REQUIRED",
            "Authentication is required.",
            401,
        )

    try:
        payload = await run_in_threadpool(
            load_current_user,
            authorization,
        )
    except (InvalidAccessTokenError, CurrentUserUnavailableError) as exc:
        raise ProfileError(
            "INVALID_AUTH_SESSION",
            "Your authentication session is invalid or expired.",
            401,
        ) from exc
    except MissingAuthorizationError as exc:
        raise ProfileError(
            "AUTH_REQUIRED",
            "Authentication is required.",
            401,
        ) from exc
    except PrincipalLookupError as exc:
        raise ProfileError(
            "AUTH_SERVICE_UNAVAILABLE",
            "Authentication could not be verified.",
            503,
            internal_message=str(exc),
        ) from exc

    try:
        principal = AuthenticatedUser.model_validate(payload)
    except Exception as exc:
        raise ProfileError(
            "INVALID_AUTH_RESPONSE",
            "Authentication could not be verified.",
            503,
            internal_message=str(exc),
        ) from exc

    if not principal.is_active:
        raise ProfileError(
            "ACCOUNT_INACTIVE",
            "Your account is inactive.",
            403,
        )

    return principal
