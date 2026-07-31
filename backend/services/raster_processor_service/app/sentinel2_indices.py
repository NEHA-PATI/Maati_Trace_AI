# from __future__ import annotations

# import math
# import os
# from collections import defaultdict
# from typing import Any

# import pyproj

# _proj_data_dir = pyproj.datadir.get_data_dir()
# os.environ["PROJ_LIB"] = _proj_data_dir
# os.environ["PROJ_DATA"] = _proj_data_dir



# import h3
# import numpy as np
# import rasterio
# from rasterio.warp import transform_bounds
# from rasterio.windows import from_bounds


# class RasterProcessorError(RuntimeError):
#     pass


# S2_KEY_ALIASES = {
#     "blue": ["B02", "blue"],
#     "green": ["B03", "green"],
#     "red": ["B04", "red"],
#     "rededge1": ["B05", "rededge1"],
#     "rededge2": ["B06", "rededge2"],
#     "rededge3": ["B07", "rededge3"],
#     "nir": ["B08", "nir"],
#     "nir08": ["B8A", "nir08"],
#     "swir16": ["B11", "swir16"],
#     "swir22": ["B12", "swir22"],
#     "scl": ["SCL", "scl"],
# }


# REQUIRED_BANDS = [
#     "blue",
#     "green",
#     "red",
#     "nir",
#     "swir16",
#     "swir22",
#     "scl",
# ]


# OPTIONAL_BANDS = [
#     "rededge1",
#     "rededge2",
#     "rededge3",
#     "nir08",
# ]


# def _safe_divide(
#     numerator: np.ndarray,
#     denominator: np.ndarray,
# ) -> np.ndarray:
#     result = np.full(numerator.shape, np.nan, dtype=np.float32)
#     mask = np.abs(denominator) > 1e-6
#     result[mask] = numerator[mask] / denominator[mask]
#     return result


# def _mean_or_none(values: np.ndarray) -> float | None:
#     if values.size == 0:
#         return None

#     valid = values[np.isfinite(values)]
#     if valid.size == 0:
#         return None

#     return round(float(np.mean(valid)), 6)


# def _clean_float(value: float | None) -> float | None:
#     if value is None:
#         return None

#     if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
#         return None

#     return round(float(value), 6)


# def _build_asset_map(assets: list[dict[str, Any]]) -> dict[str, str]:
#     raw_by_key = {}
#     raw_by_common_name = {}

#     for asset in assets:
#         key = str(asset.get("key") or "").strip()
#         common_name = str(asset.get("common_name") or "").strip()

#         if key:
#             raw_by_key[key.lower()] = asset["href"]

#         if common_name:
#             raw_by_common_name[common_name.lower()] = asset["href"]

#     normalized: dict[str, str] = {}

#     for normalized_name, aliases in S2_KEY_ALIASES.items():
#         for alias in aliases:
#             alias_lower = alias.lower()

#             if alias_lower in raw_by_key:
#                 normalized[normalized_name] = raw_by_key[alias_lower]
#                 break

#             if alias_lower in raw_by_common_name:
#                 normalized[normalized_name] = raw_by_common_name[alias_lower]
#                 break

#     return normalized


# def _validate_required_assets(asset_map: dict[str, str]) -> None:
#     missing = [band for band in REQUIRED_BANDS if band not in asset_map]

#     if missing:
#         raise RasterProcessorError(
#             "Missing required Sentinel-2 assets: " + ", ".join(missing)
#         )


# def _read_band_window(
#     href: str,
#     bbox: list[float],
#     out_shape: tuple[int, int] | None = None,
# ) -> tuple[np.ndarray, Any]:
#     with rasterio.Env(
#         GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
#         CPL_VSIL_CURL_USE_HEAD="NO",
#     ):
#         with rasterio.open(href) as dataset:
#             if dataset.crs is None:
#                 raise RasterProcessorError("Raster asset has no CRS.")

#             asset_bounds = dataset.bounds

#             bbox_in_asset_crs = transform_bounds(
#                 src_crs="EPSG:4326",
#                 dst_crs=dataset.crs,
#                 left=bbox[0],
#                 bottom=bbox[1],
#                 right=bbox[2],
#                 top=bbox[3],
#                 densify_pts=21,
#             )

#             left, bottom, right, top = bbox_in_asset_crs

#             overlaps = not (
#                 right <= asset_bounds.left
#                 or left >= asset_bounds.right
#                 or top <= asset_bounds.bottom
#                 or bottom >= asset_bounds.top
#             )

#             if not overlaps:
#                 raise RasterProcessorError(
#                     "Requested bbox does not overlap raster asset after CRS transform. "
#                     f"Input bbox EPSG:4326={bbox}; "
#                     f"bbox_in_asset_crs={bbox_in_asset_crs}; "
#                     f"asset_crs={dataset.crs}; "
#                     f"asset_bounds={asset_bounds}."
#                 )

