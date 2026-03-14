# SPECS — Design Capability Layer (DCL)

> Couche plateforme au-dessus du Visual Identity Engine
> Version : draft 1.0 | Date : 2026-03-14
> Scope : EURKAI Platform — à migrer vers EURKAI/MODULES/design_platform/ en Phase 5

---

## Préambule — Pourquoi cette couche

Le Visual Identity Engine (VIE, `theme_generator v3`) est un moteur.
Il sait résoudre un ThemeDNA en ThemeTokens. Il ne sait pas ce qu'on veut en faire.

La **Design Capability Layer (DCL)** est la couche produit au-dessus.
Elle répond à : *quoi faire, avec quoi, pour qui, sous quelle forme commerciale.*

Sans DCL, le VIE reste un composant interne.
Avec DCL, il devient une plateforme qui peut produire :
- des API vendables
- des workflows one-click
- des SaaS complets en quelques recettes

La séparation est stricte et intentionnelle :
- **VIE** = analyse, résolution, mutation, composition, rendu — le moteur ne connaît pas les produits
- **DCL** = capabilities, endpoints, workflows, recipes — la couche produit ne réimplémente pas le moteur

---

## 1. Architecture complète

```
INPUT
  image | URL | logo | brief | mockup | moodboard | preset | assets existants
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VISUAL IDENTITY ENGINE (VIE)                             │
│                                                                             │
│  StyleAnalyzer                                                              │
│  └─ analyse entrées brutes → BrandDNA / ThemeDNA                           │
│         ↓                                                                   │
│  ThemeInterpreter  →  normalise + enrichit + extrait contraintes            │
│         ↓                                                                   │
│  CandidateSelector →  interroge bibliothèques → CandidateSets              │
│         ↓                                                                   │
│  CompatibilityEngine → filtre + budgets + scoring                          │
│         ↓                                                                   │
│  ThemeResolver     →  cohérence famille + sélection finale                  │
│         ↓                                                                   │
│  MutationEngine    →  mutate / evolve / refresh / adapt                     │
│         ↓                                                                   │
│  ThemeComposer     →  assemble ThemeTokens + variants                       │
│         ↓                                                                   │
│  Renderer          →  CSS | SCSS | JSON | Print | Brand                     │
│                                                                             │
│  Bibliothèques : border · shape · texture · ornament · typography           │
│                  icon · layout · motion · palette · families                │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ VIE API (interne, typée)
┌───────────────────────────────▼─────────────────────────────────────────────┐
│                  DESIGN CAPABILITY LAYER (DCL)                              │
│                                                                             │
│  capabilities/    — opérations atomiques (wrappent le VIE)                  │
│  endpoints/       — exposition REST des capabilities et workflows            │
│  workflows/       — orchestration multi-steps                               │
│  recipes/         — produits SaaS configurés sur des workflows               │
│  schemas/         — contrats input/output (JSON Schema)                     │
│  artifacts/       — artefacts standardisés produits et consommés            │
│  execution_trace/ — traçabilité complète de chaque exécution                │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
            ┌───────────────────┼────────────────────┐
            ▼                   ▼                    ▼
      API REST             Workflows            Produits SaaS
      /design/*          one-click           recipes packagées
```

---

## 2. Rôles des sous-couches DCL

| Sous-couche | Rôle | Analogie |
|---|---|---|
| `capabilities` | Opérations atomiques. Chaque capability = une fonction design bien définie. Wrappent le VIE. | Primitives d'un SDK |
| `endpoints` | Exposition HTTP des capabilities et workflows. Gèrent auth, validation, versioning. | Routes d'une API publique |
| `workflows` | Orchestration de plusieurs capabilities en séquence. Gèrent état, erreurs, parallélisme. | Pipelines métier |
| `recipes` | Configuration commerciale d'un workflow. Définissent le produit vendable. | Produits sur une marketplace |
| `schemas` | Contrats d'entrée/sortie JSON Schema pour chaque capability, endpoint, workflow. | OpenAPI specs |
| `artifacts` | Types de sorties standardisés qui circulent entre capabilities. Versionnés, sérialisables. | Data transfer objects |
| `execution_trace` | Enregistrement complet de chaque exécution — auditabilité, debug, replay. | Audit log structuré |

---

## 3. Modèles de données

### 3.1 DesignCapability

