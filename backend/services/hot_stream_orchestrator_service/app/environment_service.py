from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from services.hot_stream_orchestrator_service.app.environment_clients import (
    process_environment_dataset,
    search_catalog_dataset,
    write_environment_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.environment_schemas import (
    DEFAULT_ENVIRONMENT_DATASETS,
    EnvironmentRefreshRequest,
)
from services.hot_stream_orchestrator_service.app.environment_cache import (
    STATIC_TABLES,
    expected_static_rows,
    static_dataset_is_cached,
)
from services.hot_stream_orchestrator_service.app.clients import (
    run_raster_preview_for_scene,
    write_sentinel2_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.repository import (
    complete_pipeline_job,
    create_pipeline_job,
    fail_pipeline_job,
    update_pipeline_job_stage,
)
from services.hot_stream_orchestrator_service.app.service import (
    _full_farm_bbox,
    _normalize_polygon,
    _static_h3_cells,
    ensure_farm_analysis_ready,
)


class EnvironmentRefreshError(RuntimeError):
    code = "ENVIRONMENT_DATASETS_FAILED"


def materialize_environment(
    farm_id: UUID,
    payload: EnvironmentRefreshRequest,
    progress_callback: Callable[[list[dict[str, Any]], str | None], None] | None = None,
) -> dict[str, Any]:
    if not payload.dataset_keys:
        raise EnvironmentRefreshError("At least one environmental dataset is required.")
    unknown = sorted(set(payload.dataset_keys) - set(DEFAULT_ENVIRONMENT_DATASETS))
    if unknown:
        raise EnvironmentRefreshError(
            "Unregistered environmental dataset(s): " + ", ".join(unknown)
        )

    job = create_pipeline_job(
        farm_id=farm_id,
        job_type="environment_refresh",
        metadata={"datasets": payload.dataset_keys},
    )
    job_id = job["job_id"]
    stage_results: list[dict[str, Any]] = []

    try:
        update_pipeline_job_stage(job_id, "environment_ensure_farm", status="running")
        repair = ensure_farm_analysis_ready(farm_id)
        farm = repair["farm"]
        bbox = _full_farm_bbox(farm)
        polygon = _normalize_polygon(farm.get("polygon_geojson"))
        h3_cells = _static_h3_cells(farm)
        h3_resolution = int(farm.get("h3_resolution") or 12)
        if polygon is None:
            raise EnvironmentRefreshError("Farm polygon is missing or invalid")
        update_pipeline_job_stage(job_id, "environment_ensure_farm", status="succeeded")

        for dataset_key in payload.dataset_keys:
            stage_name = f"environment:{dataset_key}"
            current: dict[str, Any] = {
                "dataset_key": dataset_key,
                "status": "running",
                "source_items_found": 0,
                "source_items_processed": 0,
                "postgres_rows_written": 0,
                "parquet_rows_written": 0,
            }
            update_pipeline_job_stage(
                job_id,
                stage_name,
                status="running",
                metadata={"completed_datasets": stage_results, "current_dataset": dataset_key},
            )
            if progress_callback:
                progress_callback(stage_results, dataset_key)
            try:
                dataset_options = payload.dataset_options.get(dataset_key) or {}
                if dataset_key in STATIC_TABLES and not payload.force_refresh:
                    expected_rows = expected_static_rows(dataset_key, len(h3_cells), dataset_options)
                    if static_dataset_is_cached(farm_id, dataset_key, expected_rows):
                        current["status"] = "cached"
                        current["message"] = f"Static dataset already materialized ({expected_rows} expected rows)."
                        stage_results.append(current)
                        continue

                search = search_catalog_dataset(
                    dataset_key=dataset_key,
                    bbox=bbox,
                    start_date=payload.start_date,
                    end_date=payload.end_date,
                    limit=max(payload.max_items_per_dataset, 1),
                    max_cloud_cover=payload.max_cloud_cover,
                )
                items = search.get("items") or []
                current["provider"] = search.get("provider")
                current["source_items_found"] = len(items)
                if not items:
                    current["status"] = "unavailable"
                    current["message"] = "; ".join(search.get("errors") or []) or "No source item found"
                    stage_results.append(current)
                    continue

                # Scene/composite/subdaily sources can return several items. Static and
                # virtual sources normally return one. The request controls max items.
                for source_item in items[: payload.max_items_per_dataset]:
                    if dataset_key == "sentinel_2_l2a":
                        # Sentinel-2 uses the protected raster contract because
                        # its complete optical-index response has a stricter
                        # schema than generic environmental processors. It is
                        # still part of this same environmental dataset stage.
                        processed = run_raster_preview_for_scene(
                            farm_id=farm_id,
                            bbox=bbox,
                            scene=source_item,
                            h3_resolution=h3_resolution,
                            h3_cells_bigint=h3_cells,
                            farm_polygon_geojson=polygon,
                        )
                        returned_h3 = {
                            int(row["h3_index"])
                            for row in (processed.get("features") or [])
                            if row.get("h3_index") is not None
                        }
                        expected_h3 = {int(value) for value in h3_cells}
                        if returned_h3 != expected_h3:
                            raise EnvironmentRefreshError(
                                "Sentinel-2 did not produce exactly one observation for every registered H3 cell."
                            )
                        written = write_sentinel2_to_lakehouse(farm_id, processed)
                    else:
                        processed = process_environment_dataset(
                            dataset_key=dataset_key,
                            farm_id=farm_id,
                            bbox=bbox,
                            farm_polygon_geojson=polygon,
                            h3_resolution=h3_resolution,
                            h3_cells_bigint=h3_cells,
                            source_item=source_item,
                            options=dataset_options,
                        )
                        written = write_environment_to_lakehouse(
                            farm_id=farm_id,
                            process_result=processed,
                        )
                    current["source_items_processed"] += 1
                    current["postgres_rows_written"] += int(written.get("postgres_rows_written") or 0)
                    current["parquet_rows_written"] += int(written.get("parquet_rows_written") or 0)

                current["status"] = "succeeded"
            except Exception as exc:
                # Isolate a dataset failure. Every sibling dataset must still
                # be attempted so the feature engine can use all observations
                # that were successfully produced.
                current["status"] = "failed"
                current["message"] = str(exc)
            stage_results.append(current)
            update_pipeline_job_stage(
                job_id,
                stage_name,
                status="running",
                metadata={"completed_datasets": stage_results},
            )
            if progress_callback:
                progress_callback(stage_results, None)

        failures = [row for row in stage_results if row["status"] in {"failed", "unavailable"}]
        successes = [row for row in stage_results if row["status"] in {"succeeded", "cached"}]
        if not failures:
            overall = "succeeded"
        elif successes:
            overall = "completed_with_warnings"
        else:
            overall = "failed"

        if overall == "failed":
            raise EnvironmentRefreshError(
                "Required environmental dataset processing failed: "
                + ", ".join(row["dataset_key"] for row in failures)
            )
        complete_pipeline_job(job_id, metadata={"overall_status": overall, "datasets": stage_results})
        return {"farm_id": str(farm_id), "status": overall, "datasets": stage_results}
    except Exception as exc:
        try:
            fail_pipeline_job(
                job_id,
                error_code="ENVIRONMENT_REFRESH_ERROR",
                error_message=str(exc),
                metadata={"datasets": stage_results},
            )
        except Exception:
            pass
        raise
