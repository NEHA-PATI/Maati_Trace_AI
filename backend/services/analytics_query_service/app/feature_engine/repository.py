from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class FeatureEngineRepositoryError(RuntimeError):
    pass


def _is_undefined_table(exc: SQLAlchemyError) -> bool:
    """True when the query failed only because a feature-engine table does not exist
    yet (migration 20260903_08 not applied). Lets read/list endpoints degrade to
    empty instead of 500 before the operator runs the migration."""
    pgcode = getattr(getattr(exc, "orig", None), "pgcode", None)
    if pgcode == "42P01":
        return True
    message = str(exc).lower()
    return "does not exist" in message and (
        "relation" in message or "table" in message
    )


def _json(value: Any) -> str:
    def default(item: Any):
        if isinstance(item, (date, datetime)):
            return item.isoformat()
        if isinstance(item, UUID):
            return str(item)
        try:
            from decimal import Decimal
            if isinstance(item, Decimal):
                return float(item)
        except Exception:
            pass
        return str(item)

    return json.dumps(value if value is not None else {}, default=default)


def _rows(query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).mappings().all()
        return [dict(row) for row in result]
    except SQLAlchemyError as exc:
        if _is_undefined_table(exc):
            return []
        raise FeatureEngineRepositoryError(str(exc)) from exc


def _row(query: str, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params).mappings().first()
        return dict(result) if result else None
    except SQLAlchemyError as exc:
        if _is_undefined_table(exc):
            return None
        raise FeatureEngineRepositoryError(str(exc)) from exc


def get_farm_context(farm_id: UUID | str) -> dict[str, Any] | None:
    return _row(
        """
        SELECT
            farm_id, farmer_id, fpo_id, farm_name,
            state_name, district_name, district_code, block_name, block_code,
            h3_resolution, h3_cells, h3_cell_count, area_acres,
            crop_code, crop_name, crop_variety, crop_stage, planting_date,
            is_active
        FROM farms
        WHERE farm_id = :farm_id
          AND is_active = TRUE
        LIMIT 1;
        """,
        {"farm_id": str(farm_id)},
    )


def get_active_crop_profile(crop_code: str) -> dict[str, Any] | None:
    return _row(
        """
        SELECT *
        FROM crop_feature_profiles
        WHERE crop_code = :crop_code
          AND is_active = TRUE
          AND status = 'published'
        ORDER BY published_at DESC NULLS LAST, created_at DESC
        LIMIT 1;
        """,
        {"crop_code": crop_code},
    )


def get_active_formulas(
    crop_code: str,
    crop_profile_version: str | None = None,
) -> list[dict[str, Any]]:
    where = [
        "crop_code = :crop_code",
        "is_active = TRUE",
        "status = 'published'",
    ]
    params: dict[str, Any] = {"crop_code": crop_code}
    if crop_profile_version:
        where.append("crop_profile_version = :crop_profile_version")
        params["crop_profile_version"] = crop_profile_version
    return _rows(
        f"""
        SELECT *
        FROM crop_formula_registry
        WHERE {' AND '.join(where)}
        ORDER BY execution_order, prediction_key;
        """,
        params,
    )


def list_public_crop_profiles() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT
            profile_id, crop_code, crop_name, profile_version, crop_type,
            minimum_history_days, preferred_history_days,
            temporal_windows, root_zone_weights, soil_ranges, normalization,
            growth_config, metadata, status, is_active, published_at
        FROM crop_feature_profiles p
        WHERE p.status = 'published'
          AND p.is_active = TRUE
          AND EXISTS (
              SELECT 1
              FROM crop_formula_registry f
              WHERE f.crop_code = p.crop_code
                AND f.crop_profile_version = p.profile_version
                AND f.status = 'published'
                AND f.is_active = TRUE
          )
        ORDER BY crop_name;
        """,
        {},
    )


def list_public_formulas(crop_code: str | None = None) -> list[dict[str, Any]]:
    where = "WHERE f.status = 'published' AND f.is_active = TRUE"
    params: dict[str, Any] = {}
    if crop_code:
        where += " AND f.crop_code = :crop_code"
        params["crop_code"] = crop_code
    return _rows(
        f"""
        SELECT f.formula_id, f.crop_code, f.prediction_key, f.display_name,
               f.formula_version, f.crop_profile_version, f.formula_type,
               f.score_direction, f.execution_order, f.component_weights,
               f.thresholds, f.parameters, f.description, f.metadata, f.status,
               f.is_active, f.published_at
        FROM crop_formula_registry f
        JOIN crop_feature_profiles p
          ON p.crop_code = f.crop_code
         AND p.profile_version = f.crop_profile_version
         AND p.status = 'published'
         AND p.is_active = TRUE
        {where}
        ORDER BY f.crop_code, f.execution_order, f.prediction_key;
        """,
        params,
    )


def get_component_catalog() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT *
        FROM calculation_component_catalog
        WHERE is_active = TRUE
        ORDER BY category, display_name;
        """,
        {},
    )


