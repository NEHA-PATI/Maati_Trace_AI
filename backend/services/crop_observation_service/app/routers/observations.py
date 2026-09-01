from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from services.crop_observation_service.app import observation_service, service
from services.crop_observation_service.app.dependencies import (
    RequestContext,
    get_request_context,
)
from services.crop_observation_service.app.schemas import (
    DailyStatusResponse,
    DailyStatusSaveRequest,
    PracticeObservationResponse,
    PracticeSaveRequest,
    ScreenResponse,
)

router = APIRouter(prefix="/v1/crop-observations", tags=["observations"])


@router.get(
    "/crop-cycles/{crop_cycle_id}/stages/{stage_code}/screen",
    response_model=ScreenResponse,
)
def get_stage_screen_endpoint(
    crop_cycle_id: UUID,
    stage_code: str,
    locale: str = Query(default="en-IN", max_length=10),
    context: RequestContext = Depends(get_request_context),
):
    return service.get_stage_screen(context, crop_cycle_id, stage_code, locale=locale)


@router.put(
    "/crop-cycles/{crop_cycle_id}/stages/{stage_code}/today",
    response_model=DailyStatusResponse,
)
def save_daily_status_endpoint(
    crop_cycle_id: UUID,
    stage_code: str,
    payload: DailyStatusSaveRequest,
    context: RequestContext = Depends(get_request_context),
):
    return observation_service.save_daily_status(context, crop_cycle_id, stage_code, payload)


@router.put(
    "/crop-cycles/{crop_cycle_id}/stages/{stage_code}/practices/{practice_code}/today",
    response_model=PracticeObservationResponse,
)
def save_practice_observation_endpoint(
    crop_cycle_id: UUID,
    stage_code: str,
    practice_code: str,
    payload: PracticeSaveRequest,
    context: RequestContext = Depends(get_request_context),
):
    return observation_service.save_practice_observation(
        context, crop_cycle_id, stage_code, practice_code, payload
    )