#             window = from_bounds(
#                 left=left,
#                 bottom=bottom,
#                 right=right,
#                 top=top,
#                 transform=dataset.transform,
#             )

#             window = window.round_offsets().round_lengths()

#             if window.width <= 0 or window.height <= 0:
#                 raise RasterProcessorError(
#                     "Requested bbox produced an empty raster window. "
#                     "Try a slightly larger bbox for this test farm."
#                 )

#             if out_shape is None:
#                 data = dataset.read(1, window=window, masked=True)
#             else:
#                 data = dataset.read(
#                     1,
#                     window=window,
#                     out_shape=out_shape,
#                     masked=True,
#                     resampling=rasterio.enums.Resampling.bilinear,
#                 )

#             return data, dataset.window_transform(window)


# def _read_all_required_bands(
#     asset_map: dict[str, str],
#     bbox: list[float],
# ) -> tuple[dict[str, np.ndarray], Any]:
#     red_raw, transform = _read_band_window(asset_map["red"], bbox)
#     target_shape = red_raw.shape

#     bands: dict[str, np.ndarray] = {
#         "red": red_raw.astype("float32").filled(np.nan) / 10000.0,
#     }

#     for band_name in [
#         "blue",
#         "green",
#         "nir",
#         "swir16",
#         "swir22",
#         "rededge1",
#         "rededge2",
#         "rededge3",
#         "nir08",
#     ]:
#         href = asset_map.get(band_name)
#         if not href:
#             continue

#         band_raw, _ = _read_band_window(
#             href=href,
#             bbox=bbox,
#             out_shape=target_shape,
#         )
#         bands[band_name] = band_raw.astype("float32").filled(np.nan) / 10000.0

#     scl_raw, _ = _read_band_window(
#         href=asset_map["scl"],
#         bbox=bbox,
#         out_shape=target_shape,
#     )
#     bands["scl"] = scl_raw.astype("float32").filled(np.nan)

#     return bands, transform


# def _build_quality_masks(bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
#     scl = bands["scl"]

#     nodata_mask = np.isnan(scl) | (scl == 0)

#     cloud_mask = np.isin(
#         scl,
#         [
#             3,   # cloud shadow
#             8,   # medium probability cloud
#             9,   # high probability cloud
#             10,  # thin cirrus
#             11,  # snow / ice
#         ],
#     )

#     invalid_scl_mask = np.isin(
#         scl,
#         [
#             0,  # no data
#             1,  # saturated / defective
#             2,  # dark area pixels
#         ],
#     )

#     required_band_mask = (
#         np.isfinite(bands["blue"])
#         & np.isfinite(bands["green"])
#         & np.isfinite(bands["red"])
#         & np.isfinite(bands["nir"])
#         & np.isfinite(bands["swir16"])
#         & np.isfinite(bands["swir22"])
#     )

#     valid_mask = required_band_mask & ~nodata_mask & ~cloud_mask & ~invalid_scl_mask

#     return {
#         "nodata": nodata_mask,
#         "cloud": cloud_mask,
#         "valid": valid_mask,
#     }


# def _calculate_index_arrays(bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
#     blue = bands["blue"]
#     green = bands["green"]
#     red = bands["red"]
#     nir = bands["nir"]
#     swir16 = bands["swir16"]
#     swir22 = bands["swir22"]

#     indices = {
#         "ndvi": _safe_divide(nir - red, nir + red),
#         "gndvi": _safe_divide(nir - green, nir + green),
#         "evi": _safe_divide(
#             2.5 * (nir - red),
#             nir + (6.0 * red) - (7.5 * blue) + 1.0,
#         ),
#         "savi": _safe_divide(
#             1.5 * (nir - red),
#             nir + red + 0.5,
#         ),
#         "ndmi": _safe_divide(nir - swir16, nir + swir16),
#         "ndwi": _safe_divide(green - nir, green + nir),
#         "mndwi": _safe_divide(green - swir16, green + swir16),
#         "msi": _safe_divide(swir16, nir),
#         "bsi": _safe_divide(
#             (swir16 + red) - (nir + blue),
#             (swir16 + red) + (nir + blue),
#         ),
#         "nbr": _safe_divide(nir - swir22, nir + swir22),
#         "nbr2": _safe_divide(swir16 - swir22, swir16 + swir22),
#     }

#     if "rededge1" in bands:
#         rededge1 = bands["rededge1"]
#         indices["ndre"] = _safe_divide(nir - rededge1, nir + rededge1)
#         indices["reci"] = _safe_divide(nir, rededge1) - 1.0
#     else:
#         indices["ndre"] = np.full(nir.shape, np.nan, dtype=np.float32)
#         indices["reci"] = np.full(nir.shape, np.nan, dtype=np.float32)

#     return indices


