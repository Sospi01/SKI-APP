-- Ski Info local database schema.
-- Populated by ski_pipeline from OpenSkiMap's ski_areas/runs/lifts GeoJSON.

CREATE TABLE IF NOT EXISTS ski_areas (
    id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    activities TEXT,          -- comma-separated: downhill,nordic
    run_convention TEXT,      -- europe / north_america / japan
    country_code TEXT,
    region TEXT,
    locality TEXT,
    latitude REAL,
    longitude REAL,
    min_elevation_m REAL,
    max_elevation_m REAL,
    wikidata_id TEXT,
    websites TEXT             -- JSON array, as text
);

-- Km of piste and run count per ski area, broken down by activity and difficulty.
-- Precomputed upstream by OpenSkiMap; we just flatten it into rows.
CREATE TABLE IF NOT EXISTS ski_area_run_stats (
    ski_area_id TEXT NOT NULL REFERENCES ski_areas(id),
    activity TEXT NOT NULL,          -- downhill / nordic / other
    difficulty TEXT NOT NULL,        -- novice / easy / intermediate / advanced / expert / freeride / extreme / other
    run_count INTEGER NOT NULL DEFAULT 0,
    length_km REAL NOT NULL DEFAULT 0,
    snowmaking_length_km REAL,
    snowfarming_length_km REAL,
    PRIMARY KEY (ski_area_id, activity, difficulty)
);

CREATE TABLE IF NOT EXISTS ski_area_lift_stats (
    ski_area_id TEXT NOT NULL REFERENCES ski_areas(id),
    lift_type TEXT NOT NULL,
    lift_count INTEGER NOT NULL DEFAULT 0,
    length_km REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (ski_area_id, lift_type)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    name TEXT,
    ref TEXT,
    status TEXT,
    difficulty TEXT,
    difficulty_convention TEXT,
    grooming TEXT,
    uses TEXT,                 -- comma-separated
    lit INTEGER,               -- 0/1/NULL (unknown)
    gladed INTEGER,
    patrolled INTEGER,
    snowmaking INTEGER,
    snowfarming INTEGER,
    oneway INTEGER,
    tunnel INTEGER,
    geometry_type TEXT,
    length_m REAL,
    ascent_m REAL,
    descent_m REAL,
    vertical_m REAL,
    min_elevation_m REAL,
    max_elevation_m REAL,
    avg_pitch_percent REAL,
    max_pitch_percent REAL,
    geometry_json TEXT         -- raw GeoJSON geometry, for map rendering in the app
);

-- A run can belong to more than one ski area (shared lift/piste systems).
CREATE TABLE IF NOT EXISTS run_ski_areas (
    run_id TEXT NOT NULL REFERENCES runs(id),
    ski_area_id TEXT NOT NULL REFERENCES ski_areas(id),
    PRIMARY KEY (run_id, ski_area_id)
);

CREATE TABLE IF NOT EXISTS lifts (
    id TEXT PRIMARY KEY,
    name TEXT,
    ref TEXT,
    lift_type TEXT,
    status TEXT,
    access TEXT,               -- 'private' or NULL
    occupancy INTEGER,
    capacity INTEGER,
    duration_s INTEGER,
    detachable INTEGER,
    bubble INTEGER,
    heating INTEGER,
    oneway INTEGER,
    tunnel INTEGER,
    length_m REAL,
    vertical_m REAL,
    geometry_json TEXT
);

CREATE TABLE IF NOT EXISTS lift_ski_areas (
    lift_id TEXT NOT NULL REFERENCES lifts(id),
    ski_area_id TEXT NOT NULL REFERENCES ski_areas(id),
    PRIMARY KEY (lift_id, ski_area_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_difficulty ON runs(difficulty);
CREATE INDEX IF NOT EXISTS idx_lifts_type ON lifts(lift_type);
CREATE INDEX IF NOT EXISTS idx_ski_areas_country ON ski_areas(country_code);
CREATE INDEX IF NOT EXISTS idx_run_ski_areas_ski_area ON run_ski_areas(ski_area_id);
CREATE INDEX IF NOT EXISTS idx_lift_ski_areas_ski_area ON lift_ski_areas(ski_area_id);
