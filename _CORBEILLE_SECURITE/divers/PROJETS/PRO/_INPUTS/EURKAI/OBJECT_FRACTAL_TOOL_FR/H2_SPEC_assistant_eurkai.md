# H2 — Spécification Technique : Assistant Eurkai dans le Cockpit

## 1. Contrat d'API : `Super.orchestrate`

### 1.1 Signature

```typescript
interface OrchestrateRequest {
  input: OrchestrateInput;
  session_id: string;           // ID session Cockpit
  dry_run?: boolean;            // true = preview sans commit (défaut: true)
}

interface OrchestrateInput {
  type: 'text' | 'file' | 'mixed';
  text?: string;                // Texte brut (brief, instruction)
  files?: FilePayload[];        // Fichiers uploadés
  context?: InputContext;       // Contexte optionnel
}

interface FilePayload {
  name: string;                 // Nom du fichier
  mime_type: string;            // application/json, text/markdown, etc.
  content: string;              // Contenu (base64 pour binaires, texte sinon)
  encoding: 'utf-8' | 'base64';
}

interface InputContext {
  target_path?: string;         // Chemin fractal cible (ex: "/projects/alpha")
  scenario_hint?: string;       // Indice de scénario souhaité
  tags?: string[];              // Tags pour classification
}
```

### 1.2 Réponse

```typescript
interface OrchestrateResponse {
  request_id: string;           // UUID unique pour traçabilité
  status: 'success' | 'partial' | 'error';
  scenario: ScenarioResult;
  suggestions: Suggestion[];
  fractal_diff: FractalDiff;    // Preview des modifications (non appliquées)
  logs: LogEntry[];
  timestamp: string;            // ISO 8601
}

interface ScenarioResult {
  id: string;                   // Identifiant du scénario exécuté
  name: string;                 // Nom lisible
  description: string;
  confidence: number;           // 0.0 - 1.0
  parameters_detected: Record<string, any>;
}

interface Suggestion {
  type: 'action' | 'clarification' | 'warning';
  message: string;
  action_id?: string;           // Pour les actions proposées
  priority: 'low' | 'medium' | 'high';
}

interface FractalDiff {
  operations: DiffOperation[];
  summary: string;              // Résumé humain
  affected_paths: string[];     // Chemins fractals impactés
}

interface DiffOperation {
  op: 'create' | 'update' | 'delete' | 'link';
  path: string;
  value?: any;                  // Nouvelle valeur (create/update)
  previous?: any;               // Ancienne valeur (update/delete)
}

interface LogEntry {
  level: 'debug' | 'info' | 'warn' | 'error';
  source: string;               // Composant source
  message: string;
  timestamp: string;
  data?: Record<string, any>;
}
```

---

## 2. Structure des Messages Échangés

### 2.1 Envoi de texte brut

```json
{
  "input": {
    "type": "text",
    "text": "Créer un nouveau projet 'Dashboard Analytics' avec 3 modules : users, metrics, reports"
  },
  "session_id": "sess_abc123",
  "dry_run": true
}
```

### 2.2 Envoi de fichiers

**Brief Markdown :**
```json
{
  "input": {
    "type": "file",
    "files": [{
      "name": "brief_projet.md",
      "mime_type": "text/markdown",
      "content": "# Brief Projet\n\n## Objectif\nCréer une application de gestion...",
      "encoding": "utf-8"
    }]
  },
  "session_id": "sess_abc123",
  "dry_run": true
}
```

**Cahier des charges JSON :**
```json
{
  "input": {
    "type": "file",
    "files": [{
      "name": "cahier_charges.json",
      "mime_type": "application/json",
      "content": "{\"project\":{\"name\":\"CRM\",\"modules\":[...]}}",
      "encoding": "utf-8"
    }],
    "context": {
      "target_path": "/projects",
      "scenario_hint": "project_creation"
    }
  },
  "session_id": "sess_abc123"
}
```

**Manifest YAML :**
```json
{
  "input": {
    "type": "file",
    "files": [{
      "name": "manifest.yaml",
      "mime_type": "application/x-yaml",
      "content": "bmFtZTogTXlQcm9qZWN0Ci4uLg==",
      "encoding": "base64"
    }]
  },
  "session_id": "sess_abc123"
}
```

