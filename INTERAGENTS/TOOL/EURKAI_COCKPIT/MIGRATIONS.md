# MIGRATIONS.md — EURKAI_COCKPIT

> **Version:** 1.0.0  
> **Chantier:** C00 — Versioning & Release Hygiene  
> **Status:** STABLE

---

## 1. Philosophie de migration

### 1.1 Principes

| Principe | Description |
|----------|-------------|
| **Backward compat by default** | Ajouts = MINOR, suppressions = MAJOR |
| **No silent breaks** | Toute migration documentée ici |
| **Rollback possible** | Chaque migration a son rollback |
| **SQLite-first** | V1 = SQLite, PostgreSQL = trajectoire future |

### 1.2 Quand migrer ?

| Changement | Migration requise ? | Bump |
|------------|-------------------|------|
| Ajout colonne nullable | ❌ Non | MINOR |
| Ajout colonne NOT NULL | ✅ Oui (valeur default) | MINOR |
| Suppression colonne | ✅ Oui | MAJOR |
| Renommage colonne | ✅ Oui | MAJOR |
| Ajout table | ❌ Non | MINOR |
| Suppression table | ✅ Oui | MAJOR |
| Modification type colonne | ✅ Oui | MAJOR |

---

## 2. Structure des migrations

### 2.1 Dossier

```
backend/db/
├── schema.sql          # Schéma courant (source of truth)
├── migrations/
│   ├── 001_init.sql
│   ├── 002_add_runs_table.sql
│   ├── 003_add_secrets.sql
│   └── ...
└── rollbacks/
    ├── 001_init_rollback.sql
    ├── 002_add_runs_table_rollback.sql
    └── ...
```

### 2.2 Nommage

```
<NNN>_<description_snake_case>.sql
```

Exemples :
- `001_init.sql`
- `002_add_runs_table.sql`
- `003_rename_config_to_settings.sql`

### 2.3 Format d'un fichier migration

```sql
-- Migration: 002_add_runs_table
-- Version: 1.1.0
-- Date: 2025-01-15
-- Description: Add runs table for execution history
-- Breaking: NO

-- UP
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    started_at DATETIME,
    finished_at DATETIME,
    output_json TEXT,
    FOREIGN KEY (brief_id) REFERENCES briefs(id)
);

CREATE INDEX idx_runs_brief_id ON runs(brief_id);
CREATE INDEX idx_runs_status ON runs(status);
```

### 2.4 Format d'un fichier rollback

```sql
-- Rollback: 002_add_runs_table
-- Reverts to: 1.0.0

-- DOWN
DROP INDEX IF EXISTS idx_runs_status;
DROP INDEX IF EXISTS idx_runs_brief_id;
DROP TABLE IF EXISTS runs;
```

---

## 3. Exécution des migrations

### 3.1 Script de migration

```bash
#!/bin/bash
# scripts/migrate.sh

DB_PATH="${1:-data/cockpit.db}"
MIGRATIONS_DIR="backend/db/migrations"

# Créer table de tracking si absente
sqlite3 "$DB_PATH" <<EOF
CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
EOF

# Appliquer les migrations non appliquées
for migration in $(ls -1 "$MIGRATIONS_DIR"/*.sql | sort); do
    name=$(basename "$migration")
    
    # Vérifier si déjà appliquée
    applied=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM _migrations WHERE name='$name'")
    
    if [ "$applied" -eq 0 ]; then
        echo "Applying: $name"
        sqlite3 "$DB_PATH" < "$migration"
        sqlite3 "$DB_PATH" "INSERT INTO _migrations (name) VALUES ('$name')"
        echo "✓ Applied: $name"
    else
        echo "⊘ Already applied: $name"
    fi
done

echo "✓ Migrations complete"
```

### 3.2 Script de rollback

```bash
#!/bin/bash
# scripts/rollback.sh

DB_PATH="${1:-data/cockpit.db}"
ROLLBACKS_DIR="backend/db/rollbacks"
TARGET="${2:-1}"  # Nombre de migrations à rollback

# Récupérer les N dernières migrations
migrations=$(sqlite3 "$DB_PATH" \
    "SELECT name FROM _migrations ORDER BY id DESC LIMIT $TARGET")

for name in $migrations; do
    rollback_file="$ROLLBACKS_DIR/${name%.sql}_rollback.sql"
    
    if [ -f "$rollback_file" ]; then
        echo "Rolling back: $name"
        sqlite3 "$DB_PATH" < "$rollback_file"
        sqlite3 "$DB_PATH" "DELETE FROM _migrations WHERE name='$name'"
        echo "✓ Rolled back: $name"
    else
        echo "⚠ No rollback file for: $name"
        exit 1
    fi
done

echo "✓ Rollback complete"
```

---

## 4. Stratégies de compatibilité

### 4.1 Ajout de champ (compatible)

```sql
-- ✅ SAFE: ajout nullable
ALTER TABLE projects ADD COLUMN description TEXT;

-- ✅ SAFE: ajout avec default
ALTER TABLE projects ADD COLUMN priority INTEGER DEFAULT 0;
```

