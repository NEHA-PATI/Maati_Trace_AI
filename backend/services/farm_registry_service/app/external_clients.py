import requests

from shared.config.settings import settings


class ExternalServiceError(RuntimeError):
    pass


def validate_location(
    state_name: str,
    district_name: str,
    block_name: str | None,
    block_code: int | None,
) -> dict:
    url = f"{settings.district_boundary_service_url}/v1/location/validate"

    payload = {
        "state_name": state_name,
        "district_name": district_name,
        "block_name": block_name,
        "block_code": block_code,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
    except requests.RequestException as exc:
        raise ExternalServiceError(f"District service unavailable: {exc}") from exc

    if response.status_code != 200:
        raise ExternalServiceError(f"District service error: {response.text}")

    data = response.json()

    if not data.get("is_valid"):
        raise ExternalServiceError(data.get("message", "Invalid location"))

    return data


def create_h3_preview(
    polygon: dict,
    resolution: int,
    max_cells: int | None = 1000,
) -> dict:
    url = f"{settings.boundary_index_service_url}/v1/h3/preview"

    payload = {
        "polygon": polygon,
        "resolution": resolution,
        "include_cells": True,
        "max_cells": max_cells,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
    except requests.RequestException as exc:
        raise ExternalServiceError(f"Boundary service unavailable: {exc}") from exc

    if response.status_code != 200:
        raise ExternalServiceError(f"Boundary service error: {response.text}")

    return response.json()
