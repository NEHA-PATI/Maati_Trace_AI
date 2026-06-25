from typing import Any

from pyproj import Geod
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient
from shapely.validation import explain_validity

ACRES_PER_SQUARE_METER = 0.00024710538146717


class FarmGeometryError(ValueError):
    pass


def validate_farm_polygon(geojson: dict[str, Any]) -> BaseGeometry:
    try:
        geom = shape(geojson)
    except Exception as exc:
        raise FarmGeometryError(f"Invalid GeoJSON: {exc}") from exc

    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise FarmGeometryError("Only Polygon and MultiPolygon are supported")

    if geom.is_empty:
        raise FarmGeometryError("Farm geometry is empty")

    if not geom.is_valid:
        raise FarmGeometryError(f"Invalid farm geometry: {explain_validity(geom)}")

    minx, miny, maxx, maxy = geom.bounds

    if minx < -180 or maxx > 180:
        raise FarmGeometryError("Longitude must be between -180 and 180")

    if miny < -90 or maxy > 90:
        raise FarmGeometryError("Latitude must be between -90 and 90")

    return geom


def calculate_area_acres(geojson: dict[str, Any]) -> float:
    geom = validate_farm_polygon(geojson)

    geod = Geod(ellps="WGS84")

    if geom.geom_type == "Polygon":
        oriented = orient(geom, sign=1.0)
        area_sqm, _ = geod.geometry_area_perimeter(oriented)
        return round(abs(area_sqm) * ACRES_PER_SQUARE_METER, 4)

    total_area_sqm = 0.0
    for polygon in geom.geoms:
        oriented = orient(polygon, sign=1.0)
        area_sqm, _ = geod.geometry_area_perimeter(oriented)
        total_area_sqm += abs(area_sqm)

    return round(total_area_sqm * ACRES_PER_SQUARE_METER, 4)