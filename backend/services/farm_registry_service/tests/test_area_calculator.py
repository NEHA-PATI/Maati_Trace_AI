import os

import pytest

os.environ.setdefault("JWT_SECRET", "test-secret")

from services.farm_registry_service.app.area_calculator import (
    FarmGeometryError,
    calculate_area_acres,
)


def test_polygon_area_is_positive():
    area = calculate_area_acres(
        {
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
        }
    )
    assert area > 0


def test_point_is_rejected():
    with pytest.raises(FarmGeometryError):
        calculate_area_acres(
            {
                "type": "Point",
                "coordinates": [85.831, 19.814],
            }
        )


def test_invalid_latitude_is_rejected():
    with pytest.raises(FarmGeometryError):
        calculate_area_acres(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [85.831, 91],
                        [85.833, 91],
                        [85.833, 92],
                        [85.831, 91],
                    ]
                ],
            }
        )
