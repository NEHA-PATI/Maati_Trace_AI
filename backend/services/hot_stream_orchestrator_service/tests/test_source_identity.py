from services.hot_stream_orchestrator_service.app.source_identity import (
    h3_index_set_hash,
    materialization_fingerprint,
    source_item_hash,
)


def test_source_item_hash_ignores_signed_asset_urls():
    first = {
        "id": "scene-1",
        "collection": "demo",
        "datetime": "2026-09-01T00:00:00Z",
        "assets": {"data": {"href": "https://one.example/signed"}},
    }
    second = {
        **first,
        "assets": {"data": {"href": "https://two.example/signed"}},
    }
    assert source_item_hash(first) == source_item_hash(second)


def test_h3_hash_is_order_independent():
    assert h3_index_set_hash([3, 1, 2, 2]) == h3_index_set_hash([1, 2, 3])


def test_materialization_fingerprint_changes_when_h3_set_changes():
    common = {
        "farm_id": "farm-1",
        "boundary_hash": "boundary-1",
        "h3_resolution": 12,
        "dataset_key": "cop_dem_glo30",
        "dataset_version": "static-v1",
        "source_version": "static-v1",
        "processing_version": "dem-v1",
    }
    first = materialization_fingerprint(**common, h3_indexes=[1, 2])
    second = materialization_fingerprint(**common, h3_indexes=[1, 3])
    assert first != second
