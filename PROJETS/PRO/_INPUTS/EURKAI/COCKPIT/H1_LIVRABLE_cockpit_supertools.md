# H1 — Connexion du Cockpit aux SuperTools EURKAI
## Livrable technique complet

**Version** : 1.0  
**Date** : 2025-12-01  
**Statut** : Lecture seule + Audits  
**Contrainte** : Aucun write — Accès exclusif via SuperTools

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture d'intégration](#2-architecture-dintégration)
3. [API Backend — Points d'entrée](#3-api-backend--points-dentrée)
4. [Contrats de données](#4-contrats-de-données)
5. [Design d'intégration Cockpit](#5-design-dintégration-cockpit)
6. [Gestion de la volumétrie](#6-gestion-de-la-volumétrie)
7. [Sécurité et contrôles](#7-sécurité-et-contrôles)
8. [Annexes techniques](#8-annexes-techniques)

---

## 1. Vue d'ensemble

### 1.1 Objectif du chantier H1

Le chantier H1 établit la **première connexion concrète** entre le Cockpit (interface utilisateur) et le cœur EURKAI (backend fractal) via les SuperTools. Cette connexion est strictement en **lecture seule** :

| Autorisé | Interdit |
|----------|----------|
| Charger la fractale | Créer des objets |
| Naviguer dans les lineages | Modifier des bundles |
| Visualiser les bundles | Écrire sur la fractale |
| Lancer des audits | Exécuter des mutations |
| Consulter les rapports | Toute opération CRUDOE sauf READ |

### 1.2 SuperTools mobilisés

```
┌─────────────────────────────────────────────────────────────┐
│                      COCKPIT (Frontend)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY H1                            │
│  ┌─────────────────┐     ┌──────────────────┐               │
│  │   SuperRead     │     │  SuperEvaluate   │               │
│  │  (lecture)      │     │  (audits)        │               │
│  └────────┬────────┘     └────────┬─────────┘               │
│           │                       │                          │
│           └───────────┬───────────┘                          │
│                       ▼                                      │
│              ┌────────────────┐                              │
│              │   FRACTALE     │                              │
│              │   (read-only)  │                              │
│              └────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture d'intégration

### 2.1 Flux de données

```
COCKPIT                          BACKEND EURKAI
   │                                   │
   │  1. GET /api/fractal/tree         │
   │ ─────────────────────────────────>│
   │                                   │ SuperRead.execute(whatVector)
   │  2. Response: TreeView            │
   │ <─────────────────────────────────│
   │                                   │
   │  3. GET /api/object/{oid}         │
   │ ─────────────────────────────────>│
   │                                   │ SuperRead.execute(whatVector)
   │  4. Response: ObjectBundle        │
   │ <─────────────────────────────────│
   │                                   │
   │  5. POST /api/audit/run           │
   │ ─────────────────────────────────>│
   │                                   │ SuperEvaluate.execute(whatVector, howVector)
   │  6. Response: AuditReport         │
   │ <─────────────────────────────────│
```

### 2.2 Principes d'intégration

1. **Isolation stricte** : Le Cockpit n'accède jamais directement à la base de données ou à la fractale. Tous les accès passent par les SuperTools.

2. **Vecteurs standardisés** : Chaque requête est traduite en `whatVector` (quoi lire) et `howVector` (comment traiter). Le backend retourne un `scriptVector` ou un `resultVector`.

3. **Stateless** : Chaque requête est autonome. Le Cockpit maintient son état local (cache, navigation) mais le backend ne conserve pas de session.

---

## 3. API Backend — Points d'entrée

### 3.1 Endpoint : Charger l'arbre fractal

```yaml
Endpoint: GET /api/v1/fractal/tree
Description: Retourne l'arborescence des objets avec leurs lineages
SuperTool: SuperRead

Query Parameters:
  root_oid:     string | null   # OID racine (null = racine système)
  depth:        integer         # Profondeur max (défaut: 3, max: 10)
  include:      string[]        # Types d'objets à inclure
  exclude:      string[]        # Types d'objets à exclure
  page:         integer         # Numéro de page (défaut: 1)
  page_size:    integer         # Taille de page (défaut: 50, max: 200)

Headers:
  X-EURKAI-Session: string      # Identifiant de session Cockpit
  Accept: application/json

Response: 200 OK
  Content-Type: application/json
  Body: TreeViewResponse (voir contrat 4.1)

Errors:
  400: Paramètres invalides
  404: root_oid introuvable
  429: Rate limit dépassé
```

**Implémentation backend (pseudo-code)** :

```python
@router.get("/api/v1/fractal/tree")
async def get_fractal_tree(
    root_oid: Optional[str] = None,
    depth: int = 3,
    include: List[str] = [],
    exclude: List[str] = [],
    page: int = 1,
    page_size: int = 50
) -> TreeViewResponse:
    
    # Construction du whatVector
    what_vector = {
        "target": "fractal.tree",
        "root": root_oid or "SYSTEM_ROOT",
        "depth": min(depth, 10),
        "filters": {
            "include_types": include,
            "exclude_types": exclude
        },
        "pagination": {
            "page": page,
            "size": min(page_size, 200)
        }
    }
    
    # Exécution via SuperRead
    result = await SuperRead.execute(
        what_vector=what_vector,
        mode="READ_ONLY"
    )
    
    # Transformation en TreeViewResponse
    return TreeViewResponse.from_script_vector(result.script_vector)
```

---

### 3.2 Endpoint : Charger un objet complet

```yaml
Endpoint: GET /api/v1/object/{oid}
Description: Retourne le bundle complet d'un objet avec sa vue fractale
SuperTool: SuperRead

Path Parameters:
  oid:          string          # Identifiant unique de l'objet

Query Parameters:
  include_lineage:    boolean   # Inclure le lineage complet (défaut: true)
  include_xfractal:   boolean   # Inclure la XFractal résolue (défaut: true)
  include_relations:  boolean   # Inclure les relations (défaut: true)
  resolve_depth:      integer   # Profondeur de résolution (défaut: 1)

Headers:
  X-EURKAI-Session: string
  Accept: application/json

Response: 200 OK
  Body: ObjectBundleResponse (voir contrat 4.2)

Errors:
  400: Paramètres invalides
  404: Objet introuvable
```

**Implémentation backend (pseudo-code)** :

```python
@router.get("/api/v1/object/{oid}")
async def get_object(
    oid: str,
    include_lineage: bool = True,
    include_xfractal: bool = True,
    include_relations: bool = True,
    resolve_depth: int = 1
) -> ObjectBundleResponse:
    
    what_vector = {
        "target": "object.bundle",
        "oid": oid,
        "includes": {
            "lineage": include_lineage,
            "xfractal": include_xfractal,
            "relations": include_relations
        },
        "resolve_depth": min(resolve_depth, 5)
    }
    
    result = await SuperRead.execute(
        what_vector=what_vector,
        mode="READ_ONLY"
    )
    
    if result.is_empty:
        raise HTTPException(404, f"Object {oid} not found")
    
    return ObjectBundleResponse.from_script_vector(result.script_vector)
```

---

### 3.3 Endpoint : Lister les audits disponibles

```yaml
Endpoint: GET /api/v1/audit/catalog
Description: Retourne le catalogue des audits exécutables
SuperTool: SuperRead

Query Parameters:
  category:     string[]        # Filtrer par catégorie (MetaRules, MetaRelations, MetaTests)
  scope:        string          # Scope de l'audit (object, lineage, global)

Response: 200 OK
  Body: AuditCatalogResponse (voir contrat 4.3)
```

**Implémentation backend** :

```python
@router.get("/api/v1/audit/catalog")
async def get_audit_catalog(
    category: List[str] = [],
    scope: Optional[str] = None
) -> AuditCatalogResponse:
    
    what_vector = {
        "target": "audit.catalog",
        "filters": {
            "categories": category if category else ["MetaRules", "MetaRelations", "MetaTests"],
            "scope": scope
        }
    }
    
    result = await SuperRead.execute(what_vector=what_vector, mode="READ_ONLY")
    return AuditCatalogResponse.from_script_vector(result.script_vector)
```

---

### 3.4 Endpoint : Exécuter un audit

```yaml
Endpoint: POST /api/v1/audit/run
Description: Lance un audit sur un périmètre donné et retourne le rapport
SuperTool: SuperEvaluate

Request Body:
  audit_id:     string          # ID de l'audit à exécuter
  scope:        AuditScope      # Périmètre de l'audit
  options:      AuditOptions    # Options d'exécution

AuditScope:
  type:         "object" | "lineage" | "subtree" | "global"
  target_oid:   string | null   # OID cible (si type != global)
  depth:        integer         # Profondeur pour subtree

AuditOptions:
  stop_on_first_error:  boolean # Arrêter à la première erreur
  include_warnings:     boolean # Inclure les warnings
  include_suggestions:  boolean # Inclure les suggestions IA
  output_format:        "summary" | "detailed" | "full"

Response: 200 OK
  Body: AuditReportResponse (voir contrat 4.4)

Response: 202 Accepted (si audit long)
  Body: { "job_id": string, "status_url": string }
```

**Implémentation backend** :

```python
@router.post("/api/v1/audit/run")
async def run_audit(request: AuditRunRequest) -> Union[AuditReportResponse, AuditJobResponse]:
    
    # Construction des vecteurs
    what_vector = {
        "target": "audit.execution",
        "audit_id": request.audit_id,
        "scope": {
            "type": request.scope.type,
            "target": request.scope.target_oid,
            "depth": request.scope.depth
        }
    }
    
    how_vector = {
        "mode": "EVALUATE_ONLY",  # Lecture seule garantie
        "stop_on_error": request.options.stop_on_first_error,
        "include_warnings": request.options.include_warnings,
        "include_suggestions": request.options.include_suggestions,
        "output_format": request.options.output_format
    }
    
    # Estimation de la durée
    estimated_duration = await estimate_audit_duration(what_vector)
    
    if estimated_duration > SYNC_THRESHOLD_SECONDS:
        # Audit asynchrone
        job = await create_audit_job(what_vector, how_vector)
        return AuditJobResponse(
            job_id=job.id,
            status_url=f"/api/v1/audit/job/{job.id}"
        )
    
    # Audit synchrone
    result = await SuperEvaluate.execute(
        what_vector=what_vector,
        how_vector=how_vector
    )
    
    return AuditReportResponse.from_script_vector(result.script_vector)
```

---

### 3.5 Endpoint : Statut d'un audit asynchrone

```yaml
Endpoint: GET /api/v1/audit/job/{job_id}
Description: Retourne le statut d'un audit en cours ou terminé

Response: 200 OK
  Body:
    job_id:     string
    status:     "pending" | "running" | "completed" | "failed"
    progress:   float           # 0.0 à 1.0
    started_at: datetime
    completed_at: datetime | null
    result:     AuditReportResponse | null  # Si completed
    error:      string | null   # Si failed
```

---

## 4. Contrats de données

### 4.1 TreeViewResponse — Vue arbre d'objets

```typescript
interface TreeViewResponse {
  meta: {
    root_oid: string;
    depth_requested: number;
    depth_actual: number;
    total_objects: number;
    timestamp: string;           // ISO 8601
  };
  
  pagination: {
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  
  tree: TreeNode[];
}

interface TreeNode {
  oid: string;                   // Identifiant unique
  type: string;                  // Type d'objet (Agent, Project, Rule, etc.)
  name: string;                  // Nom lisible
  lineage_summary: string;       // Lineage condensé (ex: "Agent <- BaseAgent <- CoreObject")
  
  status: {
    is_valid: boolean;           // Validité actuelle
    last_audit: string | null;   // Date du dernier audit
    issues_count: number;        // Nombre de problèmes détectés
  };
  
  children_count: number;        // Nombre d'enfants directs
  children: TreeNode[];          // Enfants (si dans la profondeur)
  
  // Métadonnées pour le rendu
  _meta: {
    depth: number;               // Niveau dans l'arbre
    has_more_children: boolean;  // Enfants non chargés
    expandable: boolean;         // Peut être expandé
  };
}
```

**Exemple de réponse** :

```json
{
  "meta": {
    "root_oid": "EURKAI_ROOT",
    "depth_requested": 3,
    "depth_actual": 3,
    "total_objects": 247,
    "timestamp": "2025-12-01T10:30:00Z"
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  },
  "tree": [
    {
      "oid": "LAYER_0_CORE",
      "type": "Layer",
      "name": "CORE (Layer 0)",
      "lineage_summary": "Layer <- SystemObject <- CoreObject",
      "status": {
        "is_valid": true,
        "last_audit": "2025-12-01T09:00:00Z",
        "issues_count": 0
      },
      "children_count": 12,
      "children": [
        {
          "oid": "META_SCHEMA_001",
          "type": "MetaSchema",
          "name": "MetaSchema Principal",
          "lineage_summary": "MetaSchema <- Schema <- CoreObject",
          "status": {
            "is_valid": true,
            "last_audit": "2025-12-01T09:00:00Z",
            "issues_count": 0
          },
          "children_count": 5,
          "children": [],
          "_meta": {
            "depth": 2,
            "has_more_children": true,
            "expandable": true
          }
        }
      ],
      "_meta": {
        "depth": 1,
        "has_more_children": false,
        "expandable": true
      }
    }
  ]
}
```

---

### 4.2 ObjectBundleResponse — Fiche objet complète

```typescript
interface ObjectBundleResponse {
  meta: {
    oid: string;
    timestamp: string;
    resolve_depth: number;
  };
  
  object: ObjectCore;
  lineage: LineageInfo;
  xfractal: XFractalView;
  relations: RelationMap;
  bundles: BundleCollection;
}

interface ObjectCore {
  oid: string;
  type: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  
  // Attributs propres (non hérités)
  own_attributes: Record<string, AttributeValue>;
}

interface LineageInfo {
  // Chaîne d'héritage complète (du plus général au plus spécifique)
  chain: LineageNode[];
  
  // Injections actives
  injections: InjectionInfo[];
  
  // Spécificités (overrides)
  specifics: SpecificInfo[];
}

interface LineageNode {
  oid: string;
  type: string;
  name: string;
  level: number;              // 0 = racine, N = courant
  contributes: {
    attributes: string[];     // Noms des attributs contribués
    methods: string[];        // Noms des méthodes contribuées
    rules: string[];          // Noms des règles contribuées
  };
}

interface InjectionInfo {
  source_oid: string;
  source_name: string;
  injection_type: "mixin" | "trait" | "capability";
  contributes: {
    attributes: string[];
    methods: string[];
    rules: string[];
  };
}

interface SpecificInfo {
  attribute: string;
  original_from: string;      // OID de l'origine
  override_value: any;
}

interface XFractalView {
  // Vue consolidée à l'instant T
  // "Ce que l'objet voit comme attributs, méthodes, règles, relations"
  
  resolved_attributes: Record<string, ResolvedAttribute>;
  resolved_methods: Record<string, ResolvedMethod>;
  resolved_rules: Record<string, ResolvedRule>;
  
  // Métadonnées de résolution
  resolution_meta: {
    computed_at: string;
    lineage_hash: string;     // Hash pour détecter les changements
    conflicts: ConflictInfo[];
  };
}

interface ResolvedAttribute {
  name: string;
  value: any;
  type: string;
  source: {
    origin: string;           // OID de l'origine
    via: "inheritance" | "injection" | "override";
  };
}

interface ResolvedMethod {
  name: string;
  signature: string;
  source: {
    origin: string;
    via: "inheritance" | "injection" | "override";
  };
}

interface ResolvedRule {
  rule_id: string;
  name: string;
  erk_expression: string;     // Expression ERK
  priority: number;
  source: {
    origin: string;
    via: "inheritance" | "injection" | "override";
  };
}

interface RelationMap {
  // Relations vers d'autres objets
  outgoing: RelationInfo[];
  
  // Relations depuis d'autres objets
  incoming: RelationInfo[];
}

interface RelationInfo {
  relation_type: string;      // Type de relation (contient, référence, extends, etc.)
  target_oid: string;
  target_name: string;
  target_type: string;
  metadata: Record<string, any>;
}

interface BundleCollection {
  // Bundles attachés à l'objet
  bundles: BundleInfo[];
}

interface BundleInfo {
  bundle_id: string;
  bundle_type: string;
  name: string;
  content_summary: string;    # Résumé du contenu
  size_bytes: number;
}
```

**Exemple de réponse** :

```json
{
  "meta": {
    "oid": "AGENT_GPT_ANALYZER",
    "timestamp": "2025-12-01T10:35:00Z",
    "resolve_depth": 1
  },
  "object": {
    "oid": "AGENT_GPT_ANALYZER",
    "type": "Agent",
    "name": "GPT Analyzer Agent",
    "description": "Agent spécialisé dans l'analyse de code et génération de prompts",
    "created_at": "2025-11-15T08:00:00Z",
    "updated_at": "2025-11-30T14:22:00Z",
    "version": 7,
    "own_attributes": {
      "model": "gpt-4o",
      "temperature": 0.3,
      "max_tokens": 4096
    }
  },
  "lineage": {
    "chain": [
      {
        "oid": "CORE_OBJECT",
        "type": "CoreObject",
        "name": "CoreObject",
        "level": 0,
        "contributes": {
          "attributes": ["oid", "created_at", "updated_at", "version"],
          "methods": ["validate", "serialize"],
          "rules": ["RULE_CORE_INTEGRITY"]
        }
      },
      {
        "oid": "BASE_AGENT",
        "type": "BaseAgent",
        "name": "BaseAgent",
        "level": 1,
        "contributes": {
          "attributes": ["model", "temperature"],
          "methods": ["execute", "analyze"],
          "rules": ["RULE_AGENT_EXECUTION"]
        }
      },
      {
        "oid": "AGENT_GPT_ANALYZER",
        "type": "Agent",
        "name": "GPT Analyzer Agent",
        "level": 2,
        "contributes": {
          "attributes": ["max_tokens"],
          "methods": ["generate_prompt"],
          "rules": []
        }
      }
    ],
    "injections": [
      {
        "source_oid": "MIXIN_LOGGING",
        "source_name": "Logging Mixin",
        "injection_type": "mixin",
        "contributes": {
          "attributes": [],
          "methods": ["log_info", "log_error"],
          "rules": []
        }
      }
    ],
    "specifics": [
      {
        "attribute": "temperature",
        "original_from": "BASE_AGENT",
        "override_value": 0.3
      }
    ]
  },
  "xfractal": {
    "resolved_attributes": {
      "oid": {
        "name": "oid",
        "value": "AGENT_GPT_ANALYZER",
        "type": "string",
        "source": { "origin": "CORE_OBJECT", "via": "inheritance" }
      },
      "model": {
        "name": "model",
        "value": "gpt-4o",
        "type": "string",
        "source": { "origin": "AGENT_GPT_ANALYZER", "via": "override" }
      }
    },
    "resolved_methods": {
      "execute": {
        "name": "execute",
        "signature": "(context: Context) -> Result",
        "source": { "origin": "BASE_AGENT", "via": "inheritance" }
      }
    },
    "resolved_rules": {
      "RULE_CORE_INTEGRITY": {
        "rule_id": "RULE_CORE_INTEGRITY",
        "name": "Core Integrity Check",
        "erk_expression": "REQUIRE(oid IS NOT NULL AND version > 0)",
        "priority": 100,
        "source": { "origin": "CORE_OBJECT", "via": "inheritance" }
      }
    },
    "resolution_meta": {
      "computed_at": "2025-12-01T10:35:00Z",
      "lineage_hash": "a7f3c2e1",
      "conflicts": []
    }
  },
  "relations": {
    "outgoing": [
      {
        "relation_type": "belongs_to",
        "target_oid": "LAYER_3_AGENCY",
        "target_name": "AGENCY (Layer 3)",
        "target_type": "Layer",
        "metadata": {}
      }
    ],
    "incoming": [
      {
        "relation_type": "uses",
        "target_oid": "PROJECT_AUTO_FUNCTION",
        "target_name": "Auto Function Builder",
        "target_type": "Project",
        "metadata": { "usage_count": 47 }
      }
    ]
  },
  "bundles": {
    "bundles": [
      {
        "bundle_id": "BUNDLE_PROMPT_TEMPLATE",
        "bundle_type": "PromptTemplate",
        "name": "Analyse de code Python",
        "content_summary": "Template pour l'analyse statique de code Python",
        "size_bytes": 2048
      }
    ]
  }
}
```

---

### 4.3 AuditCatalogResponse — Catalogue des audits

```typescript
interface AuditCatalogResponse {
  meta: {
    total_audits: number;
    categories: string[];
    timestamp: string;
  };
  
  audits: AuditDefinition[];
}

interface AuditDefinition {
  audit_id: string;
  name: string;
  description: string;
  category: "MetaRules" | "MetaRelations" | "MetaTests" | "Integrity" | "Performance";
  
  scope_options: {
    supports_object: boolean;
    supports_lineage: boolean;
    supports_subtree: boolean;
    supports_global: boolean;
  };
  
  estimated_duration: {
    per_object_ms: number;      // Durée estimée par objet
    base_ms: number;            // Durée de base
  };
  
  severity_levels: string[];    // ["critical", "error", "warning", "info"]
  
  // Dernière exécution globale
  last_global_run: {
    timestamp: string | null;
    passed: boolean | null;
    issues_found: number | null;
  };
}
```

---

### 4.4 AuditReportResponse — Rapport d'audit

```typescript
interface AuditReportResponse {
  meta: {
    audit_id: string;
    audit_name: string;
    scope: AuditScope;
    executed_at: string;
    duration_ms: number;
  };
  
  summary: {
    status: "passed" | "failed" | "warning";
    objects_analyzed: number;
    rules_evaluated: number;
    issues_total: number;
    issues_by_severity: Record<string, number>;
  };
  
  issues: AuditIssue[];
  
  suggestions: AuditSuggestion[];  // Si include_suggestions était true
  
  // Détails par objet (si output_format != summary)
  object_details: ObjectAuditDetail[];
}

interface AuditIssue {
  issue_id: string;
  severity: "critical" | "error" | "warning" | "info";
  
  location: {
    oid: string;
    object_name: string;
    attribute: string | null;
    rule_id: string | null;
  };
  
  message: string;
  erk_context: string | null;     // Expression ERK qui a échoué
  
  // Pour le rendu Cockpit
  _display: {
    icon: string;                  // Icône suggérée
    color: string;                 // Couleur suggérée
    action_label: string | null;   // Label d'action possible
  };
}

interface AuditSuggestion {
  suggestion_id: string;
  related_issue_id: string;
  
  type: "fix" | "refactor" | "optimize" | "investigate";
  confidence: number;              // 0.0 à 1.0
  
  title: string;
  description: string;
  
  // Action suggérée (pour H2+ quand le write sera activé)
  proposed_action: {
    action_type: string;
    target_oid: string;
    changes: Record<string, any>;
  } | null;
}

interface ObjectAuditDetail {
  oid: string;
  object_name: string;
  
  rules_evaluated: number;
  rules_passed: number;
  rules_failed: number;
  
  issues: string[];               // IDs des issues liées
}
```

**Exemple de rapport** :

```json
{
  "meta": {
    "audit_id": "AUDIT_LINEAGE_INTEGRITY",
    "audit_name": "Vérification d'intégrité des lineages",
    "scope": {
      "type": "subtree",
      "target_oid": "LAYER_3_AGENCY",
      "depth": 5
    },
    "executed_at": "2025-12-01T10:40:00Z",
    "duration_ms": 1247
  },
  "summary": {
    "status": "warning",
    "objects_analyzed": 34,
    "rules_evaluated": 156,
    "issues_total": 3,
    "issues_by_severity": {
      "critical": 0,
      "error": 0,
      "warning": 2,
      "info": 1
    }
  },
  "issues": [
    {
      "issue_id": "ISSUE_001",
      "severity": "warning",
      "location": {
        "oid": "AGENT_DEPRECATED_V1",
        "object_name": "Deprecated Agent V1",
        "attribute": null,
        "rule_id": "RULE_LINEAGE_ACTIVE"
      },
      "message": "L'objet hérite d'un parent marqué comme déprécié",
      "erk_context": "REQUIRE(parent.status != 'deprecated')",
      "_display": {
        "icon": "warning-triangle",
        "color": "#FFA500",
        "action_label": "Voir le parent"
      }
    }
  ],
  "suggestions": [
    {
      "suggestion_id": "SUGG_001",
      "related_issue_id": "ISSUE_001",
      "type": "refactor",
      "confidence": 0.85,
      "title": "Migrer vers le nouveau parent",
      "description": "Remplacer l'héritage de DEPRECATED_PARENT par NEW_PARENT qui offre les mêmes capacités",
      "proposed_action": null
    }
  ],
  "object_details": []
}
```

---

## 5. Design d'intégration Cockpit

### 5.1 Architecture côté Cockpit

```
┌─────────────────────────────────────────────────────────────┐
│                     COCKPIT APPLICATION                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    STATE MANAGER                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ TreeState   │  │ ObjectState │  │ AuditState  │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   API SERVICE LAYER                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ FractalAPI  │  │ ObjectAPI   │  │ AuditAPI    │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                      UI COMPONENTS                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │ TreeView    │  │ ObjectPanel │  │ AuditPanel  │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Service API — FractalAPI

```typescript
// services/FractalAPI.ts

class FractalAPI {
  private baseUrl: string;
  private cache: Map<string, CacheEntry>;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.cache = new Map();
  }
  
  /**
   * Charge l'arbre fractal
   */
  async loadTree(options: TreeLoadOptions): Promise<TreeViewResponse> {
    const cacheKey = this.buildCacheKey('tree', options);
    
    if (this.isCacheValid(cacheKey)) {
      return this.cache.get(cacheKey)!.data;
    }
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/fractal/tree?` + new URLSearchParams({
        root_oid: options.rootOid || '',
        depth: String(options.depth || 3),
        page: String(options.page || 1),
        page_size: String(options.pageSize || 50),
        ...(options.include && { include: options.include.join(',') }),
        ...(options.exclude && { exclude: options.exclude.join(',') })
      })
    );
    
    if (!response.ok) {
      throw new FractalAPIError(response.status, await response.text());
    }
    
    const data = await response.json();
    this.setCache(cacheKey, data, 60000); // Cache 1 minute
    return data;
  }
  
  /**
   * Charge un sous-arbre (expansion lazy)
   */
  async expandNode(oid: string, depth: number = 2): Promise<TreeNode[]> {
    const response = await this.loadTree({
      rootOid: oid,
      depth: depth,
      page: 1,
      pageSize: 100
    });
    
    return response.tree;
  }
  
  /**
   * Recherche dans l'arbre
   */
  async searchTree(query: string, options?: SearchOptions): Promise<TreeNode[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/fractal/search?` + new URLSearchParams({
        q: query,
        limit: String(options?.limit || 20)
      })
    );
    
    if (!response.ok) {
      throw new FractalAPIError(response.status, await response.text());
    }
    
    return (await response.json()).results;
  }
}
```

### 5.3 Service API — ObjectAPI

```typescript
// services/ObjectAPI.ts

class ObjectAPI {
  private baseUrl: string;
  private objectCache: Map<string, CacheEntry>;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.objectCache = new Map();
  }
  
  /**
   * Charge un objet complet avec son bundle
   */
  async loadObject(oid: string, options?: ObjectLoadOptions): Promise<ObjectBundleResponse> {
    const cacheKey = `object:${oid}:${JSON.stringify(options || {})}`;
    
    if (this.isCacheValid(cacheKey)) {
      return this.objectCache.get(cacheKey)!.data;
    }
    
    const params = new URLSearchParams({
      include_lineage: String(options?.includeLineage ?? true),
      include_xfractal: String(options?.includeXFractal ?? true),
      include_relations: String(options?.includeRelations ?? true),
      resolve_depth: String(options?.resolveDepth ?? 1)
    });
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/object/${oid}?${params}`
    );
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new ObjectNotFoundError(oid);
      }
      throw new ObjectAPIError(response.status, await response.text());
    }
    
    const data = await response.json();
    this.setCache(cacheKey, data, 30000); // Cache 30 secondes
    return data;
  }
  
  /**
   * Charge uniquement le lineage (léger)
   */
  async loadLineage(oid: string): Promise<LineageInfo> {
    const obj = await this.loadObject(oid, {
      includeLineage: true,
      includeXFractal: false,
      includeRelations: false,
      resolveDepth: 0
    });
    return obj.lineage;
  }
  
  /**
   * Invalide le cache pour un objet
   */
  invalidateObject(oid: string): void {
    for (const key of this.objectCache.keys()) {
      if (key.startsWith(`object:${oid}:`)) {
        this.objectCache.delete(key);
      }
    }
  }
}
```

### 5.4 Service API — AuditAPI

```typescript
// services/AuditAPI.ts

class AuditAPI {
  private baseUrl: string;
  private pollingIntervalMs: number = 1000;
  
  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }
  
  /**
   * Récupère le catalogue des audits disponibles
   */
  async getCatalog(filters?: AuditCatalogFilters): Promise<AuditCatalogResponse> {
    const params = new URLSearchParams();
    if (filters?.category) {
      filters.category.forEach(c => params.append('category', c));
    }
    if (filters?.scope) {
      params.set('scope', filters.scope);
    }
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/audit/catalog?${params}`
    );
    
    if (!response.ok) {
      throw new AuditAPIError(response.status, await response.text());
    }
    
    return response.json();
  }
  
  /**
   * Lance un audit et attend le résultat
   */
  async runAudit(
    auditId: string,
    scope: AuditScope,
    options: AuditOptions,
    onProgress?: (progress: number) => void
  ): Promise<AuditReportResponse> {
    
    const response = await fetch(`${this.baseUrl}/api/v1/audit/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        audit_id: auditId,
        scope: scope,
        options: options
      })
    });
    
    if (!response.ok) {
      throw new AuditAPIError(response.status, await response.text());
    }
    
    const result = await response.json();
    
    // Si c'est un job asynchrone, on poll
    if (result.job_id) {
      return this.pollAuditJob(result.job_id, onProgress);
    }
    
    // Sinon, résultat direct
    return result;
  }
  
  /**
   * Poll un job d'audit jusqu'à complétion
   */
  private async pollAuditJob(
    jobId: string,
    onProgress?: (progress: number) => void
  ): Promise<AuditReportResponse> {
    
    while (true) {
      const response = await fetch(
        `${this.baseUrl}/api/v1/audit/job/${jobId}`
      );
      
      if (!response.ok) {
        throw new AuditAPIError(response.status, await response.text());
      }
      
      const status = await response.json();
      
      if (onProgress) {
        onProgress(status.progress);
      }
      
      if (status.status === 'completed') {
        return status.result;
      }
      
      if (status.status === 'failed') {
        throw new AuditExecutionError(status.error);
      }
      
      // Attendre avant le prochain poll
      await new Promise(resolve => setTimeout(resolve, this.pollingIntervalMs));
    }
  }
  
  /**
   * Raccourci : audit rapide sur un objet
   */
  async quickAudit(oid: string): Promise<AuditReportResponse> {
    return this.runAudit(
      'AUDIT_QUICK_VALIDATION',
      { type: 'object', target_oid: oid, depth: 0 },
      { stop_on_first_error: false, include_warnings: true, include_suggestions: true, output_format: 'detailed' }
    );
  }
}
```

### 5.5 Composants UI

#### 5.5.1 TreeView — Arbre fractal

```tsx
// components/TreeView.tsx

