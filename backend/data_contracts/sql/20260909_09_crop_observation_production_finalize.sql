BEGIN;

-- =============================================================================
-- Crop Observation production finalization
-- - production system-media upload lifecycle
-- - review workflow / practice-record read model
-- - safer review-flag deduplication
-- - admin audit trail
-- - indexes used by the final farmer/admin screens
--
-- Assumes migrations through 20260903_07 are already applied.
-- Additive and idempotent.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. System media: support LOCAL and S3 upload -> verify -> activate lifecycle.
-- -----------------------------------------------------------------------------

ALTER TABLE crop_observation.media_assets
    ADD COLUMN IF NOT EXISTS upload_expires_at timestamptz;

ALTER TABLE crop_observation.system_media_assets
    ADD COLUMN IF NOT EXISTS upload_status varchar(20) NOT NULL DEFAULT 'READY',
    ADD COLUMN IF NOT EXISTS checksum_sha256 varchar(64),
    ADD COLUMN IF NOT EXISTS created_by_user_id uuid,
    ADD COLUMN IF NOT EXISTS upload_expires_at timestamptz,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_system_media_upload_status'
          AND connamespace = 'crop_observation'::regnamespace
    ) THEN
        ALTER TABLE crop_observation.system_media_assets
            ADD CONSTRAINT ck_system_media_upload_status
            CHECK (
                upload_status IN (
                    'REQUESTED',
                    'UPLOADED',
                    'VERIFIED',
                    'READY',
                    'REJECTED',
                    'DELETED'
                )
            );
    END IF;
END $$;

UPDATE crop_observation.system_media_assets
SET upload_status = 'READY'
WHERE upload_status IS NULL;