```python
@dataclass
class DesignCapability:
    id: str                      # snake_case, unique — ex: "extract_brand_dna"
    category: str                # "analysis" | "generation" | "mutation" |
                                 # "reverse" | "harmonization" | "render"
    subcategory: str             # ex: "palette" | "typography" | "layout"
    name: str
    description: str

    input_schema: dict           # JSON Schema — artefacts et params attendus
    output_artifacts: List[str]  # types d'artefacts produits ex: ["BrandDNA", "DecisionTrace"]

    engine_modules: List[str]    # modules VIE appelés ex: ["StyleAnalyzer", "ThemeResolver"]
    requires_ai: bool            # nécessite un appel IA externe (vision, LLM)
    cacheable: bool              # le résultat peut-il être mis en cache ?
    async_supported: bool        # peut s'exécuter en tâche de fond
    estimated_duration_ms: int   # estimation P50

    tags: List[str]              # tags libres pour découverte, matching, filtrage
    version: str                 # "1.0.0"
    deprecated: bool
    replaces: Optional[str]      # id d'une capability remplacée
```

### 3.2 DesignEndpointSpec

```python
@dataclass
class DesignEndpointSpec:
    method: str                  # "POST" | "GET" | "PATCH"
    path: str                    # ex: "/v1/design/extract-brand-dna"
    api_version: str             # "v1"
    capability_id: Optional[str]
    workflow_id: Optional[str]

    request_schema: dict         # JSON Schema du body
    response_schema: dict        # JSON Schema de la réponse
    error_codes: List[ErrorSpec]

    auth_required: bool
    rate_limit: Optional[str]    # ex: "60/min" | "1000/day"
    async_mode: bool             # si True → retourne job_id + polling ou webhook
    webhook_support: bool
    idempotent: bool

    tags: List[str]              # groupement OpenAPI
    changelog: List[str]         # historique des modifications

@dataclass
class ErrorSpec:
    code: int
    reason: str
    description: str
```

### 3.3 WorkflowStep

```python
@dataclass
class WorkflowStep:
    step_id: str
    capability_id: str
    name: str

    input_mapping: dict          # JSONPath vers contexte workflow
                                 # ex: {"image": "$.inputs.logo_url"}
    output_key: str              # clé dans le contexte partagé du workflow

    optional: bool               # si True et erreur → continue sans ce step
    fallback_capability: Optional[str]
    parallel_with: List[str]     # step_ids exécutables en parallèle
    condition: Optional[str]     # expression d'activation ex: "$.context.has_logo == true"
    timeout_ms: Optional[int]
```

### 3.4 DesignWorkflow

```python
@dataclass
class DesignWorkflow:
    id: str                      # snake_case — ex: "reverse_brand_from_site"
    category: str                # "reverse" | "generation" | "evolution" |
                                 # "design_system" | "event" | "white_label"
    name: str
    description: str
    use_case: str                # description business en 1 phrase

    steps: List[WorkflowStep]
    input_schema: dict           # JSON Schema des inputs utilisateur
    output_artifacts: List[str]  # artefacts produits par le workflow

    async_supported: bool
    estimated_duration_s: int
    engine_dependencies: List[str]  # modules VIE nécessaires
    capability_dependencies: List[str]

    tags: List[str]
    version: str
```

### 3.5 DesignRecipe

```python
@dataclass
class DesignRecipe:
    id: str                       # ex: "brand_reverse_audit"
    use_case: str                 # description business courte
    target_audience: str          # ex: "agences web, freelances, startups"
    problem_solved: str           # le vrai problème résolu

    workflow_id: str
    input_schema: dict            # simplifié vs workflow — vision utilisateur final
    output_artifacts: List[str]

    execution_mode: str           # "sync" | "async" | "batch"
    automation_level: str         # "full" | "supervised" | "assisted"
    customization_level: str      # "none" | "low" | "medium" | "high"

    packaging: RecipePackaging
    example_inputs: dict
    example_outputs: List[str]
    demo_available: bool
    tags: List[str]

@dataclass
class RecipePackaging:
    product_name: str
    tagline: str
    pricing_model: str            # "per_generation" | "subscription" |
                                  # "credits" | "white_label" | "enterprise"
    price_indication: str         # ex: "5€/génération" | "49€/mois"
    delivery_format: str          # "api" | "webapp" | "saas" | "embedded" | "download"
    time_to_value: str            # ex: "< 30 secondes"
    differentiator: str           # pourquoi c'est meilleur qu'une alternative
```

### 3.6 DesignArtifact

```python
@dataclass
class DesignArtifact:
    artifact_id: str             # UUID
    type: str                    # depuis la taxonomie (section 8)
    subtype: Optional[str]
    format: str                  # "json" | "css" | "scss" | "html" | "zip" | "pdf" | "svg"
    target: List[str]            # ["web"] | ["app"] | ["print"] | ["figma"]

    content: Any                 # données brutes ou chemin fichier
    size_bytes: Optional[int]
    checksum: Optional[str]

    source_capability: str       # capability_id qui a produit cet artefact
    source_trace_id: str         # lien vers DesignExecutionTrace
    created_at: str
    expires_at: Optional[str]
    metadata: dict               # champs libres selon le type
```