def get_source_bundle(
    farm_id: UUID | str,
    *,
    history_start: date,
    end_date: date,
) -> dict[str, list[dict[str, Any]]]:
    params = {
        "farm_id": str(farm_id),
        "history_start": history_start,
        "end_date": end_date,
    }
    return {
        "sentinel2": _rows(
            """
            SELECT *
            FROM h3_sentinel2_features
            WHERE farm_id = :farm_id
              AND snapshot_date BETWEEN :history_start AND :end_date
            ORDER BY h3_index, snapshot_date, valid_fraction DESC NULLS LAST, created_at DESC;
            """,
            params,
        ),
        "sentinel1": _rows(
            """
            SELECT *
            FROM h3_sentinel1_features
            WHERE farm_id = :farm_id
              AND snapshot_date BETWEEN :history_start AND :end_date
            ORDER BY h3_index, snapshot_date, valid_fraction DESC NULLS LAST, created_at DESC;
            """,
            params,
        ),
        "landsat": _rows(
            """
            SELECT *
            FROM h3_landsat_features
            WHERE farm_id = :farm_id
              AND snapshot_date BETWEEN :history_start AND :end_date
            ORDER BY h3_index, snapshot_date, valid_fraction DESC NULLS LAST, created_at DESC;
            """,
            params,
        ),
        "gpm": _rows(
            """
            SELECT *
            FROM farm_weather_observations
            WHERE farm_id = :farm_id
              AND observation_date BETWEEN :history_start AND :end_date
            ORDER BY observation_date;
            """,
            params,
        ),
        "era5": _rows(
            """
            SELECT *
            FROM farm_reanalysis_daily
            WHERE farm_id = :farm_id
              AND observation_date BETWEEN :history_start AND :end_date
            ORDER BY observation_date;
            """,
            params,
        ),
        "smap": _rows(
            """
            SELECT *
            FROM farm_smap_observations
            WHERE farm_id = :farm_id
              AND observed_at::date BETWEEN :history_start AND :end_date
            ORDER BY observed_at;
            """,
            params,
        ),
        "modis_et": _rows(
            """
            SELECT *
            FROM farm_modis_et_observations
            WHERE farm_id = :farm_id
              AND period_end >= :history_start
              AND period_start <= :end_date
            ORDER BY period_start;
            """,
            params,
        ),
        "modis_vegetation": _rows(
            """
            SELECT *
            FROM farm_modis_vegetation_observations
            WHERE farm_id = :farm_id
              AND period_end >= :history_start
              AND period_start <= :end_date
            ORDER BY period_start;
            """,
            params,
        ),
        "forecast": _rows(
            """
            SELECT *
            FROM farm_weather_forecasts
            WHERE farm_id = :farm_id
              AND issued_at::date <= :end_date
              AND valid_at::date >= :history_start
            ORDER BY issued_at, valid_at;
            """,
            params,
        ),
        "terrain": _rows(
            "SELECT * FROM h3_terrain_features WHERE farm_id = :farm_id ORDER BY h3_index, updated_at DESC;",
            {"farm_id": str(farm_id)},
        ),
        "landcover": _rows(
            "SELECT * FROM h3_landcover_features WHERE farm_id = :farm_id ORDER BY h3_index, reference_year DESC NULLS LAST, created_at DESC;",
            {"farm_id": str(farm_id)},
        ),
        "jrc_water": _rows(
            "SELECT * FROM h3_surface_water_features WHERE farm_id = :farm_id ORDER BY h3_index, created_at DESC;",
            {"farm_id": str(farm_id)},
        ),
        "soilgrids": _rows(
            """
            SELECT *
            FROM h3_soilgrids_features
            WHERE farm_id = :farm_id
            ORDER BY h3_index, property_key, depth_top_cm, depth_bottom_cm, created_at DESC;
            """,
            {"farm_id": str(farm_id)},
        ),
    }