CREATE INDEX IF NOT EXISTS ix_system_media_upload_status
ON crop_observation.system_media_assets(upload_status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_media_upload_expiry
ON crop_observation.media_assets(upload_expires_at)
WHERE upload_status = 'REQUESTED';

CREATE INDEX IF NOT EXISTS ix_system_media_upload_expiry
ON crop_observation.system_media_assets(upload_expires_at)
WHERE upload_status = 'REQUESTED';

CREATE INDEX IF NOT EXISTS ix_system_media_binding_target
ON crop_observation.system_media_bindings(
    target_type,
    target_id,
    asset_role,
    is_active
);

CREATE INDEX IF NOT EXISTS ix_system_media_binding_asset
ON crop_observation.system_media_bindings(asset_id);

-- -----------------------------------------------------------------------------
-- 2. Practice record review workflow.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.record_reviews (
    review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    record_type varchar(20) NOT NULL
        CHECK (record_type IN ('STAGE', 'PRACTICE')),

    record_id uuid NOT NULL,

    review_status varchar(30) NOT NULL DEFAULT 'NEW'
        CHECK (
            review_status IN (
                'NEW',
                'IN_REVIEW',
                'NEEDS_FOLLOW_UP',
                'REVIEWED',
                'RESOLVED'
            )
        ),

    admin_note text,
    reviewed_by_user_id uuid,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(record_type, record_id)
);

CREATE INDEX IF NOT EXISTS ix_record_reviews_status
ON crop_observation.record_reviews(review_status, updated_at DESC);

-- -----------------------------------------------------------------------------
-- 3. Prevent repeated serious-problem saves from generating duplicate open flags.
-- Existing duplicates are collapsed before the unique index is installed.
-- -----------------------------------------------------------------------------

WITH ranked AS (
    SELECT
        review_flag_id,
        row_number() OVER (
            PARTITION BY source_type, source_id, flag_type
            ORDER BY created_at ASC, review_flag_id ASC
        ) AS rn
    FROM crop_observation.review_flags
    WHERE status = 'OPEN'
)
DELETE FROM crop_observation.review_flags rf
USING ranked r
WHERE rf.review_flag_id = r.review_flag_id
  AND r.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS ux_review_flag_open_source
ON crop_observation.review_flags(source_type, source_id, flag_type)
WHERE status = 'OPEN';

CREATE INDEX IF NOT EXISTS ix_review_flags_priority
ON crop_observation.review_flags(status, priority, created_at DESC);

-- -----------------------------------------------------------------------------
-- 4. Admin audit events for configuration/media/TTS/review actions.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.admin_audit_events (
    audit_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid,
    action varchar(120) NOT NULL,
    entity_type varchar(60) NOT NULL,
    entity_id uuid,
    before_state jsonb,
    after_state jsonb,
    correlation_id varchar(120),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_crop_obs_admin_audit_created
ON crop_observation.admin_audit_events(created_at DESC);

CREATE INDEX IF NOT EXISTS ix_crop_obs_admin_audit_entity
ON crop_observation.admin_audit_events(entity_type, entity_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- 5. Read model: one PRACTICE observation = one operational record row.
-- Farmer writes remain normalized in the existing tables; admin reads this view.
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW crop_observation.v_practice_records AS
SELECT
    po.practice_observation_id AS record_id,
    po.daily_observation_id,
    d.crop_cycle_id,
    cc.farm_crop_id,
    fc.farmer_user_id,
    fc.farm_id,
    fc.crop_code,
    cc.season_year,
    cc.season_name,
    d.config_version_id,
    d.stage_code,
    d.observed_on,
    d.crop_status,
    po.stage_practice_id,
    po.practice_code,
    po.answers,
    po.completion_status,
    po.answers ->> 'severity' AS severity,
    COALESCE(
        po.answers ->> 'pest_observed',
        po.answers ->> 'disease_observed',
        po.answers ->> 'damage_cause'
    ) AS issue_code,
    COALESCE(rr.review_status, 'NEW') AS review_status,
    rr.admin_note,
    rr.reviewed_by_user_id,
    po.created_at,
    po.updated_at,
    COALESCE(media.issue_image_count, 0)::integer AS issue_image_count,
    COALESCE(media.practice_image_count, 0)::integer AS practice_image_count,
    COALESCE(media.voice_count, 0)::integer AS voice_count
FROM crop_observation.practice_observations po
JOIN crop_observation.daily_stage_observations d
  ON d.daily_observation_id = po.daily_observation_id
JOIN crop_observation.crop_cycles cc
  ON cc.crop_cycle_id = d.crop_cycle_id
JOIN crop_observation.farm_crops fc
  ON fc.farm_crop_id = cc.farm_crop_id
LEFT JOIN crop_observation.record_reviews rr
  ON rr.record_type = 'PRACTICE'
 AND rr.record_id = po.practice_observation_id
LEFT JOIN LATERAL (
    SELECT
        count(*) FILTER (
            WHERE om.media_role = 'PHOTO'
              AND om.media_purpose = 'ISSUE_EVIDENCE'
              AND ma.upload_status = 'READY'
        ) AS issue_image_count,
        count(*) FILTER (
            WHERE om.media_role = 'PHOTO'
              AND om.media_purpose = 'PRACTICE_EVIDENCE'
              AND ma.upload_status = 'READY'
        ) AS practice_image_count,
        count(*) FILTER (
            WHERE om.media_role = 'VOICE_NOTE'
              AND ma.upload_status = 'READY'
        ) AS voice_count
    FROM crop_observation.observation_media om
    JOIN crop_observation.media_assets ma
      ON ma.media_asset_id = om.media_asset_id
    WHERE om.owner_type = 'PRACTICE'
      AND om.owner_id = po.practice_observation_id
) media ON true;

-- -----------------------------------------------------------------------------
-- 6. Additional indexes for the history/admin record paths.
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_daily_admin_date_crop
ON crop_observation.daily_stage_observations(observed_on DESC, crop_status);

CREATE INDEX IF NOT EXISTS ix_practice_code_updated
ON crop_observation.practice_observations(practice_code, updated_at DESC);

CREATE INDEX IF NOT EXISTS ix_observation_media_owner_purpose
ON crop_observation.observation_media(owner_type, owner_id, media_purpose, media_role);

CREATE INDEX IF NOT EXISTS ix_media_asset_ready
ON crop_observation.media_assets(upload_status, created_at DESC);

-- -----------------------------------------------------------------------------
-- 7. Generic updated_at helper for new tables / system-media.
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION crop_observation.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_record_reviews_updated_at
ON crop_observation.record_reviews;

CREATE TRIGGER trg_record_reviews_updated_at
BEFORE UPDATE ON crop_observation.record_reviews
FOR EACH ROW
EXECUTE FUNCTION crop_observation.set_updated_at();

DROP TRIGGER IF EXISTS trg_system_media_assets_updated_at
ON crop_observation.system_media_assets;

CREATE TRIGGER trg_system_media_assets_updated_at
BEFORE UPDATE ON crop_observation.system_media_assets
FOR EACH ROW
EXECUTE FUNCTION crop_observation.set_updated_at();

COMMIT;
