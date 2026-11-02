import pytest
from pydantic import ValidationError

from services.hot_stream_orchestrator_service.app.schemas import LatestAnalysisRequest


def test_latest_analysis_request_defaults_to_a_bounded_lookback():
    request = LatestAnalysisRequest()

    assert request.start_date < request.end_date
    assert request.max_items_per_dataset == 1
    assert request.h3_resolution == 12


def test_latest_analysis_request_preserves_sentinel2_history_limits():
    request = LatestAnalysisRequest(
        sentinel2_history_min_dates=2,
        sentinel2_history_max_scenes=3,
    )

    assert request.sentinel2_history_min_dates == 2
    assert request.sentinel2_history_max_scenes == 3


def test_latest_analysis_request_rejects_invalid_ranges():
    with pytest.raises(ValidationError):
        LatestAnalysisRequest(start_date="2026-09-08", end_date="2026-09-07")

    with pytest.raises(ValidationError):
        LatestAnalysisRequest(start_date="2020-01-01", end_date="2026-01-01")
