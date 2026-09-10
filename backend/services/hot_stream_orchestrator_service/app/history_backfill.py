from __future__ import annotations

from typing import Any
from uuid import UUID

from services.hot_stream_orchestrator_service.app.clients import (
    run_raster_preview_for_scene,
    search_sentinel2_scene_candidates,
    write_sentinel2_to_lakehouse,
)
from services.hot_stream_orchestrator_service.app.repository import (
    complete_pipeline_job,
    create_pipeline_job,
    fail_pipeline_job,
    get_existing_scene_analysis_summary,
    update_pipeline_job_stage,
)
from services.hot_stream_orchestrator_service.app.schemas import Sentinel2HistoryBackfillRequest
from services.hot_stream_orchestrator_service.app.service import (
    HotStreamOrchestratorError,
    _full_farm_bbox,
    _normalize_polygon,
    _snapshot_date_from_scene,
    _static_h3_cells,
    ensure_farm_analysis_ready,
)


def backfill_sentinel2_history(farm_id: UUID, payload: Sentinel2HistoryBackfillRequest) -> dict[str, Any]:
    job = create_pipeline_job(
        farm_id,
        "sentinel2_history_backfill",
        {
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "max_cloud_cover": payload.max_cloud_cover,
            "max_scenes": payload.max_scenes,
            "provider": payload.provider,
            "collection_id": payload.collection_id,
        },
    )
    job_id = job["job_id"]
    statuses: list[dict[str, Any]] = []
    try:
        update_pipeline_job_stage(job_id, "ensure_farm_ready", status="running")
        repair = ensure_farm_analysis_ready(farm_id)
        farm = repair["farm"]
        bbox = _full_farm_bbox(farm)
        h3_cells = _static_h3_cells(farm)
        polygon = _normalize_polygon(farm.get("polygon_geojson"))
        if not h3_cells or polygon is None:
            raise HotStreamOrchestratorError(
                "Farm H3 cells/polygon are unavailable for history processing.",
                code="FARM_SPATIAL_CONTEXT_MISSING",
                status_code=422,
            )
        update_pipeline_job_stage(job_id, "search_history", status="running")
        scenes = search_sentinel2_scene_candidates(
            provider=payload.provider,
            collection_id=payload.collection_id,
            bbox=bbox,
            start_date=payload.start_date,
            end_date=payload.end_date,
            max_cloud_cover=payload.max_cloud_cover,
            limit=payload.max_scenes,
        )
        # Oldest first gives a predictable historical build order.
        scenes = sorted(scenes, key=lambda scene: str(scene.get("datetime") or ""))[: payload.max_scenes]
        update_pipeline_job_stage(job_id, "search_history", status="succeeded", metadata={"scene_count": len(scenes)})
        if not scenes:
            raise HotStreamOrchestratorError(
                "No Sentinel-2 scenes found for the requested history window.",
                code="S2_HISTORY_NO_SCENES",
                status_code=404,
            )

        processed = 0
        cached = 0
        failed = 0
        for index, scene in enumerate(scenes, start=1):
            scene_id = scene.get("scene_id")
            snapshot_date = _snapshot_date_from_scene(scene)
            try:
                existing = get_existing_scene_analysis_summary(farm_id, scene_id, snapshot_date)
                if (
                    existing
                    and not payload.force_refresh
                    and int(existing.get("distinct_h3_count") or 0) >= len(h3_cells)
                ):
                    cached += 1
                    statuses.append({
                        "scene_id": scene_id,
                        "snapshot_date": snapshot_date.isoformat(),
                        "status": "cached",
                        "h3_rows": int(existing.get("distinct_h3_count") or 0),
                    })
                    continue

                update_pipeline_job_stage(
                    job_id,
                    "process_history_scene",
                    status="running",
                    metadata={"scene_index": index, "scene_count": len(scenes), "scene_id": scene_id},
                )
                raster = run_raster_preview_for_scene(
                    farm_id=farm_id,
                    bbox=bbox,
                    scene=scene,
                    h3_resolution=int(farm.get("h3_resolution") or 12),
                    h3_cells_bigint=h3_cells,
                    farm_polygon_geojson=polygon,
                )
                returned = {int(row["h3_index"]) for row in (raster.get("features") or []) if row.get("h3_index") is not None}
                missing = set(h3_cells) - returned
                if missing:
                    raise HotStreamOrchestratorError(
                        f"Sentinel-2 history scene did not return all registered H3 cells. Missing {len(missing)} cells.",
                        code="S2_HISTORY_H3_CONTRACT_MISMATCH",
                        status_code=422,
                    )
                lakehouse = write_sentinel2_to_lakehouse(farm_id, raster)
                processed += 1
                statuses.append({
                    "scene_id": scene_id,
                    "snapshot_date": snapshot_date.isoformat(),
                    "status": "succeeded",
                    "h3_rows": len(raster.get("features") or []),
                    "postgres_rows_written": lakehouse.get("postgres_rows_written"),
                    "parquet_uri": lakehouse.get("parquet_uri"),
                })
            except Exception as exc:
                failed += 1
                statuses.append({
                    "scene_id": scene_id,
                    "snapshot_date": snapshot_date.isoformat(),
                    "status": "failed",
                    "error": str(exc),
                })

        overall = "succeeded" if failed == 0 else ("partial" if processed + cached > 0 else "failed")
        metadata = {
            "scene_count": len(scenes),
            "processed": processed,
            "cached": cached,
            "failed": failed,
            "status": overall,
        }
        if overall == "failed":
            fail_pipeline_job(job_id, error_code="S2_HISTORY_ALL_FAILED", error_message="All Sentinel-2 history scenes failed", metadata=metadata)
        else:
            complete_pipeline_job(job_id, metadata=metadata)
        return {
            "farm_id": str(farm_id),
            "status": overall,
            "requested_start_date": payload.start_date,
            "requested_end_date": payload.end_date,
            "scenes_found": len(scenes),
            "processed": processed,
            "cached": cached,
            "failed": failed,
            "pipeline_job_id": job_id,
            "scenes": statuses,
        }
    except Exception as exc:
        try:
            fail_pipeline_job(job_id, error_code=getattr(exc, "code", "S2_HISTORY_BACKFILL_ERROR"), error_message=str(exc))
        except Exception:
            pass
        raise