interface TreeViewProps {
  onSelectNode: (oid: string) => void;
  onExpandNode: (oid: string) => void;
  selectedOid: string | null;
}

const TreeView: React.FC<TreeViewProps> = ({ onSelectNode, onExpandNode, selectedOid }) => {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  
  const fractalAPI = useFractalAPI();
  
  useEffect(() => {
    loadInitialTree();
  }, []);
  
  const loadInitialTree = async () => {
    setLoading(true);
    try {
      const response = await fractalAPI.loadTree({ depth: 2 });
      setTree(response.tree);
    } catch (error) {
      console.error('Failed to load tree:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleExpand = async (node: TreeNode) => {
    if (expandedNodes.has(node.oid)) {
      // Collapse
      setExpandedNodes(prev => {
        const next = new Set(prev);
        next.delete(node.oid);
        return next;
      });
    } else {
      // Expand — charger les enfants si nécessaire
      if (node._meta.has_more_children && node.children.length === 0) {
        const children = await fractalAPI.expandNode(node.oid);
        // Mettre à jour le nœud avec les enfants chargés
        updateNodeChildren(node.oid, children);
      }
      setExpandedNodes(prev => new Set(prev).add(node.oid));
    }
    onExpandNode(node.oid);
  };
  
  const renderNode = (node: TreeNode, depth: number = 0) => (
    <div 
      key={node.oid} 
      className={`tree-node depth-${depth} ${selectedOid === node.oid ? 'selected' : ''}`}
    >
      <div className="tree-node-content" onClick={() => onSelectNode(node.oid)}>
        {node._meta.expandable && (
          <button 
            className="expand-btn" 
            onClick={(e) => { e.stopPropagation(); handleExpand(node); }}
          >
            {expandedNodes.has(node.oid) ? '▼' : '▶'}
          </button>
        )}
        
        <span className="node-icon">{getIconForType(node.type)}</span>
        <span className="node-name">{node.name}</span>
        
        {node.status.issues_count > 0 && (
          <span className="issues-badge">{node.status.issues_count}</span>
        )}
      </div>
      
      {expandedNodes.has(node.oid) && node.children.length > 0 && (
        <div className="tree-children">
          {node.children.map(child => renderNode(child, depth + 1))}
        </div>
      )}
    </div>
  );
  
  if (loading) {
    return <div className="tree-loading">Chargement de la fractale...</div>;
  }
  
  return (
    <div className="tree-view">
      <div className="tree-header">
        <h3>Fractale EURKAI</h3>
        <button onClick={loadInitialTree}>↻ Rafraîchir</button>
      </div>
      <div className="tree-container">
        {tree.map(node => renderNode(node))}
      </div>
    </div>
  );
};
```

#### 5.5.2 ObjectPanel — Fiche objet

```tsx
// components/ObjectPanel.tsx

interface ObjectPanelProps {
  oid: string | null;
  onRunAudit: (oid: string) => void;
}

const ObjectPanel: React.FC<ObjectPanelProps> = ({ oid, onRunAudit }) => {
  const [object, setObject] = useState<ObjectBundleResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'lineage' | 'xfractal' | 'relations'>('overview');
  const [loading, setLoading] = useState(false);
  
  const objectAPI = useObjectAPI();
  
  useEffect(() => {
    if (oid) {
      loadObject(oid);
    } else {
      setObject(null);
    }
  }, [oid]);
  
  const loadObject = async (oid: string) => {
    setLoading(true);
    try {
      const data = await objectAPI.loadObject(oid);
      setObject(data);
    } catch (error) {
      console.error('Failed to load object:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (!oid) {
    return (
      <div className="object-panel empty">
        <p>Sélectionnez un objet dans l'arbre pour voir ses détails</p>
      </div>
    );
  }
  
  if (loading) {
    return <div className="object-panel loading">Chargement...</div>;
  }
  
  if (!object) {
    return <div className="object-panel error">Objet introuvable</div>;
  }
  
  return (
    <div className="object-panel">
      <div className="object-header">
        <h2>{object.object.name}</h2>
        <span className="object-type">{object.object.type}</span>
        <span className="object-oid">{object.object.oid}</span>
        
        <div className="object-actions">
          <button onClick={() => onRunAudit(oid)}>🔍 Auditer</button>
          <button onClick={() => loadObject(oid)}>↻ Rafraîchir</button>
        </div>
      </div>
      
      <div className="object-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''} 
          onClick={() => setActiveTab('overview')}
        >
          Vue générale
        </button>
        <button 
          className={activeTab === 'lineage' ? 'active' : ''} 
          onClick={() => setActiveTab('lineage')}
        >
          Lineage
        </button>
        <button 
          className={activeTab === 'xfractal' ? 'active' : ''} 
          onClick={() => setActiveTab('xfractal')}
        >
          XFractal
        </button>
        <button 
          className={activeTab === 'relations' ? 'active' : ''} 
          onClick={() => setActiveTab('relations')}
        >
          Relations
        </button>
      </div>
      
      <div className="object-content">
        {activeTab === 'overview' && <OverviewTab object={object} />}
        {activeTab === 'lineage' && <LineageTab lineage={object.lineage} />}
        {activeTab === 'xfractal' && <XFractalTab xfractal={object.xfractal} />}
        {activeTab === 'relations' && <RelationsTab relations={object.relations} />}
      </div>
    </div>
  );
};
```

#### 5.5.3 AuditPanel — Panneau d'audit

```tsx
// components/AuditPanel.tsx

interface AuditPanelProps {
  targetOid: string | null;
}

const AuditPanel: React.FC<AuditPanelProps> = ({ targetOid }) => {
  const [catalog, setCatalog] = useState<AuditDefinition[]>([]);
  const [selectedAudit, setSelectedAudit] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [report, setReport] = useState<AuditReportResponse | null>(null);
  
  const auditAPI = useAuditAPI();
  
  useEffect(() => {
    loadCatalog();
  }, []);
  
  const loadCatalog = async () => {
    const response = await auditAPI.getCatalog();
    setCatalog(response.audits);
  };
  
  const runSelectedAudit = async () => {
    if (!selectedAudit || !targetOid) return;
    
    setRunning(true);
    setProgress(0);
    setReport(null);
    
    try {
      const result = await auditAPI.runAudit(
        selectedAudit,
        { type: 'object', target_oid: targetOid, depth: 3 },
        { 
          stop_on_first_error: false, 
          include_warnings: true, 
          include_suggestions: true, 
          output_format: 'detailed' 
        },
        (p) => setProgress(p)
      );
      setReport(result);
    } catch (error) {
      console.error('Audit failed:', error);
    } finally {
      setRunning(false);
    }
  };
  
  return (
    <div className="audit-panel">
      <div className="audit-header">
        <h3>Audits</h3>
      </div>
      
      <div className="audit-selector">
        <select 
          value={selectedAudit || ''} 
          onChange={(e) => setSelectedAudit(e.target.value || null)}
          disabled={running}
        >
          <option value="">-- Sélectionner un audit --</option>
          {catalog.map(audit => (
            <option key={audit.audit_id} value={audit.audit_id}>
              {audit.name} ({audit.category})
            </option>
          ))}
        </select>
        
        <button 
          onClick={runSelectedAudit} 
          disabled={!selectedAudit || !targetOid || running}
        >
          {running ? `Exécution... ${Math.round(progress * 100)}%` : '▶ Exécuter'}
        </button>
      </div>
      
      {report && (
        <div className="audit-report">
          <div className={`report-status status-${report.summary.status}`}>
            {report.summary.status === 'passed' && '✓ Validé'}
            {report.summary.status === 'warning' && '⚠ Warnings'}
            {report.summary.status === 'failed' && '✗ Échec'}
          </div>
          
          <div className="report-summary">
            <span>{report.summary.objects_analyzed} objets analysés</span>
            <span>{report.summary.rules_evaluated} règles évaluées</span>
            <span>{report.summary.issues_total} problèmes</span>
          </div>
          
          {report.issues.length > 0 && (
            <div className="report-issues">
              <h4>Problèmes détectés</h4>
              {report.issues.map(issue => (
                <div 
                  key={issue.issue_id} 
                  className={`issue severity-${issue.severity}`}
                >
                  <span className="issue-icon">{issue._display.icon}</span>
                  <span className="issue-location">{issue.location.object_name}</span>
                  <span className="issue-message">{issue.message}</span>
                </div>
              ))}
            </div>
          )}
          
          {report.suggestions.length > 0 && (
            <div className="report-suggestions">
              <h4>Suggestions</h4>
              {report.suggestions.map(sugg => (
                <div key={sugg.suggestion_id} className="suggestion">
                  <span className="suggestion-type">{sugg.type}</span>
                  <span className="suggestion-title">{sugg.title}</span>
                  <p className="suggestion-desc">{sugg.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## 6. Gestion de la volumétrie

### 6.1 Stratégie de pagination

| Endpoint | Pagination par défaut | Max | Stratégie |
|----------|----------------------|-----|-----------|
| `/fractal/tree` | 50 | 200 | Cursor-based (page) |
| `/object/{oid}` | N/A | N/A | Objet unique |
| `/audit/catalog` | 50 | 100 | Offset |
| `/audit/run` | N/A | N/A | Streaming si > seuil |

### 6.2 Chargement lazy de l'arbre

```typescript
// Stratégie de chargement progressif

interface LazyTreeStrategy {
  // Chargement initial
  initialDepth: 2,
  initialPageSize: 50,
  
  // Expansion d'un nœud
  expansionDepth: 2,
  expansionPageSize: 100,
  
  // Seuils pour affichage
  maxVisibleChildren: 100,      // Au-delà, afficher "... et N autres"
  virtualScrollThreshold: 500,  // Activer virtual scroll au-delà
}

// Implémentation du chargement lazy
async function loadNodeChildren(
  oid: string, 
  page: number = 1
): Promise<{nodes: TreeNode[], hasMore: boolean}> {
  const response = await fractalAPI.loadTree({
    rootOid: oid,
    depth: 1,
    page: page,
    pageSize: 100
  });
  
  return {
    nodes: response.tree[0]?.children || [],
    hasMore: response.pagination.has_next
  };
}
```

### 6.3 Cache côté Cockpit

```typescript
// Configuration du cache

interface CacheConfig {
  // Cache de l'arbre
  tree: {
    ttl: 60000,          // 1 minute
    maxEntries: 100,
    invalidateOn: ['audit_complete', 'manual_refresh']
  },
  
  // Cache des objets
  object: {
    ttl: 30000,          // 30 secondes
    maxEntries: 50,
    invalidateOn: ['audit_complete', 'manual_refresh']
  },
  
  // Cache du catalogue d'audits
  auditCatalog: {
    ttl: 300000,         // 5 minutes
    maxEntries: 1,
    invalidateOn: ['manual_refresh']
  }
}
```

---

## 7. Sécurité et contrôles

### 7.1 Garanties de lecture seule

```python
# Middleware de sécurité backend

class ReadOnlyMiddleware:
    """
    Garantit que toutes les requêtes H1 sont en lecture seule.
    """
    
    ALLOWED_METHODS = {'GET', 'HEAD', 'OPTIONS'}
    AUDIT_ENDPOINT = '/api/v1/audit/run'  # Seul POST autorisé
    
    async def __call__(self, request: Request, call_next):
        # Vérifier la méthode
        if request.method not in self.ALLOWED_METHODS:
            # Exception pour l'audit (POST mais read-only)
            if request.url.path == self.AUDIT_ENDPOINT and request.method == 'POST':
                # Vérifier que l'audit ne modifie rien
                body = await request.json()
                if body.get('mode') == 'EVALUATE_ONLY':
                    return await call_next(request)
                raise HTTPException(403, "Write operations not allowed in H1")
            raise HTTPException(405, "Method not allowed in read-only mode")
        
        return await call_next(request)
```

### 7.2 Validation des SuperTools

```python
# Vérification que SuperRead/SuperEvaluate sont bien en mode lecture

class SuperToolGuard:
    """
    Vérifie que les SuperTools ne peuvent pas modifier la fractale.
    """
    
    ALLOWED_SUPERTOOLS = {'SuperRead', 'SuperEvaluate'}
    
    def validate_execution(self, supertool_name: str, how_vector: dict) -> bool:
        if supertool_name not in self.ALLOWED_SUPERTOOLS:
            raise SecurityException(f"SuperTool {supertool_name} not allowed in H1")
        
        # SuperEvaluate doit être en mode EVALUATE_ONLY
        if supertool_name == 'SuperEvaluate':
            if how_vector.get('mode') != 'EVALUATE_ONLY':
                raise SecurityException("SuperEvaluate must be in EVALUATE_ONLY mode")
        
        return True
```

### 7.3 Logging des accès

```python
# Traçabilité des accès

@dataclass
class AccessLog:
    timestamp: datetime
    session_id: str
    endpoint: str
    supertool: str
    what_vector_hash: str
    duration_ms: int
    result_status: str
    objects_accessed: List[str]

class AccessLogger:
    async def log_access(
        self, 
        request: Request, 
        supertool: str, 
        what_vector: dict,
        result: Any,
        duration_ms: int
    ):
        log = AccessLog(
            timestamp=datetime.utcnow(),
            session_id=request.headers.get('X-EURKAI-Session', 'unknown'),
            endpoint=request.url.path,
            supertool=supertool,
            what_vector_hash=hash_vector(what_vector),
            duration_ms=duration_ms,
            result_status='success' if result else 'empty',
            objects_accessed=extract_oids(result)
        )
        await self.store(log)
```

---

## 8. Annexes techniques

### 8.1 Codes d'erreur

| Code | Signification | Action Cockpit |
|------|---------------|----------------|
| 400 | Paramètres invalides | Afficher message d'erreur |
| 404 | Objet/Audit introuvable | Afficher "Non trouvé" |
| 405 | Méthode non autorisée | Log erreur interne |
| 429 | Rate limit dépassé | Attendre et réessayer |
| 500 | Erreur serveur | Afficher message générique |
| 503 | Service indisponible | Afficher mode dégradé |

### 8.2 Headers HTTP

```yaml
# Requête
X-EURKAI-Session: string       # Identifiant de session Cockpit
Accept: application/json
Accept-Language: fr-FR         # Pour les messages localisés

# Réponse
X-EURKAI-Request-Id: string    # ID unique pour traçabilité
X-EURKAI-Cache-Status: HIT|MISS
X-EURKAI-Execution-Time: number # Temps d'exécution en ms
```

### 8.3 Diagramme de séquence — Audit complet

```
┌─────────┐     ┌─────────┐     ┌───────────────┐     ┌──────────┐
│ Cockpit │     │ Gateway │     │ SuperEvaluate │     │ Fractale │
└────┬────┘     └────┬────┘     └───────┬───────┘     └────┬─────┘
     │               │                  │                   │
     │ POST /audit/run                  │                   │
     │──────────────>│                  │                   │
     │               │ validate_request │                   │
     │               │─────────────────>│                   │
     │               │                  │ read_scope        │
     │               │                  │──────────────────>│
     │               │                  │<──────────────────│
     │               │                  │ evaluate_rules    │
     │               │                  │──────────────────>│
     │               │                  │<──────────────────│
     │               │ build_report     │                   │
     │               │<─────────────────│                   │
     │ AuditReport   │                  │                   │
     │<──────────────│                  │                   │
```

### 8.4 Checklist d'implémentation

**Backend :**
- [ ] Endpoint GET /api/v1/fractal/tree
- [ ] Endpoint GET /api/v1/object/{oid}
- [ ] Endpoint GET /api/v1/audit/catalog
- [ ] Endpoint POST /api/v1/audit/run
- [ ] Endpoint GET /api/v1/audit/job/{job_id}
- [ ] Middleware ReadOnly
- [ ] SuperToolGuard
- [ ] AccessLogger
- [ ] Tests unitaires endpoints
- [ ] Tests d'intégration SuperTools

**Cockpit :**
- [ ] FractalAPI service
- [ ] ObjectAPI service
- [ ] AuditAPI service
- [ ] TreeView component
- [ ] ObjectPanel component
- [ ] AuditPanel component
- [ ] Cache manager
- [ ] Error handling global
- [ ] Tests composants

---

## Fin du document H1

**Prochaine étape** : H2 — Activation des opérations d'écriture (SuperCreate, SuperUpdate, SuperDelete) avec validation GEVR.
