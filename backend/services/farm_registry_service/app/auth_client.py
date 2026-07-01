from __future__ import annotations

from typing import Any

import requests

from shared.config.settings import settings


class FarmRegistryAuthClientError(RuntimeError):
    pass


def get_current_user_from_auth_service(authorization: str | None) -> dict[str, Any]:
    if not authorization:
        raise FarmRegistryAuthClientError("Missing Authorization header")

    url = f"{settings.auth_service_url}/v1/auth/me"

    try:
        response = requests.get(
            url,
            headers={"Authorization": authorization},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise FarmRegistryAuthClientError(
            f"Failed to reach auth service: {exc}"
        ) from exc

    if response.status_code != 200:
        raise FarmRegistryAuthClientError("Invalid or expired bearer token")

    try:
        payload = response.json()
    except ValueError as exc:
        raise FarmRegistryAuthClientError(
            "Auth service returned invalid JSON"
        ) from exc

    return {
        "user_id": payload.get("user_id"),
        "full_name": payload.get("full_name"),
        "email": payload.get("email"),
        "phone_number": payload.get("phone_number"),
        "role": payload.get("role"),
        "is_active": payload.get("is_active"),
        "is_verified": payload.get("is_verified"),
    }
