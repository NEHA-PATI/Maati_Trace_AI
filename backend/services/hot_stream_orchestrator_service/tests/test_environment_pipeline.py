from types import SimpleNamespace
from uuid import UUID

import pytest

from services.hot_stream_orchestrator_service.app import environment_service
from services.hot_stream_orchestrator_service.app import service as orchestrator_service


FARM_ID = UUID("11111111-1111-4111-8111-111111111111")
POLYGON = {
    "type": "Polygon",
    "coordinates": [[[85.0, 20.0], [85.001, 20.0], [85.001, 20.001], [85.0, 20.0]]],
}


def payload(*datasets):
    return SimpleNamespace(
        dataset_keys=list(datasets),
        dataset_options={},
        max_items_per_dataset=1,
        max_cloud_cover=40,
        force_refresh=True,
        start_date="2026-01-01",
        end_date="2026-09-01",
    )


def setup_common(monkeypatch):
    events = []
    monkeypatch.setattr(environment_service, "create_pipeline_job", lambda **kwargs: {"job_id": "job-1"})
    monkeypatch.setattr(
        environment_service,
        "update_pipeline_job_stage",
        lambda *args, **kwargs: events.append(("stage", kwargs.get("stage") or args[1])),
    )
    monkeypatch.setattr(
        environment_service,
        "ensure_farm_analysis_ready",
        lambda farm_id: {
            "farm": {
                "bbox": [85.0, 20.0, 85.001, 20.001],
                "polygon_geojson": POLYGON,
                "h3_cells": [101, 102],
                "h3_resolution": 12,
            }
        },
    )
    monkeypatch.setattr(environment_service, "complete_pipeline_job", lambda *args, **kwargs: events.append(("complete", kwargs)))
    monkeypatch.setattr(environment_service, "fail_pipeline_job", lambda *args, **kwargs: events.append(("fail", kwargs)))
    return events


def test_sentinel2_is_processed_inside_mandatory_environment_stage(monkeypatch):
    events = setup_common(monkeypatch)
    searches = []
    writes = []

    monkeypatch.setattr(
        environment_service,
        "search_catalog_dataset",
        lambda **kwargs: searches.append(kwargs) or {"provider": "test", "items": [{"scene_id": "s2-1", "datetime": "2026-08-01"}]},
    )
    monkeypatch.setattr(
        environment_service,
        "run_raster_preview_for_scene",
        lambda **kwargs: {
            "scene_id": kwargs["scene"]["scene_id"],
            "h3_resolution": 12,
            "features": [{"h3_index": 101}, {"h3_index": 102}],
        },
    )
    monkeypatch.setattr(
        environment_service,
        "write_sentinel2_to_lakehouse",
        lambda *args, **kwargs: writes.append("sentinel2") or {"postgres_rows_written": 2},
    )
    monkeypatch.setattr(
        environment_service,
        "process_environment_dataset",
        lambda **kwargs: {"dataset_key": kwargs["dataset_key"], "provider": "test", "source_item_id": "x", "processing_version": "v1", "records": []},
    )
    monkeypatch.setattr(
        environment_service,
        "write_environment_to_lakehouse",
        lambda **kwargs: writes.append(kwargs["process_result"]["dataset_key"]) or {"postgres_rows_written": 1},
    )

    result = environment_service.materialize_environment(
        FARM_ID, payload("sentinel_2_l2a", "sentinel_1_rtc")
    )

    assert result["status"] == "succeeded"
    assert [item["dataset_key"] for item in result["datasets"]] == ["sentinel_2_l2a", "sentinel_1_rtc"]
    assert writes == ["sentinel2", "sentinel_1_rtc"]
    assert searches[0]["dataset_key"] == "sentinel_2_l2a"
    assert ("complete",) == tuple(event[:1] for event in events if event[0] == "complete")[0]


def test_unavailable_environment_dataset_does_not_stop_sibling_processing(monkeypatch):
    events = setup_common(monkeypatch)
    processed = []
    monkeypatch.setattr(
        environment_service,
        "search_catalog_dataset",
        lambda **kwargs: (
            {"provider": "test", "items": [], "errors": ["source unavailable"]}
            if kwargs["dataset_key"] == "sentinel_2_l2a"
            else {"provider": "test", "items": [{"scene_id": "s1"}]}
        ),
    )
    monkeypatch.setattr(
        environment_service,
        "process_environment_dataset",
        lambda **kwargs: processed.append(kwargs["dataset_key"]) or {
            "dataset_key": kwargs["dataset_key"],
            "provider": "test",
            "source_item_id": "x",
            "processing_version": "v1",
            "records": [],
        },
    )
    monkeypatch.setattr(
        environment_service,
        "write_environment_to_lakehouse",
        lambda **kwargs: {"postgres_rows_written": 1},
    )

    result = environment_service.materialize_environment(
        FARM_ID, payload("sentinel_2_l2a", "sentinel_1_rtc")
    )

    assert result["status"] == "completed_with_warnings"
    assert processed == ["sentinel_1_rtc"]
    assert any(event[0] == "complete" for event in events)
    assert not any(event[0] == "fail" for event in events)


def test_canonical_analysis_has_one_ordered_pipeline(monkeypatch):
    operations = []
    monkeypatch.setattr(orchestrator_service, "update_pipeline_job_stage", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator_service, "complete_pipeline_job", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator_service, "fail_pipeline_job", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        orchestrator_service,
        "ensure_farm_analysis_ready",
        lambda farm_id: operations.append("farm_ready") or {"status": "succeeded"},
    )
    monkeypatch.setattr(
        orchestrator_service,
        "materialize_trends_for_farm",
        lambda farm_id: operations.append("trends") or {"status": "succeeded"},
    )
    monkeypatch.setattr(
        orchestrator_service,
        "materialize_grid_for_farm",
        lambda farm_id: operations.append("grid_context") or {"status": "succeeded"},
    )
    monkeypatch.setattr(
        environment_service,
        "materialize_environment",
        lambda farm_id, payload: operations.append("environment_datasets") or {"status": "succeeded", "datasets": []},
    )
    monkeypatch.setattr(
        "services.analytics_query_service.app.feature_engine.service.materialize_intelligence",
        lambda *args, **kwargs: operations.append("intelligence") or {
            "status": "succeeded",
            "feature_processing": {},
            "calculation_processing": {},
        },
    )

    result = orchestrator_service.run_latest_analysis(
        FARM_ID,
        SimpleNamespace(
            start_date="2026-01-01",
            end_date="2026-09-01",
            max_cloud_cover=40,
            h3_resolution=12,
            max_candidate_scenes=10,
            max_items_per_dataset=1,
            provider="test",
            collection_id="test",
            force_refresh=True,
            model_dump=lambda: {},
        ),
        job_id="job-1",
    )

    assert result["status"] == "completed"
    assert operations == ["farm_ready", "environment_datasets", "trends", "grid_context", "intelligence"]
