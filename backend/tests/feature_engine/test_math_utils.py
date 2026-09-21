from datetime import date

import pytest

from services.analytics_query_service.app.feature_engine.math_utils import (
    freshness_score,
    linear_slope,
    robust_z,
    trapezoid_suitability,
    weighted_score,
)


def test_robust_z_detects_negative_departure():
    z = robust_z(0.30, [0.60, 0.61, 0.59, 0.62, 0.58])
    assert z is not None
    assert z < -3


def test_linear_slope_uses_elapsed_days():
    slope = linear_slope([
        (date(2026, 8, 1), 0.40),
        (date(2026, 8, 6), 0.50),
        (date(2026, 8, 11), 0.60),
    ])
    assert slope == pytest.approx(0.02)


def test_trapezoid_suitability():
    assert trapezoid_suitability(6.0, [4.5, 5.5, 7.0, 8.0]) == 1.0
    assert trapezoid_suitability(4.5, [4.5, 5.5, 7.0, 8.0]) == 0.0
    assert trapezoid_suitability(5.0, [4.5, 5.5, 7.0, 8.0]) == pytest.approx(0.5)


def test_quality_aware_score_renormalizes_missing_component():
    score, confidence = weighted_score(
        {
            "a": {"value": 1.0, "quality": 1.0},
            "b": {"value": None, "quality": 0.0},
        },
        {"a": 0.5, "b": 0.5},
    )
    assert score == pytest.approx(1.0)
    assert confidence == pytest.approx(0.5)


def test_freshness_half_life():
    assert freshness_score(0, 10) == pytest.approx(1.0)
    assert freshness_score(10, 10) == pytest.approx(0.5)
