# I2 — Modules Réutilisables EURKAI

## Spécification Technique Complète

**Version** : 1.0  
**Date** : 2025-12-01  
**Dépendances** : I1 (Génération Projet), H2 (Super.orchestrate), H3 (FractalDiff)  
**Pattern** : GEVR (Get-Execute-Validate-Render)

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [ObjectType Module](#2-objecttype-module)
3. [Taxonomie des modules](#3-taxonomie-des-modules)
4. [Catalogue de modules](#4-catalogue-de-modules)
5. [Sélection automatique](#5-sélection-automatique)
6. [Templates et composition](#6-templates-et-composition)
7. [Intégration avec I1](#7-intégration-avec-i1)
8. [Annexes](#8-annexes)

---

## 1. Vue d'ensemble

### 1.1 Objectif

I2 définit le **framework de modules réutilisables** d'EURKAI : un système unifié pour modéliser, cataloguer et instancier des composants réutilisables à travers tous les domaines d'application (web, mobile, email, flows, API, etc.).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      I2 — MODULE FRAMEWORK                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   CATALOG                    RESOLUTION                   INSTANCE       │
│   ───────                    ──────────                   ────────       │
│   ModuleCatalog              ┌─────────────────────┐      ModuleInstance │
│   ├─ types[]                 │  1. MATCH           │      ├─ oid        │
│   │  └─ Module.*             │     Brief → Types   │      ├─ config     │
│   ├─ templates[]             │                     │      ├─ bindings   │
│   │  └─ ModuleTemplate.*     │  2. SELECT          │      └─ state      │
│   ├─ components[]            │     Score & Rank    │                     │
│   │  └─ Component.*          │                     │      +              │
│   └─ seeds[]                 │  3. RESOLVE         │      FractalDiff    │
│      └─ Seed.*               │     Dependencies    │      (pour I1)      │
│                              │                     │                     │
│                              │  4. INSTANTIATE     │                     │
│                              │     Config & Bind   │                     │
│                              └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Principes architecturaux

| Principe | Description |
|----------|-------------|
| **Généricité** | Module agnostique du medium (web, mobile, email, CLI, flow) |
| **Composabilité** | Modules emboîtables sans limite de profondeur |
| **Résolution tardive** | Configuration résolue au moment de l'instanciation |
| **Versioning sémantique** | Chaque module versionné indépendamment |
| **IVC×DRO** | Respect complet du pattern Identity-View-Context × Definition-Rule-Option |

### 1.3 Hiérarchie fractale

```
FractalObject
└── Module (abstract)
    ├── Module.Page
    │   ├── Module.Page.Landing
    │   ├── Module.Page.Dashboard
    │   └── Module.Page.Form
    ├── Module.Section
    │   ├── Module.Section.Hero
    │   ├── Module.Section.Features
    │   └─ Module.Section.CTA
    ├── Module.Component
    │   ├── Module.Component.Button
    │   ├── Module.Component.Card
    │   └── Module.Component.Modal
    ├── Module.Template
    │   ├── Module.Template.Strategy
    │   ├── Module.Template.Offer
    │   └── Module.Template.Flow
    ├── Module.Flow
    │   ├── Module.Flow.Onboarding
    │   ├── Module.Flow.Checkout
    │   └── Module.Flow.Support
    └── Module.Email
        ├── Module.Email.Transactional
        ├── Module.Email.Marketing
        └── Module.Email.Notification
```

---

## 2. ObjectType Module

### 2.1 Définition IVC×DRO

```yaml
Module:
  # ═══════════════════════════════════════════════════════════════════
  # IDENTITY (I) — Ce qu'est le module
  # ═══════════════════════════════════════════════════════════════════
  identity:
    oid: { type: string, format: "mod_{ulid}", auto: true }
    type: { type: string, pattern: "^Module\\.[A-Z][a-zA-Z.]*$" }
    name: { type: string, required: true, max_length: 64 }
    slug: { type: string, pattern: "^[a-z0-9-]+$", auto_from: name }
    version: { type: semver, default: "1.0.0" }
    
  # ═══════════════════════════════════════════════════════════════════
  # VIEW (V) — Comment le module se présente
  # ═══════════════════════════════════════════════════════════════════
  view:
    display_name: { type: i18n_string }
    description: { type: i18n_text }
    icon: { type: string, format: icon_ref }
    thumbnail: { type: string, format: uri }
    preview_url: { type: string, format: uri }
    tags: { type: array, items: string, max_items: 20 }
    
  # ═══════════════════════════════════════════════════════════════════
  # CONTEXT (C) — Où et quand le module s'applique
  # ═══════════════════════════════════════════════════════════════════
  context:
    domain: 
      type: enum
      values: [web, mobile, email, flow, api, cli, universal]
      default: universal
    platforms: 
      type: array
      items: { enum: [react, vue, svelte, html, react_native, flutter, email_html] }
    compatibility:
      min_eurkai_version: { type: semver }
      max_eurkai_version: { type: semver, nullable: true }
      required_capabilities: { type: array, items: string }
    audience:
      type: array
      items: { enum: [b2b, b2c, internal, saas, marketplace, agency] }
    locale_support: { type: array, items: locale_code, default: ["*"] }

  # ═══════════════════════════════════════════════════════════════════
  # DEFINITION (D) — Structure interne du module
  # ═══════════════════════════════════════════════════════════════════
  definition:
    # Slots = emplacements pour enfants
    slots:
      type: map
      key_type: string
      value_type:
        slot_name: { type: string }
        accepts: { type: array, items: type_pattern }
        min_items: { type: integer, default: 0 }
        max_items: { type: integer, default: null }
        default_content: { type: oid_ref, nullable: true }
        
    # Props = paramètres configurables
    props:
      type: map
      key_type: string
      value_type:
        prop_name: { type: string }
        prop_type: { type: json_schema }
        default: { type: any }
        required: { type: boolean, default: false }
        ui_hint: { type: string }
        
    # Bindings = connexions aux données
    bindings:
      type: map
      key_type: string
      value_type:
        source: { type: binding_expr }
        transform: { type: transform_expr, nullable: true }
        fallback: { type: any }
        
    # Assets = ressources associées
    assets:
      type: array
      items:
        asset_type: { enum: [style, script, image, font, data] }
        path: { type: string }
        inline: { type: boolean, default: false }
        conditions: { type: array, items: condition_expr }

  # ═══════════════════════════════════════════════════════════════════
  # RULE (R) — Contraintes et validations
  # ═══════════════════════════════════════════════════════════════════
  rules:
    - rule_id: "module.name.valid"
      erk: "MATCH($.identity.name, '^[A-Za-z][A-Za-z0-9_-]*$')"
      severity: error
      message: "Module name must start with letter and contain only alphanumeric, underscore, dash"
      
    - rule_id: "module.slots.accepts.valid"
      erk: "FORALL($.definition.slots.*, VALID_TYPE_PATTERN($.accepts))"
      severity: error
      
    - rule_id: "module.version.increment"
      erk: "SEMVER_GTE($.identity.version, $.previous.identity.version)"
      severity: warning
      context: on_update
      
    - rule_id: "module.dependencies.resolvable"
      erk: "FORALL($.relations.depends_on, EXISTS_IN_CATALOG($))"
      severity: error
      
    - rule_id: "module.circular.check"
      erk: "NOT(HAS_CYCLE($.relations.depends_on))"
      severity: error
      message: "Circular dependency detected"

  # ═══════════════════════════════════════════════════════════════════
  # OPTION (O) — Variantes et configurations
  # ═══════════════════════════════════════════════════════════════════
  options:
    variants:
      type: map
      key_type: string
      value_type:
        variant_name: { type: string }
        overrides: { type: partial_module_def }
        conditions: { type: array, items: condition_expr }
        
    themes:
      type: array
      items:
        theme_id: { type: string }
        style_tokens: { type: map }
        
    feature_flags:
      type: map
      key_type: string
      value_type:
        enabled: { type: boolean, default: true }
        rollout_percentage: { type: number, min: 0, max: 100 }
```

### 2.2 Méthodes

```yaml
Module.methods:
  # ─────────────────────────────────────────────────────────────────
  # Lifecycle
  # ─────────────────────────────────────────────────────────────────
  initialize:
    signature: "(config: ModuleConfig) -> ModuleInstance"
    description: "Crée une instance configurée du module"
    
  validate:
    signature: "() -> ValidationResult"
    description: "Valide la cohérence interne du module"
    
  dispose:
    signature: "() -> void"
    description: "Libère les ressources de l'instance"

  # ─────────────────────────────────────────────────────────────────
  # Rendering
  # ─────────────────────────────────────────────────────────────────
  render:
    signature: "(context: RenderContext) -> RenderOutput"
    description: "Génère la sortie pour le medium cible"
    parameters:
      context:
        medium: { enum: [html, json, react, vue, native, email] }
        locale: { type: locale_code }
        theme: { type: string }
        
  preview:
    signature: "(options: PreviewOptions) -> PreviewOutput"
    description: "Génère un aperçu statique"
    
  # ─────────────────────────────────────────────────────────────────
  # Export / Import
  # ─────────────────────────────────────────────────────────────────
  export:
    signature: "(format: ExportFormat) -> ExportPayload"
    description: "Exporte le module dans un format portable"
    parameters:
      format: { enum: [eurkai_json, eurkai_yaml, figma, storybook] }
      
  import:
    signature: "(payload: ImportPayload) -> Module"
    description: "Importe depuis un format externe"
    static: true

  # ─────────────────────────────────────────────────────────────────
  # Composition
  # ─────────────────────────────────────────────────────────────────
  compose:
    signature: "(children: ModuleInstance[]) -> ComposedModule"
    description: "Compose plusieurs modules enfants"
    
  clone:
    signature: "(overrides?: Partial<ModuleConfig>) -> Module"
    description: "Clone le module avec modifications optionnelles"
    
  extend:
    signature: "(extensions: ModuleExtension) -> Module"
    description: "Étend le module avec de nouvelles capacités"

  # ─────────────────────────────────────────────────────────────────
  # Resolution
  # ─────────────────────────────────────────────────────────────────
  resolve_dependencies:
    signature: "() -> DependencyGraph"
    description: "Résout l'arbre complet des dépendances"
    
  resolve_bindings:
    signature: "(data_context: DataContext) -> BoundModule"
    description: "Résout les bindings avec les données"
```

### 2.3 Relations

```yaml
Module.relations:
  # Héritage et lineage
  inherits_from:
    type: many_to_one
    target: Module
    description: "Module parent dans la hiérarchie"
    
  lineage:
    type: computed
    expression: "ANCESTORS($.inherits_from)"
    description: "Chaîne complète d'héritage"

  # Dépendances
  depends_on:
    type: many_to_many
    target: [Module, Seed, Style, Asset]
    description: "Dépendances requises"
    attributes:
      dependency_type: { enum: [required, optional, dev] }
      version_constraint: { type: semver_range }
      
  # Composition
  children:
    type: one_to_many
    target: Module
    via: slots
    description: "Modules enfants dans les slots"
    
  # Scénarios
  used_in_scenarios:
    type: many_to_many
    target: Scenario
    description: "Scénarios utilisant ce module"
    
  # Seeds (données de base)
  requires_seeds:
    type: many_to_many
    target: Seed
    description: "Seeds nécessaires au fonctionnement"
    
  # Styles
  styled_by:
    type: many_to_many
    target: Style
    description: "Styles applicables"
```

---

## 3. Taxonomie des modules

### 3.1 Par granularité

```yaml
granularity_taxonomy:
  atom:
    description: "Élément indivisible"
    examples: [Button, Icon, Badge, Input]
    typical_slots: 0
    
  molecule:
    description: "Combinaison d'atomes"
    examples: [SearchBar, Card, MenuItem]
    typical_slots: 1-3
    
  organism:
    description: "Groupe fonctionnel complet"
    examples: [Header, Footer, ProductGrid, Form]
    typical_slots: 3-10
    
  template:
    description: "Structure de page sans contenu"
    examples: [DashboardLayout, LandingLayout, BlogLayout]
    typical_slots: 5-20
    
  page:
    description: "Instance complète avec contenu"
    examples: [HomePage, ProductPage, CheckoutPage]
    typical_slots: 10+
    
  flow:
    description: "Séquence de pages/étapes"
    examples: [OnboardingFlow, CheckoutFlow, SupportFlow]
    typical_slots: varies
```

### 3.2 Par domaine fonctionnel

```yaml
domain_taxonomy:
  navigation:
    types: [Header, Footer, Sidebar, Breadcrumb, Menu, Tabs]
    
  content:
    types: [Hero, TextBlock, MediaGallery, Testimonials, FAQ]
    
  commerce:
    types: [ProductCard, Cart, Checkout, PriceTable, Wishlist]
    
  forms:
    types: [ContactForm, SubscribeForm, SearchForm, FilterForm]
    
  data_display:
    types: [Table, Chart, KPI, Timeline, Calendar]
    
  communication:
    types: [Chat, Notification, Alert, Toast, Modal]
    
  authentication:
    types: [Login, Register, ForgotPassword, MFA]
    
  marketing:
    types: [CTA, Banner, Popup, SocialProof, Countdown]
```

### 3.3 Par medium

```yaml
medium_taxonomy:
  web:
    platforms: [html, react, vue, svelte]
    constraints:
      responsive: required
      accessibility: required
      seo: recommended
      
  mobile:
    platforms: [react_native, flutter, swift, kotlin]
    constraints:
      touch_optimized: required
      offline_capable: recommended
      
  email:
    platforms: [email_html, mjml]
    constraints:
      client_compatibility: required
      max_width: 600
      inline_styles: required
      
  flow:
    platforms: [n8n, zapier, make, custom]
    constraints:
      idempotent: required
      error_handling: required
      
  api:
    platforms: [openapi, graphql, grpc]
    constraints:
      versioned: required
      documented: required
```

---

## 4. Catalogue de modules

### 4.1 Structure du catalogue

```yaml
ModuleCatalog:
  identity:
    oid: { type: string, format: "cat_{ulid}" }
    name: { type: string }
    version: { type: semver }
    
  collections:
    - collection_id: core
      description: "Modules fondamentaux"
      modules: [...]
      
    - collection_id: ui
      description: "Composants UI"
      modules: [...]
      
    - collection_id: commerce
      description: "Modules e-commerce"
      modules: [...]
      
    - collection_id: marketing
      description: "Modules marketing"
      modules: [...]
      
    - collection_id: templates
      description: "Templates de pages"
      modules: [...]
      
  indexes:
    by_type: { type: btree, key: "$.type" }
    by_domain: { type: btree, key: "$.context.domain" }
    by_tags: { type: gin, key: "$.view.tags" }
    by_platform: { type: gin, key: "$.context.platforms" }
    full_text: { type: gin, key: ["$.view.display_name", "$.view.description"] }
```

### 4.2 Format d'entrée catalogue

```yaml
# Exemple : Module Hero
- oid: mod_01HX7VGHN2QF9KZWM5XY3T8P6R
  type: Module.Section.Hero
  identity:
    name: HeroSplit
    slug: hero-split
    version: "2.1.0"
    
  view:
    display_name:
      fr: "Hero Split"
      en: "Split Hero"
    description:
      fr: "Section héro avec image à droite et texte à gauche"
      en: "Hero section with right image and left text"
    icon: "layout-split"
    tags: [hero, landing, above-fold, image, cta]
    
  context:
    domain: web
    platforms: [html, react, vue]
    audience: [b2c, saas]
    
  definition:
    slots:
      media:
        accepts: ["Module.Component.Image", "Module.Component.Video"]
        min_items: 1
        max_items: 1
      cta:
        accepts: ["Module.Component.Button", "Module.Component.ButtonGroup"]
        max_items: 2
        
    props:
      headline:
        prop_type: { type: string, maxLength: 120 }
        required: true
        ui_hint: "textarea"
      subheadline:
        prop_type: { type: string, maxLength: 300 }
        ui_hint: "textarea"
      alignment:
        prop_type: { enum: [left, right] }
        default: left
      overlay_opacity:
        prop_type: { type: number, min: 0, max: 1 }
        default: 0
        
  options:
    variants:
      reversed:
        overrides:
          props:
            alignment:
              default: right
      video:
        overrides:
          slots:
            media:
              accepts: ["Module.Component.Video"]
              
  relations:
    depends_on:
      - { oid: "seed_typography_hero", type: Seed }
      - { oid: "style_hero_base", type: Style }
    styled_by:
      - { oid: "theme_light", type: Theme }
      - { oid: "theme_dark", type: Theme }
```

### 4.3 API de requête catalogue

```typescript
interface CatalogQuery {
  // Filtres
  filters?: {
    type?: TypePattern | TypePattern[];
    domain?: Domain | Domain[];
    platforms?: Platform[];
    tags?: { any?: string[]; all?: string[]; none?: string[] };
    audience?: Audience[];
    version?: SemverRange;
    compatibility?: {
      eurkai_version?: SemverRange;
      capabilities?: string[];
    };
  };
  
  // Recherche textuelle
  search?: {
    query: string;
    fields?: ('name' | 'description' | 'tags')[];
    fuzzy?: boolean;
  };
  
  // Tri
  sort?: {
    field: 'name' | 'version' | 'created_at' | 'popularity' | 'relevance';
    order: 'asc' | 'desc';
  }[];
  
  // Pagination
  pagination?: {
    limit: number;
    offset?: number;
    cursor?: string;
  };
  
  // Projection
  include?: string[];
  exclude?: string[];
}

interface CatalogQueryResult {
  modules: Module[];
  total: number;
  facets?: {
    by_type: { type: string; count: number }[];
    by_domain: { domain: string; count: number }[];
    by_tag: { tag: string; count: number }[];
  };
  pagination: {
    has_more: boolean;
    next_cursor?: string;
  };
}
```

---

## 5. Sélection automatique

### 5.1 Pipeline de matching

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODULE SELECTION PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   BRIEF                  ANALYSIS               CANDIDATES              │
│   ─────                  ────────               ──────────              │
│   "Landing page          ┌────────────┐         Module.Page.Landing     │
│    SaaS B2B avec         │ NLP Parse  │         ├─ score: 0.92         │
│    hero, features,   ──► │            │  ──►    │                       │
│    pricing,              │ Intent     │         Module.Page.Marketing   │
│    testimonials"         │ Detection  │         ├─ score: 0.78         │
│                          └────────────┘         │                       │
│                                                 └─ ...                  │
│                                                                          │
│   CONTEXT                CONSTRAINTS            RESOLVED                │
│   ───────                ───────────            ────────                │
│   domain: web            ┌────────────┐         SelectedModules[]       │
│   platform: react        │ Filter     │         ├─ HeroSplit           │
│   audience: b2b      ──► │            │  ──►    ├─ FeatureGrid         │
│   locale: fr             │ Score      │         ├─ PricingTable        │
│                          │            │         ├─ TestimonialCarousel │
│                          │ Rank       │         └─ FooterStandard      │
│                          └────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Règles de scoring

```yaml
scoring_rules:
  # Score de pertinence textuelle (0-100)
  text_relevance:
    weight: 0.3
    algorithm: bm25
    fields:
      name: 2.0
      description: 1.0
      tags: 1.5
      
  # Score de compatibilité contexte (0-100)
  context_match:
    weight: 0.25
    rules:
      - condition: "module.domain == brief.domain"
        score: 30
      - condition: "brief.platform IN module.platforms"
        score: 30
      - condition: "brief.audience INTERSECTS module.audience"
        score: 20
      - condition: "module.locale_support CONTAINS brief.locale"
        score: 20
        
  # Score de popularité (0-100)
  popularity:
    weight: 0.15
    factors:
      usage_count: 0.4
      rating: 0.3
      recent_usage: 0.3
      
  # Score de qualité (0-100)
  quality:
    weight: 0.15
    factors:
      test_coverage: 0.3
      documentation: 0.3
      accessibility_score: 0.2
      performance_score: 0.2
      
  # Score de fraîcheur (0-100)
  freshness:
    weight: 0.1
    decay:
      type: exponential
      half_life_days: 180
      
  # Score de cohérence (0-100)
  coherence:
    weight: 0.05
    rules:
      - condition: "already_selected USES_SAME_STYLE_SYSTEM"
        bonus: 20
      - condition: "already_selected FROM_SAME_COLLECTION"
        bonus: 15
```

### 5.3 Intent patterns

```yaml
intent_patterns:
  # Patterns pour détecter le type de page
  page_intents:
    - pattern: "(landing|accueil|home|vitrine)"
      suggests: [Module.Page.Landing]
      confidence: 0.9
      
    - pattern: "(dashboard|tableau de bord|admin)"
      suggests: [Module.Page.Dashboard]
      confidence: 0.9
      
    - pattern: "(blog|article|post)"
      suggests: [Module.Page.Blog]
      confidence: 0.85
      
    - pattern: "(produit|product|fiche)"
      suggests: [Module.Page.Product]
      confidence: 0.85
      
    - pattern: "(checkout|panier|commande)"
      suggests: [Module.Page.Checkout]
      confidence: 0.9

  # Patterns pour détecter les sections
  section_intents:
    - pattern: "(hero|bannière|entête principale)"
      suggests: [Module.Section.Hero]
      confidence: 0.95
      
    - pattern: "(features?|fonctionnalités?|avantages)"
      suggests: [Module.Section.Features]
      confidence: 0.9
      
    - pattern: "(pricing|tarifs?|prix|offres?)"
      suggests: [Module.Section.Pricing]
      confidence: 0.95
      
    - pattern: "(témoignages?|testimonials?|avis)"
      suggests: [Module.Section.Testimonials]
      confidence: 0.9
      
    - pattern: "(faq|questions)"
      suggests: [Module.Section.FAQ]
      confidence: 0.95
      
    - pattern: "(cta|call.to.action|appel.à.l.action)"
      suggests: [Module.Section.CTA]
      confidence: 0.9
      
    - pattern: "(équipe|team|membres)"
      suggests: [Module.Section.Team]
      confidence: 0.85

  # Patterns pour composants
  component_intents:
    - pattern: "(formulaire|form)"
      suggests: [Module.Component.Form]
      variants:
        - pattern: "contact"
          suggests: [Module.Component.ContactForm]
        - pattern: "(inscription|newsletter)"
          suggests: [Module.Component.SubscribeForm]
          
    - pattern: "(slider|carousel|galerie)"
      suggests: [Module.Component.Carousel]
      confidence: 0.85

  # Patterns contextuels
  context_intents:
    - pattern: "(saas|logiciel|application)"
      sets_context:
        audience: saas
        suggests_templates: [SaaSLanding, ProductPage]
        
    - pattern: "(e-?commerce|boutique|shop)"
      sets_context:
        audience: marketplace
        suggests_templates: [StoreFront, ProductCatalog]
        
    - pattern: "(b2b|entreprise|corporate)"
      sets_context:
        audience: b2b
        style_hints: [professional, minimal]
```

### 5.4 Algorithme de sélection

```python
# Pseudo-code de l'algorithme de sélection
class ModuleSelector:
    def select(self, brief: Brief, context: Context) -> List[SelectedModule]:
        # 1. Parse le brief
        parsed = self.parse_brief(brief)
        
        # 2. Détecte les intents
        intents = self.detect_intents(parsed)
        
        # 3. Pour chaque intent, query le catalogue
        candidates = []
        for intent in intents:
            query = self.build_query(intent, context)
            modules = self.catalog.query(query)
            candidates.extend(modules)
            
        # 4. Score chaque candidat
        scored = []
        for module in candidates:
            score = self.compute_score(module, parsed, context)
            scored.append((module, score))
            
        # 5. Rank et déduplique
        ranked = self.rank_and_dedupe(scored)
        
        # 6. Vérifie cohérence
        coherent = self.ensure_coherence(ranked)
        
        # 7. Résout dépendances
        resolved = self.resolve_dependencies(coherent)
        
        return resolved
        
    def compute_score(self, module, parsed, context) -> float:
        scores = {
            'text': self.score_text_relevance(module, parsed),
            'context': self.score_context_match(module, context),
            'popularity': self.score_popularity(module),
            'quality': self.score_quality(module),
            'freshness': self.score_freshness(module),
            'coherence': self.score_coherence(module, already_selected)
        }
        
        weights = self.get_weights()
        return sum(scores[k] * weights[k] for k in scores)
```

---

## 6. Templates et composition

### 6.1 Structure de template

```yaml
ModuleTemplate:
  lineage: ["Module", "FractalObject"]
  
  identity:
    oid: { type: string, format: "tpl_{ulid}" }
    type: { type: string, pattern: "^ModuleTemplate\\.[A-Z][a-zA-Z.]*$" }
    name: { type: string, required: true }
    category: { enum: [strategy, offer, flow, layout, email_sequence] }
    
  definition:
    # Structure hiérarchique
    structure:
      type: tree
      root:
        type: Module
        children:
          type: array
          items:
            slot: { type: string }
            module: { type: Module | ModuleTemplate }
            optional: { type: boolean, default: false }
            alternatives: { type: array, items: Module }
            
    # Variables du template
    variables:
      type: map
      key_type: string
      value_type:
        var_name: { type: string }
        var_type: { type: json_schema }
        default: { type: any }
        description: { type: string }
        
    # Règles de composition
    composition_rules:
      type: array
      items:
        rule_id: { type: string }
        condition: { type: expression }
        action: { type: composition_action }
```

### 6.2 Exemples de templates

```yaml
# Template : Landing Page SaaS
ModuleTemplate.SaaSLanding:
  identity:
    name: SaaSLanding
    category: layout
    
  definition:
    structure:
      root:
        type: Module.Page.Landing
        children:
          - slot: header
            module: Module.Navigation.Header
            
          - slot: main
            children:
              - slot: hero
                module: Module.Section.Hero
                alternatives:
                  - Module.Section.HeroSplit
                  - Module.Section.HeroVideo
                  
              - slot: social_proof
                module: Module.Section.LogoCloud
                optional: true
                
              - slot: features
                module: Module.Section.Features
                alternatives:
                  - Module.Section.FeatureGrid
                  - Module.Section.FeatureList
                  
              - slot: how_it_works
                module: Module.Section.Process
                optional: true
                
              - slot: pricing
                module: Module.Section.Pricing
                optional: true
                
              - slot: testimonials
                module: Module.Section.Testimonials
                optional: true
                
              - slot: faq
                module: Module.Section.FAQ
                optional: true
                
              - slot: cta
                module: Module.Section.CTA
                
          - slot: footer
            module: Module.Navigation.Footer
            
    variables:
      brand_name:
        var_type: string
        description: "Nom de la marque"
      primary_cta:
        var_type: { type: object, properties: { text: string, url: string } }
        description: "Call-to-action principal"
      show_pricing:
        var_type: boolean
        default: true
        
    composition_rules:
      - rule_id: "pricing_requires_cta"
        condition: "$.slots.pricing.enabled == true"
        action: { set: "$.slots.cta.enabled", value: true }
```

```yaml
# Template : Offre commerciale
ModuleTemplate.OfferPresentation:
  identity:
    name: OfferPresentation
    category: offer
    
  definition:
    structure:
      root:
        type: Module.Flow.Presentation
        children:
          - slot: intro
            module: Module.Slide.Title
            
          - slot: problem
            module: Module.Slide.ProblemStatement
            
          - slot: solution
            module: Module.Slide.SolutionOverview
            
          - slot: features
            module: Module.Slide.FeatureShowcase
            repeat: { min: 2, max: 5 }
            
          - slot: proof
            module: Module.Slide.SocialProof
            optional: true
            
          - slot: pricing
            module: Module.Slide.PricingOptions
            
          - slot: next_steps
            module: Module.Slide.NextSteps
            
          - slot: contact
            module: Module.Slide.Contact
            
    variables:
      client_name:
        var_type: string
      offer_title:
        var_type: string
      features:
        var_type: { type: array, items: { title: string, description: string } }
      pricing_tiers:
        var_type: { type: array, items: PricingTier }
```

### 6.3 Composition programmatique

```typescript
interface CompositionBuilder {
  // Initialise depuis un template
  fromTemplate(templateId: string): CompositionBuilder;
  
  // Remplace un module dans un slot
  replaceSlot(slotPath: string, moduleId: string): CompositionBuilder;
  
  // Active/désactive un slot optionnel
  toggleSlot(slotPath: string, enabled: boolean): CompositionBuilder;
  
  // Définit les variables
  setVariable(name: string, value: any): CompositionBuilder;
  setVariables(vars: Record<string, any>): CompositionBuilder;
  
  // Ajoute des enfants à un slot répétable
  addToSlot(slotPath: string, moduleId: string): CompositionBuilder;
  removeFromSlot(slotPath: string, index: number): CompositionBuilder;
  
  // Applique un thème
  applyTheme(themeId: string): CompositionBuilder;
  
  // Valide et build
  validate(): ValidationResult;
  build(): ComposedModule;
}

// Exemple d'utilisation
const landing = composer
  .fromTemplate("ModuleTemplate.SaaSLanding")
  .setVariables({
    brand_name: "EURKAI",
    primary_cta: { text: "Démarrer", url: "/signup" }
  })
  .replaceSlot("main.hero", "Module.Section.HeroSplit")
  .toggleSlot("main.how_it_works", true)
  .toggleSlot("main.faq", false)
  .applyTheme("theme_modern_dark")
  .build();
```

---

## 7. Intégration avec I1

### 7.1 Flux I1 → I2

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     I1 ←→ I2 INTEGRATION                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  I1: ProjectGenerator                    I2: ModuleCatalog              │
│  ───────────────────                     ─────────────────              │
│                                                                          │
│  1. Parse Brief                                                          │
│     ↓                                                                    │
│  2. Analyze Intent ─────────────────────► 3. Query Catalog              │
│     │                                         ↓                         │
│     │                                     4. Match Modules              │
│     │                                         ↓                         │
│     │                                     5. Score & Rank               │
│     │                                         ↓                         │
│  6. Receive Suggestions ◄─────────────── 7. Return Candidates          │
│     ↓                                                                    │
│  8. Map to ObjectDiffs                                                   │
│     ↓                                                                    │
│  9. Build Skeleton ─────────────────────► 10. Resolve Templates         │
│     │                                          ↓                        │
│     │                                     11. Compose Modules           │
│     │                                          ↓                        │
│  12. Receive Structure ◄────────────────  13. Return Composed          │
│     ↓                                                                    │
│  14. Generate FractalDiff                                               │
│     ↓                                                                    │
│  15. Return to H2/H3                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Interface I1 → I2

```typescript
// Service exposé par I2 pour I1
interface I2ModuleService {
  /**
   * Suggère des modules pour un intent détecté
   */
  suggestModules(request: ModuleSuggestionRequest): Promise<ModuleSuggestionResponse>;
  
  /**
   * Résout un template en structure de modules
   */
  resolveTemplate(request: TemplateResolutionRequest): Promise<ResolvedTemplate>;
  
  /**
   * Compose des modules selon une structure
   */
  composeModules(request: CompositionRequest): Promise<ComposedModuleTree>;
  
  /**
   * Valide une composition avant génération du diff
   */
  validateComposition(tree: ComposedModuleTree): Promise<CompositionValidation>;
}

interface ModuleSuggestionRequest {
  intent: DetectedIntent;
  context: I1Context;
  constraints?: {
    max_results?: number;
    preferred_types?: string[];
    excluded_types?: string[];
  };
}

interface ModuleSuggestionResponse {
  suggestions: SuggestedModule[];
  alternatives: Map<string, SuggestedModule[]>;
  template_matches: TemplateMatch[];
}

interface SuggestedModule {
  module_oid: string;
  module_type: string;
  score: number;
  reasoning: string;
  slot_suggestion?: string;
  config_hints?: Record<string, any>;
}
```

### 7.3 Génération de FractalDiff pour modules

```yaml
# Mapping Module → ObjectDiff
module_diff_mapping:
  Module.Section.Hero:
    generates:
      - operation: create
        object_type: Section
        attributes_from:
          - module.identity.*
          - module.definition.props.*
        children_from:
          - module.definition.slots.*
          
  Module.Page.Landing:
    generates:
      - operation: create
        object_type: Page
        attributes_from:
          - module.identity.*
        children:
          - for_each: module.structure.root.children
            generate: ObjectDiff
            recursive: true
            
  Module.Template.*:
    generates:
      - operation: create
        object_type: Template
        expand_structure: true
        resolve_variables: true
```

---

## 8. Annexes

### 8.1 Catalogue initial (extrait)

```yaml
initial_catalog:
  # ─────────────────────────────────────────
  # SECTIONS
  # ─────────────────────────────────────────
  sections:
    - oid: mod_hero_centered
      type: Module.Section.Hero
      name: HeroCentered
      tags: [hero, centered, minimal]
      
    - oid: mod_hero_split
      type: Module.Section.Hero
      name: HeroSplit
      tags: [hero, split, image]
      
    - oid: mod_hero_video
      type: Module.Section.Hero
      name: HeroVideo
      tags: [hero, video, immersive]
      
    - oid: mod_features_grid
      type: Module.Section.Features
      name: FeatureGrid
      tags: [features, grid, icons]
      
    - oid: mod_features_alternating
      type: Module.Section.Features
      name: FeatureAlternating
      tags: [features, alternating, images]
      
    - oid: mod_pricing_3col
      type: Module.Section.Pricing
      name: Pricing3Column
      tags: [pricing, 3-tier, comparison]
      
    - oid: mod_testimonials_carousel
      type: Module.Section.Testimonials
      name: TestimonialCarousel
      tags: [testimonials, carousel, quotes]
      
    - oid: mod_faq_accordion
      type: Module.Section.FAQ
      name: FAQAccordion
      tags: [faq, accordion, expandable]
      
    - oid: mod_cta_split
      type: Module.Section.CTA
      name: CTASplit
      tags: [cta, split, form]

  # ─────────────────────────────────────────
  # COMPONENTS
  # ─────────────────────────────────────────
  components:
    - oid: mod_button_primary
      type: Module.Component.Button
      name: ButtonPrimary
      tags: [button, primary, cta]
      
    - oid: mod_card_feature
      type: Module.Component.Card
      name: FeatureCard
      tags: [card, feature, icon]
      
    - oid: mod_form_contact
      type: Module.Component.Form
      name: ContactForm
      tags: [form, contact, fields]

  # ─────────────────────────────────────────
  # TEMPLATES
  # ─────────────────────────────────────────
  templates:
    - oid: tpl_saas_landing
      type: ModuleTemplate.SaaSLanding
      name: SaaSLanding
      tags: [landing, saas, b2b, complete]
      
    - oid: tpl_ecommerce_home
      type: ModuleTemplate.EcommerceLanding
      name: EcommerceLanding
      tags: [landing, ecommerce, b2c, shop]
      
    - oid: tpl_agency_portfolio
      type: ModuleTemplate.AgencyPortfolio
      name: AgencyPortfolio
      tags: [landing, agency, portfolio, creative]
```

### 8.2 Schémas JSON complets

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://eurkai.io/schemas/module/v1",
  "title": "EURKAI Module",
  "type": "object",
  "required": ["identity", "context", "definition"],
  "properties": {
    "identity": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "oid": { "type": "string", "pattern": "^mod_[0-9A-Z]{26}$" },
        "type": { "type": "string", "pattern": "^Module\\.[A-Z][a-zA-Z.]*$" },
        "name": { "type": "string", "maxLength": 64 },
        "slug": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-z0-9.]+)?$" }
      }
    },
    "view": {
      "type": "object",
      "properties": {
        "display_name": { "$ref": "#/$defs/i18n_string" },
        "description": { "$ref": "#/$defs/i18n_text" },
        "icon": { "type": "string" },
        "tags": { "type": "array", "items": { "type": "string" }, "maxItems": 20 }
      }
    },
    "context": {
      "type": "object",
      "properties": {
        "domain": { "enum": ["web", "mobile", "email", "flow", "api", "cli", "universal"] },
        "platforms": { "type": "array", "items": { "type": "string" } },
        "audience": { "type": "array", "items": { "type": "string" } }
      }
    },
    "definition": {
      "type": "object",
      "properties": {
        "slots": { "type": "object", "additionalProperties": { "$ref": "#/$defs/slot_def" } },
        "props": { "type": "object", "additionalProperties": { "$ref": "#/$defs/prop_def" } },
        "bindings": { "type": "object" },
        "assets": { "type": "array", "items": { "$ref": "#/$defs/asset_def" } }
      }
    },
    "rules": { "type": "array", "items": { "$ref": "#/$defs/rule_def" } },
    "options": {
      "type": "object",
      "properties": {
        "variants": { "type": "object" },
        "themes": { "type": "array" },
        "feature_flags": { "type": "object" }
      }
    },
    "relations": {
      "type": "object",
      "properties": {
        "inherits_from": { "type": "string" },
        "depends_on": { "type": "array", "items": { "$ref": "#/$defs/dependency_ref" } }
      }
    }
  },
  "$defs": {
    "i18n_string": {
      "oneOf": [
        { "type": "string" },
        { "type": "object", "additionalProperties": { "type": "string" } }
      ]
    },
    "i18n_text": {
      "oneOf": [
        { "type": "string" },
        { "type": "object", "additionalProperties": { "type": "string" } }
      ]
    },
    "slot_def": {
      "type": "object",
      "properties": {
        "accepts": { "type": "array", "items": { "type": "string" } },
        "min_items": { "type": "integer", "minimum": 0 },
        "max_items": { "type": "integer", "minimum": 1 },
        "default_content": { "type": "string" }
      }
    },
    "prop_def": {
      "type": "object",
      "required": ["prop_type"],
      "properties": {
        "prop_type": { "type": "object" },
        "default": {},
        "required": { "type": "boolean" },
        "ui_hint": { "type": "string" }
      }
    },
    "asset_def": {
      "type": "object",
      "required": ["asset_type", "path"],
      "properties": {
        "asset_type": { "enum": ["style", "script", "image", "font", "data"] },
        "path": { "type": "string" },
        "inline": { "type": "boolean" }
      }
    },
    "rule_def": {
      "type": "object",
      "required": ["rule_id", "erk"],
      "properties": {
        "rule_id": { "type": "string" },
        "erk": { "type": "string" },
        "severity": { "enum": ["error", "warning", "info"] },
        "message": { "type": "string" }
      }
    },
    "dependency_ref": {
      "type": "object",
      "required": ["oid"],
      "properties": {
        "oid": { "type": "string" },
        "type": { "type": "string" },
        "version_constraint": { "type": "string" }
      }
    }
  }
}
```

### 8.3 Glossaire

| Terme | Définition |
|-------|------------|
| **Slot** | Emplacement nommé dans un module pour recevoir des enfants |
| **Prop** | Propriété configurable d'un module |
| **Binding** | Connexion entre une prop et une source de données |
| **Variant** | Version alternative d'un module avec overrides |
| **Template** | Structure pré-composée de modules |
| **Seed** | Données de base nécessaires à un module |
| **Style** | Ensemble de tokens visuels applicables |
| **Catalog** | Registre centralisé des modules disponibles |
| **Intent** | Intention détectée depuis un brief |
| **Score** | Note de pertinence d'un module pour un contexte |

### 8.4 Références

- **I1** : Génération de Projet depuis Brief
- **H2** : Spécification Super.orchestrate
- **H3** : Cockpit Diff & Validation
- **Catalogue EURKAI** : `/system/catalog/modules`
- **Templates** : `/system/catalog/templates`
- **Seeds** : `/system/catalog/seeds`

---

## Fin du document I2

**Prochaines étapes** :
- I3 : Clonage et versioning de projets
- I4 : Marketplace de modules
