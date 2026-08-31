from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from services.lakehouse_writer_service.app.environment_repository import (
    get_table_spec,
    upsert_environment_rows,
)
from services.lakehouse_writer_service.app.multisource_schemas import (
    EnvironmentLakehouseWriteRequest,
)
from services.lakehouse_writer_service.app.parquet_writer import (
    write_partitioned_parquet_rows,
)
from services.lakehouse_writer_service.app.repository import get_farm_context


class EnvironmentLakehouseError(RuntimeError):
    pass


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise EnvironmentLakehouseError(f"Invalid source datetime: {value}") from exc


def _record_partition_date(dataset_key: str, row: dict[str, Any], source_dt: datetime | None) -> str:
    for key in ["snapshot_date", "observation_date", "period_start"]:
        if row.get(key):
            return str(row[key])[:10]
    for key in ["observed_at", "valid_at"]:
        if row.get(key):
            return str(row[key])[:10]
    return (source_dt.date() if source_dt else date.today()).isoformat()


def _enrich_record(
    *,
    payload: EnvironmentLakehouseWriteRequest,
    farm: dict[str, Any],
    record: dict[str, Any],
    parquet_uri: str | None,
) -> dict[str, Any]:
    source_dt = _parse_datetime(payload.source_datetime)
    row = dict(record)
    row.update(
        {
            "farm_id": str(payload.farm_id),
            "farmer_id": str(farm["farmer_id"]),
            "fpo_id": str(farm["fpo_id"]) if farm.get("fpo_id") else None,
            "state_name": farm["state_name"],
            "district_name": farm["district_name"],
            "district_code": farm.get("district_code"),
            "block_name": farm.get("block_name"),
            "block_code": farm.get("block_code"),
            "source_provider": payload.provider,
            "source_collection": payload.source_collection,
            "source_item_id": payload.source_item_id,
            "source_datetime": source_dt,
            "processing_version": payload.processing_version,
            "parquet_uri": parquet_uri,
        }
    )

    if payload.dataset_key in {"sentinel_1_rtc", "landsat_c2_l2"}:
        row.setdefault("snapshot_date", (source_dt.date() if source_dt else date.today()))
        row.setdefault("scene_id", payload.source_item_id)
        row.setdefault("scene_datetime", source_dt)
        row.setdefault("h3_resolution", payload.h3_resolution)
        row.setdefault("source_assets_used", payload.source_assets_used)
    elif payload.dataset_key in {"cop_dem_glo30", "esa_worldcover", "jrc_surface_water", "soilgrids_v2"}:
        row.setdefault("h3_resolution", payload.h3_resolution)
        row.setdefault("source_assets_used", payload.source_assets_used)
    return row


def write_environment_features(payload: EnvironmentLakehouseWriteRequest) -> dict[str, Any]:
    if payload.dataset_key == "sentinel_2_l2a":
        raise EnvironmentLakehouseError(
            "Sentinel-2 must continue using /v1/lakehouse/sentinel2/write"
        )
    if not payload.records:
        raise EnvironmentLakehouseError("No environment records supplied")

    farm = get_farm_context(payload.farm_id)
    source_dt = _parse_datetime(payload.source_datetime)
    rows_without_uri = [
        _enrich_record(payload=payload, farm=farm, record=record, parquet_uri=None)
        for record in payload.records
    ]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows_without_uri:
        grouped[_record_partition_date(payload.dataset_key, row, source_dt)].append(row)

    parquet_uris: list[str] = []
    final_rows: list[dict[str, Any]] = []
    for partition_date, group_rows in grouped.items():
        uri = write_partitioned_parquet_rows(
            dataset=get_table_spec(payload.dataset_key).table,
            rows=group_rows,
            partitions={
                "state": farm["state_name"],
                "district": farm["district_name"],
                "date": partition_date,
            },
        )
        parquet_uris.append(uri)
        for row in group_rows:
            final_rows.append({**row, "parquet_uri": uri})

    postgres_rows = upsert_environment_rows(payload.dataset_key, final_rows)
    spec = get_table_spec(payload.dataset_key)
    return {
        "dataset_key": payload.dataset_key,
        "postgres_table": spec.table,
        "farm_id": payload.farm_id,
        "row_count": len(final_rows),
        "postgres_rows_written": postgres_rows,
        "parquet_rows_written": len(final_rows),
        "parquet_uris": parquet_uris,
    }
