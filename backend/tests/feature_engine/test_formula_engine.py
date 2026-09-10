from datetime import date

import pytest

from services.analytics_query_service.app.feature_engine.formula_engine import (
    aggregate_farm_predictions,
    calculate_h3_predictions,
    project_h3_predictions_to_grid,
    status_label,
)


def profile():
    return {
        "crop_code": "coconut",
        "profile_version": "coconut_v1",
        "normalization": {"z_critical": 3.0},
        "temporal_windows": {"primary_rainfall_window": 30},
        "soil_ranges": {},
    }


def water_formula():
    return {
        "crop_code": "coconut",
        "prediction_key": "water_stress",
        "display_name": "Water Stress Risk",
        "formula_version": "water_stress_coconut_v1",
        "crop_profile_version": "coconut_v1",
        "score_direction": "risk",
        "execution_order": 100,
        "component_weights": {
            "canopy_moisture_stress": 0.5,
            "rainfall_stress": 0.5,
        },
        "thresholds": {
            "normal": 20,
            "watch": 40,
            "attention": 60,
            "high": 80,
            "affected_threshold": 60,
        },
        "parameters": {"rain_window_days": 30},
        "metadata": {"validation_status": "engineering_default"},
    }


def feature_row(h3_index=1, ndmi_z=-3.0, msi_z=3.0, rain_z=-3.0, rain_deficit=1.0, area=100.0):
    return {
        "farm_id": "00000000-0000-0000-0000-000000000001",
        "farmer_id": "00000000-0000-0000-0000-000000000002",
        "fpo_id": None,
        "h3_index": h3_index,
        "h3_resolution": 12,
        "feature_date": date(2026, 8, 20),
        "crop_code": "coconut",
        "crop_profile_version": "coconut_v1",
        "feature_version": "farm_h3_engineered_features_v1",
        "confidence": 1.0,
        "observed_area_m2": area,
        "features": {
            "ndmi_z": ndmi_z,
            "msi_z": msi_z,
            "rain_30d_z": rain_z,
            "rain_30d_deficit": rain_deficit,
        },
        "quality": {
            "source_quality": {
                "sentinel2": 1.0,
                "gpm": 1.0,
            }
        },
    }


def test_status_labels_are_direction_consistent():
    assert status_label(85, "risk", {"normal": 20, "watch": 40, "attention": 60, "high": 80}) == "Critical"
    assert status_label(85, "condition", {"critical": 20, "poor": 40, "attention": 60, "fair": 80}) == "Good"


def test_calculates_high_water_stress_from_high_evidence():
    rows = calculate_h3_predictions(feature_rows=[feature_row()], formulas=[water_formula()], profile=profile())
    assert len(rows) == 1
    assert rows[0]["score"] > 90
    assert rows[0]["confidence"] == pytest.approx(1.0)
    assert rows[0]["status_label"] == "Critical"


def test_farm_aggregation_is_area_and_confidence_weighted():
    h3_rows = calculate_h3_predictions(
        feature_rows=[
            feature_row(h3_index=1, ndmi_z=-3, msi_z=3, rain_z=-3, area=100),
            feature_row(h3_index=2, ndmi_z=0, msi_z=0, rain_z=0, rain_deficit=0, area=300),
        ],
        formulas=[water_formula()],
        profile=profile(),
    )
    farm_rows = aggregate_farm_predictions(h3_rows=h3_rows, formulas=[water_formula()])
    assert len(farm_rows) == 1
    assert 20 <= farm_rows[0]["score"] <= 30
    assert farm_rows[0]["affected_area_percent"] == pytest.approx(25.0)


def test_grid_projection_uses_crosswalk_and_marks_semantics():
    h3_rows = calculate_h3_predictions(
        feature_rows=[
            feature_row(h3_index=1, ndmi_z=-3, msi_z=3, rain_z=-3, area=100),
            feature_row(h3_index=2, ndmi_z=0, msi_z=0, rain_z=0, rain_deficit=0, area=100),
        ],
        formulas=[water_formula()],
        profile=profile(),
    )
    crosswalk = [
        {"grid_cell_id": "00000000-0000-0000-0000-000000000010", "h3_index": 1, "overlap_ratio": 0.75},
        {"grid_cell_id": "00000000-0000-0000-0000-000000000010", "h3_index": 2, "overlap_ratio": 0.25},
    ]
    grid = project_h3_predictions_to_grid(h3_rows=h3_rows, crosswalk=crosswalk, formulas=[water_formula()])
    assert len(grid) == 1
    assert grid[0]["value_source"] == "h3_formula_grid_overlap_weighted"
    assert grid[0]["contributing_h3_count"] == 2
    assert grid[0]["dominant_h3_index"] == 1
    assert grid[0]["score"] > 70
