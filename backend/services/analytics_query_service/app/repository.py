from __future__ import annotations

import json
import math
from collections import defaultdict
from typing import Any
from uuid import UUID

from shapely.geometry import Point, Polygon, mapping, shape
import uuid
import h3
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class AnalyticsQueryRepositoryError(RuntimeError):
    pass


GRID_SIZE_METERS = 10
METERS_PER_DEGREE_LAT = 111_320.0

USABLE_SCENE_MAX_CLOUD_PERCENTAGE = 40.0
USABLE_SCENE_MIN_VALID_PIXEL_PERCENTAGE = 1.0


def _fallback_grid_degrees(latitude: float) -> tuple[float, float]:
    lat_step = GRID_SIZE_METERS / METERS_PER_DEGREE_LAT
    lon_step = GRID_SIZE_METERS / max(1.0, METERS_PER_DEGREE_LAT * max(0.2, abs(__import__("math").cos(__import__("math").radians(latitude)))))
    return lon_step, lat_step


def _latest_feature_rows_by_h3(farm_id: UUID | str) -> dict[int, dict[str, Any]]:
    rows = get_latest_features(farm_id, usable_only=True)
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


def get_latest_usable_snapshot_key(farm_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            snapshot_date,
            scene_id,
            MAX(scene_datetime) AS scene_datetime,
            MAX(scene_cloud_cover) AS scene_cloud_cover,
            COUNT(*) AS row_count,
            COUNT(DISTINCT h3_index) AS distinct_h3_count,
            COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
            COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
            COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,
            CASE
                WHEN COALESCE(SUM(pixel_count), 0) > 0
                THEN ROUND(
                    (
                        COALESCE(SUM(valid_pixel_count), 0)::numeric
                        / NULLIF(COALESCE(SUM(pixel_count), 0), 0)::numeric
                    ) * 100.0,
                    6
                )::double precision
                ELSE 0.0
            END AS valid_pixel_percentage,
            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,
            MAX(created_at) AS latest_created_at
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY snapshot_date, scene_id
        HAVING
            COALESCE(SUM(valid_pixel_count), 0) > 0
            AND ROUND(AVG(cloud_percentage)::numeric, 6)::double precision <= 40.0
        ORDER BY snapshot_date DESC, latest_created_at DESC
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()

    return dict(row) if row else None

def get_latest_snapshot_key(
    farm_id: UUID | str,
    usable_only: bool = False,
) -> dict[str, Any] | None:
    if usable_only:
        query = text(
            """
            SELECT
                snapshot_date,
                scene_id,
                MAX(scene_datetime) AS scene_datetime,
                MAX(scene_cloud_cover) AS scene_cloud_cover,
                COUNT(*) AS row_count,
                COUNT(DISTINCT h3_index) AS distinct_h3_count,
                COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
                COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
                COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,
                ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,
                MAX(created_at) AS latest_created_at
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
            GROUP BY snapshot_date, scene_id
            HAVING
                COALESCE(SUM(valid_pixel_count), 0) > 0
                AND ROUND(AVG(cloud_percentage)::numeric, 6)::double precision <= :max_cloud
            ORDER BY snapshot_date DESC, latest_created_at DESC
            LIMIT 1;
            """
        )

        params = {
            "farm_id": str(farm_id),
            "max_cloud": USABLE_SCENE_MAX_CLOUD_PERCENTAGE,
        }

    else:
        query = text(
            """
            SELECT
                snapshot_date,
                scene_id,
                MAX(scene_datetime) AS scene_datetime,
                MAX(scene_cloud_cover) AS scene_cloud_cover,
                COUNT(*) AS row_count,
                COUNT(DISTINCT h3_index) AS distinct_h3_count,
                COALESCE(SUM(pixel_count), 0) AS total_pixel_count,
                COALESCE(SUM(valid_pixel_count), 0) AS total_valid_pixel_count,
                COALESCE(SUM(cloud_pixel_count), 0) AS total_cloud_pixel_count,
                ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,
                MAX(created_at) AS latest_created_at
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
            GROUP BY snapshot_date, scene_id
            ORDER BY snapshot_date DESC, latest_created_at DESC
            LIMIT 1;
            """
        )

        params = {
            "farm_id": str(farm_id),
        }

    with engine.connect() as conn:
        row = conn.execute(query, params).mappings().first()

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


def get_latest_features(
    farm_id: UUID | str,
    usable_only: bool = False,
) -> list[dict[str, Any]]:
    if usable_only:
        latest = get_latest_usable_snapshot_key(farm_id)
    else:
        latest = get_latest_snapshot_key(farm_id)

    if latest is None and usable_only:
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
    latest = get_latest_usable_snapshot_key(farm_id)

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
            ROUND(AVG(ndre)::numeric, 6)::double precision AS avg_ndre,
            ROUND(AVG(cloud_percentage)::numeric, 6)::double precision AS avg_cloud_percentage,
            CASE
                WHEN COALESCE(SUM(pixel_count), 0) > 0
                THEN ROUND(
                    (
                        COALESCE(SUM(valid_pixel_count), 0)::numeric
                        / NULLIF(COALESCE(SUM(pixel_count), 0), 0)::numeric
                    ) * 100.0,
                    6
                )::double precision
                ELSE 0.0
            END AS valid_pixel_percentage
        FROM h3_sentinel2_features
        WHERE farm_id = :farm_id
        GROUP BY farm_id, snapshot_date
        HAVING
            COALESCE(SUM(valid_pixel_count), 0) > 0
            AND ROUND(AVG(cloud_percentage)::numeric, 6)::double precision <= 40.0
        ORDER BY snapshot_date DESC
        LIMIT 30;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()

    return [dict(row) for row in rows]


def get_farm_h3_cells(farm_id: UUID | str) -> list[dict[str, Any]]:
    latest = get_latest_snapshot_key(farm_id, usable_only=True)

    if latest is None:
        latest = get_latest_snapshot_key(farm_id, usable_only=False)

    if latest is None:
        return []

    return get_features_for_snapshot(
        farm_id=farm_id,
        snapshot_date=latest["snapshot_date"],
        scene_id=latest["scene_id"],
    )


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


def get_persisted_grid_cell_count(farm_id: UUID | str) -> int:
    query = text(
        """
        SELECT COUNT(*) AS count
        FROM farm_grid_cells
        WHERE farm_id = :farm_id;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().one()

    return int(row["count"] or 0)

def get_latest_grid_value_count(farm_id: UUID | str) -> int:
    latest = get_latest_usable_snapshot_key(farm_id)

    if latest is None:
        latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return 0

    query = text(
        """
        SELECT COUNT(*) AS count
        FROM farm_grid_daily_values
        WHERE farm_id = :farm_id
          AND snapshot_date = :snapshot_date;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(
            query,
            {
                "farm_id": str(farm_id),
                "snapshot_date": latest["snapshot_date"],
            },
        ).mappings().one()

    return int(row["count"] or 0)


def get_latest_grid_values(farm_id: UUID | str) -> list[dict[str, Any]]:
    latest = get_latest_usable_snapshot_key(farm_id)

    if latest is None:
        latest = get_latest_snapshot_key(farm_id)

    if latest is None:
        return _fallback_grid_values(farm_id)

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
          AND gv.snapshot_date = :snapshot_date
        ORDER BY gc.grid_row, gc.grid_col;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {
                "farm_id": str(farm_id),
                "snapshot_date": latest["snapshot_date"],
            },
        ).mappings().all()

    if rows:
        return [dict(row) for row in rows]

    return _fallback_grid_values(farm_id)


def get_grid_cell_details(farm_id: UUID | str, grid_cell_id: UUID | str) -> dict[str, Any] | None:
    grid_cell_id_text = str(grid_cell_id)

    if grid_cell_id_text.startswith("fallback-"):
        fallback_cells = _generate_fallback_grid(farm_id)
        selected_cell = None

        for cell in fallback_cells:
            if str(cell.get("grid_cell_id")) == grid_cell_id_text:
                selected_cell = cell
                break

        if selected_cell is None:
            return None

        latest_values = None
        fallback_values = _fallback_grid_values(farm_id)

        for value in fallback_values:
            if str(value.get("grid_cell_id")) == grid_cell_id_text:
                latest_values = value
                break

        recommendations = [
            "This is a visual fallback grid cell.",
            "Run grid materialization to store real 10m grid cells, H3 overlap, and weighted grid values.",
        ]

        if latest_values:
            if latest_values.get("ndvi") is None:
                recommendations.append("No valid NDVI value is available for this cell yet.")
            if latest_values.get("valid_pixel_percentage") in (None, 0):
                recommendations.append("The latest satellite row has no valid pixels for vegetation calculation.")

        return {
            "grid_cell": selected_cell,
            "latest_values": latest_values,
            "h3_contributions": [],
            "weighted_average": {
                "ndvi": latest_values.get("ndvi") if latest_values else None,
                "ndmi": latest_values.get("ndmi") if latest_values else None,
                "ndwi": latest_values.get("ndwi") if latest_values else None,
                "bsi": latest_values.get("bsi") if latest_values else None,
                "evi": latest_values.get("evi") if latest_values else None,
                "savi": latest_values.get("savi") if latest_values else None,
                "msi": latest_values.get("msi") if latest_values else None,
                "nbr": latest_values.get("nbr") if latest_values else None,
                "ndre": latest_values.get("ndre") if latest_values else None,
                "surface_temp_c": latest_values.get("surface_temp_c") if latest_values else None,
                "cloud_percentage": latest_values.get("cloud_percentage") if latest_values else None,
                "valid_pixel_percentage": latest_values.get("valid_pixel_percentage") if latest_values else None,
            },
            "recommendations": recommendations,
            "value_source": "visual_fallback",
        }
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
        ORDER BY
            CASE
                WHEN COALESCE(gv.valid_pixel_percentage, 0) >= :min_valid
                 AND COALESCE(gv.cloud_percentage, 100) <= :max_cloud
                THEN 0
                ELSE 1
            END,
            gv.snapshot_date DESC
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
        latest = conn.execute(
    value_query,
    {
        "farm_id": str(farm_id),
        "grid_cell_id": str(grid_cell_id),
        "min_valid": USABLE_SCENE_MIN_VALID_PIXEL_PERCENTAGE,
        "max_cloud": USABLE_SCENE_MAX_CLOUD_PERCENTAGE,
    },
    ).mappings().first()
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

def _stable_grid_cell_uuid(
    farm_id: UUID | str,
    grid_size_meters: int,
    grid_row: int,
    grid_col: int,
) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"maatitrace:grid-cell:{farm_id}:{grid_size_meters}:{grid_row}:{grid_col}",
        )
    )


