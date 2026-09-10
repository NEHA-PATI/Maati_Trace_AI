"""Copy READY Crop Observation media from LOCAL storage to the configured S3 bucket.

Run from the backend root so `services` and `shared` resolve:

    # Keep MEDIA_STORAGE_BACKEND=LOCAL while copying. Only the S3 bucket/AWS
    # credentials/role must be configured.
    python -m services.crop_observation_service.scripts.migrate_local_media_to_s3 --dry-run
    python -m services.crop_observation_service.scripts.migrate_local_media_to_s3

The DB row is switched to S3 only after upload + HEAD verification succeeds.
Local files are deliberately retained as rollback copies. Delete them later
through your normal deployment/backup process after production verification.
"""

from __future__ import annotations

import argparse

from sqlalchemy import text

from shared.config.settings import settings
from shared.db.postgres import engine
from services.crop_observation_service.app.storage import local as local_storage
from services.crop_observation_service.app.storage import s3 as s3_storage


def _rows(table: str, id_column: str):
    with engine.connect() as conn:
        return conn.execute(
            text(
                f"""
                SELECT {id_column} AS asset_id, object_key, mime_type, byte_size
                FROM crop_observation.{table}
                WHERE storage_backend = 'LOCAL'
                  AND upload_status = 'READY'
                ORDER BY created_at;
                """
            )
        ).mappings().all()


def _migrate(table: str, id_column: str, *, dry_run: bool) -> tuple[int, int]:
    moved = 0
    skipped = 0
    for row in _rows(table, id_column):
        key = row["object_key"]
        local_head = local_storage.head_object(object_key=key)
        if local_head is None:
            print(f"MISSING  {table:<20} {key}")
            skipped += 1
            continue

        print(f"{'PLAN' if dry_run else 'COPY'}     {table:<20} {key}")
        if dry_run:
            moved += 1
            continue

        data = local_storage.read_bytes(object_key=key)
        s3_storage.put_bytes(object_key=key, data=data, mime_type=row["mime_type"])
        head = s3_storage.head_object(object_key=key)
        if head is None or int(head.get("ContentLength") or -1) != len(data):
            raise RuntimeError(f"S3 verification failed for {key}")

        with engine.begin() as conn:
            conn.execute(
                text(
                    f"""
                    UPDATE crop_observation.{table}
                    SET storage_backend = 'S3',
                        bucket_name = :bucket_name,
                        updated_at = now()
                    WHERE {id_column} = :asset_id
                      AND storage_backend = 'LOCAL';
                    """
                ),
                {
                    "bucket_name": settings.crop_observation_s3_bucket,
                    "asset_id": row["asset_id"],
                },
            )
        moved += 1

    return moved, skipped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--system-only", action="store_true")
    parser.add_argument("--farmer-only", action="store_true")
    args = parser.parse_args()

    if args.system_only and args.farmer_only:
        raise SystemExit("Choose at most one of --system-only / --farmer-only")
    if not settings.crop_observation_s3_bucket:
        raise SystemExit("CROP_OBSERVATION_S3_BUCKET is required")

    total_moved = total_skipped = 0
    if not args.farmer_only:
        moved, skipped = _migrate("system_media_assets", "asset_id", dry_run=args.dry_run)
        total_moved += moved
        total_skipped += skipped
    if not args.system_only:
        moved, skipped = _migrate("media_assets", "media_asset_id", dry_run=args.dry_run)
        total_moved += moved
        total_skipped += skipped

    print(
        f"Done. {'planned' if args.dry_run else 'migrated'}={total_moved} "
        f"missing/skipped={total_skipped} bucket={settings.crop_observation_s3_bucket}"
    )


if __name__ == "__main__":
    main()
