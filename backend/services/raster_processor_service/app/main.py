import os

import pyproj
from fastapi import FastAPI

_proj_data_dir = pyproj.datadir.get_data_dir()
os.environ["PROJ_LIB"] = _proj_data_dir
os.environ["PROJ_DATA"] = _proj_data_dir

from shared.config.settings import settings
from shared.errors.api_errors import bad_request
from shared.logging.json_logging import configure_json_logging
from services.raster_processor_service.app.schemas import (
    HealthResponse,
    Sentinel2IndicesFromSearchRequest,
    Sentinel2IndicesPreviewRequest,
    Sentinel2IndicesPreviewResponse,
)
from services.raster_processor_service.app.sentinel2_indices import (
    RasterProcessorError,
    process_sentinel2_indices,
)
from services.raster_processor_service.app.stac_client import (
    RasterStacClientError,
    search_latest_sentinel2_scene,
)

SERVICE_NAME = "raster_processor_service"

configure_json_logging(SERVICE_NAME)

app = FastAPI(
    title="Raster Processor Service",
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


@app.post(
    "/v1/raster/sentinel2/indices/preview",
    response_model=Sentinel2IndicesPreviewResponse,
)
def sentinel2_indices_preview(payload: Sentinel2IndicesPreviewRequest):
    try:
        result = process_sentinel2_indices(
            scene=payload.scene.model_dump(),
            bbox=payload.bbox,
            h3_resolution=payload.h3_resolution,
        )
    except RasterProcessorError as exc:
        raise bad_request(str(exc), code="RASTER_PROCESSING_ERROR") from exc
    except Exception as exc:
        raise bad_request(
            f"Unexpected raster processing error: {exc}",
            code="RASTER_PROCESSING_ERROR",
        ) from exc

    return Sentinel2IndicesPreviewResponse(
        farm_id=payload.farm_id,
        provider=payload.scene.provider,
        collection_id=payload.scene.collection_id,
        scene_id=payload.scene.scene_id,
        scene_datetime=payload.scene.datetime,
        scene_cloud_cover=payload.scene.cloud_cover,
        bbox=payload.bbox,
        h3_resolution=payload.h3_resolution,
        source_assets_used=result["source_assets_used"],
        row_count=result["row_count"],
        total_pixel_count=result["total_pixel_count"],
        total_valid_pixel_count=result["total_valid_pixel_count"],
        total_cloud_pixel_count=result["total_cloud_pixel_count"],
        features=result["features"],
    )

@app.post(
    "/v1/raster/sentinel2/indices/preview-from-search",
    response_model=Sentinel2IndicesPreviewResponse,
)
def sentinel2_indices_preview_from_search(payload: Sentinel2IndicesFromSearchRequest):
    try:
        scene = search_latest_sentinel2_scene(
            provider=payload.provider,
            collection_id=payload.collection_id,
            bbox=payload.bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
        )

        result = process_sentinel2_indices(
            scene=scene,
            bbox=payload.bbox,
            h3_resolution=payload.h3_resolution,
            h3_cells_bigint=payload.h3_cells_bigint,
        )
    except (RasterProcessorError, RasterStacClientError) as exc:
        raise bad_request(str(exc), code="RASTER_PROCESSING_ERROR") from exc
    except Exception as exc:
        raise bad_request(
            f"Unexpected raster processing error: {exc}",
            code="RASTER_PROCESSING_ERROR",
        ) from exc

    return Sentinel2IndicesPreviewResponse(
        farm_id=payload.farm_id,
        provider=scene.get("provider"),
        collection_id=scene.get("collection_id"),
        scene_id=scene.get("scene_id"),
        scene_datetime=scene.get("datetime"),
        scene_cloud_cover=scene.get("cloud_cover"),
        bbox=payload.bbox,
        h3_resolution=payload.h3_resolution,
        source_assets_used=result["source_assets_used"],
        row_count=result["row_count"],
        total_pixel_count=result["total_pixel_count"],
        total_valid_pixel_count=result["total_valid_pixel_count"],
        total_cloud_pixel_count=result["total_cloud_pixel_count"],
        features=result["features"],
    )
