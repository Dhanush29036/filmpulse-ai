-- ============================================================
-- FilmPulse AI — PostgreSQL Schema (Phase 2)
-- Run: psql -U postgres -d filmpulse -f schema.sql
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for full-text similarity search

-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    email            VARCHAR(200) UNIQUE NOT NULL,
    name             VARCHAR(100) NOT NULL,
    hashed_password  VARCHAR(300) NOT NULL,
    company          VARCHAR(100),
    role             VARCHAR(20) DEFAULT 'producer',
    avatar_initials  VARCHAR(3),
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================
-- 2. FILMS TABLE  (extended)
-- ============================================================
CREATE TABLE IF NOT EXISTS films (
    id                  SERIAL PRIMARY KEY,
    film_id             VARCHAR(20) UNIQUE NOT NULL,          -- e.g. "FP-001234"
    title               VARCHAR(200) NOT NULL,
    genre               VARCHAR(50),
    language            VARCHAR(50),
    budget              NUMERIC(15,2),                        -- production budget (INR)
    release_date        DATE,
    platform            VARCHAR(50),                         -- 'Theatre'|'OTT'|'Both'

    -- Performance metrics
    box_office          NUMERIC(15,2),                        -- actual box-office (INR)
    ott_views           BIGINT,                               -- OTT streams/views
    
    -- ML-derived scores (written after analysis)
    discoverability     NUMERIC(5,2),                         -- 0–100
    hype_score          NUMERIC(5,2),                         -- 0–100
    revenue_estimate    NUMERIC(15,2),                        -- ML mid-point estimate
    grade               VARCHAR(2),                           -- 'A'|'B'|'C'|'D'
    
    -- Metadata
    director            VARCHAR(100),
    production_house    VARCHAR(100),
    cast_popularity     NUMERIC(4,2) DEFAULT 7.0,
    status              VARCHAR(20) DEFAULT 'registered',     -- 'registered'|'analyzed'|'released'
    trailer_url         TEXT,
    poster_url          TEXT,

    -- Ownership
    owner_id            INTEGER REFERENCES users(id) ON DELETE SET NULL,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_films_genre        ON films(genre);
CREATE INDEX IF NOT EXISTS idx_films_language     ON films(language);
CREATE INDEX IF NOT EXISTS idx_films_owner        ON films(owner_id);
CREATE INDEX IF NOT EXISTS idx_films_status       ON films(status);
CREATE INDEX IF NOT EXISTS idx_films_release_date ON films(release_date);
CREATE INDEX IF NOT EXISTS idx_films_title_trgm   ON films USING gin(title gin_trgm_ops);  -- fuzzy title search

-- ============================================================
-- 3. AUDIENCE SEGMENTS TABLE  (extended)
-- ============================================================
CREATE TABLE IF NOT EXISTS audience_segments (
    id               SERIAL PRIMARY KEY,
    film_id          INTEGER REFERENCES films(id) ON DELETE CASCADE,

    -- Demographic breakdowns
    age_group        VARCHAR(20),           -- '18-24'|'25-34'|'35-44'|'45+'
    gender           VARCHAR(10),           -- 'male'|'female'|'all'
    region           VARCHAR(50),           -- 'North India'|'South India'|'Metro'|...
    tier             VARCHAR(20),           -- 'Tier 1'|'Tier 2'|'Tier 3' city tier

    -- Interest profile
    interest_tags    JSONB,                 -- ["action", "thriller", "superhero"]
    
    -- Predicted scores
    engagement_score NUMERIC(5,2),          -- 0–100
    reach_pct        NUMERIC(5,2),          -- % of target segment reachable
    affinity_score   NUMERIC(5,2),          -- 0–100 genre-audience affinity

    -- Source
    source           VARCHAR(30) DEFAULT 'ml_model',  -- 'ml_model'|'survey'|'api'

    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audience_film    ON audience_segments(film_id);
CREATE INDEX IF NOT EXISTS idx_audience_age     ON audience_segments(age_group);
CREATE INDEX IF NOT EXISTS idx_audience_region  ON audience_segments(region);

-- ============================================================
-- 4. CAMPAIGNS TABLE  (extended)
-- ============================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id               SERIAL PRIMARY KEY,
    film_id          INTEGER REFERENCES films(id) ON DELETE CASCADE,

    -- Channel info
    platform         VARCHAR(50) NOT NULL,  -- 'YouTube Ads'|'Instagram'|'TV Spots'|...
    campaign_name    VARCHAR(200),

    -- Budget & Performance
    budget           NUMERIC(15,2),         -- allocated budget (INR)
    actual_spend     NUMERIC(15,2),         -- actual amount spent
    roi              NUMERIC(6,3),          -- return on investment (e.g. 2.45x)
    impressions      BIGINT,                -- total impressions
    clicks           INTEGER,               -- total clicks
    conversions      INTEGER,               -- total conversions (ticket/app installs)
    cpm              NUMERIC(10,2),         -- cost per 1000 impressions
    ctr              NUMERIC(5,4),          -- click-through rate

    -- Timeline
    start_date       DATE,
    end_date         DATE,
    spend_date       DATE,

    -- AI recommendation
    ai_recommended   BOOLEAN DEFAULT FALSE,
    allocation_pct   NUMERIC(5,2),           -- % of total budget allocated by ML

    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_film     ON campaigns(film_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_platform ON campaigns(platform);
CREATE INDEX IF NOT EXISTS idx_campaigns_date     ON campaigns(spend_date);

-- ============================================================
-- 5. CHAT MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    role       VARCHAR(10) NOT NULL,   -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id);

-- ============================================================
-- 6. AUTO-UPDATE updated_at TRIGGER
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    CREATE TRIGGER trg_films_updated_at
        BEFORE UPDATE ON films
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_campaigns_updated_at
        BEFORE UPDATE ON campaigns
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- 7. SEED DATA
-- ============================================================
INSERT INTO users (email, name, hashed_password, company, role, avatar_initials)
VALUES ('demo@filmpulse.ai', 'Demo Producer', '$2b$12$placeholder_hash_change_me', 'FilmPulse Demo', 'producer', 'DP')
ON CONFLICT (email) DO NOTHING;

INSERT INTO films (film_id, title, genre, language, budget, release_date, platform, box_office, ott_views, discoverability, hype_score, revenue_estimate, grade, director, cast_popularity, status)
VALUES
  ('FP-000001', 'Action Storm',    'Action',  'Hindi',   80000000, '2025-06-15', 'Both',    185000000, 8500000,  78.4, 82.1, 185, 'B', 'Rohit Shetty', 8.5, 'analyzed'),
  ('FP-000002', 'Love in Mumbai',  'Romance', 'Hindi',   30000000, '2025-02-14', 'OTT',     NULL,      15200000, 65.2, 71.5, 68,  'C', 'Imtiaz Ali',   7.0, 'analyzed'),
  ('FP-000003', 'Dark Signal',     'Thriller','English', 20000000, '2025-04-10', 'Both',    42000000,  3200000,  82.9, 76.3, 98,  'A', 'Anurag Kashyap',7.8,'analyzed')
ON CONFLICT DO NOTHING;

INSERT INTO audience_segments (film_id, age_group, gender, region, tier, interest_tags, engagement_score, reach_pct, affinity_score, source)
SELECT
    f.id, '18-24', 'all', 'Metro Cities', 'Tier 1',
    '["action", "adventure", "blockbuster"]'::jsonb,
    88.5, 72.0, 91.2, 'ml_model'
FROM films f WHERE f.film_id = 'FP-000001'
ON CONFLICT DO NOTHING;

INSERT INTO campaigns (film_id, platform, campaign_name, budget, roi, impressions, allocation_pct, ai_recommended)
SELECT
    f.id, 'YouTube Ads', 'Action Storm — Pre-Release Blitz',
    22400000, 2.84, 45000000, 28.0, TRUE
FROM films f WHERE f.film_id = 'FP-000001'
ON CONFLICT DO NOTHING;
