# VERSIONING_POLICY.md — EURKAI_COCKPIT

> **Version:** 1.0.0  
> **Chantier:** C00 — Versioning & Release Hygiene  
> **Status:** STABLE

---

## 1. Semantic Versioning (SemVer)

Le cockpit suit **SemVer 2.0.0** : `MAJOR.MINOR.PATCH`

| Bump | Quand ? | Exemple |
|------|---------|---------|
| **MAJOR** | Breaking change sur un contrat public (API, CLI, manifest, schéma DB) | `1.2.3 → 2.0.0` |
| **MINOR** | Nouvelle feature, nouveau module, extension compatible | `1.2.3 → 1.3.0` |
| **PATCH** | Bugfix, refactor interne, doc, tests | `1.2.3 → 1.2.4` |

---

## 2. Contrats publics (ce qui déclenche un bump)

Un **contrat public** est toute interface consommée par un agent externe ou un utilisateur :

| Contrat | Fichier(s) de référence | Bump si modifié |
|---------|------------------------|-----------------|
| API REST | `backend/api/openapi.yaml` | MAJOR si breaking, MINOR sinon |
| CLI flags/commands | `cli/CLI_SPEC.md` | MAJOR si breaking |
| Manifest shape | `docs/MANIFEST_SPEC.md` | MAJOR si champ obligatoire ajouté/supprimé |
| Schéma DB | `backend/db/schema.sql` | MAJOR si colonne supprimée, MINOR si ajout nullable |
| Config/Secrets shape | `docs/CONFIG_SPEC.md` | MINOR (ajout), MAJOR (suppression) |

---

## 3. Layers & dépendances (C01→C08)

Chaque chantier est un **layer** avec des dépendances strictes :

```
C00 ─► C01 ─► C02 ─► C03 ─► C04
                 │       │
                 │       └─► C05
                 │
                 └─► C06 ─► C07 ─► C08
```

| Layer | Nom | Dépend de |
|-------|-----|-----------|
| C00 | Versioning & Release | — |
| C01 | Specs & Contracts | C00 |
| C02 | Data Model + Storage | C01 |
| C03 | Backend API | C02 |
| C04 | Frontend UI | C03 |
| C05 | CLI + Runner hooks | C03 |
| C06 | Secrets (copy gated) | C02 |
| C07 | Backup DB → GitHub | C06 |
| C08 | Install/Validate ALL | C04, C05, C07 |

**Règle :** un layer N ne peut être déclaré stable que si tous ses layers dépendants (N-1) sont stables.

---

## 4. Self-enrichment (sans forks)

Le cockpit peut **s'enrichir lui-même** (nouveaux modules, chantiers, prompts) sous conditions :

### 4.1 Règles d'ajout

1. **Nouveau module** = nouveau manifest versionné dans `manifests/`
2. **Nouveau chantier** = nouveau fichier `prompts/C<NN>_<NAME>.md`
3. **Aucun fork** : tout ajout se fait dans le même repo, même base de code

### 4.2 Traçabilité obligatoire

| Action | Obligation |
|--------|-----------|
| Ajout module | Entry dans `CHANGELOG.md` + manifest versionné |
| Modification contrat | Version bump + notes migration |
| Suppression | MAJOR bump + migration documentée |

### 4.3 Append-only logs

Les runs sont **append-only** (jamais d'écrasement) :
- `data/runs/<timestamp>_<brief_id>.json`
- Historique consultable, jamais supprimé automatiquement

---

## 5. Définition de "STABLE"

Un release est **STABLE** si et seulement si :

- [ ] Tests verts (`npm test` / `pytest` selon stack)
- [ ] Contrats versionnés (pas de diff non versionné)
- [ ] Backup GitHub OK (ou dry-run si remote absent)
- [ ] C08 validation passée (rapport vert)

---

## 6. Fichiers versionnés (source of truth)

| Fichier | Rôle |
|---------|------|
| `VERSION` | Fichier texte avec version courante (`1.0.0`) |
| `CHANGELOG.md` | Historique des releases |
| `manifests/*.json` | Manifests modules versionnés |
| `docs/MIGRATIONS.md` | Notes de migration DB |

---

## 7. Workflow de bump

```bash
# 1. Vérifier les changements
git diff --name-only HEAD~1

# 2. Déterminer le type de bump
#    - contrat modifié ? → MAJOR ou MINOR
#    - interne seulement ? → PATCH

# 3. Mettre à jour
echo "1.1.0" > VERSION
# Ajouter entry dans CHANGELOG.md

# 4. Tag + push
git add VERSION CHANGELOG.md
git commit -m "release: v1.1.0"
git tag v1.1.0
git push origin main --tags
```

---

## 8. Compatibilité & refactors

| Type de changement | Autorisé sans bump ? |
|--------------------|---------------------|
| Refactor interne (même comportement) | ✅ Oui (PATCH optionnel) |
| Ajout champ optionnel DB | ✅ Oui (MINOR) |
| Suppression champ DB | ❌ Non (MAJOR + migration) |
| Nouveau endpoint API | ✅ Oui (MINOR) |
| Modification signature endpoint | ❌ Non (MAJOR) |
| Ajout flag CLI | ✅ Oui (MINOR) |
| Suppression flag CLI | ❌ Non (MAJOR) |

---

*Fin du document — v1.0.0*
