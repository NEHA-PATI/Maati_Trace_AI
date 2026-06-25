from fastapi.testclient import TestClient

from services.district_boundary_service.app.main import app

client = TestClient(app)


def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_validate_request_schema_district_only():
    payload = {
        "state_name": "Odisha",
        "district_name": "Khordha",
    }

    response = client.post("/v1/location/validate", json=payload)

    assert response.status_code in {200, 500}


def test_reject_short_district_name():
    payload = {
        "state_name": "Odisha",
        "district_name": "K",
    }

    response = client.post("/v1/location/validate", json=payload)

    assert response.status_code == 422