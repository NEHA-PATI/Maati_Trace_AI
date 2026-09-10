from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine
from services.farm_registry_service.app.errors import FarmRegistryRepositoryError

FARM_SELECT = """
    farm_id,
    farmer_id,
    fpo_id,
    farm_name,
    survey_number,
    state_name,
    district_name,
    district_code,
    block_name,
    block_code,
    village_name,
    crop_code,
    crop_name,
    crop_variety,
    crop_stage,
    planting_date,
    polygon_geojson,
    h3_resolution,
    h3_cell_count,
    area_acres,
    bbox,
    is_active,
    created_at,
    updated_at
"""


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).strip().split())
    return cleaned or None


def get_active_crop_registration_option(crop_code: str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT p.crop_code, p.crop_name, p.profile_version, p.crop_type
        FROM crop_feature_profiles p
        WHERE p.crop_code = :crop_code
          AND p.status = 'published'
          AND p.is_active = TRUE
          AND EXISTS (
              SELECT 1
              FROM crop_formula_registry f
              WHERE f.crop_code = p.crop_code
                AND f.crop_profile_version = p.profile_version
                AND f.status = 'published'
                AND f.is_active = TRUE
          )
        LIMIT 1;
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"crop_code": _normalize_text(crop_code)}).mappings().first()
        return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to validate farm crop: {exc}") from exc


def create_farm(data: dict[str, Any]) -> dict[str, Any]:
    query = text(
        f"""
        INSERT INTO farms (
            farmer_id,
            fpo_id,
            farm_name,
            survey_number,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            crop_code,
            crop_name,
            crop_variety,
            crop_stage,
            planting_date,
            polygon_geojson,
            h3_resolution,
            h3_cells,
            h3_cell_count,
            area_acres,
            bbox
        )
        VALUES (
            :farmer_id,
            :fpo_id,
            :farm_name,
            :survey_number,
            :state_name,
            :district_name,
            :district_code,
            :block_name,
            :block_code,
            :village_name,
            :crop_code,
            :crop_name,
            :crop_variety,
            :crop_stage,
            :planting_date,
            CAST(:polygon_geojson AS jsonb),
            :h3_resolution,
            CAST(:h3_cells AS bigint[]),
            :h3_cell_count,
            :area_acres,
            CAST(:bbox AS jsonb)
        )
        RETURNING {FARM_SELECT};
        """
    )
    payload = {
        "farmer_id": str(data["farmer_id"]),
        "fpo_id": str(data["fpo_id"]) if data.get("fpo_id") else None,
        "farm_name": _normalize_text(data.get("farm_name")),
        "survey_number": _normalize_text(data.get("survey_number")),
        "state_name": _normalize_text(data.get("state_name")) or "Odisha",
        "district_name": _normalize_text(data.get("district_name")),
        "district_code": data.get("district_code"),
        "block_name": _normalize_text(data.get("block_name")),
        "block_code": data.get("block_code"),
        "village_name": _normalize_text(data.get("village_name")),
        "crop_code": _normalize_text(data.get("crop_code")),
        "crop_name": _normalize_text(data.get("crop_name")),
        "crop_variety": _normalize_text(data.get("crop_variety")),
        "crop_stage": _normalize_text(data.get("crop_stage")),
        "planting_date": data.get("planting_date"),
        "polygon_geojson": json.dumps(data["polygon_geojson"]),
        "h3_resolution": data["h3_resolution"],
        "h3_cells": list(data["h3_cells"]),
        "h3_cell_count": data["h3_cell_count"],
        "area_acres": data.get("area_acres"),
        "bbox": json.dumps(data.get("bbox")),
    }
    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().one()
            return dict(row)
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to create farm: {exc}") from exc


