from __future__ import annotations

import json
import math
from collections import defaultdict
from typing import Any
from uuid import UUID

from shapely.geometry import Point, Polygon, mapping, shape
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class AnalyticsQueryRepositoryError(RuntimeError):
    pass


GRID_SIZE_METERS = 10
METERS_PER_DEGREE_LAT = 111_320.0


def _fallback_grid_degrees(latitude: float) -> tuple[float, float]:
    lat_step = GRID_SIZE_METERS / METERS_PER_DEGREE_LAT
    lon_step = GRID_SIZE_METERS / max(1.0, METERS_PER_DEGREE_LAT * max(0.2, abs(__import__("math").cos(__import__("math").radians(latitude)))))
    return lon_step, lat_step


def _latest_feature_rows_by_h3(farm_id: UUID | str) -> dict[int, dict[str, Any]]:
    rows = get_latest_features(farm_id)
    return {int(row["h3_index"]): row for row in rows if row.get("h3_index") is not None}


def _weighted_row_from_contributions(
    farm_id: UUID | str,
    cell: dict[str, Any],
    contributions: list[dict[str, Any]],
    features_by_h3: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    if not contributions:
        return {
            "grid_cell_id": cell["grid_cell_id"],
            "farm_id": str(farm_id),
            "snapshot_date": None,
            "ndvi": None,
            "ndmi": None,
            "ndwi": None,
            "bsi": None,
            "evi": None,
            "savi": None,
            "msi": None,
            "nbr": None,
            "ndre": None,
            "surface_temp_c": None,
            "cloud_percentage": None,
            "valid_pixel_percentage": None,
            "vegetation_trend": "unknown",
            "moisture_trend": "unknown",
            "soil_exposure_trend": "unknown",
            "value_source": "farm_weighted_average_fallback",
            "grid_row": cell.get("grid_row"),
            "grid_col": cell.get("grid_col"),
            "cell_polygon_geojson": cell.get("cell_polygon_geojson"),
            "cell_centroid_lon": cell.get("cell_centroid_lon"),
            "cell_centroid_lat": cell.get("cell_centroid_lat"),
            "coverage_ratio": cell.get("coverage_ratio"),
        }

    params = ["ndvi", "ndmi", "ndwi", "bsi", "evi", "savi", "msi", "nbr", "ndre"]
    weighted: dict[str, float | None] = {param: None for param in params}
    weights_by_param = defaultdict(float)
    sums_by_param = defaultdict(float)
    total_overlap = 0.0
    max_overlap = 0.0
    dominant_h3 = None
    dominant_weight = -1.0
    snapshot_date = None
    cloud_weight_sum = 0.0
    valid_weight_sum = 0.0
    cloud_sum = 0.0
    valid_sum = 0.0
    temp_sum = 0.0
    temp_weight_sum = 0.0

    for contrib in contributions:
        h3_index = int(contrib["h3_index"])
        feature = features_by_h3.get(h3_index)
        if not feature:
            continue
        overlap = float(contrib.get("overlap_ratio") or 0)
        valid_weight = float(feature.get("valid_pixel_count") or feature.get("pixel_count") or 1 or 1)
        effective_weight = max(0.000001, overlap * max(1.0, valid_weight))
        total_overlap += overlap
        if overlap > max_overlap:
            max_overlap = overlap
            dominant_h3 = h3_index
        if snapshot_date is None:
            snapshot_date = feature.get("snapshot_date")
        for param in params:
            value = feature.get(param)
            if value is None:
                continue
            sums_by_param[param] += float(value) * effective_weight
            weights_by_param[param] += effective_weight
        if feature.get("cloud_percentage") is not None:
            cloud_sum += float(feature["cloud_percentage"]) * overlap
            cloud_weight_sum += overlap
        if feature.get("valid_pixel_count") is not None and feature.get("pixel_count"):
            valid_sum += (float(feature["valid_pixel_count"]) / max(1.0, float(feature["pixel_count"]))) * overlap * 100.0
            valid_weight_sum += overlap
        if feature.get("mean_swir16") is not None or feature.get("mean_swir22") is not None:
            temp = (float(feature.get("mean_swir16") or 0) + float(feature.get("mean_swir22") or 0)) / 2.0
            temp_sum += temp * effective_weight
            temp_weight_sum += effective_weight

    def safe_avg(param: str) -> float | None:
        if weights_by_param[param] <= 0:
            return None
        return round(sums_by_param[param] / weights_by_param[param], 6)

    cloud = round(cloud_sum / cloud_weight_sum, 6) if cloud_weight_sum else None
    valid_pixels = round(valid_sum / valid_weight_sum, 6) if valid_weight_sum else None
    temp = round(temp_sum / temp_weight_sum, 6) if temp_weight_sum else None

    return {
        "grid_cell_id": cell["grid_cell_id"],
        "farm_id": str(farm_id),
        "snapshot_date": snapshot_date,
        "ndvi": safe_avg("ndvi"),
        "ndmi": safe_avg("ndmi"),
        "ndwi": safe_avg("ndwi"),
        "bsi": safe_avg("bsi"),
        "evi": safe_avg("evi"),
        "savi": safe_avg("savi"),
        "msi": safe_avg("msi"),
        "nbr": safe_avg("nbr"),
        "ndre": safe_avg("ndre"),
        "surface_temp_c": temp,
        "cloud_percentage": cloud,
        "valid_pixel_percentage": valid_pixels,
        "vegetation_trend": "stable",
        "moisture_trend": "stable",
        "soil_exposure_trend": "stable",
        "value_source": "h3_grid_overlap_weighted",
        "grid_row": cell.get("grid_row"),
        "grid_col": cell.get("grid_col"),
        "cell_polygon_geojson": cell.get("cell_polygon_geojson"),
        "cell_centroid_lon": cell.get("cell_centroid_lon"),
        "cell_centroid_lat": cell.get("cell_centroid_lat"),
        "coverage_ratio": cell.get("coverage_ratio"),
        "contributing_h3_count": len([c for c in contributions if features_by_h3.get(int(c["h3_index"]))]),
        "dominant_h3_index": dominant_h3,
        "max_h3_overlap_ratio": round(max_overlap, 6),
    }


def _load_farm_polygon(farm_id: UUID | str) -> tuple[dict[str, Any] | None, Polygon | None]:
    query = text(
        """
        SELECT farm_id, polygon_geojson
        FROM farms
        WHERE farm_id = :farm_id
          AND is_active = TRUE
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()
    if row is None:
        return None, None
    polygon_geojson = row["polygon_geojson"]
    if isinstance(polygon_geojson, str):
        import json
        polygon_geojson = json.loads(polygon_geojson)
    try:
        geom = shape(polygon_geojson)
    except Exception:
        return dict(row), None
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    return dict(row), geom


def _point_inside_polygon(poly: Polygon, lon: float, lat: float) -> bool:
    return poly.contains(Point(lon, lat)) or poly.touches(Point(lon, lat))


def _polygon_cell(lon0: float, lat0: float, lon1: float, lat1: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]],
    }


def _generate_fallback_grid(farm_id: UUID | str) -> list[dict[str, Any]]:
    farm_row, polygon = _load_farm_polygon(farm_id)
    if farm_row is None or polygon is None:
        return []

    minx, miny, maxx, maxy = polygon.bounds
    lon_step, lat_step = _fallback_grid_degrees((miny + maxy) / 2.0)

    cells: list[dict[str, Any]] = []
    grid_row = 0
    lat = miny
    while lat < maxy + lat_step:
        grid_col = 0
        lon = minx
        while lon < maxx + lon_step:
            cell_poly = Polygon([(lon, lat), (lon + lon_step, lat), (lon + lon_step, lat + lat_step), (lon, lat + lat_step)])
            centroid = cell_poly.centroid
            clipped = cell_poly.intersection(polygon)
            coverage_ratio = 0.0
            try:
                if not clipped.is_empty and cell_poly.area > 0:
                    coverage_ratio = round(float(clipped.area) / float(cell_poly.area), 6)
            except Exception:
                coverage_ratio = 0.0
            if coverage_ratio > 0.01:
                cells.append(
                    {
                        "grid_cell_id": f"fallback-{farm_id}-{grid_row}-{grid_col}",
                        "farm_id": str(farm_id),
                        "grid_size_meters": GRID_SIZE_METERS,
                        "grid_row": grid_row,
                        "grid_col": grid_col,
                        "cell_polygon_geojson": mapping(clipped if not clipped.is_empty else cell_poly),
                        "cell_centroid_lon": round(float(centroid.x), 6),
                        "cell_centroid_lat": round(float(centroid.y), 6),
                        "coverage_ratio": coverage_ratio,
                        "created_at": None,
                    }
                )
            lon += lon_step
            grid_col += 1
        lat += lat_step
        grid_row += 1

    return cells


def _latest_farm_summary(farm_id: UUID | str) -> dict[str, Any] | None:
    latest = get_latest_aggregate(farm_id)
    if latest is None:
        return None
    return latest


def _fallback_grid_values(farm_id: UUID | str) -> list[dict[str, Any]]:
    summary = _latest_farm_summary(farm_id)
    cells = get_farm_grid_cells(farm_id)
    if not cells:
        cells = _generate_fallback_grid(farm_id)
    if not cells:
        return []
    base = summary or {}
    snapshot_date = base.get("snapshot_date")
    if snapshot_date is None:
        return []
    return [
        {
            "grid_cell_id": cell["grid_cell_id"],
            "farm_id": str(farm_id),
            "snapshot_date": snapshot_date,
            "ndvi": base.get("avg_ndvi"),
            "ndmi": base.get("avg_ndmi"),
            "ndwi": base.get("avg_ndwi"),
            "bsi": base.get("avg_bsi"),
            "evi": base.get("avg_evi"),
            "savi": base.get("avg_savi"),
            "msi": base.get("avg_msi"),
            "nbr": base.get("avg_nbr"),
            "ndre": base.get("avg_ndre"),
            "surface_temp_c": None,
            "cloud_percentage": base.get("avg_cloud_percentage"),
            "valid_pixel_percentage": base.get("valid_pixel_percentage"),
            "vegetation_trend": "stable",
            "moisture_trend": "stable",
            "soil_exposure_trend": "stable",
            "value_source": "farm_weighted_average_fallback",
            "grid_row": cell.get("grid_row"),
            "grid_col": cell.get("grid_col"),
            "cell_polygon_geojson": cell.get("cell_polygon_geojson"),
            "cell_centroid_lon": cell.get("cell_centroid_lon"),
            "cell_centroid_lat": cell.get("cell_centroid_lat"),
            "coverage_ratio": cell.get("coverage_ratio"),
        }
        for cell in cells
    ]


FEATURE_COLUMNS = """
    feature_id,
    farm_id,
    farmer_id,
    fpo_id,

    state_name,
    district_name,
    district_code,
    block_name,
    block_code,

    snapshot_date,
    scene_id,
    scene_datetime,
    scene_cloud_cover,

    h3_resolution,
    h3_index,

    pixel_count,
    valid_pixel_count,
    cloud_pixel_count,
    nodata_pixel_count,
    cloud_percentage,

    mean_blue,
    mean_green,
    mean_red,
    mean_rededge1,
    mean_rededge2,
    mean_rededge3,
    mean_nir,
    mean_nir08,
    mean_swir16,
    mean_swir22,

    ndvi,
    gndvi,
    evi,
    savi,
    ndmi,
    ndwi,
    mndwi,
    msi,
    bsi,
    nbr,
    nbr2,
    ndre,
    reci,

    source_assets_used,
    parquet_uri,
    created_at
"""


def get_latest_snapshot_key(farm_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT snapshot_date, scene_id
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        ORDER BY snapshot_date DESC, created_at DESC
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()

    return dict(row) if row else None


def get_features_for_snapshot(
    farm_id: UUID | str,
    snapshot_date: Any,
    scene_id: str,
) -> list[dict[str, Any]]:
    query = text(
        f"""
        SELECT {FEATURE_COLUMNS}
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = :snapshot_date
          AND scene_id = :scene_id
        ORDER BY h3_index;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "snapshot_date": snapshot_date,
                    "scene_id": scene_id,
                },
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read Sentinel-2 features: {exc}"
        ) from exc

    return [dict(row) for row in rows]


