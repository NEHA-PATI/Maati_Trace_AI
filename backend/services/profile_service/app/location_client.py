from __future__ import annotations

from typing import Any

import httpx

from services.profile_service.app.config_validation import (
    get_profile_config,
)
from services.profile_service.app.errors import ProfileError


async def validate_location(
    *,
    state_name: str,
    district_name: str,
    block_name: str | None,
    block_code: int | None,
) -> dict[str, Any]:
    config = get_profile_config()

    payload = {
        "state_name": state_name,
        "district_name": district_name,
        "block_name": block_name,
        "block_code": block_code,
    }

    try:
        async with httpx.AsyncClient(
            timeout=config.request_timeout_seconds,
        ) as client:
            response = await client.post(
                (
                    f"{config.district_boundary_service_url}"
                    "/v1/location/validate"
                ),
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise ProfileError(
            "LOCATION_SERVICE_UNAVAILABLE",
            "Location validation is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code != 200:
        raise ProfileError(
            "LOCATION_VALIDATION_FAILED",
            "The selected district and block could not be validated.",
            422,
            internal_message=response.text[:1000],
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise ProfileError(
            "INVALID_LOCATION_RESPONSE",
            "Location validation is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if not data.get("is_valid"):
        raise ProfileError(
            "INVALID_LOCATION",
            data.get(
                "message",
                "The selected district and block are invalid.",
            ),
            422,
        )

    return data