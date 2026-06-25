from fastapi.testclient import TestClient

from services.boundary_index_service.app.main import app
from services.boundary_index_service.app.h3_indexer import polygon_to_h3_bigints

client = TestClient(app)


VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [85.8200, 20.2900],
            [85.8210, 20.2900],
            [85.8210, 20.2910],
            [85.8200, 20.2910],
            [85.8200, 20.2900],
        ]
    ],
}


def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_polygon_to_h3_bigints():
    result = polygon_to_h3_bigints(
        geojson=VALID_POLYGON,
        resolution=12,
        include_cells=True,
    )

    assert result["resolution"] == 12
    assert result["cell_count"] >= 0
    assert result["returned_cell_count"] == len(result["h3_cells_bigint"])
    assert result["geometry_type"] == "Polygon"


def test_polygon_to_h3_bigints_returns_full_set_when_unbounded():
    result = polygon_to_h3_bigints(
        geojson=VALID_POLYGON,
        resolution=12,
        include_cells=True,
        max_cells=None,
    )

    assert result["returned_cell_count"] == result["cell_count"]
    assert len(result["h3_cells_bigint"]) == result["cell_count"]


def test_h3_preview_endpoint():
    payload = {
        "resolution": 12,
        "include_cells": True,
        "polygon": VALID_POLYGON,
    }

    response = client.post("/v1/h3/preview", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["resolution"] == 12
    assert "cell_count" in body
    assert "h3_cells_bigint" in body


def test_h3_preview_endpoint_can_return_full_set():
    payload = {
        "resolution": 12,
        "include_cells": True,
        "max_cells": None,
        "polygon": VALID_POLYGON,
    }

    response = client.post("/v1/h3/preview", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["returned_cell_count"] == body["cell_count"]


def test_reject_point_geometry():
    payload = {
        "resolution": 12,
        "include_cells": True,
        "polygon": {
            "type": "Point",
            "coordinates": [85.82, 20.29],
        },
    }

    response = client.post("/v1/h3/preview", json=payload)

    assert response.status_code == 400
