CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE,
    email TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'farmer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS registered_farms (
    farm_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    district_name TEXT NOT NULL,
    area_acres NUMERIC(12,4),
    polygon_geometry GEOMETRY(POLYGON, 4326) NOT NULL,
    h3_res12 BIGINT[] NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_registered_farms_user
ON registered_farms(user_id);

CREATE INDEX IF NOT EXISTS idx_registered_farms_district
ON registered_farms(district_name);

CREATE INDEX IF NOT EXISTS idx_registered_farms_h3
ON registered_farms USING GIN(h3_res12);

CREATE INDEX IF NOT EXISTS idx_registered_farms_geom
ON registered_farms USING GIST(polygon_geometry);

CREATE TABLE IF NOT EXISTS pipeline_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL,
    job_type TEXT NOT NULL,
    district_name TEXT,
    status TEXT NOT NULL,
    input_uri TEXT,
    output_uri TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_status
ON pipeline_jobs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_jobs_service
ON pipeline_jobs(service_name);

CREATE TABLE IF NOT EXISTS farm_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL REFERENCES registered_farms(farm_id),
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    source_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_farm_alerts_farm_date
ON farm_alerts(farm_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_farm_alerts_severity
ON farm_alerts(severity);