### 3.7 DesignExecutionTrace

```python
@dataclass
class DesignExecutionTrace:
    trace_id: str                # UUID
    timestamp: str
    trigger: str                 # "capability" | "workflow" | "recipe" | "api" | "agent"
    trigger_id: str              # id de ce qui a déclenché l'exécution
    recipe_id: Optional[str]
    workflow_id: Optional[str]

    input_summary: dict          # résumé des inputs (sans données sensibles)
    input_hash: str              # hash pour déduplication / cache

    steps: List[ExecutionStep]
    artifacts_generated: List[DesignArtifact]

    scores: dict                 # ex: {"coherence": 0.82, "accessibility": 0.95}
    budgets: dict                # BudgetState du VIE
    mutations_applied: List[str] # ids des mutations appliquées

    warnings: List[str]
    errors: List[ExecutionError]

    duration_ms: int
    engine_version: str          # version du VIE utilisé
    dcl_version: str             # version de la DCL

    output_summary: dict         # résumé des outputs produits

@dataclass
class ExecutionStep:
    step_id: str
    capability_id: str
    started_at: str
    duration_ms: int
    input_hash: str
    output_artifact_ids: List[str]
    status: str                  # "success" | "error" | "skipped" | "fallback"
    fallback_used: Optional[str]
    engine_calls: List[str]      # modules VIE appelés
    vie_trace_ref: Optional[str] # lien vers DecisionTrace du VIE si applicable

@dataclass
class ExecutionError:
    step_id: Optional[str]
    code: str
    message: str
    recoverable: bool
    fallback_applied: Optional[str]
```

---

## 4. Taxonomie des capabilities

> Chaque capability est une fonction atomique. Elle appelle le VIE, jamais d'autres capabilities.
> Les workflows composent les capabilities.

### 4.1 ANALYSE

```
analysis/
├── brand/
│   ├── extract_brand_dna         image | URL | logo → BrandDNA
│   ├── extract_visual_signature  [images] → VisualSignature
│   └── compare_styles            ThemeDNA × 2 → StyleDiff + DriftReport
│
├── palette/
│   ├── analyze_palette           image | CSS → PaletteProfile
│   └── harmonize_palette         colors + harmony_target → PaletteProfile harmonisée
│
├── typography/
│   ├── analyze_typography        image | CSS → TypographyProfile
│   └── harmonize_typography      font_set → TypographyProfile cohérente
│
├── layout/
│   ├── analyze_layout_rhythm     screenshot → LayoutProfile
│   └── analyze_geometry          image → GeometryProfile
│
├── theme/
│   ├── extract_theme_dna         image | preset → ThemeDNA
│   └── score_theme_coherence     ThemeTokens → CoherenceReport
│
└── quality/
    ├── validate_accessibility    ThemeTokens → AccessibilityReport (WCAG)
    ├── validate_identity_drift   BrandDNA × 2 → DriftReport (avant/après)
    ├── detect_visual_overlap     [ThemeTokens] → OverlapReport
    └── deduplicate_themes        [ThemeTokens] → set dédupliqué
```

### 4.2 GÉNÉRATION

```
generation/
├── theme/
│   ├── generate_theme_from_image    image → ThemeTokens
│   ├── generate_theme_from_logo     logo → ThemeTokens
│   └── generate_theme_from_brand_dna BrandDNA → ThemeTokens
│
├── design_system/
│   ├── generate_ui_kit              ThemeTokens → UiKitBundle
│   ├── generate_brand_guidelines    ThemeTokens + brand_info → BrandGuidelines
│   └── generate_design_tokens       ThemeTokens → JsonTokens (multi-formats)
│
└── assets/
    ├── generate_border_family       style_tags → BorderFamilyPack
    ├── generate_ornament_pack       style_tags → OrnamentPack
    └── generate_layout_variants     ThemeTokens → LayoutVariantSet
```

### 4.3 MUTATION / ÉVOLUTION

```
mutation/
├── mutate_theme                ThemeTokens + mutation_params → ThemeTokens
├── evolve_brand_identity       BrandDNA + evolution_prompt → BrandDNA (évolué)
├── refresh_theme_with_trends   ThemeTokens + trend_tags → ThemeTokens
├── create_theme_variants       ThemeTokens → ThemeVariantSet
└── adapt_theme_to_target       ThemeTokens + target (web|app|print) → ThemeTokens adapté
```

### 4.4 REVERSE DESIGN

```
reverse/
├── reverse_brand_from_site       URL → BrandDNA  (scrape + analyse)
├── reverse_brand_from_mockup     mockup_image → BrandDNA
└── reverse_brand_from_image_set  [images] → BrandDNA (consensus multi-sources)
```

