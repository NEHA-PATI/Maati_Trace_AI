from uuid import UUID

from fastapi import FastAPI, Query

from shared.config.settings import settings
from shared.errors.api_errors import bad_request, not_found
from shared.logging.json_logging import configure_json_logging
from services.analytics_query_service.app.repository import (
    AnalyticsQueryRepositoryError,
)
from services.analytics_query_service.app.schemas import (
    FarmIntelligenceSummaryResponse,
    FarmSentinel2HistoryResponse,
    FarmSentinel2LatestResponse,
    HealthResponse,
)
from services.analytics_query_service.app.service import (
    build_history_response,
    build_latest_response,
    build_summary_response,
)

SERVICE_NAME = "analytics_query_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Analytics Query Service",
    version="1.0.0",
)


@app.get("/health/live", response_model=HealthResponse)
def live():
    return HealthResponse(
        service=SERVICE_NAME,
        status="live",
        environment=settings.app_env,
    )


@app.get("/health/ready", response_model=HealthResponse)
def ready():
    return HealthResponse(
        service=SERVICE_NAME,
        status="ready",
        environment=settings.app_env,
    )


@app.get(
    "/v1/analytics/farms/{farm_id}/sentinel2/latest",
    response_model=FarmSentinel2LatestResponse,
)
def latest_sentinel2(farm_id: UUID):
    try:
        result = build_latest_response(farm_id)
    except AnalyticsQueryRepositoryError as exc:
        raise bad_request(str(exc), code="ANALYTICS_QUERY_ERROR") from exc

    if result is None:
        raise not_found("No Sentinel-2 analysis found for this farm")

    return FarmSentinel2LatestResponse(**result)


@app.get(
    "/v1/analytics/farms/{farm_id}/sentinel2/history",
    response_model=FarmSentinel2HistoryResponse,
)
def sentinel2_history(
    farm_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        result = build_history_response(farm_id=farm_id, limit=limit)
    except AnalyticsQueryRepositoryError as exc:
        raise bad_request(str(exc), code="ANALYTICS_QUERY_ERROR") from exc

    return FarmSentinel2HistoryResponse(**result)


@app.get(
    "/v1/analytics/farms/{farm_id}/summary",
    response_model=FarmIntelligenceSummaryResponse,
)
def farm_summary(farm_id: UUID):
    try:
        result = build_summary_response(farm_id)
    except AnalyticsQueryRepositoryError as exc:
        raise bad_request(str(exc), code="ANALYTICS_QUERY_ERROR") from exc

    return FarmIntelligenceSummaryResponse(**result)