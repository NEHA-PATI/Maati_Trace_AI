from __future__ import annotations

import httpx

from services.profile_service.app.config_validation import (
    get_profile_config,
)
from services.profile_service.app.errors import ProfileError
from services.profile_service.app.schemas import (
    AuthenticatedUser,
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

    config = get_profile_config()

    try:
        async with httpx.AsyncClient(
            timeout=config.request_timeout_seconds,
        ) as client:
            response = await client.get(
                f"{config.auth_service_url}/v1/auth/me",
                headers={
                    "Authorization": authorization,
                },
            )
    except httpx.HTTPError as exc:
        raise ProfileError(
            "AUTH_SERVICE_UNAVAILABLE",
            "Authentication could not be verified.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code in {401, 403}:
        raise ProfileError(
            "INVALID_AUTH_SESSION",
            "Your authentication session is invalid or expired.",
            401,
        )

    if response.status_code != 200:
        raise ProfileError(
            "AUTH_SERVICE_ERROR",
            "Authentication could not be verified.",
            503,
            internal_message=response.text[:1000],
        )

    try:
        principal = AuthenticatedUser.model_validate(
            response.json()
        )
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