def get_latest_features(farm_id: UUID | str) -> list[dict[str, Any]]:
    latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return []

    return get_features_for_snapshot(
        farm_id=farm_id,
        snapshot_date=latest["snapshot_date"],
        scene_id=latest["scene_id"],
    )


def get_history(farm_id: UUID | str, limit: int = 20) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            farm_id,
            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,

            COUNT(*) AS row_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,

            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,

            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi

        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY farm_id, snapshot_date, scene_id
        ORDER BY snapshot_date DESC
        LIMIT :limit;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "limit": limit,
                },
            ).mappings().all()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read Sentinel-2 history: {exc}"
        ) from exc

    return [dict(row) for row in rows]


def get_latest_aggregate(farm_id: UUID | str) -> dict[str, Any] | None:
    latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return None

    query = text(
        """
        SELECT
            farm_id,
            MIN(farmer_id::text)::uuid AS farmer_id,
            MIN(fpo_id::text)::uuid AS fpo_id,

            MAX(district_name) AS district_name,
            MAX(block_name) AS block_name,
            MAX(block_code) AS block_code,

            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,

            COUNT(*) AS row_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,

            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,

            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(gndvi)::numeric, 6)::double precision AS avg_gndvi,
            ROUND(AVG(evi)::numeric, 6)::double precision AS avg_evi,
            ROUND(AVG(savi)::numeric, 6)::double precision AS avg_savi,

            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(mndwi)::numeric, 6)::double precision AS avg_mndwi,
            ROUND(AVG(msi)::numeric, 6)::double precision AS avg_msi,

            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi,
            ROUND(AVG(nbr)::numeric, 6)::double precision AS avg_nbr,
            ROUND(AVG(nbr2)::numeric, 6)::double precision AS avg_nbr2,

            ROUND(AVG(ndre)::numeric, 6)::double precision AS avg_ndre,
            ROUND(AVG(reci)::numeric, 6)::double precision AS avg_reci

        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = :snapshot_date
          AND scene_id = :scene_id
        GROUP BY farm_id, snapshot_date, scene_id;
        """
    )

    try:
        with engine.connect() as conn:
            row = conn.execute(
                query,
                {
                    "farm_id": str(farm_id),
                    "snapshot_date": latest["snapshot_date"],
                    "scene_id": latest["scene_id"],
                },
            ).mappings().first()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to read latest aggregate: {exc}"
        ) from exc

    return dict(row) if row else None


