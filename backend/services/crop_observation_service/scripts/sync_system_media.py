"""Upserts crop_observation.system_media_assets from media_manifest.json.

This is the "temporary admin panel" for crop card images, stage images and
instruction audio while there is no admin UI for media (the config UI itself
stays frozen per the V1 decision — see media_manifest.json). Safe to re-run;
existing (crop_id/stage_id/asset_type/locale) rows are refreshed in place.

Run from the backend/ directory so the `services`/`shared` packages resolve:

    cd backend
    python -m services.crop_observation_service.scripts.sync_system_media
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from sqlalchemy import text

from shared.db.postgres import engine

SERVICE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SERVICE_ROOT / "media_manifest.json"
MEDIA_ROOT = SERVICE_ROOT / "storage"

mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("audio/webm", ".webm")


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    with engine.begin() as conn:
        for item in manifest["assets"]:
            object_key = item["file"]
            actual_file = (MEDIA_ROOT / object_key).resolve()
            if not actual_file.exists():
                raise RuntimeError(f"Missing file declared in media_manifest.json: {actual_file}")

            mime_type, _ = mimetypes.guess_type(actual_file.name)
            if mime_type is None:
                raise RuntimeError(f"Could not guess a MIME type for {actual_file}")

            crop = conn.execute(
                text(
                    """
                    SELECT crop_id FROM crop_observation.crops WHERE crop_code = :crop_code;
                    """
                ),
                {"crop_code": item["crop_code"]},
            ).mappings().one()

            stage_id = None
            if item.get("stage_code"):
                stage = conn.execute(
                    text(
                        """
                        SELECT s.stage_id
                        FROM crop_observation.crop_stages s
                        JOIN crop_observation.crop_config_versions cv
                            ON cv.config_version_id = s.config_version_id
                        WHERE cv.crop_id = :crop_id
                          AND cv.status = 'PUBLISHED'
                          AND s.stage_code = :stage_code;
                        """
                    ),
                    {"crop_id": crop["crop_id"], "stage_code": item["stage_code"]},
                ).mappings().one()
                stage_id = stage["stage_id"]

            existing = conn.execute(
                text(
                    """
                    SELECT asset_id FROM crop_observation.system_media_assets
                    WHERE asset_type = :asset_type
                      AND crop_id = :crop_id
                      AND stage_id IS NOT DISTINCT FROM :stage_id
                      AND locale IS NOT DISTINCT FROM :locale;
                    """
                ),
                {
                    "asset_type": item["asset_type"],
                    "crop_id": crop["crop_id"],
                    "stage_id": stage_id,
                    "locale": item.get("locale"),
                },
            ).mappings().first()

            params = {
                "asset_type": item["asset_type"],
                "crop_id": crop["crop_id"],
                "stage_id": stage_id,
                "object_key": object_key,
                "mime_type": mime_type,
                "byte_size": actual_file.stat().st_size,
                "locale": item.get("locale"),
                "duration_seconds": item.get("duration_seconds"),
                "original_filename": actual_file.name,
            }

            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE crop_observation.system_media_assets
                        SET bucket_name = 'local',
                            object_key = :object_key,
                            mime_type = :mime_type,
                            byte_size = :byte_size,
                            duration_seconds = :duration_seconds,
                            storage_backend = 'LOCAL',
                            original_filename = :original_filename,
                            is_active = true
                        WHERE asset_id = :asset_id;
                        """
                    ),
                    {**params, "asset_id": existing["asset_id"]},
                )
                print(f"updated  {item['asset_type']:<24} {object_key}")
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO crop_observation.system_media_assets (
                            asset_type, crop_id, stage_id, bucket_name, object_key,
                            mime_type, byte_size, locale, duration_seconds,
                            storage_backend, original_filename, is_active
                        )
                        VALUES (
                            :asset_type, :crop_id, :stage_id, 'local', :object_key,
                            :mime_type, :byte_size, :locale, :duration_seconds,
                            'LOCAL', :original_filename, true
                        );
                        """
                    ),
                    params,
                )
                print(f"created  {item['asset_type']:<24} {object_key}")

    print("System media sync complete.")


if __name__ == "__main__":
    main()
