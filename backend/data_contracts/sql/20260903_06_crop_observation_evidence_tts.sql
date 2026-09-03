-- =============================================================================
-- crop_observation_service — evidence semantics, reusable system bindings,
-- and Cartesia-backed TTS cache.
--
-- Additive only: extends the 20260901 crop-observation contracts without
-- rewriting ownership or media tables.
-- =============================================================================

ALTER TABLE crop_observation.stage_practices
    ADD COLUMN IF NOT EXISTS media_config jsonb NOT NULL DEFAULT
    '{
      "issue_evidence": {
        "enabled": false,
        "max_images": 2,
        "required": false
      },
      "practice_evidence": {
        "enabled": true,
        "max_images": 2,
        "required": false
      },
      "voice_note": {
        "enabled": true,
        "max_count": 1,
        "max_seconds": 60
      }
    }'::jsonb;

ALTER TABLE crop_observation.observation_media
    ADD COLUMN IF NOT EXISTS media_purpose varchar(40) NOT NULL DEFAULT 'GENERAL';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_observation_media_purpose'
    ) THEN
        ALTER TABLE crop_observation.observation_media
            ADD CONSTRAINT ck_observation_media_purpose
            CHECK (
                media_purpose IN (
                    'GENERAL',
                    'CROP_CONDITION',
                    'ISSUE_EVIDENCE',
                    'PRACTICE_EVIDENCE'
                )
            );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_observation_photo_purpose_slot
ON crop_observation.observation_media (
    owner_type,
    owner_id,
    media_purpose,
    slot_number
)
WHERE media_role = 'PHOTO'
  AND slot_number IS NOT NULL;

CREATE TABLE IF NOT EXISTS crop_observation.system_media_bindings (
    binding_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id uuid NOT NULL
        REFERENCES crop_observation.system_media_assets(asset_id)
        ON DELETE CASCADE,
    target_type varchar(40) NOT NULL
        CHECK (
            target_type IN (
                'CROP',
                'STAGE',
                'STAGE_PRACTICE',
                'FIELD_OPTION'
            )
        ),
    target_id uuid NOT NULL,
    asset_role varchar(60) NOT NULL
        CHECK (
            asset_role IN (
                'CROP_CARD_IMAGE',
                'STAGE_IMAGE',
                'INSTRUCTION_AUDIO',
                'PRACTICE_GUIDE_IMAGE',
                'OPTION_IMAGE'
            )
        ),
    locale varchar(10),
    slot_number smallint,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_system_media_binding_unique
ON crop_observation.system_media_bindings (
    target_type,
    target_id,
    asset_role,
    COALESCE(locale, ''),
    COALESCE(slot_number, -1)
)
WHERE is_active = true;

INSERT INTO crop_observation.system_media_bindings (asset_id, target_type, target_id, asset_role, locale)
SELECT sma.asset_id,
       'CROP',
       sma.crop_id,
       'CROP_CARD_IMAGE',
       sma.locale
FROM crop_observation.system_media_assets sma
WHERE sma.crop_id IS NOT NULL
  AND sma.asset_type = 'CROP_CARD_IMAGE'
  AND sma.is_active = true
  AND NOT EXISTS (
      SELECT 1
      FROM crop_observation.system_media_bindings smb
      WHERE smb.asset_id = sma.asset_id
  );

INSERT INTO crop_observation.system_media_bindings (asset_id, target_type, target_id, asset_role, locale)
SELECT sma.asset_id,
       'STAGE',
       sma.stage_id,
       CASE
           WHEN sma.asset_type = 'STAGE_IMAGE' THEN 'STAGE_IMAGE'
           ELSE 'INSTRUCTION_AUDIO'
       END,
       sma.locale
FROM crop_observation.system_media_assets sma
WHERE sma.stage_id IS NOT NULL
  AND sma.asset_type IN ('STAGE_IMAGE', 'STAGE_INSTRUCTION_AUDIO')
  AND sma.is_active = true
  AND NOT EXISTS (
      SELECT 1
      FROM crop_observation.system_media_bindings smb
      WHERE smb.asset_id = sma.asset_id
  );

CREATE TABLE IF NOT EXISTS crop_observation.tts_profiles (
    tts_profile_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_code varchar(80) NOT NULL UNIQUE,
    locale varchar(10) NOT NULL,
    provider varchar(30) NOT NULL DEFAULT 'CARTESIA',
    model_id varchar(100) NOT NULL,
    voice_id varchar(150) NOT NULL,
    voice_name varchar(200),
    output_format jsonb NOT NULL DEFAULT '{"container":"mp3"}'::jsonb,
    generation_config jsonb NOT NULL DEFAULT '{"speed":0.95,"volume":1.0}'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS crop_observation.tts_generations (
    tts_generation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type varchar(40) NOT NULL,
    target_id uuid NOT NULL,
    locale varchar(10) NOT NULL,
    transcript text NOT NULL,
    profile_id uuid NOT NULL
        REFERENCES crop_observation.tts_profiles(tts_profile_id),
    cache_key varchar(64) NOT NULL UNIQUE,
    status varchar(20) NOT NULL
        CHECK (status IN ('PENDING', 'READY', 'FAILED')),
    system_media_asset_id uuid
        REFERENCES crop_observation.system_media_assets(asset_id),
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO crop_observation.tts_profiles
    (profile_code, locale, provider, model_id, voice_id, output_format, generation_config)
VALUES
    (
        'odia_default',
        'or-IN',
        'CARTESIA',
        'sonic-3.6-2026-08-27',
        '__SET_IN_ENV__',
        '{"container":"mp3"}'::jsonb,
        '{"speed":0.95,"volume":1.0}'::jsonb
    ),
    (
        'english_default',
        'en-IN',
        'CARTESIA',
        'sonic-3.6-2026-08-27',
        '__SET_IN_ENV__',
        '{"container":"mp3"}'::jsonb,
        '{"speed":0.95,"volume":1.0}'::jsonb
    )
ON CONFLICT (profile_code) DO NOTHING;

UPDATE crop_observation.stage_practices sp
SET media_config =
'{
  "issue_evidence": {
    "enabled": true,
    "max_images": 2,
    "required": false
  },
  "practice_evidence": {
    "enabled": true,
    "max_images": 2,
    "required": false
  },
  "voice_note": {
    "enabled": true,
    "max_count": 1,
    "max_seconds": 60
  }
}'::jsonb
FROM crop_observation.practice_templates pt
WHERE pt.practice_template_id = sp.practice_template_id
  AND pt.practice_code IN ('pest_management', 'disease_management', 'crop_damage');
