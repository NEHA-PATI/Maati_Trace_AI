ALTER TABLE public.refresh_tokens
ADD COLUMN IF NOT EXISTS replaced_by_token_hash text;