def _h3_bigint_to_polygon(h3_index: int) -> Polygon:
    h3_cell = h3.int_to_str(int(h3_index))

    if hasattr(h3, "cell_to_boundary"):
        boundary = h3.cell_to_boundary(h3_cell)
        coords = [(float(lng), float(lat)) for lat, lng in boundary]
        return Polygon(coords)

    boundary = h3.h3_to_geo_boundary(h3_cell, geo_json=True)
    coords = [(float(point[0]), float(point[1])) for point in boundary]
    return Polygon(coords)

def _generate_grid_cells_for_materialization(farm_id: UUID | str) -> list[dict[str, Any]]:
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
            raw_cell_poly = Polygon(
                [
                    (lon, lat),
                    (lon + lon_step, lat),
                    (lon + lon_step, lat + lat_step),
                    (lon, lat + lat_step),
                ]
            )

            clipped = raw_cell_poly.intersection(polygon)

            coverage_ratio = 0.0
            try:
                if not clipped.is_empty and raw_cell_poly.area > 0:
                    coverage_ratio = round(float(clipped.area) / float(raw_cell_poly.area), 6)
            except Exception:
                coverage_ratio = 0.0

            if coverage_ratio > 0.01:
                materialized_poly = clipped if not clipped.is_empty else raw_cell_poly
                centroid = materialized_poly.centroid

                cells.append(
                    {
                        "grid_cell_id": _stable_grid_cell_uuid(
                            farm_id=farm_id,
                            grid_size_meters=GRID_SIZE_METERS,
                            grid_row=grid_row,
                            grid_col=grid_col,
                        ),
                        "farm_id": str(farm_id),
                        "grid_size_meters": GRID_SIZE_METERS,
                        "grid_row": grid_row,
                        "grid_col": grid_col,
                        "cell_polygon_geojson": mapping(materialized_poly),
                        "cell_centroid_lon": round(float(centroid.x), 6),
                        "cell_centroid_lat": round(float(centroid.y), 6),
                        "coverage_ratio": coverage_ratio,
                    }
                )

            lon += lon_step
            grid_col += 1

        lat += lat_step
        grid_row += 1

    return cells


