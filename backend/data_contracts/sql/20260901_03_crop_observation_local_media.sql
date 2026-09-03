-- =============================================================================
-- crop_observation_service — local filesystem media (V1).
--
-- Extends the media model from 20260901_01 (media_assets / system_media_assets)
-- rather than replacing it: storage_backend/original_filename let a row say
-- whether it lives on local disk or in S3, so flipping
-- MEDIA_STORAGE_BACKEND=S3 later is a config change, not a migration.
--
-- Idempotent: safe to re-run.
-- =============================================================================

ALTER TABLE crop_observation.media_assets
    ADD COLUMN IF NOT EXISTS storage_backend varchar(20) NOT NULL DEFAULT 'LOCAL';

ALTER TABLE crop_observation.media_assets
    ADD COLUMN IF NOT EXISTS original_filename varchar(500);

ALTER TABLE crop_observation.media_assets
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE crop_observation.system_media_assets
    ADD COLUMN IF NOT EXISTS storage_backend varchar(20) NOT NULL DEFAULT 'LOCAL';

ALTER TABLE crop_observation.system_media_assets
    ADD COLUMN IF NOT EXISTS original_filename varchar(500);

ALTER TABLE crop_observation.system_media_assets
    ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

-- One farmer voice note per stage/practice observation (a race-safe backstop
-- for the count check media_service.py already does before inserting).
CREATE UNIQUE INDEX IF NOT EXISTS ux_observation_media_voice
ON crop_observation.observation_media (owner_type, owner_id)
WHERE media_role = 'VOICE_NOTE';

-- Photo count (max MAX_IMAGES_PER_OWNER) stays an application-layer check —
-- observation_media.slot_number isn't populated in this schema, so there is
-- no per-slot column to key a DB constraint off.

-- One active stage image, one active instruction audio per stage+locale, one
-- active crop card image per crop.
CREATE UNIQUE INDEX IF NOT EXISTS ux_system_stage_image
ON crop_observation.system_media_assets (stage_id)
WHERE asset_type = 'STAGE_IMAGE' AND is_active = true;

CREATE UNIQUE INDEX IF NOT EXISTS ux_system_stage_instruction_locale
ON crop_observation.system_media_assets (stage_id, locale)
WHERE asset_type = 'STAGE_INSTRUCTION_AUDIO' AND is_active = true;

CREATE UNIQUE INDEX IF NOT EXISTS ux_system_crop_card_image
ON crop_observation.system_media_assets (crop_id)
WHERE asset_type = 'CROP_CARD_IMAGE' AND is_active = true;

CREATE INDEX IF NOT EXISTS ix_media_owner_user_status
ON crop_observation.media_assets (owner_user_id, upload_status);

-- Speeds up the per-practice "previous entries" history query.
CREATE INDEX IF NOT EXISTS ix_practice_history
ON crop_observation.practice_observations (daily_observation_id, practice_code, created_at DESC);
