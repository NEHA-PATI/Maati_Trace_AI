BEGIN;

ALTER TABLE public.auth_outbox_events
    ADD COLUMN IF NOT EXISTS correlation_id uuid NOT NULL DEFAULT gen_random_uuid();

ALTER TABLE public.fpo_event_inbox
    ADD COLUMN IF NOT EXISTS event_payload jsonb,
    ADD COLUMN IF NOT EXISTS correlation_id uuid,
    ADD COLUMN IF NOT EXISTS occurred_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS delivery_count integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS poison_count integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS error_code text;

ALTER TABLE public.fpo_organizations
    ADD COLUMN IF NOT EXISTS provisioning_step text,
    ADD COLUMN IF NOT EXISTS provisioning_error_code text,
    ADD COLUMN IF NOT EXISTS provisioning_correlation_id uuid;

CREATE INDEX IF NOT EXISTS idx_fpo_event_inbox_claim
    ON public.fpo_event_inbox (consumer_name, status, available_at, created_at);

CREATE TABLE IF NOT EXISTS public.fpo_service_heartbeats (
    service_name text PRIMARY KEY,
    heartbeat_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
