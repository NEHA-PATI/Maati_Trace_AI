from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from services.lakehouse_writer_service.app.parquet_writer import (
    write_parquet_rows,
)
from services.lakehouse_writer_service.app.repository import (
    get_farm_context,
    upsert_sentinel2_feature_rows,
)
from services.lakehouse_writer_service.app.schemas import (
    Sentinel2LakehouseWriteRequest,
)


DATASET_NAME = "h3_sentinel2_features"


class LakehouseWriterError(RuntimeError):
    pass


def _parse_scene_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    cleaned = value.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise LakehouseWriterError(f"Invalid scene_datetime: {value}") from exc


def _snapshot_date_from_scene_datetime(scene_datetime: datetime | None) -> date:
    if scene_datetime is None:
        return date.today()

    return scene_datetime.date()


def _feature_to_row(
    feature: dict[str, Any],
    farm_context: dict[str, Any],
    payload: Sentinel2LakehouseWriteRequest,
    scene_datetime: datetime | None,
    snapshot_date: date,
    parquet_uri: str | None,
) -> dict[str, Any]:
    return {
        "farm_id": str(payload.farm_id),
        "farmer_id": str(farm_context["farmer_id"]),
        "fpo_id": str(farm_context["fpo_id"]) if farm_context.get("fpo_id") else None,

        "state_name": farm_context["state_name"],
        "district_name": farm_context["district_name"],
        "district_code": farm_context.get("district_code"),
        "block_name": farm_context.get("block_name"),
        "block_code": farm_context.get("block_code"),

        "snapshot_date": snapshot_date,
        "scene_id": payload.scene_id,
        "scene_datetime": scene_datetime,
        "scene_cloud_cover": payload.scene_cloud_cover,

        "h3_resolution": payload.h3_resolution,
        "h3_index": feature["h3_index"],

        "pixel_count": feature.get("pixel_count", 0),
        "valid_pixel_count": feature.get("valid_pixel_count", 0),
        "cloud_pixel_count": feature.get("cloud_pixel_count", 0),
        "nodata_pixel_count": feature.get("nodata_pixel_count", 0),
        "cloud_percentage": feature.get("cloud_percentage", 0),

        "observed_area_m2": feature.get("observed_area_m2"),
        "valid_area_m2": feature.get("valid_area_m2"),
        "cloud_area_m2": feature.get("cloud_area_m2"),
        "shadow_area_m2": feature.get("shadow_area_m2"),
        "water_area_m2": feature.get("water_area_m2"),
        "snow_area_m2": feature.get("snow_area_m2"),
        "nodata_area_m2": feature.get("nodata_area_m2"),
        "invalid_area_m2": feature.get("invalid_area_m2"),
        "valid_fraction": feature.get("valid_fraction"),

        "mean_blue": feature.get("mean_blue"),
        "mean_green": feature.get("mean_green"),
        "mean_red": feature.get("mean_red"),
        "mean_rededge1": feature.get("mean_rededge1"),
        "mean_rededge2": feature.get("mean_rededge2"),
        "mean_rededge3": feature.get("mean_rededge3"),
        "mean_nir": feature.get("mean_nir"),
        "mean_nir08": feature.get("mean_nir08"),
        "mean_swir16": feature.get("mean_swir16"),
        "mean_swir22": feature.get("mean_swir22"),

        "ndvi": feature.get("ndvi"),
        "gndvi": feature.get("gndvi"),
        "evi": feature.get("evi"),
        "savi": feature.get("savi"),

        "ndmi": feature.get("ndmi"),
        "ndwi": feature.get("ndwi"),
        "mndwi": feature.get("mndwi"),
        "msi": feature.get("msi"),

        "bsi": feature.get("bsi"),
        "nbr": feature.get("nbr"),
        "nbr2": feature.get("nbr2"),

        "ndre": feature.get("ndre"),
        "reci": feature.get("reci"),

        "fvc_proxy": feature.get("fvc_proxy"),
        "nirv": feature.get("nirv"),

        "optical_resolution_m": feature.get(
            "optical_resolution_m",
            10,
        ),
        "rededge_swir_resolution_m": feature.get(
            "rededge_swir_resolution_m",
            20,
        ),
        "processing_version": feature.get(
            "processing_version",
            "s2_zonal_v1",
        ),

        "source_assets_used": payload.source_assets_used,
        "parquet_uri": parquet_uri,
    }


def write_sentinel2_features(payload: Sentinel2LakehouseWriteRequest) -> dict[str, Any]:
    if not payload.features:
        raise LakehouseWriterError("No Sentinel-2 feature rows supplied")

    farm_context = get_farm_context(payload.farm_id)

    scene_datetime = _parse_scene_datetime(payload.scene_datetime)
    snapshot_date = _snapshot_date_from_scene_datetime(scene_datetime)

    rows_without_uri = [
        _feature_to_row(
            feature=feature.model_dump(),
            farm_context=farm_context,
            payload=payload,
            scene_datetime=scene_datetime,
            snapshot_date=snapshot_date,
            parquet_uri=None,
        )
        for feature in payload.features
    ]

    parquet_uri = write_parquet_rows(
        dataset=DATASET_NAME,
        rows=rows_without_uri,
        state_name=farm_context["state_name"],
        district_name=farm_context["district_name"],
        block_name=farm_context.get("block_name"),
        snapshot_date=snapshot_date,
    )

    rows_with_uri = [
        {
            **row,
            "parquet_uri": parquet_uri,
        }
        for row in rows_without_uri
    ]

    postgres_rows_written = upsert_sentinel2_feature_rows(rows_with_uri)

    return {
        "dataset": DATASET_NAME,
        "farm_id": payload.farm_id,
        "farmer_id": farm_context["farmer_id"],
        "fpo_id": farm_context.get("fpo_id"),
        "snapshot_date": snapshot_date,
        "scene_id": payload.scene_id,
        "row_count": len(rows_with_uri),
        "postgres_rows_written": postgres_rows_written,
        "parquet_rows_written": len(rows_with_uri),
        "parquet_uri": parquet_uri,
    }