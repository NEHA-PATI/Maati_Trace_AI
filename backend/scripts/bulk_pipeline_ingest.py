from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import requests

BOUNDARY_INDEX_SERVICE_URL = "http://localhost:8004"
DISTRICT_BOUNDARY_SERVICE_URL = "http://localhost:8005"
FARM_REGISTRY_SERVICE_URL = "http://localhost:8006"
RASTER_SERVICE_URL = "http://localhost:8008"

DEFAULT_INPUT_CSV = Path("data_contracts/csv/maatitrace_bulk_pipeline_template.csv")
DEFAULT_REPORT_JSON = Path("reports/bulk_pipeline_ingest_report.json")
DEFAULT_OUTPUT_CSV = Path("reports/bulk_pipeline_ingest_results.csv")


def yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "1"}


def clean(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def clean_int(value: Any) -> int | None:
    text = clean(value)
    if text is None:
        return None
    return int(float(text))


def clean_float(value: Any) -> float | None:
    text = clean(value)
    if text is None:
        return None
    return float(text)


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


def make_rectangle_polygon(row: dict[str, Any]) -> dict[str, Any]:
    polygon_text = clean(row.get("polygon_geojson"))
    if polygon_text:
        return json.loads(polygon_text)

    lon = clean_float(row.get("polygon_origin_lon"))
    lat = clean_float(row.get("polygon_origin_lat"))
    width = clean_float(row.get("polygon_width_deg")) or 0.00078
    height = clean_float(row.get("polygon_height_deg")) or 0.00037

    if lon is None or lat is None:
        raise ValueError("Either polygon_geojson or polygon_origin_lon/polygon_origin_lat is required.")

    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon, lat],
                [lon + width, lat],
                [lon + width, lat + height],
                [lon, lat + height],
                [lon, lat],
            ]
        ],
    }


def polygon_bbox(polygon: dict[str, Any]) -> list[float]:
    coords = polygon["coordinates"][0]
    lons = [float(point[0]) for point in coords]
    lats = [float(point[1]) for point in coords]
    return [min(lons), min(lats), max(lons), max(lats)]


def make_raster_bbox(row: dict[str, Any], farm_bbox: list[float]) -> list[float]:
    mode = str(row.get("raster_bbox_mode") or "tiny").strip().lower()

    if mode == "full":
        return farm_bbox

    size = clean_float(row.get("raster_bbox_size_deg")) or 0.00020
    lon = clean_float(row.get("polygon_origin_lon"))
    lat = clean_float(row.get("polygon_origin_lat"))

    if lon is None or lat is None:
        lon = farm_bbox[0]
        lat = farm_bbox[1]

    return [lon, lat, lon + size, lat + size]


def health_checks() -> dict[str, Any]:
    return {
        "boundary_index_service": get_json(f"{BOUNDARY_INDEX_SERVICE_URL}/health/live"),
        "district_boundary_service": get_json(f"{DISTRICT_BOUNDARY_SERVICE_URL}/health/live"),
        "farm_registry_service": get_json(f"{FARM_REGISTRY_SERVICE_URL}/health/live"),
        "raster_processor_service": get_json(f"{RASTER_SERVICE_URL}/health/live"),
    }


def create_fpo(row: dict[str, Any]) -> dict[str, Any] | None:
    if not yes(row.get("create_fpo")):
        return None

    if not clean(row.get("fpo_name")):
        return None

    body = {
        "fpo_name": clean(row.get("fpo_name")),
        "registration_number": clean(row.get("fpo_registration_number")),
        "state_name": clean(row.get("fpo_state_name")) or "Odisha",
        "district_name": clean(row.get("fpo_district_name")) or clean(row.get("farm_district_name")),
        "block_name": clean(row.get("fpo_block_name")),
        "block_code": clean_int(row.get("fpo_block_code")),
        "contact_phone": clean(row.get("fpo_contact_phone")),
        "contact_email": clean(row.get("fpo_contact_email")),
    }
    return post_json(f"{FARM_REGISTRY_SERVICE_URL}/v1/fpos", body)


