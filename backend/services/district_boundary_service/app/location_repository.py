from sqlalchemy import text

from shared.db.postgres import engine


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.strip().split())


def list_states() -> list[dict]:
    query = text(
        """
        SELECT state_code, state_name
        FROM states
        ORDER BY state_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    return [dict(row) for row in rows]


def list_districts(state_name: str = "Odisha") -> list[dict]:
    state_name = normalize_text(state_name)

    query = text(
        """
        SELECT district_code, district_name, state_code, state_name
        FROM districts
        WHERE lower(state_name) = lower(:state_name)
        ORDER BY district_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(query, {"state_name": state_name}).mappings().all()

    return [dict(row) for row in rows]


def list_blocks_by_district(
    district_name: str,
    state_name: str = "Odisha",
) -> list[dict]:
    state_name = normalize_text(state_name)
    district_name = normalize_text(district_name)

    query = text(
        """
        SELECT
            block_code,
            block_name,
            district_code,
            district_name,
            state_code,
            state_name
        FROM blocks
        WHERE lower(state_name) = lower(:state_name)
          AND lower(district_name) = lower(:district_name)
        ORDER BY block_name;
        """
    )

    with engine.connect() as conn:
        rows = conn.execute(
            query,
            {
                "state_name": state_name,
                "district_name": district_name,
            },
        ).mappings().all()

    return [dict(row) for row in rows]


def get_service_stats() -> dict:
    query = text(
        """
        SELECT
            (SELECT COUNT(*) FROM states) AS states_count,
            (SELECT COUNT(*) FROM districts) AS districts_count,
            (SELECT COUNT(*) FROM blocks) AS blocks_count;
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query).mappings().one()

    return dict(row)


def validate_location(
    state_name: str,
    district_name: str,
    block_name: str | None = None,
    block_code: int | None = None,
) -> dict:
    state_name = normalize_text(state_name)
    district_name = normalize_text(district_name)
    block_name = normalize_text(block_name)

    district_query = text(
        """
        SELECT district_code, district_name, state_code, state_name
        FROM districts
        WHERE lower(state_name) = lower(:state_name)
          AND lower(district_name) = lower(:district_name)
        LIMIT 1;
        """
    )

    block_query = text(
        """
        SELECT block_code, block_name
        FROM blocks
        WHERE district_code = :district_code
          AND (
                (:block_code IS NOT NULL AND block_code = :block_code)
                OR
                (:block_name IS NOT NULL AND lower(block_name) = lower(:block_name))
              )
        LIMIT 1;
        """
    )

    with engine.connect() as conn:
        district = conn.execute(
            district_query,
            {
                "state_name": state_name,
                "district_name": district_name,
            },
        ).mappings().first()

        if district is None:
            return {
                "is_valid": False,
                "state_name": state_name or "",
                "district_name": district_name or "",
                "district_code": None,
                "block_name": block_name,
                "block_code": block_code,
                "message": "District not found",
            }

        if block_name is None and block_code is None:
            return {
                "is_valid": True,
                "state_name": district["state_name"],
                "district_name": district["district_name"],
                "district_code": district["district_code"],
                "block_name": None,
                "block_code": None,
                "message": "District is valid",
            }

        block = conn.execute(
            block_query,
            {
                "district_code": district["district_code"],
                "block_name": block_name,
                "block_code": block_code,
            },
        ).mappings().first()

    if block is None:
        return {
            "is_valid": False,
            "state_name": district["state_name"],
            "district_name": district["district_name"],
            "district_code": district["district_code"],
            "block_name": block_name,
            "block_code": block_code,
            "message": "Block not found in selected district",
        }

    return {
        "is_valid": True,
        "state_name": district["state_name"],
        "district_name": district["district_name"],
        "district_code": district["district_code"],
        "block_name": block["block_name"],
        "block_code": block["block_code"],
        "message": "Location is valid",
    }