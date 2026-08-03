import os
from uuid import UUID

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")

from services.farm_registry_service.app.auth_client import AuthPrincipal
from services.farm_registry_service.app.dependencies import (
    RequestContext,
    require_internal_farm_service,
)
from services.farm_registry_service.app.errors import FarmRegistryError
from services.farm_registry_service.app.profile_client import FarmerValidation
from services.farm_registry_service.app.schemas import FarmRegisterRequest
from services.farm_registry_service.app import service

FARMER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_FARMER_ID = UUID("22222222-2222-2222-2222-222222222222")
FPO_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_ID = UUID("99999999-9999-9999-9999-999999999999")


def farmer_context():
    return RequestContext(
        authorization="Bearer token",
        correlation_id="corr-test",
        principal=AuthPrincipal(
            user_id=USER_ID,
            full_name="Farmer",
            email="farmer@example.com",
            role="farmer",
            is_active=True,
            is_verified=True,
            onboarding_status="completed",
        ),
    )


def payload(farmer_id=FARMER_ID):
    return FarmRegisterRequest.model_validate(
        {
            "farmer_id": str(farmer_id),
            "farm_name": "Test Farm",
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
    )


def profile_envelope():
    return {
        "profile_type": "farmer",
        "onboarding_status": "completed",
        "completion_percentage": 80,
        "missing_fields": [],
        "profile": {
            "farmer_id": str(FARMER_ID),
            "fpo_id": str(FPO_ID),
            "is_active": True,
        },
    }


def created_farm_row():
    return {
        "farm_id": UUID("33333333-3333-3333-3333-333333333333"),
        "farmer_id": FARMER_ID,
        "fpo_id": FPO_ID,
        "farm_name": "Test Farm",
        "survey_number": None,
        "state_name": "Odisha",
        "district_name": "Puri",
        "district_code": 21,
        "block_name": "Sadar",
        "block_code": 123,
        "village_name": None,
        "polygon_geojson": payload().polygon,
        "h3_resolution": 12,
        "h3_cell_count": 1,
        "area_acres": 0.12,
        "bbox": [85.831, 19.814, 85.833, 19.816],
        "is_active": True,
        "created_at": None,
        "updated_at": None,
    }


def configure_success(monkeypatch, *, complete=True):
    monkeypatch.setattr(
        service.profile_client,
        "get_my_profile",
        lambda **_kwargs: profile_envelope(),
    )
    monkeypatch.setattr(
        service.profile_client,
        "validate_farmer_internal",
        lambda farmer_id, _correlation_id: FarmerValidation(
            farmer_id=farmer_id,
            fpo_id=FPO_ID,
            is_active=True,
            profile_complete=complete,
            onboarding_status="completed" if complete else "pending",
        ),
    )
    monkeypatch.setattr(
        service.external_clients,
        "validate_location",
        lambda **_kwargs: {
            "is_valid": True,
            "state_name": "Odisha",
            "district_name": "Puri",
            "district_code": 21,
            "block_name": "Sadar",
            "block_code": 123,
        },
    )
    monkeypatch.setattr(
        service.external_clients,
        "create_h3_preview",
        lambda **_kwargs: {
            "resolution": 12,
            "h3_cells_bigint": [123456789],
            "cell_count": 1,
            "bbox": [85.831, 19.814, 85.833, 19.816],
        },
    )
    monkeypatch.setattr(
        service.repository,
        "create_farm",
        lambda _data: created_farm_row(),
    )


def test_farmer_registers_own_farm(monkeypatch):
    configure_success(monkeypatch)
    result = service.register_farm(farmer_context(), payload())
    assert result["farmer_id"] == FARMER_ID
    assert result["fpo_id"] == FPO_ID


def test_incomplete_farmer_cannot_register(monkeypatch):
    configure_success(monkeypatch, complete=False)
    with pytest.raises(FarmRegistryError) as exc:
        service.register_farm(farmer_context(), payload())
    assert exc.value.code == "FARMER_PROFILE_INCOMPLETE"
    assert exc.value.status_code == 409


def test_farmer_cannot_register_for_other_farmer(monkeypatch):
    configure_success(monkeypatch)
    monkeypatch.setattr(
        service.profile_client,
        "validate_farmer_internal",
        lambda farmer_id, _correlation_id: FarmerValidation(
            farmer_id=farmer_id,
            fpo_id=FPO_ID,
            is_active=True,
            profile_complete=True,
            onboarding_status="completed",
        ),
    )
    with pytest.raises(FarmRegistryError) as exc:
        service.register_farm(farmer_context(), payload(OTHER_FARMER_ID))
    assert exc.value.code == "FARMER_ACCESS_FORBIDDEN"


def test_client_cannot_force_fpo_id(monkeypatch):
    configure_success(monkeypatch)
    forced_payload = payload()
    forced_payload.fpo_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    with pytest.raises(FarmRegistryError) as exc:
        service.register_farm(farmer_context(), forced_payload)
    assert exc.value.code == "FARM_FPO_MISMATCH"


def test_internal_token_is_required(monkeypatch):
    monkeypatch.setenv("FARM_REGISTRY_INTERNAL_SERVICE_TOKEN", "expected")
    with pytest.raises(FarmRegistryError) as exc:
        require_internal_farm_service("wrong")
    assert exc.value.status_code == 403


def test_internal_token_accepts_expected_value(monkeypatch):
    monkeypatch.setenv("FARM_REGISTRY_INTERNAL_SERVICE_TOKEN", "expected")
    assert require_internal_farm_service("expected") is None