def get_farm_trends(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            farm_id,
            snapshot_date,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi,
            ROUND(AVG(evi)::numeric, 6)::double precision AS avg_evi,
            ROUND(AVG(savi)::numeric, 6)::double precision AS avg_savi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(msi)::numeric, 6)::double precision AS avg_msi,
            ROUND(AVG(nbr)::numeric, 6)::double precision AS avg_nbr,
            ROUND(AVG(ndre)::numeric, 6)::double precision AS avg_ndre
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY farm_id, snapshot_date
        ORDER BY snapshot_date DESC
        LIMIT 30;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_farm_h3_cells(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        f"""
        SELECT {FEATURE_COLUMNS}
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
          AND snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
          )
        ORDER BY h3_index;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_farm_grid_cells(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            grid_cell_id,
            farm_id,
            grid_size_meters,
            grid_row,
            grid_col,
            cell_polygon_geojson,
            cell_centroid_lon,
            cell_centroid_lat,
            coverage_ratio,
            created_at
        FROM farm_grid_cells
        WHERE farm_id = :farm_id
        ORDER BY grid_row, grid_col;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    if rows:
        return [dict(row) for row in rows]
    return _generate_fallback_grid(farm_id)


def get_latest_grid_values(farm_id: UUID | str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            gv.*,
            gc.grid_row,
            gc.grid_col,
            gc.cell_polygon_geojson,
            gc.cell_centroid_lon,
            gc.cell_centroid_lat
        FROM farm_grid_daily_values gv
        JOIN farm_grid_cells gc ON gc.grid_cell_id = gv.grid_cell_id
        WHERE gv.farm_id = :farm_id
          AND gv.snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM farm_grid_daily_values
            WHERE farm_id = :farm_id
          )
        ORDER BY gc.grid_row, gc.grid_col;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    if rows:
        return [dict(row) for row in rows]
    cells = get_farm_grid_cells(farm_id)
    features_by_h3 = _latest_feature_rows_by_h3(farm_id)
    crosswalk_query = text(
        """
        SELECT
            grid_cell_id,
            h3_index,
            overlap_ratio
        FROM farm_grid_h3_crosswalk
        WHERE farm_id = :farm_id
        ORDER BY grid_cell_id, overlap_ratio DESC;
        """
    )
    with engine.connect() as conn:
        crosswalk_rows = conn.execute(crosswalk_query, {"farm_id": str(farm_id)}).mappings().all()

    crosswalk_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in crosswalk_rows:
        crosswalk_by_cell[str(row["grid_cell_id"])].append(dict(row))

    if cells and features_by_h3 and crosswalk_by_cell:
        values: list[dict[str, Any]] = []
        for cell in cells:
            contributions = crosswalk_by_cell.get(str(cell["grid_cell_id"]), [])
            weighted = _weighted_row_from_contributions(farm_id, cell, contributions, features_by_h3)
            if weighted:
                values.append(weighted)
        if values:
            return values

    return _fallback_grid_values(farm_id)


def get_grid_cell_details(farm_id: UUID | str, grid_cell_id: UUID | str) -> dict[str, Any] | None:
    cell_query = text(
        """
        SELECT *
        FROM farm_grid_cells
        WHERE farm_id = :farm_id
          AND grid_cell_id = :grid_cell_id
        LIMIT 1;
        """
    )
    value_query = text(
        """
        SELECT gv.*
        FROM farm_grid_daily_values gv
        WHERE gv.farm_id = :farm_id
          AND gv.grid_cell_id = :grid_cell_id
        ORDER BY gv.snapshot_date DESC
        LIMIT 1;
        """
    )
    contrib_query = text(
        """
        SELECT
            c.h3_index,
            c.overlap_ratio,
            f.snapshot_date,
            f.ndvi,
            f.ndmi,
            f.ndwi,
            f.bsi,
            f.valid_pixel_count
        FROM farm_grid_h3_crosswalk c
        LEFT JOIN LATERAL (
            SELECT *
            FROM h3_sentinel2_features
            WHERE farm_id = c.farm_id
              AND h3_index = c.h3_index
            ORDER BY snapshot_date DESC, created_at DESC
            LIMIT 1
        ) f ON TRUE
        WHERE c.farm_id = :farm_id
          AND c.grid_cell_id = :grid_cell_id
        ORDER BY c.overlap_ratio DESC;
        """
    )
    with engine.connect() as conn:
        cell = conn.execute(cell_query, {"farm_id": str(farm_id), "grid_cell_id": str(grid_cell_id)}).mappings().first()
        if cell is None:
            return None
        latest = conn.execute(value_query, {"farm_id": str(farm_id), "grid_cell_id": str(grid_cell_id)}).mappings().first()
        contributions = conn.execute(contrib_query, {"farm_id": str(farm_id), "grid_cell_id": str(grid_cell_id)}).mappings().all()
    features_by_h3 = _latest_feature_rows_by_h3(farm_id)

    def _recommendations(data: dict[str, Any]) -> list[str]:
        notes: list[str] = []
        if data.get("ndvi") is not None and float(data["ndvi"]) < 0.25:
            notes.append("Vegetation stress detected")
        if (data.get("ndmi") is not None and float(data["ndmi"]) < 0.05) or (data.get("ndwi") is not None and float(data["ndwi"]) < 0.05):
            notes.append("Moisture stress possible")
        if data.get("bsi") is not None and float(data["bsi"]) > 0.15:
            notes.append("Bare soil exposure is high")
        if data.get("cloud_percentage") is not None and float(data["cloud_percentage"]) > 40:
            notes.append("Satellite data quality warning due to cloud")
        return notes

    latest_values = dict(latest) if latest else {}
    if not latest_values:
        latest_values = _weighted_row_from_contributions(farm_id, dict(cell), [dict(row) for row in contributions], features_by_h3)
    weighted_average = {k: latest_values.get(k) for k in ["ndvi", "ndmi", "ndwi", "bsi", "evi", "savi", "msi", "nbr", "ndre", "surface_temp_c", "cloud_percentage", "valid_pixel_percentage"]}
    recommendations = _recommendations(latest_values)

    return {
        "grid_cell": dict(cell),
        "latest_values": latest_values,
        "h3_contributions": [
            {
                "h3_index": row.get("h3_index"),
                "overlap_ratio": row.get("overlap_ratio"),
                "overlap_percentage": round(float(row.get("overlap_ratio") or 0) * 100.0, 2),
                "ndvi": (features_by_h3.get(int(row.get("h3_index"))) or {}).get("ndvi"),
                "ndmi": (features_by_h3.get(int(row.get("h3_index"))) or {}).get("ndmi"),
                "bsi": (features_by_h3.get(int(row.get("h3_index"))) or {}).get("bsi"),
                "valid_pixel_count": (features_by_h3.get(int(row.get("h3_index"))) or {}).get("valid_pixel_count"),
            }
            for row in contributions
            if features_by_h3.get(int(row.get("h3_index")))
        ],
        "weighted_average": weighted_average,
        "recommendations": recommendations,
    }


def get_grid_value_history(farm_id: UUID | str, limit: int = 10) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            snapshot_date,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(ndwi)::numeric, 6)::double precision AS avg_ndwi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM farm_grid_daily_values
        WHERE farm_id = :farm_id
        GROUP BY snapshot_date
        ORDER BY snapshot_date DESC
        LIMIT :limit;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id), "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_farmer_analytics_summary(farmer_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            :farmer_id::uuid AS farmer_id,
            COUNT(DISTINCT farm_id) AS farm_count,
            COUNT(*) AS h3_record_count,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM h3_sentinel2_features
        WHERE farmer_id = :farmer_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().first()
    return dict(row) if row else {"farmer_id": str(farmer_id), "farm_count": 0, "h3_record_count": 0}


def get_fpo_analytics_summary(fpo_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            :fpo_id::uuid AS fpo_id,
            COUNT(DISTINCT farm_id) AS farm_count,
            COUNT(*) AS h3_record_count,
            ROUND(AVG(ndvi)::numeric, 6)::double precision AS avg_ndvi,
            ROUND(AVG(ndmi)::numeric, 6)::double precision AS avg_ndmi,
            ROUND(AVG(bsi)::numeric, 6)::double precision AS avg_bsi
        FROM h3_sentinel2_features
        WHERE fpo_id = :fpo_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().first()
    return dict(row) if row else {"fpo_id": str(fpo_id), "farm_count": 0, "h3_record_count": 0}
