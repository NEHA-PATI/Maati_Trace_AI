from __future__ import annotations

import os
from typing import Any

import requests

from shared.config.settings import settings
from services.farm_registry_service.app.errors import FarmRegistryError


def _message(response: requests.Response, fallback: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or fallback

    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail.get("message") or fallback
    return payload.get("message") or fallback


def validate_location(
    *,
    state_name: str,
    district_name: str,
    block_name: str | None,
    block_code: int | None,
    correlation_id: str,
) -> dict[str, Any]:
    payload = {
        "state_name": state_name,
        "district_name": district_name,
        "block_name": block_name,
        "block_code": block_code,
    }
    try:
        response = requests.post(
            f"{settings.district_boundary_service_url}/v1/location/validate",
            json=payload,
            headers={"X-Correlation-ID": correlation_id},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise FarmRegistryError(
            "LOCATION_SERVICE_UNAVAILABLE",
            "Location validation is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code != 200:
        raise FarmRegistryError(
            "LOCATION_VALIDATION_FAILED",
            _message(response, "Location validation failed."),
            422,
        )

    data = response.json()
    if not data.get("is_valid"):
        raise FarmRegistryError(
            "INVALID_LOCATION",
            data.get("message") or "Invalid farm location.",
            422,
        )
    return data


def create_h3_preview(
    *,
    polygon: dict[str, Any],
    resolution: int,
    correlation_id: str,
) -> dict[str, Any]:
    max_cells = int(os.getenv("MAX_FARM_H3_CELLS", str(settings.max_farm_h3_cells)))
    payload = {
        "polygon": polygon,
        "resolution": resolution,
        "include_cells": True,
        "max_cells": max_cells,
    }
    try:
        response = requests.post(
            f"{settings.boundary_index_service_url}/v1/h3/preview",
            json=payload,
            headers={"X-Correlation-ID": correlation_id},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise FarmRegistryError(
            "H3_SERVICE_UNAVAILABLE",
            "H3 generation is temporarily unavailable.",
            503,
            internal_message=str(exc),
        ) from exc

    if response.status_code != 200:
        raise FarmRegistryError(
            "H3_PREVIEW_FAILED",
            _message(response, "The farm boundary could not be converted to H3 cells."),
            422,
        )

    data = response.json()
    cells = data.get("h3_cells_bigint")
    cell_count = data.get("cell_count")
    if not isinstance(cells, list) or not cells:
        raise FarmRegistryError(
            "EMPTY_H3_COVERAGE",
            "The farm boundary did not produce any H3 cells.",
            422,
        )
    if cell_count != len(cells):
        raise FarmRegistryError(
            "INVALID_H3_RESPONSE",
            "H3 generation returned inconsistent cell counts.",
            502,
        )
    if cell_count > max_cells:
        raise FarmRegistryError(
            "H3_CELL_LIMIT_EXCEEDED",
            "The farm boundary produces too many H3 cells.",
            422,
        )
    return data
