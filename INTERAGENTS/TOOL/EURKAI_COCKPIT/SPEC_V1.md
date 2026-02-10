# EURKAI_COCKPIT — SPEC_V1

**Version** : 1.0.0  
**Date** : 2025-01-12  
**Statut** : VERROUILLÉ

---

## 1. Vue d'ensemble

Cockpit local-first pour orchestrer des briefs IA, gérer des projets, et préparer l'intégration de modules plug-and-play.

### Stack technique

| Couche | Choix | Justification |
|--------|-------|---------------|
| Backend | Python 3.11+ / FastAPI | Cohérent existant, async, rapide |
| Frontend | React 18 + Vite | Standard, évolutif |
| DB | SQLite (sqlite3/aiosqlite) | Local-first, contrôle total |
| Chiffrement | AES-256-GCM | Secrets at-rest |

---

## 2. Data Model

### 2.1 Tables

```sql
-- projects
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- briefs (toujours rattaché à un projet)
CREATE TABLE briefs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  goal TEXT,
  system_prompt TEXT,
  user_prompt TEXT NOT NULL,
  variables TEXT DEFAULT '{}',  -- JSON
  expected_output TEXT,
  tags TEXT DEFAULT '[]',       -- JSON array
  policy TEXT DEFAULT '{"passes_in_a_row": 2, "max_iters": 8}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- runs
CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  brief_id TEXT NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending|running|success|failed
  output TEXT,
  logs TEXT,
  model TEXT,
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  finished_at TEXT
);

-- secrets (globaux ou par projet)
CREATE TABLE secrets (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,  -- NULL = global
  key TEXT NOT NULL,
  value_encrypted BLOB NOT NULL,
  nonce BLOB NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(project_id, key)
);

-- config (clé/valeur système)
CREATE TABLE config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- tags (simple référentiel)
CREATE TABLE tags (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  color TEXT DEFAULT '#888888'
);

-- module_manifests (registry minimaliste)
CREATE TABLE module_manifests (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  version TEXT NOT NULL,
  description TEXT,
  inputs TEXT NOT NULL DEFAULT '[]',   -- JSON array
  outputs TEXT NOT NULL DEFAULT '[]',  -- JSON array
  constraints TEXT DEFAULT '{}',
  tags TEXT DEFAULT '[]',
  registered_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- backups (historique)
CREATE TABLE backups (
  id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  commit_sha TEXT,
  status TEXT NOT NULL,  -- success|failed|dry_run
  notes TEXT
);
```

### 2.2 Index recommandés

```sql
CREATE INDEX idx_briefs_project ON briefs(project_id);
CREATE INDEX idx_runs_brief ON runs(brief_id);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_secrets_project ON secrets(project_id);
```

---

## 3. Écrans (Frontend)

### 3.1 Navigation principale

```
┌─────────────────────────────────────────────┐
│  EURKAI COCKPIT                    [⚙️]    │
├─────────────────────────────────────────────┤
│  📁 Projects                                │
│  📝 Briefs                                  │
│  🔐 Secrets                                 │
│  📦 Modules                                 │
│  💾 Backups                                 │
│  ⚙️  Config                                 │
└─────────────────────────────────────────────┘
```

### 3.2 Écrans détaillés

| Écran | Route | Fonctions |
|-------|-------|----------|
| Projects List | `/projects` | CRUD projets, filtres, stats briefs |
| Project Detail | `/projects/:id` | Détail, liste briefs liés |
| Briefs List | `/briefs` | Tous briefs, filtre par projet/tag |
| Brief Editor | `/briefs/:id` | Édition complète, lancer run |
| Brief Runs | `/briefs/:id/runs` | Historique runs, logs |
| Secrets | `/secrets` | Liste masquée, CRUD avec gate mdp |
| Modules | `/modules` | Registry, compatibilité i/o |
| Backups | `/backups` | Historique, trigger manuel |
| Config | `/config` | Paramètres système |

---

## 4. API Endpoints