def get_farm(farm_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        f"""
        SELECT {FARM_SELECT}
        FROM farms
        WHERE farm_id = :farm_id
          AND is_active = TRUE
        LIMIT 1;
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()
            return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to read farm: {exc}") from exc


def get_complete_farm(farm_id: UUID | str) -> dict[str, Any] | None:
    query = text(
        f"""
        SELECT
            {FARM_SELECT},
            h3_cells
        FROM farms
        WHERE farm_id = :farm_id
          AND is_active = TRUE
        LIMIT 1;
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()
            return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to read complete farm: {exc}") from exc


def list_farms(
    *,
    fpo_id: UUID | str | None = None,
    farmer_id: UUID | str | None = None,
    district_name: str | None = None,
    block_name: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    where = ["is_active = TRUE"]
    params: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }
    if fpo_id is not None:
        where.append("fpo_id = :fpo_id")
        params["fpo_id"] = str(fpo_id)
    if farmer_id is not None:
        where.append("farmer_id = :farmer_id")
        params["farmer_id"] = str(farmer_id)
    if district_name:
        where.append("district_name = :district_name")
        params["district_name"] = _normalize_text(district_name)
    if block_name:
        where.append("block_name = :block_name")
        params["block_name"] = _normalize_text(block_name)

    query = text(
        f"""
        SELECT {FARM_SELECT}
        FROM farms
        WHERE {" AND ".join(where)}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset;
        """
    )
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to list farms: {exc}") from exc


def list_farms_by_farmer(farmer_id: UUID | str) -> list[dict[str, Any]]:
    return list_farms(farmer_id=farmer_id)


def list_farms_by_fpo(fpo_id: UUID | str) -> list[dict[str, Any]]:
    return list_farms(fpo_id=fpo_id)


def get_farmer_summary(farmer_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            CAST(:farmer_id AS uuid) AS farmer_id,
            COUNT(farm_id)::integer AS farm_count,
            COALESCE(SUM(area_acres), 0)::numeric AS total_area_acres,
            MAX(state_name) AS state_name,
            MAX(district_name) AS district_name,
            MAX(block_name) AS block_name
        FROM farms
        WHERE farmer_id = :farmer_id
          AND is_active = TRUE;
        """
    )
    try:
        with engine.connect() as conn:
            return dict(conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().one())
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to read farmer farm summary: {exc}") from exc


def get_fpo_summary(fpo_id: UUID | str) -> dict[str, Any]:
    query = text(
        """
        SELECT
            CAST(:fpo_id AS uuid) AS fpo_id,
            COUNT(DISTINCT farmer_id)::integer AS farmer_count,
            COUNT(farm_id)::integer AS farm_count,
            COALESCE(SUM(area_acres), 0)::numeric AS total_area_acres
        FROM farms
        WHERE fpo_id = :fpo_id
          AND is_active = TRUE;
        """
    )
    try:
        with engine.connect() as conn:
            return dict(conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().one())
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to read FPO farm summary: {exc}") from exc


def update_farm_derived_fields(
    farm_id: UUID | str,
    *,
    district_code: int | None = None,
    block_code: int | None = None,
    h3_resolution: int | None = None,
    h3_cells: list[int] | None = None,
    h3_cell_count: int | None = None,
    area_acres: float | None = None,
    bbox: list[float] | None = None,
) -> dict[str, Any] | None:
    query = text(
        f"""
        UPDATE farms
        SET
            district_code = COALESCE(:district_code, district_code),
            block_code = COALESCE(:block_code, block_code),
            h3_resolution = COALESCE(:h3_resolution, h3_resolution),
            h3_cells = COALESCE(CAST(:h3_cells AS bigint[]), h3_cells),
            h3_cell_count = COALESCE(:h3_cell_count, h3_cell_count),
            area_acres = COALESCE(:area_acres, area_acres),
            bbox = COALESCE(CAST(:bbox AS jsonb), bbox),
            updated_at = now()
        WHERE farm_id = :farm_id
          AND is_active = TRUE
        RETURNING {FARM_SELECT};
        """
    )
    payload = {
        "farm_id": str(farm_id),
        "district_code": district_code,
        "block_code": block_code,
        "h3_resolution": h3_resolution,
        "h3_cells": h3_cells,
        "h3_cell_count": h3_cell_count,
        "area_acres": area_acres,
        "bbox": json.dumps(bbox) if bbox is not None else None,
    }
    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().first()
            return dict(row) if row else None
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to update farm derived fields: {exc}") from exc
