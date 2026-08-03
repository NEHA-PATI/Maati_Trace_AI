import pytest
from pydantic import ValidationError

from services.profile_service.app.schemas import (
    FarmerProfileUpdate,
    FpoProfileSetupRequest,
)


def test_farmer_profile_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        FarmerProfileUpdate.model_validate(
            {
                "email": (
                    "cannot-change@example.com"
                )
            }
        )


def test_farmer_profile_rejects_fpo_id():
    with pytest.raises(ValidationError):
        FarmerProfileUpdate.model_validate(
            {
                "fpo_id": (
                    "11111111-1111-1111-1111-111111111111"
                )
            }
        )


def test_farmer_profile_normalizes_phone():
    payload = (
        FarmerProfileUpdate.model_validate(
            {
                "phone_number": (
                    "8208504361"
                )
            }
        )
    )

    assert (
        payload.phone_number
        == "+918208504361"
    )


def test_farmer_area_validation():
    with pytest.raises(ValidationError):
        FarmerProfileUpdate.model_validate(
            {
                "total_landholding_acres": 2,
                "cultivated_area_acres": 3,
            }
        )


def test_fpo_member_count_validation():
    with pytest.raises(ValidationError):
        FpoProfileSetupRequest.model_validate(
            {
                "fpo_name": "Example FPO",
                "registration_number": (
                    "REG-001"
                ),
                "contact_person_name": (
                    "Manager"
                ),
                "contact_phone": (
                    "9876543210"
                ),
                "contact_email": (
                    "manager@example.com"
                ),
                "state_name": "Odisha",
                "district_name": "Puri",
                "office_address": (
                    "Example office"
                ),
                "member_count": 10,
                "active_member_count": 12,
            }
        )


def test_fpo_setup_accepts_core_required_fields_only():
    payload = FpoProfileSetupRequest.model_validate(
        {
            "fpo_name": "Example FPO",
            "contact_person_name": "Manager",
            "contact_phone": "9876543210",
            "contact_email": (
                "manager@example.com"
            ),
        }
    )

    assert payload.registration_number is None
    assert payload.district_name is None
    assert payload.office_address is None
    assert (
        payload.contact_phone
        == "+919876543210"
    )