def upsert_engineered_features(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    query = text(
        """
        INSERT INTO farm_h3_engineered_features (
            farm_id, farmer_id, fpo_id, h3_index, h3_resolution,
            feature_date, crop_code, crop_profile_version, feature_version,
            anchor_dataset, anchor_scene_id, observed_area_m2,
            anchor_valid_fraction, confidence,
            features, quality, source_dates, source_versions
        ) VALUES (
            :farm_id, :farmer_id, :fpo_id, :h3_index, :h3_resolution,
            :feature_date, :crop_code, :crop_profile_version, :feature_version,
            :anchor_dataset, :anchor_scene_id, :observed_area_m2,
            :anchor_valid_fraction, :confidence,
            CAST(:features AS jsonb), CAST(:quality AS jsonb),
            CAST(:source_dates AS jsonb), CAST(:source_versions AS jsonb)
        )
        ON CONFLICT ON CONSTRAINT uq_farm_h3_engineered_feature
        DO UPDATE SET
            farmer_id = EXCLUDED.farmer_id,
            fpo_id = EXCLUDED.fpo_id,
            h3_resolution = EXCLUDED.h3_resolution,
            anchor_dataset = EXCLUDED.anchor_dataset,
            anchor_scene_id = EXCLUDED.anchor_scene_id,
            observed_area_m2 = EXCLUDED.observed_area_m2,
            anchor_valid_fraction = EXCLUDED.anchor_valid_fraction,
            confidence = EXCLUDED.confidence,
            features = EXCLUDED.features,
            quality = EXCLUDED.quality,
            source_dates = EXCLUDED.source_dates,
            source_versions = EXCLUDED.source_versions,
            updated_at = now();
        """
    )
    try:
        with engine.begin() as conn:
            for row in rows:
                payload = dict(row)
                for key in ["features", "quality", "source_dates", "source_versions"]:
                    payload[key] = _json(payload.get(key))
                conn.execute(query, payload)
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to persist engineered features: {exc}") from exc
    return len(rows)


def get_engineered_features(
    farm_id: UUID | str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    latest_only: bool = False,
) -> list[dict[str, Any]]:
    where = ["farm_id = :farm_id"]
    params: dict[str, Any] = {"farm_id": str(farm_id)}
    if start_date:
        where.append("feature_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where.append("feature_date <= :end_date")
        params["end_date"] = end_date
    if latest_only:
        where.append("feature_date = (SELECT MAX(feature_date) FROM farm_h3_engineered_features WHERE farm_id = :farm_id)")
    return _rows(
        f"""
        SELECT *
        FROM farm_h3_engineered_features
        WHERE {' AND '.join(where)}
        ORDER BY feature_date, h3_index;
        """,
        params,
    )


def upsert_prediction_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    h3_query = text(
        """
        INSERT INTO farm_calculated_predictions (
            farm_id, farmer_id, fpo_id, h3_index, h3_resolution,
            result_scope, result_date, crop_code, prediction_key, display_name,
            score, score_direction, status_label, confidence, affected_area_percent,
            formula_version, crop_profile_version, feature_version,
            components, evidence, quality, metadata
        ) VALUES (
            :farm_id, :farmer_id, :fpo_id, :h3_index, :h3_resolution,
            :result_scope, :result_date, :crop_code, :prediction_key, :display_name,
            :score, :score_direction, :status_label, :confidence, :affected_area_percent,
            :formula_version, :crop_profile_version, :feature_version,
            CAST(:components AS jsonb), CAST(:evidence AS jsonb), CAST(:quality AS jsonb), CAST(:metadata AS jsonb)
        )
        ON CONFLICT (farm_id, h3_index, result_date, prediction_key, formula_version)
          WHERE result_scope = 'h3' AND h3_index IS NOT NULL
        DO UPDATE SET
            score = EXCLUDED.score,
            status_label = EXCLUDED.status_label,
            confidence = EXCLUDED.confidence,
            affected_area_percent = EXCLUDED.affected_area_percent,
            components = EXCLUDED.components,
            evidence = EXCLUDED.evidence,
            quality = EXCLUDED.quality,
            metadata = EXCLUDED.metadata,
            updated_at = now();
        """
    )
    farm_query = text(
        """
        INSERT INTO farm_calculated_predictions (
            farm_id, farmer_id, fpo_id, h3_index, h3_resolution,
            result_scope, result_date, crop_code, prediction_key, display_name,
            score, score_direction, status_label, confidence, affected_area_percent,
            formula_version, crop_profile_version, feature_version,
            components, evidence, quality, metadata
        ) VALUES (
            :farm_id, :farmer_id, :fpo_id, NULL, NULL,
            :result_scope, :result_date, :crop_code, :prediction_key, :display_name,
            :score, :score_direction, :status_label, :confidence, :affected_area_percent,
            :formula_version, :crop_profile_version, :feature_version,
            CAST(:components AS jsonb), CAST(:evidence AS jsonb), CAST(:quality AS jsonb), CAST(:metadata AS jsonb)
        )
        ON CONFLICT (farm_id, result_date, prediction_key, formula_version)
          WHERE result_scope = 'farm' AND h3_index IS NULL
        DO UPDATE SET
            score = EXCLUDED.score,
            status_label = EXCLUDED.status_label,
            confidence = EXCLUDED.confidence,
            affected_area_percent = EXCLUDED.affected_area_percent,
            components = EXCLUDED.components,
            evidence = EXCLUDED.evidence,
            quality = EXCLUDED.quality,
            metadata = EXCLUDED.metadata,
            updated_at = now();
        """
    )
    try:
        with engine.begin() as conn:
            for row in rows:
                payload = dict(row)
                for key in ["components", "evidence", "quality", "metadata"]:
                    payload[key] = _json(payload.get(key))
                conn.execute(h3_query if row.get("result_scope") == "h3" else farm_query, payload)
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to persist calculated predictions: {exc}") from exc
    return len(rows)


def get_calculated_predictions(
    farm_id: UUID | str,
    *,
    scope: str = "farm",
    latest_only: bool = True,
    prediction_key: str | None = None,
) -> list[dict[str, Any]]:
    where = ["farm_id = :farm_id", "result_scope = :scope"]
    params: dict[str, Any] = {"farm_id": str(farm_id), "scope": scope}
    if prediction_key:
        where.append("prediction_key = :prediction_key")
        params["prediction_key"] = prediction_key
    if latest_only:
        where.append(
            "result_date = (SELECT MAX(result_date) FROM farm_calculated_predictions WHERE farm_id = :farm_id AND result_scope = :scope)"
        )
    return _rows(
        f"""
        SELECT *
        FROM farm_calculated_predictions
        WHERE {' AND '.join(where)}
        ORDER BY result_date DESC, prediction_key, h3_index NULLS LAST;
        """,
        params,
    )


def get_grid_crosswalk(farm_id: UUID | str) -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT
            c.farm_id, c.grid_cell_id, c.h3_index, c.h3_resolution, c.overlap_ratio,
            gc.grid_row, gc.grid_col, gc.grid_size_meters, gc.cell_polygon_geojson,
            gc.cell_centroid_lon, gc.cell_centroid_lat, gc.coverage_ratio
        FROM farm_grid_h3_crosswalk c
        JOIN farm_grid_cells gc ON gc.grid_cell_id = c.grid_cell_id
        WHERE c.farm_id = :farm_id
        ORDER BY gc.grid_row, gc.grid_col, c.overlap_ratio DESC;
        """,
        {"farm_id": str(farm_id)},
    )


def upsert_grid_prediction_rows(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    query = text(
        """
        INSERT INTO farm_grid_calculated_values (
            farm_id, grid_cell_id, result_date, crop_code,
            prediction_key, display_name, score, score_direction,
            status_label, confidence, formula_version, crop_profile_version,
            feature_version, value_source, contributing_h3_count,
            dominant_h3_index, max_h3_overlap_ratio, components, evidence
        ) VALUES (
            :farm_id, :grid_cell_id, :result_date, :crop_code,
            :prediction_key, :display_name, :score, :score_direction,
            :status_label, :confidence, :formula_version, :crop_profile_version,
            :feature_version, :value_source, :contributing_h3_count,
            :dominant_h3_index, :max_h3_overlap_ratio,
            CAST(:components AS jsonb), CAST(:evidence AS jsonb)
        )
        ON CONFLICT ON CONSTRAINT uq_farm_grid_calculated_value
        DO UPDATE SET
            score = EXCLUDED.score,
            status_label = EXCLUDED.status_label,
            confidence = EXCLUDED.confidence,
            value_source = EXCLUDED.value_source,
            contributing_h3_count = EXCLUDED.contributing_h3_count,
            dominant_h3_index = EXCLUDED.dominant_h3_index,
            max_h3_overlap_ratio = EXCLUDED.max_h3_overlap_ratio,
            components = EXCLUDED.components,
            evidence = EXCLUDED.evidence,
            updated_at = now();
        """
    )
    try:
        with engine.begin() as conn:
            for row in rows:
                payload = dict(row)
                payload["components"] = _json(payload.get("components"))
                payload["evidence"] = _json(payload.get("evidence"))
                conn.execute(query, payload)
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to persist grid calculations: {exc}") from exc
    return len(rows)


def get_latest_grid_calculations(farm_id: UUID | str) -> list[dict[str, Any]]:
    rows = _rows(
        """
        SELECT
            gv.*,
            gc.grid_row, gc.grid_col, gc.grid_size_meters,
            gc.cell_polygon_geojson, gc.cell_centroid_lon, gc.cell_centroid_lat,
            gc.coverage_ratio
        FROM farm_grid_calculated_values gv
        JOIN farm_grid_cells gc ON gc.grid_cell_id = gv.grid_cell_id
        WHERE gv.farm_id = :farm_id
          AND gv.result_date = (
              SELECT MAX(result_date) FROM farm_grid_calculated_values WHERE farm_id = :farm_id
          )
        ORDER BY gc.grid_row, gc.grid_col, gv.prediction_key;
        """,
        {"farm_id": str(farm_id)},
    )
    # Pivot one database row per prediction into one frontend row per display grid cell.
    by_cell: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row["grid_cell_id"])
        cell = by_cell.setdefault(
            key,
            {
                "farm_id": row["farm_id"],
                "grid_cell_id": row["grid_cell_id"],
                "grid_row": row["grid_row"],
                "grid_col": row["grid_col"],
                "grid_size_meters": row["grid_size_meters"],
                "cell_polygon_geojson": row["cell_polygon_geojson"],
                "cell_centroid_lon": row["cell_centroid_lon"],
                "cell_centroid_lat": row["cell_centroid_lat"],
                "coverage_ratio": row["coverage_ratio"],
                "result_date": row["result_date"],
                "crop_code": row["crop_code"],
                "calculations": {},
            },
        )
        prediction = row["prediction_key"]
        payload = {
            "score": row.get("score"),
            "status_label": row.get("status_label"),
            "confidence": row.get("confidence"),
            "score_direction": row.get("score_direction"),
            "display_name": row.get("display_name"),
            "formula_version": row.get("formula_version"),
            "components": row.get("components") or {},
            "evidence": row.get("evidence") or [],
            "value_source": row.get("value_source"),
            "contributing_h3_count": row.get("contributing_h3_count"),
            "dominant_h3_index": row.get("dominant_h3_index"),
        }
        cell["calculations"][prediction] = payload
        cell[f"{prediction}_score"] = row.get("score")
        cell[f"{prediction}_status"] = row.get("status_label")
        cell[f"{prediction}_confidence"] = row.get("confidence")
    return list(by_cell.values())


def get_grid_cell_calculations(farm_id: UUID | str, grid_cell_id: UUID | str) -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT *
        FROM farm_grid_calculated_values
        WHERE farm_id = :farm_id
          AND grid_cell_id = :grid_cell_id
          AND result_date = (
              SELECT MAX(result_date)
              FROM farm_grid_calculated_values
              WHERE farm_id = :farm_id AND grid_cell_id = :grid_cell_id
          )
        ORDER BY prediction_key;
        """,
        {"farm_id": str(farm_id), "grid_cell_id": str(grid_cell_id)},
    )


# ---------------- Pipeline job tracking ----------------

def create_pipeline_job(farm_id: UUID | str, job_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    INSERT INTO pipeline_jobs (farm_id, service_name, job_type, status, current_stage, metadata)
                    VALUES (:farm_id, 'analytics_query_service', :job_type, 'running', 'starting', CAST(:metadata AS jsonb))
                    RETURNING *;
                    """
                ),
                {"farm_id": str(farm_id), "job_type": job_type, "metadata": _json(metadata)},
            ).mappings().one()
        return dict(row)
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to create pipeline job: {exc}") from exc


def update_pipeline_job(job_id: UUID | str, *, stage: str, status: str = "running", metadata: dict[str, Any] | None = None) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE pipeline_jobs
                    SET current_stage = :stage,
                        status = :status,
                        metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                        updated_at = now()
                    WHERE job_id = :job_id;
                    """
                ),
                {"job_id": str(job_id), "stage": stage, "status": status, "metadata": _json(metadata)},
            )
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to update pipeline job: {exc}") from exc


