-- EURKAI_COCKPIT — SQLite Schema
-- Version: 1.0.0
-- Source: C01/SPEC_V1.md (LOCKED)

-- projects
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- briefs (toujours rattaché à un projet)
CREATE TABLE IF NOT EXISTS briefs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  goal TEXT,
  system_prompt TEXT,
  user_prompt TEXT NOT NULL,
  variables TEXT DEFAULT '{}',
  expected_output TEXT,
  tags TEXT DEFAULT '[]',
  policy TEXT DEFAULT '{"passes_in_a_row": 2, "max_iters": 8}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- runs
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  brief_id TEXT NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  output TEXT,
  logs TEXT,
  model TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT
);

-- secrets (globaux ou par projet)
CREATE TABLE IF NOT EXISTS secrets (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  value_encrypted BLOB NOT NULL,
  nonce BLOB NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(project_id, key)
);

-- config (clé/valeur système)
CREATE TABLE IF NOT EXISTS config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- tags (simple référentiel)
CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  color TEXT DEFAULT '#888888'
);

-- module_manifests (registry minimaliste)
CREATE TABLE IF NOT EXISTS module_manifests (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  version TEXT NOT NULL,
  description TEXT,
  inputs TEXT NOT NULL DEFAULT '[]',
  outputs TEXT NOT NULL DEFAULT '[]',
  constraints TEXT DEFAULT '{}',
  tags TEXT DEFAULT '[]',
  registered_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- backups (historique)
CREATE TABLE IF NOT EXISTS backups (
  id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  commit_sha TEXT,
  status TEXT NOT NULL,
  notes TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_briefs_project ON briefs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_brief ON runs(brief_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_secrets_project ON secrets(project_id);