### 4.5 HARMONISATION

```
harmonization/
├── harmonize_palette           colors → PaletteProfile harmonisée
├── harmonize_typography        font_set → TypographyProfile cohérente
├── deduplicate_themes          [ThemeTokens] → set dédupliqué
├── detect_visual_overlap       [ThemeTokens] → OverlapReport
├── validate_identity_drift     BrandDNA × 2 → DriftReport
└── validate_accessibility      ThemeTokens → AccessibilityReport
```

### 4.6 RENDU / EXPORT

```
render/
├── render_css_bundle           ThemeTokens → CssBundle
├── render_scss_tokens          ThemeTokens → ScssBundle
├── render_json_tokens          ThemeTokens → JsonTokens
├── render_brand_guidelines     BrandGuidelines → HTML + PDF
└── render_preview_pack         ThemeTokens → PreviewPack (HTML + screenshots)
```

---

## 5. Taxonomie des endpoints API

### 5.1 Conventions

```
Base URL    : /v{n}/design/
Versioning  : dans l'URL (/v1/, /v2/) — pas dans le header
Nommage     : verbe-complément en kebab-case
Auth        : Bearer token dans header Authorization
Async       : POST retourne { job_id } si async_mode=true
Polling     : GET /v1/jobs/{job_id}
Webhooks    : webhook_url dans le body de la requête
Pagination  : ?page=1&limit=20 sur les GET collections
```

### 5.2 Capabilities exposées

```
# Analyse
POST /v1/design/extract-brand-dna
POST /v1/design/extract-theme-dna
POST /v1/design/extract-visual-signature
POST /v1/design/analyze-palette
POST /v1/design/analyze-typography
POST /v1/design/compare-styles
POST /v1/design/score-coherence
POST /v1/design/validate-accessibility

# Génération
POST /v1/design/generate-theme
POST /v1/design/generate-theme-from-logo
POST /v1/design/generate-ui-kit
POST /v1/design/generate-brand-guidelines
POST /v1/design/generate-design-tokens
POST /v1/design/generate-border-family
POST /v1/design/generate-ornament-pack

# Mutation
POST /v1/design/mutate-theme
POST /v1/design/evolve-brand
POST /v1/design/refresh-with-trends
POST /v1/design/create-variants
POST /v1/design/adapt-theme

# Reverse
POST /v1/design/reverse-brand-from-site
POST /v1/design/reverse-brand-from-mockup

# Render
POST /v1/design/render-css
POST /v1/design/render-scss
POST /v1/design/render-tokens
POST /v1/design/render-preview
```

### 5.3 Workflows exposés

```
POST /v1/design/workflows/reverse-brand-from-site
POST /v1/design/workflows/generate-theme-pack
POST /v1/design/workflows/build-design-system
POST /v1/design/workflows/evolve-identity
POST /v1/design/workflows/launch-event-pack
POST /v1/design/workflows/create-white-label-bundle
POST /v1/design/workflows/redesign-site
```

### 5.4 Ressources (GET)

```
GET /v1/design/themes/{id}
GET /v1/design/brand-dna/{id}
GET /v1/design/artifacts/{id}
GET /v1/design/workflows/{id}
GET /v1/design/recipes/{id}
GET /v1/design/recipes                          ?category=&tag=
GET /v1/design/libraries/{library_name}
GET /v1/design/libraries/{library_name}/{asset_id}
GET /v1/jobs/{job_id}                           polling async
GET /v1/design/capabilities                     catalogue des capabilities
```

### 5.5 Exemple de schéma request/response

```json
// POST /v1/design/generate-theme
// Request
{
  "input_type": "image",            // "image" | "logo" | "brand_dna" | "url"
  "image_url": "https://...",
  "targets": ["web", "app"],
  "requested_variants": ["dark", "soft"],
  "complexity_level": 3,
  "style_tags": ["luxe", "warm"],
  "async": false
}

// Response 200
{
  "theme_tokens": { "..." },
  "artifacts": [
    { "type": "ThemeTokens", "format": "json", "url": "..." },
    { "type": "CssBundle",   "format": "css",  "url": "..." },
    { "type": "PreviewPack", "format": "zip",  "url": "..." }
  ],
  "execution_trace_id": "trc_abc123",
  "coherence_score": 0.84,
  "warnings": [],
  "duration_ms": 1240
}
```

---

## 6. Taxonomie des workflows

### 6.1 REVERSE

**`reverse_brand_from_site`**
> Analyser l'identité visuelle d'un site existant.

