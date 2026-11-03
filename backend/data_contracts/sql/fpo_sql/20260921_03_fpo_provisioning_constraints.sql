BEGIN;

-- Compatibility cleanup before the provisioning worker writes the canonical owner role.
-- Existing deployments may have named this check constraint differently, so remove
-- only checks whose definition explicitly restricts fpo_users.role/fpo_role.
DO $$
DECLARE
    constraint_row record;
BEGIN
    FOR constraint_row IN
        SELECT c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
          AND t.relname = 'fpo_users'
          AND c.contype = 'c'
          AND pg_get_constraintdef(c.oid) ILIKE '%role%'
    LOOP
        EXECUTE format('ALTER TABLE public.fpo_users DROP CONSTRAINT IF EXISTS %I', constraint_row.conname);
    END LOOP;
END $$;

UPDATE public.fpo_users
SET fpo_role = 'owner', role = 'owner', updated_at = now()
WHERE is_active = TRUE;

ALTER TABLE public.fpo_users
    ADD CONSTRAINT ck_fpo_users_owner_role
    CHECK (fpo_role = 'owner' AND role = 'owner');

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_one_active_account
    ON public.fpo_users (fpo_id)
    WHERE is_active = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_account_one_active_org
    ON public.fpo_users (user_id)
    WHERE is_active = TRUE;

COMMIT;
