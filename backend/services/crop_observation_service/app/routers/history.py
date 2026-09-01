from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from services.crop_observation_service.app import history_service
from services.crop_observation_service.app.dependencies import (
    RequestContext,
    get_request_context,
)
from services.crop_observation_service.app.schemas import HistoryResponse

router = APIRouter(prefix="/v1/crop-observations", tags=["history"])


@router.get(
    "/crop-cycles/{crop_cycle_id}/history",
    response_model=HistoryResponse,
)
def get_history_endpoint(
    crop_cycle_id: UUID,
    before: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    context: RequestContext = Depends(get_request_context),
):
    return history_service.get_history(context, crop_cycle_id, before=before, limit=limit)
