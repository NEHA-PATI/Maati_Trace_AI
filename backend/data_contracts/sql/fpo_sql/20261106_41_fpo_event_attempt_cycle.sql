BEGIN;

ALTER TABLE public.fpo_event_inbox
    ADD COLUMN IF NOT EXISTS attempts_in_cycle integer NOT NULL DEFAULT 0;

COMMIT;
