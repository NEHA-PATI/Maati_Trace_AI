CREATE TABLE IF NOT EXISTS states (
    state_code INTEGER PRIMARY KEY,
    state_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS districts (
    district_code INTEGER PRIMARY KEY,
    district_name TEXT NOT NULL,
    state_code INTEGER NOT NULL REFERENCES states(state_code),
    state_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (district_name, state_code)
);

CREATE INDEX IF NOT EXISTS idx_districts_state_code
ON districts(state_code);

CREATE INDEX IF NOT EXISTS idx_districts_name
ON districts(lower(district_name));

CREATE TABLE IF NOT EXISTS blocks (
    block_code INTEGER PRIMARY KEY,
    block_name TEXT NOT NULL,
    district_code INTEGER REFERENCES districts(district_code),
    district_name TEXT NOT NULL,
    state_code INTEGER,
    state_name TEXT DEFAULT 'Odisha',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blocks_district_code
ON blocks(district_code);

CREATE INDEX IF NOT EXISTS idx_blocks_district_name
ON blocks(lower(district_name));

CREATE INDEX IF NOT EXISTS idx_blocks_name
ON blocks(lower(block_name));

CREATE INDEX IF NOT EXISTS idx_blocks_state_district
ON blocks(lower(state_name), lower(district_name));