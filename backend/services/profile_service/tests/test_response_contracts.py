from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import TypeAdapter

from services.profile_service.app.schemas import (
    FarmerProfileEnvelope,
    FpoProfileEnvelope,
    ProfileEnvelope,
)
from services.profile_service.app.service import (
    _farmer_envelope,
    _fpo_envelope,
)


def farmer_repository_row():
    now = datetime.now(timezone.utc)

    return {
        "farmer_id": uuid4(),
        "user_id": uuid4(),
        "fpo_id": None,

        "full_name": "NEHA PATI",
        "email": "nehapati11122004@gmail.com",
        "phone_number": "+918208504361",
        "gender": "female",
        "date_of_birth": None,
        "preferred_language": "en",

        "aadhaar_last4": None,
        "kyc_status": "pending",

        "state_name": "Odisha",
        "district_name": "Puri",
        "district_code": 369,
        "block_name": "Satyabadi",
        "block_code": 3546,
        "village_name": "Example Village",
        "gram_panchayat": None,
        "pincode": "752014",

        "farmer_type": "small",
        "total_landholding_acres": Decimal(
            "3.5000"
        ),
        "cultivated_area_acres": Decimal(
            "2.7500"
        ),
        "primary_crop": "Paddy",
        "irrigation_status": (
            "partially_irrigated"
        ),

        "consent_location_use": True,
        "consent_data_processing": True,
        "consent_advisory_messages": True,
        "consent_fpo_data_sharing": False,

        "profile_image_url": None,
        "is_active": True,

        "onboarding_completed_at": now,
        "created_at": now,
        "updated_at": now,
        "profile_version": 2,

        # Repository-only field that must never
        # leak into the nested profile response.
        "onboarding_status": "completed",
    }


def test_farmer_envelope_matches_schema():
    envelope = _farmer_envelope(
        farmer_repository_row()
    )

    validated = (
        FarmerProfileEnvelope.model_validate(
            envelope
        )
    )

    assert (
        validated.profile_type
        == "farmer"
    )

    assert (
        validated.onboarding_status
        == "completed"
    )

    assert (
        validated.profile
        .onboarding_completed_at
        is not None
    )

    assert (
        "onboarding_status"
        not in validated.profile.model_dump()
    )


def test_discriminated_profile_union():
    envelope = _farmer_envelope(
        farmer_repository_row()
    )

    validated = TypeAdapter(
        ProfileEnvelope
    ).validate_python(envelope)

    assert (
        validated.profile_type
        == "farmer"
    )


def test_pending_database_location_is_hidden():
    row = farmer_repository_row()
    row["district_name"] = "Pending"
    row["block_name"] = None
    row["block_code"] = None
    row["village_name"] = None
    row["consent_data_processing"] = False

    envelope = _farmer_envelope(row)

    assert (
        envelope["profile"][
            "district_name"
        ]
        is None
    )

    assert (
        envelope["onboarding_status"]
        == "pending"
    )


def test_fpo_pending_database_location_is_hidden():
    now = datetime.now(timezone.utc)
    row = {
        "fpo_id": uuid4(),
        "fpo_name": "Green FPO",
        "registration_number": None,
        "registration_type": None,
        "date_of_registration": None,
        "promoted_by": None,
        "promoting_institution_name": None,
        "contact_person_name": "Manager",
        "contact_person_designation": None,
        "contact_phone": "+919876543210",
        "alternate_phone": None,
        "contact_email": (
            "manager@example.com"
        ),
        "state_name": "Odisha",
        "district_name": "Pending",
        "district_code": None,
        "block_name": None,
        "block_code": None,
        "village_name": None,
        "gram_panchayat": None,
        "pincode": None,
        "office_address": None,
        "main_commodities": [],
        "member_count": None,
        "active_member_count": None,
        "services_provided": [],
        "verification_status": "pending",
        "profile_image_url": None,
        "is_active": True,
        "onboarding_completed_at": now,
        "created_at": now,
        "updated_at": now,
        "profile_version": 1,
        "current_user_fpo_role": "owner",
    }

    envelope = _fpo_envelope(row)
    validated = (
        FpoProfileEnvelope.model_validate(
            envelope
        )
    )

    assert (
        validated.profile
        .district_name
        is None
    )
    assert (
        validated.onboarding_status
        == "completed"
    )
