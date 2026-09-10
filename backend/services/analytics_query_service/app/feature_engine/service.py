from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from services.analytics_query_service.app.feature_engine.builder import (
    FEATURE_VERSION,
    build_feature_rows,
)
from services.analytics_query_service.app.feature_engine.component_catalog import SOURCE_REQUIREMENTS
from services.analytics_query_service.app.feature_engine.formula_engine import (
    aggregate_farm_predictions,
    calculate_h3_predictions,
    project_h3_predictions_to_grid,
)
from services.analytics_query_service.app.feature_engine import repository


class FeatureEngineError(RuntimeError):
    def __init__(self, message: str, code: str = "FEATURE_ENGINE_ERROR", status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _farm_and_profile(farm_id: UUID | str) -> tuple[dict[str, Any], dict[str, Any]]:
    farm = repository.get_farm_context(farm_id)
    if not farm:
        raise FeatureEngineError("Farm not found", "FARM_NOT_FOUND", 404)
    crop_code = str(farm.get("crop_code") or "").strip().lower()
    if not crop_code:
        raise FeatureEngineError(
            "This farm has no crop_code. Set the farm crop before running crop-specific feature processing.",
            "FARM_CROP_REQUIRED",
            409,
        )
    profile = repository.get_active_crop_profile(crop_code)
    if not profile:
        raise FeatureEngineError(
            f"No active published feature profile exists for crop '{crop_code}'.",
            "CROP_PROFILE_NOT_FOUND",
            409,
        )
    return farm, profile


def materialize_features(
    farm_id: UUID | str,
    *,
    start_date: date,
    end_date: date,
    latest_only: bool = False,
    force_refresh: bool = False,
) -> dict[str, Any]:
    farm, profile = _farm_and_profile(farm_id)
    preferred = int(profile.get("preferred_history_days") or 180)
    history_start = start_date - timedelta(days=preferred)

    job = repository.create_pipeline_job(
        farm_id,
        "feature_processing",
        {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "history_start": history_start.isoformat(),
            "latest_only": latest_only,
            "force_refresh": force_refresh,
            "crop_code": farm["crop_code"],
        },
    )
    job_id = job["job_id"]
    try:
        repository.update_pipeline_job(job_id, stage="load_observations")
        bundle = repository.get_source_bundle(farm_id, history_start=history_start, end_date=end_date)
        repository.update_pipeline_job(
            job_id,
            stage="engineer_features",
            metadata={"source_row_counts": {key: len(value) for key, value in bundle.items()}},
        )
        rows = build_feature_rows(
            farm=farm,
            profile=profile,
            bundle=bundle,
            start_date=start_date,
            end_date=end_date,
            latest_only=latest_only,
        )
        if not rows:
            raise FeatureEngineError(
                "No usable H3 environmental observations were found in the requested period. Process at least one H3-compatible environmental dataset first.",
                "FEATURE_ANCHOR_DATA_MISSING",
                409,
            )
        repository.update_pipeline_job(job_id, stage="persist_features", metadata={"rows": len(rows)})
        written = repository.upsert_engineered_features(rows)
        latest_date = max(row["feature_date"] for row in rows)
        source_availability = {}
        for key in bundle:
            source_availability[key] = bool(bundle[key])
        repository.finish_pipeline_job(
            job_id,
            succeeded=True,
            metadata={"rows_written": written, "latest_feature_date": latest_date.isoformat()},
        )
        return {
            "farm_id": str(farm_id),
            "crop_code": farm["crop_code"],
            "crop_profile_version": profile["profile_version"],
            "feature_version": FEATURE_VERSION,
            "history_start": history_start,
            "requested_start_date": start_date,
            "requested_end_date": end_date,
            "latest_feature_date": latest_date,
            "h3_rows_written": written,
            "anchor_observation_dates": len({row["feature_date"] for row in rows}),
            "h3_cells": len({row["h3_index"] for row in rows}),
            "source_availability": source_availability,
            "pipeline_job_id": job_id,
            "status": "succeeded",
        }
    except Exception as exc:
        try:
            repository.finish_pipeline_job(job_id, succeeded=False, error=str(exc))
        except Exception:
            pass
        raise


def materialize_calculations(
    farm_id: UUID | str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    latest_only: bool = False,
) -> dict[str, Any]:
    farm, profile = _farm_and_profile(farm_id)
    formulas = repository.get_active_formulas(farm["crop_code"], profile["profile_version"])
    if not formulas:
        raise FeatureEngineError(
            f"No active formulas exist for crop '{farm['crop_code']}'.",
            "FORMULAS_NOT_FOUND",
            409,
        )
    job = repository.create_pipeline_job(
        farm_id,
        "crop_formula_processing",
        {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "latest_only": latest_only,
            "crop_code": farm["crop_code"],
        },
    )
    job_id = job["job_id"]
    try:
        repository.update_pipeline_job(job_id, stage="load_engineered_features")
        features = repository.get_engineered_features(
            farm_id,
            start_date=start_date,
            end_date=end_date,
            latest_only=latest_only,
        )
        if not features:
            raise FeatureEngineError(
                "No engineered feature rows exist for the requested farm/date range. Run feature materialization first.",
                "ENGINEERED_FEATURES_MISSING",
                409,
            )
        repository.update_pipeline_job(job_id, stage="calculate_h3", metadata={"feature_rows": len(features)})
        h3_rows = calculate_h3_predictions(feature_rows=features, formulas=formulas, profile=profile)
        h3_written = repository.upsert_prediction_rows(h3_rows)

        repository.update_pipeline_job(job_id, stage="aggregate_farm")
        farm_rows = aggregate_farm_predictions(h3_rows=h3_rows, formulas=formulas)
        farm_written = repository.upsert_prediction_rows(farm_rows)

        repository.update_pipeline_job(job_id, stage="project_display_grid")
        crosswalk = repository.get_grid_crosswalk(farm_id)
        grid_rows = project_h3_predictions_to_grid(h3_rows=h3_rows, crosswalk=crosswalk, formulas=formulas)
        grid_written = repository.upsert_grid_prediction_rows(grid_rows)

        latest_date = max(row["result_date"] for row in h3_rows)
        repository.finish_pipeline_job(
            job_id,
            succeeded=True,
            metadata={
                "h3_predictions_written": h3_written,
                "farm_predictions_written": farm_written,
                "grid_values_written": grid_written,
                "latest_result_date": latest_date.isoformat(),
            },
        )
        return {
            "farm_id": str(farm_id),
            "crop_code": farm["crop_code"],
            "crop_profile_version": profile["profile_version"],
            "feature_version": features[0]["feature_version"],
            "formula_count": len(formulas),
            "h3_predictions_written": h3_written,
            "farm_predictions_written": farm_written,
            "grid_values_written": grid_written,
            "latest_result_date": latest_date,
            "pipeline_job_id": job_id,
            "status": "succeeded",
            "grid_semantics": "Grid scores are overlap-weighted projections of H3 formula results for visualization; they are not independent 10 m physical measurements.",
        }
    except Exception as exc:
        try:
            repository.finish_pipeline_job(job_id, succeeded=False, error=str(exc))
        except Exception:
            pass
        raise


def materialize_intelligence(
    farm_id: UUID | str,
    *,
    start_date: date,
    end_date: date,
    latest_only: bool = False,
    force_refresh: bool = False,
) -> dict[str, Any]:
    feature_result = materialize_features(
        farm_id,
        start_date=start_date,
        end_date=end_date,
        latest_only=latest_only,
        force_refresh=force_refresh,
    )
    calculation_result = materialize_calculations(
        farm_id,
        start_date=start_date,
        end_date=end_date,
        latest_only=latest_only,
    )
    return {
        "farm_id": str(farm_id),
        "status": "succeeded",
        "feature_processing": feature_result,
        "calculation_processing": calculation_result,
    }


def validate_formula_components(component_weights: dict[str, Any]) -> None:
    known = {row["component_key"] for row in repository.get_component_catalog()}
    for key in component_weights:
        if key.startswith("prediction:") or key.startswith("prediction_inverse:"):
            continue
        if key not in known and key not in SOURCE_REQUIREMENTS:
            raise FeatureEngineError(f"Unknown/non-approved component: {key}", "INVALID_FORMULA_COMPONENT", 422)
