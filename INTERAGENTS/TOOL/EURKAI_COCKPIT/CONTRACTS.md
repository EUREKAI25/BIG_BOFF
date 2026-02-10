# EURKAI_COCKPIT — CONTRACTS

**Version** : 1.0.0  
**Date** : 2025-01-12  
**Statut** : VERROUILLÉ

---

## 1. PRE-FLIGHT Contract

Tout chantier DOIT commencer par un PRE-FLIGHT JSON.

### 1.1 Structure obligatoire

```json
{
  "preflight": {
    "ready": true | false,
    "certainty": 0.0 - 1.0,
    "missing_info": ["string", ...],
    "assumptions": ["string", ...]
  }
}
```

### 1.2 Règles

| Condition | Action |
|-----------|--------|
| `ready=true` ET `certainty=1.0` | Procéder aux livrables |
| `ready=false` OU `certainty<1.0` | Mode `ask_orchestrator`, poser 1-5 questions |
| `missing_info` non vide | Lister explicitement ce qui manque |
| `assumptions` non vide | Lister les hypothèses faites (à valider) |

### 1.3 Exemple — Prêt

```json
{
  "preflight": {
    "ready": true,
    "certainty": 1.0,
    "missing_info": [],
    "assumptions": []
  }
}
```

### 1.4 Exemple — Questions requises

```json
{
  "preflight": {
    "ready": false,
    "certainty": 0.6,
    "missing_info": ["Format de sortie attendu", "Scope des tests"],
    "assumptions": ["SQLite local uniquement"]
  },
  "mode": "ask_orchestrator",
  "questions": [
    "Quel format de sortie pour les exports ?",
    "Les tests doivent-ils couvrir l'UI ?"
  ]
}
```

---

## 2. Response Contract (JSON)

Toute réponse chantier = **UN seul objet JSON**.

### 2.1 Structure complète

```json
{
  "preflight": { ... },
  "role": "planner" | "coder" | "tester" | "reviewer",
  "mode": "deliverable" | "fix" | "ask_orchestrator",
  "summary": "string — résumé en 1-2 phrases",
  "questions": ["string", ...],
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "string — contenu complet du fichier"
    }
  ],
  "commands": ["string — commande shell à exécuter"],
  "acceptance": {
    "passes_in_a_row": 2,
    "max_iters": 8
  }
}
```

### 2.2 Champs obligatoires

| Champ | Obligatoire | Notes |
|-------|-------------|-------|
| `preflight` | ✅ | Toujours premier |
| `role` | ✅ | Rôle du chantier |
| `mode` | ✅ | Type de réponse |
| `summary` | ✅ | Résumé humain |
| `questions` | Si mode=ask_orchestrator | 1-5 questions |
| `files` | Si mode=deliverable | Fichiers complets |
| `commands` | Optionnel | Commandes à exécuter |
| `acceptance` | Si mode=deliverable | Critères de validation |

### 2.3 Règles fichiers

- **Fichiers complets** (pas de patches/diffs)
- Chemins relatifs à la racine projet
- Contenu UTF-8
- Créer les dossiers implicitement

### 2.4 Règles commandes

- Exécutables dans un shell POSIX
- Ordre d'exécution = ordre du tableau
- Aucune commande interactive (pas de `read`, pas de `sudo` avec mdp)

---

## 3. ask_orchestrator Protocol

Quand `mode="ask_orchestrator"` :

### 3.1 Format questions

```json
{
  "preflight": {
    "ready": false,
    "certainty": 0.7,
    "missing_info": ["..."],
    "assumptions": []
  },
  "role": "planner",
  "mode": "ask_orchestrator",
  "summary": "Besoin de clarification avant de produire les specs.",
  "questions": [
    "Q1 — Titre court : détail de la question ?",
    "Q2 — Titre court : détail de la question ?"
  ],
  "files": [],
  "commands": []
}
```

### 3.2 Règles questions

| Règle | Description |
|-------|-------------|
| Minimum | 1 question |
| Maximum | 5 questions |
| Format | Numérotées, titrées, concises |
| Focus | Bloquantes uniquement (pas de nice-to-have) |

### 3.3 Réponse orchestrateur

L'orchestrateur répond avec un document Markdown structuré.
Le chantier reprend ensuite avec `preflight.ready=true`.

---

## 4. API Response Contract

Toutes les réponses API suivent ce format.

### 4.1 Succès

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

### 4.2 Erreur

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

### 4.3 Codes d'erreur standard

| Code | HTTP | Description |
|------|------|-------------|
| `ERR_VALIDATION` | 400 | Données invalides |
| `ERR_UNAUTHORIZED` | 401 | Gate mdp requis |
| `ERR_NOT_FOUND` | 404 | Ressource introuvable |
| `ERR_CONFLICT` | 409 | Conflit (ex: clé dupliquée) |
| `ERR_INTERNAL` | 500 | Erreur serveur |

---

## 5. Versioning Contract

### 5.1 SemVer strict

```
MAJOR.MINOR.PATCH

MAJOR : breaking change (contrat modifié)
MINOR : ajout rétrocompatible
PATCH : fix sans changement d'interface
```

### 5.2 Ce qui déclenche un bump

| Changement | Bump |
|------------|------|
| Nouveau champ optionnel API | MINOR |
| Champ requis ajouté | MAJOR |
| Champ supprimé | MAJOR |
| Type de champ modifié | MAJOR |
| Nouveau endpoint | MINOR |
| Endpoint supprimé | MAJOR |
| Fix interne | PATCH |

### 5.3 Obligation de documentation

Tout MAJOR/MINOR bump DOIT inclure :
- Note dans CHANGELOG.md
- Migration notes si MAJOR

---

## 6. Validation Contract

### 6.1 Acceptance criteria

```json
{
  "acceptance": {
    "passes_in_a_row": 2,
    "max_iters": 8
  }
}
```

| Champ | Description |
|-------|-------------|
| `passes_in_a_row` | Nombre de succès consécutifs requis |
| `max_iters` | Maximum d'itérations avant échec |

### 6.2 Définition "pass"

- Tous les tests passent
- Aucune erreur de lint
- Contrats respectés
- Fichiers créés valides

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-01-12 | Initial contracts verrouillés |
