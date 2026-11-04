BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_support_tickets (
    ticket_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    farm_id uuid REFERENCES public.farms(farm_id) ON DELETE SET NULL,
    fpo_id uuid REFERENCES public.fpo_organizations(fpo_id) ON DELETE SET NULL,
    category varchar(40) NOT NULL DEFAULT 'ACCESS',
    subject varchar(180) NOT NULL,
    description text NOT NULL,
    status varchar(25) NOT NULL DEFAULT 'OPEN',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_support_ticket_category CHECK (category IN ('ACCESS','CONSENT','DOCUMENTS','FARM_DATA','OTHER')),
    CONSTRAINT ck_fpo_support_ticket_status CHECK (status IN ('OPEN','IN_PROGRESS','RESOLVED','CLOSED'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_support_tickets_farmer
    ON public.fpo_support_tickets (farmer_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_support_tickets_fpo
    ON public.fpo_support_tickets (fpo_id, status, created_at DESC);

COMMIT;
