import pytest
from pydantic import ValidationError

from services.analytics_query_service.app.feature_engine.schemas import (
    CropProfileCreateRequest,
    FormulaCreateRequest,
)


def test_formula_weights_must_sum_to_one():
    with pytest.raises(ValidationError):
        FormulaCreateRequest(
            crop_code="future_crop",
            prediction_key="water_stress",
            display_name="Water Stress",
            formula_version="v1",
            crop_profile_version="future_crop_v1",
            score_direction="risk",
            component_weights={"canopy_moisture_stress": 0.5, "rainfall_stress": 0.4},
        )


def test_root_zone_weights_must_sum_to_one():
    with pytest.raises(ValidationError):
        CropProfileCreateRequest(
            crop_code="future_crop",
            crop_name="Future Crop",
            profile_version="future_crop_v1",
            root_zone_weights={"soil_water_0_7": 0.5, "soil_water_7_28": 0.2},
        )
