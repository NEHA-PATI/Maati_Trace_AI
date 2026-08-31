from __future__ import annotations

import math
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import numpy as np
import planetary_computer
import rasterio
from pyproj import CRS, Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

from shared.config.settings import settings


class MultiRasterIOError(RuntimeError):
    pass


@dataclass(frozen=True)
class TargetGrid:
    crs: CRS
    transform: rasterio.Affine
    width: int
    height: int
    resolution_m: float


def refresh_planetary_computer_href(href: str) -> str:
    if "blob.core.windows.net" not in href:
        return href
    parsed = urlsplit(href)
    clean = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return planetary_computer.sign(clean)


def local_utm_crs(bbox: list[float]) -> CRS:
    west, south, east, north = bbox
    lon = (west + east) / 2.0
    lat = (south + north) / 2.0
    zone = int(math.floor((lon + 180.0) / 6.0) + 1)
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)


def build_target_grid(
    bbox: list[float],
    resolution_m: float,
    *,
    max_pixels: int | None = None,
) -> TargetGrid:
    target_crs = local_utm_crs(bbox)
    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    west, south, east, north = bbox
    x1, y1 = transformer.transform(west, south)
    x2, y2 = transformer.transform(east, north)
    minx, maxx = sorted([x1, x2])
    miny, maxy = sorted([y1, y2])

    width = max(1, int(math.ceil((maxx - minx) / resolution_m)))
    height = max(1, int(math.ceil((maxy - miny) / resolution_m)))
    pixel_count = width * height
    limit = max_pixels or settings.raster_max_pixels_per_request
    if pixel_count > limit:
        raise MultiRasterIOError(
            f"Target raster request too large: {pixel_count} pixels; limit={limit}."
        )
    transform = from_origin(minx, maxy, resolution_m, resolution_m)
    return TargetGrid(
        crs=target_crs,
        transform=transform,
        width=width,
        height=height,
        resolution_m=resolution_m,
    )


def _resampling(name: str) -> Resampling:
    mapping = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
        "cubic": Resampling.cubic,
    }
    return mapping.get(name, Resampling.bilinear)


def read_asset_to_grid(
    href: str,
    grid: TargetGrid,
    *,
    resampling: str = "bilinear",
    masked: bool = True,
) -> np.ndarray:
    href = refresh_planetary_computer_href(href)
    try:
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_USE_HEAD="NO",
            GTIFF_SRS_SOURCE="EPSG",
            VSI_CACHE="TRUE",
            GDAL_HTTP_MAX_RETRY="3",
            GDAL_HTTP_RETRY_DELAY="1",
            GDAL_HTTP_TIMEOUT=str(settings.raster_http_timeout_seconds),
        ):
            with rasterio.open(href) as src:
                with WarpedVRT(
                    src,
                    crs=grid.crs,
                    transform=grid.transform,
                    width=grid.width,
                    height=grid.height,
                    resampling=_resampling(resampling),
                ) as vrt:
                    data = vrt.read(1, masked=masked)
    except Exception as exc:
        raise MultiRasterIOError(f"Failed to read raster asset {href}: {exc}") from exc

    if hasattr(data, "filled"):
        return data.astype("float64").filled(np.nan)
    return np.asarray(data, dtype="float64")


def apply_scale_offset(
    values: np.ndarray,
    *,
    scale: float | None,
    offset: float | None,
    nodata: float | int | None = None,
) -> np.ndarray:
    out = values.astype("float64", copy=True)
    if nodata is not None:
        out[np.isclose(out, float(nodata), equal_nan=False)] = np.nan
    if scale is not None:
        out = out * float(scale)
    if offset is not None:
        out = out + float(offset)
    return out


def safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype="float64")
    valid = np.isfinite(numerator) & np.isfinite(denominator) & (np.abs(denominator) > 1e-12)
    result[valid] = numerator[valid] / denominator[valid]
    return result


@dataclass(frozen=True)
class NativeWindowSample:
    values: np.ndarray  # 2D array, native units (no scale/offset applied)
    center_row: int      # row of the farm-nearest pixel, in `values` coordinates
    center_col: int       # col of the farm-nearest pixel, in `values` coordinates


def sample_native_window(
    href: str,
    lon: float,
    lat: float,
    *,
    half_window_pixels: int = 2,
) -> NativeWindowSample | None:
    """
    Read a small square window, in the asset's OWN native grid and resolution,
    centred on the pixel nearest (lon, lat). Unlike read_asset_to_grid(), this
    does not warp/resample onto a synthetic target grid - it returns the raw
    native pixels around the point so a caller can search a real neighbourhood
    for a usable value.

    This exists for coarse-resolution products (500 m MODIS, ...) queried for
    a farm that is smaller than one native pixel: the exact pixel under the
    farm centroid can be masked (cloud/QC) while an adjacent native pixel a
    few hundred metres away is genuinely valid. A single warped destination
    pixel anchored at the farm's own bbox has no way to see that neighbour;
    sampling the native grid directly does.

    Returns None if the point falls outside the raster's extent.
    """
    href = refresh_planetary_computer_href(href)
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_USE_HEAD="NO",
        GTIFF_SRS_SOURCE="EPSG",
        VSI_CACHE="TRUE",
        GDAL_HTTP_MAX_RETRY="3",
        GDAL_HTTP_RETRY_DELAY="1",
        GDAL_HTTP_TIMEOUT=str(settings.raster_http_timeout_seconds),
    ):
        with rasterio.open(href) as src:
            if src.crs is None:
                raise MultiRasterIOError(f"Raster asset has no CRS: {href}")
            transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            x, y = transformer.transform(lon, lat)
            row, col = src.index(x, y)

            if not (0 <= row < src.height and 0 <= col < src.width):
                return None

            size = 2 * half_window_pixels + 1
            row_off = row - half_window_pixels
            col_off = col - half_window_pixels
            window = Window(col_off, row_off, size, size)
            # boundless=True pads out-of-raster edges with nodata rather than
            # shrinking the window, so the centre index stays fixed regardless
            # of how close the farm is to the raster's own edge.
            data = src.read(1, window=window, masked=True, boundless=True)
            values = data.astype("float64").filled(np.nan) if hasattr(data, "filled") else np.asarray(data, dtype="float64")

    return NativeWindowSample(values=values, center_row=half_window_pixels, center_col=half_window_pixels)


def nearest_valid_pixel(
    sample: NativeWindowSample,
    valid_mask: np.ndarray,
) -> tuple[float | None, int | None, int | None]:
    """
    Given a NativeWindowSample and a same-shaped boolean validity mask, return
    the value of the pixel nearest (by Euclidean pixel distance) to the
    window's centre for which valid_mask is True, plus its (row, col) offset
    from the centre. Returns (None, None, None) if nothing in the window is
    valid.
    """
    if valid_mask.shape != sample.values.shape:
        raise MultiRasterIOError("valid_mask shape does not match sampled window shape")

    rows, cols = np.where(valid_mask & np.isfinite(sample.values))
    if rows.size == 0:
        return None, None, None

    distances = (rows - sample.center_row) ** 2 + (cols - sample.center_col) ** 2
    best = int(np.argmin(distances))
    best_row, best_col = int(rows[best]), int(cols[best])
    return (
        float(sample.values[best_row, best_col]),
        best_row - sample.center_row,
        best_col - sample.center_col,
    )