### 2.3 Envoi mixte (texte + fichiers)

```json
{
  "input": {
    "type": "mixed",
    "text": "Analyser ce brief et créer la structure projet correspondante",
    "files": [{
      "name": "brief.md",
      "mime_type": "text/markdown",
      "content": "# Mon Projet\n...",
      "encoding": "utf-8"
    }],
    "context": {
      "tags": ["import", "project-init"]
    }
  },
  "session_id": "sess_abc123",
  "dry_run": true
}
```

### 2.4 Réponse structurée type

```json
{
  "request_id": "req_7f8a9b2c",
  "status": "success",
  "scenario": {
    "id": "scn_project_create",
    "name": "Création de Projet",
    "description": "Génération d'une structure projet complète à partir d'un brief",
    "confidence": 0.92,
    "parameters_detected": {
      "project_name": "Dashboard Analytics",
      "modules": ["users", "metrics", "reports"],
      "architecture": "standard"
    }
  },
  "suggestions": [
    {
      "type": "action",
      "message": "Appliquer la structure projet générée",
      "action_id": "act_apply_diff_7f8a9b2c",
      "priority": "high"
    },
    {
      "type": "clarification",
      "message": "Souhaitez-vous ajouter un module d'authentification ?",
      "priority": "medium"
    }
  ],
  "fractal_diff": {
    "operations": [
      {
        "op": "create",
        "path": "/projects/dashboard-analytics",
        "value": {
          "name": "Dashboard Analytics",
          "type": "project",
          "status": "draft"
        }
      },
      {
        "op": "create",
        "path": "/projects/dashboard-analytics/modules/users",
        "value": { "name": "users", "type": "module" }
      },
      {
        "op": "create",
        "path": "/projects/dashboard-analytics/modules/metrics",
        "value": { "name": "metrics", "type": "module" }
      },
      {
        "op": "create",
        "path": "/projects/dashboard-analytics/modules/reports",
        "value": { "name": "reports", "type": "module" }
      }
    ],
    "summary": "Création du projet 'Dashboard Analytics' avec 3 modules",
    "affected_paths": [
      "/projects/dashboard-analytics",
      "/projects/dashboard-analytics/modules/users",
      "/projects/dashboard-analytics/modules/metrics",
      "/projects/dashboard-analytics/modules/reports"
    ]
  },
  "logs": [
    {
      "level": "info",
      "source": "InputParser",
      "message": "Input text parsed successfully",
      "timestamp": "2025-01-15T10:30:00.123Z"
    },
    {
      "level": "info",
      "source": "ScenarioMatcher",
      "message": "Matched scenario: project_create (confidence: 0.92)",
      "timestamp": "2025-01-15T10:30:00.456Z"
    }
  ],
  "timestamp": "2025-01-15T10:30:01.000Z"
}
```

---

## 3. Modèle Interne : Historique des Actions

### 3.1 Schema `AssistantHistoryEntry`

```typescript
interface AssistantHistoryEntry {
  // Identification
  id: string;                   // UUID unique
  session_id: string;           // Session Cockpit
  request_id: string;           // Lien vers OrchestrateResponse
  
  // Input original
  input: {
    type: 'text' | 'file' | 'mixed';
    text_preview: string;       // Premiers 200 caractères
    file_names: string[];       // Noms des fichiers
    file_count: number;
    context: InputContext | null;
  };
  
  // Scénario exécuté
  scenario: {
    id: string;
    name: string;
    confidence: number;
    parameters: Record<string, any>;
  };
  
  // Diff fractal associé
  fractal_diff: {
    operation_count: number;
    operations_summary: string[];  // ["create /projects/x", "update /config/y"]
    affected_paths: string[];
    full_diff_ref: string;         // Référence vers stockage complet
  };
  
  // État et métadonnées
  status: 'pending' | 'previewed' | 'applied' | 'rejected' | 'expired';
  applied_at: string | null;       // Si appliqué
  applied_by: string | null;       // Utilisateur qui a validé
  
  // Timestamps
  created_at: string;
  updated_at: string;
  expires_at: string;              // Expiration du diff (ex: +24h)
}
```

