BEGIN;

-- Class A operational surface: portfolio summary and auditable alerts.
CREATE TABLE IF NOT EXISTS public.fpo_operational_alerts (
    alert_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    alert_type varchar(80) NOT NULL,
    severity varchar(20) NOT NULL DEFAULT 'INFO',
    title varchar(180) NOT NULL,
    message text NOT NULL,
    source varchar(80) NOT NULL DEFAULT 'SYSTEM',
    status varchar(30) NOT NULL DEFAULT 'OPEN',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    acknowledged_by uuid REFERENCES public.users(user_id) ON DELETE SET NULL,
    acknowledged_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_alert_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    CONSTRAINT ck_fpo_alert_status CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED'))
);

CREATE INDEX IF NOT EXISTS idx_fpo_operational_alerts_inbox
    ON public.fpo_operational_alerts (fpo_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fpo_operational_alerts_type
    ON public.fpo_operational_alerts (fpo_id, alert_type, created_at DESC);

COMMIT;