### 4.1 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | Liste tous les projets |
| POST | `/api/projects` | Créer un projet |
| GET | `/api/projects/{id}` | Détail projet |
| PUT | `/api/projects/{id}` | Modifier projet |
| DELETE | `/api/projects/{id}` | Supprimer (cascade briefs) |

### 4.2 Briefs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/briefs` | Liste (filtre ?project_id=) |
| POST | `/api/briefs` | Créer brief (project_id requis) |
| GET | `/api/briefs/{id}` | Détail brief |
| PUT | `/api/briefs/{id}` | Modifier brief |
| DELETE | `/api/briefs/{id}` | Supprimer brief |
| POST | `/api/briefs/{id}/run` | Lancer un run |

### 4.3 Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/briefs/{id}/runs` | Historique runs du brief |
| GET | `/api/runs/{id}` | Détail run |
| DELETE | `/api/runs/{id}` | Supprimer run |

### 4.4 Secrets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/secrets` | Liste (clés seulement, jamais valeurs) |
| POST | `/api/secrets` | Créer secret |
| GET | `/api/secrets/{id}/copy` | Copier valeur (gate mdp requis) |
| PUT | `/api/secrets/{id}` | Modifier secret |
| DELETE | `/api/secrets/{id}` | Supprimer secret |
| POST | `/api/secrets/unlock` | Déverrouiller session (mdp master) |

### 4.5 Modules

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/modules` | Liste manifests |
| POST | `/api/modules` | Enregistrer manifest |
| GET | `/api/modules/{id}` | Détail manifest |
| DELETE | `/api/modules/{id}` | Retirer du registry |
| GET | `/api/modules/compatible` | Vérifier compatibilité i/o |

### 4.6 Backups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/backups` | Historique backups |
| POST | `/api/backups` | Déclencher backup |
| POST | `/api/backups/dry-run` | Test sans commit |

### 4.7 Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Liste config |
| PUT | `/api/config/{key}` | Modifier valeur |

---

## 5. Permissions (MVP)

**Pas de multi-user** → permissions implicites.

| Action | Règle |
|--------|-------|
| Lecture | Toujours autorisé |
| Écriture | Toujours autorisé |
| Secrets copy | Gate mdp master requis |
| Backup | Git configuré requis (sinon dry-run) |

---

## 6. Secrets — Flux détaillé

```
┌──────────────┐     POST /secrets/unlock      ┌──────────────┐
│   UI/CLI     │ ────────────────────────────▶ │   Backend    │
│              │   { master_password }         │              │
└──────────────┘                               └──────────────┘
       │                                              │
       │         { session_token, ttl: 300s }        │
       │◀─────────────────────────────────────────────│
       │                                              │
       │     GET /secrets/{id}/copy                  │
       │     Header: X-Session-Token: xxx            │
       │─────────────────────────────────────────────▶│
       │                                              │
       │         { value: "decrypted" }              │
       │◀─────────────────────────────────────────────│
```

---

## 7. Backup — Flux détaillé

```
POST /api/backups
       │
       ▼
┌─────────────────┐
│ 1. Export .db   │
│ 2. Export .json │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     git configured?    ┌─────────────────┐
│ Check git repo  │────────────────────────│  NO → dry_run   │
└────────┬────────┘                        │  local dump     │
         │ YES                             └─────────────────┘
         ▼
┌─────────────────┐
│ Commit to       │
│ backup/auto     │
│ branch          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log to backups  │
│ table           │
└─────────────────┘
```

---

## 8. Contraintes techniques

- **IDs** : UUIDv4 (text)
- **Dates** : ISO 8601 UTC
- **JSON fields** : validés à l'écriture
- **Chiffrement secrets** : AES-256-GCM, clé dérivée de master_password via PBKDF2
- **Session unlock** : token mémoire, TTL 5 min, non persisté

---

## 9. Limitations MVP

- ❌ Pas de multi-user
- ❌ Pas de cloud deploy
- ❌ Pas de marketplace modules
- ❌ Pas de tracking coût/tokens
- ❌ Pas de résolution auto dépendances modules
- ❌ Pas de backup auto (cron)

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-01-12 | Initial spec verrouillée |
