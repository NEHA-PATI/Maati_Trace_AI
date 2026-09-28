from services.fpo_management_service.app.bulk_states import staged_status_for_farmer_match


def test_farmer_match_requires_consent_before_relationship():
    assert staged_status_for_farmer_match("FARMER") == "AWAITING_CONSENT"


def test_farm_match_requires_confirmation_before_relationship():
    assert staged_status_for_farmer_match("FARM") == "AWAITING_FARM_CONFIRMATION"
