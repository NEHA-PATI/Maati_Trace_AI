from __future__ import annotations

import os
from typing import Any

from pyproj import Geod
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient
from shapely.validation import explain_validity

ACRES_PER_SQUARE_METER = 0.00024710538146717
MAX_POLYGON_VERTICES = int(os.getenv("MAX_POLYGON_VERTICES", "500"))


class FarmGeometryError(ValueError):
    pass


def _count_vertices(geometry: BaseGeometry) -> int:
    if geometry.geom_type == "Polygon":
        return (
            len(geometry.exterior.coords)
            + sum(len(ring.coords) for ring in geometry.interiors)
        )
    if geometry.geom_type == "MultiPolygon":
        return sum(_count_vertices(polygon) for polygon in geometry.geoms)
    return 0


def validate_farm_polygon(geojson: dict[str, Any]) -> BaseGeometry:
    try:
        geometry = shape(geojson)
    except Exception as exc:
        raise FarmGeometryError(f"Invalid GeoJSON: {exc}") from exc

    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise FarmGeometryError("Only Polygon and MultiPolygon farm boundaries are supported.")
    if geometry.is_empty:
        raise FarmGeometryError("Farm geometry is empty.")
    if not geometry.is_valid:
        raise FarmGeometryError(f"Invalid farm geometry: {explain_validity(geometry)}")

    vertex_count = _count_vertices(geometry)
    if vertex_count > MAX_POLYGON_VERTICES:
        raise FarmGeometryError(
            f"Farm boundary contains too many vertices. Maximum allowed is {MAX_POLYGON_VERTICES}."
        )

    minx, miny, maxx, maxy = geometry.bounds
    if minx < -180 or maxx > 180:
        raise FarmGeometryError("Longitude must be between -180 and 180.")
    if miny < -90 or maxy > 90:
        raise FarmGeometryError("Latitude must be between -90 and 90.")

    return geometry


def calculate_area_acres(geojson: dict[str, Any]) -> float:
    geometry = validate_farm_polygon(geojson)
    geod = Geod(ellps="WGS84")

    if geometry.geom_type == "Polygon":
        oriented = orient(geometry, sign=1.0)
        area_sqm, _ = geod.geometry_area_perimeter(oriented)
        acres = abs(area_sqm) * ACRES_PER_SQUARE_METER
        if acres <= 0:
            raise FarmGeometryError("Farm boundary area must be greater than zero.")
        return round(acres, 4)

    total_area_sqm = 0.0
    for polygon in geometry.geoms:
        oriented = orient(polygon, sign=1.0)
        area_sqm, _ = geod.geometry_area_perimeter(oriented)
        total_area_sqm += abs(area_sqm)

    acres = total_area_sqm * ACRES_PER_SQUARE_METER
    if acres <= 0:
        raise FarmGeometryError("Farm boundary area must be greater than zero.")
    return round(acres, 4)
