# EURKAI_COCKPIT — API Documentation

**Version** : 1.0.0  
**Date** : 2025-01-12  
**Statut** : VERROUILLÉ (C03)

---

## 1. Vue d'ensemble

Backend local-first exposant une API REST pour orchestrer des briefs IA.

### Stack
- **Framework** : FastAPI
- **Base de données** : SQLite (via C02 storage layer)
- **Chiffrement secrets** : AES-256 via Fernet + PBKDF2

### Démarrage

```bash
# Installation
pip install fastapi uvicorn pydantic cryptography

# Lancer le serveur
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000

# Ou directement
python -m backend.app
```

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `EURKAI_DB_PATH` | Chemin base SQLite | `~/.eurkai_cockpit/cockpit.db` |
| `EURKAI_TOKEN` | Token API (vide = désactivé) | — |
| `EURKAI_MASTER_PASSWORD` | Mot de passe master pour secrets | — |
| `EURKAI_BACKUP_DIR` | Répertoire backups | `~/.eurkai_cockpit/backups` |
| `EURKAI_HOST` | Host serveur | `127.0.0.1` |
| `EURKAI_PORT` | Port serveur | `8000` |

---

## 2. Authentification

### Token API (optionnel)

Si `EURKAI_TOKEN` est défini, toutes les requêtes doivent inclure :

```
X-EURKAI-TOKEN: <token>
```

### Session Secrets

Pour copier une valeur de secret :

1. **Unlock** : `POST /api/secrets/unlock` avec `master_password`
2. Récupérer le `session_token` (TTL 5 minutes)
3. **Copy** : `GET /api/secrets/{id}/copy` avec header `X-Session-Token`

---

## 3. Format des réponses

### Succès (C01 Contract 4.1)

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-12T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### Erreur (C01 Contract 4.2)

```json
{
  "success": false,
  "error": {
    "code": "ERR_NOT_FOUND",
    "message": "Resource not found",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2025-01-12T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### Codes d'erreur

| Code | HTTP | Description |
|------|------|-------------|
| `ERR_VALIDATION` | 400 | Données invalides |
| `ERR_UNAUTHORIZED` | 401 | Token/session requis |
| `ERR_NOT_FOUND` | 404 | Ressource introuvable |
| `ERR_CONFLICT` | 409 | Conflit (ex: clé dupliquée) |
| `ERR_INTERNAL` | 500 | Erreur serveur |

---

## 4. Endpoints

### 4.1 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | Liste tous les projets |
| `POST` | `/api/projects` | Créer un projet |
| `GET` | `/api/projects/{id}` | Détail projet |
| `PUT` | `/api/projects/{id}` | Modifier projet |
| `DELETE` | `/api/projects/{id}` | Supprimer (cascade briefs) |

**Create/Update payload :**

```json
{
  "name": "Mon Projet",
  "description": "Description optionnelle"
}
```

---

### 4.2 Briefs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/briefs` | Liste (filtre `?project_id=`) |
| `POST` | `/api/briefs` | Créer brief |
| `GET` | `/api/briefs/{id}` | Détail brief |
| `PUT` | `/api/briefs/{id}` | Modifier brief |
| `DELETE` | `/api/briefs/{id}` | Supprimer brief |
| `POST` | `/api/briefs/{id}/run` | Lancer un run |
| `GET` | `/api/briefs/{id}/runs` | Historique runs |

**Create payload :**

```json
{
  "project_id": "uuid",
  "title": "Brief Title",
  "user_prompt": "Do something...",
  "goal": "Optional goal",
  "system_prompt": "Optional system prompt",
  "variables": {"key": "value"},
  "expected_output": "Optional expected output",
  "tags": ["tag1", "tag2"],
  "policy": {
    "passes_in_a_row": 2,
    "max_iters": 8
  }
}
```

---

### 4.3 Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/runs/{id}` | Détail run |
| `DELETE` | `/api/runs/{id}` | Supprimer run |

**Run status** : `pending` → `running` → `success` | `failed`

---

### 4.4 Config

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config` | Liste config |
| `PUT` | `/api/config/{key}` | Modifier/créer valeur |

**Update payload :**

```json
{
  "value": "config_value"
}
```

---

### 4.5 Secrets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/secrets` | Liste (clés seulement) |
| `POST` | `/api/secrets` | Créer secret |
| `POST` | `/api/secrets/unlock` | Déverrouiller session |
| `GET` | `/api/secrets/{id}/copy` | Copier valeur (session requise) |
| `PUT` | `/api/secrets/{id}` | Modifier secret |
| `DELETE` | `/api/secrets/{id}` | Supprimer secret |

**Create payload :**

```json
{
  "key": "API_KEY",
  "value": "secret_value",
  "project_id": null
}
```

**Unlock payload :**

```json
{
  "master_password": "your_master_password"
}
```

**Unlock response :**

```json
{
  "session_token": "xxx",
  "ttl": 300
}
```

---

### 4.6 Modules

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/modules` | Liste manifests |
| `POST` | `/api/modules` | Enregistrer manifest |
| `GET` | `/api/modules/{id}` | Détail manifest |
| `DELETE` | `/api/modules/{id}` | Retirer du registry |
| `GET` | `/api/modules/compatible?from=A&to=B` | Vérifier compatibilité |

**Register payload (ModuleManifest v1) :**

```json
{
  "name": "my-module",
  "version": "1.0.0",
  "description": "Module description",
  "inputs": [
    {
      "name": "text",
      "type": "string",
      "required": true,
      "description": "Input text"
    }
  ],
  "outputs": [
    {
      "name": "result",
      "type": "object"
    }
  ],
  "constraints": {
    "timeout_seconds": 30
  },
  "tags": ["nlp"]
}
```

**Types supportés** : `string`, `number`, `boolean`, `object`, `array`, `file`

**Règles de versioning :**
- Même nom + même version = **REJET** (409)
- Même nom + version supérieure = **MISE À JOUR**

---

### 4.7 Backups

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/backups` | Historique backups |
| `POST` | `/api/backups` | Déclencher backup |
| `POST` | `/api/backups/dry-run` | Test sans commit |

**Trigger payload (optionnel) :**

```json
{
  "notes": "Manual backup before migration"
}
```

---

## 5. Documentation interactive

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`
- **OpenAPI JSON** : `http://localhost:8000/openapi.json`

---

## 6. Tests

```bash
# Installation test dependencies
pip install pytest httpx

# Lancer les tests
python -m pytest tests/test_api_smoke.py -v

# Avec couverture
pip install pytest-cov
python -m pytest tests/ --cov=backend --cov-report=html
```

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-01-12 | Initial API (C03) |
