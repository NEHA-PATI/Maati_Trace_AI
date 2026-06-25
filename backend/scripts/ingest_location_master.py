import csv
from pathlib import Path

from sqlalchemy import text

from shared.db.postgres import engine

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_DIR = BASE_DIR / "data_contracts" / "csv"

STATES_CSV = CSV_DIR / "states.csv"
DISTRICTS_CSV = CSV_DIR / "districts.csv"
BLOCKS_CSV = CSV_DIR / "blocks.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().split())


def ingest_states() -> None:
    rows = read_csv(STATES_CSV)

    query = text(
        """
        INSERT INTO states (state_code, state_name)
        VALUES (:state_code, :state_name)
        ON CONFLICT (state_code)
        DO UPDATE SET
            state_name = EXCLUDED.state_name;
        """
    )

    payload = []
    seen_codes = set()

    for row in rows:
        state_code = int(row["state_code"])
        state_name = normalize_text(row["state_name"])

        if state_code in seen_codes:
            raise ValueError(f"Duplicate state_code found: {state_code}")

        if not state_name:
            raise ValueError(f"Empty state_name for state_code: {state_code}")

        seen_codes.add(state_code)

        payload.append(
            {
                "state_code": state_code,
                "state_name": state_name,
            }
        )

    with engine.begin() as conn:
        conn.execute(query, payload)

    print(f"Inserted/updated states: {len(payload)}")


def ingest_districts() -> None:
    rows = read_csv(DISTRICTS_CSV)

    query = text(
        """
        INSERT INTO districts (
            district_code,
            district_name,
            state_code,
            state_name
        )
        SELECT
            :district_code,
            :district_name,
            s.state_code,
            s.state_name
        FROM states s
        WHERE lower(s.state_name) = lower(:state_name)
        ON CONFLICT (district_code)
        DO UPDATE SET
            district_name = EXCLUDED.district_name,
            state_code = EXCLUDED.state_code,
            state_name = EXCLUDED.state_name;
        """
    )

    payload = []
    seen_codes = set()

    for row in rows:
        district_code = int(row["district_code"])
        district_name = normalize_text(row["district_name"])
        state_name = normalize_text(row["state_name"])

        if district_code in seen_codes:
            raise ValueError(f"Duplicate district_code found: {district_code}")

        if not district_name:
            raise ValueError(f"Empty district_name for district_code: {district_code}")

        if not state_name:
            raise ValueError(f"Empty state_name for district_code: {district_code}")

        seen_codes.add(district_code)

        payload.append(
            {
                "district_code": district_code,
                "district_name": district_name,
                "state_name": state_name,
            }
        )

    with engine.begin() as conn:
        conn.execute(query, payload)

    print(f"Inserted/updated districts: {len(payload)}")


def ingest_blocks() -> None:
    rows = read_csv(BLOCKS_CSV)

    query = text(
        """
        INSERT INTO blocks (
            block_code,
            block_name,
            district_code,
            district_name,
            state_code,
            state_name
        )
        SELECT
            :block_code,
            :block_name,
            d.district_code,
            d.district_name,
            d.state_code,
            d.state_name
        FROM districts d
        WHERE lower(d.district_name) = lower(:district_name)
          AND lower(d.state_name) = lower(:state_name)
        ON CONFLICT (block_code)
        DO UPDATE SET
            block_name = EXCLUDED.block_name,
            district_code = EXCLUDED.district_code,
            district_name = EXCLUDED.district_name,
            state_code = EXCLUDED.state_code,
            state_name = EXCLUDED.state_name;
        """
    )

    payload = []
    seen_codes = set()

    for row in rows:
        block_code = int(row["block_code"])
        block_name = normalize_text(row["block_name"])
        district_name = normalize_text(row["district_name"])

        if block_code in seen_codes:
            raise ValueError(f"Duplicate block_code found: {block_code}")

        if not block_name:
            raise ValueError(f"Empty block_name for block_code: {block_code}")

        if not district_name:
            raise ValueError(f"Empty district_name for block_code: {block_code}")

        seen_codes.add(block_code)

        payload.append(
            {
                "block_code": block_code,
                "block_name": block_name,
                "district_name": district_name,
                "state_name": "Odisha",
            }
        )

    with engine.begin() as conn:
        conn.execute(query, payload)

    print(f"Inserted/updated blocks: {len(payload)}")


def validate_ingestion() -> None:
    queries = {
        "states": "SELECT COUNT(*) FROM states;",
        "districts": "SELECT COUNT(*) FROM districts;",
        "blocks": "SELECT COUNT(*) FROM blocks;",
        "orphan_blocks": """
            SELECT COUNT(*)
            FROM blocks b
            LEFT JOIN districts d ON b.district_code = d.district_code
            WHERE d.district_code IS NULL;
        """,
    }

    with engine.connect() as conn:
        for name, sql in queries.items():
            count = conn.execute(text(sql)).scalar_one()
            print(f"{name}: {count}")

        invalid_blocks = conn.execute(
            text(
                """
                SELECT block_code, block_name, district_name
                FROM blocks
                WHERE district_code IS NULL
                ORDER BY block_code;
                """
            )
        ).mappings().all()

    if invalid_blocks:
        raise ValueError(f"Blocks without district mapping found: {invalid_blocks}")

    print("Location master ingestion validation passed")


def main() -> None:
    ingest_states()
    ingest_districts()
    ingest_blocks()
    validate_ingestion()


if __name__ == "__main__":
    main()