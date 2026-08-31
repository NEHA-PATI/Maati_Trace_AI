from __future__ import annotations

import math
from typing import Any

import h3
import numpy as np
from pyproj import CRS, Transformer
from rasterio.windows import Window, bounds as window_bounds, from_bounds
from shapely.geometry import Polygon, box, shape
from shapely.ops import transform as transform_geometry


class GenericZonalError(RuntimeError):
    pass


def _h3_polygon_wgs84(h3_index: int) -> Polygon:
    boundary = h3.cell_to_boundary(h3.int_to_str(int(h3_index)))
    return Polygon([(lng, lat) for lat, lng in boundary])


def _pixel_overlap_weights(
    geometry: Any,
    raster_transform: Any,
    raster_shape: tuple[int, int],
) -> tuple[np.ndarray, tuple[slice, slice]]:
    height, width = raster_shape
    raw_window = from_bounds(*geometry.bounds, transform=raster_transform)
    row_start = max(0, math.floor(raw_window.row_off))
    col_start = max(0, math.floor(raw_window.col_off))
    row_stop = min(height, math.ceil(raw_window.row_off + raw_window.height))
    col_stop = min(width, math.ceil(raw_window.col_off + raw_window.width))
    if row_start >= row_stop or col_start >= col_stop:
        return np.zeros((0, 0), dtype="float64"), (slice(0, 0), slice(0, 0))

    weights = np.zeros((row_stop - row_start, col_stop - col_start), dtype="float64")
    for local_row, raster_row in enumerate(range(row_start, row_stop)):
        for local_col, raster_col in enumerate(range(col_start, col_stop)):
            left, bottom, right, top = window_bounds(
                Window(raster_col, raster_row, 1, 1), raster_transform
            )
            overlap = geometry.intersection(box(left, bottom, right, top))
            if not overlap.is_empty:
                weights[local_row, local_col] = max(0.0, float(overlap.area))
    return weights, (slice(row_start, row_stop), slice(col_start, col_stop))


def _weighted_mean(values: np.ndarray, mask: np.ndarray, weights: np.ndarray) -> float | None:
    usable = mask & np.isfinite(values) & (weights > 0)
    if not np.any(usable):
        return None
    denominator = float(np.sum(weights[usable]))
    if denominator <= 0:
        return None
    return float(np.sum(values[usable] * weights[usable]) / denominator)


def _stat(values: np.ndarray, mask: np.ndarray, weights: np.ndarray, reducer: str) -> float | None:
    usable = mask & np.isfinite(values) & (weights > 0)
    if not np.any(usable):
        return None
    selected = values[usable]
    if reducer == "mean":
        return _weighted_mean(values, mask, weights)
    if reducer == "min":
        return float(np.min(selected))
    if reducer == "max":
        return float(np.max(selected))
    raise GenericZonalError(f"Unsupported reducer: {reducer}")


