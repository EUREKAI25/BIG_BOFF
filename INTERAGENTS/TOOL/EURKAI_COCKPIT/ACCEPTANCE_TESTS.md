# EURKAI_COCKPIT — ACCEPTANCE_TESTS

**Version** : 1.0.0  
**Date** : 2025-01-12  
**Statut** : VERROUILLÉ

---

## 1. Instructions

Cette checklist valide que l'implémentation respecte SPEC_V1.
Chaque test doit passer **2 fois consécutives** avant validation.

### Légende

- `[ ]` — Non testé
- `[P]` — Pass
- `[F]` — Fail
- `[S]` — Skip (non applicable)

---

## 2. Tests Database

### 2.1 Schema

```
[ ] T-DB-001: Table 'projects' existe avec tous les champs
[ ] T-DB-002: Table 'briefs' existe avec FK vers projects
[ ] T-DB-003: Table 'runs' existe avec FK vers briefs
[ ] T-DB-004: Table 'secrets' existe avec champs chiffrés
[ ] T-DB-005: Table 'config' existe
[ ] T-DB-006: Table 'tags' existe
[ ] T-DB-007: Table 'module_manifests' existe
[ ] T-DB-008: Table 'backups' existe
[ ] T-DB-009: Index idx_briefs_project existe
[ ] T-DB-010: Index idx_runs_brief existe
[ ] T-DB-011: Index idx_runs_status existe
[ ] T-DB-012: Index idx_secrets_project existe
```

### 2.2 Contraintes

```
[ ] T-DB-020: Brief sans project_id → ERREUR FK
[ ] T-DB-021: Run sans brief_id → ERREUR FK
[ ] T-DB-022: DELETE project → CASCADE briefs
[ ] T-DB-023: DELETE brief → CASCADE runs
[ ] T-DB-024: Secret project_id NULL accepté (global)
[ ] T-DB-025: Secret (project_id, key) unique
```

---

## 3. Tests API — Projects

```
[ ] T-API-P-001: GET /api/projects → 200 + liste
[ ] T-API-P-002: POST /api/projects {name} → 201 + id
[ ] T-API-P-003: POST /api/projects {} → 400 ERR_VALIDATION
[ ] T-API-P-004: GET /api/projects/{id} → 200 + détail
[ ] T-API-P-005: GET /api/projects/{invalid} → 404 ERR_NOT_FOUND
[ ] T-API-P-006: PUT /api/projects/{id} {name} → 200
[ ] T-API-P-007: DELETE /api/projects/{id} → 204
[ ] T-API-P-008: DELETE /api/projects/{id} → cascade briefs vérifiée
```

---

## 4. Tests API — Briefs

```
[ ] T-API-B-001: GET /api/briefs → 200 + liste
[ ] T-API-B-002: GET /api/briefs?project_id=x → filtre OK
[ ] T-API-B-003: POST /api/briefs {project_id, title, user_prompt} → 201
[ ] T-API-B-004: POST /api/briefs sans project_id → 400
[ ] T-API-B-005: POST /api/briefs project_id invalide → 400
[ ] T-API-B-006: GET /api/briefs/{id} → 200
[ ] T-API-B-007: PUT /api/briefs/{id} → 200
[ ] T-API-B-008: DELETE /api/briefs/{id} → 204
[ ] T-API-B-009: POST /api/briefs/{id}/run → 202 + run_id
[ ] T-API-B-010: Champs optionnels (system_prompt, variables, etc.) acceptés
```

---

## 5. Tests API — Runs

```
[ ] T-API-R-001: GET /api/briefs/{id}/runs → 200 + liste
[ ] T-API-R-002: GET /api/runs/{id} → 200 + détail complet
[ ] T-API-R-003: Run contient: output, logs, status, duration_ms, model
[ ] T-API-R-004: DELETE /api/runs/{id} → 204
[ ] T-API-R-005: Status transitions: pending → running → success|failed
```

---

## 6. Tests API — Secrets

```
[ ] T-API-S-001: GET /api/secrets → 200 + liste (clés seulement)
[ ] T-API-S-002: GET /api/secrets → valeurs NON exposées
[ ] T-API-S-003: POST /api/secrets {key, value} → 201
[ ] T-API-S-004: POST /api/secrets {key, value, project_id} → 201 (scoped)
[ ] T-API-S-005: GET /api/secrets/{id}/copy sans session → 401
[ ] T-API-S-006: POST /api/secrets/unlock {master_password} → session_token
[ ] T-API-S-007: GET /api/secrets/{id}/copy avec session → 200 + value
[ ] T-API-S-008: Session expire après TTL (5 min)
[ ] T-API-S-009: PUT /api/secrets/{id} → 200
[ ] T-API-S-010: DELETE /api/secrets/{id} → 204
[ ] T-API-S-011: Valeur stockée chiffrée AES-256-GCM
[ ] T-API-S-012: Clé dérivée PBKDF2 du master_password
```

