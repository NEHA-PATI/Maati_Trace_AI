"""Seed system instruction-audio metadata for an existing S3 bucket.

This script never reads or uploads local media. It only verifies the manifest
objects exist in S3, then creates the database asset rows and bindings needed
by the API to return playable presigned URLs.
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from sqlalchemy import text

from shared.config.settings import settings
from shared.db.postgres import engine
from services.crop_observation_service.app.storage import s3 as s3_storage

SERVICE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SERVICE_ROOT / "media_manifest.json"


def main() -> None:
    if not settings.crop_observation_s3_bucket:
        raise SystemExit("CROP_OBSERVATION_S3_BUCKET is required")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    audio = [item for item in manifest["assets"] if item["asset_type"] == "STAGE_INSTRUCTION_AUDIO"]
    seeded = 0
    skipped = 0

    with engine.begin() as conn:
        for item in audio:
            key = item.get("object_key") or item["file"]
            head = s3_storage.head_object(object_key=key)
            if not head:
                print(f"MISSING_S3 {key}")
                skipped += 1
                continue

            crop = conn.execute(
                text("SELECT crop_id FROM crop_observation.crops WHERE crop_code = :code"),
                {"code": item["crop_code"]},
            ).mappings().first()
            if not crop:
                print(f"MISSING_CROP {item['crop_code']} {key}")
                skipped += 1
                continue

            stage = conn.execute(
                text(
                    """
                    SELECT s.stage_id
                    FROM crop_observation.crop_stages s
                    JOIN crop_observation.crop_config_versions cv
                      ON cv.config_version_id = s.config_version_id
                    WHERE cv.crop_id = :crop_id
                      AND cv.status = 'PUBLISHED'
                      AND s.stage_code = :stage_code
                    """
                ),
                {"crop_id": crop["crop_id"], "stage_code": item["stage_code"]},
            ).mappings().first()
            if not stage:
                print(f"MISSING_STAGE {item['crop_code']}/{item['stage_code']} {key}")
                skipped += 1
                continue

            params = {
                "asset_type": item["asset_type"],
                "crop_id": crop["crop_id"],
                "stage_id": stage["stage_id"],
                "bucket_name": settings.crop_observation_s3_bucket,
                "object_key": key,
                "mime_type": mimetypes.guess_type(key)[0] or "audio/wav",
                "byte_size": int(head.get("ContentLength") or 0),
                "locale": item.get("locale"),
                "duration_seconds": item.get("duration_seconds"),
                "original_filename": Path(key).name,
            }

            asset = conn.execute(
                text(
                    """
                    SELECT asset_id FROM crop_observation.system_media_assets
                    WHERE bucket_name = :bucket_name AND object_key = :object_key
                    LIMIT 1
                    """
                ),
                params,
            ).mappings().first()
            if asset:
                asset_id = asset["asset_id"]
                conn.execute(
                    text(
                        """
                        UPDATE crop_observation.system_media_assets
                        SET asset_type = :asset_type, crop_id = :crop_id, stage_id = :stage_id,
                            mime_type = :mime_type, byte_size = :byte_size, locale = :locale,
                            duration_seconds = :duration_seconds, storage_backend = 'S3',
                            upload_status = 'READY', original_filename = :original_filename,
                            is_active = true, updated_at = now()
                        WHERE asset_id = :asset_id
                        """
                    ),
                    {**params, "asset_id": asset_id},
                )
            else:
                asset_id = conn.execute(
                    text(
                        """
                        INSERT INTO crop_observation.system_media_assets
                          (asset_type, crop_id, stage_id, bucket_name, object_key, mime_type,
                           byte_size, locale, duration_seconds, storage_backend,
                           original_filename, upload_status, is_active)
                        VALUES
                          (:asset_type, :crop_id, :stage_id, :bucket_name, :object_key, :mime_type,
                           :byte_size, :locale, :duration_seconds, 'S3',
                           :original_filename, 'READY', true)
                        RETURNING asset_id
                        """
                    ),
                    params,
                ).scalar()

            conn.execute(
                text(
                    """
                    UPDATE crop_observation.system_media_bindings
                    SET is_active = false
                    WHERE target_type = 'STAGE' AND target_id = :stage_id
                      AND asset_role = 'INSTRUCTION_AUDIO'
                      AND COALESCE(locale, '') = COALESCE(:locale, '')
                    """
                ),
                {"stage_id": stage["stage_id"], "locale": item.get("locale")},
            )
            conn.execute(
                text(
                    """
                    INSERT INTO crop_observation.system_media_bindings
                      (asset_id, target_type, target_id, asset_role, locale, is_active)
                    VALUES (:asset_id, 'STAGE', :stage_id, 'INSTRUCTION_AUDIO', :locale, true)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"asset_id": asset_id, "stage_id": stage["stage_id"], "locale": item.get("locale")},
            )
            conn.execute(
                text(
                    """
                    UPDATE crop_observation.system_media_bindings
                    SET is_active = true
                    WHERE asset_id = :asset_id AND target_type = 'STAGE'
                      AND target_id = :stage_id AND asset_role = 'INSTRUCTION_AUDIO'
                      AND COALESCE(locale, '') = COALESCE(:locale, '')
                    """
                ),
                {"asset_id": asset_id, "stage_id": stage["stage_id"], "locale": item.get("locale")},
            )
            print(f"SEEDED   {item['crop_code']}/{item['stage_code']} {item.get('locale')} {key}")
            seeded += 1

    print(f"Done. seeded={seeded} skipped={skipped}")


if __name__ == "__main__":
    main()
