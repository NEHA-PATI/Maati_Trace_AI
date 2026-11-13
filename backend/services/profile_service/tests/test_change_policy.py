from services.profile_service.app.profile_change_policy import classify_profile_changes


def test_safe_profile_change_does_not_require_review():
    assert classify_profile_changes(["display_name", "website_url"]) == "SAFE"


def test_operational_change_is_review_warning():
    assert classify_profile_changes(["member_count"]) == "REVIEW_WARNING"


def test_legal_change_requires_reverification():
    assert classify_profile_changes(["description", "registration_number"]) == "REVERIFICATION_REQUIRED"
