from __future__ import annotations

import secrets
from dataclasses import dataclass
from uuid import UUID

from fastapi import Header, Request

from services.profile_service.app.auth_client import (
    get_current_user_from_auth_service,
)
from services.profile_service.app.config_validation import (
    get_profile_config,
)
from services.profile_service.app.errors import ProfileError
from services.profile_service.app.middleware import (
    get_correlation_id,
)
from services.profile_service.app.schemas import (
    AuthenticatedUser,
)


@dataclass(frozen=True, slots=True)
class RequestContext:
    principal: AuthenticatedUser
    correlation_id: str
    ip_address: str | None
    authorization: str
    fpo_context_id: UUID | None


async def get_request_context(
    request: Request,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
    x_fpo_id: UUID | None = Header(
        default=None,
        alias="X-FPO-ID",
    ),
) -> RequestContext:
    principal = await get_current_user_from_auth_service(
        authorization
    )

    return RequestContext(
        principal=principal,
        correlation_id=get_correlation_id(),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        authorization=authorization or "",
        fpo_context_id=x_fpo_id,
    )


def require_internal_service(
    x_internal_service_token: str | None = Header(
        default=None,
        alias="X-Internal-Service-Token",
    ),
) -> None:
    config = get_profile_config()

    if (
        not x_internal_service_token
        or not secrets.compare_digest(
            x_internal_service_token,
            config.internal_service_token,
        )
    ):
        raise ProfileError(
            "INTERNAL_SERVICE_UNAUTHORIZED",
            "Internal service authentication failed.",
            401,
        )