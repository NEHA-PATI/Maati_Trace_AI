from services.fpo_management_service.app.repository import normalize_consent_language


def test_regional_browser_language_matches_base_policy_language():
    assert normalize_consent_language("en-US,en;q=0.9") == "en"


def test_missing_language_defaults_to_english():
    assert normalize_consent_language(None) == "en"
