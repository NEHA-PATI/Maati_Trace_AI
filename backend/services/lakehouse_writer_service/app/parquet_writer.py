from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq
import s3fs

from shared.config.settings import settings


class LakehouseStorageError(RuntimeError):
    pass


def _clean_partition_value(value: Any) -> str:
    text_value = str(value or "unknown").strip()
    text_value = re.sub(r"[^A-Za-z0-9_.-]+", "_", text_value)
    text_value = re.sub(r"_+", "_", text_value).strip("_")
    return text_value or "unknown"


def _build_generic_partition_path(dataset: str, partitions: dict[str, Any]) -> str:
    path = _clean_partition_value(dataset)
    for key, value in partitions.items():
        path += f"/{_clean_partition_value(key)}={_clean_partition_value(value)}"
    return path


def write_partitioned_parquet_rows(
    *,
    dataset: str,
    rows: list[dict[str, Any]],
    partitions: dict[str, Any],
) -> str:
    if not rows:
        raise LakehouseStorageError("No rows supplied for Parquet write")

    partition_path = _build_generic_partition_path(dataset, partitions)
    file_name = f"part-{uuid4().hex}.parquet"

    normalized_rows = []
    for row in rows:
        normalized = row.copy()
        for key, value in list(normalized.items()):
            if hasattr(value, "isoformat"):
                normalized[key] = value.isoformat()
        normalized_rows.append(normalized)

    table = pa.Table.from_pylist(normalized_rows)
    storage_mode = settings.storage_mode.strip().lower()

    if storage_mode == "local":
        root_path = Path(settings.local_lakehouse_path)
        target_dir = root_path / partition_path
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / file_name
        pq.write_table(table, target_file, compression="snappy")
        return str(target_file).replace("\\", "/")

    if storage_mode == "s3":
        if not settings.s3_lakehouse_bucket:
            raise LakehouseStorageError(
                "S3_LAKEHOUSE_BUCKET is required when STORAGE_MODE=s3"
            )
        s3_path = f"s3://{settings.s3_lakehouse_bucket}/{partition_path}/{file_name}"
        fs = s3fs.S3FileSystem(client_kwargs={"region_name": settings.aws_region})
        with fs.open(s3_path, "wb") as file_obj:
            pq.write_table(table, file_obj, compression="snappy")
        return s3_path

    raise LakehouseStorageError(
        f"Unsupported STORAGE_MODE: {settings.storage_mode}. Use local or s3."
    )


# Existing Sentinel-2 function and partition contract remain unchanged.
def _build_partition_path(
    dataset: str,
    state_name: str,
    district_name: str,
    block_name: str | None,
    snapshot_date: date,
) -> str:
    return _build_generic_partition_path(
        dataset,
        {
            "state": state_name,
            "district": district_name,
            "block": block_name,
            "snapshot_date": snapshot_date.isoformat(),
        },
    )


def write_parquet_rows(
    dataset: str,
    rows: list[dict[str, Any]],
    state_name: str,
    district_name: str,
    block_name: str | None,
    snapshot_date: date,
) -> str:
    return write_partitioned_parquet_rows(
        dataset=dataset,
        rows=rows,
        partitions={
            "state": state_name,
            "district": district_name,
            "block": block_name,
            "snapshot_date": snapshot_date.isoformat(),
        },
    )
