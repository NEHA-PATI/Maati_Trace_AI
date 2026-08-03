from services.profile_service.app.service import (
    farmer_profile_progress,
    fpo_profile_progress,
)


def test_pending_district_still_allows_internal_completion():
    complete, percentage, missing = (
        farmer_profile_progress(
            {
                "full_name": "Neha Pati",
                "phone_number": (
                    "+918208504361"
                ),
                "state_name": "Odisha",
                "district_name": "Pending",
                "block_name": None,
                "block_code": None,
                "village_name": None,
                "consent_data_processing": (
                    True
                ),
            }
        )
    )

    assert complete is True
    assert percentage < 100
    assert missing == []


def test_required_consent_is_incomplete():
    complete, _, missing = (
        farmer_profile_progress(
            {
                "full_name": "Farmer",
                "phone_number": (
                    "+919876543210"
                ),
                "state_name": "Odisha",
                "district_name": (
                    "Unassigned"
                ),
                "block_name": None,
                "block_code": None,
                "village_name": None,
                "consent_data_processing": (
                    False
                ),
            }
        )
    )

    assert complete is False
    assert "consent_data_processing" in missing


def test_complete_farmer_profile():
    complete, percentage, missing = (
        farmer_profile_progress(
            {
                "full_name": "Neha Pati",
                "phone_number": (
                    "+918208504361"
                ),
                "state_name": "Odisha",
                "district_name": "Puri",
                "block_name": "Satyabadi",
                "block_code": 3546,
                "village_name": (
                    "Example Village"
                ),
                "consent_data_processing": (
                    True
                ),
            }
        )
    )

    assert complete is True
    assert percentage < 100
    assert missing == []


def test_complete_fpo_profile():
    complete, percentage, missing = (
        fpo_profile_progress(
            {
                "fpo_name": "Example FPO",
                "registration_number": (
                    "FPO-001"
                ),
                "contact_person_name": (
                    "Test Manager"
                ),
                "contact_phone": (
                    "+919876543210"
                ),
                "contact_email": (
                    "fpo@example.com"
                ),
                "state_name": "Odisha",
                "district_name": "Puri",
                "office_address": (
                    "Example office address"
                ),
            }
        )
    )

    assert complete is True
    assert percentage < 100
    assert missing == []
