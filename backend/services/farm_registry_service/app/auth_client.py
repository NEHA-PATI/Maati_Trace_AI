from __future__ import annotations

from typing import Any
from uuid import UUID

import requests
from pydantic import BaseModel

from shared.config.settings import settings
from services.farm_registry_service.app.errors import FarmRegistryError


class AuthPrincipal(BaseModel):
    user_id: UUID
    full_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    role: str
    is_active: bool = True
    is_verified: bool = False
    onboarding_status: str | None = None


def _error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Invalid or expired bearer token."

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail.get("message") or "Invalid or expired bearer token."
    return payload.get("message") or "Invalid or expired bearer token."


def get_current_user_from_auth_service(
    authorization: str | None,
    *,
    correlation_id: str,
) -> AuthPrincipal:
    if not authorization:
        raise FarmRegistryError(
            "UNAUTHORIZED",
            "Missing Authorization header.",
            401,
        )

    try:
        response = requests.get(
            f"{settings.auth_service_url}/v1/auth/me",
            headers={
                "Authorization": authorization,
                "X-Correlation-ID": correlation_id,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise FarmRegistryError(
            "AUTH_SERVICE_UNAVAILABLE",
            "Authentication is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code != 200:
        raise FarmRegistryError(
            "UNAUTHORIZED",
            _error_message(response),
            401,
        )

    try:
        payload: dict[str, Any] = response.json()
        return AuthPrincipal.model_validate(payload)
    except Exception as exc:
        raise FarmRegistryError(
            "INVALID_AUTH_RESPONSE",
            "Authentication response could not be read.",
            503,
            internal_message=str(exc),
        ) from exc
