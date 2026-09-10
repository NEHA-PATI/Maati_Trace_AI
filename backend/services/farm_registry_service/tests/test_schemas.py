import os

import pytest
from pydantic import ValidationError

os.environ.setdefault("JWT_SECRET", "test-secret")

from services.farm_registry_service.app.schemas import FarmRegisterRequest


def valid_payload():
    return {
        "farmer_id": "11111111-1111-1111-1111-111111111111",
        "farm_name": " Test Farm ",
        "crop_code": "coconut",
        "state_name": "Odisha",
        "district_name": "Puri",
        "block_code": 123,
        "polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.831, 19.814],
                    [85.833, 19.814],
                    [85.833, 19.816],
                    [85.831, 19.816],
                    [85.831, 19.814],
                ]
            ],
        },
        "h3_resolution": 12,
    }


def test_valid_farm_registration_payload():
    payload = FarmRegisterRequest.model_validate(valid_payload())
    assert payload.farm_name == "Test Farm"
    assert payload.h3_resolution == 12


def test_unknown_fields_are_rejected():
    payload = valid_payload()
    payload["profile_name"] = "not owned here"
    with pytest.raises(ValidationError):
        FarmRegisterRequest.model_validate(payload)


def test_unsupported_h3_resolution_is_rejected():
    payload = valid_payload()
    payload["h3_resolution"] = 6
    with pytest.raises(ValidationError):
        FarmRegisterRequest.model_validate(payload)


def test_non_polygon_geometry_is_rejected():
    payload = valid_payload()
    payload["polygon"] = {
        "type": "Point",
        "coordinates": [85.831, 19.814],
    }
    with pytest.raises(ValidationError):
        FarmRegisterRequest.model_validate(payload)
