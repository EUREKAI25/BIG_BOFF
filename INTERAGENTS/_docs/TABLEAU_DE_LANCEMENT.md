# EURKAI_COCKPIT — TABLEAU DE LANCEMENT (v1)

Objectif: construire un **cockpit local-first** (UI + mini-serveur + storage) pour piloter projets/briefs/runs/config/secrets,
avec **préparation des manifests plug-and-play** (inputs/outputs), sans sur-ingénierie.

## TABLEAU DE LANCEMENT

| Ordre | Chantier | Mode | Dépend de | Responsable | Livrable principal | Validation |
|---:|---|---|---|---|---|---|
| 1 | C00 — Versioning & Release Policy | Séquentiel | — | Planner | VERSIONING_POLICY.md + release rules | Revue + checklist |
| 2 | C01 — Specs & Contracts (incl. manifests) | Séquentiel | — | Planner | Spec verrouillée + contrats | Revue cohérence + check-list |
| 3 | C02 — Data Model + Storage (SQLite CRUD) | Séquentiel | C01 | Coder | Schéma + storage layer | Tests unitaires storage |
| 4 | C03 — Backend API (local server) | Séquentiel | C02 | Coder | API Projects/Briefs/Runs/Secrets | Tests API + lint |
| 5 | C04 — Frontend UI (cockpit minimal) | Séquentiel | C03 | Coder | UI 5–6 écrans | Tests UI (min) + smoke test |
| 6 | C05 — CLI d’intégration + Runner hooks | Séquentiel | C03 | Coder | CLI pour import/export/run | Tests CLI + E2E smoke |
| 7 | C06 — Secrets (copy gated) + policy | Parallèle | C03 | Coder | Gestion secrets + gate mdp | Tests + audit logs |
| 8 | C07 — Backup DB → GitHub (cron/local) | Parallèle | C02 | Coder | backup command + doc | Test “dry-run” |
| 9 | C08 — Install/Validate ALL (one-shot) | Séquentiel | C04,C05,C06,C07 | Tester | script d’install + validation | pipeline local vert |

Notes:
- C06 et C07 peuvent démarrer en parallèle une fois C03/C02 prêts.
- C08 est le dernier: il doit installer + exécuter tests + produire un “validation report”.
