# RELEASE_PROCESS.md — EURKAI_COCKPIT

> **Version:** 1.0.0  
> **Chantier:** C00 — Versioning & Release Hygiene  
> **Status:** STABLE

---

## 1. Vue d'ensemble

```
Feature → Dev → Tests → Review → Tag → Push → Backup
```

| Étape | Branch | Action |
|-------|--------|--------|
| Développement | `feature/<name>` | Code + tests |
| Intégration | `dev` | Merge feature, CI local |
| Release | `main` | Tag, changelog, push |
| Backup | `main` | Dump DB → commit artifacts |

---

## 2. Workflow Git

### 2.1 Branches

| Branch | Usage | Protection |
|--------|-------|------------|
| `main` | Stable, releases tagées | Merge via PR ou validation C08 |
| `dev` | Intégration chantiers | Tests verts requis |
| `feature/<name>` | Travail isolé | Libre |

### 2.2 Nommage des commits

```
<type>: <description courte>

Types autorisés :
- feat     → nouvelle feature
- fix      → bugfix
- docs     → documentation
- refactor → refactor sans changement de comportement
- test     → ajout/modif tests
- chore    → maintenance (deps, scripts)
- release  → bump version + tag
```

Exemples :
```
feat: add project CRUD endpoints
fix: handle null brief description
release: v1.2.0
```

---

## 3. Processus de release

### 3.1 Checklist pré-release

- [ ] Tous les tests passent (`npm test` / `pytest`)
- [ ] Pas de TODO critiques dans le code
- [ ] CHANGELOG.md à jour
- [ ] Contrats versionnés (pas de diff non commité)
- [ ] C08 validation passée (si applicable)

### 3.2 Commandes de release

```bash
# 1. S'assurer d'être sur main à jour
git checkout main
git pull origin main

# 2. Merger dev si nécessaire
git merge dev

# 3. Bump version
NEW_VERSION="1.2.0"
echo "$NEW_VERSION" > VERSION

# 4. Mettre à jour CHANGELOG
# (voir section 4)

# 5. Commit + tag
git add VERSION CHANGELOG.md
git commit -m "release: v$NEW_VERSION"
git tag "v$NEW_VERSION"

# 6. Push
git push origin main --tags

# 7. Backup DB (optionnel mais recommandé)
./scripts/backup_db.sh
```

### 3.3 Hotfix (urgence)

```bash
# Depuis main
git checkout main
git checkout -b hotfix/<issue>

# Fix + test
# ...

# Merge direct dans main
git checkout main
git merge hotfix/<issue>

# Bump PATCH
echo "1.2.1" > VERSION
git add VERSION CHANGELOG.md
git commit -m "release: v1.2.1 (hotfix)"
git tag v1.2.1
git push origin main --tags
```

---

## 4. CHANGELOG.md

### 4.1 Format

```markdown
# Changelog

## [1.2.0] - 2025-01-15

### Added
- Endpoint POST /api/briefs (#12)
- CLI command `cockpit run`

### Changed
- Manifest format v2 (voir MIGRATIONS.md)

### Fixed
- Null handling in project list

### Deprecated
- CLI flag `--legacy` (removed in 2.0)

## [1.1.0] - 2025-01-10
...
```

### 4.2 Catégories

| Catégorie | Usage |
|-----------|-------|
| **Added** | Nouvelles features |
| **Changed** | Modifications comportement existant |
| **Deprecated** | Features marquées pour suppression future |
| **Removed** | Features supprimées (MAJOR) |
| **Fixed** | Bugfixes |
| **Security** | Correctifs sécurité |

---

## 5. Migration notes

Toute release avec **MAJOR bump** ou changement de schéma doit inclure :

1. Entry dans `docs/MIGRATIONS.md`
2. Section dédiée dans CHANGELOG sous "Changed" ou "Removed"
3. Script de migration si applicable (`scripts/migrate_X_to_Y.sql`)

Exemple d'entry CHANGELOG :
```markdown
### Changed
- **BREAKING:** Manifest shape v2 — voir [MIGRATIONS.md](docs/MIGRATIONS.md#v2-manifest)
```

---

## 6. Critères "STABLE"

Une release est déclarée **STABLE** si :

| Critère | Vérification |
|---------|--------------|
| Tests verts | `npm test` exit 0 |
| Contrats versionnés | `git status` clean après bump |
| Backup OK | `./scripts/backup_db.sh` exit 0 (ou dry-run) |
| C08 validation | `cockpit validate` rapport vert |
| No critical TODOs | grep "TODO.*CRITICAL" = 0 |

### 6.1 Commande de validation

```bash
# Script de validation complète (C08)
./scripts/validate_release.sh

# Output attendu :
# ✓ Tests: PASS
# ✓ Contracts: versioned
# ✓ Backup: OK (dry-run)
# ✓ C08: PASS
# → STABLE: YES
```

---

## 7. Backup DB → GitHub

### 7.1 Comportement

| Condition | Action |
|-----------|--------|
| Git repo + remote configuré | Commit + push dump |
| Git repo, pas de remote | Commit local + warning |
| Pas de git | Dump local uniquement (`data/backups/`) |

### 7.2 Script

```bash
#!/bin/bash
# scripts/backup_db.sh

BACKUP_DIR="data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="$BACKUP_DIR/cockpit_$TIMESTAMP.sqlite"

# 1. Dump
mkdir -p "$BACKUP_DIR"
cp data/cockpit.db "$DUMP_FILE"

# 2. Git commit (si possible)
if git rev-parse --git-dir > /dev/null 2>&1; then
  git add "$DUMP_FILE"
  git commit -m "backup: db snapshot $TIMESTAMP"
  
  # 3. Push (si remote existe)
  if git remote get-url origin > /dev/null 2>&1; then
    git push origin main
    echo "✓ Backup pushed to remote"
  else
    echo "⚠ No remote configured — local commit only"
  fi
else
  echo "⚠ Not a git repo — local dump only"
fi

echo "✓ Backup saved: $DUMP_FILE"
```

---

## 8. Tags & releases

### 8.1 Convention de tags

```
v<MAJOR>.<MINOR>.<PATCH>
```

Exemples : `v1.0.0`, `v1.2.3`, `v2.0.0`

### 8.2 Releases GitHub (optionnel)

Si GitHub releases sont utilisées :
1. Créer release depuis le tag
2. Copier la section CHANGELOG correspondante
3. Attacher les artifacts si pertinent (dump DB, binaires)

---

## 9. Récapitulatif des fichiers

| Fichier | Màj à chaque release ? |
|---------|----------------------|
| `VERSION` | ✅ Toujours |
| `CHANGELOG.md` | ✅ Toujours |
| `docs/MIGRATIONS.md` | Si changement schéma/contrat |
| `data/backups/*.sqlite` | Via backup script |

---

*Fin du document — v1.0.0*