def upsert_farm_grid_cells(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO farm_grid_cells (
            grid_cell_id,
            farm_id,
            grid_size_meters,
            grid_row,
            grid_col,
            cell_polygon_geojson,
            cell_centroid_lon,
            cell_centroid_lat,
            coverage_ratio
        ) VALUES (
            :grid_cell_id,
            :farm_id,
            :grid_size_meters,
            :grid_row,
            :grid_col,
            CAST(:cell_polygon_geojson AS jsonb),
            :cell_centroid_lon,
            :cell_centroid_lat,
            :coverage_ratio
        )
        ON CONFLICT ON CONSTRAINT uq_farm_grid_cell
        DO UPDATE SET
            cell_polygon_geojson = EXCLUDED.cell_polygon_geojson,
            cell_centroid_lon = EXCLUDED.cell_centroid_lon,
            cell_centroid_lat = EXCLUDED.cell_centroid_lat,
            coverage_ratio = EXCLUDED.coverage_ratio,
            updated_at = now()
        RETURNING grid_cell_id;
        """
    )

    try:
        with engine.begin() as conn:
            for row in rows:
                params = row.copy()
                params["cell_polygon_geojson"] = json.dumps(
                    params.get("cell_polygon_geojson") or {}
                )

                returned = conn.execute(query, params).mappings().one()

                # Important:
                # If an existing grid cell was updated due to conflict,
                # use the real DB grid_cell_id for crosswalk + values.
                row["grid_cell_id"] = str(returned["grid_cell_id"])

    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(
            f"Failed to upsert farm grid cells: {exc}"
        ) from exc

    return len(rows)


def upsert_farm_grid_h3_crosswalk(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO farm_grid_h3_crosswalk (
            farm_id,
            grid_cell_id,
            h3_index,
            h3_resolution,
            overlap_ratio
        ) VALUES (
            :farm_id,
            :grid_cell_id,
            :h3_index,
            :h3_resolution,
            :overlap_ratio
        )
        ON CONFLICT ON CONSTRAINT uq_grid_h3_crosswalk
        DO UPDATE SET
            overlap_ratio = EXCLUDED.overlap_ratio,
            updated_at = now();
        """
    )

    try:
        with engine.begin() as conn:
            for row in rows:
                conn.execute(query, row)
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(f"Failed to upsert crosswalk rows: {exc}") from exc

    return len(rows)


