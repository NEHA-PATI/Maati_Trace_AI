from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import requests
from pydantic import BaseModel

from shared.config.settings import settings
from services.farm_registry_service.app.errors import FarmRegistryError


class FarmerValidation(BaseModel):
    farmer_id: UUID
    user_id: UUID | None = None
    fpo_id: UUID | None = None
    is_active: bool
    profile_complete: bool
    onboarding_status: str


class FpoValidation(BaseModel):
    fpo_id: UUID
    is_active: bool
    verification_status: str
    profile_complete: bool


def _error_detail(response: requests.Response, fallback: str) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return "PROFILE_SERVICE_ERROR", response.text or fallback

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return (
            detail.get("code") or "PROFILE_SERVICE_ERROR",
            detail.get("message") or fallback,
        )
    return payload.get("code") or "PROFILE_SERVICE_ERROR", payload.get("message") or fallback


def _get_json(
    path: str,
    *,
    headers: dict[str, str],
    not_found_code: str,
    not_found_message: str,
) -> dict[str, Any] | list[Any]:
    try:
        response = requests.get(
            f"{settings.profile_service_url}{path}",
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise FarmRegistryError(
            "PROFILE_SERVICE_UNAVAILABLE",
            "Profile information is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code == 404:
        raise FarmRegistryError(not_found_code, not_found_message, 404)
    if response.status_code != 200:
        code, message = _error_detail(response, "Profile service request failed.")
        raise FarmRegistryError(code, message, response.status_code)
    return response.json()


def get_my_profile(
    *,
    authorization: str,
    correlation_id: str,
    fpo_context_id: UUID | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": authorization,
        "X-Correlation-ID": correlation_id,
    }
    if fpo_context_id is not None:
        headers["X-FPO-ID"] = str(fpo_context_id)
    payload = _get_json(
        "/v1/profiles/me",
        headers=headers,
        not_found_code="PROFILE_NOT_FOUND",
        not_found_message="Profile was not found.",
    )
    if not isinstance(payload, dict):
        raise FarmRegistryError("INVALID_PROFILE_RESPONSE", "Profile response could not be read.", 502)
    return payload


def get_farmer_profile(
    farmer_id: UUID,
    *,
    authorization: str,
    correlation_id: str,
) -> dict[str, Any]:
    payload = _get_json(
        f"/v1/profiles/farmers/{farmer_id}",
        headers={
            "Authorization": authorization,
            "X-Correlation-ID": correlation_id,
        },
        not_found_code="FARMER_PROFILE_NOT_FOUND",
        not_found_message="Farmer profile was not found.",
    )
    if not isinstance(payload, dict):
        raise FarmRegistryError("INVALID_PROFILE_RESPONSE", "Farmer profile response could not be read.", 502)
    return payload


def get_fpo_profile(
    fpo_id: UUID,
    *,
    authorization: str,
    correlation_id: str,
) -> dict[str, Any]:
    payload = _get_json(
        f"/v1/profiles/fpos/{fpo_id}",
        headers={
            "Authorization": authorization,
            "X-Correlation-ID": correlation_id,
        },
        not_found_code="FPO_PROFILE_NOT_FOUND",
        not_found_message="FPO profile was not found.",
    )
    if not isinstance(payload, dict):
        raise FarmRegistryError("INVALID_PROFILE_RESPONSE", "FPO profile response could not be read.", 502)
    return payload


def get_fpo_farmers(
    fpo_id: UUID,
    *,
    authorization: str,
    correlation_id: str,
) -> list[Any]:
    payload = _get_json(
        f"/v1/profiles/fpos/{fpo_id}/farmers",
        headers={
            "Authorization": authorization,
            "X-Correlation-ID": correlation_id,
        },
        not_found_code="FPO_PROFILE_NOT_FOUND",
        not_found_message="FPO profile was not found.",
    )
    if not isinstance(payload, list):
        raise FarmRegistryError("INVALID_PROFILE_RESPONSE", "FPO farmers response could not be read.", 502)
    return payload


def validate_farmer_internal(farmer_id: UUID, correlation_id: str) -> FarmerValidation:
    token = os.getenv("PROFILE_INTERNAL_SERVICE_TOKEN", "")
    payload = _get_json(
        f"/internal/v1/farmers/{farmer_id}/validation",
        headers={
            "X-Internal-Service-Token": token,
            "X-Correlation-ID": correlation_id,
        },
        not_found_code="FARMER_PROFILE_NOT_FOUND",
        not_found_message="Farmer profile was not found.",
    )
    return FarmerValidation.model_validate(payload)


def validate_fpo_internal(fpo_id: UUID, correlation_id: str) -> FpoValidation:
    token = os.getenv("PROFILE_INTERNAL_SERVICE_TOKEN", "")
    payload = _get_json(
        f"/internal/v1/fpos/{fpo_id}/validation",
        headers={
            "X-Internal-Service-Token": token,
            "X-Correlation-ID": correlation_id,
        },
        not_found_code="FPO_PROFILE_NOT_FOUND",
        not_found_message="FPO profile was not found.",
    )
    return FpoValidation.model_validate(payload)