def finish_pipeline_job(job_id: UUID | str, *, succeeded: bool, metadata: dict[str, Any] | None = None, error: str | None = None) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE pipeline_jobs
                    SET current_stage = NULL,
                        status = :status,
                        finished_at = now(),
                        error_code = CASE WHEN :success THEN NULL ELSE 'FEATURE_PROCESSING_ERROR' END,
                        error_message = :error,
                        metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata AS jsonb),
                        updated_at = now()
                    WHERE job_id = :job_id;
                    """
                ),
                {
                    "job_id": str(job_id),
                    "status": "succeeded" if succeeded else "failed",
                    "success": succeeded,
                    "error": error,
                    "metadata": _json(metadata),
                },
            )
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to finish pipeline job: {exc}") from exc


# ---------------- Admin configuration ----------------
def admin_list_profiles(include_inactive: bool = True) -> list[dict[str, Any]]:
    where = "" if include_inactive else "WHERE is_active = TRUE"
    return _rows(f"SELECT * FROM crop_feature_profiles {where} ORDER BY crop_code, created_at DESC;", {})


def admin_create_profile(data: dict[str, Any], actor_user_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        INSERT INTO crop_feature_profiles (
            crop_code, crop_name, profile_version, crop_type,
            minimum_history_days, preferred_history_days,
            temporal_windows, root_zone_weights, soil_ranges, normalization,
            growth_config, metadata, status, is_active, created_by, updated_by
        ) VALUES (
            :crop_code, :crop_name, :profile_version, :crop_type,
            :minimum_history_days, :preferred_history_days,
            CAST(:temporal_windows AS jsonb), CAST(:root_zone_weights AS jsonb),
            CAST(:soil_ranges AS jsonb), CAST(:normalization AS jsonb),
            CAST(:growth_config AS jsonb), CAST(:metadata AS jsonb),
            'draft', FALSE, :actor, :actor
        ) RETURNING *;
        """
    )
    payload = dict(data)
    for key in ["temporal_windows", "root_zone_weights", "soil_ranges", "normalization", "growth_config", "metadata"]:
        payload[key] = _json(payload.get(key))
    payload["actor"] = str(actor_user_id)
    try:
        with engine.begin() as conn:
            row = dict(conn.execute(query, payload).mappings().one())
        audit_change(actor_user_id, "crop_feature_profile", row["profile_id"], "create", None, row)
        return row
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to create crop profile: {exc}") from exc