### 3.2 Schema de stockage (table/collection)

```sql
CREATE TABLE assistant_history (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      VARCHAR(64) NOT NULL,
  request_id      VARCHAR(64) NOT NULL UNIQUE,
  
  -- Input (JSONB pour flexibilité)
  input_type      VARCHAR(16) NOT NULL,
  input_preview   TEXT,
  input_files     JSONB DEFAULT '[]',
  input_context   JSONB,
  
  -- Scénario
  scenario_id     VARCHAR(64),
  scenario_name   VARCHAR(128),
  scenario_conf   DECIMAL(3,2),
  scenario_params JSONB,
  
  -- Diff
  diff_op_count   INTEGER DEFAULT 0,
  diff_summary    TEXT[],
  diff_paths      TEXT[],
  diff_full_ref   VARCHAR(256),      -- S3/blob reference
  
  -- État
  status          VARCHAR(16) DEFAULT 'pending',
  applied_at      TIMESTAMPTZ,
  applied_by      VARCHAR(64),
  
  -- Timestamps
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  expires_at      TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
  
  -- Index
  CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_history_session ON assistant_history(session_id);
CREATE INDEX idx_history_status ON assistant_history(status);
CREATE INDEX idx_history_created ON assistant_history(created_at DESC);
```

### 3.3 Lifecycle du Diff

```
                    ┌─────────────┐
                    │   INPUT     │
                    │  (Cockpit)  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  PENDING    │  ← Entry créée
                    └──────┬──────┘
                           │
              Super.orchestrate()
                           │
                           ▼
                    ┌─────────────┐
                    │  PREVIEWED  │  ← Diff généré, affiché
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ APPLIED  │ │ REJECTED │ │ EXPIRED  │
       │  (user)  │ │  (user)  │ │  (auto)  │
       └──────────┘ └──────────┘ └──────────┘
```

---

## 4. Onglet Discussion IA (Chat Clarification)

### 4.1 Contrat séparé (non-orchestration)

```typescript
interface ClarificationRequest {
  session_id: string;
  history_entry_id?: string;    // Lié à un input existant (optionnel)
  message: string;              // Question utilisateur
  conversation_id: string;      // ID conversation pour contexte
}

interface ClarificationResponse {
  message: string;              // Réponse IA
  suggestions?: string[];       // Reformulations suggérées
  ready_for_orchestration: boolean;
  refined_input?: OrchestrateInput;  // Input amélioré si prêt
}
```

### 4.2 Flux

1. User tape dans l'onglet Discussion IA
2. L'IA répond pour clarifier (pas d'accès au Core)
3. Quand l'idée est claire → bouton "Générer" active
4. Clic sur "Générer" → `Super.orchestrate()` avec l'input raffiné
5. Résultat affiché dans l'onglet Discussion + historique mis à jour

---

## 5. Endpoints REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/assistant/orchestrate` | Exécute Super.orchestrate |
| `POST` | `/api/assistant/clarify` | Chat de clarification |
| `GET` | `/api/assistant/history` | Liste historique (paginé) |
| `GET` | `/api/assistant/history/:id` | Détail d'une entrée |
| `POST` | `/api/assistant/history/:id/apply` | Applique un diff validé |
| `POST` | `/api/assistant/history/:id/reject` | Rejette un diff |
| `GET` | `/api/assistant/history/:id/diff` | Récupère le diff complet |

---

## 6. Résumé des Contraintes Respectées

| Contrainte | Implémentation |
|------------|----------------|
| Pas de modification directe | `dry_run: true` par défaut, diff en preview |
| Discussion IA isolée | Endpoint `/clarify` séparé, pas d'accès Core |
| Writes validés uniquement | Endpoint `/apply` explicite après preview |
| Traçabilité complète | `request_id` + `AssistantHistoryEntry` |
| Expiration des diffs | `expires_at` avec cleanup automatique |
