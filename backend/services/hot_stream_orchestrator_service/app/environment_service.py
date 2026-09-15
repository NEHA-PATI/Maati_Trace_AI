from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable
from uuid import UUID

from shared.config.settings import settings
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


SENTINEL2_CANDIDATE_LIMIT = 5


def _has_usable_records(dataset_key: str, records: list[dict[str, Any]]) -> bool:
    """Return false when a source produced rows but no usable observations."""
    if not records:
        # Keep the existing processing contract for non-optical datasets and
        # test doubles. Raster processors that return no rows are still
        # validated by their own processors; this guard is specifically for
        # optical scenes that commonly contain only cloud/nodata pixels.
        return dataset_key != "sentinel_2_l2a"
    if dataset_key not in {"sentinel_2_l2a", "landsat_c2_l2", "sentinel_1_rtc"}:
        return True
    quality_fields = {
        "valid_fraction",
        "valid_pixel_count",
        "pixel_count",
        "cloud_pixel_count",
    }
    if not any(quality_fields.intersection(row) for row in records):
        return True
    return any(
        float(row.get("valid_fraction") or 0) > 0
        and any(
            row.get(field) is not None
            for field in (
                "ndvi",
                "ndmi",
                "mean_vv",
                "mean_vh",
                "surface_temp_c",
            )
        )
        for row in records
    )


def _search_unavailable_reason(errors: list[str]) -> tuple[str, str]:
    message = " ".join(errors).lower()
    if any(token in message for token in ("rate limit", "too many requests", "429")):
        return "provider_unavailable", "SOURCE_RATE_LIMITED"
    if any(token in message for token in ("failed to open", "connection", "timed out", "timeout", "dns")):
        return "provider_unavailable", "SOURCE_PROVIDER_ERROR"
    return "data_unavailable", "NO_SOURCE_ITEM"


def _source_item_label(source_item: dict[str, Any]) -> str:
    return str(
        source_item.get("id")
        or source_item.get("scene_id")
        or source_item.get("source_item_id")
        or source_item.get("datetime")
        or "unknown-scene"
    )


