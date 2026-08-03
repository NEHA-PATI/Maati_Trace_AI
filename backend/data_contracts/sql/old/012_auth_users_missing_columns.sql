-- Auth service compatibility migration
-- Fixes: column users.onboarding_status does not exist
-- Safe to run once or repeatedly in pgAdmin.

BEGIN;

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS onboarding_status TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS profile_image_url TEXT;

COMMIT;

