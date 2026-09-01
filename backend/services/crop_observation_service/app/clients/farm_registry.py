from __future__ import annotations

from typing import Any
from uuid import UUID

import requests

from shared.config.settings import settings
from services.crop_observation_service.app.errors import CropObservationError


def _error_detail(response: requests.Response, fallback: str) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return "FARM_REGISTRY_ERROR", response.text or fallback

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return (
            detail.get("code") or "FARM_REGISTRY_ERROR",
            detail.get("message") or fallback,
        )
    return payload.get("code") or "FARM_REGISTRY_ERROR", payload.get("message") or fallback


def get_authorized_farm(
    farm_id: UUID,
    *,
    authorization: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Fetch a farm from farm_registry_service, forwarding the caller's own
    bearer token so farm_registry_service's existing ownership checks decide
    access. A 200 response means the caller (farmer/fpo/admin) is allowed to
    see this farm — do not duplicate that authorization logic here.
    """
    try:
        response = requests.get(
            f"{settings.farm_registry_service_url}/v1/farms/{farm_id}",
            headers={
                "Authorization": authorization,
                "X-Correlation-ID": correlation_id,
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise CropObservationError(
            "FARM_REGISTRY_UNAVAILABLE",
            "Farm information is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code == 404:
        raise CropObservationError("FARM_NOT_FOUND", "Farm was not found.", 404)
    if response.status_code == 403:
        raise CropObservationError(
            "FARM_ACCESS_FORBIDDEN",
            "You cannot access this farm.",
            403,
        )
    if response.status_code != 200:
        code, message = _error_detail(response, "Farm registry request failed.")
        raise CropObservationError(code, message, response.status_code)

    return response.json()