def aggregate_continuous_h3(
    *,
    arrays: dict[str, np.ndarray],
    valid_mask: np.ndarray,
    raster_transform: Any,
    raster_crs: Any,
    h3_cells_bigint: list[int],
    farm_polygon_geojson: dict[str, Any],
    reducers: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    if not arrays:
        raise GenericZonalError("No arrays supplied")
    first = next(iter(arrays.values()))
    shape_ = first.shape
    if any(array.shape != shape_ for array in arrays.values()):
        raise GenericZonalError("All arrays must share one aligned raster grid")
    if valid_mask.shape != shape_:
        raise GenericZonalError("valid_mask shape does not match raster arrays")

    crs = CRS.from_user_input(raster_crs)
    if not crs.is_projected:
        raise GenericZonalError(
            f"Projected CRS is required for square-metre weights, received {crs}"
        )
    to_raster = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform
    farm = shape(farm_polygon_geojson)
    if farm.is_empty or not farm.is_valid:
        raise GenericZonalError("Farm polygon is invalid")

    reducers = reducers or {name: ["mean"] for name in arrays}
    output: list[dict[str, Any]] = []

    for h3_index in sorted({int(v) for v in h3_cells_bigint if v is not None}):
        clipped = _h3_polygon_wgs84(h3_index).intersection(farm)
        if clipped.is_empty:
            output.append(
                {
                    "h3_index": h3_index,
                    "observed_area_m2": 0.0,
                    "valid_area_m2": 0.0,
                    "invalid_area_m2": 0.0,
                    "valid_fraction": 0.0,
                }
            )
            continue
        projected = transform_geometry(to_raster, clipped)
        weights, slices = _pixel_overlap_weights(projected, raster_transform, shape_)
        if weights.size == 0 or float(weights.sum()) <= 0:
            output.append(
                {
                    "h3_index": h3_index,
                    "observed_area_m2": 0.0,
                    "valid_area_m2": 0.0,
                    "invalid_area_m2": 0.0,
                    "valid_fraction": 0.0,
                }
            )
            continue

        touched = weights > 0
        local_valid = valid_mask[slices] & touched
        observed_area = float(np.sum(weights[touched]))
        valid_area = float(np.sum(weights[local_valid]))
        row: dict[str, Any] = {
            "h3_index": h3_index,
            "observed_area_m2": round(observed_area, 4),
            "valid_area_m2": round(valid_area, 4),
            "invalid_area_m2": round(max(0.0, observed_area - valid_area), 4),
            "valid_fraction": round(valid_area / observed_area, 6) if observed_area > 0 else 0.0,
        }

        for name, array in arrays.items():
            local = array[slices]
            requested = reducers.get(name, ["mean"])
            for reducer in requested:
                value = _stat(local, local_valid, weights, reducer)
                if len(requested) == 1 and reducer == "mean":
                    field = name
                else:
                    field = f"{reducer}_{name}"
                row[field] = round(value, 6) if value is not None and math.isfinite(value) else None
        output.append(row)
    return output


def aggregate_categorical_h3(
    *,
    class_array: np.ndarray,
    valid_mask: np.ndarray,
    raster_transform: Any,
    raster_crs: Any,
    h3_cells_bigint: list[int],
    farm_polygon_geojson: dict[str, Any],
    class_codes: dict[int, str],
) -> list[dict[str, Any]]:
    crs = CRS.from_user_input(raster_crs)
    if not crs.is_projected:
        raise GenericZonalError("Categorical zonal statistics require projected CRS")
    to_raster = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform
    farm = shape(farm_polygon_geojson)
    output: list[dict[str, Any]] = []

    for h3_index in sorted({int(v) for v in h3_cells_bigint if v is not None}):
        clipped = _h3_polygon_wgs84(h3_index).intersection(farm)
        if clipped.is_empty:
            output.append({"h3_index": h3_index, "valid_fraction": 0.0})
            continue
        projected = transform_geometry(to_raster, clipped)
        weights, slices = _pixel_overlap_weights(projected, raster_transform, class_array.shape)
        if weights.size == 0 or weights.sum() <= 0:
            output.append({"h3_index": h3_index, "valid_fraction": 0.0})
            continue
        touched = weights > 0
        local_valid = valid_mask[slices] & touched
        observed_area = float(np.sum(weights[touched]))
        valid_area = float(np.sum(weights[local_valid]))
        values = class_array[slices]
        row: dict[str, Any] = {
            "h3_index": h3_index,
            "observed_area_m2": round(observed_area, 4),
            "valid_area_m2": round(valid_area, 4),
            "valid_fraction": round(valid_area / observed_area, 6) if observed_area > 0 else 0.0,
        }
        best_code = None
        best_fraction = -1.0
        for code, field_name in class_codes.items():
            selected = local_valid & (values == code)
            class_area = float(np.sum(weights[selected]))
            fraction = class_area / valid_area if valid_area > 0 else 0.0
            row[field_name] = round(fraction, 6)
            if fraction > best_fraction:
                best_fraction = fraction
                best_code = code
        row["dominant_class"] = best_code
        row["dominant_fraction"] = round(max(best_fraction, 0.0), 6)
        output.append(row)
    return output