```
Objectif  : extraire et formaliser l'identité visuelle d'une URL
Inputs    : url, targets, depth (light|full)
Steps     :
  1. scrape_site               → [screenshots, CSS, fonts]
  2. extract_brand_dna         → BrandDNA
  3. extract_theme_dna         → ThemeDNA
  4. score_theme_coherence     → CoherenceReport
  5. render_preview_pack       → PreviewPack
  6. render_brand_guidelines   → BrandGuidelines (optionnel)
Outputs   : BrandDNA + ThemeTokens + CoherenceReport + PreviewPack
Durée est.: 15-45s
```

**`reverse_brand_from_image_set`**
> Reconstituer une identité depuis un ensemble d'images (photos produits, mockups, etc.)

```
Steps     :
  1. extract_visual_signature  [images] → VisualSignature
  2. analyze_palette           → PaletteProfile
  3. analyze_geometry          → GeometryProfile
  4. extract_brand_dna         → BrandDNA
  5. generate_theme_from_brand_dna → ThemeTokens
  6. render_preview_pack       → PreviewPack
```

---

### 6.2 GÉNÉRATION

**`generate_theme_pack`**
> Générer N thèmes variés depuis un brief ou une image.

```
Objectif  : produire un pack de thèmes cohérents mais distincts
Inputs    : image | brief, n_themes (3-8), style_constraints
Steps     :
  1. extract_brand_dna         → BrandDNA
  2. generate_theme × N        → [ThemeTokens] (parallèle)
  3. detect_visual_overlap     → vérification différenciation
  4. deduplicate_themes        → si overlap trop fort
  5. render_preview_pack × N   → [PreviewPack]
  6. render_css_bundle × N     → [CssBundle]
Outputs   : ThemeVariantSet + [PreviewPack] + [CssBundle]
Durée est.: 30-90s
```

**`generate_brand_from_moodboard`**
> Transformer un moodboard en identité complète.

```
Steps     :
  1. reverse_brand_from_image_set  → BrandDNA
  2. generate_theme_from_brand_dna → ThemeTokens
  3. generate_ui_kit               → UiKitBundle
  4. generate_brand_guidelines     → BrandGuidelines
  5. score_theme_coherence         → CoherenceReport
  6. render_preview_pack           → PreviewPack
```

---

### 6.3 DESIGN SYSTEM

**`build_saas_design_system`**
> Construire un design system complet pour un produit SaaS.

```
Objectif  : design system production-ready depuis un brief produit
Inputs    : product_brief, logo?, color_preferences, target_platforms
Steps     :
  1. extract_brand_dna         → BrandDNA
  2. generate_theme_from_brand_dna → ThemeTokens
  3. validate_accessibility    → AccessibilityReport (hard gate)
  4. generate_ui_kit           → UiKitBundle
  5. generate_design_tokens    → JsonTokens (web + app)
  6. generate_brand_guidelines → BrandGuidelines
  7. render_preview_pack       → PreviewPack
Outputs   : ThemeTokens + UiKitBundle + JsonTokens + BrandGuidelines + PreviewPack
Durée est.: 60-120s
```

---

### 6.4 ÉVOLUTION

**`evolve_existing_identity`**
> Faire évoluer une identité existante sans la casser.

```
Objectif  : moderniser / rafraîchir sans perdre la reconnaissance
Inputs    : brand_assets | url, evolution_direction, drift_tolerance
Steps     :
  1. reverse_brand_from_site | reverse_brand_from_image_set → BrandDNA (v1)
  2. evolve_brand_identity     → BrandDNA (v2, évolué)
  3. validate_identity_drift   → DriftReport (v1 vs v2)
  4. generate_theme_from_brand_dna → ThemeTokens
  5. score_theme_coherence     → CoherenceReport
  6. render_preview_pack       → PreviewPack (avant/après)
Outputs   : BrandDNA v2 + ThemeTokens + DriftReport + PreviewPack
```

**`redesign_existing_site`**
> Reproduire + améliorer un site en tenant compte du DNA existant.

```
Steps     :
  1. reverse_brand_from_site   → BrandDNA + ThemeDNA actuels
  2. mutate_theme              → ThemeTokens (selon brief d'évolution)
  3. validate_identity_drift   → vérification cohérence
  4. validate_accessibility    → WCAG gate
  5. generate_ui_kit           → UiKitBundle
  6. render_css_bundle         → CssBundle
  7. render_preview_pack       → PreviewPack
```

---

### 6.5 ÉVÉNEMENTIEL / PACKAGING

**`launch_event_design_pack`**
> Pack design complet pour un événement ou une occasion.

```
Inputs    : event_brief (nom, type, date, univers), targets
Steps     :
  1. extract_brand_dna         → BrandDNA (depuis brief)
  2. generate_theme_from_brand_dna → ThemeTokens
  3. create_theme_variants     → ThemeVariantSet (digital + print)
  4. adapt_theme_to_target × 2 → ThemeTokens web + ThemeTokens print
  5. generate_ui_kit           → UiKitBundle
  6. render_preview_pack       → PreviewPack
  7. render_css_bundle         → CssBundle web
  8. render_json_tokens        → JsonTokens print
```

