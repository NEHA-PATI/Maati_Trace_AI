from datetime import date

from services.analytics_query_service.app.feature_engine.builder import build_feature_rows


def _farm():
    return {
        "farm_id": "00000000-0000-0000-0000-000000000001",
        "farmer_id": "00000000-0000-0000-0000-000000000002",
        "fpo_id": None,
        "crop_code": "coconut",
        "h3_resolution": 12,
    }


def _profile():
    return {
        "profile_version": "coconut_v1",
        "preferred_history_days": 180,
        "temporal_windows": {"rainfall": [7, 30]},
    }


def test_feature_builder_falls_back_to_successful_h3_environment_source():
    rows = build_feature_rows(
        farm=_farm(),
        profile=_profile(),
        bundle={
            "sentinel2": [
                {"h3_index": 1, "snapshot_date": date(2026, 7, 1), "valid_fraction": 1.0},
            ],
            "sentinel1": [
                {
                    "h3_index": 1,
                    "snapshot_date": date(2026, 8, 20),
                    "valid_fraction": 0.8,
                    "mean_vv": -10.0,
                    "mean_vh": -15.0,
                    "vh_vv_ratio": 1.5,
                },
            ],
        },
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert len(rows) == 1
    assert rows[0]["anchor_dataset"] == "sentinel1_l2a"
    assert rows[0]["anchor_scene_id"] is None
    assert rows[0]["quality"]["source_quality"]["sentinel2"] == 0.0
    assert rows[0]["quality"]["source_quality"]["sentinel1"] > 0.0

