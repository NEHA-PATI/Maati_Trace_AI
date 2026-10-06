-- Phase 1: historical acquisition control plane.
-- Execute once against the MaatiTrace PostgreSQL database before starting the API.
-- Safe to re-run: all objects are created idempotently.

CREATE SCHEMA IF NOT EXISTS ml_acquisition;

CREATE TABLE IF NOT EXISTS ml_acquisition.jobs (
  job_id uuid PRIMARY KEY,
  request_hash text NOT NULL UNIQUE,
  request jsonb NOT NULL,
  status text NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','running','succeeded','partial','failed','cancelled')),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  total_shards bigint NOT NULL DEFAULT 0,
  actual_bytes bigint NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ml_acquisition.shards (
  shard_id text PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES ml_acquisition.jobs(job_id),
  spec jsonb NOT NULL,
  state text NOT NULL DEFAULT 'planned' CHECK (state IN ('planned','running','succeeded','retryable','failed','cancelled')),
  attempts integer NOT NULL DEFAULT 0,
  lease_owner text,
  lease_until timestamptz,
  item_count bigint NOT NULL DEFAULT 0,
  asset_count bigint NOT NULL DEFAULT 0,
  byte_count bigint NOT NULL DEFAULT 0,
  error_class text,
  error_message text,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS acquisition_claim_idx ON ml_acquisition.shards(state, lease_until, updated_at);
CREATE INDEX IF NOT EXISTS acquisition_job_shards_idx ON ml_acquisition.shards(job_id, state);
CREATE INDEX IF NOT EXISTS acquisition_running_source_idx ON ml_acquisition.shards ((spec->>'source'), lease_until) WHERE state='running';

CREATE TABLE IF NOT EXISTS ml_acquisition.events (
  event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES ml_acquisition.jobs(job_id),
  shard_id text,
  event_type text NOT NULL,
  message text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS acquisition_events_job_idx ON ml_acquisition.events(job_id, created_at DESC);