**`create_white_label_theme_bundle`**
> Générer un bundle de N thèmes différenciés pour revente.

```
Inputs    : base_theme | brief, n_themes, min_differentiation
Steps     :
  1. generate_theme × N        (parallèle, contraintes de différenciation)
  2. detect_visual_overlap     → vérification
  3. deduplicate_themes        → si overlap
  4. validate_accessibility × N → gate WCAG
  5. render_css_bundle × N     → [CssBundle]
  6. render_preview_pack × N   → [PreviewPack]
  7. package_bundle            → ThemeBundleZip
```

---

## 7. Bibliothèque de recettes SaaS

### 7.1 Structure DesignRecipe complète

```json
{
  "id": "brand_reverse_audit",
  "use_case": "Analyser et formaliser l'identité visuelle d'un concurrent ou d'une inspiration",
  "target_audience": "Agences web, freelances design, directeurs artistiques",
  "problem_solved": "Reproduire manuellement un style prend des heures. Cette recette extrait en 30s le DNA complet d'un site ou d'une image.",

  "workflow_id": "reverse_brand_from_site",
  "input_schema": {
    "url": "string (URL du site à analyser)",
    "depth": "'light' | 'full'",
    "output_formats": "['json', 'css', 'pdf']"
  },
  "output_artifacts": ["BrandDNA", "ThemeTokens", "CoherenceReport", "PreviewPack"],

  "execution_mode": "async",
  "automation_level": "full",
  "customization_level": "low",

  "packaging": {
    "product_name": "Brand Reverse Audit",
    "tagline": "Le DNA visuel de n'importe quel site en 30 secondes.",
    "pricing_model": "credits",
    "price_indication": "2 crédits / analyse",
    "delivery_format": "api + webapp",
    "time_to_value": "< 30 secondes",
    "differentiator": "Résultats structurés (JSON + CSS prêt à l'emploi), pas juste des couleurs"
  }
}
```

### 7.2 Catalogue de recettes

---

**`brand_reverse_audit`**
- **Use case :** Analyser l'identité visuelle d'un site ou d'une image
- **Workflow :** `reverse_brand_from_site` / `reverse_brand_from_image_set`
- **Inputs :** URL ou image(s)
- **Outputs :** BrandDNA + ThemeTokens + CSS + PreviewPack
- **Automation :** Full
- **Pricing :** À la génération (credits)
- **Clients :** Agences, freelances, directeurs artistiques

---

**`theme_from_logo`**
- **Use case :** Uploader un logo et obtenir un thème complet en quelques secondes
- **Workflow :** `generate_brand_from_moodboard` (simplifié logo)
- **Inputs :** logo (PNG/SVG), style preferences optionnelles
- **Outputs :** ThemeTokens + CssBundle + ScssBundle + PreviewPack
- **Automation :** Full
- **Pricing :** Freemium (1 génération gratuite, puis credits)
- **Clients :** Freelances, créateurs, petites entreprises

---

**`brand_evolution_studio`**
- **Use case :** Faire évoluer une identité existante sans la casser
- **Workflow :** `evolve_existing_identity`
- **Inputs :** URL ou assets existants + direction d'évolution (brief libre)
- **Outputs :** BrandDNA v2 + DriftReport + PreviewPack avant/après + CssBundle
- **Automation :** Supervised (validation intermédiaire)
- **Pricing :** Subscription mensuelle
- **Clients :** Startups en rebranding, agences en refontes

---

**`event_design_generator`**
- **Use case :** Générer un pack design complet pour un événement
- **Workflow :** `launch_event_design_pack`
- **Inputs :** Nom événement, type (conférence / anniversaire / festival...), univers, date
- **Outputs :** ThemeTokens web + print + UiKitBundle + PreviewPack
- **Automation :** Full
- **Pricing :** À la génération
- **Clients :** Organisateurs d'événements, agences événementielles, particuliers

---

**`white_label_theme_factory`**
- **Use case :** Générer N thèmes différenciés pour revente ou licensing
- **Workflow :** `create_white_label_theme_bundle`
- **Inputs :** Brief ou thème de base, N (3-20), contraintes de différenciation
- **Outputs :** ThemeBundleZip (N × CSS + JSON + Preview)
- **Automation :** Full
- **Pricing :** Volume — prix dégressif par thème
- **Clients :** Marketplaces de thèmes, agences produisant des kits

---

