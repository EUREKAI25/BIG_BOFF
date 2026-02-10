-- EURKAI_COCKPIT — Schema v1.0.0
-- Generated: C02 Data Model + Storage
-- IDs: UUID (TEXT)
-- Dates: ISO 8601 UTC
-- JSON fields: validated at write time

PRAGMA foreign_keys = ON;

-- ============================================
-- PROJECTS
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    root_path TEXT,
    tags TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- BRIEFS (always attached to a project)
-- ============================================
CREATE TABLE IF NOT EXISTS briefs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    goal TEXT,
    system_prompt TEXT,
    user_prompt TEXT NOT NULL,
    variables_json TEXT DEFAULT '{}',
    expected_output TEXT,
    tags TEXT DEFAULT '[]',
    policy TEXT DEFAULT '{"passes_in_a_row": 2, "max_iters": 8}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- RUNS
-- ============================================
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    brief_id TEXT NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed')),
    result_json TEXT,
    logs_json TEXT DEFAULT '[]',
    error TEXT,
    model TEXT,
    duration_ms INTEGER,
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- CONFIG (key/value system settings)
-- ============================================
CREATE TABLE IF NOT EXISTS config (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- SECRETS (encrypted, global or project-scoped)
-- ============================================
CREATE TABLE IF NOT EXISTS secrets (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL,
    encrypted_value BLOB NOT NULL,
    nonce BLOB NOT NULL,
    scope TEXT NOT NULL DEFAULT 'global' CHECK (scope IN ('global', 'project')),
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(key, scope, project_id)
);

-- ============================================
-- MODULES (manifest registry)
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    description TEXT,
    manifest_json TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- BACKUPS (history)
-- ============================================
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    commit_sha TEXT,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'dry_run')),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_briefs_project ON briefs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_brief ON runs(brief_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_run_id ON runs(run_id);
CREATE INDEX IF NOT EXISTS idx_secrets_scope ON secrets(scope);
CREATE INDEX IF NOT EXISTS idx_secrets_project ON secrets(project_id);
CREATE INDEX IF NOT EXISTS idx_modules_name ON modules(name);
CREATE INDEX IF NOT EXISTS idx_config_key ON config(key);