### 4.2 Suppression de champ (breaking)

```sql
-- ⚠️ BREAKING: SQLite ne supporte pas DROP COLUMN directement
-- Stratégie: recréer la table

-- 1. Créer nouvelle table sans la colonne
CREATE TABLE projects_new (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    -- 'legacy_field' supprimé
    created_at DATETIME
);

-- 2. Copier les données
INSERT INTO projects_new (id, name, created_at)
SELECT id, name, created_at FROM projects;

-- 3. Supprimer ancienne table
DROP TABLE projects;

-- 4. Renommer
ALTER TABLE projects_new RENAME TO projects;
```

### 4.3 Renommage de champ (breaking)

```sql
-- ⚠️ BREAKING: même stratégie que suppression
-- + mapping explicite des valeurs
```

### 4.4 Modification de type (breaking)

```sql
-- ⚠️ BREAKING: conversion de données requise
-- Exemple: TEXT → INTEGER

CREATE TABLE config_new (
    id INTEGER PRIMARY KEY,
    key TEXT NOT NULL,
    value INTEGER  -- était TEXT
);

INSERT INTO config_new (id, key, value)
SELECT id, key, CAST(value AS INTEGER) FROM config
WHERE value GLOB '[0-9]*';

-- Gérer les valeurs non convertibles séparément
```

---

## 5. Trajectoire PostgreSQL (future)

### 5.1 Quand migrer vers PostgreSQL ?

| Critère | Seuil |
|---------|-------|
| Volume de données | > 10 GB |
| Concurrence | > 10 users simultanés |
| Requêtes complexes | Besoin de CTEs, window functions avancées |
| Intégration Eurkai core | Quand core l'exige |

### 5.2 Plan de migration SQLite → PostgreSQL

```
Phase 1: Dual-write (SQLite + PG)
   ↓
Phase 2: Read from PG, write to both
   ↓
Phase 3: PG only, SQLite backup
   ↓
Phase 4: Deprecate SQLite
```

### 5.3 Script de migration (template)

```bash
#!/bin/bash
# scripts/migrate_to_postgres.sh (FUTURE - NOT V1)

# 1. Export SQLite
sqlite3 data/cockpit.db .dump > /tmp/sqlite_dump.sql

# 2. Convertir syntaxe
sed -i 's/INTEGER PRIMARY KEY AUTOINCREMENT/SERIAL PRIMARY KEY/g' /tmp/sqlite_dump.sql
sed -i 's/DATETIME/TIMESTAMP/g' /tmp/sqlite_dump.sql

# 3. Import PostgreSQL
psql -d eurkai_cockpit < /tmp/sqlite_dump.sql

# 4. Valider
psql -d eurkai_cockpit -c "SELECT COUNT(*) FROM projects"
```

### 5.4 Différences syntaxiques clés

| SQLite | PostgreSQL |
|--------|------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| `DATETIME` | `TIMESTAMP` |
| `TEXT` | `TEXT` ou `VARCHAR(n)` |
| `GLOB` | `LIKE` ou `~` (regex) |
| Pas de `ALTER COLUMN` | `ALTER COLUMN` supporté |

---

## 6. Registre des migrations

### 6.1 Historique

| Version | Migration | Date | Breaking | Description |
|---------|-----------|------|----------|-------------|
| 1.0.0 | `001_init.sql` | 2025-01-XX | — | Schéma initial |

### 6.2 Template pour nouvelles entrées

```markdown
| 1.X.0 | `00N_description.sql` | YYYY-MM-DD | YES/NO | Description courte |
```

---

## 7. Validation des migrations

### 7.1 Tests requis

Chaque migration doit être testée avec :

```bash
# 1. Appliquer sur DB vide
./scripts/migrate.sh /tmp/test_empty.db

# 2. Appliquer sur DB existante
cp data/cockpit.db /tmp/test_existing.db
./scripts/migrate.sh /tmp/test_existing.db

# 3. Rollback
./scripts/rollback.sh /tmp/test_existing.db 1

# 4. Re-appliquer
./scripts/migrate.sh /tmp/test_existing.db

# 5. Vérifier intégrité
sqlite3 /tmp/test_existing.db "PRAGMA integrity_check"
```

### 7.2 Checklist avant merge

- [ ] Migration appliquée sur DB vide ✓
- [ ] Migration appliquée sur DB avec données ✓
- [ ] Rollback testé ✓
- [ ] Re-application après rollback ✓
- [ ] Integrity check OK ✓
- [ ] Entry ajoutée dans ce document ✓
- [ ] CHANGELOG.md mis à jour ✓

---

## 8. Récapitulatif des commandes

```bash
# Appliquer toutes les migrations
./scripts/migrate.sh

# Appliquer sur une DB spécifique
./scripts/migrate.sh data/test.db

# Rollback de 1 migration
./scripts/rollback.sh data/cockpit.db 1

# Rollback de N migrations
./scripts/rollback.sh data/cockpit.db 3

# Vérifier l'état
sqlite3 data/cockpit.db "SELECT * FROM _migrations"
```

---

*Fin du document — v1.0.0*