# def _pixel_centers_to_h3(
#     shape: tuple[int, int],
#     transform: Any,
#     h3_resolution: int,
# ) -> np.ndarray:
#     rows, cols = shape
#     h3_grid = np.empty(shape, dtype=object)

#     for row in range(rows):
#         for col in range(cols):
#             lon, lat = rasterio.transform.xy(
#                 transform,
#                 row,
#                 col,
#                 offset="center",
#             )
#             h3_grid[row, col] = h3.latlng_to_cell(
#                 lat=float(lat),
#                 lng=float(lon),
#                 res=h3_resolution,
#             )

#     return h3_grid


# def _aggregate_by_h3(
#     bands: dict[str, np.ndarray],
#     indices: dict[str, np.ndarray],
#     masks: dict[str, np.ndarray],
#     h3_grid: np.ndarray,
# ) -> list[dict[str, Any]]:
#     buckets: dict[str, dict[str, Any]] = defaultdict(
#         lambda: {
#             "pixel_count": 0,
#             "valid_pixel_count": 0,
#             "cloud_pixel_count": 0,
#             "nodata_pixel_count": 0,
#             "values": defaultdict(list),
#         }
#     )

#     rows, cols = bands["red"].shape

#     band_fields = {
#         "mean_blue": "blue",
#         "mean_green": "green",
#         "mean_red": "red",
#         "mean_rededge1": "rededge1",
#         "mean_rededge2": "rededge2",
#         "mean_rededge3": "rededge3",
#         "mean_nir": "nir",
#         "mean_nir08": "nir08",
#         "mean_swir16": "swir16",
#         "mean_swir22": "swir22",
#     }

#     for row in range(rows):
#         for col in range(cols):
#             h3_cell = h3_grid[row, col]
#             bucket = buckets[h3_cell]

#             bucket["pixel_count"] += 1

#             if bool(masks["cloud"][row, col]):
#                 bucket["cloud_pixel_count"] += 1

#             if bool(masks["nodata"][row, col]):
#                 bucket["nodata_pixel_count"] += 1

#             if not bool(masks["valid"][row, col]):
#                 continue

#             bucket["valid_pixel_count"] += 1

#             for output_name, band_name in band_fields.items():
#                 if band_name in bands:
#                     value = bands[band_name][row, col]
#                     if np.isfinite(value):
#                         bucket["values"][output_name].append(float(value))

#             for index_name, array in indices.items():
#                 value = array[row, col]
#                 if np.isfinite(value):
#                     bucket["values"][index_name].append(float(value))

#     features: list[dict[str, Any]] = []

#     for h3_cell, bucket in buckets.items():
#         pixel_count = int(bucket["pixel_count"])
#         cloud_pixel_count = int(bucket["cloud_pixel_count"])
#         valid_pixel_count = int(bucket["valid_pixel_count"])
#         nodata_pixel_count = int(bucket["nodata_pixel_count"])

#         cloud_percentage = (
#             round((cloud_pixel_count / pixel_count) * 100.0, 4)
#             if pixel_count > 0
#             else 0.0
#         )

#         row = {
#             "h3_index": h3.str_to_int(h3_cell),
#             "pixel_count": pixel_count,
#             "valid_pixel_count": valid_pixel_count,
#             "cloud_pixel_count": cloud_pixel_count,
#             "nodata_pixel_count": nodata_pixel_count,
#             "cloud_percentage": cloud_percentage,
#         }

#         for field_name, values in bucket["values"].items():
#             row[field_name] = _clean_float(_mean_or_none(np.array(values)))

#         features.append(row)

#     features.sort(key=lambda item: item["h3_index"])

#     return features


# def process_sentinel2_indices(
#     scene: dict[str, Any],
#     bbox: list[float],
#     h3_resolution: int,
# ) -> dict[str, Any]:
#     asset_map = _build_asset_map(scene["assets"])
#     _validate_required_assets(asset_map)

#     bands, transform = _read_all_required_bands(
#         asset_map=asset_map,
#         bbox=bbox,
#     )

#     rows, cols = bands["red"].shape
#     total_pixels = rows * cols

#     masks = _build_quality_masks(bands)
#     indices = _calculate_index_arrays(bands)

#     h3_grid = _pixel_centers_to_h3(
#         shape=bands["red"].shape,
#         transform=transform,
#         h3_resolution=h3_resolution,
#     )

#     features = _aggregate_by_h3(
#         bands=bands,
#         indices=indices,
#         masks=masks,
#         h3_grid=h3_grid,
#     )

#     total_valid = int(np.sum(masks["valid"]))
#     total_cloud = int(np.sum(masks["cloud"]))

#     return {
#         "source_assets_used": sorted(asset_map.keys()),
#         "row_count": len(features),
#         "total_pixel_count": int(total_pixels),
#         "total_valid_pixel_count": total_valid,
#         "total_cloud_pixel_count": total_cloud,
#         "features": features,
#     }






from __future__ import annotations