def admin_update_profile(profile_id: UUID | str, data: dict[str, Any], actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not before:
        raise FeatureEngineRepositoryError("Crop profile not found")
    if before.get("status") != "draft":
        raise FeatureEngineRepositoryError("Published/archived profiles are immutable. Clone a new version before editing.")
    payload = dict(data)
    payload.update({"id": str(profile_id), "actor": str(actor_user_id)})
    for key in ["temporal_windows", "root_zone_weights", "soil_ranges", "normalization", "growth_config", "metadata"]:
        payload[key] = _json(payload.get(key))
    query = text(
        """
        UPDATE crop_feature_profiles SET
            crop_name=:crop_name, crop_type=:crop_type,
            minimum_history_days=:minimum_history_days,
            preferred_history_days=:preferred_history_days,
            temporal_windows=CAST(:temporal_windows AS jsonb),
            root_zone_weights=CAST(:root_zone_weights AS jsonb),
            soil_ranges=CAST(:soil_ranges AS jsonb),
            normalization=CAST(:normalization AS jsonb),
            growth_config=CAST(:growth_config AS jsonb),
            metadata=CAST(:metadata AS jsonb),
            updated_by=:actor, updated_at=now()
        WHERE profile_id=:id
        RETURNING *;
        """
    )
    try:
        with engine.begin() as conn:
            after = dict(conn.execute(query, payload).mappings().one())
        audit_change(actor_user_id, "crop_feature_profile", profile_id, "update", before, after)
        return after
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to update crop profile: {exc}") from exc


def admin_publish_profile(profile_id: UUID | str, actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not before:
        raise FeatureEngineRepositoryError("Crop profile not found")
    if before.get("status") == "archived":
        raise FeatureEngineRepositoryError("Archived crop profiles cannot be published")

    formula_count_row = _row(
        """
        SELECT COUNT(*)::integer AS formula_count
        FROM crop_formula_registry
        WHERE crop_code=:crop_code
          AND crop_profile_version=:profile_version
          AND status='published';
        """,
        {"crop_code": before["crop_code"], "profile_version": before["profile_version"]},
    )
    formula_count = int((formula_count_row or {}).get("formula_count") or 0)
    if formula_count <= 0:
        raise FeatureEngineRepositoryError(
            "Publish at least one formula for this profile version before publishing the crop profile. "
            "Formula versions can be published while the profile is still a draft; they remain inactive until this profile is activated."
        )

    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE crop_feature_profiles SET is_active=FALSE WHERE crop_code=:crop_code AND profile_id<>:id"),
                {"crop_code": before["crop_code"], "id": str(profile_id)},
            )
            after = dict(
                conn.execute(
                    text(
                        """
                        UPDATE crop_feature_profiles
                        SET status='published', is_active=TRUE, published_at=now(),
                            updated_by=:actor, updated_at=now()
                        WHERE profile_id=:id
                        RETURNING *;
                        """
                    ),
                    {"id": str(profile_id), "actor": str(actor_user_id)},
                ).mappings().one()
            )
            # Profile activation is the atomic production switch for crop formulas.
            conn.execute(
                text("UPDATE crop_formula_registry SET is_active=FALSE WHERE crop_code=:crop_code"),
                {"crop_code": before["crop_code"]},
            )
            conn.execute(
                text(
                    """
                    UPDATE crop_formula_registry
                    SET is_active=TRUE, updated_at=now()
                    WHERE crop_code=:crop_code
                      AND crop_profile_version=:profile_version
                      AND status='published';
                    """
                ),
                {"crop_code": before["crop_code"], "profile_version": before["profile_version"]},
            )
        audit_change(actor_user_id, "crop_feature_profile", profile_id, "publish", before, after)
        return {**after, "activated_formula_count": formula_count}
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to publish crop profile: {exc}") from exc


def admin_seed_formulas_for_profile(
    profile_id: UUID | str,
    source_crop_code: str,
    actor_user_id: UUID | str,
    formula_version_suffix: str = "v1",
) -> dict[str, Any]:
    target = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not target:
        raise FeatureEngineRepositoryError("Crop profile not found")
    if target.get("status") != "draft":
        raise FeatureEngineRepositoryError(
            "Formulas can only be seeded into a draft crop profile. Clone a new version first."
        )

    source_formulas = get_active_formulas(source_crop_code)
    if not source_formulas:
        source_formulas = _rows(
            """
            SELECT DISTINCT ON (prediction_key) *
            FROM crop_formula_registry
            WHERE crop_code = :c AND status = 'published'
            ORDER BY prediction_key, published_at DESC NULLS LAST, created_at DESC;
            """,
            {"c": source_crop_code},
        )
    if not source_formulas:
        raise FeatureEngineRepositoryError(
            f"No published formulas found on source crop '{source_crop_code}' to copy from."
        )

    existing = {
        row["prediction_key"]
        for row in _rows(
            "SELECT prediction_key FROM crop_formula_registry WHERE crop_code=:c AND crop_profile_version=:v",
            {"c": target["crop_code"], "v": target["profile_version"]},
        )
    }

    created: list[dict[str, Any]] = []
    for source in source_formulas:
        if source["prediction_key"] in existing:
            continue
        data = {key: source.get(key) for key in [
            "prediction_key", "display_name", "formula_type", "score_direction", "execution_order",
            "component_weights", "thresholds", "parameters", "description", "metadata",
        ]}
        data.update({
            "crop_code": target["crop_code"],
            "crop_profile_version": target["profile_version"],
            "formula_version": f"{source['prediction_key']}_{target['crop_code']}_{formula_version_suffix}",
        })
        created.append(admin_create_formula(data, actor_user_id))

    return {
        "profile_id": str(profile_id),
        "crop_code": target["crop_code"],
        "crop_profile_version": target["profile_version"],
        "source_crop_code": source_crop_code,
        "seeded": len(created),
        "skipped_existing": sorted(existing),
        "formulas": created,
    }


def admin_publish_all_formulas_for_profile(profile_id: UUID | str, actor_user_id: UUID | str) -> dict[str, Any]:
    target = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not target:
        raise FeatureEngineRepositoryError("Crop profile not found")
    drafts = _rows(
        """
        SELECT formula_id, prediction_key
        FROM crop_formula_registry
        WHERE crop_code=:c AND crop_profile_version=:v AND status='draft'
        ORDER BY execution_order;
        """,
        {"c": target["crop_code"], "v": target["profile_version"]},
    )
    published: list[str] = []
    errors: list[dict[str, Any]] = []
    for draft in drafts:
        try:
            admin_publish_formula(draft["formula_id"], actor_user_id)
            published.append(draft["prediction_key"])
        except FeatureEngineRepositoryError as exc:
            errors.append({"prediction_key": draft["prediction_key"], "error": str(exc)})
    return {
        "profile_id": str(profile_id),
        "crop_profile_version": target["profile_version"],
        "published": published,
        "published_count": len(published),
        "errors": errors,
    }


def admin_delete_profile(profile_id: UUID | str, actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not before:
        raise FeatureEngineRepositoryError("Crop profile not found")
    if before.get("status") != "draft":
        raise FeatureEngineRepositoryError(
            "Only draft crop profiles can be deleted. Published profiles are immutable — clone a new version instead."
        )
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM crop_formula_registry "
                    "WHERE crop_code=:c AND crop_profile_version=:v AND status='draft'"
                ),
                {"c": before["crop_code"], "v": before["profile_version"]},
            )
            conn.execute(
                text("DELETE FROM crop_feature_profiles WHERE profile_id=:id AND status='draft'"),
                {"id": str(profile_id)},
            )
        audit_change(actor_user_id, "crop_feature_profile", profile_id, "delete", before, None)
        return {"deleted": True, "profile_id": str(profile_id)}
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to delete crop profile: {exc}") from exc