def upsert_farm_grid_daily_values(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO farm_grid_daily_values (
            farm_id,
            grid_cell_id,
            snapshot_date,
            ndvi,
            ndmi,
            ndwi,
            bsi,
            evi,
            savi,
            msi,
            nbr,
            ndre,
            cloud_percentage,
            valid_pixel_percentage,
            value_source,
            contributing_h3_count,
            dominant_h3_index,
            max_h3_overlap_ratio
        ) VALUES (
            :farm_id,
            :grid_cell_id,
            :snapshot_date,
            :ndvi,
            :ndmi,
            :ndwi,
            :bsi,
            :evi,
            :savi,
            :msi,
            :nbr,
            :ndre,
            :cloud_percentage,
            :valid_pixel_percentage,
            :value_source,
            :contributing_h3_count,
            :dominant_h3_index,
            :max_h3_overlap_ratio
        )
        ON CONFLICT ON CONSTRAINT uq_farm_grid_daily_value
        DO UPDATE SET
            ndvi = EXCLUDED.ndvi,
            ndmi = EXCLUDED.ndmi,
            ndwi = EXCLUDED.ndwi,
            bsi = EXCLUDED.bsi,
            evi = EXCLUDED.evi,
            savi = EXCLUDED.savi,
            msi = EXCLUDED.msi,
            nbr = EXCLUDED.nbr,
            ndre = EXCLUDED.ndre,
            cloud_percentage = EXCLUDED.cloud_percentage,
            valid_pixel_percentage = EXCLUDED.valid_pixel_percentage,
            value_source = EXCLUDED.value_source,
            contributing_h3_count = EXCLUDED.contributing_h3_count,
            dominant_h3_index = EXCLUDED.dominant_h3_index,
            max_h3_overlap_ratio = EXCLUDED.max_h3_overlap_ratio,
            updated_at = now();
        """
    )

    try:
        with engine.begin() as conn:
            for row in rows:
                conn.execute(query, row)
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(f"Failed to upsert grid daily values: {exc}") from exc

    return len(rows)


def materialize_grid_for_farm(farm_id: UUID | str) -> dict[str, Any]:
    features = get_latest_features(farm_id, usable_only=True)

    if not features:
        return {
            "farm_id": str(farm_id),
            "status": "failed",
            "code": "NO_H3_FEATURES",
            "message": "Run farm analysis before grid materialization.",
            "grid_cells_created": 0,
            "crosswalk_rows_created": 0,
            "grid_values_created": 0,
            "warnings": ["No latest h3_sentinel2_features rows found for this farm."],
        }

    features_by_h3 = {
        int(row["h3_index"]): row
        for row in features
        if row.get("h3_index") is not None
    }

    if not features_by_h3:
        return {
            "farm_id": str(farm_id),
            "status": "failed",
            "code": "NO_VALID_H3_INDEXES",
            "message": "Latest feature rows do not contain H3 indexes.",
            "grid_cells_created": 0,
            "crosswalk_rows_created": 0,
            "grid_values_created": 0,
            "warnings": ["Feature rows exist but h3_index is missing."],
        }

    cells = _generate_grid_cells_for_materialization(farm_id)
    grid_cells_created = upsert_farm_grid_cells(cells)

    grid_polys: list[tuple[dict[str, Any], Polygon, float]] = []

    for cell in cells:
        try:
            poly = shape(cell["cell_polygon_geojson"])
            if poly.is_empty or poly.area <= 0:
                continue
            grid_polys.append((cell, poly, float(poly.area)))
        except Exception:
            continue

    h3_polys: dict[int, Polygon] = {}

    for h3_index in features_by_h3.keys():
        try:
            h3_polys[int(h3_index)] = _h3_bigint_to_polygon(int(h3_index))
        except Exception:
            continue

    crosswalk_rows: list[dict[str, Any]] = []

    for cell, grid_poly, grid_area in grid_polys:
        for h3_index, h3_poly in h3_polys.items():
            try:
                intersection = grid_poly.intersection(h3_poly)

                if intersection.is_empty:
                    continue

                overlap_ratio = round(
                    float(intersection.area) / max(1e-12, grid_area),
                    6,
                )

                if overlap_ratio <= 0:
                    continue

                feature = features_by_h3.get(int(h3_index)) or {}

                crosswalk_rows.append(
                    {
                        "farm_id": str(farm_id),
                        "grid_cell_id": str(cell["grid_cell_id"]),
                        "h3_index": int(h3_index),
                        "h3_resolution": int(feature.get("h3_resolution") or 12),
                        "overlap_ratio": overlap_ratio,
                    }
                )

            except Exception:
                continue

    crosswalk_created = upsert_farm_grid_h3_crosswalk(crosswalk_rows)

    crosswalk_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in crosswalk_rows:
        crosswalk_by_cell[str(row["grid_cell_id"])].append(row)

    values_rows: list[dict[str, Any]] = []

    for cell in cells:
        contributions = crosswalk_by_cell.get(str(cell["grid_cell_id"]), [])

        if not contributions:
            continue

        weighted = _weighted_row_from_contributions(
            farm_id=farm_id,
            cell=cell,
            contributions=contributions,
            features_by_h3=features_by_h3,
        )

        if not weighted:
            continue

        if weighted.get("snapshot_date") is None:
            continue

        values_rows.append(weighted)

    values_created = upsert_farm_grid_daily_values(values_rows)

    warnings: list[str] = []

    if len(features_by_h3) < 2:
        warnings.append(
            "Only one processed H3 feature is available. Run farm analysis again to process all static farm H3 cells."
        )

    if crosswalk_created == 0:
        warnings.append(
            "No H3-grid overlap rows were created. Check H3 polygon conversion and farm grid geometry."
        )

    if values_created == 0:
        warnings.append(
            "No weighted grid values were created. This usually means no crosswalk overlap or no valid snapshot values."
        )

    return {
        "farm_id": str(farm_id),
        "status": "succeeded" if values_created > 0 else "partial",
        "grid_size_meters": GRID_SIZE_METERS,
        "latest_h3_feature_count": len(features),
        "processed_h3_cell_count": len(features_by_h3),
        "grid_cells_created": grid_cells_created,
        "crosswalk_rows_created": crosswalk_created,
        "grid_values_created": values_created,
        "value_source": "h3_grid_overlap_weighted" if values_created > 0 else "not_available",
        "warnings": warnings,
    }


def upsert_farm_h3_daily_trends(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0

    query = text(
        """
        INSERT INTO farm_h3_daily_trends (
            farm_id,
            farmer_id,
            fpo_id,
            h3_index,
            h3_resolution,
            snapshot_date,
            ndvi,
            ndmi,
            bsi,
            ndvi_change,
            ndmi_change,
            bsi_change,
            vegetation_trend,
            moisture_trend,
            soil_exposure_trend
        ) VALUES (
            :farm_id,
            :farmer_id,
            :fpo_id,
            :h3_index,
            :h3_resolution,
            :snapshot_date,
            :ndvi,
            :ndmi,
            :bsi,
            :ndvi_change,
            :ndmi_change,
            :bsi_change,
            :vegetation_trend,
            :moisture_trend,
            :soil_exposure_trend
        )
        ON CONFLICT ON CONSTRAINT uq_farm_h3_daily_trend
        DO UPDATE SET
            ndvi = EXCLUDED.ndvi,
            ndmi = EXCLUDED.ndmi,
            bsi = EXCLUDED.bsi,
            ndvi_change = EXCLUDED.ndvi_change,
            ndmi_change = EXCLUDED.ndmi_change,
            bsi_change = EXCLUDED.bsi_change,
            vegetation_trend = EXCLUDED.vegetation_trend,
            moisture_trend = EXCLUDED.moisture_trend,
            soil_exposure_trend = EXCLUDED.soil_exposure_trend,
            updated_at = now();
        """
    )

    try:
        with engine.begin() as conn:
            for row in rows:
                conn.execute(query, row)
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(f"Failed to upsert h3 daily trends: {exc}") from exc

    return len(rows)


def materialize_trends_for_farm(farm_id: UUID | str) -> dict[str, Any]:
    # Select latest two records per h3_index
    query = text(
        """
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY h3_index ORDER BY snapshot_date DESC, created_at DESC) as rn
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
        ) t
        WHERE rn <= 2
        ORDER BY h3_index, rn;
        """
    )

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"farm_id": str(farm_id)}).mappings().all()
    except SQLAlchemyError as exc:
        raise AnalyticsQueryRepositoryError(f"Failed to read features for trends: {exc}") from exc

    from collections import defaultdict

    by_h3 = defaultdict(list)
    for r in rows:
        by_h3[int(r["h3_index"])].append(dict(r))

    trend_rows: list[dict[str, Any]] = []
    for h3_index, recs in by_h3.items():
        if not recs:
            continue
        latest = recs[0]
        prev = recs[1] if len(recs) > 1 else None

        def delta(curr, prevv):
            if curr is None or prevv is None:
                return None
            try:
                return round(float(curr) - float(prevv), 6)
            except Exception:
                return None

        ndvi_change = delta(latest.get("ndvi"), prev.get("ndvi") if prev else None)
        ndmi_change = delta(latest.get("ndmi"), prev.get("ndmi") if prev else None)
        bsi_change = delta(latest.get("bsi"), prev.get("bsi") if prev else None)

        def trend_label(change):
            if change is None:
                return "unknown"
            if abs(change) < 0.03:
                return "stable"
            return "improving" if change > 0 else "degrading"

        vegetation_trend = trend_label(ndvi_change)
        moisture_trend = trend_label(ndmi_change)
        soil_exposure_trend = trend_label(bsi_change)

        trend_rows.append(
            {
                "farm_id": str(farm_id),
                "farmer_id": latest.get("farmer_id"),
                "fpo_id": latest.get("fpo_id"),
                "h3_index": int(h3_index),
                "h3_resolution": int(latest.get("h3_resolution") or 0),
                "snapshot_date": latest.get("snapshot_date"),
                "ndvi": latest.get("ndvi"),
                "ndmi": latest.get("ndmi"),
                "bsi": latest.get("bsi"),
                "ndvi_change": ndvi_change,
                "ndmi_change": ndmi_change,
                "bsi_change": bsi_change,
                "vegetation_trend": vegetation_trend,
                "moisture_trend": moisture_trend,
                "soil_exposure_trend": soil_exposure_trend,
            }
        )

    created = upsert_farm_h3_daily_trends(trend_rows)

    return {
        "farm_id": str(farm_id),
        "status": "succeeded" if created > 0 else "partial",
        "trends_created": created,
        "h3_cells_with_trends": len(trend_rows),
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
