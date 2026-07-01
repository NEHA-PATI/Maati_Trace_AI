from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


BOUNDARY_INDEX_SERVICE_URL = "http://localhost:8004"
DISTRICT_BOUNDARY_SERVICE_URL = "http://localhost:8005"
FARM_REGISTRY_SERVICE_URL = "http://localhost:8006"
STAC_SERVICE_URL = "http://localhost:8007"
RASTER_SERVICE_URL = "http://localhost:8008"

EXISTING_TEST_FARMER_ID = "ded106f9-972d-4e0b-b4e8-193a3c2874f9"

REPORT_PATH = Path("reports/cross_district_pipeline_report.json")


TEST_BLOCKS = [
    {
        "test_name": "Puri Pipili Test",
        "district_name": "Puri",
        "block_name": "Pipili",
        "block_code": 3544,
        "lon": 85.8320,
        "lat": 20.1130,
    },
    {
        "test_name": "Puri Sadar Test",
        "district_name": "Puri",
        "block_name": "Sadar",
        "block_code": 3545,
        "lon": 85.8240,
        "lat": 19.8190,
    },
    {
        "test_name": "Puri Satyabadi Test",
        "district_name": "Puri",
        "block_name": "Satyabadi",
        "block_code": 3546,
        "lon": 85.8205,
        "lat": 19.9900,
    },
    {
        "test_name": "Sambalpur Bamra Test",
        "district_name": "Sambalpur",
        "block_name": "Bamra",
        "block_code": 3558,
        "lon": 84.3950,
        "lat": 22.0640,
    },
    {
        "test_name": "Sambalpur Dhankauda Test",
        "district_name": "Sambalpur",
        "block_name": "Dhankauda",
        "block_code": 3559,
        "lon": 83.9660,
        "lat": 21.4700,
    },
    {
        "test_name": "Sambalpur Jamankira Test",
        "district_name": "Sambalpur",
        "block_name": "Jamankira",
        "block_code": 3560,
        "lon": 84.3660,
        "lat": 21.5400,
    },
    {
        "test_name": "Sambalpur Jujomura Test",
        "district_name": "Sambalpur",
        "block_name": "Jujomura",
        "block_code": 3561,
        "lon": 84.0440,
        "lat": 21.3600,
    },
]


def post_json(url: str, body: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    response = requests.post(url, json=body, timeout=timeout)

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    if response.status_code >= 400:
        raise RuntimeError(
            f"POST failed: {url}\n"
            f"Status: {response.status_code}\n"
            f"Response: {json.dumps(payload, indent=2)}"
        )

    return payload


def get_json(url: str, timeout: int = 60) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    if response.status_code >= 400:
        raise RuntimeError(
            f"GET failed: {url}\n"
            f"Status: {response.status_code}\n"
            f"Response: {json.dumps(payload, indent=2)}"
        )

    return payload


def make_farm_polygon(lon: float, lat: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon, lat],
                [lon + 0.00078, lat],
                [lon + 0.00078, lat + 0.00037],
                [lon, lat + 0.00037],
                [lon, lat],
            ]
        ],
    }


def make_tiny_raster_bbox(lon: float, lat: float) -> list[float]:
    return [
        lon,
        lat,
        lon + 0.00020,
        lat + 0.00020,
    ]


def make_stac_bbox(lon: float, lat: float) -> list[float]:
    return [
        lon - 0.005,
        lat - 0.005,
        lon + 0.006,
        lat + 0.006,
    ]


def validate_location(test: dict[str, Any]) -> dict[str, Any]:
    body = {
        "state_name": "Odisha",
        "district_name": test["district_name"],
        "block_name": test["block_name"],
        "block_code": test["block_code"],
    }

    return post_json(
        f"{DISTRICT_BOUNDARY_SERVICE_URL}/v1/location/validate",
        body,
    )


def register_test_farm(test: dict[str, Any]) -> dict[str, Any]:
    unique_suffix = str(int(time.time() * 1000))

    body = {
        "farmer_id": EXISTING_TEST_FARMER_ID,
        "farm_name": f"{test['test_name']} Farm",
        "survey_number": f"PIPE-{test['block_code']}-{unique_suffix}",
        "state_name": "Odisha",
        "district_name": test["district_name"],
        "block_name": test["block_name"],
        "block_code": test["block_code"],
        "village_name": "Pipeline Test Village",
        "h3_resolution": 12,
        "polygon": make_farm_polygon(test["lon"], test["lat"]),
    }

    return post_json(
        f"{FARM_REGISTRY_SERVICE_URL}/v1/farms/register",
        body,
    )


def search_stac_scene(test: dict[str, Any]) -> dict[str, Any]:
    cloud_limits = [30, 60, 100]

    last_error: Exception | None = None

    for max_cloud_cover in cloud_limits:
        body = {
            "provider": "planetary_computer",
            "collection_id": "sentinel-2-l2a",
            "bbox": make_stac_bbox(test["lon"], test["lat"]),
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "max_cloud_cover": max_cloud_cover,
            "limit": 1,
        }

        try:
            result = post_json(
                f"{STAC_SERVICE_URL}/v1/stac/search",
                body,
            )

            if result.get("returned_count", 0) > 0:
                result["used_max_cloud_cover"] = max_cloud_cover
                return result

        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise RuntimeError(f"No Sentinel-2 scene found for {test['test_name']}")


