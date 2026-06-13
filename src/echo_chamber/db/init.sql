-- ECHO CHAMBER — Database Initialisation
-- Executed automatically by Docker Compose on first run.

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Signals Table ──────────────────────────────────────────────────────
-- Raw signals ingested from all sources (Reddit, RSS, manual, etc.)
CREATE TABLE IF NOT EXISTS signals (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    platform        TEXT,
    community       TEXT,
    content         TEXT NOT NULL,
    url             TEXT,
    author          TEXT,
    category        TEXT,  -- trend / mention / opportunity / threat / noise
    confidence      REAL DEFAULT 0.0,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_signals_source ON signals (source);
CREATE INDEX IF NOT EXISTS idx_signals_platform ON signals (platform);
CREATE INDEX IF NOT EXISTS idx_signals_category ON signals (category);
CREATE INDEX IF NOT EXISTS idx_signals_ingested_at ON signals (ingested_at DESC);

-- ── Deployments Table ──────────────────────────────────────────────────
-- Every content deployment tracked for memory & learning.
CREATE TABLE IF NOT EXISTS deployments (
    id              BIGSERIAL PRIMARY KEY,
    client_id       TEXT,
    deployment_id   UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    platform        TEXT NOT NULL,
    community       TEXT,
    account_id      TEXT,
    content         TEXT NOT NULL,
    autonomy_level  TEXT NOT NULL DEFAULT 'L1',
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / deployed / monitoring / complete / rejected / burned
    deployed_at     TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    metrics         JSONB DEFAULT '{}'::jsonb,
    embedding       vector(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deployments_client ON deployments (client_id);
CREATE INDEX IF NOT EXISTS idx_deployments_platform ON deployments (platform);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments (status);
CREATE INDEX IF NOT EXISTS idx_deployments_embedding ON deployments
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ── Accounts Table ─────────────────────────────────────────────────────
-- Ghost account pool management.
CREATE TABLE IF NOT EXISTS accounts (
    id              BIGSERIAL PRIMARY KEY,
    platform        TEXT NOT NULL,
    username        TEXT NOT NULL,
    credentials     JSONB NOT NULL DEFAULT '{}'::jsonb,  -- encrypted tokens
    status          TEXT NOT NULL DEFAULT 'maturing',  -- maturing / active / cooldown / burned
    karma           INTEGER DEFAULT 0,
    age_days        INTEGER DEFAULT 0,
    last_used_at    TIMESTAMPTZ,
    subreddits      TEXT[] DEFAULT '{}',
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts (platform);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts (status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_platform_username ON accounts (platform, username);

-- ── Clients Table ──────────────────────────────────────────────────────
-- Onboarded client profiles.
CREATE TABLE IF NOT EXISTS clients (
    id              BIGSERIAL PRIMARY KEY,
    client_id       TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    url             TEXT NOT NULL,
    voice_profile   JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraints     JSONB DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'active',  -- active / paused / archived
    onboarded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'::jsonb
);

-- ── Semantic Memory Table ──────────────────────────────────────────────
-- Cross-client patterns and lessons.
CREATE TABLE IF NOT EXISTS semantic_memory (
    id              BIGSERIAL PRIMARY KEY,
    pattern         TEXT NOT NULL,
    evidence_ids    BIGINT[] DEFAULT '{}',  -- references to deployments.id
    client_ids      TEXT[] DEFAULT '{}',
    confidence      REAL DEFAULT 0.0,
    reinforced_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_semantic_memory_confidence ON semantic_memory (confidence DESC);

-- ── Audit Log Table ────────────────────────────────────────────────────
-- All Commander actions logged for accountability.
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    target_type     TEXT,
    target_id       TEXT,
    details         JSONB DEFAULT '{}'::jsonb,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log (actor);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log (timestamp DESC);
