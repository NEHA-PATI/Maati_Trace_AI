from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: Literal["live", "ready"]
    environment: str


class GatewayRouteInfo(BaseModel):
    prefix: str
    target_service: str
    target_base_url: str