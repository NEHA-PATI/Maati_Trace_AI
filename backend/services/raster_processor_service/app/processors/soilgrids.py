from __future__ import annotations

import math
import os
import tempfile
from typing import Any
from urllib.parse import urlencode

import numpy as np
import requests
from pyproj import Transformer

from shared.config.settings import settings
from services.raster_processor_service.app.common.h3_generic import aggregate_continuous_h3
import rasterio


PROCESSING_VERSION = "soilgrids_wcs_zonal_v1"
PROPERTIES = ["phh2o", "soc", "nitrogen", "clay", "sand", "silt", "bdod", "cec", "cfvo"]
DEPTHS = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200)]
QUANTILE = "Q0.5"
NATIVE_RESOLUTION_M = 250.0

# ISRIC's WCS server (MapServer) computes an output raster purely from the
# requested SUBSET bounds unless an explicit output size is given. For a farm
# smaller than one 250 m SoilGrids pixel, that produces a near-zero-area
# request that MapServer cannot rasterize and it fails with:
#   "msImageCreate(): ... Attempt to allocate raw image failed, out of memory."
# The platform must be able to render small farms, so every request explicitly
# asks for a small fixed output grid via the WCS 2.0 Scaling Extension. ISRIC's
# server expects the axis labels to match the SUBSET axis names ("X"/"Y"), not
# the generic OGC axis URIs (confirmed against the live server: the URI form
# returns "InvalidAxisLabel", the X/Y form returns a real GeoTIFF).
MIN_OUTPUT_PIXELS = 4

# SoilGrids WCS uses its Interrupted Goode Homolosine pseudo-EPSG:152160.
# ISRIC's MapServer instance renders correct pixel spacing/geolocation into
# the returned GeoTIFF (confirmed against a live request: the transform's
# bounds match the requested SUBSET exactly) but does NOT embed a readable
# CRS tag for this custom projection - rasterio reports ds.crs as None. We
# already know the exact CRS we asked for, so it is supplied explicitly to
# the aggregator rather than trusted from (missing) file metadata.
SOILGRIDS_CRS_PROJ4 = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"
CONVERSION = {
    "phh2o": (10.0, "pH"),
    "soc": (10.0, "g/kg"),
    "nitrogen": (100.0, "g/kg"),
    "clay": (10.0, "%"),
    "sand": (10.0, "%"),
    "silt": (10.0, "%"),
    "bdod": (100.0, "kg/dm3"),
    "cec": (10.0, "cmol(c)/kg"),
    "cfvo": (10.0, "vol%"),
}


def _coverage_url(property_key: str, depth: tuple[int, int], bbox: list[float]) -> str:
    transformer = Transformer.from_crs("EPSG:4326", SOILGRIDS_CRS_PROJ4, always_xy=True)
    west, south, east, north = bbox
    corners = [
        transformer.transform(west, south), transformer.transform(west, north),
        transformer.transform(east, south), transformer.transform(east, north),
    ]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    top, bottom = depth
    coverage = f"{property_key}_{top}-{bottom}cm_{QUANTILE}"

    # Request enough output pixels to cover the AOI at native resolution, with
    # a floor so a farm far smaller than one 250 m pixel still gets a valid,
    # renderable coverage instead of a degenerate (near-zero-pixel) request.
    width_px = max(MIN_OUTPUT_PIXELS, math.ceil((maxx - minx) / NATIVE_RESOLUTION_M))
    height_px = max(MIN_OUTPUT_PIXELS, math.ceil((maxy - miny) / NATIVE_RESOLUTION_M))

    params = [
        ("map", f"/map/{property_key}.map"),
        ("SERVICE", "WCS"),
        ("VERSION", "2.0.1"),
        ("REQUEST", "GetCoverage"),
        ("COVERAGEID", coverage),
        ("FORMAT", "GEOTIFF_INT16"),
        ("SUBSET", f"X({minx},{maxx})"),
        ("SUBSET", f"Y({miny},{maxy})"),
        ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/152160"),
        ("OUTPUTCRS", "http://www.opengis.net/def/crs/EPSG/0/152160"),
        ("SCALESIZE", f"X({width_px}),Y({height_px})"),
    ]
    return settings.soilgrids_wcs_base_url + "?" + urlencode(params)


def _download(url: str) -> str:
    fd, path = tempfile.mkstemp(prefix="maatitrace_soilgrids_", suffix=".tif")
    os.close(fd)
    try:
        response = requests.get(url, timeout=settings.source_download_timeout_seconds)
        response.raise_for_status()
        with open(path, "wb") as out:
            out.write(response.content)
        return path
    except Exception:
        try: os.remove(path)
        except OSError: pass
        raise


def process(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload["source_item"]
    properties = payload.get("options", {}).get("properties") or PROPERTIES
    requested_depths = payload.get("options", {}).get("depths_cm") or [list(v) for v in DEPTHS]
    depths = [(int(v[0]), int(v[1])) for v in requested_depths]
    records: list[dict[str, Any]] = []
    used: list[str] = []

    for property_key in properties:
        if property_key not in PROPERTIES:
            raise ValueError(f"Unsupported SoilGrids property: {property_key}")
        divisor, unit = CONVERSION[property_key]
        for depth in depths:
            url = _coverage_url(property_key, depth, payload["bbox"])
            path = _download(url)
            try:
                with rasterio.open(path) as ds:
                    raw = ds.read(1, masked=True).astype("float64").filled(np.nan)
                    valid = np.isfinite(raw)
                    values = raw / divisor
                    rows = aggregate_continuous_h3(
                        arrays={"value": values},
                        valid_mask=valid,
                        raster_transform=ds.transform,
                        raster_crs=SOILGRIDS_CRS_PROJ4,
                        h3_cells_bigint=payload["h3_cells_bigint"],
                        farm_polygon_geojson=payload["farm_polygon_geojson"],
                    )
                    for row in rows:
                        records.append(
                            {
                                "h3_index": row["h3_index"],
                                "h3_resolution": payload["h3_resolution"],
                                "property_key": property_key,
                                "depth_top_cm": depth[0],
                                "depth_bottom_cm": depth[1],
                                "quantile": QUANTILE,
                                "value": row.get("value"),
                                "unit": unit,
                                "valid_fraction": row.get("valid_fraction"),
                                "source_dataset": "soilgrids_v2",
                                "source_version": "latest",
                                "native_resolution_m": 250.0,
                            }
                        )
                used.append(f"{property_key}_{depth[0]}-{depth[1]}cm_{QUANTILE}")
            finally:
                try: os.remove(path)
                except OSError: pass

    return {
        "dataset_key": "soilgrids_v2",
        "provider": item["provider"],
        "source_collection": "SoilGrids WCS",
        "source_item_id": item["item_id"],
        "source_datetime": None,
        "processing_version": PROCESSING_VERSION,
        "spatial_level": "h3",
        "h3_resolution": payload["h3_resolution"],
        "source_assets_used": used,
        "record_count": len(records),
        "records": records,
        "metadata": {"quantile": QUANTILE},
    }
