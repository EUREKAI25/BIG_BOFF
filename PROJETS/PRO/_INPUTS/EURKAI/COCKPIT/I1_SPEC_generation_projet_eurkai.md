# I1 — Génération de Projet EURKAI depuis un Brief

## Spécification Technique Complète

**Version** : 1.0  
**Date** : 2025-12-01  
**Dépendances** : H2 (Super.orchestrate), H3 (FractalDiff)  
**Pattern** : GEVR (Get-Execute-Validate-Render)

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Formats d'entrée acceptés](#2-formats-dentrée-acceptés)
3. [Analyse d'intention](#3-analyse-dintention)
4. [Pipeline de génération](#4-pipeline-de-génération)
5. [Manifest Projet](#5-manifest-projet)
6. [Intégration avec H2/H3](#6-intégration-avec-h2h3)
7. [Scénarios de test](#7-scénarios-de-test)
8. [Annexes](#8-annexes)

---

## 1. Vue d'ensemble

### 1.1 Objectif

I1 implémente le **MetaScénario "Projet EURKAI"** : transformer n'importe quel input (texte, brief, cahier des charges, manifest) en une **structure fractale complète** prête à être validée et appliquée via le Cockpit.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          I1 — PROJECT GENERATOR                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   INPUT                    PROCESS                      OUTPUT           │
│   ─────                    ───────                      ──────           │
│   OrchestrateInput         ┌─────────────────────┐      FractalDiff      │
│   (H2)                     │  1. GET             │      (H3)             │
│   ├─ text                  │     Parse input     │      ├─ changes[]    │
│   ├─ files[]               │     Load context    │      │  └─ ObjectDiff│
│   │  ├─ .md                │                     │      ├─ summary      │
│   │  ├─ .json              │  2. EXECUTE         │      └─ manifest     │
│   │  └─ .yaml              │     Analyze intent  │                       │
│   └─ context               │     Map to objects  │      +                │
│      ├─ target_path        │     Build skeleton  │      ProjectManifest │
│      └─ scenario_hint      │                     │                       │
│                            │  3. VALIDATE        │                       │
│                            │     Check coherence │                       │
│                            │     Resolve conflicts│                      │
│                            │                     │                       │
│                            │  4. RENDER          │                       │
│                            │     Generate diff   │                       │
│                            │     Produce manifest│                       │
│                            └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Principes architecturaux

| Principe | Description |
|----------|-------------|
| **Fractalité** | Tout projet est un objet fractal avec lineage, bundles, relations |
| **IVC×DRO** | Chaque objet respecte Identity-View-Context × Definition-Rule-Option |
| **Dry-run first** | Aucune écriture directe, uniquement génération de FractalDiff |
| **Idempotence** | Le même input produit toujours le même output |
| **Traçabilité** | Chaque décision de mapping est loggée |

### 1.3 Flux d'exécution

```
User Input ──► Super.orchestrate() ──► I1.ProjectGenerator ──► FractalDiff
                    │                         │                    │
                    │                         ▼                    │
                    │                  IntentAnalyzer              │
                    │                         │                    │
                    │                         ▼                    │
                    │                  ObjectMapper                │
                    │                         │                    │
                    │                         ▼                    │
                    │                  SkeletonBuilder             │
                    │                         │                    │
                    │                         ▼                    │
                    │                  ManifestGenerator           │
                    │                         │                    │
                    └─────────────────────────┴────────────────────┘
```

---

## 2. Formats d'entrée acceptés

### 2.1 Compatibilité H2 (OrchestrateInput)

I1 consomme directement le format `OrchestrateInput` défini dans H2 :

```typescript
interface I1Input extends OrchestrateInput {
  type: 'text' | 'file' | 'mixed';
  text?: string;                    // Brief textuel
  files?: FilePayload[];            // Fichiers structurés
  context?: I1Context;              // Contexte enrichi
}

interface I1Context extends InputContext {
  target_path?: string;             // Chemin fractal cible
  scenario_hint?: 'project_creation' | 'module_addition' | 'migration';
  tags?: string[];
  
  // Extensions I1
  project_template?: string;        // Template prédéfini
  inherit_from?: string;            // OID parent pour héritage
  domain?: string;                  // Domaine métier
}
```

### 2.2 Formats de fichiers supportés

| Format | MIME Type | Usage | Parser |
|--------|-----------|-------|--------|
| **Markdown** | `text/markdown` | Brief, documentation | `MarkdownBriefParser` |
| **JSON** | `application/json` | Cahier des charges structuré | `JSONSpecParser` |
| **YAML** | `application/x-yaml` | Manifest, configuration | `YAMLManifestParser` |
| **Plain Text** | `text/plain` | Brief minimal | `TextBriefParser` |

### 2.3 Schémas d'entrée détaillés

#### 2.3.1 Brief Markdown (`.md`)

```markdown
# Nom du Projet

## Objectif
Description de l'objectif principal du projet.

## Modules
- **Module A** : Description du module A
- **Module B** : Description du module B

## Fonctionnalités
1. Fonctionnalité 1
2. Fonctionnalité 2

## Contraintes
- Contrainte technique 1
- Contrainte métier 1

## Stack technique (optionnel)
- Python 3.11+
- FastAPI
- PostgreSQL
```

**Extraction** :
```typescript
interface ParsedMarkdownBrief {
  project_name: string;           // Extrait du H1
  objective: string;              // Section "Objectif"
  modules: ModuleSpec[];          // Section "Modules"
  features: FeatureSpec[];        // Section "Fonctionnalités"
  constraints: string[];          // Section "Contraintes"
  stack?: TechStack;              // Section "Stack technique"
}
```

#### 2.3.2 Cahier des charges JSON (`.json`)

```json
{
  "$schema": "https://eurkai.io/schemas/project-spec/v1",
  "project": {
    "name": "MonProjet",
    "description": "Description du projet",
    "domain": "e-commerce",
    "version": "1.0.0"
  },
  "modules": [
    {
      "name": "users",
      "type": "crud",
      "entities": ["User", "Role", "Permission"],
      "features": ["authentication", "authorization"]
    },
    {
      "name": "products",
      "type": "crud",
      "entities": ["Product", "Category", "Inventory"],
      "features": ["search", "filtering"]
    }
  ],
  "integrations": [
    {
      "type": "database",
      "provider": "postgresql"
    },
    {
      "type": "cache",
      "provider": "redis"
    }
  ],
  "constraints": {
    "performance": {
      "max_response_time_ms": 200,
      "min_availability": 99.9
    },
    "security": {
      "authentication": "jwt",
      "encryption": "aes-256"
    }
  }
}
```

#### 2.3.3 Manifest YAML (`.yaml`)

```yaml
eurkai:
  version: "1.0"
  type: project

project:
  name: MonProjet
  path: /projects/mon-projet
  inherit_from: ProjectTemplate.Standard

modules:
  - name: core
    type: Module.Infrastructure
    children:
      - name: config
        type: Module.Config
      - name: logging
        type: Module.Logging

  - name: api
    type: Module.API
    children:
      - name: routes
        type: Module.Routes
      - name: middleware
        type: Module.Middleware

scenarios:
  - id: user_registration
    type: Scenario.CRUD
    entity: User
    operations: [create, read, update]

lineage:
  inherit:
    - ProjectTemplate.Standard
    - SecurityMixin.JWT
  inject:
    - LoggingCapability
    - MetricsCapability
```

### 2.4 Validation des entrées

```typescript
interface InputValidationResult {
  valid: boolean;
  format_detected: 'markdown' | 'json' | 'yaml' | 'text' | 'unknown';
  confidence: number;               // 0.0 - 1.0
  errors: ValidationError[];
  warnings: ValidationWarning[];
  normalized_input: NormalizedInput;
}

interface ValidationError {
  code: string;
  message: string;
  location?: string;                // Path dans le document
  suggestion?: string;
}
```

**Règles de validation** :

| Règle | Description | Sévérité |
|-------|-------------|----------|
| `PROJECT_NAME_REQUIRED` | Un nom de projet doit être identifiable | Error |
| `EMPTY_MODULES` | Aucun module détecté | Warning |
| `CIRCULAR_DEPENDENCY` | Dépendance circulaire dans les modules | Error |
| `UNKNOWN_TYPE` | Type d'objet non reconnu dans le catalogue | Warning |
| `INVALID_PATH` | Chemin fractal invalide | Error |

---

## 3. Analyse d'intention

### 3.1 IntentAnalyzer

Le composant `IntentAnalyzer` détermine l'intention de l'utilisateur à partir de l'input normalisé.

```typescript
interface IntentAnalysis {
  primary_intent: Intent;
  confidence: number;
  detected_domain: string;
  detected_scale: ProjectScale;
  detected_patterns: ArchPattern[];
  suggested_templates: TemplateMatch[];
}

enum Intent {
  CREATE_PROJECT = 'create_project',
  ADD_MODULE = 'add_module',
  EXTEND_EXISTING = 'extend_existing',
  MIGRATE_LEGACY = 'migrate_legacy',
  CLONE_TEMPLATE = 'clone_template'
}

enum ProjectScale {
  MICRO = 'micro',           // 1-3 modules
  SMALL = 'small',           // 4-10 modules
  MEDIUM = 'medium',         // 11-30 modules
  LARGE = 'large',           // 31-100 modules
  ENTERPRISE = 'enterprise'  // 100+ modules
}

interface ArchPattern {
  pattern_id: string;
  name: string;
  confidence: number;
  applicable_modules: string[];
}
```

### 3.2 Règles de détection d'intention

```python
# Pseudo-code des règles de détection

INTENT_RULES = [
    {
        "intent": Intent.CREATE_PROJECT,
        "indicators": [
            "contains_project_name",
            "has_modules_section",
            "no_existing_oid_reference"
        ],
        "weight": 1.0
    },
    {
        "intent": Intent.ADD_MODULE,
        "indicators": [
            "references_existing_project",
            "single_module_focus",
            "has_parent_path"
        ],
        "weight": 0.9
    },
    {
        "intent": Intent.EXTEND_EXISTING,
        "indicators": [
            "references_existing_oid",
            "modification_keywords",
            "partial_structure"
        ],
        "weight": 0.8
    },
    {
        "intent": Intent.MIGRATE_LEGACY,
        "indicators": [
            "legacy_format_detected",
            "conversion_keywords",
            "external_source_reference"
        ],
        "weight": 0.7
    }
]
```

### 3.3 Détection de domaine

```typescript
interface DomainDetector {
  detect(input: NormalizedInput): DomainAnalysis;
}

interface DomainAnalysis {
  primary_domain: string;
  sub_domains: string[];
  confidence: number;
  keywords_matched: string[];
}

// Domaines pré-configurés
const DOMAIN_SIGNATURES: Record<string, string[]> = {
  "e-commerce": ["product", "cart", "checkout", "payment", "order", "inventory"],
  "crm": ["customer", "contact", "lead", "opportunity", "pipeline"],
  "cms": ["content", "page", "article", "media", "template", "workflow"],
  "erp": ["resource", "planning", "procurement", "accounting", "hr"],
  "saas": ["tenant", "subscription", "billing", "usage", "plan"],
  "iot": ["device", "sensor", "telemetry", "gateway", "protocol"],
  "analytics": ["metric", "dashboard", "report", "aggregation", "visualization"],
  "ai-ml": ["model", "training", "inference", "dataset", "pipeline"]
};
```

### 3.4 Matching de templates

```typescript
interface TemplateMatch {
  template_id: string;
  template_name: string;
  match_score: number;            // 0.0 - 1.0
  coverage: number;               // % des besoins couverts
  gaps: string[];                 // Éléments non couverts
  extras: string[];               // Éléments en trop
}

// Catalogue de templates (extrait)
const PROJECT_TEMPLATES = {
  "ProjectTemplate.Microservice": {
    modules: ["api", "core", "data", "config"],
    patterns: ["hexagonal", "cqrs"],
    suitable_for: ["small", "medium"]
  },
  "ProjectTemplate.Monolith": {
    modules: ["presentation", "business", "data", "infrastructure"],
    patterns: ["layered", "mvc"],
    suitable_for: ["micro", "small"]
  },
  "ProjectTemplate.EventDriven": {
    modules: ["producers", "consumers", "handlers", "projections"],
    patterns: ["event-sourcing", "saga"],
    suitable_for: ["medium", "large", "enterprise"]
  }
};
```

---

## 4. Pipeline de génération

### 4.1 Architecture GEVR

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GEVR PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐         │
│  │   GET   │───►│ EXECUTE │───►│ VALIDATE │───►│ RENDER  │         │
│  └─────────┘    └─────────┘    └──────────┘    └─────────┘         │
│       │              │               │               │              │
│       ▼              ▼               ▼               ▼              │
│  ParseInput    MapToObjects    CheckCoherence   BuildDiff          │
│  LoadContext   BuildSkeleton   ResolveConflicts ProduceManifest    │
│  FetchCatalog  AssignLineages  ValidateRules    FormatOutput       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 GET — Récupération et parsing

```typescript
interface GetPhase {
  // Entrée
  input: OrchestrateInput;
  
  // Sorties
  parsed_input: NormalizedInput;
  catalog_snapshot: CatalogSnapshot;
  existing_context: ExistingContext | null;
}

class GetPhaseExecutor {
  async execute(input: OrchestrateInput): Promise<GetPhaseResult> {
    // 1. Parser l'input selon son format
    const parsed = await this.parseInput(input);
    
    // 2. Charger le catalogue d'ObjectTypes
    const catalog = await this.loadCatalog();
    
    // 3. Charger le contexte existant si target_path fourni
    const existing = input.context?.target_path 
      ? await this.loadExistingContext(input.context.target_path)
      : null;
    
    return { parsed_input: parsed, catalog_snapshot: catalog, existing_context: existing };
  }
  
  private async parseInput(input: OrchestrateInput): Promise<NormalizedInput> {
    if (input.type === 'text') {
      return this.textParser.parse(input.text!);
    }
    
    if (input.type === 'file') {
      const file = input.files![0];
      const parser = this.getParserForMime(file.mime_type);
      return parser.parse(file.content);
    }
    
    if (input.type === 'mixed') {
      const textPart = this.textParser.parse(input.text!);
      const fileParts = await Promise.all(
        input.files!.map(f => this.getParserForMime(f.mime_type).parse(f.content))
      );
      return this.mergeInputs(textPart, ...fileParts);
    }
    
    throw new Error(`Unknown input type: ${input.type}`);
  }
}
```

### 4.3 EXECUTE — Mapping et construction

#### 4.3.1 ObjectMapper

```typescript
interface ObjectMapping {
  source_element: string;           // Élément dans l'input
  target_type: string;              // Type dans le catalogue
  target_path: string;              // Chemin fractal
  confidence: number;
  mapping_rule: string;             // Règle utilisée
}

class ObjectMapper {
  private catalog: CatalogSnapshot;
  private mappingRules: MappingRule[];
  
  map(parsed: NormalizedInput): ObjectMapping[] {
    const mappings: ObjectMapping[] = [];
    
    // 1. Mapper le projet racine
    mappings.push(this.mapProject(parsed.project));
    
    // 2. Mapper les modules
    for (const module of parsed.modules) {
      mappings.push(...this.mapModule(module, parsed.project.path));
    }
    
    // 3. Mapper les entités
    for (const entity of parsed.entities) {
      mappings.push(this.mapEntity(entity));
    }
    
    // 4. Mapper les scénarios
    for (const scenario of parsed.scenarios) {
      mappings.push(this.mapScenario(scenario));
    }
    
    return mappings;
  }
  
  private mapProject(project: ProjectSpec): ObjectMapping {
    return {
      source_element: project.name,
      target_type: this.resolveProjectType(project),
      target_path: project.path || `/projects/${slugify(project.name)}`,
      confidence: 1.0,
      mapping_rule: 'PROJECT_ROOT'
    };
  }
  
  private mapModule(module: ModuleSpec, parentPath: string): ObjectMapping[] {
    const mappings: ObjectMapping[] = [];
    const moduleType = this.resolveModuleType(module);
    const modulePath = `${parentPath}/modules/${slugify(module.name)}`;
    
    // Module principal
    mappings.push({
      source_element: module.name,
      target_type: moduleType,
      target_path: modulePath,
      confidence: this.computeConfidence(module, moduleType),
      mapping_rule: 'MODULE_INFERENCE'
    });
    
    // Sous-modules récursifs
    if (module.children) {
      for (const child of module.children) {
        mappings.push(...this.mapModule(child, modulePath));
      }
    }
    
    return mappings;
  }
  
  private resolveModuleType(module: ModuleSpec): string {
    // Règles de résolution basées sur le nom et les features
    const typeMap: Record<string, string> = {
      'api': 'Module.API',
      'core': 'Module.Core',
      'data': 'Module.Data',
      'config': 'Module.Config',
      'auth': 'Module.Authentication',
      'users': 'Module.CRUD',
      'products': 'Module.CRUD',
      // ...
    };
    
    return typeMap[module.name.toLowerCase()] 
      || typeMap[module.type] 
      || 'Module.Generic';
  }
}
```

#### 4.3.2 SkeletonBuilder

```typescript
interface ProjectSkeleton {
  root: SkeletonNode;
  total_objects: number;
  depth: number;
  lineages: LineageSpec[];
  relations: RelationSpec[];
}

interface SkeletonNode {
  id: string;                       // ID temporaire (sera remplacé par OID)
  type: string;
  path: string;
  name: string;
  bundles: {
    attributes: Record<string, any>;
    methods: Record<string, any>;
    rules: Record<string, any>;
    relations: Record<string, any>;
  };
  children: SkeletonNode[];
  lineage: string[];                // Types parents
  injections: string[];             // Mixins/Traits injectés
  tags: string[];
}

class SkeletonBuilder {
  build(
    mappings: ObjectMapping[], 
    intent: IntentAnalysis,
    catalog: CatalogSnapshot
  ): ProjectSkeleton {
    
    // 1. Construire l'arbre de nœuds
    const root = this.buildTree(mappings);
    
    // 2. Résoudre les lineages
    const lineages = this.resolveLineages(root, catalog);
    
    // 3. Appliquer les templates de bundles
    this.applyBundleTemplates(root, catalog);
    
    // 4. Générer les relations
    const relations = this.generateRelations(root);
    
    // 5. Appliquer les injections suggérées
    this.applyInjections(root, intent.detected_patterns);
    
    return {
      root,
      total_objects: this.countNodes(root),
      depth: this.computeDepth(root),
      lineages,
      relations
    };
  }
  
  private buildTree(mappings: ObjectMapping[]): SkeletonNode {
    // Construire un arbre à partir des paths
    const nodes = new Map<string, SkeletonNode>();
    
    for (const mapping of mappings) {
      const node: SkeletonNode = {
        id: generateTempId(),
        type: mapping.target_type,
        path: mapping.target_path,
        name: this.extractName(mapping.target_path),
        bundles: { attributes: {}, methods: {}, rules: {}, relations: {} },
        children: [],
        lineage: [],
        injections: [],
        tags: []
      };
      nodes.set(mapping.target_path, node);
    }
    
    // Établir les relations parent-enfant
    for (const [path, node] of nodes) {
      const parentPath = this.getParentPath(path);
      if (parentPath && nodes.has(parentPath)) {
        nodes.get(parentPath)!.children.push(node);
      }
    }
    
    // Retourner la racine
    return nodes.get(mappings[0].target_path)!;
  }
  
  private resolveLineages(node: SkeletonNode, catalog: CatalogSnapshot): LineageSpec[] {
    const lineages: LineageSpec[] = [];
    
    // Récupérer le lineage standard pour ce type
    const typeInfo = catalog.types[node.type];
    if (typeInfo) {
      node.lineage = typeInfo.default_lineage;
      lineages.push({
        object_path: node.path,
        lineage_chain: typeInfo.default_lineage
      });
    }
    
    // Récursion sur les enfants
    for (const child of node.children) {
      lineages.push(...this.resolveLineages(child, catalog));
    }
    
    return lineages;
  }
  
  private applyBundleTemplates(node: SkeletonNode, catalog: CatalogSnapshot): void {
    const typeInfo = catalog.types[node.type];
    if (!typeInfo) return;
    
    // Appliquer les attributs par défaut
    node.bundles.attributes = {
      ...typeInfo.default_attributes,
      name: node.name,
      path: node.path,
      created_at: new Date().toISOString(),
      status: 'draft'
    };
    
    // Appliquer les méthodes standards
    node.bundles.methods = { ...typeInfo.default_methods };
    
    // Appliquer les règles par défaut
    node.bundles.rules = { ...typeInfo.default_rules };
    
    // Récursion
    for (const child of node.children) {
      this.applyBundleTemplates(child, catalog);
    }
  }
}
```

### 4.4 VALIDATE — Cohérence et résolution

```typescript
interface ValidationResult {
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  auto_fixes: AutoFix[];
}

interface ValidationIssue {
  code: string;
  severity: 'error' | 'warning' | 'info';
  path: string;
  message: string;
  context: Record<string, any>;
}

interface AutoFix {
  issue_code: string;
  fix_type: 'rename' | 'retype' | 'add_relation' | 'remove_duplicate';
  original: any;
  fixed: any;
  applied: boolean;
}

class SkeletonValidator {
  validate(skeleton: ProjectSkeleton, catalog: CatalogSnapshot): ValidationResult {
    const errors: ValidationIssue[] = [];
    const warnings: ValidationIssue[] = [];
    const autoFixes: AutoFix[] = [];
    
    // 1. Valider l'unicité des paths
    this.validatePathUniqueness(skeleton.root, errors);
    
    // 2. Valider les types contre le catalogue
    this.validateTypes(skeleton.root, catalog, errors, warnings);
    
    // 3. Valider les lineages
    this.validateLineages(skeleton.lineages, catalog, errors);
    
    // 4. Valider les relations
    this.validateRelations(skeleton.relations, skeleton.root, errors, warnings);
    
    // 5. Vérifier les dépendances circulaires
    this.checkCircularDependencies(skeleton.root, errors);
    
    // 6. Appliquer les auto-fixes si possible
    this.applyAutoFixes(errors, warnings, autoFixes);
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
      auto_fixes: autoFixes
    };
  }
  
  private validateTypes(
    node: SkeletonNode, 
    catalog: CatalogSnapshot,
    errors: ValidationIssue[],
    warnings: ValidationIssue[]
  ): void {
    if (!catalog.types[node.type]) {
      // Type inconnu - warning avec suggestion
      const suggestion = this.findClosestType(node.type, catalog);
      warnings.push({
        code: 'UNKNOWN_TYPE',
        severity: 'warning',
        path: node.path,
        message: `Type '${node.type}' not found in catalog`,
        context: { suggested: suggestion }
      });
    }
    
    for (const child of node.children) {
      this.validateTypes(child, catalog, errors, warnings);
    }
  }
  
  private checkCircularDependencies(root: SkeletonNode, errors: ValidationIssue[]): void {
    const visited = new Set<string>();
    const recursionStack = new Set<string>();
    
    const dfs = (node: SkeletonNode): boolean => {
      visited.add(node.path);
      recursionStack.add(node.path);
      
      for (const child of node.children) {
        if (!visited.has(child.path)) {
          if (dfs(child)) return true;
        } else if (recursionStack.has(child.path)) {
          errors.push({
            code: 'CIRCULAR_DEPENDENCY',
            severity: 'error',
            path: node.path,
            message: `Circular dependency detected: ${node.path} -> ${child.path}`,
            context: { cycle: [node.path, child.path] }
          });
          return true;
        }
      }
      
      recursionStack.delete(node.path);
      return false;
    };
    
    dfs(root);
  }
}
```

### 4.5 RENDER — Production du FractalDiff

```typescript
class DiffRenderer {
  render(
    skeleton: ProjectSkeleton,
    validation: ValidationResult,
    scenario_id: string
  ): FractalDiff {
    
    const changes: ObjectDiff[] = [];
    
    // Convertir chaque nœud du squelette en ObjectDiff
    this.renderNode(skeleton.root, changes);
    
    // Créer le FractalDiff (compatible H3)
    return {
      diff_id: generateUUID(),
      scenario_id: scenario_id,
      scenario_label: 'Génération de Projet EURKAI',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: 'pending',
      changes: changes,
      summary: this.computeSummary(changes)
    };
  }
  
  private renderNode(node: SkeletonNode, changes: ObjectDiff[]): void {
    // Créer l'ObjectDiff pour ce nœud
    const objectDiff: ObjectDiff = {
      diff_item_id: generateUUID(),
      object_id: node.id,               // ID temporaire
      object_type: node.type,
      object_path: node.path,
      object_label: node.name,
      operation: 'create',              // Toujours création pour I1
      
      // Bundles comme BundleDiff
      attributes: this.bundleToDiff(node.bundles.attributes, 'attributes'),
      methods: this.bundleToDiff(node.bundles.methods, 'methods'),
      rules: this.bundleToDiff(node.bundles.rules, 'rules'),
      relations: this.bundleToDiff(node.bundles.relations, 'relations'),
      tags: {
        added: node.tags,
        removed: []
      },
      
      // État initial
      decision: 'pending',
      user_override: null,
      decision_comment: null,
      decision_timestamp: null,
      decision_user_id: null
    };
    
    changes.push(objectDiff);
    
    // Récursion sur les enfants
    for (const child of node.children) {
      this.renderNode(child, changes);
    }
  }
  
  private bundleToDiff(
    bundle: Record<string, any>, 
    bundleType: string
  ): BundleDiff {
    const fields: FieldDiff[] = [];
    
    for (const [key, value] of Object.entries(bundle)) {
      fields.push({
        field_name: key,
        old_value: null,              // Création = pas de valeur précédente
        new_value: value,
        change_type: 'added'
      });
    }
    
    return {
      bundle_type: bundleType,
      fields: fields
    };
  }
  
  private computeSummary(changes: ObjectDiff[]): DiffSummary {
    return {
      total_changes: changes.length,
      creates: changes.length,        // Tout est création dans I1
      updates: 0,
      deletes: 0,
      disables: 0,
      pending: changes.length,
      accepted: 0,
      rejected: 0,
      modified: 0
    };
  }
}
```

---

## 5. Manifest Projet

### 5.1 Structure du ProjectManifest

```typescript
interface ProjectManifest {
  // Métadonnées
  eurkai_version: string;
  manifest_version: string;
  generated_at: string;
  generator: 'I1.ProjectGenerator';
  
  // Identification
  project: {
    id: string;                     // UUID
    name: string;
    slug: string;
    description: string;
    path: string;
    version: string;
  };
  
  // Structure
  structure: {
    total_objects: number;
    max_depth: number;
    modules: ManifestModule[];
    scenarios: ManifestScenario[];
  };
  
  // Lineage
  lineage: {
    inherit_from: string[];
    injections: string[];
    overrides: ManifestOverride[];
  };
  
  // Configuration
  config: {
    domain: string;
    template_used: string | null;
    patterns: string[];
    tags: string[];
  };
  
  // Références
  references: {
    diff_id: string;                // Lien vers FractalDiff
    catalog_version: string;
    source_hash: string;            // Hash de l'input
  };
  
  // Validation
  validation: {
    status: 'valid' | 'warnings' | 'errors';
    issues_count: number;
    last_validated: string;
  };
}

interface ManifestModule {
  name: string;
  type: string;
  path: string;
  children_count: number;
  features: string[];
}

interface ManifestScenario {
  id: string;
  name: string;
  type: string;
  triggers: string[];
}

interface ManifestOverride {
  target_path: string;
  attribute: string;
  original_type: string;
  override_value: any;
}
```

### 5.2 Génération du manifest

```typescript
class ManifestGenerator {
  generate(
    skeleton: ProjectSkeleton,
    validation: ValidationResult,
    diff: FractalDiff,
    intent: IntentAnalysis,
    input: NormalizedInput
  ): ProjectManifest {
    
    return {
      eurkai_version: '1.0',
      manifest_version: '1.0',
      generated_at: new Date().toISOString(),
      generator: 'I1.ProjectGenerator',
      
      project: {
        id: generateUUID(),
        name: input.project.name,
        slug: slugify(input.project.name),
        description: input.project.description || '',
        path: skeleton.root.path,
        version: '0.1.0'
      },
      
      structure: {
        total_objects: skeleton.total_objects,
        max_depth: skeleton.depth,
        modules: this.extractModules(skeleton.root),
        scenarios: this.extractScenarios(input)
      },
      
      lineage: {
        inherit_from: skeleton.root.lineage,
        injections: skeleton.root.injections,
        overrides: this.extractOverrides(skeleton)
      },
      
      config: {
        domain: intent.detected_domain,
        template_used: intent.suggested_templates[0]?.template_id || null,
        patterns: intent.detected_patterns.map(p => p.pattern_id),
        tags: this.generateTags(input, intent)
      },
      
      references: {
        diff_id: diff.diff_id,
        catalog_version: this.getCatalogVersion(),
        source_hash: this.hashInput(input)
      },
      
      validation: {
        status: validation.valid 
          ? 'valid' 
          : (validation.errors.length > 0 ? 'errors' : 'warnings'),
        issues_count: validation.errors.length + validation.warnings.length,
        last_validated: new Date().toISOString()
      }
    };
  }
  
  private extractModules(node: SkeletonNode): ManifestModule[] {
    const modules: ManifestModule[] = [];
    
    if (node.type.startsWith('Module.')) {
      modules.push({
        name: node.name,
        type: node.type,
        path: node.path,
        children_count: node.children.length,
        features: this.extractFeatures(node)
      });
    }
    
    for (const child of node.children) {
      modules.push(...this.extractModules(child));
    }
    
    return modules;
  }
}
```

### 5.3 Format de sortie YAML

```yaml
# Exemple de ProjectManifest généré

eurkai_version: "1.0"
manifest_version: "1.0"
generated_at: "2025-12-01T14:30:00Z"
generator: "I1.ProjectGenerator"

project:
  id: "proj_a1b2c3d4"
  name: "Dashboard Analytics"
  slug: "dashboard-analytics"
  description: "Application de dashboard avec 3 modules"
  path: "/projects/dashboard-analytics"
  version: "0.1.0"

structure:
  total_objects: 12
  max_depth: 3
  modules:
    - name: "users"
      type: "Module.CRUD"
      path: "/projects/dashboard-analytics/modules/users"
      children_count: 3
      features: ["authentication", "authorization"]
    - name: "metrics"
      type: "Module.Analytics"
      path: "/projects/dashboard-analytics/modules/metrics"
      children_count: 2
      features: ["aggregation", "visualization"]
    - name: "reports"
      type: "Module.Reporting"
      path: "/projects/dashboard-analytics/modules/reports"
      children_count: 2
      features: ["export", "scheduling"]
  scenarios:
    - id: "scn_user_crud"
      name: "User CRUD Operations"
      type: "Scenario.CRUD"
      triggers: ["api.users.*"]

lineage:
  inherit_from:
    - "ProjectTemplate.Standard"
    - "Project"
    - "FractalObject"
  injections:
    - "LoggingCapability"
    - "MetricsCapability"
  overrides: []

config:
  domain: "analytics"
  template_used: "ProjectTemplate.Standard"
  patterns:
    - "layered"
    - "crud"
  tags:
    - "dashboard"
    - "analytics"
    - "generated"

references:
  diff_id: "diff_x1y2z3"
  catalog_version: "2025.12.01"
  source_hash: "sha256:abc123..."

validation:
  status: "valid"
  issues_count: 0
  last_validated: "2025-12-01T14:30:00Z"
```

---

## 6. Intégration avec H2/H3

### 6.1 Point d'entrée : Super.orchestrate

```typescript
// Extension du ScenarioMatcher (H2) pour reconnaître I1

const I1_SCENARIO: ScenarioDefinition = {
  id: 'scn_project_create',
  name: 'Création de Projet EURKAI',
  description: 'Génère une structure projet complète depuis un brief',
  
  // Conditions de matching
  match_conditions: [
    { type: 'keyword', values: ['projet', 'project', 'créer', 'create', 'nouveau', 'new'] },
    { type: 'structure', has: ['modules', 'features', 'objectif'] },
    { type: 'file_type', accepts: ['markdown', 'json', 'yaml'] }
  ],
  
  // Handler
  handler: 'I1.ProjectGenerator',
  
  // Configuration
  config: {
    dry_run_default: true,
    require_validation: true,
    output_format: 'fractal_diff'
  }
};
```

### 6.2 Réponse compatible H2

```typescript
// La réponse I1 s'intègre dans OrchestrateResponse (H2)

interface I1OrchestrateResponse extends OrchestrateResponse {
  request_id: string;
  status: 'success' | 'partial' | 'error';
  
  scenario: {
    id: 'scn_project_create';
    name: 'Création de Projet EURKAI';
    description: string;
    confidence: number;
    parameters_detected: {
      project_name: string;
      modules: string[];
      domain: string;
      template: string | null;
    };
  };
  
  suggestions: Suggestion[];
  
  // FractalDiff compatible H3
  fractal_diff: FractalDiff;
  
  // Extension I1 : Manifest
  project_manifest: ProjectManifest;
  
  logs: LogEntry[];
  timestamp: string;
}
```

### 6.3 Handoff vers H3 (DiffService)

```typescript
// Après génération, le diff est transmis à H3 pour validation

class I1ToH3Bridge {
  async handoff(
    response: I1OrchestrateResponse,
    session_id: string
  ): Promise<string> {
    
    // 1. Enregistrer le diff dans le DiffService (H3)
    const diffService = new DiffService();
    
    // Le diff est déjà au format FractalDiff compatible
    const registeredDiff = await diffService.registerDiff(
      response.fractal_diff,
      {
        source: 'I1.ProjectGenerator',
        session_id: session_id,
        manifest: response.project_manifest
      }
    );
    
    // 2. Créer l'entrée historique (H2)
    await this.createHistoryEntry(response, session_id, registeredDiff.diff_id);
    
    return registeredDiff.diff_id;
  }
}
```

### 6.4 Diagramme de séquence complet

```
┌─────────┐     ┌────────────────┐     ┌────────────────┐     ┌───────────┐
│ Cockpit │     │ Super.orchestrate │  │ I1.Generator   │     │ H3.Diff   │
└────┬────┘     └───────┬────────┘     └───────┬────────┘     └─────┬─────┘
     │                  │                      │                    │
     │ POST /orchestrate                       │                    │
     │ {input, session_id}                     │                    │
     │─────────────────>│                      │                    │
     │                  │                      │                    │
     │                  │ match_scenario()     │                    │
     │                  │─────────────────────>│                    │
     │                  │                      │                    │
     │                  │ execute_generator()  │                    │
     │                  │─────────────────────>│                    │
     │                  │                      │ GET: parse, load   │
     │                  │                      │────────┐           │
     │                  │                      │<───────┘           │
     │                  │                      │                    │
     │                  │                      │ EXECUTE: map, build│
     │                  │                      │────────┐           │
     │                  │                      │<───────┘           │
     │                  │                      │                    │
     │                  │                      │ VALIDATE: check    │
     │                  │                      │────────┐           │
     │                  │                      │<───────┘           │
     │                  │                      │                    │
     │                  │                      │ RENDER: diff+manifest
     │                  │                      │────────┐           │
     │                  │                      │<───────┘           │
     │                  │                      │                    │
     │                  │ FractalDiff          │                    │
     │                  │<─────────────────────│                    │
     │                  │                      │                    │
     │                  │ register_diff()      │                    │
     │                  │──────────────────────────────────────────>│
     │                  │                      │                    │
     │                  │ diff_id              │                    │
     │                  │<──────────────────────────────────────────│
     │                  │                      │                    │
     │ OrchestrateResponse                     │                    │
     │ {fractal_diff, manifest}                │                    │
     │<─────────────────│                      │                    │
     │                  │                      │                    │
     │ [User reviews diff in Cockpit]          │                    │
     │                  │                      │                    │
     │ POST /apply      │                      │                    │
     │─────────────────────────────────────────────────────────────>│
     │                  │                      │                    │
     │ DiffOperationResult                     │                    │
     │<─────────────────────────────────────────────────────────────│
```

---

## 7. Scénarios de test

### 7.1 Test : Brief textuel minimal

**Input** :
```json
{
  "input": {
    "type": "text",
    "text": "Créer un projet CRM avec les modules: contacts, opportunités, rapports"
  },
  "session_id": "test_001"
}
```

**Expected Output** :
```json
{
  "status": "success",
  "scenario": {
    "id": "scn_project_create",
    "confidence": 0.85,
    "parameters_detected": {
      "project_name": "CRM",
      "modules": ["contacts", "opportunités", "rapports"],
      "domain": "crm"
    }
  },
  "fractal_diff": {
    "changes": [
      { "operation": "create", "object_type": "Project", "object_path": "/projects/crm" },
      { "operation": "create", "object_type": "Module.CRUD", "object_path": "/projects/crm/modules/contacts" },
      { "operation": "create", "object_type": "Module.CRUD", "object_path": "/projects/crm/modules/opportunites" },
      { "operation": "create", "object_type": "Module.Reporting", "object_path": "/projects/crm/modules/rapports" }
    ],
    "summary": { "total_changes": 4, "creates": 4 }
  }
}
```

### 7.2 Test : Brief Markdown complet

**Input** : Fichier `brief.md`
```markdown
# E-Commerce Platform

## Objectif
Plateforme de vente en ligne B2C

## Modules
- **Catalogue** : Gestion des produits et catégories
- **Panier** : Gestion du panier d'achat
- **Checkout** : Processus de commande
- **Paiement** : Intégration Stripe

## Contraintes
- Temps de réponse < 200ms
- Disponibilité 99.9%
```

**Expected** :
- 5 ObjectDiff (1 projet + 4 modules)
- Domain détecté : "e-commerce"
- Template suggéré : "ProjectTemplate.Microservice"
- Patterns : ["crud", "layered"]

### 7.3 Test : Cahier des charges JSON

**Input** : Fichier `spec.json` (voir section 2.3.2)

**Expected** :
- Parsing complet des modules
- Résolution des types depuis le catalogue
- Génération des bundles avec contraintes
- Manifest avec intégrations référencées

### 7.4 Test : Erreur - Input invalide

**Input** :
```json
{
  "input": {
    "type": "text",
    "text": ""
  },
  "session_id": "test_err"
}
```

**Expected** :
```json
{
  "status": "error",
  "scenario": null,
  "fractal_diff": null,
  "logs": [
    {
      "level": "error",
      "source": "InputParser",
      "message": "Empty input provided"
    }
  ]
}
```

### 7.5 Matrice de couverture

| Scénario | Input Type | Modules | Validation | Résultat attendu |
|----------|------------|---------|------------|------------------|
| Minimal text | text | 1-3 | ✓ | Success |
| Full markdown | file.md | 4-10 | ✓ | Success |
| Complex JSON | file.json | 10+ | ✓ | Success |
| YAML manifest | file.yaml | Any | ✓ | Success |
| Mixed input | mixed | Any | ✓ | Success |
| Empty input | text | 0 | ✗ | Error |
| Invalid type | file.pdf | - | ✗ | Error |
| Circular deps | json | 3+ | ✗ | Error |
| Unknown types | json | 5 | ⚠ | Warnings |

---

## 8. Annexes

### 8.1 Catalogue d'ObjectTypes (extrait)

```yaml
types:
  Project:
    lineage: ["FractalObject"]
    default_attributes:
      name: { type: string, required: true }
      description: { type: string }
      status: { type: enum, values: [draft, active, archived] }
      version: { type: semver }
    default_methods:
      initialize: { signature: "() -> void" }
      validate: { signature: "() -> ValidationResult" }
    default_rules:
      - rule_id: "project.name.unique"
        erk: "UNIQUE($.name)"

  Module.CRUD:
    lineage: ["Module", "FractalObject"]
    default_attributes:
      entity_name: { type: string, required: true }
      operations: { type: array, items: enum[create, read, update, delete] }
    default_methods:
      create: { signature: "(data: T) -> T" }
      read: { signature: "(id: string) -> T | null" }
      update: { signature: "(id: string, data: Partial<T>) -> T" }
      delete: { signature: "(id: string) -> boolean" }

  Module.API:
    lineage: ["Module", "FractalObject"]
    default_attributes:
      base_path: { type: string }
      version: { type: string }
      auth_required: { type: boolean, default: true }
    default_methods:
      handle_request: { signature: "(req: Request) -> Response" }
      validate_auth: { signature: "(token: string) -> boolean" }

  Module.Analytics:
    lineage: ["Module", "FractalObject"]
    default_attributes:
      metrics: { type: array }
      aggregations: { type: array }
    default_methods:
      compute: { signature: "(query: Query) -> Result" }
      aggregate: { signature: "(data: Data[], fn: AggFn) -> Aggregate" }
```

### 8.2 Règles de mapping

```yaml
mapping_rules:
  - id: "MODULE_BY_NAME"
    description: "Infère le type de module depuis son nom"
    patterns:
      - pattern: "user|users|auth|account"
        target_type: "Module.CRUD"
        features: ["authentication"]
      - pattern: "product|catalog|inventory"
        target_type: "Module.CRUD"
        features: ["search", "filtering"]
      - pattern: "report|analytics|dashboard"
        target_type: "Module.Analytics"
        features: ["aggregation", "visualization"]
      - pattern: "api|gateway|routes"
        target_type: "Module.API"
        features: ["routing", "middleware"]
      - pattern: "config|settings"
        target_type: "Module.Config"
        features: ["environment", "secrets"]

  - id: "MODULE_BY_TYPE_HINT"
    description: "Utilise le type explicite fourni"
    priority: 1
    condition: "module.type != null"
    action: "use module.type as target_type"

  - id: "DEFAULT_MODULE"
    description: "Type par défaut si aucune règle ne matche"
    priority: 100
    target_type: "Module.Generic"
```

### 8.3 Glossaire

| Terme | Définition |
|-------|------------|
| **Brief** | Document textuel décrivant un projet de manière informelle |
| **Cahier des charges** | Spécification structurée (JSON/YAML) |
| **FractalDiff** | Structure de diff compatible H3 pour validation |
| **Lineage** | Chaîne d'héritage d'un objet fractal |
| **Manifest** | Document de référence décrivant un projet généré |
| **ObjectDiff** | Diff unitaire sur un objet fractal |
| **Skeleton** | Structure intermédiaire avant génération du diff |
| **GEVR** | Pattern Get-Execute-Validate-Render |
| **IVC×DRO** | Identity-View-Context × Definition-Rule-Option |

### 8.4 Références

- **H1** : Cockpit SuperTools (lecture seule)
- **H2** : Spécification Super.orchestrate
- **H3** : Cockpit Diff & Validation
- **Catalogue EURKAI** : `/system/catalog/types`
- **Templates** : `/system/templates/projects`

---

## Fin du document I1

**Prochaines étapes** :
- I2 : Import de structures existantes (legacy migration)
- I3 : Clonage et versioning de projets