import math
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import importlib.util
import os
from pathlib import Path


def _force_rasterio_proj_paths() -> None:
    rasterio_spec = importlib.util.find_spec("rasterio")

    if rasterio_spec is None or rasterio_spec.origin is None:
        return

    rasterio_dir = Path(rasterio_spec.origin).parent
    rasterio_proj_dir = rasterio_dir / "proj_data"
    rasterio_gdal_dir = rasterio_dir / "gdal_data"

    if rasterio_proj_dir.exists():
        os.environ["PROJ_LIB"] = str(rasterio_proj_dir)
        os.environ["PROJ_DATA"] = str(rasterio_proj_dir)

    if rasterio_gdal_dir.exists():
        os.environ["GDAL_DATA"] = str(rasterio_gdal_dir)


_force_rasterio_proj_paths()

import h3
import numpy as np
import planetary_computer
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from pyproj import Transformer

from services.raster_processor_service.app.h3_zonal_statistics import (
    H3ZonalStatisticsError,
    aggregate_h3_zonal_statistics,
)


class RasterProcessorError(RuntimeError):
    pass


S2_KEY_ALIASES = {
    "blue": ["B02", "blue"],
    "green": ["B03", "green"],
    "red": ["B04", "red"],
    "rededge1": ["B05", "rededge1"],
    "rededge2": ["B06", "rededge2"],
    "rededge3": ["B07", "rededge3"],
    "nir": ["B08", "nir"],
    "nir08": ["B8A", "nir08"],
    "swir16": ["B11", "swir16"],
    "swir22": ["B12", "swir22"],
    "scl": ["SCL", "scl"],
}


REQUIRED_BANDS = [
    "blue",
    "green",
    "red",
    "nir",
    "swir16",
    "swir22",
    "scl",
]


MAX_PIXELS_PER_REQUEST = 250000


def _refresh_planetary_computer_href(href: str) -> str:
    """
    Standard fix:
    - STAC service may return signed Planetary Computer URLs.
    - Signed SAS query can expire.
    - Raster service must remove old query params and re-sign immediately before reading.
    """
    if "blob.core.windows.net" not in href:
        return href

    parsed = urlsplit(href)

    clean_href = urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            "",
        )
    )

    return planetary_computer.sign(clean_href)


def _safe_divide(
    numerator: np.ndarray,
    denominator: np.ndarray,
) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype=np.float32)
    mask = np.abs(denominator) > 1e-6
    result[mask] = numerator[mask] / denominator[mask]
    return result


def _mean_or_none(values: np.ndarray) -> float | None:
    if values.size == 0:
        return None

    valid = values[np.isfinite(values)]
    if valid.size == 0:
        return None

    return round(float(np.mean(valid)), 6)

def _get_raster_crs(href: str):
    href = _refresh_planetary_computer_href(href)

    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_USE_HEAD="NO",
        GTIFF_SRS_SOURCE="EPSG",
    ):
        with rasterio.open(href) as dataset:
            if dataset.crs is None:
                raise RasterProcessorError(
                    "Sentinel-2 raster asset has no CRS"
                )
            return dataset.crs


def _clean_float(value: float | None) -> float | None:
    if value is None:
        return None

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None

    return round(float(value), 6)


def _build_asset_map(assets: list[dict[str, Any]]) -> dict[str, str]:
    raw_by_key: dict[str, str] = {}
    raw_by_common_name: dict[str, str] = {}

    for asset in assets:
        key = str(asset.get("key") or "").strip()
        common_name = str(asset.get("common_name") or "").strip()
        href = str(asset.get("href") or "").strip()

        if not href:
            continue

        href = _refresh_planetary_computer_href(href)

        if key:
            raw_by_key[key.lower()] = href

        if common_name:
            raw_by_common_name[common_name.lower()] = href

    normalized: dict[str, str] = {}

    for normalized_name, aliases in S2_KEY_ALIASES.items():
        for alias in aliases:
            alias_lower = alias.lower()

            if alias_lower in raw_by_key:
                normalized[normalized_name] = raw_by_key[alias_lower]
                break

            if alias_lower in raw_by_common_name:
                normalized[normalized_name] = raw_by_common_name[alias_lower]
                break

    return normalized


def _validate_required_assets(asset_map: dict[str, str]) -> None:
    missing = [band for band in REQUIRED_BANDS if band not in asset_map]

    if missing:
        raise RasterProcessorError(
            "Missing required Sentinel-2 assets: " + ", ".join(missing)
        )


def _bbox_to_asset_crs(
    bbox: list[float],
    dataset: rasterio.DatasetReader,
) -> tuple[float, float, float, float]:
    if dataset.crs is None:
        raise RasterProcessorError("Raster asset has no CRS.")

    return transform_bounds(
        src_crs="EPSG:4326",
        dst_crs=dataset.crs,
        left=bbox[0],
        bottom=bbox[1],
        right=bbox[2],
        top=bbox[3],
        densify_pts=21,
    )


