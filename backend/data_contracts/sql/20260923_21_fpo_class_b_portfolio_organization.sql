BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_farmer_tags (
    tag_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    name varchar(80) NOT NULL, normalized_name varchar(80) NOT NULL, description text, color_token varchar(40) NOT NULL DEFAULT 'emerald',
    is_active boolean NOT NULL DEFAULT true, created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE (fpo_id, normalized_name)
);
CREATE TABLE IF NOT EXISTS public.fpo_farmer_tag_assignments (
    tag_assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    tag_id uuid NOT NULL REFERENCES public.fpo_farmer_tags(tag_id) ON DELETE CASCADE, farmer_id uuid NOT NULL,
    relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT,
    assigned_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, assigned_at timestamptz NOT NULL DEFAULT now(),
    removed_at timestamptz, removed_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    UNIQUE (tag_id, farmer_id)
);
CREATE INDEX IF NOT EXISTS idx_fpo_farmer_tags_owner ON public.fpo_farmer_tags (fpo_id, is_active, normalized_name);
CREATE INDEX IF NOT EXISTS idx_fpo_tag_assignments_farmer ON public.fpo_farmer_tag_assignments (fpo_id, farmer_id) WHERE removed_at IS NULL;

CREATE TABLE IF NOT EXISTS public.fpo_farmer_segments (
    segment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    name varchar(160) NOT NULL, description text, segment_type text NOT NULL DEFAULT 'DYNAMIC', criteria jsonb NOT NULL DEFAULT '{}'::jsonb,
    criteria_schema_version integer NOT NULL DEFAULT 1, status text NOT NULL DEFAULT 'ACTIVE', last_evaluated_at timestamptz,
    member_count integer NOT NULL DEFAULT 0, created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_segment_type CHECK (segment_type IN ('DYNAMIC','STATIC')), CONSTRAINT ck_fpo_segment_status CHECK (status IN ('ACTIVE','ARCHIVED'))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_segment_name ON public.fpo_farmer_segments (fpo_id, lower(name)) WHERE status <> 'ARCHIVED';
CREATE TABLE IF NOT EXISTS public.fpo_farmer_segment_members (
    segment_id uuid NOT NULL REFERENCES public.fpo_farmer_segments(segment_id) ON DELETE CASCADE, farmer_id uuid NOT NULL,
    relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT,
    membership_source text NOT NULL DEFAULT 'RULE', evaluated_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz,
    PRIMARY KEY (segment_id, farmer_id), CONSTRAINT ck_fpo_segment_membership_source CHECK (membership_source IN ('RULE','MANUAL'))
);

CREATE TABLE IF NOT EXISTS public.fpo_farmer_notes (
    note_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    farmer_id uuid NOT NULL, relationship_id uuid NOT NULL REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE RESTRICT,
    note_type text NOT NULL DEFAULT 'GENERAL', title varchar(200) NOT NULL, content_ciphertext bytea NOT NULL, content_key_version integer NOT NULL DEFAULT 1,
    visibility text NOT NULL DEFAULT 'FPO_PRIVATE', follow_up_at timestamptz, status text NOT NULL DEFAULT 'OPEN',
    created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, completed_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    completed_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_note_type CHECK (note_type IN ('GENERAL','FOLLOW_UP','VISIT','DATA_QUALITY','ADVISORY')), CONSTRAINT ck_fpo_note_status CHECK (status IN ('OPEN','COMPLETED','ARCHIVED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_notes_owner ON public.fpo_farmer_notes (fpo_id, farmer_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.fpo_season_plans (
    season_plan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    season_code varchar(50) NOT NULL, season_year integer NOT NULL, name varchar(160) NOT NULL, status text NOT NULL DEFAULT 'DRAFT',
    planning_start_date date NOT NULL, season_start_date date NOT NULL, season_end_date date NOT NULL, geography_filter jsonb NOT NULL DEFAULT '{}'::jsonb,
    notes text, created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, activated_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    activated_at timestamptz, locked_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_season_status CHECK (status IN ('DRAFT','ACTIVE','LOCKED','COMPLETED','CANCELLED')), CONSTRAINT ck_fpo_season_dates CHECK (season_end_date >= season_start_date)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_active_season ON public.fpo_season_plans (fpo_id, season_code, season_year) WHERE status IN ('DRAFT','ACTIVE','LOCKED');
CREATE TABLE IF NOT EXISTS public.fpo_season_crop_targets (
    crop_target_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), season_plan_id uuid NOT NULL REFERENCES public.fpo_season_plans(season_plan_id) ON DELETE CASCADE,
    crop_code text NOT NULL, variety_code text, target_farmer_count integer, target_farm_count integer, target_area_acres numeric(16,4) NOT NULL DEFAULT 0,
    target_sowing_start date, target_sowing_end date, target_harvest_start date, target_harvest_end date, target_yield_value numeric(16,4), target_yield_unit text,
    input_assumptions jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (season_plan_id, crop_code, variety_code)
);

CREATE TABLE IF NOT EXISTS public.fpo_field_tasks (
    task_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    task_type text NOT NULL, title varchar(240) NOT NULL, description text, priority text NOT NULL DEFAULT 'NORMAL', status text NOT NULL DEFAULT 'OPEN',
    farmer_id uuid, farm_id uuid, relationship_id uuid REFERENCES public.fpo_farmer_relationships(relationship_id) ON DELETE SET NULL, source_type text, source_id uuid,
    due_at timestamptz, assigned_actor_type text NOT NULL DEFAULT 'FPO_OWNER', assigned_actor_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    completion_note text, completed_at timestamptz, created_by uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), version integer NOT NULL DEFAULT 1,
    CONSTRAINT ck_fpo_task_type CHECK (task_type IN ('FARM_VISIT','FOLLOW_UP','DATA_CORRECTION','OBSERVATION','ADVISORY','VERIFICATION')),
    CONSTRAINT ck_fpo_task_priority CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT')),
    CONSTRAINT ck_fpo_task_status CHECK (status IN ('OPEN','IN_PROGRESS','COMPLETED','CANCELLED','OVERDUE'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_tasks_queue ON public.fpo_field_tasks (fpo_id, status, due_at, priority);
CREATE TABLE IF NOT EXISTS public.fpo_field_task_events (
    task_event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), task_id uuid NOT NULL REFERENCES public.fpo_field_tasks(task_id) ON DELETE CASCADE,
    event_type text NOT NULL, status_from text, status_to text, actor_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    note text, metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
