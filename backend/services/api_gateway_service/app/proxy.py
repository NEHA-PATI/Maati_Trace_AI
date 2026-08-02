from __future__ import annotations

import httpx
from fastapi import Request
from fastapi.responses import Response

from shared.config.settings import settings


class GatewayProxyError(RuntimeError):
    pass


ROUTE_TARGETS = {
    "auth": settings.auth_service_url,
    "location": settings.district_boundary_service_url,
    "h3": settings.boundary_index_service_url,
    "profiles": settings.profile_service_url,
    "fpos": settings.farm_registry_service_url,
    "farmers": settings.farm_registry_service_url,
    "farms": settings.farm_registry_service_url,
    "stac": settings.stac_catalog_service_url,
    "raster": settings.raster_processor_service_url,
    "lakehouse": settings.lakehouse_writer_service_url,
    "hot-stream": settings.hot_stream_orchestrator_service_url,
    "farm-analysis": settings.hot_stream_orchestrator_service_url,
    "analytics": settings.analytics_query_service_url,
}

HEALTH_ROUTE_TARGETS = {
    "auth": settings.auth_service_url,
    "location": settings.district_boundary_service_url,
    "registry": settings.farm_registry_service_url,
    "profile": settings.profile_service_url,
    "boundary": settings.boundary_index_service_url,
    "stac": settings.stac_catalog_service_url,
    "raster": settings.raster_processor_service_url,
    "lakehouse": settings.lakehouse_writer_service_url,
    "orchestrator": settings.hot_stream_orchestrator_service_url,
    "analytics": settings.analytics_query_service_url,
}


def get_route_targets() -> dict[str, str]:
    return ROUTE_TARGETS.copy()


def _build_target_url(prefix: str, rest_path: str, query_string: bytes) -> str:
    base_url = ROUTE_TARGETS.get(prefix)

    if not base_url:
        raise GatewayProxyError(f"Unsupported gateway route: {prefix}")

    clean_base = base_url.rstrip("/")

    # Public gateway path:
    # /api/auth/login
    #
    # Internal service path:
    # /v1/auth/login
    #
    # So we map:
    # /api/{prefix}/{rest_path} -> /v1/{prefix}/{rest_path}
    if prefix == "location":
        location_aliases = {
            "states": "/v1/states",
            "districts": "/v1/districts",
            "blocks": "/v1/blocks",
            "validate": "/v1/location/validate",
            "location/validate": "/v1/location/validate",
            "location/stats": "/v1/location/stats",
        }
        target_path = location_aliases.get(rest_path, "/v1/location")
    else:
        target_path = f"/v1/{prefix}"
        if rest_path:
            target_path += f"/{rest_path}"

    target_url = f"{clean_base}{target_path}"

    if query_string:
        target_url += f"?{query_string.decode('utf-8')}"

    return target_url


def _build_health_target_url(service_name: str, check: str) -> str:
    base_url = HEALTH_ROUTE_TARGETS.get(service_name)
    if not base_url:
        raise GatewayProxyError(f"Unsupported gateway health route: {service_name}")
    if check not in {"live", "ready"}:
        raise GatewayProxyError(f"Unsupported gateway health check: {check}")
    return f"{base_url.rstrip('/')}/health/{check}"


def _response_from_upstream(upstream_response: httpx.Response) -> Response:
    response = Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_response.headers.get("content-type"),
    )

    excluded_headers = {
        "content-encoding",
        "transfer-encoding",
        "connection",
        "content-length",
    }

    for key, value in upstream_response.headers.multi_items():
        if key.lower() in excluded_headers:
            continue
        response.headers.append(key, value)

    return response


async def _proxy_request(
    target_url: str,
    request: Request,
    *,
    method: str | None = None,
) -> Response:
    body = await request.body()

    excluded_headers = {
        "host",
        "content-length",
        "connection",
    }

    headers: dict[str, str] = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in excluded_headers
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            upstream_response = await client.request(
                method=method or request.method,
                url=target_url,
                headers=headers,
                content=body if (method or request.method) != "GET" else None,
            )
    except httpx.RequestError as exc:
        raise GatewayProxyError(f"Failed to reach upstream service: {exc}") from exc

    return _response_from_upstream(upstream_response)


async def proxy_health_request(service_name: str, check: str, request: Request) -> Response:
    target_url = _build_health_target_url(service_name=service_name, check=check)
    return await _proxy_request(target_url, request, method="GET")


async def proxy_request(prefix: str, rest_path: str, request: Request) -> Response:
    target_url = _build_target_url(
        prefix=prefix,
        rest_path=rest_path,
        query_string=request.scope.get("query_string", b""),
    )
    return await _proxy_request(target_url, request)