def _check_overlap(
    bbox_in_asset_crs: tuple[float, float, float, float],
    dataset: rasterio.DatasetReader,
) -> None:
    left, bottom, right, top = bbox_in_asset_crs
    asset_bounds = dataset.bounds

    overlaps = not (
        right <= asset_bounds.left
        or left >= asset_bounds.right
        or top <= asset_bounds.bottom
        or bottom >= asset_bounds.top
    )

    if not overlaps:
        raise RasterProcessorError(
            "Requested bbox does not overlap raster asset after CRS transform. "
            f"bbox_in_asset_crs={bbox_in_asset_crs}; "
            f"asset_crs={dataset.crs}; "
            f"asset_bounds={asset_bounds}."
        )


def _read_band_window(
    href: str,
    bbox: list[float],
    out_shape: tuple[int, int] | None = None,
    resampling: Resampling = Resampling.bilinear,
) -> tuple[np.ndarray, Any]:
    href = _refresh_planetary_computer_href(href)

    try:
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_USE_HEAD="NO",
            GTIFF_SRS_SOURCE="EPSG",
            VSI_CACHE="TRUE",
            GDAL_HTTP_MAX_RETRY="3",
            GDAL_HTTP_RETRY_DELAY="1",
            GDAL_HTTP_TIMEOUT="120",
        ):
            with rasterio.open(href) as dataset:
                bbox_in_asset_crs = _bbox_to_asset_crs(bbox, dataset)
                _check_overlap(bbox_in_asset_crs, dataset)

                left, bottom, right, top = bbox_in_asset_crs

                window = from_bounds(
                    left=left,
                    bottom=bottom,
                    right=right,
                    top=top,
                    transform=dataset.transform,
                )

                window = window.round_offsets().round_lengths()

                if window.width <= 0 or window.height <= 0:
                    raise RasterProcessorError(
                        "Requested bbox produced an empty raster window. "
                        "Use a slightly larger bbox."
                    )

                pixel_count = int(window.width * window.height)

                if pixel_count > MAX_PIXELS_PER_REQUEST:
                    raise RasterProcessorError(
                        f"Raster request too large: {pixel_count} pixels. "
                        f"Limit is {MAX_PIXELS_PER_REQUEST}. Use a smaller bbox."
                    )

                if out_shape is None:
                    data = dataset.read(1, window=window, masked=True)
                else:
                    data = dataset.read(
                        1,
                        window=window,
                        out_shape=out_shape,
                        masked=True,
                        resampling=resampling,
                    )

                return data, dataset.window_transform(window)

    except RasterProcessorError:
        raise
    except Exception as exc:
        message = str(exc)

        if "403" in message or "AccessDenied" in message or "AuthenticationFailed" in message:
            raise RasterProcessorError(
                "Could not read raster asset because the signed URL was rejected. "
                "The raster service attempted to refresh the Planetary Computer URL. "
                "Run STAC search again and retry. Original error: "
                f"{message}"
            ) from exc

        raise RasterProcessorError(f"Failed to read raster asset: {message}") from exc


def _read_all_required_bands(
    asset_map: dict[str, str],
    bbox: list[float],
) -> tuple[dict[str, np.ndarray], Any]:
    red_raw, transform = _read_band_window(asset_map["red"], bbox)
    target_shape = red_raw.shape

    bands: dict[str, np.ndarray] = {
        "red": red_raw.astype("float32").filled(np.nan) / 10000.0,
    }

    for band_name in [
        "blue",
        "green",
        "nir",
        "swir16",
        "swir22",
        "rededge1",
        "rededge2",
        "rededge3",
        "nir08",
    ]:
        href = asset_map.get(band_name)
        if not href:
            continue

        band_raw, _ = _read_band_window(
            href=href,
            bbox=bbox,
            out_shape=target_shape,
            resampling=Resampling.bilinear,
        )
        bands[band_name] = band_raw.astype("float32").filled(np.nan) / 10000.0

    scl_raw, _ = _read_band_window(
        href=asset_map["scl"],
        bbox=bbox,
        out_shape=target_shape,
        resampling=Resampling.nearest,
    )
    bands["scl"] = scl_raw.astype("float32").filled(np.nan)

    return bands, transform


