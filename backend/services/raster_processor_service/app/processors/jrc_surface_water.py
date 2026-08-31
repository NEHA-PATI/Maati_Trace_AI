from __future__ import annotations

from typing import Any

import numpy as np

from services.raster_processor_service.app.common.h3_generic import aggregate_continuous_h3
from services.raster_processor_service.app.common.raster_io import build_target_grid, read_asset_to_grid
from services.raster_processor_service.app.processors.helpers import find_asset


PROCESSING_VERSION = "jrc_gsw_zonal_v1"


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    occurrence_asset = find_asset(item, "occurrence")
    recurrence_asset = find_asset(item, "recurrence", required=False)
    seasonality_asset = find_asset(item, "seasonality", required=False)
    extent_asset = find_asset(item, "extent", required=False)
    grid = build_target_grid(payload["bbox"], 30.0)

    occurrence = read_asset_to_grid(occurrence_asset["href"], grid, resampling="bilinear")
    occurrence[(occurrence < 0) | (occurrence > 100)] = np.nan
    valid = np.isfinite(occurrence)
    arrays: dict[str, np.ndarray] = {"water_occurrence_pct": occurrence}

    if recurrence_asset:
        recurrence = read_asset_to_grid(recurrence_asset["href"], grid, resampling="bilinear")
        recurrence[(recurrence < 0) | (recurrence > 100)] = np.nan
        arrays["water_recurrence_pct"] = recurrence
    if seasonality_asset:
        seasonality = read_asset_to_grid(seasonality_asset["href"], grid, resampling="nearest")
        seasonality[(seasonality < 0) | (seasonality > 12)] = np.nan
        arrays["water_seasonality_months"] = seasonality
        arrays["permanent_water_fraction"] = np.where(np.isfinite(seasonality), (seasonality >= 12).astype(float), np.nan)
    if extent_asset:
        extent = read_asset_to_grid(extent_asset["href"], grid, resampling="nearest")
        arrays["historic_extent_fraction"] = np.where(np.isfinite(extent), (extent > 0).astype(float), np.nan)

    rows = aggregate_continuous_h3(
        arrays=arrays,
        valid_mask=valid,
        raster_transform=grid.transform,
        raster_crs=grid.crs,
        h3_cells_bigint=payload["h3_cells_bigint"],
        farm_polygon_geojson=payload["farm_polygon_geojson"],
    )
    for row in rows:
        row["source_dataset"] = "jrc_surface_water"
        row["source_reference_period"] = "1984-2020"
        row["native_resolution_m"] = 30.0

    used = [a["key"] for a in [occurrence_asset, recurrence_asset, seasonality_asset, extent_asset] if a]
    return {
        "dataset_key": "jrc_surface_water",
        "provider": item["provider"],
        "source_collection": item.get("collection_id"),
        "source_item_id": item["item_id"],
        "source_datetime": item.get("datetime"),
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "h3",
        "h3_resolution": payload["h3_resolution"],
        "source_assets_used": used,
        "record_count": len(rows),
        "records": rows,
        "metadata": {"interpretation": "historical water context, not current flood detection"},
    }
