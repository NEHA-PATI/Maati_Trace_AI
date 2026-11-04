BEGIN;

CREATE TABLE IF NOT EXISTS public.fpo_api_clients (
    client_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    client_name varchar(160) NOT NULL, client_identifier varchar(80) NOT NULL, secret_hash varchar(128) NOT NULL, scopes jsonb NOT NULL DEFAULT '[]'::jsonb,
    rate_limit_per_minute integer NOT NULL DEFAULT 60, ip_allowlist jsonb NOT NULL DEFAULT '[]'::jsonb, status varchar(20) NOT NULL DEFAULT 'ACTIVE',
    last_used_at timestamptz, expires_at timestamptz, revoked_at timestamptz, created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_api_client_identifier UNIQUE (fpo_id,client_identifier), CONSTRAINT ck_fpo_api_client_status CHECK (status IN ('ACTIVE','REVOKED','EXPIRED','DISABLED'))
);
CREATE TABLE IF NOT EXISTS public.fpo_webhook_subscriptions (
    subscription_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE,
    name varchar(160) NOT NULL, endpoint_url varchar(500) NOT NULL, secret_hash varchar(128) NOT NULL, event_types jsonb NOT NULL DEFAULT '[]'::jsonb,
    status varchar(20) NOT NULL DEFAULT 'PENDING_VERIFICATION', failure_count integer NOT NULL DEFAULT 0, last_delivered_at timestamptz, disabled_at timestamptz,
    created_by_user_id uuid NOT NULL REFERENCES public.users(user_id) ON DELETE RESTRICT, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_fpo_webhook_status CHECK (status IN ('PENDING_VERIFICATION','ACTIVE','PAUSED','DISABLED'))
);
CREATE TABLE IF NOT EXISTS public.fpo_webhook_deliveries (
    delivery_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), fpo_id uuid NOT NULL REFERENCES public.fpo_organizations(fpo_id) ON DELETE CASCADE, subscription_id uuid NOT NULL REFERENCES public.fpo_webhook_subscriptions(subscription_id) ON DELETE CASCADE,
    event_id uuid NOT NULL, event_type varchar(120) NOT NULL, payload_hash varchar(128) NOT NULL, attempt_count integer NOT NULL DEFAULT 0, status varchar(20) NOT NULL DEFAULT 'QUEUED', response_status integer, next_attempt_at timestamptz, delivered_at timestamptz, last_error text, created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_fpo_webhook_delivery UNIQUE (subscription_id,event_id), CONSTRAINT ck_fpo_webhook_delivery_status CHECK (status IN ('QUEUED','DELIVERED','RETRYING','DEAD','CANCELLED'))
);
CREATE INDEX IF NOT EXISTS idx_fpo_webhook_delivery_queue ON public.fpo_webhook_deliveries (status,next_attempt_at);

COMMIT;