**`saas_design_system_builder`**
- **Use case :** Construire un design system production-ready depuis un brief produit
- **Workflow :** `build_saas_design_system`
- **Inputs :** Product brief, logo?, couleurs préférées, stack technique
- **Outputs :** ThemeTokens + UiKitBundle + JsonTokens + BrandGuidelines + PreviewPack
- **Automation :** Supervised (validation accessibilité)
- **Pricing :** Subscription — usage intensif
- **Clients :** Startups, équipes produit, développeurs solo

---

**`redesign_assistant`**
- **Use case :** Refondre un site existant en s'appuyant sur son DNA actuel
- **Workflow :** `redesign_existing_site`
- **Inputs :** URL, brief d'évolution, tolérance de dérive
- **Outputs :** ThemeTokens + CssBundle + DriftReport + PreviewPack avant/après
- **Automation :** Supervised
- **Pricing :** Subscription ou projet
- **Clients :** Agences web, freelances, équipes marketing

---

## 8. Taxonomie des artefacts

### 8.1 Artefacts d'entrée (inputs)

```
inputs/
├── ImageInput          image brute (PNG, JPG, WebP, SVG)
├── LogoInput           logo vectoriel ou raster
├── UrlInput            URL d'un site à analyser
├── BriefInput          description textuelle libre
└── PresetInput         ThemePreset v1 (compatibilité ascendante)
```

### 8.2 Artefacts d'analyse (intermédiaires)

```
analysis/
├── BrandDNA            identité de marque complète (DNA niveau marque)
├── ThemeDNA            DNA visuel niveau thème (tags ouverts, voir VIE)
├── VisualSignature     empreinte visuelle extraite d'un set d'images
├── PaletteProfile      profil couleur (primary, secondary, mood, dérivées)
├── TypographyProfile   profil typographique (familles, rôles, échelle)
├── GeometryProfile     profil géométrique (formes, radius, densité)
├── LayoutProfile       profil de layout (rhythm, grille, densité)
└── StyleDiff           différentiel entre deux styles / identités
```

### 8.3 Artefacts core (produits par le VIE)

```
core/
├── ThemeTokens         tokens complets (couleurs, typo, spacing, shapes...)
├── ThemeVariantSet     ensemble de variants (dark, soft, playful...)
└── DecisionTrace       trace complète de résolution du VIE (voir _SPECS.md)
```

### 8.4 Artefacts design system

```
design_system/
├── UiKitBundle         composants HTML/CSS prêts à l'emploi
├── BrandGuidelines     charte graphique structurée (HTML + PDF)
└── AccessibilityReport rapport WCAG (contraste, lisibilité, taille minimale)
```

### 8.5 Artefacts de rendu (outputs finaux)

```
render/
├── CssBundle           fichier CSS complet (variables + reset + composants)
├── ScssBundle          fichier SCSS tokens ($variables + mixins)
├── JsonTokens          tokens JSON (multi-formats : web, RN, Flutter, Figma)
├── PreviewPack         aperçu HTML + captures (landing, composants, palette)
└── ThemeBundleZip      bundle multi-thèmes packagé (white-label)
```

### 8.6 Artefacts d'analyse qualité

```
quality/
├── CoherenceReport     score + détail cohérence VIE (global + par dimension)
├── DriftReport         mesure de dérive entre deux identités (avant/après)
├── OverlapReport       détection de similarité entre thèmes d'un set
└── TrendReport         analyse tendances visuelles (futur)
```

### 8.7 Relations entre artefacts

```
ImageInput / UrlInput / LogoInput
    ↓ extract_*
BrandDNA / ThemeDNA / VisualSignature
    ↓ generate_theme_* / ThemeCompiler (VIE)
ThemeTokens
    ↓ generate_ui_kit / generate_brand_guidelines
    ├── UiKitBundle
    └── BrandGuidelines
    ↓ render_*
    ├── CssBundle
    ├── ScssBundle
    ├── JsonTokens
    └── PreviewPack

ThemeTokens × N
    ↓ create_theme_variants / white_label
ThemeVariantSet → ThemeBundleZip
```

---

## 9. Dialogue DCL ↔ VIE

### Principe de séparation

```
VIE ne connaît pas :          DCL ne réimplémente pas :
- les capabilities            - la résolution de thème
- les endpoints               - le scoring CompatibilityEngine
- les workflows               - le calcul de variantes
- les recipes                 - la dérivation palette
- les artefacts DCL           - le moteur de mutation
```

### Interface VIE exposée à la DCL

