from __future__ import annotations

from typing import Any
from uuid import UUID

from services.hot_stream_orchestrator_service.app.environment_clients import (
    process_environment_dataset,
    search_catalog_dataset,
    write_environment_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.environment_schemas import (
    EnvironmentRefreshRequest,
)
from services.hot_stream_orchestrator_service.app.environment_cache import (
    STATIC_TABLES,
    expected_static_rows,
    static_dataset_is_cached,
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
    pass


def materialize_environment(
    farm_id: UUID,
    payload: EnvironmentRefreshRequest,
) -> dict[str, Any]:
    if "sentinel_2_l2a" in payload.dataset_keys:
        raise EnvironmentRefreshError(
            "sentinel_2_l2a is intentionally excluded from environment-refresh; use the existing full-refresh endpoint for Sentinel-2"
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
                # Multi-source enrichment is intentionally fault isolated: one optional
                # source must not invalidate all other source observations.
                current["status"] = "failed"
                current["message"] = str(exc)
            stage_results.append(current)
            update_pipeline_job_stage(
                job_id,
                stage_name,
                status="running",
                metadata={"completed_datasets": stage_results},
            )

        failures = [row for row in stage_results if row["status"] == "failed"]
        successes = [row for row in stage_results if row["status"] == "succeeded"]
        overall = "succeeded" if not failures else ("partial" if successes else "failed")
        if overall == "failed":
            fail_pipeline_job(
                job_id,
                error_code="ALL_ENVIRONMENT_DATASETS_FAILED",
                error_message="All requested environment datasets failed",
                metadata={"datasets": stage_results},
            )
        else:
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