def _process_dataset(
    *,
    farm_id: UUID,
    dataset_key: str,
    payload: EnvironmentRefreshRequest,
    bbox: Any,
    polygon: dict[str, Any],
    h3_cells: list[int],
    h3_resolution: int,
) -> dict[str, Any]:
    """Process one environmental source.

    Dataset clients are synchronous and mostly I/O-bound, so this function is
    executed in a bounded thread pool by ``materialize_environment``.
    """
    current: dict[str, Any] = {
        "dataset_key": dataset_key,
        "status": "running",
        "reason_type": None,
        "reason_code": None,
        "source_items_found": 0,
        "source_items_processed": 0,
        "postgres_rows_written": 0,
        "parquet_rows_written": 0,
    }
    try:
        dataset_options = payload.dataset_options.get(dataset_key) or {}
        if dataset_key in STATIC_TABLES and not payload.force_refresh:
            expected_rows = expected_static_rows(dataset_key, len(h3_cells), dataset_options)
            if static_dataset_is_cached(farm_id, dataset_key, expected_rows):
                current.update({
                    "status": "cached",
                    "reason_type": "cached",
                    "reason_code": "STATIC_DATASET_CACHED",
                    "message": f"Static dataset already materialized ({expected_rows} expected rows).",
                })
                return current

        candidate_limit = (
            SENTINEL2_CANDIDATE_LIMIT
            if dataset_key == "sentinel_2_l2a"
            else max(payload.max_items_per_dataset, 1)
        )
        search = search_catalog_dataset(
            dataset_key=dataset_key,
            bbox=bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            limit=candidate_limit,
            max_cloud_cover=payload.max_cloud_cover,
        )
        items = search.get("items") or []
        current["provider"] = search.get("provider")
        current["source_items_found"] = len(items)
        if not items:
            reason_type, reason_code = _search_unavailable_reason(search.get("errors") or [])
            current.update({
                "status": "unavailable",
                "reason_type": reason_type,
                "reason_code": reason_code,
                "message": "; ".join(search.get("errors") or []) or "No source item found for the requested location/date range.",
            })
            return current

        sentinel2_rejections: list[str] = []
        sentinel2_accepted = False

        for source_item in items[:candidate_limit]:
            if dataset_key == "sentinel_2_l2a":
                label = _source_item_label(source_item)
                try:
                    processed = run_raster_preview_for_scene(
                        farm_id=farm_id,
                        bbox=bbox,
                        scene=source_item,
                        h3_resolution=h3_resolution,
                        h3_cells_bigint=h3_cells,
                        farm_polygon_geojson=polygon,
                    )
                    current["source_items_processed"] += 1
                except Exception as exc:
                    sentinel2_rejections.append(f"{label}: processing failed: {exc}")
                    continue

                returned_h3 = {
                    int(row["h3_index"])
                    for row in (processed.get("features") or [])
                    if row.get("h3_index") is not None
                }
                expected_h3 = {int(value) for value in h3_cells}
                if returned_h3 != expected_h3:
                    sentinel2_rejections.append(
                        f"{label}: H3 coverage mismatch ({len(returned_h3)}/{len(expected_h3)} cells)"
                    )
                    continue
                features = processed.get("features") or []
                if not _has_usable_records(dataset_key, features):
                    sentinel2_rejections.append(
                        f"{label}: no valid pixels after cloud/nodata masking"
                    )
                    continue
                written = write_sentinel2_to_lakehouse(farm_id, processed)
                sentinel2_accepted = True
                current["accepted_source_item"] = label
                current["candidate_rejections"] = sentinel2_rejections
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
                if not _has_usable_records(dataset_key, processed.get("records") or []):
                    current.update({
                        "status": "unavailable",
                        "reason_type": "data_unavailable",
                        "reason_code": "NO_VALID_PIXELS",
                        "message": "Scene found, but no valid pixels remained after cloud/nodata masking.",
                    })
                    return current
                written = write_environment_to_lakehouse(
                    farm_id=farm_id,
                    process_result=processed,
                )
                current["source_items_processed"] += 1
            current["postgres_rows_written"] += int(written.get("postgres_rows_written") or 0)
            current["parquet_rows_written"] += int(written.get("parquet_rows_written") or 0)
            if dataset_key == "sentinel_2_l2a" and sentinel2_accepted:
                break

        if dataset_key == "sentinel_2_l2a" and not sentinel2_accepted:
            message = "No Sentinel-2 candidate scene produced valid pixels."
            if sentinel2_rejections:
                message += " Tried: " + " | ".join(sentinel2_rejections)
            current.update({
                "status": "unavailable",
                "reason_type": "data_unavailable",
                "reason_code": "NO_VALID_PIXELS",
                "message": message,
                "candidate_rejections": sentinel2_rejections,
            })
            return current

        current.update({
            "status": "succeeded",
            "reason_type": "data_available",
            "reason_code": "SOURCE_PROCESSED",
        })
    except Exception as exc:
        current.update({
            "status": "failed",
            "reason_type": "processing_failed",
            "reason_code": "DATASET_PROCESSING_ERROR",
            "message": str(exc),
        })
    return current


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

        # Source calls are synchronous I/O, so run independent datasets in a
        # bounded pool. Keep the limit configurable to protect provider APIs
        # and the database from an unbounded fan-out.
        configured_workers = max(1, int(settings.environment_pipeline_max_workers))
        max_workers = max(1, min(configured_workers, len(payload.dataset_keys)))
        running = [
            {"dataset_key": key, "status": "running", "reason_type": None, "reason_code": None}
            for key in payload.dataset_keys
        ]
        update_pipeline_job_stage(
            job_id,
            "environment_datasets",
            status="running",
            metadata={"completed_datasets": [], "running_datasets": running, "max_workers": max_workers},
        )
        if progress_callback:
            progress_callback([], "parallel")

        futures = {}
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="env-dataset") as executor:
            for dataset_key in payload.dataset_keys:
                futures[executor.submit(
                    _process_dataset,
                    farm_id=farm_id,
                    dataset_key=dataset_key,
                    payload=payload,
                    bbox=bbox,
                    polygon=polygon,
                    h3_cells=h3_cells,
                    h3_resolution=h3_resolution,
                )] = dataset_key

            for future in as_completed(futures):
                result = future.result()
                stage_results.append(result)
                stage_results.sort(key=lambda row: payload.dataset_keys.index(row["dataset_key"]))
                update_pipeline_job_stage(
                    job_id,
                    f"environment:{result['dataset_key']}",
                    status="succeeded" if result["status"] in {"succeeded", "cached", "unavailable"} else "failed",
                    metadata=result,
                )
                update_pipeline_job_stage(
                    job_id,
                    "environment_datasets",
                    status="running",
                    metadata={
                        "completed_datasets": stage_results,
                        "running_datasets": [
                            {"dataset_key": key, "status": "running"}
                            for key in payload.dataset_keys
                            if key not in {row["dataset_key"] for row in stage_results}
                        ],
                        "max_workers": max_workers,
                    },
                )
                if progress_callback:
                    progress_callback(stage_results, result["dataset_key"])

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