```python
# Le VIE expose une API interne typée — la DCL ne touche qu'à ça

class VisualIdentityEngine:

    # Analyse
    def analyze_image(self, image: bytes) -> ThemeDNA
    def analyze_url(self, url: str) -> ThemeDNA

    # Pipeline principal
    def resolve(self, dna: ThemeDNA) -> Resolution
    # Resolution = ResolvedAssets + DecisionTrace

    # Compilation
    def compile(self, dna: ThemeDNA, resolved: ResolvedAssets) -> ThemeTokens

    # Mutation
    def mutate(self, tokens: ThemeTokens, params: MutationParams) -> ThemeTokens
    def evolve(self, dna: ThemeDNA, direction: str) -> ThemeDNA
    def create_variants(self, tokens: ThemeTokens, variants: List[str]) -> ThemeVariantSet

    # Rendu
    def render_css(self, tokens: ThemeTokens) -> str
    def render_scss(self, tokens: ThemeTokens) -> str
    def render_json(self, tokens: ThemeTokens) -> dict

    # Scoring
    def score_coherence(self, tokens: ThemeTokens) -> CoherenceReport
    def validate_accessibility(self, tokens: ThemeTokens) -> AccessibilityReport
    def detect_drift(self, dna_a: ThemeDNA, dna_b: ThemeDNA) -> DriftReport
```

### Flux d'une capability typique

```python
# Exemple : generate_theme_from_image

class GenerateThemeFromImageCapability(DesignCapability):
    id = "generate_theme_from_image"

    def execute(self, inputs: dict, vie: VisualIdentityEngine) -> CapabilityResult:
        trace = DesignExecutionTrace(trigger="capability", trigger_id=self.id)

        # 1. Appel VIE — analyse
        theme_dna = vie.analyze_image(inputs["image"])
        trace.add_step("analyze_image", engine_calls=["StyleAnalyzer"])

        # 2. Appel VIE — résolution
        resolution = vie.resolve(theme_dna)
        trace.add_step("resolve", engine_calls=["ThemeInterpreter", "CompatibilityEngine", "ThemeResolver"])

        # 3. Appel VIE — compilation
        theme_tokens = vie.compile(theme_dna, resolution.assets)
        trace.add_step("compile", engine_calls=["ThemeCompiler"])

        # 4. Appel VIE — rendu
        css = vie.render_css(theme_tokens)

        # 5. Packaging artefacts
        artifacts = [
            DesignArtifact(type="ThemeTokens", content=theme_tokens, format="json"),
            DesignArtifact(type="CssBundle",   content=css,          format="css"),
        ]

        trace.finalize(artifacts=artifacts, vie_trace=resolution.trace)
        return CapabilityResult(artifacts=artifacts, trace=trace)
```

---

## 10. Stratégie d'implémentation progressive

### Phase A — Fondations DCL (après VIE Phase 1-3)
- [ ] Définir les dataclasses DCL : `DesignCapability`, `DesignArtifact`, `DesignExecutionTrace`
- [ ] Implémenter interface VIE (`VisualIdentityEngine` facade)
- [ ] Capabilities analyse : `extract_brand_dna`, `score_theme_coherence`, `validate_accessibility`
- [ ] Capabilities génération core : `generate_theme_from_image`, `generate_theme_from_logo`
- [ ] Capabilities rendu : `render_css_bundle`, `render_scss_tokens`, `render_json_tokens`
- [ ] Tests unitaires capabilities

### Phase B — Workflows + Endpoints
- [ ] Framework workflow : `WorkflowStep`, `DesignWorkflow`, orchestrateur
- [ ] Workflows prioritaires : `reverse_brand_from_site`, `generate_theme_pack`
- [ ] API FastAPI : router `/v1/design/`, schemas OpenAPI auto-générés
- [ ] Endpoints capabilities core (POST)
- [ ] Endpoints workflows (POST async + polling)
- [ ] Tests intégration

### Phase C — Mutations + Évolution
- [ ] `MutationEngine` dans le VIE
- [ ] Capabilities mutation : `mutate_theme`, `evolve_brand_identity`, `create_theme_variants`
- [ ] Workflow `evolve_existing_identity`, `redesign_existing_site`
- [ ] Recettes : `brand_evolution_studio`, `redesign_assistant`

### Phase D — Recettes SaaS + Packaging
- [ ] `DesignRecipe` dataclass + catalogue
- [ ] Recette `brand_reverse_audit` (première commercialisable)
- [ ] Recette `theme_from_logo`
- [ ] Recette `saas_design_system_builder`
- [ ] UI produit pour chaque recette (formulaire → génération → download)

### Phase E — Scale + White Label
- [ ] Recettes `white_label_theme_factory`, `event_design_generator`
- [ ] Workflows batch (génération multiple en parallèle)
- [ ] Authentification + rate limiting + credits
- [ ] Package DCL indépendant du VIE (`eurkai-design-platform`)
- [ ] Migration vers `EURKAI/MODULES/design_platform/`

---

*Prochaine étape : validation architecture DCL → démarrer Phase A (après VIE Phase 3)*
