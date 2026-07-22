from __future__ import annotations

import math
from typing import Any

import h3
import numpy as np
from pyproj import CRS, Transformer
from rasterio.windows import Window, bounds as window_bounds, from_bounds
from shapely.geometry import Polygon, box, shape
from shapely.ops import transform as transform_geometry


class H3ZonalStatisticsError(RuntimeError):
    pass


BAND_FIELDS = {
    "mean_blue": "blue",
    "mean_green": "green",
    "mean_red": "red",
    "mean_rededge1": "rededge1",
    "mean_rededge2": "rededge2",
    "mean_rededge3": "rededge3",
    "mean_nir": "nir",
    "mean_nir08": "nir08",
    "mean_swir16": "swir16",
    "mean_swir22": "swir22",
}


def _clean(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), 6)


def _h3_polygon_wgs84(h3_index: int) -> Polygon:
    boundary = h3.cell_to_boundary(
        h3.int_to_str(int(h3_index))
    )

    # h3 returns latitude, longitude.
    # Shapely expects longitude, latitude.
    return Polygon([
        (lng, lat)
        for lat, lng in boundary
    ])


def _weighted_mean(
    values: np.ndarray,
    valid_mask: np.ndarray,
    area_weights: np.ndarray,
) -> float | None:
    usable = (
        valid_mask
        & np.isfinite(values)
        & (area_weights > 0)
    )

    if not np.any(usable):
        return None

    denominator = float(np.sum(area_weights[usable]))

    if denominator <= 0:
        return None

    numerator = float(
        np.sum(values[usable] * area_weights[usable])
    )

    return _clean(numerator / denominator)


def _pixel_overlap_weights(
    geometry: Any,
    raster_transform: Any,
    raster_shape: tuple[int, int],
) -> tuple[np.ndarray, tuple[slice, slice]]:
    height, width = raster_shape

    raw_window = from_bounds(
        *geometry.bounds,
        transform=raster_transform,
    )

    row_start = max(0, math.floor(raw_window.row_off))
    col_start = max(0, math.floor(raw_window.col_off))

    row_stop = min(
        height,
        math.ceil(raw_window.row_off + raw_window.height),
    )
    col_stop = min(
        width,
        math.ceil(raw_window.col_off + raw_window.width),
    )

    if row_start >= row_stop or col_start >= col_stop:
        empty = np.zeros((0, 0), dtype=np.float64)
        return empty, (slice(0, 0), slice(0, 0))

    weights = np.zeros(
        (
            row_stop - row_start,
            col_stop - col_start,
        ),
        dtype=np.float64,
    )

    for local_row, raster_row in enumerate(
        range(row_start, row_stop)
    ):
        for local_col, raster_col in enumerate(
            range(col_start, col_stop)
        ):
            left, bottom, right, top = window_bounds(
                Window(
                    raster_col,
                    raster_row,
                    1,
                    1,
                ),
                raster_transform,
            )

            pixel_polygon = box(
                left,
                bottom,
                right,
                top,
            )

            overlap = geometry.intersection(pixel_polygon)

            if not overlap.is_empty:
                weights[local_row, local_col] = max(
                    0.0,
                    float(overlap.area),
                )

    return weights, (
        slice(row_start, row_stop),
        slice(col_start, col_stop),
    )


def _empty_row(h3_index: int) -> dict[str, Any]:
    return {
        "h3_index": int(h3_index),
        "pixel_count": 0,
        "valid_pixel_count": 0,
        "cloud_pixel_count": 0,
        "nodata_pixel_count": 0,
        "cloud_percentage": 0.0,
        "observed_area_m2": 0.0,
        "valid_area_m2": 0.0,
        "cloud_area_m2": 0.0,
        "shadow_area_m2": 0.0,
        "water_area_m2": 0.0,
        "snow_area_m2": 0.0,
        "nodata_area_m2": 0.0,
        "invalid_area_m2": 0.0,
        "valid_fraction": 0.0,
        "optical_resolution_m": 10,
        "rededge_swir_resolution_m": 20,
        "processing_version": "s2_zonal_v1",
    }