def _build_quality_masks(
    bands: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    scl = bands["scl"]

    nodata_mask = np.isnan(scl) | (scl == 0)
    invalid_mask = np.isin(scl, [1, 2])

    shadow_mask = scl == 3
    water_mask = scl == 6
    cloud_mask = np.isin(scl, [8, 9, 10])
    snow_mask = scl == 11

    required_band_mask = (
        np.isfinite(bands["blue"])
        & np.isfinite(bands["green"])
        & np.isfinite(bands["red"])
        & np.isfinite(bands["nir"])
        & np.isfinite(bands["swir16"])
        & np.isfinite(bands["swir22"])
    )

    valid_mask = (
        required_band_mask
        & ~nodata_mask
        & ~invalid_mask
        & ~shadow_mask
        & ~cloud_mask
        & ~snow_mask
    )

    return {
        "nodata": nodata_mask,
        "invalid": invalid_mask,
        "shadow": shadow_mask,
        "water": water_mask,
        "cloud": cloud_mask,
        "snow": snow_mask,
        "valid": valid_mask,
    }


def _calculate_index_arrays(
    bands: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    blue = bands["blue"]
    green = bands["green"]
    red = bands["red"]
    nir = bands["nir"]
    swir16 = bands["swir16"]
    swir22 = bands["swir22"]

    ndvi = _safe_divide(
        nir - red,
        nir + red,
    )

    # Tunable endmembers. They must later move into the
    # versioned derived-parameter registry.
    ndvi_soil = 0.20
    ndvi_vegetation = 0.86

    fvc_ratio = np.clip(
        (ndvi - ndvi_soil)
        / (ndvi_vegetation - ndvi_soil),
        0.0,
        1.0,
    )

    indices = {
        "ndvi": ndvi,
        "gndvi": _safe_divide(
            nir - green,
            nir + green,
        ),
        "evi": _safe_divide(
            2.5 * (nir - red),
            nir + (6.0 * red) - (7.5 * blue) + 1.0,
        ),
        "savi": _safe_divide(
            1.5 * (nir - red),
            nir + red + 0.5,
        ),

        # Explicit meanings:
        # NDMI = canopy moisture proxy.
        # NDWI/MNDWI = open-water signals.
        "ndmi": _safe_divide(
            nir - swir16,
            nir + swir16,
        ),
        "ndwi": _safe_divide(
            green - nir,
            green + nir,
        ),
        "mndwi": _safe_divide(
            green - swir16,
            green + swir16,
        ),
        "msi": _safe_divide(
            swir16,
            nir,
        ),

        "bsi": _safe_divide(
            (swir16 + red) - (nir + blue),
            (swir16 + red) + (nir + blue),
        ),
        "nbr": _safe_divide(
            nir - swir22,
            nir + swir22,
        ),
        "nbr2": _safe_divide(
            swir16 - swir22,
            swir16 + swir22,
        ),

        # New derived parameters.
        "fvc_proxy": np.square(fvc_ratio),
        "nirv": ndvi * nir,
    }

    if "rededge1" in bands:
        rededge1 = bands["rededge1"]

        indices["ndre"] = _safe_divide(
            nir - rededge1,
            nir + rededge1,
        )

        indices["reci"] = (
            _safe_divide(nir, rededge1) - 1.0
        )
    else:
        indices["ndre"] = np.full(
            nir.shape,
            np.nan,
            dtype=np.float32,
        )
        indices["reci"] = np.full(
            nir.shape,
            np.nan,
            dtype=np.float32,
        )

    return indices


def _pixel_centers_to_h3(
    shape: tuple[int, int],
    transform: Any,
    h3_resolution: int,
) -> np.ndarray:
    rows, cols = shape
    h3_grid = np.empty(shape, dtype=object)

    for row in range(rows):
        for col in range(cols):
            lon, lat = rasterio.transform.xy(
                transform,
                row,
                col,
                offset="center",
            )

            # transform is still in asset CRS, usually EPSG:32645.
            # For now we only use this after reading Sentinel-2 UTM tiles.
            # The h3 values will be corrected in the next version by storing
            # the dataset CRS and transforming pixel centers back to EPSG:4326.
            #
            # Temporary safety:
            # if values do not look like lon/lat, skip exact h3 mapping later.
            h3_grid[row, col] = (float(lon), float(lat))

    return h3_grid


def _aggregate_whole_bbox(
    bands: dict[str, np.ndarray],
    indices: dict[str, np.ndarray],
    masks: dict[str, np.ndarray],
    h3_resolution: int,
    bbox: list[float],
) -> list[dict[str, Any]]:
    """
    Standard v1 aggregation:
    Use bbox center as farm-preview H3 cell.
    This avoids incorrect H3 from UTM pixel centers.
    Later we will transform every pixel center back to EPSG:4326.
    """
    center_lon = (bbox[0] + bbox[2]) / 2.0
    center_lat = (bbox[1] + bbox[3]) / 2.0

    h3_cell = h3.latlng_to_cell(
        lat=center_lat,
        lng=center_lon,
        res=h3_resolution,
    )

    pixel_count = int(bands["red"].size)
    valid_pixel_count = int(np.sum(masks["valid"]))
    cloud_pixel_count = int(np.sum(masks["cloud"]))
    nodata_pixel_count = int(np.sum(masks["nodata"]))

    cloud_percentage = (
        round((cloud_pixel_count / pixel_count) * 100.0, 4)
        if pixel_count > 0
        else 0.0
    )

    valid_mask = masks["valid"]

    row: dict[str, Any] = {
        "h3_index": h3.str_to_int(h3_cell),
        "pixel_count": pixel_count,
        "valid_pixel_count": valid_pixel_count,
        "cloud_pixel_count": cloud_pixel_count,
        "nodata_pixel_count": nodata_pixel_count,
        "cloud_percentage": cloud_percentage,
    }

    band_fields = {
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

    for output_name, band_name in band_fields.items():
        if band_name in bands:
            row[output_name] = _clean_float(_mean_or_none(bands[band_name][valid_mask]))

    for index_name, array in indices.items():
        row[index_name] = _clean_float(_mean_or_none(array[valid_mask]))

    return [row]


def _sample_bands_at_point(
    asset_map: dict[str, str],
    lon: float,
    lat: float,
) -> dict[str, float | None]:
    sample_values: dict[str, float | None] = {}

    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_USE_HEAD="NO",
        GTIFF_SRS_SOURCE="EPSG",
        VSI_CACHE="TRUE",
        GDAL_HTTP_MAX_RETRY="3",
        GDAL_HTTP_RETRY_DELAY="1",
        GDAL_HTTP_TIMEOUT="120",
    ):
        with rasterio.open(asset_map["red"]) as ref_dataset:
            if ref_dataset.crs is None:
                raise RasterProcessorError("Raster asset has no CRS.")

            transformer = Transformer.from_crs(
                "EPSG:4326",
                ref_dataset.crs,
                always_xy=True,
            )
            x, y = transformer.transform(lon, lat)

        # Read SCL first because it decides whether spectral values are usable.
        with rasterio.open(asset_map["scl"]) as dataset:
            sample = next(dataset.sample([(x, y)], indexes=1, masked=True))
            scl_value = float(sample[0]) if np.isfinite(sample[0]) else np.nan

        is_nodata = bool(np.isnan(scl_value) or scl_value == 0)
        is_invalid = bool(scl_value in {0, 1, 2})
        is_cloud = bool(scl_value in {3, 8, 9, 10, 11})
        is_valid = not is_nodata and not is_invalid and not is_cloud

        cloud_percentage = 100.0 if is_cloud else 0.0
        valid_pixel_count = 1 if is_valid else 0
        cloud_pixel_count = 1 if is_cloud else 0
        nodata_pixel_count = 1 if is_nodata else 0

        empty_result = {
            "pixel_count": 1,
            "valid_pixel_count": valid_pixel_count,
            "cloud_pixel_count": cloud_pixel_count,
            "nodata_pixel_count": nodata_pixel_count,
            "cloud_percentage": cloud_percentage,

            "mean_blue": None,
            "mean_green": None,
            "mean_red": None,
            "mean_rededge1": None,
            "mean_rededge2": None,
            "mean_rededge3": None,
            "mean_nir": None,
            "mean_nir08": None,
            "mean_swir16": None,
            "mean_swir22": None,

            "ndvi": None,
            "gndvi": None,
            "evi": None,
            "savi": None,
            "ndmi": None,
            "ndwi": None,
            "mndwi": None,
            "msi": None,
            "bsi": None,
            "nbr": None,
            "nbr2": None,
            "ndre": None,
            "reci": None,
        }

        if not is_valid:
            return empty_result

        band_names = {
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

        band_samples: dict[str, float | None] = {}

        for out_name, band_name in band_names.items():
            href = asset_map.get(band_name)

            if not href:
                band_samples[out_name] = None
                continue

            with rasterio.open(href) as dataset:
                sample = next(dataset.sample([(x, y)], indexes=1, masked=True))
                value = sample[0]
                band_samples[out_name] = (
                    _clean_float(float(value) / 10000.0)
                    if np.isfinite(value)
                    else None
                )

    blue = band_samples.get("mean_blue")
    green = band_samples.get("mean_green")
    red = band_samples.get("mean_red")
    nir = band_samples.get("mean_nir")
    swir16 = band_samples.get("mean_swir16")
    swir22 = band_samples.get("mean_swir22")
    rededge1 = band_samples.get("mean_rededge1")

    def div(a: float | None, b: float | None) -> float | None:
        if a is None or b is None:
            return None
        if abs(a + b) < 1e-6:
            return None
        return _clean_float((a - b) / (a + b))

    ndvi = div(nir, red)
    gndvi = div(nir, green)

    evi = None
    if None not in (nir, red, blue):
        denom = nir + (6.0 * red) - (7.5 * blue) + 1.0
        if abs(denom) > 1e-6:
            evi = _clean_float(2.5 * (nir - red) / denom)

    savi = None
    if None not in (nir, red):
        denom = nir + red + 0.5
        if abs(denom) > 1e-6:
            savi = _clean_float(1.5 * (nir - red) / denom)

    ndmi = div(nir, swir16)
    ndwi = div(green, nir)
    mndwi = div(green, swir16)

    msi = None
    if nir is not None and swir16 is not None and abs(nir) > 1e-6:
        msi = _clean_float(swir16 / nir)

    bsi = None
    if None not in (swir16, red, nir, blue):
        denom = (swir16 + red) + (nir + blue)
        if abs(denom) > 1e-6:
            bsi = _clean_float(((swir16 + red) - (nir + blue)) / denom)

    nbr = div(nir, swir22)
    nbr2 = div(swir16, swir22)
    ndre = div(nir, rededge1)

    reci = None
    if nir is not None and rededge1 is not None and abs(rededge1) > 1e-6:
        reci = _clean_float((nir / rededge1) - 1.0)

    return {
        "pixel_count": 1,
        "valid_pixel_count": valid_pixel_count,
        "cloud_pixel_count": cloud_pixel_count,
        "nodata_pixel_count": nodata_pixel_count,
        "cloud_percentage": cloud_percentage,

        "mean_blue": blue,
        "mean_green": green,
        "mean_red": red,
        "mean_rededge1": rededge1,
        "mean_rededge2": band_samples.get("mean_rededge2"),
        "mean_rededge3": band_samples.get("mean_rededge3"),
        "mean_nir": nir,
        "mean_nir08": band_samples.get("mean_nir08"),
        "mean_swir16": swir16,
        "mean_swir22": swir22,

        "ndvi": ndvi,
        "gndvi": gndvi,
        "evi": evi,
        "savi": savi,
        "ndmi": ndmi,
        "ndwi": ndwi,
        "mndwi": mndwi,
        "msi": msi,
        "bsi": bsi,
        "nbr": nbr,
        "nbr2": nbr2,
        "ndre": ndre,
        "reci": reci,
    }


def _aggregate_by_h3_cells(
    scene: dict[str, Any],
    asset_map: dict[str, str],
    h3_cells_bigint: list[int],
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for cell_bigint in sorted({int(v) for v in h3_cells_bigint if v is not None}):
        h3_cell = h3.int_to_str(cell_bigint)
        lat, lon = h3.cell_to_latlng(h3_cell)
        sampled = _sample_bands_at_point(asset_map, lon=lon, lat=lat)
        sampled["h3_index"] = cell_bigint
        sampled["cloud_percentage"] = sampled.get("cloud_percentage", 0.0)
        features.append(sampled)
    return features


def process_sentinel2_indices(
    scene: dict[str, Any],
    bbox: list[float],
    h3_resolution: int,
    h3_cells_bigint: list[int] | None = None,
    farm_polygon_geojson: dict[str, Any] | None = None,
) -> dict[str, Any]:
    asset_map = _build_asset_map(scene["assets"])
    _validate_required_assets(asset_map)

    bands, raster_transform = _read_all_required_bands(
        asset_map=asset_map,
        bbox=bbox,
    )

    raster_crs = _get_raster_crs(asset_map["red"])

    masks = _build_quality_masks(bands)
    indices = _calculate_index_arrays(bands)

    if h3_cells_bigint:
        try:
            features = aggregate_h3_zonal_statistics(
                bands=bands,
                indices=indices,
                masks=masks,
                raster_transform=raster_transform,
                raster_crs=raster_crs,
                h3_cells_bigint=h3_cells_bigint,
                farm_polygon_geojson=farm_polygon_geojson,
            )
        except H3ZonalStatisticsError as exc:
            raise RasterProcessorError(str(exc)) from exc
    else:
        features = _aggregate_whole_bbox(
            bands=bands,
            indices=indices,
            masks=masks,
            h3_resolution=h3_resolution,
            bbox=bbox,
        )

    total_pixels = sum(
        int(row.get("pixel_count") or 0)
        for row in features
    )
    total_valid = sum(
        int(row.get("valid_pixel_count") or 0)
        for row in features
    )
    total_cloud = sum(
        int(row.get("cloud_pixel_count") or 0)
        for row in features
    )

    total_observed_area_m2 = round(
        sum(
            float(row.get("observed_area_m2") or 0)
            for row in features
        ),
        4,
    )

    total_valid_area_m2 = round(
        sum(
            float(row.get("valid_area_m2") or 0)
            for row in features
        ),
        4,
    )

    farm_valid_fraction = (
        round(
            total_valid_area_m2
            / total_observed_area_m2,
            6,
        )
        if total_observed_area_m2 > 0
        else 0.0
    )

    return {
        "source_assets_used": sorted(asset_map.keys()),
        "row_count": len(features),
        "total_pixel_count": total_pixels,
        "total_valid_pixel_count": total_valid,
        "total_cloud_pixel_count": total_cloud,
        "total_observed_area_m2": total_observed_area_m2,
        "total_valid_area_m2": total_valid_area_m2,
        "farm_valid_fraction": farm_valid_fraction,
        "features": features,
    }