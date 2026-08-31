from services.hot_stream_orchestrator_service.app.environment_schemas import (
    DEFAULT_ENVIRONMENT_DATASETS,
)


def test_environment_refresh_does_not_replace_sentinel2():
    assert "sentinel_2_l2a" not in DEFAULT_ENVIRONMENT_DATASETS
    assert "landsat_c2_l2" in DEFAULT_ENVIRONMENT_DATASETS
    assert "sentinel_1_rtc" in DEFAULT_ENVIRONMENT_DATASETS
