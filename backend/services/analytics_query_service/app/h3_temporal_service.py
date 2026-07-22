from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from services.analytics_query_service.app.h3_temporal_engine import (
    RULE_VERSION,
    build_h3_observation,
    build_missing_h3_observation,
)
from services.analytics_query_service.app.h3_temporal_repository import (
    get_latest_valid_h3_mosaic,
    get_valid_h3_history,
)
from services.farm_registry_service.app.repository import get_farm


def _expected_h3_cells(farm: dict[str, Any] | None) -> list[int]:
    if not farm:
        return []
    return sorted({int(value) for value in (farm.get("h3_cells") or [])})


def build_latest_h3_mosaic(
    farm_id: UUID,
    *,
    as_of_date: date | None = None,
) -> dict[str, Any] | None:
    farm = get_farm(farm_id)
    if farm is None:
        return None

    expected = _expected_h3_cells(farm)
    rows = get_latest_valid_h3_mosaic(farm_id)
    rows_by_h3 = {int(row["h3_index"]): row for row in rows}

    # Preserve the farm's complete static H3 contract. A missing historical
    # value remains a visible cell with an honest waiting status.
    cell_ids = expected or sorted(rows_by_h3)
    cells = [
        build_h3_observation(rows_by_h3[h3_index], as_of_date=as_of_date)
        if h3_index in rows_by_h3
        else build_missing_h3_observation(h3_index)
        for h3_index in cell_ids
    ]

    available = [cell for cell in cells if cell["observation_date"] is not None]
    dates = [cell["observation_date"] for cell in available]
    weight_rows = [rows_by_h3[cell["h3_index"]] for cell in available]

    def weighted(field: str) -> float | None:
        usable = [
            row for row in weight_rows
            if row.get(field) is not None
            and float(row.get("valid_area_m2") or 0) > 0
        ]
        denominator = sum(float(row["valid_area_m2"]) for row in usable)
        if denominator <= 0:
            return None
        return round(
            sum(
                float(row[field]) * float(row["valid_area_m2"])
                for row in usable
            ) / denominator,
            6,
        )

    return {
        "farm_id": farm_id,
        "analysis_mode": "per_h3_latest_valid_temporal_mosaic",
        "rule_version": RULE_VERSION,
        "h3_valid_fraction_threshold": 0.20,
        "total_h3_cells": len(cells),
        "h3_cells_with_valid_history": len(available),
        "h3_cells_waiting_for_valid_observation": len(cells) - len(available),
        "historical_cell_coverage_percent": round(
            len(available) / len(cells) * 100.0,
            2,
        ) if cells else 0.0,
        "newest_cell_observation_date": max(dates) if dates else None,
        "oldest_cell_observation_date": min(dates) if dates else None,
        "mosaic_date_span_days": (
            (max(dates) - min(dates)).days if dates else None
        ),
        # Informational only; never used to overwrite the individual cells.
        "farm_weighted_information": {
            "weighted_ndvi": weighted("ndvi"),
            "weighted_ndmi": weighted("ndmi"),
            "weighted_bsi": weighted("bsi"),
            "weighted_fvc_proxy": weighted("fvc_proxy"),
            "weighted_nirv": weighted("nirv"),
            "warning": (
                "This summary combines each H3 cell's latest valid value and "
                "may mix observation dates. Use cell results for decisions."
            ),
        },
        "priority_counts": {
            key: sum(1 for cell in cells if cell["action_priority"] == key)
            for key in {
                "inspect_first",
                "inspect",
                "watch",
                "normal_monitoring",
                "awaiting_observation",
            }
        },
        "cells": cells,
    }


def build_h3_history(
    farm_id: UUID,
    h3_index: int,
    limit: int,
) -> dict[str, Any]:
    rows = get_valid_h3_history(farm_id, h3_index, limit)
    return {
        "farm_id": farm_id,
        "h3_index": h3_index,
        "item_count": len(rows),
        "items": rows,
    }