from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class ObservabilityRepositoryError(RuntimeError):
    pass


def _is_undefined_table(exc: SQLAlchemyError) -> bool:
    pgcode = getattr(getattr(exc, "orig", None), "pgcode", None)
    if pgcode == "42P01":
        return True
    message = str(exc).lower()
    return "does not exist" in message and ("relation" in message or "table" in message)


SOURCE_TABLES = {
    "sentinel_2_l2a": ("h3_sentinel2_features", "snapshot_date"),
    "sentinel_1_rtc": ("h3_sentinel1_features", "snapshot_date"),
    "landsat_c2_l2": ("h3_landsat_features", "snapshot_date"),
    "gpm_imerg": ("farm_weather_observations", "observation_date"),
    "cop_dem_glo30": ("h3_terrain_features", "created_at"),
    "esa_worldcover": ("h3_landcover_features", "created_at"),
    "jrc_surface_water": ("h3_surface_water_features", "created_at"),
    "era5_land": ("farm_reanalysis_daily", "observation_date"),
    "soilgrids_v2": ("h3_soilgrids_features", "created_at"),
    "smap_l4_sm": ("farm_smap_observations", "observed_at"),
    "modis_et": ("farm_modis_et_observations", "period_end"),
    "modis_lai_fpar": ("farm_modis_vegetation_observations", "period_end"),
    "weather_forecast": ("farm_weather_forecasts", "valid_at"),
}


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        if _is_undefined_table(exc):
            return []
        raise ObservabilityRepositoryError(str(exc)) from exc


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = _rows(sql, params)
    return rows[0] if rows else {}


def feature_processing_summary() -> dict[str, Any]:
    return _row(
        """
        SELECT
          (SELECT COUNT(*) FROM pipeline_jobs
             WHERE service_name IN ('analytics_query_service','hot_stream_orchestrator_service')
               AND job_type IN ('feature_processing','crop_formula_processing','sentinel2_history_backfill')
               AND started_at >= now() - interval '24 hours')::integer AS jobs_24h,
          (SELECT COUNT(*) FROM pipeline_jobs
             WHERE job_type IN ('feature_processing','crop_formula_processing','sentinel2_history_backfill')
               AND status='running')::integer AS jobs_running,
          (SELECT COUNT(*) FROM pipeline_jobs
             WHERE job_type IN ('feature_processing','crop_formula_processing','sentinel2_history_backfill')
               AND status='succeeded' AND started_at >= now() - interval '24 hours')::integer AS jobs_succeeded_24h,
          (SELECT COUNT(*) FROM pipeline_jobs
             WHERE job_type IN ('feature_processing','crop_formula_processing','sentinel2_history_backfill')
               AND status='failed' AND started_at >= now() - interval '24 hours')::integer AS jobs_failed_24h,
          (SELECT COUNT(*) FROM farm_h3_engineered_features)::bigint AS engineered_feature_rows,
          (SELECT COUNT(*) FROM farm_calculated_predictions)::bigint AS calculated_prediction_rows,
          (SELECT COUNT(*) FROM farm_grid_calculated_values)::bigint AS grid_calculation_rows,
          (SELECT COUNT(DISTINCT farm_id) FROM farm_h3_engineered_features)::integer AS farms_with_features,
          (SELECT COUNT(*) FROM crop_feature_profiles WHERE is_active=TRUE AND status='published')::integer AS active_crop_profiles,
          (SELECT COUNT(*) FROM crop_formula_registry WHERE is_active=TRUE AND status='published')::integer AS active_formulas,
          (SELECT MAX(updated_at) FROM farm_h3_engineered_features) AS latest_feature_processing_at,
          (SELECT MAX(updated_at) FROM farm_calculated_predictions) AS latest_calculation_at;
        """
    )


def processing_runs(limit: int = 100) -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT job_id, farm_id, service_name, job_type, status, current_stage,
               error_code, error_message, started_at, finished_at, updated_at, metadata
        FROM pipeline_jobs
        WHERE job_type IN (
          'feature_processing','crop_formula_processing','sentinel2_history_backfill',
          'environment_refresh','farm_analysis_materialize'
        )
        ORDER BY COALESCE(updated_at, started_at) DESC
        LIMIT :limit;
        """,
        {"limit": limit},
    )


def source_status() -> list[dict[str, Any]]:
    output = []
    for dataset_key, (table, time_col) in SOURCE_TABLES.items():
        # table names are server-side constants only; no user input enters SQL identifiers.
        row = _row(
            f"""
            SELECT COUNT(*)::bigint AS row_count,
                   COUNT(DISTINCT farm_id)::integer AS farm_count,
                   MAX({time_col}) AS latest_observation
            FROM {table};
            """
        )
        output.append({"dataset_key": dataset_key, "table": table, **row})
    return output


def formula_status() -> dict[str, Any]:
    profiles = _rows(
        """
        SELECT crop_code, crop_name, profile_version, crop_type,
               minimum_history_days, preferred_history_days, temporal_windows,
               status, is_active, published_at
        FROM crop_feature_profiles
        ORDER BY crop_code, created_at DESC;
        """
    )
    formulas = _rows(
        """
        SELECT crop_code, prediction_key, display_name, formula_version,
               crop_profile_version, score_direction, execution_order,
               component_weights, thresholds, parameters, status, is_active, published_at
        FROM crop_formula_registry
        ORDER BY crop_code, execution_order, created_at DESC;
        """
    )
    return {"profiles": profiles, "formulas": formulas}


def farm_feature_status(farm_id: UUID | str) -> dict[str, Any]:
    farm = _row(
        """
        SELECT farm_id, farmer_id, fpo_id, farm_name, crop_code, crop_name,
               crop_variety, crop_stage, planting_date, h3_cell_count, area_acres
        FROM farms WHERE farm_id=:farm_id LIMIT 1;
        """,
        {"farm_id": str(farm_id)},
    )
    if not farm:
        return {}
    features = _row(
        """
        SELECT COUNT(*)::bigint AS feature_rows,
               COUNT(DISTINCT h3_index)::integer AS h3_cells_with_features,
               MIN(feature_date) AS first_feature_date,
               MAX(feature_date) AS latest_feature_date,
               AVG(confidence) AS average_feature_confidence
        FROM farm_h3_engineered_features WHERE farm_id=:farm_id;
        """,
        {"farm_id": str(farm_id)},
    )
    predictions = _rows(
        """
        SELECT result_scope, prediction_key, MAX(result_date) AS latest_result_date,
               COUNT(*)::integer AS row_count, AVG(confidence) AS average_confidence
        FROM farm_calculated_predictions
        WHERE farm_id=:farm_id
        GROUP BY result_scope, prediction_key
        ORDER BY result_scope, prediction_key;
        """,
        {"farm_id": str(farm_id)},
    )
    source_counts = []
    for dataset_key, (table, time_col) in SOURCE_TABLES.items():
        row = _row(
            f"SELECT COUNT(*)::bigint AS row_count, MAX({time_col}) AS latest_observation FROM {table} WHERE farm_id=:farm_id;",
            {"farm_id": str(farm_id)},
        )
        source_counts.append({"dataset_key": dataset_key, **row})
    return {"farm": farm, "features": features, "predictions": predictions, "sources": source_counts}
