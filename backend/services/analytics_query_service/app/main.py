from uuid import UUID

from fastapi import FastAPI, Query

from shared.config.settings import settings
from shared.errors.api_errors import bad_request, not_found
from shared.logging.json_logging import configure_json_logging
from services.analytics_query_service.app.repository import (
    AnalyticsQueryRepositoryError,
    get_grid_cell_details,
    get_farm_grid_cells,
    get_farm_h3_cells,
    get_farm_trends,
    get_farmer_analytics_summary,
    get_fpo_analytics_summary,
    get_grid_value_history,
    get_latest_grid_values,
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


@app.get("/v1/analytics/farms/{farm_id}/trends")
def farm_trends(farm_id: UUID):
    return {"farm_id": str(farm_id), "items": get_farm_trends(farm_id)}


@app.get("/v1/analytics/farms/{farm_id}/h3-cells")
def farm_h3_cells(farm_id: UUID):
    return {"farm_id": str(farm_id), "items": get_farm_h3_cells(farm_id)}


@app.get("/v1/analytics/farms/{farm_id}/grid-cells")
def farm_grid_cells(farm_id: UUID):
    return {"farm_id": str(farm_id), "items": get_farm_grid_cells(farm_id)}


@app.get("/v1/analytics/farms/{farm_id}/grid-values/latest")
def farm_grid_values_latest(farm_id: UUID):
    return {"farm_id": str(farm_id), "items": get_latest_grid_values(farm_id)}


@app.get("/v1/analytics/farms/{farm_id}/grid-values/history")
def farm_grid_values_history(
    farm_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
):
    return {"farm_id": str(farm_id), "items": get_grid_value_history(farm_id, limit)}


@app.get("/v1/analytics/farms/{farm_id}/grid-cells/{grid_cell_id}/details")
def farm_grid_cell_details(farm_id: UUID, grid_cell_id: UUID):
    result = get_grid_cell_details(farm_id, grid_cell_id)
    if result is None:
        raise not_found("Grid cell not found")
    return result


@app.get("/v1/analytics/farmers/{farmer_id}/summary")
def farmer_summary(farmer_id: UUID):
    return get_farmer_analytics_summary(farmer_id)


@app.get("/v1/analytics/fpos/{fpo_id}/summary")
def fpo_summary(fpo_id: UUID):
    return get_fpo_analytics_summary(fpo_id)
