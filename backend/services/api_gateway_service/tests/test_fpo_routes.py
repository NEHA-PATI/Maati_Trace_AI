from services.api_gateway_service.app.proxy import _build_target_url


def test_fpo_owner_routes_forward_to_fpo_management_service():
    detail = _build_target_url("fpo", "me/farmers/farmer-id", b"")
    farms = _build_target_url("fpo", "me/farmers/farmer-id/farms", b"limit=20")

    assert detail.endswith("/v1/fpo/me/farmers/farmer-id")
    assert farms.endswith("/v1/fpo/me/farmers/farmer-id/farms?limit=20")


def test_legacy_fpo_portal_route_remains_unchanged():
    assert _build_target_url("fpo-portal", "bootstrap", b"").endswith("/v1/fpo-portal/bootstrap")


def test_historical_acquisition_routes_forward_to_ml_service():
    target = _build_target_url("historical-acquisition", "jobs/123", b"limit=10")

    assert target.endswith("/v1/historical-acquisition/jobs/123?limit=10")
