from __future__ import annotations

import time
from threading import Lock
from typing import Any
from uuid import UUID

import requests

from services.crop_observation_service.app.errors import CropObservationError
from shared.config.settings import settings

# get_authorized_farm is a chatty dependency: farm_registry_service itself
# re-resolves the caller's profile from profile_service on every call
# (crop_observation_service -> farm_registry_service -> profile_service,
# two network hops plus their own DB reads). A single "open a crop" click
# in the farmer UI calls it three times in a row (attach crop, start/find
# cycle, load the stage screen), and every stage-screen navigation and save
# calls it again — none of that changes access within the same few seconds,
# so we cache the authorized farm per (bearer token, farm_id) briefly. This
# is what actually made "My Crop" feel slow on every click.
_AUTHORIZED_FARM_TTL_SECONDS = 20.0
_MAX_CACHE_ENTRIES = 1000
_authorized_farm_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_cache_lock = Lock()


def _cache_get(key: tuple[str, str]) -> dict[str, Any] | None:
    with _cache_lock:
        entry = _authorized_farm_cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < time.monotonic():
            _authorized_farm_cache.pop(key, None)
            return None
        return value


def _cache_set(key: tuple[str, str], value: dict[str, Any]) -> None:
    with _cache_lock:
        if len(_authorized_farm_cache) >= _MAX_CACHE_ENTRIES:
            # Cheap unbounded-growth guard — drop everything rather than
            # maintain LRU bookkeeping for what is just a latency shortcut.
            _authorized_farm_cache.clear()
        _authorized_farm_cache[key] = (time.monotonic() + _AUTHORIZED_FARM_TTL_SECONDS, value)


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

    Cached briefly per (bearer token, farm_id) — see _authorized_farm_cache
    above.
    """
    cache_key = (authorization, str(farm_id))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

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

    farm = response.json()
    _cache_set(cache_key, farm)
    return farm
