-- =============================================================================
-- crop_observation_service — schema, tables, indexes, seeds (Phase 1)
--
-- Owns: farmer-facing crop configuration (stages/practices/fields/translations),
-- per-farm crop tracking, and farmer observations/media.
--
-- Does NOT own: analytics profiles/formulas/weights — those remain in the
-- existing feature-engine's crop_feature_profiles. Both sides share the same
-- canonical crop_code values (kala_jeera, coconut, mango).
--
-- Idempotent: safe to re-run (CREATE ... IF NOT EXISTS, seed upserts).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS crop_observation;

-- ---------------------------------------------------------------------------
-- Configuration: crops
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.crops (
    crop_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    crop_code varchar(80) NOT NULL UNIQUE,

    lifecycle_type varchar(20) NOT NULL
        CHECK (lifecycle_type IN ('ANNUAL', 'PERENNIAL')),

    default_stage_strategy varchar(30) NOT NULL
        CHECK (
            default_stage_strategy IN (
                'FIRST_STAGE',
                'CURRENT_STAGE',
                'SYSTEM_SUGGESTED'
            )
        ),

    is_active boolean NOT NULL DEFAULT true,
    display_order integer NOT NULL DEFAULT 0,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS crop_observation.crop_translations (
    crop_translation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_id uuid NOT NULL
        REFERENCES crop_observation.crops(crop_id)
        ON DELETE CASCADE,

    locale varchar(10) NOT NULL,

    display_name varchar(150) NOT NULL,
    short_description varchar(500),

    UNIQUE(crop_id, locale)
);

-- ---------------------------------------------------------------------------
-- Configuration: versioned stages / practices
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.crop_config_versions (
    config_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    crop_id uuid NOT NULL
        REFERENCES crop_observation.crops(crop_id),

    version_number integer NOT NULL,

    status varchar(20) NOT NULL
        CHECK (
            status IN (
                'DRAFT',
                'PUBLISHED',
                'SUPERSEDED',
                'ARCHIVED'
            )
        ),

    created_by_user_id uuid,
    published_by_user_id uuid,

    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,

    UNIQUE(crop_id, version_number)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_crop_one_published_config
ON crop_observation.crop_config_versions(crop_id)
WHERE status = 'PUBLISHED';

CREATE TABLE IF NOT EXISTS crop_observation.crop_stages (
    stage_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    config_version_id uuid NOT NULL
        REFERENCES crop_observation.crop_config_versions(config_version_id)
        ON DELETE CASCADE,

    stage_code varchar(80) NOT NULL,
    display_order integer NOT NULL,

    is_initial boolean NOT NULL DEFAULT false,
    is_enabled boolean NOT NULL DEFAULT true,

    expected_start_day integer,
    expected_end_day integer,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(config_version_id, stage_code)
);

CREATE TABLE IF NOT EXISTS crop_observation.crop_stage_translations (
    stage_translation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    stage_id uuid NOT NULL
        REFERENCES crop_observation.crop_stages(stage_id)
        ON DELETE CASCADE,

    locale varchar(10) NOT NULL,

    display_name varchar(150) NOT NULL,
    short_description varchar(1000),
    instruction_text varchar(1200),

    UNIQUE(stage_id, locale)
);

CREATE TABLE IF NOT EXISTS crop_observation.practice_templates (
    practice_template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    practice_code varchar(80) NOT NULL UNIQUE,

    system_type varchar(40) NOT NULL,

    is_active boolean NOT NULL DEFAULT true,

    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS crop_observation.practice_translations (
    practice_translation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    practice_template_id uuid NOT NULL
        REFERENCES crop_observation.practice_templates(practice_template_id)
        ON DELETE CASCADE,

    locale varchar(10) NOT NULL,
    display_name varchar(150) NOT NULL,
    help_text varchar(700),

    UNIQUE(practice_template_id, locale)
);

CREATE TABLE IF NOT EXISTS crop_observation.stage_practices (
    stage_practice_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    stage_id uuid NOT NULL
        REFERENCES crop_observation.crop_stages(stage_id)
        ON DELETE CASCADE,

    practice_template_id uuid NOT NULL
        REFERENCES crop_observation.practice_templates(practice_template_id),

    availability_scope varchar(30) NOT NULL DEFAULT 'STAGE_SPECIFIC'
        CHECK (
            availability_scope IN (
                'STAGE_SPECIFIC',
                'ALWAYS_AVAILABLE'
            )
        ),

    display_order integer NOT NULL DEFAULT 0,

    is_enabled boolean NOT NULL DEFAULT true,

    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(stage_id, practice_template_id)
);

-- Controlled field library. field_type must be one of: BOOLEAN,
-- YES_NO_UNKNOWN, SINGLE_CHOICE, MULTI_CHOICE, PICTURE_CHOICE, SEVERITY,
-- QUANTITY_UNIT, NUMBER, SHORT_TEXT, PRODUCT, PEST, DISEASE,
-- APPLICATION_AREA. Enforced in the admin service layer (Phase 4), not here.

CREATE TABLE IF NOT EXISTS crop_observation.practice_field_definitions (
    field_definition_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    stage_practice_id uuid NOT NULL
        REFERENCES crop_observation.stage_practices(stage_practice_id)
        ON DELETE CASCADE,

    field_code varchar(100) NOT NULL,

    field_type varchar(40) NOT NULL,

    semantic_type varchar(80),

    display_order integer NOT NULL,

    is_required boolean NOT NULL DEFAULT false,
    is_enabled boolean NOT NULL DEFAULT true,

    validation_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    ui_config jsonb NOT NULL DEFAULT '{}'::jsonb,

    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(stage_practice_id, field_code)
);

CREATE TABLE IF NOT EXISTS crop_observation.practice_field_translations (
    field_translation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    field_definition_id uuid NOT NULL
        REFERENCES crop_observation.practice_field_definitions(field_definition_id)
        ON DELETE CASCADE,

    locale varchar(10) NOT NULL,

    label varchar(200) NOT NULL,
    help_text varchar(500),

    UNIQUE(field_definition_id, locale)
);

CREATE TABLE IF NOT EXISTS crop_observation.practice_field_options (
    field_option_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    field_definition_id uuid NOT NULL
        REFERENCES crop_observation.practice_field_definitions(field_definition_id)
        ON DELETE CASCADE,

    option_code varchar(100) NOT NULL,
    display_order integer NOT NULL,

    icon_key varchar(100),

    is_active boolean NOT NULL DEFAULT true,

    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

    UNIQUE(field_definition_id, option_code)
);

CREATE TABLE IF NOT EXISTS crop_observation.practice_field_option_translations (
    option_translation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    field_option_id uuid NOT NULL
        REFERENCES crop_observation.practice_field_options(field_option_id)
        ON DELETE CASCADE,

    locale varchar(10) NOT NULL,

    label varchar(150) NOT NULL,

    UNIQUE(field_option_id, locale)
);

CREATE TABLE IF NOT EXISTS crop_observation.system_media_assets (
    asset_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    asset_type varchar(40) NOT NULL,

    crop_id uuid,
    stage_id uuid,

    bucket_name varchar(255) NOT NULL,
    object_key varchar(1000) NOT NULL,

    mime_type varchar(150) NOT NULL,
    byte_size bigint,

    locale varchar(10),

    duration_seconds numeric(8,2),

    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(bucket_name, object_key)
);

-- ---------------------------------------------------------------------------
-- Farmer crop tracking
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.farm_crops (
    farm_crop_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    farm_id uuid NOT NULL,
    farmer_user_id uuid NOT NULL,

    crop_code varchar(80) NOT NULL,

    variety_name varchar(200),

    planted_on date,

    status varchar(20) NOT NULL
        CHECK (
            status IN (
                'ACTIVE',
                'COMPLETED',
                'REMOVED'
            )
        ),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_farm_crops_farm
ON crop_observation.farm_crops(farm_id);

CREATE INDEX IF NOT EXISTS ix_farm_crops_farmer
ON crop_observation.farm_crops(farmer_user_id);

CREATE TABLE IF NOT EXISTS crop_observation.crop_cycles (
    crop_cycle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    farm_crop_id uuid NOT NULL
        REFERENCES crop_observation.farm_crops(farm_crop_id),

    config_version_id uuid NOT NULL
        REFERENCES crop_observation.crop_config_versions(config_version_id),

    season_year integer,

    season_name varchar(100),

    cycle_started_on date NOT NULL,

    cycle_ended_on date,

    current_stage_code varchar(80),

    current_stage_source varchar(30)
        CHECK (
            current_stage_source IN (
                'FARMER',
                'ADMIN',
                'SYSTEM',
                'SATELLITE'
            )
        ),

    status varchar(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            status IN (
                'ACTIVE',
                'COMPLETED',
                'CANCELLED'
            )
        ),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_crop_cycles_farm_crop
ON crop_observation.crop_cycles(farm_crop_id);

CREATE TABLE IF NOT EXISTS crop_observation.crop_stage_history (
    stage_history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    crop_cycle_id uuid NOT NULL
        REFERENCES crop_observation.crop_cycles(crop_cycle_id),

    stage_code varchar(80) NOT NULL,

    effective_from date NOT NULL,
    effective_until date,

    source varchar(30) NOT NULL,

    changed_by_user_id uuid,

    created_at timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Farmer observations (Phase 2 writes; created now for referential integrity
-- and so the schema matches the full data contract in one migration)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.daily_stage_observations (
    daily_observation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    crop_cycle_id uuid NOT NULL
        REFERENCES crop_observation.crop_cycles(crop_cycle_id),

    config_version_id uuid NOT NULL
        REFERENCES crop_observation.crop_config_versions(config_version_id),

    stage_code varchar(80) NOT NULL,

    observed_on date NOT NULL,

    crop_status varchar(30) NOT NULL
        CHECK (
            crop_status IN (
                'GOOD',
                'SOME_PROBLEM',
                'SERIOUS_PROBLEM'
            )
        ),

    client_entry_id uuid NOT NULL,

    sync_source varchar(30) NOT NULL DEFAULT 'ONLINE'
        CHECK (
            sync_source IN (
                'ONLINE',
                'OFFLINE_SYNC'
            )
        ),

    captured_at_client timestamptz,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(crop_cycle_id, stage_code, observed_on),
    UNIQUE(client_entry_id)
);

CREATE INDEX IF NOT EXISTS ix_daily_crop_cycle_date
ON crop_observation.daily_stage_observations(crop_cycle_id, observed_on DESC);

CREATE TABLE IF NOT EXISTS crop_observation.practice_observations (
    practice_observation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    daily_observation_id uuid NOT NULL
        REFERENCES crop_observation.daily_stage_observations(daily_observation_id)
        ON DELETE CASCADE,

    stage_practice_id uuid NOT NULL
        REFERENCES crop_observation.stage_practices(stage_practice_id),

    practice_code varchar(80) NOT NULL,

    answers jsonb NOT NULL DEFAULT '{}'::jsonb,

    completion_status varchar(20) NOT NULL DEFAULT 'COMPLETE',

    client_entry_id uuid NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(daily_observation_id, practice_code),
    UNIQUE(client_entry_id)
);

CREATE INDEX IF NOT EXISTS ix_practice_daily
ON crop_observation.practice_observations(daily_observation_id);

CREATE TABLE IF NOT EXISTS crop_observation.observation_revisions (
    revision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    observation_type varchar(30) NOT NULL,

    observation_id uuid NOT NULL,

    revision_number integer NOT NULL,

    previous_payload jsonb,
    new_payload jsonb NOT NULL,

    changed_by_user_id uuid NOT NULL,

    changed_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(
        observation_type,
        observation_id,
        revision_number
    )
);

-- ---------------------------------------------------------------------------
-- Media (Phase 2 writes)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.media_assets (
    media_asset_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    owner_user_id uuid NOT NULL,

    bucket_name varchar(255) NOT NULL,
    object_key varchar(1000) NOT NULL,

    media_type varchar(20) NOT NULL
        CHECK (
            media_type IN (
                'IMAGE',
                'AUDIO'
            )
        ),

    mime_type varchar(150) NOT NULL,
    byte_size bigint NOT NULL,

    duration_seconds numeric(8,2),

    checksum_sha256 varchar(64),

    upload_status varchar(20) NOT NULL
        CHECK (
            upload_status IN (
                'REQUESTED',
                'UPLOADED',
                'VERIFIED',
                'READY',
                'REJECTED',
                'DELETED'
            )
        ),

    created_at timestamptz NOT NULL DEFAULT now(),
    uploaded_at timestamptz,
    verified_at timestamptz,

    UNIQUE(bucket_name, object_key)
);

CREATE TABLE IF NOT EXISTS crop_observation.observation_media (
    observation_media_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    owner_type varchar(30) NOT NULL
        CHECK (
            owner_type IN (
                'DAILY_STAGE',
                'PRACTICE'
            )
        ),

    owner_id uuid NOT NULL,

    media_asset_id uuid NOT NULL
        REFERENCES crop_observation.media_assets(media_asset_id),

    media_role varchar(20) NOT NULL
        CHECK (
            media_role IN (
                'PHOTO',
                'VOICE_NOTE'
            )
        ),

    slot_number smallint,

    created_at timestamptz NOT NULL DEFAULT now()
);

-- Max 2 PHOTO / max 1 VOICE_NOTE per owner is enforced in the application
-- layer (Phase 2 media_service), not as a DB constraint.

-- ---------------------------------------------------------------------------
-- Operational
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS crop_observation.review_flags (
    review_flag_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    farmer_user_id uuid NOT NULL,
    farm_id uuid NOT NULL,

    crop_cycle_id uuid NOT NULL,

    source_type varchar(40) NOT NULL,
    source_id uuid NOT NULL,

    flag_type varchar(60) NOT NULL,
    priority varchar(20) NOT NULL,

    status varchar(20) NOT NULL DEFAULT 'OPEN',

    created_at timestamptz NOT NULL DEFAULT now(),
    resolved_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_review_open
ON crop_observation.review_flags(status, created_at DESC);

CREATE TABLE IF NOT EXISTS crop_observation.outbox_events (
    event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    aggregate_type varchar(60) NOT NULL,
    aggregate_id uuid NOT NULL,

    event_type varchar(120) NOT NULL,
    event_version integer NOT NULL DEFAULT 1,

    payload jsonb NOT NULL,

    status varchar(20) NOT NULL DEFAULT 'PENDING',

    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);

CREATE INDEX IF NOT EXISTS ix_outbox_pending
ON crop_observation.outbox_events(status, created_at)
WHERE status = 'PENDING';

-- ---------------------------------------------------------------------------
-- Seeds — canonical crop_code values shared with the existing feature-engine
-- crop_feature_profiles (kala_jeera, coconut, mango). Do not rename.
-- ---------------------------------------------------------------------------

INSERT INTO crop_observation.crops
    (crop_code, lifecycle_type, default_stage_strategy, display_order)
VALUES
    ('kala_jeera', 'ANNUAL', 'FIRST_STAGE', 10),
    ('coconut', 'PERENNIAL', 'CURRENT_STAGE', 20),
    ('mango', 'PERENNIAL', 'CURRENT_STAGE', 30)
ON CONFLICT (crop_code) DO NOTHING;

INSERT INTO crop_observation.crop_translations (crop_id, locale, display_name)
SELECT c.crop_id, v.locale, v.display_name
FROM crop_observation.crops c
JOIN (
    VALUES
        ('kala_jeera', 'en-IN', 'Kala Jeera'),
        ('kala_jeera', 'or-IN', 'କଳାଜିରା ଧାନ'),
        ('coconut', 'en-IN', 'Coconut'),
        ('coconut', 'or-IN', 'ନଡ଼ିଆ'),
        ('mango', 'en-IN', 'Mango'),
        ('mango', 'or-IN', 'ଆମ୍ବ')
) AS v(crop_code, locale, display_name)
    ON v.crop_code = c.crop_code
ON CONFLICT (crop_id, locale) DO NOTHING;

INSERT INTO crop_observation.practice_templates (practice_code, system_type)
VALUES
    ('nutrient_management', 'FARMER_PRACTICE'),
    ('weed_management', 'FARMER_PRACTICE'),
    ('pest_management', 'FARMER_PRACTICE'),
    ('disease_management', 'FARMER_PRACTICE'),
    ('harvest_management', 'FARMER_PRACTICE'),
    ('post_harvest', 'FARMER_PRACTICE'),
    ('seed_management', 'FARMER_PRACTICE'),
    ('nursery_management', 'FARMER_PRACTICE'),
    ('orchard_management', 'FARMER_PRACTICE'),
    ('crop_damage', 'FARMER_PRACTICE')
ON CONFLICT (practice_code) DO NOTHING;
