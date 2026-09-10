"""Release expired, never-completed media upload tickets.

Safe to run periodically (for example every hour). It only touches REQUESTED
rows whose upload window has expired. Observation-media links are removed so
photo slots can be reused. Any object that happens to exist is deleted from the
row's recorded storage backend before the row is marked REJECTED.

    python -m services.crop_observation_service.scripts.cleanup_expired_uploads
"""

from __future__ import annotations

from sqlalchemy import text

from shared.db.postgres import engine
from services.crop_observation_service.app.storage import backend_for


def _expired(table: str, id_column: str):
    with engine.connect() as conn:
        return conn.execute(
            text(
                f"""
                SELECT {id_column} AS asset_id, object_key, storage_backend
                FROM crop_observation.{table}
                WHERE upload_status = 'REQUESTED'
                  AND COALESCE(upload_expires_at, created_at + interval '15 minutes') <= now()
                ORDER BY created_at
                LIMIT 1000;
                """
            )
        ).mappings().all()


def _cleanup_farmer() -> int:
    rows = _expired("media_assets", "media_asset_id")
    count = 0
    for row in rows:
        try:
            backend_for(row["storage_backend"]).delete(object_key=row["object_key"])
        except Exception as exc:
            print(f"WARN delete failed {row['object_key']}: {exc}")
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM crop_observation.observation_media WHERE media_asset_id = :asset_id"),
                {"asset_id": row["asset_id"]},
            )
            conn.execute(
                text(
                    """
                    UPDATE crop_observation.media_assets
                    SET upload_status = 'REJECTED', updated_at = now()
                    WHERE media_asset_id = :asset_id
                      AND upload_status = 'REQUESTED'
                    """
                ),
                {"asset_id": row["asset_id"]},
            )
        count += 1
    return count


def _cleanup_system() -> int:
    rows = _expired("system_media_assets", "asset_id")
    count = 0
    for row in rows:
        try:
            backend_for(row["storage_backend"]).delete(object_key=row["object_key"])
        except Exception as exc:
            print(f"WARN delete failed {row['object_key']}: {exc}")
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM crop_observation.system_media_bindings WHERE asset_id = :asset_id"),
                {"asset_id": row["asset_id"]},
            )
            conn.execute(
                text(
                    """
                    UPDATE crop_observation.system_media_assets
                    SET upload_status = 'REJECTED', is_active = false, updated_at = now()
                    WHERE asset_id = :asset_id
                      AND upload_status = 'REQUESTED'
                    """
                ),
                {"asset_id": row["asset_id"]},
            )
        count += 1
    return count


def main() -> None:
    farmer = _cleanup_farmer()
    system = _cleanup_system()
    print(f"Expired uploads cleaned: farmer={farmer}, system={system}")


if __name__ == "__main__":
    main()