def run_raster_preview(
    test: dict[str, Any],
    farm_result: dict[str, Any],
    stac_result: dict[str, Any],
) -> dict[str, Any]:
    scene = stac_result["items"][0]

    body = {
        "farm_id": farm_result["farm_id"],
        "bbox": make_tiny_raster_bbox(test["lon"], test["lat"]),
        "h3_resolution": 12,
        "scene": {
            "provider": scene["provider"],
            "collection_id": scene["collection_id"],
            "scene_id": scene["scene_id"],
            "datetime": scene.get("datetime"),
            "cloud_cover": scene.get("cloud_cover"),
            "properties": scene.get("properties", {}),
            "assets": scene["assets"],
        },
    }

    return post_json(
        f"{RASTER_SERVICE_URL}/v1/raster/sentinel2/indices/preview",
        body,
        timeout=240,
    )


def run_health_checks() -> dict[str, Any]:
    return {
        "boundary_index_service": get_json(
            f"{BOUNDARY_INDEX_SERVICE_URL}/health/live"
        ),
        "district_boundary_service": get_json(
            f"{DISTRICT_BOUNDARY_SERVICE_URL}/health/live"
        ),
        "farm_registry_service": get_json(
            f"{FARM_REGISTRY_SERVICE_URL}/health/live"
        ),
        "stac_catalog_service": get_json(
            f"{STAC_SERVICE_URL}/health/live"
        ),
        "raster_processor_service": get_json(
            f"{RASTER_SERVICE_URL}/health/live"
        ),
    }


def run_pipeline() -> dict[str, Any]:
    report: dict[str, Any] = {
        "pipeline_name": "MaatiTrace Cross District Pipeline Test",
        "tested_services": [
            "boundary_index_service",
            "district_boundary_service",
            "farm_registry_service",
            "stac_catalog_service",
            "raster_processor_service",
        ],
        "health_checks": {},
        "tests": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
        },
    }

    print("\n1. Running health checks...")
    report["health_checks"] = run_health_checks()
    print("   Health checks passed.")

    for index, test in enumerate(TEST_BLOCKS, start=1):
        print(
            f"\n{index + 1}. Running {test['test_name']} - "
            f"{test['block_name']}, {test['district_name']}"
        )

        test_report: dict[str, Any] = {
            "test_name": test["test_name"],
            "district_name": test["district_name"],
            "block_name": test["block_name"],
            "block_code": test["block_code"],
            "input_lon": test["lon"],
            "input_lat": test["lat"],
            "status": "FAILED",
            "steps": {},
        }

        try:
            location_result = validate_location(test)
            print("   Location validation passed.")

            farm_result = register_test_farm(test)
            print(f"   Farm registered: {farm_result['farm_id']}")

            stac_result = search_stac_scene(test)
            scene = stac_result["items"][0]
            print(f"   STAC scene found: {scene['scene_id']}")

            raster_result = run_raster_preview(test, farm_result, stac_result)
            print(
                "   Raster preview passed: "
                f"rows={raster_result['row_count']}, "
                f"pixels={raster_result['total_pixel_count']}, "
                f"valid={raster_result['total_valid_pixel_count']}"
            )

            first_feature = (
                raster_result["features"][0]
                if raster_result.get("features")
                else {}
            )

            test_report["status"] = "PASSED"
            test_report["steps"] = {
                "location_validation": location_result,
                "farm_registration": {
                    "farm_id": farm_result["farm_id"],
                    "area_acres": farm_result.get("area_acres"),
                    "h3_cell_count": farm_result.get("h3_cell_count"),
                    "bbox": farm_result.get("bbox"),
                    "district_name": farm_result.get("district_name"),
                    "block_name": farm_result.get("block_name"),
                    "block_code": farm_result.get("block_code"),
                },
                "stac_search": {
                    "returned_count": stac_result.get("returned_count"),
                    "used_max_cloud_cover": stac_result.get("used_max_cloud_cover"),
                    "scene_id": scene.get("scene_id"),
                    "scene_datetime": scene.get("datetime"),
                    "scene_cloud_cover": scene.get("cloud_cover"),
                    "scene_bbox": scene.get("bbox"),
                    "proj_code": scene.get("properties", {}).get("proj:code"),
                },
                "raster_preview": {
                    "row_count": raster_result.get("row_count"),
                    "total_pixel_count": raster_result.get("total_pixel_count"),
                    "total_valid_pixel_count": raster_result.get(
                        "total_valid_pixel_count"
                    ),
                    "total_cloud_pixel_count": raster_result.get(
                        "total_cloud_pixel_count"
                    ),
                    "source_assets_used": raster_result.get("source_assets_used"),
                    "first_feature": {
                        "h3_index": first_feature.get("h3_index"),
                        "cloud_percentage": first_feature.get("cloud_percentage"),
                        "ndvi": first_feature.get("ndvi"),
                        "gndvi": first_feature.get("gndvi"),
                        "evi": first_feature.get("evi"),
                        "savi": first_feature.get("savi"),
                        "ndmi": first_feature.get("ndmi"),
                        "ndwi": first_feature.get("ndwi"),
                        "mndwi": first_feature.get("mndwi"),
                        "msi": first_feature.get("msi"),
                        "bsi": first_feature.get("bsi"),
                        "nbr": first_feature.get("nbr"),
                        "nbr2": first_feature.get("nbr2"),
                        "ndre": first_feature.get("ndre"),
                        "reci": first_feature.get("reci"),
                    },
                },
            }

            report["summary"]["passed"] += 1

        except Exception as exc:
            print(f"   FAILED: {exc}")
            test_report["error"] = str(exc)
            report["summary"]["failed"] += 1

        report["summary"]["total"] += 1
        report["tests"].append(test_report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    final_report = run_pipeline()

    print("\n==============================")
    print("PIPELINE TEST SUMMARY")
    print("==============================")
    print(json.dumps(final_report["summary"], indent=2))
    print(f"\nFull report saved to: {REPORT_PATH}")