def admin_delete_formula(formula_id: UUID | str, actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_formula_registry WHERE formula_id=:id", {"id": str(formula_id)})
    if not before:
        raise FeatureEngineRepositoryError("Formula not found")
    if before.get("status") != "draft":
        raise FeatureEngineRepositoryError("Only draft formulas can be deleted.")
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM crop_formula_registry WHERE formula_id=:id AND status='draft'"), {"id": str(formula_id)})
        audit_change(actor_user_id, "crop_formula", formula_id, "delete", before, None)
        return {"deleted": True, "formula_id": str(formula_id)}
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to delete formula: {exc}") from exc


def admin_clone_profile(profile_id: UUID | str, new_version: str, actor_user_id: UUID | str) -> dict[str, Any]:
    source = _row("SELECT * FROM crop_feature_profiles WHERE profile_id=:id", {"id": str(profile_id)})
    if not source:
        raise FeatureEngineRepositoryError("Crop profile not found")
    data = {key: source.get(key) for key in [
        "crop_code", "crop_name", "crop_type", "minimum_history_days", "preferred_history_days",
        "temporal_windows", "root_zone_weights", "soil_ranges", "normalization", "growth_config", "metadata",
    ]}
    data["profile_version"] = new_version
    return admin_create_profile(data, actor_user_id)


def admin_list_formulas(include_inactive: bool = True, crop_code: str | None = None) -> list[dict[str, Any]]:
    where: list[str] = []
    params: dict[str, Any] = {}
    if not include_inactive:
        where.append("is_active = TRUE")
    if crop_code:
        where.append("crop_code = :crop_code")
        params["crop_code"] = crop_code
    clause = "WHERE " + " AND ".join(where) if where else ""
    return _rows(
        f"SELECT * FROM crop_formula_registry {clause} ORDER BY crop_code, execution_order, created_at DESC;",
        params,
    )


def admin_create_formula(data: dict[str, Any], actor_user_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        INSERT INTO crop_formula_registry (
            crop_code, prediction_key, display_name, formula_version,
            crop_profile_version, formula_type, score_direction, execution_order,
            component_weights, thresholds, parameters, description, metadata,
            status, is_active, created_by, updated_by
        ) VALUES (
            :crop_code, :prediction_key, :display_name, :formula_version,
            :crop_profile_version, :formula_type, :score_direction, :execution_order,
            CAST(:component_weights AS jsonb), CAST(:thresholds AS jsonb),
            CAST(:parameters AS jsonb), :description, CAST(:metadata AS jsonb),
            'draft', FALSE, :actor, :actor
        ) RETURNING *;
        """
    )
    payload = dict(data)
    for key in ["component_weights", "thresholds", "parameters", "metadata"]:
        payload[key] = _json(payload.get(key))
    payload["actor"] = str(actor_user_id)
    try:
        with engine.begin() as conn:
            row = dict(conn.execute(query, payload).mappings().one())
        audit_change(actor_user_id, "crop_formula", row["formula_id"], "create", None, row)
        return row
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to create formula: {exc}") from exc


def admin_update_formula(formula_id: UUID | str, data: dict[str, Any], actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_formula_registry WHERE formula_id=:id", {"id": str(formula_id)})
    if not before:
        raise FeatureEngineRepositoryError("Formula not found")
    if before.get("status") != "draft":
        raise FeatureEngineRepositoryError("Published/archived formulas are immutable. Clone a new version before editing.")
    payload = dict(data)
    payload.update({"id": str(formula_id), "actor": str(actor_user_id)})
    for key in ["component_weights", "thresholds", "parameters", "metadata"]:
        payload[key] = _json(payload.get(key))
    query = text(
        """
        UPDATE crop_formula_registry SET
            display_name=:display_name,
            crop_profile_version=:crop_profile_version,
            formula_type=:formula_type,
            score_direction=:score_direction,
            execution_order=:execution_order,
            component_weights=CAST(:component_weights AS jsonb),
            thresholds=CAST(:thresholds AS jsonb),
            parameters=CAST(:parameters AS jsonb),
            description=:description,
            metadata=CAST(:metadata AS jsonb),
            updated_by=:actor, updated_at=now()
        WHERE formula_id=:id
        RETURNING *;
        """
    )
    try:
        with engine.begin() as conn:
            after = dict(conn.execute(query, payload).mappings().one())
        audit_change(actor_user_id, "crop_formula", formula_id, "update", before, after)
        return after
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to update formula: {exc}") from exc


def admin_publish_formula(formula_id: UUID | str, actor_user_id: UUID | str) -> dict[str, Any]:
    before = _row("SELECT * FROM crop_formula_registry WHERE formula_id=:id", {"id": str(formula_id)})
    if not before:
        raise FeatureEngineRepositoryError("Formula not found")
    if before.get("status") == "archived":
        raise FeatureEngineRepositoryError("Archived formulas cannot be published")
    weights = before.get("component_weights") or {}
    if not weights or abs(sum(float(v) for v in weights.values()) - 1.0) > 0.001:
        raise FeatureEngineRepositoryError("Formula component weights must sum to 1.0 before publishing")

    profile = _row(
        """
        SELECT profile_id, status, is_active
        FROM crop_feature_profiles
        WHERE crop_code=:crop_code AND profile_version=:profile_version
        LIMIT 1;
        """,
        {"crop_code": before["crop_code"], "profile_version": before["crop_profile_version"]},
    )
    if not profile:
        raise FeatureEngineRepositoryError(
            "The formula references a crop profile version that does not exist. Create/clone that crop profile first."
        )

    activate_now = bool(profile.get("status") == "published" and profile.get("is_active"))
    try:
        with engine.begin() as conn:
            if activate_now:
                conn.execute(
                    text(
                        """
                        UPDATE crop_formula_registry
                        SET is_active=FALSE
                        WHERE crop_code=:crop_code
                          AND prediction_key=:prediction_key
                          AND formula_id<>:id;
                        """
                    ),
                    {"crop_code": before["crop_code"], "prediction_key": before["prediction_key"], "id": str(formula_id)},
                )
            after = dict(
                conn.execute(
                    text(
                        """
                        UPDATE crop_formula_registry
                        SET status='published', is_active=:activate_now, published_at=now(),
                            updated_by=:actor, updated_at=now()
                        WHERE formula_id=:id
                        RETURNING *;
                        """
                    ),
                    {
                        "id": str(formula_id),
                        "actor": str(actor_user_id),
                        "activate_now": activate_now,
                    },
                ).mappings().one()
            )
        audit_change(actor_user_id, "crop_formula", formula_id, "publish", before, after)
        return {
            **after,
            "activation_note": (
                "Formula is active because its referenced crop profile is the active published profile."
                if activate_now
                else "Formula is published but staged/inactive. Publish its crop profile version to atomically activate all matching published formulas."
            ),
        }
    except SQLAlchemyError as exc:
        raise FeatureEngineRepositoryError(f"Failed to publish formula: {exc}") from exc


def admin_clone_formula(formula_id: UUID | str, new_version: str, actor_user_id: UUID | str) -> dict[str, Any]:
    source = _row("SELECT * FROM crop_formula_registry WHERE formula_id=:id", {"id": str(formula_id)})
    if not source:
        raise FeatureEngineRepositoryError("Formula not found")
    data = {key: source.get(key) for key in [
        "crop_code", "prediction_key", "display_name", "crop_profile_version", "formula_type",
        "score_direction", "execution_order", "component_weights", "thresholds", "parameters", "description", "metadata",
    ]}
    data["formula_version"] = new_version
    return admin_create_formula(data, actor_user_id)


def admin_clone_crop(
    source_crop_code: str,
    *,
    target_crop_code: str,
    target_crop_name: str,
    target_profile_version: str,
    formula_version_suffix: str,
    actor_user_id: UUID | str,
) -> dict[str, Any]:
    source_profile = get_active_crop_profile(source_crop_code)
    if not source_profile:
        raise FeatureEngineRepositoryError(f"Active source crop profile not found: {source_crop_code}")
    profile_data = {key: source_profile.get(key) for key in [
        "crop_type", "minimum_history_days", "preferred_history_days", "temporal_windows",
        "root_zone_weights", "soil_ranges", "normalization", "growth_config", "metadata",
    ]}
    profile_data.update({
        "crop_code": target_crop_code,
        "crop_name": target_crop_name,
        "profile_version": target_profile_version,
    })
    profile = admin_create_profile(profile_data, actor_user_id)

    formulas = []
    for source in get_active_formulas(source_crop_code):
        formula_data = {key: source.get(key) for key in [
            "prediction_key", "display_name", "formula_type", "score_direction", "execution_order",
            "component_weights", "thresholds", "parameters", "description", "metadata",
        ]}
        formula_data.update({
            "crop_code": target_crop_code,
            "crop_profile_version": target_profile_version,
            "formula_version": f"{source['prediction_key']}_{target_crop_code}_{formula_version_suffix}",
        })
        formulas.append(admin_create_formula(formula_data, actor_user_id))
    return {"profile": profile, "formulas": formulas}


def audit_change(
    actor_user_id: UUID | str,
    entity_type: str,
    entity_id: UUID | str | None,
    action: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    def safe(value):
        if value is None:
            return None
        normalized = {}
        for key, item in value.items():
            if isinstance(item, (date, datetime)):
                normalized[key] = item.isoformat()
            elif isinstance(item, UUID):
                normalized[key] = str(item)
            else:
                normalized[key] = item
        return normalized
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO crop_configuration_audit
                    (actor_user_id, entity_type, entity_id, action, before_state, after_state)
                    VALUES (:actor, :entity_type, :entity_id, :action,
                            CAST(:before AS jsonb), CAST(:after AS jsonb));
                    """
                ),
                {
                    "actor": str(actor_user_id),
                    "entity_type": entity_type,
                    "entity_id": str(entity_id) if entity_id else None,
                    "action": action,
                    "before": json.dumps(safe(before)) if before is not None else None,
                    "after": json.dumps(safe(after)) if after is not None else None,
                },
            )
    except SQLAlchemyError:
        # Audit failure should not silently rollback an already committed config change.
        pass
