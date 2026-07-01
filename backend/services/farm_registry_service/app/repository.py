from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.db.postgres import engine


class FarmRegistryRepositoryError(ValueError):
    pass


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def validate_fpo_exists(fpo_id: UUID | str | None) -> None:
    if fpo_id is None:
        return

    query = text(
        """
        SELECT fpo_id
        FROM fpos
        WHERE fpo_id = :fpo_id
          AND is_active = TRUE
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().first()

    if row is None:
        raise FarmRegistryRepositoryError(
            f"FPO not found or inactive: {fpo_id}. Create FPO first or send fpo_id as null."
        )


def validate_user_exists(user_id: UUID | str | None) -> None:
    if user_id is None:
        return

    query = text(
        """
        SELECT user_id
        FROM users
        WHERE user_id = :user_id
          AND is_active = TRUE
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()

    if row is None:
        raise FarmRegistryRepositoryError(
            f"User not found or inactive: {user_id}. Create the user first or send user_id as null."
        )


def get_farmer_for_write(farmer_id: UUID | str) -> dict:
    query = text(
        """
        SELECT
            farmer_id,
            user_id,
            fpo_id,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active
        FROM farmer_profiles
        WHERE farmer_id = :farmer_id
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().first()

    if row is None or not row["is_active"]:
        raise FarmRegistryRepositoryError(f"Farmer not found or inactive: {farmer_id}")

    return dict(row)


def create_fpo(data: dict[str, Any]) -> dict:
    validate_user_exists(data.get("user_id"))

    payload = data.copy()
    payload["user_id"] = str(payload["user_id"]) if payload.get("user_id") else None
    payload["fpo_user_role"] = normalize_text(payload.get("fpo_user_role")) or "fpo_admin"
    payload["fpo_name"] = normalize_text(payload.get("fpo_name"))
    payload["registration_number"] = normalize_text(payload.get("registration_number"))
    payload["state_name"] = normalize_text(payload.get("state_name")) or "Odisha"
    payload["district_name"] = normalize_text(payload.get("district_name"))
    payload["block_name"] = normalize_text(payload.get("block_name"))
    payload["contact_phone"] = normalize_text(payload.get("contact_phone"))
    payload["contact_email"] = normalize_text(payload.get("contact_email"))

    if not payload["fpo_name"]:
        raise FarmRegistryRepositoryError("FPO name is required")

    if not payload["district_name"]:
        raise FarmRegistryRepositoryError("District name is required")

    find_existing_query = text(
        """
        SELECT fpo_id
        FROM fpos
        WHERE registration_number = :registration_number
          AND registration_number IS NOT NULL
        LIMIT 1;
        """
    )

    update_query = text(
        """
        UPDATE fpos
        SET
            fpo_name = :fpo_name,
            state_name = :state_name,
            district_name = :district_name,
            block_name = :block_name,
            block_code = :block_code,
            contact_phone = :contact_phone,
            contact_email = :contact_email,
            is_active = TRUE,
            updated_at = now()
        WHERE fpo_id = :fpo_id
        RETURNING
            fpo_id,
            fpo_name,
            registration_number,
            state_name,
            district_name,
            block_name,
            block_code,
            contact_phone,
            contact_email,
            is_active;
        """
    )

    insert_query = text(
        """
        INSERT INTO fpos (
            fpo_name,
            registration_number,
            state_name,
            district_name,
            block_name,
            block_code,
            contact_phone,
            contact_email
        )
        VALUES (
            :fpo_name,
            :registration_number,
            :state_name,
            :district_name,
            :block_name,
            :block_code,
            :contact_phone,
            :contact_email
        )
        RETURNING
            fpo_id,
            fpo_name,
            registration_number,
            state_name,
            district_name,
            block_name,
            block_code,
            contact_phone,
            contact_email,
            is_active;
        """
    )

    link_user_query = text(
        """
        INSERT INTO fpo_users (
            fpo_id,
            user_id,
            role,
            is_active
        )
        VALUES (
            :fpo_id,
            :user_id,
            :fpo_user_role,
            TRUE
        )
        ON CONFLICT (fpo_id, user_id)
        DO UPDATE SET
            role = EXCLUDED.role,
            is_active = TRUE,
            updated_at = now();
        """
    )

    try:
        with engine.begin() as conn:
            existing_fpo = None

            if payload["registration_number"]:
                existing_fpo = conn.execute(
                    find_existing_query,
                    {"registration_number": payload["registration_number"]},
                ).mappings().first()

            if existing_fpo:
                payload["fpo_id"] = str(existing_fpo["fpo_id"])
                row = conn.execute(update_query, payload).mappings().one()
            else:
                row = conn.execute(insert_query, payload).mappings().one()

            if payload.get("user_id"):
                conn.execute(
                    link_user_query,
                    {
                        "fpo_id": str(row["fpo_id"]),
                        "user_id": payload["user_id"],
                        "fpo_user_role": payload["fpo_user_role"],
                    },
                )
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to create FPO: {exc}") from exc

    return dict(row)


def get_fpo(fpo_id: UUID) -> dict | None:
    query = text(
        """
        SELECT
            fpo_id,
            fpo_name,
            registration_number,
            state_name,
            district_name,
            block_name,
            block_code,
            contact_phone,
            contact_email,
            is_active
        FROM fpos
        WHERE fpo_id = :fpo_id
          AND is_active = TRUE;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().first()

    return dict(row) if row else None


def list_fpos() -> list[dict]:
    query = text(
        """
        SELECT
            fpo_id,
            fpo_name,
            registration_number,
            state_name,
            district_name,
            block_name,
            block_code,
            contact_phone,
            contact_email,
            is_active
        FROM fpos
        WHERE is_active = TRUE
        ORDER BY fpo_name ASC;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return [dict(row) for row in rows]


def get_fpo_by_user(user_id: UUID | str) -> dict | None:
    query = text(
        """
        SELECT
            f.fpo_id,
            f.fpo_name,
            f.registration_number,
            f.state_name,
            f.district_name,
            f.block_name,
            f.block_code,
            f.contact_phone,
            f.contact_email,
            f.is_active
        FROM fpo_users fu
        JOIN fpos f ON f.fpo_id = fu.fpo_id
        WHERE fu.user_id = :user_id
          AND fu.is_active = TRUE
          AND f.is_active = TRUE
        ORDER BY fu.created_at DESC
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()
    return dict(row) if row else None


def create_farmer(data: dict[str, Any]) -> dict:
    validate_user_exists(data.get("user_id"))
    validate_fpo_exists(data.get("fpo_id"))

    existing_by_user_query = text(
        """
        SELECT farmer_id
        FROM farmer_profiles
        WHERE user_id = :user_id
        LIMIT 1;
        """
    )

    update_query = text(
        """
        UPDATE farmer_profiles
        SET
            fpo_id = :fpo_id,
            full_name = :full_name,
            phone_number = :phone_number,
            gender = :gender,
            state_name = :state_name,
            district_name = :district_name,
            district_code = :district_code,
            block_name = :block_name,
            block_code = :block_code,
            village_name = :village_name,
            is_active = TRUE
        WHERE farmer_id = :farmer_id
        RETURNING
            farmer_id,
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active;
        """
    )

    insert_query = text(
        """
        INSERT INTO farmer_profiles (
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name
        )
        VALUES (
            :user_id,
            :fpo_id,
            :full_name,
            :phone_number,
            :gender,
            :state_name,
            :district_name,
            :district_code,
            :block_name,
            :block_code,
            :village_name
        )
        RETURNING
            farmer_id,
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active;
        """
    )

    payload = data.copy()
    payload["user_id"] = str(payload["user_id"]) if payload.get("user_id") else None
    payload["fpo_id"] = str(payload["fpo_id"]) if payload.get("fpo_id") else None
    payload["full_name"] = normalize_text(payload.get("full_name"))
    payload["phone_number"] = normalize_text(payload.get("phone_number"))
    payload["gender"] = normalize_text(payload.get("gender"))
    payload["state_name"] = normalize_text(payload.get("state_name")) or "Odisha"
    payload["district_name"] = normalize_text(payload.get("district_name"))
    payload["block_name"] = normalize_text(payload.get("block_name"))
    payload["village_name"] = normalize_text(payload.get("village_name"))

    if not payload["full_name"]:
        raise FarmRegistryRepositoryError("Farmer full name is required")

    if not payload["district_name"]:
        raise FarmRegistryRepositoryError("District name is required")

    try:
        with engine.begin() as conn:
            existing_by_user = None

            if payload.get("user_id"):
                existing_by_user = conn.execute(
                    existing_by_user_query,
                    {"user_id": payload["user_id"]},
                ).mappings().first()

            if existing_by_user:
                payload["farmer_id"] = str(existing_by_user["farmer_id"])
                row = conn.execute(update_query, payload).mappings().one()
            else:
                row = conn.execute(insert_query, payload).mappings().one()
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to create farmer: {exc}") from exc

    return dict(row)


def get_farmer(farmer_id: UUID) -> dict | None:
    query = text(
        """
        SELECT
            farmer_id,
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active
        FROM farmer_profiles
        WHERE farmer_id = :farmer_id
          AND is_active = TRUE;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().first()

    return dict(row) if row else None


def get_farmer_by_user_id(user_id: UUID | str) -> dict | None:
    query = text(
        """
        SELECT
            farmer_id,
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active
        FROM farmer_profiles
        WHERE user_id = :user_id
          AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": str(user_id)}).mappings().first()
    return dict(row) if row else None


def get_farmer_by_user(user_id: UUID | str) -> dict | None:
    return get_farmer_by_user_id(user_id)


def create_farm(data: dict[str, Any]) -> dict:
    farmer = get_farmer_for_write(data["farmer_id"])
    validate_fpo_exists(data.get("fpo_id"))

    query = text(
        """
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
            CAST(:polygon_geojson AS JSONB),
            :h3_resolution,
            :h3_cells,
            :h3_cell_count,
            :area_acres,
            CAST(:bbox AS JSONB)
        )
        RETURNING
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
            polygon_geojson,
            h3_resolution,
            h3_cell_count,
            area_acres,
            bbox,
            is_active;
        """
    )

    payload = data.copy()
    payload["farmer_id"] = str(payload["farmer_id"])
    payload["fpo_id"] = str(payload["fpo_id"]) if payload.get("fpo_id") else None
    payload["farm_name"] = normalize_text(payload.get("farm_name"))
    payload["survey_number"] = normalize_text(payload.get("survey_number"))
    payload["state_name"] = normalize_text(payload.get("state_name")) or "Odisha"
    payload["district_name"] = normalize_text(payload.get("district_name"))
    payload["block_name"] = normalize_text(payload.get("block_name"))
    payload["village_name"] = normalize_text(payload.get("village_name"))

    farmer_fpo_id = str(farmer["fpo_id"]) if farmer.get("fpo_id") else None
    if payload["fpo_id"] is None and farmer_fpo_id is not None:
        payload["fpo_id"] = farmer_fpo_id
    elif payload["fpo_id"] is not None and farmer_fpo_id is not None and payload["fpo_id"] != farmer_fpo_id:
        raise FarmRegistryRepositoryError(
            "Farm FPO does not match the farmer's assigned FPO"
        )

    try:
        with engine.begin() as conn:
            row = conn.execute(query, payload).mappings().one()
    except SQLAlchemyError as exc:
        raise FarmRegistryRepositoryError(f"Failed to create farm: {exc}") from exc

    return dict(row)


def get_farm(farm_id: UUID) -> dict | None:
    query = text(
        """
        SELECT
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
            polygon_geojson,
            h3_resolution,
            h3_cell_count,
            area_acres,
            bbox,
            is_active
        FROM farms
        WHERE farm_id = :farm_id
          AND is_active = TRUE;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query, {"farm_id": str(farm_id)}).mappings().first()

    return dict(row) if row else None


def list_farms_by_farmer(farmer_id: UUID) -> list[dict]:
    query = text(
        """
        SELECT
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
            polygon_geojson,
            h3_resolution,
            h3_cell_count,
            area_acres,
            bbox,
            is_active
        FROM farms
        WHERE farmer_id = :farmer_id
          AND is_active = TRUE
        ORDER BY created_at DESC;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().all()

    return [dict(row) for row in rows]


def list_farms(
    fpo_id: UUID | str | None = None,
    farmer_id: UUID | str | None = None,
    district_name: str | None = None,
    block_name: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict]:
    where_clauses = ["is_active = TRUE"]
    params: dict[str, Any] = {}

    if fpo_id is not None:
        where_clauses.append("fpo_id = :fpo_id")
        params["fpo_id"] = str(fpo_id)
    if farmer_id is not None:
        where_clauses.append("farmer_id = :farmer_id")
        params["farmer_id"] = str(farmer_id)
    if district_name:
        where_clauses.append("district_name = :district_name")
        params["district_name"] = normalize_text(district_name)
    if block_name:
        where_clauses.append("block_name = :block_name")
        params["block_name"] = normalize_text(block_name)

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT :limit"
        params["limit"] = int(limit)
        if offset is not None:
            limit_clause += " OFFSET :offset"
            params["offset"] = int(offset)

    query = text(
        f"""
        SELECT
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
            polygon_geojson,
            h3_resolution,
            h3_cell_count,
            area_acres,
            bbox,
            is_active
        FROM farms
        WHERE {" AND ".join(where_clauses)}
        ORDER BY created_at DESC
        {limit_clause};
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    return [dict(row) for row in rows]


def list_farmers_by_fpo(fpo_id: UUID | str) -> list[dict]:
    query = text(
        """
        SELECT
            farmer_id,
            user_id,
            fpo_id,
            full_name,
            phone_number,
            gender,
            state_name,
            district_name,
            district_code,
            block_name,
            block_code,
            village_name,
            is_active
        FROM farmer_profiles
        WHERE fpo_id = :fpo_id
          AND is_active = TRUE
        ORDER BY full_name ASC;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def list_farms_by_fpo(fpo_id: UUID | str) -> list[dict]:
    query = text(
        """
        SELECT
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
            polygon_geojson,
            h3_resolution,
            h3_cell_count,
            area_acres,
            bbox,
            is_active
        FROM farms
        WHERE fpo_id = :fpo_id
          AND is_active = TRUE
        ORDER BY created_at DESC;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().all()
    return [dict(row) for row in rows]


def get_fpo_summary(fpo_id: UUID | str) -> dict:
    query = text(
        """
        SELECT
            :fpo_id AS fpo_id,
            COUNT(DISTINCT fp.farmer_id) AS farmer_count,
            COUNT(DISTINCT fm.farm_id) AS farm_count,
            COALESCE(SUM(fm.area_acres), 0) AS total_area_acres
        FROM fpos f
        LEFT JOIN farmer_profiles fp ON fp.fpo_id = f.fpo_id AND fp.is_active = TRUE
        LEFT JOIN farms fm ON fm.fpo_id = f.fpo_id AND fm.is_active = TRUE
        WHERE f.fpo_id = :fpo_id
          AND f.is_active = TRUE
        GROUP BY f.fpo_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"fpo_id": str(fpo_id)}).mappings().first()
    return dict(row) if row else {"fpo_id": str(fpo_id), "farmer_count": 0, "farm_count": 0, "total_area_acres": 0}


def get_farmer_summary(farmer_id: UUID | str) -> dict:
    query = text(
        """
        SELECT
            :farmer_id AS farmer_id,
            COUNT(f.farm_id) AS farm_count,
            COALESCE(SUM(f.area_acres), 0) AS total_area_acres,
            MAX(f.state_name) AS state_name,
            MAX(f.district_name) AS district_name,
            MAX(f.block_name) AS block_name
        FROM farms f
        WHERE f.farmer_id = :farmer_id
          AND f.is_active = TRUE
        GROUP BY f.farmer_id;
        """
    )
    with engine.connect() as conn:
        row = conn.execute(query, {"farmer_id": str(farmer_id)}).mappings().first()
    return dict(row) if row else {"farmer_id": str(farmer_id), "farm_count": 0, "total_area_acres": 0, "state_name": None, "district_name": None, "block_name": None}