def aggregate_h3_zonal_statistics(
    *,
    bands: dict[str, np.ndarray],
    indices: dict[str, np.ndarray],
    masks: dict[str, np.ndarray],
    raster_transform: Any,
    raster_crs: Any,
    h3_cells_bigint: list[int],
    farm_polygon_geojson: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if "red" not in bands:
        raise H3ZonalStatisticsError(
            "The red reference band is required"
        )

    crs = CRS.from_user_input(raster_crs)

    if not crs.is_projected:
        raise H3ZonalStatisticsError(
            "Expected projected Sentinel-2 CRS for "
            f"square-metre areas, received {crs}."
        )

    to_raster_crs = Transformer.from_crs(
        "EPSG:4326",
        crs,
        always_xy=True,
    ).transform

    farm_wgs84 = (
        shape(farm_polygon_geojson)
        if farm_polygon_geojson
        else None
    )

    if farm_wgs84 is not None:
        if farm_wgs84.is_empty or not farm_wgs84.is_valid:
            raise H3ZonalStatisticsError(
                "Farm polygon is empty or invalid"
            )

    results: list[dict[str, Any]] = []
    raster_shape = bands["red"].shape

    unique_h3_cells = sorted({
        int(value)
        for value in h3_cells_bigint
        if value is not None
    })

    for h3_index in unique_h3_cells:
        cell_wgs84 = _h3_polygon_wgs84(h3_index)

        clipped_wgs84 = (
            cell_wgs84.intersection(farm_wgs84)
            if farm_wgs84 is not None
            else cell_wgs84
        )

        if clipped_wgs84.is_empty:
            results.append(_empty_row(h3_index))
            continue

        clipped_projected = transform_geometry(
            to_raster_crs,
            clipped_wgs84,
        )

        weights, slices = _pixel_overlap_weights(
            geometry=clipped_projected,
            raster_transform=raster_transform,
            raster_shape=raster_shape,
        )

        if weights.size == 0 or float(np.sum(weights)) <= 0:
            results.append(_empty_row(h3_index))
            continue

        touched = weights > 0

        local_masks = {
            name: values[slices]
            for name, values in masks.items()
        }

        observed_area = float(np.sum(weights))

        def area(mask_name: str) -> float:
            selected = touched & local_masks[mask_name]
            return float(np.sum(weights[selected]))

        valid_area = area("valid")
        cloud_area = area("cloud")

        row: dict[str, Any] = {
            "h3_index": h3_index,

            # Legacy integer counters remain for compatibility.
            "pixel_count": int(np.count_nonzero(touched)),
            "valid_pixel_count": int(
                np.count_nonzero(
                    touched & local_masks["valid"]
                )
            ),
            "cloud_pixel_count": int(
                np.count_nonzero(
                    touched & local_masks["cloud"]
                )
            ),
            "nodata_pixel_count": int(
                np.count_nonzero(
                    touched & local_masks["nodata"]
                )
            ),

            # Area values are the authoritative quality fields.
            "cloud_percentage": round(
                (cloud_area / observed_area) * 100.0,
                4,
            ),
            "observed_area_m2": round(
                observed_area,
                4,
            ),
            "valid_area_m2": round(
                valid_area,
                4,
            ),
            "cloud_area_m2": round(
                cloud_area,
                4,
            ),
            "shadow_area_m2": round(
                area("shadow"),
                4,
            ),
            "water_area_m2": round(
                area("water"),
                4,
            ),
            "snow_area_m2": round(
                area("snow"),
                4,
            ),
            "nodata_area_m2": round(
                area("nodata"),
                4,
            ),
            "invalid_area_m2": round(
                area("invalid"),
                4,
            ),
            "valid_fraction": round(
                valid_area / observed_area,
                6,
            ),

            "optical_resolution_m": 10,
            "rededge_swir_resolution_m": 20,
            "processing_version": "s2_zonal_v1",
        }

        for output_name, band_name in BAND_FIELDS.items():
            if band_name not in bands:
                continue

            row[output_name] = _weighted_mean(
                bands[band_name][slices],
                local_masks["valid"],
                weights,
            )

        for index_name, values in indices.items():
            row[index_name] = _weighted_mean(
                values[slices],
                local_masks["valid"],
                weights,
            )

        results.append(row)

    return results