def create_farmer(row: dict[str, Any], fpo_result: dict[str, Any] | None) -> dict[str, Any] | None:
    existing_farmer_id = clean(row.get("existing_farmer_id"))
    if existing_farmer_id:
        return {"farmer_id": existing_farmer_id, "source": "existing"}

    if not yes(row.get("create_farmer")):
        return None

    body = {
        "user_id": None,
        "fpo_id": fpo_result.get("fpo_id") if fpo_result else None,
        "full_name": clean(row.get("farmer_full_name")),
        "phone_number": clean(row.get("farmer_phone_number")),
        "gender": clean(row.get("farmer_gender")),
        "state_name": clean(row.get("farmer_state_name")) or "Odisha",
        "district_name": clean(row.get("farmer_district_name")) or clean(row.get("farm_district_name")),
        "block_name": clean(row.get("farmer_block_name")) or clean(row.get("farm_block_name")),
        "block_code": clean_int(row.get("farmer_block_code")) or clean_int(row.get("farm_block_code")),
        "village_name": clean(row.get("farmer_village_name")) or clean(row.get("farm_village_name")),
    }
    return post_json(f"{FARM_REGISTRY_SERVICE_URL}/v1/farmers", body)


def create_farm(row: dict[str, Any], farmer_result: dict[str, Any] | None, fpo_result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not yes(row.get("create_farm")):
        return None

    if farmer_result is None or not farmer_result.get("farmer_id"):
        raise ValueError("Cannot create farm without farmer_id. Use existing_farmer_id or create_farmer=yes.")

    unique_suffix = str(int(time.time() * 1000))
    survey_number = clean(row.get("survey_number")) or f"BULK-{unique_suffix}"
    polygon = make_rectangle_polygon(row)

    body = {
        "farmer_id": farmer_result["farmer_id"],
        "fpo_id": fpo_result.get("fpo_id") if fpo_result else None,
        "farm_name": clean(row.get("farm_name")),
        "survey_number": survey_number,
        "state_name": clean(row.get("farm_state_name")) or "Odisha",
        "district_name": clean(row.get("farm_district_name")),
        "block_name": clean(row.get("farm_block_name")),
        "block_code": clean_int(row.get("farm_block_code")),
        "village_name": clean(row.get("farm_village_name")),
        "h3_resolution": clean_int(row.get("h3_resolution")) or 12,
        "polygon": polygon,
    }
    return post_json(f"{FARM_REGISTRY_SERVICE_URL}/v1/farms/register", body)


def run_raster_preview(row: dict[str, Any], farm_result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not yes(row.get("run_raster_preview")):
        return None

    if farm_result is None:
        raise ValueError("Cannot run raster preview without farm creation result.")

    farm_bbox = farm_result.get("bbox") or polygon_bbox(make_rectangle_polygon(row))
    raster_bbox = make_raster_bbox(row, farm_bbox)

    body = {
        "farm_id": farm_result.get("farm_id"),
        "bbox": raster_bbox,
        "h3_resolution": clean_int(row.get("h3_resolution")) or 12,
        "provider": clean(row.get("stac_provider")) or "planetary_computer",
        "collection_id": clean(row.get("stac_collection_id")) or "sentinel-2-l2a",
        "start_date": clean(row.get("stac_start_date")) or "2025-12-01",
        "end_date": clean(row.get("stac_end_date")) or "2025-12-31",
        "max_cloud_cover": clean_float(row.get("stac_max_cloud_cover")) or 60,
    }
    return post_json(f"{RASTER_SERVICE_URL}/v1/raster/sentinel2/indices/preview-from-search", body, timeout=300)


def process_row(row: dict[str, Any]) -> dict[str, Any]:
    row_id = clean(row.get("row_id")) or "UNKNOWN_ROW"
    result: dict[str, Any] = {
        "row_id": row_id,
        "status": "FAILED",
        "steps": {},
    }

    try:
        if not yes(row.get("enabled")):
            result["status"] = "SKIPPED"
            return result

        fpo_result = create_fpo(row)
        result["steps"]["fpo"] = fpo_result

        farmer_result = create_farmer(row, fpo_result)
        result["steps"]["farmer"] = farmer_result

        farm_result = create_farm(row, farmer_result, fpo_result)
        result["steps"]["farm"] = farm_result

        raster_result = run_raster_preview(row, farm_result)
        result["steps"]["raster_preview"] = raster_result

        first_feature = None
        if raster_result and raster_result.get("features"):
            first_feature = raster_result["features"][0]

        result["summary"] = {
            "fpo_id": fpo_result.get("fpo_id") if fpo_result else None,
            "farmer_id": farmer_result.get("farmer_id") if farmer_result else None,
            "farm_id": farm_result.get("farm_id") if farm_result else None,
            "area_acres": farm_result.get("area_acres") if farm_result else None,
            "h3_cell_count": farm_result.get("h3_cell_count") if farm_result else None,
            "raster_row_count": raster_result.get("row_count") if raster_result else None,
            "raster_valid_pixels": raster_result.get("total_valid_pixel_count") if raster_result else None,
            "ndvi": first_feature.get("ndvi") if first_feature else None,
            "ndmi": first_feature.get("ndmi") if first_feature else None,
            "bsi": first_feature.get("bsi") if first_feature else None,
        }
        result["status"] = "PASSED"

    except Exception as exc:
        result["error"] = str(exc)

    return result


def write_results_csv(results: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "row_id",
        "status",
        "fpo_id",
        "farmer_id",
        "farm_id",
        "area_acres",
        "h3_cell_count",
        "raster_row_count",
        "raster_valid_pixels",
        "ndvi",
        "ndmi",
        "bsi",
        "error",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            summary = item.get("summary") or {}
            writer.writerow({
                "row_id": item.get("row_id"),
                "status": item.get("status"),
                "fpo_id": summary.get("fpo_id"),
                "farmer_id": summary.get("farmer_id"),
                "farm_id": summary.get("farm_id"),
                "area_acres": summary.get("area_acres"),
                "h3_cell_count": summary.get("h3_cell_count"),
                "raster_row_count": summary.get("raster_row_count"),
                "raster_valid_pixels": summary.get("raster_valid_pixels"),
                "ndvi": summary.get("ndvi"),
                "ndmi": summary.get("ndmi"),
                "bsi": summary.get("bsi"),
                "error": item.get("error"),
            })


def run(input_csv: Path, report_json: Path, output_csv: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "pipeline_name": "MaatiTrace Bulk CSV Pipeline Ingestion",
        "input_csv": str(input_csv),
        "health_checks": {},
        "results": [],
        "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
    }

    print("Running health checks...")
    report["health_checks"] = health_checks()
    print("Health checks passed.")

    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_id = clean(row.get("row_id")) or f"ROW-{report['summary']['total'] + 1}"
            print(f"Processing {row_id}...")
            result = process_row(row)
            print(f"  {result['status']}")
            if result.get("error"):
                print(f"  Error: {result['error']}")

            report["results"].append(result)
            report["summary"]["total"] += 1
            if result["status"] == "PASSED":
                report["summary"]["passed"] += 1
            elif result["status"] == "SKIPPED":
                report["summary"]["skipped"] += 1
            else:
                report["summary"]["failed"] += 1

    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_results_csv(report["results"], output_csv)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MaatiTrace bulk CSV pipeline ingestion.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_CSV), help="Input CSV path")
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON), help="Output report JSON path")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV), help="Output result CSV path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    final_report = run(Path(args.input), Path(args.report_json), Path(args.output_csv))
    print("\n==============================")
    print("BULK PIPELINE SUMMARY")
    print("==============================")
    print(json.dumps(final_report["summary"], indent=2))
    print(f"Report JSON: {args.report_json}")
    print(f"Result CSV: {args.output_csv}")
