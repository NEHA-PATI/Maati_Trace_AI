from typing import Any

import h3
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from shared.config.settings import settings


class BoundaryIndexError(ValueError):
    pass


def validate_geometry(geojson: dict[str, Any]) -> BaseGeometry:
    try:
        geom = shape(geojson)
    except Exception as exc:
        raise BoundaryIndexError(f"Invalid GeoJSON: {exc}") from exc

    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise BoundaryIndexError("Only Polygon and MultiPolygon are supported")

    if geom.is_empty:
        raise BoundaryIndexError("Geometry is empty")

    if not geom.is_valid:
        raise BoundaryIndexError(f"Invalid geometry: {explain_validity(geom)}")

    vertex_count = count_vertices(geojson)
    if vertex_count > settings.max_polygon_vertices:
        raise BoundaryIndexError(
            f"Polygon has {vertex_count} vertices. Max allowed is {settings.max_polygon_vertices}"
        )

    minx, miny, maxx, maxy = geom.bounds

    if minx < -180 or maxx > 180:
        raise BoundaryIndexError("Longitude must be between -180 and 180")

    if miny < -90 or maxy > 90:
        raise BoundaryIndexError("Latitude must be between -90 and 90")

    return geom


def count_vertices(geojson: dict[str, Any]) -> int:
    geom_type = geojson.get("type")
    coordinates = geojson.get("coordinates", [])

    if geom_type == "Polygon":
        return sum(len(ring) for ring in coordinates)

    if geom_type == "MultiPolygon":
        return sum(len(ring) for polygon in coordinates for ring in polygon)

    return 0


def strip_closing_point(ring: list[list[float]]) -> list[list[float]]:
    if len(ring) > 1 and ring[0] == ring[-1]:
        return ring[:-1]
    return ring


def lnglat_ring_to_latlng(ring: list[list[float]]) -> list[tuple[float, float]]:
    cleaned = strip_closing_point(ring)
    return [(float(lat), float(lng)) for lng, lat in cleaned]


def polygon_coordinates_to_h3_shape(coordinates: list[Any]) -> h3.LatLngPoly:
    outer = lnglat_ring_to_latlng(coordinates[0])
    holes = [lnglat_ring_to_latlng(ring) for ring in coordinates[1:]]
    return h3.LatLngPoly(outer, *holes)


def geojson_to_h3_shape(geojson: dict[str, Any]) -> h3.H3Shape:
    geom_type = geojson["type"]
    coordinates = geojson["coordinates"]

    if geom_type == "Polygon":
        return polygon_coordinates_to_h3_shape(coordinates)

    polygons = [polygon_coordinates_to_h3_shape(poly) for poly in coordinates]
    return h3.LatLngMultiPoly(*polygons)


def h3_string_to_bigint(cell: str) -> int:
    return int(cell, 16)


def polygon_to_h3_bigints(
    geojson: dict[str, Any],
    resolution: int | None,
    include_cells: bool,
    max_cells: int | None = 1000,
) -> dict[str, Any]:
    geom = validate_geometry(geojson)

    final_resolution = resolution or settings.h3_default_resolution

    if final_resolution < settings.h3_min_resolution:
        raise BoundaryIndexError(f"H3 resolution must be >= {settings.h3_min_resolution}")

    if final_resolution > settings.h3_max_resolution:
        raise BoundaryIndexError(f"H3 resolution must be <= {settings.h3_max_resolution}")

    h3_shape = geojson_to_h3_shape(geojson)
    cells = sorted(h3.polygon_to_cells(h3_shape, res=final_resolution))

    if len(cells) > settings.max_farm_h3_cells:
        raise BoundaryIndexError(
            f"Polygon produced {len(cells)} H3 cells. Max allowed is {settings.max_farm_h3_cells}"
        )

    if include_cells:
        returned_cells = cells if max_cells is None else cells[:max_cells]
    else:
        returned_cells = []

    minx, miny, maxx, maxy = geom.bounds

    return {
        "resolution": final_resolution,
        "cell_count": len(cells),
        "returned_cell_count": len(returned_cells),
        "h3_cells_bigint": [h3_string_to_bigint(cell) for cell in returned_cells],
        "bbox": [minx, miny, maxx, maxy],
        "geometry_type": geom.geom_type,
    }
