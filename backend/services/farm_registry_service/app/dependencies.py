from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID

from fastapi import Header

from services.farm_registry_service.app.auth_client import (
    AuthPrincipal,
    get_current_user_from_auth_service,
)
from services.farm_registry_service.app.errors import FarmRegistryError
from services.farm_registry_service.app.middleware import get_correlation_id


@dataclass(frozen=True)
class RequestContext:
    authorization: str
    correlation_id: str
    principal: AuthPrincipal
    fpo_context_id: UUID | None = None


def get_request_context(
    authorization: str | None = Header(default=None),
    x_fpo_id: UUID | None = Header(default=None),
) -> RequestContext:
    correlation_id = get_correlation_id()
    principal = get_current_user_from_auth_service(
        authorization,
        correlation_id=correlation_id,
    )
    return RequestContext(
        authorization=authorization or "",
        correlation_id=correlation_id,
        principal=principal,
        fpo_context_id=x_fpo_id,
    )


def require_internal_farm_service(
    x_internal_service_token: str | None = Header(default=None),
) -> None:
    expected = os.getenv("FARM_REGISTRY_INTERNAL_SERVICE_TOKEN", "")
    if not expected or x_internal_service_token != expected:
        raise FarmRegistryError(
            "INVALID_INTERNAL_SERVICE_TOKEN",
            "Internal farm access is not allowed.",
            403,
        )
