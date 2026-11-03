BEGIN;

ALTER TABLE public.account_invitations
    ADD COLUMN IF NOT EXISTS fpo_access_request_id uuid;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_account_invitations_fpo_access_request'
          AND conrelid = 'public.account_invitations'::regclass
    ) THEN
        ALTER TABLE public.account_invitations
            ADD CONSTRAINT fk_account_invitations_fpo_access_request
            FOREIGN KEY (fpo_access_request_id)
            REFERENCES public.fpo_access_requests(request_id)
            ON DELETE SET NULL;
    END IF;
END;
$$;

UPDATE public.account_invitations AS invitation
SET fpo_access_request_id = request.request_id
FROM public.fpo_access_requests AS request
WHERE invitation.role = 'fpo'
  AND invitation.fpo_access_request_id IS NULL
  AND invitation.metadata->>'access_request_id' = request.request_id::text;

WITH ranked_actionable_requests AS (
    SELECT
        request.request_id,
        row_number() OVER (
            PARTITION BY lower(request.contact_email)
            ORDER BY
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM public.account_invitations AS invitation
                        WHERE invitation.role = 'fpo'
                          AND invitation.fpo_access_request_id = request.request_id
                    ) THEN 0
                    WHEN request.status = 'approved' THEN 1
                    ELSE 2
                END,
                request.created_at DESC,
                request.request_id
        ) AS position
    FROM public.fpo_access_requests AS request
    WHERE request.status IN ('pending', 'approved')
       OR (
           request.status = 'closed'
           AND EXISTS (
               SELECT 1
               FROM public.account_invitations AS invitation
               WHERE invitation.role = 'fpo'
                 AND invitation.fpo_access_request_id = request.request_id
           )
       )
),
superseded_requests AS (
    UPDATE public.fpo_access_requests AS request
    SET status = 'closed',
        review_note = left(
            concat_ws(
                E'\n',
                nullif(request.review_note, ''),
                'Closed during duplicate-request cleanup; the existing request or invitation for this email was retained.'
            ),
            2000
        ),
        reviewed_at = COALESCE(request.reviewed_at, now()),
        updated_at = now()
    FROM ranked_actionable_requests AS ranked
    WHERE request.request_id = ranked.request_id
      AND ranked.position > 1
    RETURNING request.request_id
)
UPDATE public.account_invitations AS invitation
SET revoked_at = now(),
    updated_at = now()
FROM superseded_requests AS superseded
WHERE invitation.role = 'fpo'
  AND invitation.fpo_access_request_id = superseded.request_id
  AND invitation.accepted_at IS NULL
  AND invitation.revoked_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_fpo_access_active_email
    ON public.fpo_access_requests (lower(contact_email))
    WHERE status IN ('pending', 'approved');

CREATE INDEX IF NOT EXISTS idx_account_invitations_fpo_access_request
    ON public.account_invitations (fpo_access_request_id, created_at DESC)
    WHERE role = 'fpo';

COMMIT;
