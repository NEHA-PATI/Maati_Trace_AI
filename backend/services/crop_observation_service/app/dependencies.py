from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header

from services.crop_observation_service.app.auth_client import (
    AuthPrincipal,
    get_current_user,
)
from services.crop_observation_service.app.middleware import get_correlation_id


@dataclass(frozen=True)
class RequestContext:
    authorization: str
    correlation_id: str
    principal: AuthPrincipal


def get_request_context(
    authorization: str | None = Header(default=None),
) -> RequestContext:
    correlation_id = get_correlation_id()
    principal = get_current_user(authorization, correlation_id=correlation_id)
    return RequestContext(
        authorization=authorization or "",
        correlation_id=correlation_id,
        principal=principal,
    )