---

## 7. Tests API — Modules

```
[ ] T-API-M-001: GET /api/modules → 200 + liste manifests
[ ] T-API-M-002: POST /api/modules {manifest} → 201
[ ] T-API-M-003: POST /api/modules nom invalide → 400
[ ] T-API-M-004: POST /api/modules version invalide → 400
[ ] T-API-M-005: POST /api/modules type input invalide → 400
[ ] T-API-M-006: POST /api/modules nom+version dupliqué → 409
[ ] T-API-M-007: GET /api/modules/{id} → 200
[ ] T-API-M-008: DELETE /api/modules/{id} → 204
[ ] T-API-M-009: GET /api/modules/compatible?from=A&to=B → résultat correct
[ ] T-API-M-010: Compatibilité: types matchent → mappings retournés
[ ] T-API-M-011: Compatibilité: required manquant → missing_required
```

---

## 8. Tests API — Backups

```
[ ] T-API-BK-001: GET /api/backups → 200 + historique
[ ] T-API-BK-002: POST /api/backups/dry-run → 200 + fichiers locaux créés
[ ] T-API-BK-003: POST /api/backups (git non configuré) → dry_run auto
[ ] T-API-BK-004: POST /api/backups (git OK) → commit sur backup/auto
[ ] T-API-BK-005: Export inclut .db ET .json
[ ] T-API-BK-006: Backup loggé dans table backups
```

---

## 9. Tests API — Config

```
[ ] T-API-C-001: GET /api/config → 200 + liste
[ ] T-API-C-002: PUT /api/config/{key} {value} → 200
[ ] T-API-C-003: PUT /api/config/{key} crée si n'existe pas
```

---

## 10. Tests API — Response Contract

```
[ ] T-CTR-001: Toute réponse succès contient {success: true, data, meta}
[ ] T-CTR-002: Toute réponse erreur contient {success: false, error, meta}
[ ] T-CTR-003: meta.timestamp format ISO 8601
[ ] T-CTR-004: meta.version = version API actuelle
[ ] T-CTR-005: error.code parmi codes standard
```

---

## 11. Tests Frontend

```
[ ] T-UI-001: Navigation principale accessible
[ ] T-UI-002: /projects affiche liste projets
[ ] T-UI-003: /projects/:id affiche détail + briefs liés
[ ] T-UI-004: /briefs affiche liste avec filtres
[ ] T-UI-005: /briefs/:id permet édition complète
[ ] T-UI-006: /briefs/:id/runs affiche historique
[ ] T-UI-007: /secrets masque valeurs par défaut
[ ] T-UI-008: /secrets copy requiert gate mdp
[ ] T-UI-009: /modules affiche registry
[ ] T-UI-010: /modules compatibilité visualisée
[ ] T-UI-011: /backups permet trigger manuel
[ ] T-UI-012: /config permet modification
```

---

## 12. Tests Intégration

```
[ ] T-INT-001: Créer projet → créer brief → lancer run → vérifier résultat
[ ] T-INT-002: Créer secret → unlock → copy → vérifier valeur
[ ] T-INT-003: Enregistrer module → vérifier compatibilité
[ ] T-INT-004: Backup dry-run → vérifier fichiers
[ ] T-INT-005: DELETE projet → vérifier cascade complète
```

---

## 13. Tests Non-Fonctionnels

```
[ ] T-NF-001: DB < 100ms pour requêtes simples
[ ] T-NF-002: API < 200ms pour endpoints CRUD
[ ] T-NF-003: Chiffrement/déchiffrement < 50ms
[ ] T-NF-004: Backup < 5s pour DB < 10MB
```

---

## 14. Commandes de test

### Backend

```bash
# Lancer tous les tests
pytest tests/ -v

# Tests DB uniquement
pytest tests/test_db.py -v

# Tests API uniquement
pytest tests/test_api.py -v

# Avec couverture
pytest tests/ --cov=src --cov-report=html
```

### Frontend

```bash
# Tests unitaires
npm test

# Tests E2E (si configurés)
npm run test:e2e
```

---

## 15. Critères de validation finale

```
[ ] Tous les T-DB-* passent
[ ] Tous les T-API-* passent
[ ] Tous les T-CTR-* passent
[ ] Tous les T-UI-* passent (ou skip si frontend non requis)
[ ] Tous les T-INT-* passent
[ ] T-NF-* dans les seuils
[ ] 2 passes consécutives sans régression
[ ] Couverture ≥ 80%
```

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-01-12 | Initial acceptance tests |
