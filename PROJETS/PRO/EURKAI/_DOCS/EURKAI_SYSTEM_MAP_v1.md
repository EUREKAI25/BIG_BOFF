# EURKAI — System Map v1.0
**2026-03-27 — Reference document. Do not add marketing language. Do not simplify.**

---

## PART 1 — SYSTEM RECAP

### A. INPUT LAYER

| Object | Module | Format | Description |
|---|---|---|---|
| `idea` | — | free text | Raw user intent, unstructured |
| `conversational_brief` | `conversational_brief` | guided conversation → JSON | LLM-assisted Q&A that produces a structured spec |
| `structured_brief` | — | dict | Explicit `{project_type, features, constraints, target}` |
| `brief` (text) | `ProjectDefinitionScenario.parse_brief()` | str | Keyword-parsed into ParsedBrief |

**Flow:** idea → conversational_brief → structured_brief → ParsedBrief

---

### B. ORCHESTRATION

| Object | Module | Role |
|---|---|---|
| `ProjectDefinitionScenario` | `project_orchestration` | brief → needs → plan → execute |
| `ParsedBrief` | `project_orchestration` | Typed output of brief parsing |
| `Need` | `project_orchestration` | Single identified project need |
| `ExecutionStep` | `project_orchestration` | One step: module_name + module_ref + inputs + dependencies |
| `ExecutionPlan` | `project_orchestration` | Ordered list of ExecutionSteps |
| `ProjectDefinition` | `project_orchestration` | brief + parsed + needs + plan |
| `NEED_MODULE_MAP` | `project_orchestration` | need → module_ref mapping table (extensible) |

**Not yet implemented:** `ProjectBuildScenario` (executes plan with real module wiring)

---

### C. DESIGN SYSTEM

#### Engines

| Module | Main Function | Input → Output |
|---|---|---|
| `visual_intent_engine` | `generate_visual_intent()` | brief → visual_intent (emotion, mood, archetype, typography_strategy, color_strategy…) |
| `design_dna_resolver` | `resolve()` | brief → DesignDNA (deterministic, zero-LLM) |
| `color_palette` | `generate_palette()` | visual_intent → palette (WCAG AA guaranteed) |
| `palette_generator` | `generate_palette()` | base_color + scenario → harmonic PaletteSet (mono/analog/complementary/triadic…) |
| `color_psychology_engine` | `get_color_recommendation()` | industry + values + tone → color palette |
| `design_plan` | `generate_design_plan()` | brief + visual_intent → DesignPlan |
| `visual_coherence_engine` | `run()` | visual_intent + palette + optional reference → coherence result (3 cases) |
| `design_exploration_engine` | `explore()` | DesignDNA → N design directions |
| `visual_decorators` | `generate_visual_decorators()` | visual_intent → decorative system |

#### Rendering

| Module | Main Function | Input → Output |
|---|---|---|
| `page_builder` | HTML renderer | project_name + palette + seed + brief → HTML page |
| `brand_generator` | `generate_brand_directions()` | brief + BrandDNA → 3 BrandDirection objects |
| `brand_identity` | `generate_brand_identity()` | brief + visual_intent + palette → complete identity system |
| `logo_generator` | `generate_concepts()` | LogoDNA → LogoOutput (SVG variants, Recraft v3) |
| `theme_generator` | `ThemeGenerator` | ThemePreset → CSS |
| `theme_composer` | `ThemeComposer` | brief/style → HarmonyRules + FontMatcher + ThemePreset |

#### Validation & Fix

| Module | Main Function | Input → Output |
|---|---|---|
| `design_validator` | `validate_layout()` | DesignPlan → ValidationResult (PASS/FAIL, score 0–100) |
| `vision_audit` | `audit_page()` | screenshots → AuditResult (readability, zones, issues) |
| `auto_fix_engine` | `run_correction_loop()` | HTML + AuditResult → patched HTML (iterative, max 3) |
| `design_learning` | `DesignLearning` | audit results → Pattern (preemptive corrections for next run) |
| `visual_consistency_validator` | `validate()` | assets → ValidationReport |
| `screenshot_capture` | `ScreenshotCapture` | URL → captures (Playwright, AUDIT_ZONES) |
| `pipeline_validator` | `PipelineValidator` | module contracts → PipelineValidationResult |

#### Catalog / Introspection

| Module | Main Function | Input → Output |
|---|---|---|
| `design_catalog` | `explore()` | category / type / name → catalog entries |

---

### D. DOCUMENT SYSTEM

All objects own their `render()` method. No adapter.

#### Base types (`document_base.py`)

| Type | Description |
|---|---|
| `DocumentIssuer` | Issuing entity (name, address, SIRET, VAT) |
| `DocumentClient` | Client entity |
| `DocumentLineItem` | Line item (description, qty, unit_price, vat_rate) |
| `DocumentPageHeader` | Header block |
| `DocumentPageFooter` | Footer block |
| `BankDetails` | Bank details (IBAN, BIC, bank_name) |
| `DeliveryInfo` | Delivery address + instructions |
| `render_business_doc()` | Shared HTML renderer (injection points: extra_blocks_before/after_totals) |

#### v1.0 — Visual Surface Objects

| Object | Description |
|---|---|
| `SheetDoc` | Generic sheet: invoice, quote, order, credit note. Auto-totals HT/TVA/TTC. |
| `EmailSignature` | HTML email signature. Inline styles, 2-column layout, social links, CTA. |
| `TextDoc` | Composable text document: heading/paragraph/callout/code/quote/bullets/footer. |
| `DashboardPage` | Backoffice page: sidebar nav + stat_cards + TableSection + CardGridSection + FiltersBar. |

#### v1.1 — Specialized Business Documents

| Object | Extra Blocks | Key Fields |
|---|---|---|
| `InvoiceDoc` | PO ref + payment terms + bank details + late payment clause | due_date, bank_details, purchase_order_ref |
| `QuoteDoc` | Validity callout + conditions + acceptance/signature block | validity_date, show_acceptance_block |
| `PurchaseOrderDoc` | Delivery block + order/supplier refs + confirmation block | delivery (DeliveryInfo), order_ref |

#### v1.1 — Template Objects (brand-wired factories)

| Object | Method | Output |
|---|---|---|
| `BrandDefinition` | `design_repr()` | Compact design JSON |
| `InvoiceTemplate` | `create()` / `generate_install_script()` | InvoiceDoc + runnable Python script |
| `QuoteTemplate` | `create()` / `generate_install_script()` | QuoteDoc + runnable Python script |
| `PurchaseOrderTemplate` | `create()` / `generate_install_script()` | PurchaseOrderDoc + runnable Python script |
| `TextDocTemplate` | `create()` / `generate_install_script()` | TextDoc + runnable Python script |
| `SheetDocTemplate` | `create()` / `generate_install_script()` | SheetDoc + runnable Python script |

---

### E. DASHBOARD SYSTEM

All contained in `document_objects.dashboard_widgets`.

#### Low-level data model

| Object | Fields | Role |
|---|---|---|
| `DataPoint` | label, value, dimension, series, meta, previous_value, unit | Atomic data unit |
| `DataSeries` | name, points, color | Named group of DataPoints |
| `auto_detect_type()` | points → VisualizationType | Mapping engine (time→line, stage→funnel, meta→table, multi-series→bar, ≤6→pie, >15→list, 1→kpi_card) |

#### Business data model (first-class)

| Object | Fields | Key Methods |
|---|---|---|
| `Metric` | name, value, unit, trend (up/down/neutral), trend_pct, trend_label, subtitle | `validate()`, `to_widget()`, `render()`, `test()` |
| `Dataset` | name, dimension, labels, values, series, meta_columns | `validate()`, `to_data_points()`, `to_widget()`, `render()`, `combine()`, `test()` |

#### Widget system

| Object | Role |
|---|---|
| `WidgetConfig` | title, subtitle, height, show_legend, show_labels, show_grid, unit, format, columns, max_items, color_scheme |
| `DashboardWidget` | Owns `render()` — dispatches to 7 viz types |
| `WidgetSection` | Multi-widget section with layout (grid/row/single) and design propagation |

#### Visualization types (7)

| Type | Rendering | Trigger |
|---|---|---|
| `kpi_card` | Trend ↑↓, format, unit | 1 data point |
| `line_chart` | SVG polyline, multi-series, area fill | dimension=time |
| `bar_chart` | SVG rects, grouped, value labels | multi-series category |
| `pie_chart` | SVG donut, % labels, right legend | ≤6 points, no series |
| `table` | thead/tbody, meta columns, zebra | points with meta |
| `list` | Rank + label + progress bar + value | >15 points |
| `funnel` | SVG trapezoids, conversion % + drop % | dimension=stage |

---

## PART 2 — CANONICAL NEEDS

These are the recognized needs in EURKAI. Each maps to a module chain.

| Need | Priority | Always? | Description |
|---|---|---|---|
| `design_system` | 1 | ✓ | Visual direction: palette, plan, decorators |
| `frontend` | 2 | ✓ | Public-facing HTML page(s) |
| `backoffice` | 3 | — | Admin dashboard: stats, tables, navigation |
| `analytics` | 4 | — | KPI cards, charts, datasets |
| `crm` | 5 | — | Lead management, pipeline, contact tracking |
| `documents` | 6 | — | Invoices, quotes, purchase orders, proposals |
| `email` | 7 | — | Transactional + marketing email, signatures |
| `payments` | 8 | — | Stripe checkout, subscriptions, invoicing |
| `auth` | 9 | — | User authentication, sessions |
| `api` | 10 | — | FastAPI endpoints, webhooks |
| `search` | 11 | — | Catalogue search, filters |
| `brand` | 12 | — | Logo, icons, typography, visual identity |
| `communication` | — | — | Email warming, outbound campaigns, marketing |

**Type inference rules:**

| Project Type | Auto-injected Needs |
|---|---|
| `saas` | backoffice, analytics, auth, payments |
| `ecommerce` | backoffice, payments, search, email |
| `startup` | email |
| `corporate` | email |
| `landing` | — |
| `portfolio` | — |
| `blog` | email |

---

## PART 3 — NEED → MODULE CHAINS

Each need maps to an ordered sequence of module calls, not a single module.

---

### `design_system`
```
brief
  → visual_intent_engine.generate_visual_intent()        [direction, mood, archetype]
  → color_palette.generate_palette()                     [WCAG AA palette]
  → design_plan.generate_design_plan()                   [layout, hero, sections, CTA]
  → visual_decorators.generate_visual_decorators()       [decorative layer]
  → design_validator.validate_layout()                   [PASS/FAIL gate]
```
Optional upstream:
```
  → design_dna_resolver.resolve()                        [zero-LLM archetype inference]
  → design_exploration_engine.explore()                  [N direction alternatives]
```
Optional reference path:
```
  → visual_coherence_engine.run()                        [image↔palette, 3 cases]
```

---

### `frontend`
```
design_system output
  → page_builder (via design.render.page endpoint)       [HTML page]
  → screenshot_capture                                   [Playwright captures]
  → vision_audit                                         [readability score, issues]
  → auto_fix_engine (if score < 70)                      [patch CSS, max 3 iterations]
  → design_learning.preemptive_corrections()             [feed next run]
```

---

### `brand`
```
brief + design_system output
  → brand_identity.generate_brand_identity()             [brand_core, logo, typography, visual_signature]
  → logo_generator.generate_concepts()                   [LogoDNA → SVG variants]
  → brand_generator.generate_brand_directions()          [3 brand directions]
```

---

### `backoffice`
```
project context + design
  → DashboardPage(sections=[...])                        [full page with sidebar + header]
    ├── StatCard(...)                                     [KPI stats top bar]
    ├── TableSection(...)                                 [data table]
    ├── CardGridSection(...)                              [card grid]
    ├── FiltersBar(...)                                   [filters row]
    └── WidgetSection(widgets=[...])                      [chart/viz widgets]
  → DashboardPage.render()                               [HTML output]
```

---

### `analytics`
```
raw data (labels + values)
  → Dataset.to_data_points()                             [DataPoint list]
  → auto_detect_type()                                   [viz type selection]
  → DashboardWidget.render()                             [SVG/CSS chart HTML]
  → WidgetSection._render(design)                        [section with design propagation]
```
Or via business layer:
```
  → Metric(name, value, unit, trend, trend_pct)
  → Metric.to_widget()                                   [DashboardWidget kpi_card]
  → Metric.render()                                      [HTML]
```

---

### `documents`
```
BrandDefinition + issuer + client + items
  → InvoiceTemplate.create()    or InvoiceDoc(input)
  → InvoiceDoc.validate()
  → InvoiceDoc.render()                                  [printable HTML]

  → QuoteTemplate.create()      or QuoteDoc(input)
  → QuoteDoc.render()                                    [HTML with signature block]

  → PurchaseOrderDoc(input)
  → PurchaseOrderDoc.render()                            [HTML with delivery block]

  → TextDoc(blocks=[...])
  → TextDoc.render()                                     [HTML proposal / spec]
```

---

### `email`
```
brand + contact info
  → EmailSignature(input)
  → EmailSignature.render()                              [HTML email signature]
  → EmailSignature.render_full()                         [standalone HTML file]
```
Outbound:
```
  → OUTBOUND_EMAIL_MODULE.execute_send_batch()
  → EMAIL_WARMING_MODULE.WarmingEngine
  → MARKETING_MODULE (FastAPI /mkt)
```

---

### `payments`
*(module not yet implemented — placeholder in NEED_MODULE_MAP)*
```
  → payments.stripe_integration                          [to build]
```

---

### `auth`
*(module not yet implemented — placeholder in NEED_MODULE_MAP)*
```
  → auth.user_auth                                       [to build]
```

---

### `api`
*(module not yet implemented — placeholder in NEED_MODULE_MAP)*
```
  → api.fastapi_app                                      [to build]
```

---

### `communication`
```
  → MARKETING_MODULE (campaigns, scheduling, CRM webhooks)
  → OUTBOUND_EMAIL_MODULE (compliance, warmup, batch)
  → EMAIL_WARMING_MODULE (pool management, session tracking)
```

---

## PART 4 — CORE PIPELINES

### Pipeline 1 — `idea_to_brief`

**Input:** free text idea (str)
**Output:** structured brief (dict)

| Step | Module | Action |
|---|---|---|
| 1 | `conversational_brief` | LLM-guided Q&A with checklist |
| 2 | `conversational_brief.extract_spec()` | Extract structured JSON from conversation |
| 3 | — | Produce: `{project_type, features, constraints, target, name}` |

---

### Pipeline 2 — `brief_to_project_definition`

**Input:** brief (str or dict)
**Output:** `ProjectDefinition`

| Step | Module | Action |
|---|---|---|
| 1 | `ProjectDefinitionScenario.parse_brief()` | Extract project_type, features, constraints, target |
| 2 | `ProjectDefinitionScenario.identify_needs()` | Produce prioritized Need list (always + feature + type) |
| 3 | `ProjectDefinitionScenario.map_needs()` | Map each Need to ExecutionStep via NEED_MODULE_MAP |
| 4 | `ProjectDefinitionScenario.build_plan()` | Assemble ExecutionPlan |

---

### Pipeline 3 — `project_definition_to_execution_plan`

**Input:** `ProjectDefinition`
**Output:** ordered `ExecutionPlan` with concrete module refs

| Step | Module | Action |
|---|---|---|
| 1 | `NEED_MODULE_MAP` lookup | Resolve module_ref for each Need |
| 2 | Dependency wiring | Linear chain: each step depends on previous |
| 3 | Input declaration | Declare input keys per step (resolved at runtime) |
| 4 | Plan validation | `pipeline_validator` checks contract conformance |

---

### Pipeline 4 — `execution_plan_to_deliverables`

**Input:** `ExecutionPlan` + context `{brief, project_name, seed}`
**Output:** deliverables by need type

| Step | Need | Deliverable |
|---|---|---|
| 1 | `design_system` | visual_intent + palette + design_plan |
| 2 | `frontend` | `landing_page.html` |
| 3 | `brand` | brand_identity (logo, typography, visual_signature) |
| 4 | `backoffice` | `dashboard.html` |
| 5 | `analytics` | Widget HTML blocks |
| 6 | `documents` | `invoice.html` / `quote.html` / `purchase_order.html` |
| 7 | `email` | `email_signature.html` |

Each step:
- calls its module chain
- receives outputs from upstream steps via context propagation
- appends to results dict + trace

---

### Pipeline 5 — `deliverables_to_deployment` *(basic)*

**Input:** deliverables dict (HTML files + assets)
**Output:** deployment-ready package

| Step | Module | Action |
|---|---|---|
| 1 | — | Collect HTML files by type |
| 2 | `screenshot_capture` | Capture all pages |
| 3 | `vision_audit` | Audit all pages |
| 4 | `auto_fix_engine` | Fix pages with score < 70 |
| 5 | — | Assemble output directory: `{project_name}/` |
| 6 | VPS deploy script | SSH push to `/opt/{project_name}` |

---

## PART 5 — MASTER FLOW

```
IDEA (free text)
  │
  ▼ [Pipeline 1 — idea_to_brief]
  │  conversational_brief → guided Q&A → structured spec
  │
BRIEF (structured dict)
  │
  ▼ [Pipeline 2 — brief_to_project_definition]
  │  parse_brief → identify_needs → map_needs → build_plan
  │
PROJECT DEFINITION
  │  ParsedBrief + [Need list] + ExecutionPlan
  │
  ▼ [Pipeline 3 — project_definition_to_execution_plan]
  │  NEED_MODULE_MAP lookup → dependency wiring → contract validation
  │
EXECUTION PLAN
  │  [ExecutionStep × N] with module_ref + inputs + dependencies
  │
  ▼ [Pipeline 4 — execution_plan_to_deliverables]
  │
  ├── design_system need
  │     visual_intent_engine → color_palette → design_plan → visual_decorators
  │
  ├── frontend need
  │     page_builder → screenshot_capture → vision_audit → auto_fix_engine
  │     → landing_page.html
  │
  ├── brand need
  │     brand_identity → logo_generator → brand_generator
  │     → identity assets
  │
  ├── backoffice need
  │     DashboardPage + WidgetSection + DashboardWidget
  │     → dashboard.html
  │
  ├── analytics need
  │     Dataset / Metric → DashboardWidget → WidgetSection
  │     → chart HTML blocks
  │
  ├── documents need
  │     InvoiceDoc / QuoteDoc / PurchaseOrderDoc / TextDoc
  │     → *.html documents
  │
  ├── email need
  │     EmailSignature → email_signature.html
  │
  └── [future: payments / auth / api / crm]
  │
DELIVERABLES (multi-surface HTML)
  │
  ▼ [Pipeline 5 — deliverables_to_deployment]
  │  capture → audit → fix → package → deploy
  │
DEPLOYMENT-READY OUTPUT
  {project_name}/
    ├── landing_page.html
    ├── dashboard.html
    ├── invoice.html / quote.html / purchase_order.html
    ├── email_signature.html
    ├── brand/ (logo, colors, typography)
    └── captures/ (screenshots + audit results)
```

---

## PART 6 — SCENARIO STRUCTURE

### `ProjectDefinitionScenario` *(implemented — v1.0)*

**Role:** brief → definition. Upstream of all execution.

**Responsibilities:**
- Parse brief (text or structured dict) into `ParsedBrief`
- Identify `Need` list (always-on + feature-detected + type-inferred)
- Map needs to `ExecutionStep` via `NEED_MODULE_MAP`
- Assemble `ExecutionPlan`
- Call `execute()` which dispatches to registered or dynamically loaded modules

**Does NOT:**
- Implement any feature logic
- Render any output
- Know about specific business documents or design rules

**Extensibility points:**
- `NEED_MODULE_MAP` — add a key to support a new need
- `register_executor(module_ref, fn)` — inject real implementations (tests, agents)
- `_try_load()` — automatic dynamic discovery from `MODULES/`
- `dry_run=True` — plan without executing (for preview / approval)

**Future agents wired into this scenario:**
- `INTAKE_AGENT` — enriches brief before `parse_brief()`
- `ARCHITECT_AGENT` — validates or reorders `ExecutionPlan` before `execute()`

---

### `ProjectBuildScenario` *(not yet implemented)*

**Role:** execution_plan → deliverables. Downstream of `ProjectDefinitionScenario`.

**Responsibilities:**
- Receive a validated `ExecutionPlan`
- Wire real module calls for each `ExecutionStep`
- Propagate context between steps (design → frontend → documents)
- Collect deliverables
- Handle partial failures (skip unimplemented modules, continue)
- Return complete output dict: `{deliverables, trace, status}`

**Key difference from `ProjectDefinitionScenario`:**

| | `ProjectDefinitionScenario` | `ProjectBuildScenario` |
|---|---|---|
| Input | brief | ExecutionPlan |
| Output | ExecutionPlan | deliverables |
| Knows modules? | No (refs only) | Yes (calls them) |
| LLM required? | No | Depends on modules |
| Deterministic? | Yes | Mostly (seed-controlled) |

**Implementation path:**
1. Replace `_executor_registry` with real module calls for each implemented need
2. Context propagation: `design_system` output → `frontend` + `documents` + `backoffice`
3. Failure mode: `failed` steps are logged but do not halt subsequent independent steps

---

### Separation rationale

`ProjectDefinitionScenario` is **declarative** — it answers: *what needs to be built and in what order.*

`ProjectBuildScenario` is **imperative** — it answers: *build it.*

Keeping them separate allows:
- Plan preview and human approval before execution
- Plan serialization (JSON) and replay
- Agent injection between phases
- Partial execution (build only `design_system` + `frontend`, skip the rest)

---

## PART 7 — EXISTING ENDPOINTS & SCENARIOS (Quick Reference)

### Design Endpoints (atomic, 12)

| Name | Engine | Input → Output |
|---|---|---|
| `design.visual_intent.generate` | visual_intent_engine | brief → visual_intent |
| `design.palette.generate` | color_palette | visual_intent → palette |
| `design.coherence.apply` | visual_coherence_engine | vi + palette + ref → coherence |
| `design.plan.generate` | design_plan | brief + vi → DesignPlan |
| `design.render.page` | page_builder | project_name + seed + palette → HTML |
| `design.capture.page` | screenshot_capture | url → captures |
| `design.audit.page` | vision_audit | captures → AuditResult |
| `design.fix.page` | auto_fix_engine | HTML + audit → patched HTML |
| `design.brand.generate` | brand_identity | brief + vi + palette → brand system |
| `design.logo.generate` | logo_generator | LogoDNA → SVG variants |
| `design.icons.generate` | brand_identity | vi + palette → icon set |
| `design.typography.generate` | brand_identity | vi + palette → typography system |

### Design Scenarios (composite, 8)

| Name | Steps | Notes |
|---|---|---|
| `design.page.generate_basic` | vi → palette → plan → render | No reference |
| `design.page.generate_from_image` | vi → palette (from image) → plan → render | CASE 1 |
| `design.page.generate_from_mockup` | coherence → vi → plan → render | CASE 3 |
| `design.page.generate_full` | vi → palette → coherence → plan → render → capture → audit | Full pipeline |
| `design.page.audit` | capture → audit → report | — |
| `design.page.fix` | audit → fix loop → output | Max 3 iterations |
| `design.brand.generate_full` | vi → brand → logo → icons → typography | — |
| `design.brand.generate_from_reference` | reference → coherence → brand | CASE 3 |

---

## STATUS — WHAT IS BUILT vs. WHAT REMAINS

### Built ✅

| Layer | What |
|---|---|
| Design pipeline | 12 endpoints + 8 scenarios — fully operational |
| Document system | 7 objects + 5 templates — `render()` on each |
| Dashboard system | DashboardPage + 7 viz types + Metric + Dataset |
| Orchestration | `ProjectDefinitionScenario` (parse → plan) |
| Brand system | brand_identity + logo_generator + palette/color engines |
| Email | EmailSignature + EMAIL_WARMING_MODULE + OUTBOUND + MARKETING |

### Wired to NEED_MODULE_MAP — not yet executed ⚠️

| Need | Module Ref | Status |
|---|---|---|
| `crm` | `crm.lead_management` | To build |
| `payments` | `payments.stripe_integration` | To build |
| `auth` | `auth.user_auth` | To build |
| `api` | `api.fastapi_app` | To build |

### Missing ❌

| What | Why it matters |
|---|---|
| `ProjectBuildScenario` | Gap between plan and actual execution with real modules |
| Context propagation wiring | design_system output → downstream modules (frontend/docs/dashboard) |
| FastAPI endpoints for document_objects | HTTP surface for invoices, widgets, signatures |
| Scenarios: `generate_invoice`, `generate_quote` | Reusable document generation pipelines |
| Demo page (all widgets) | Visual reference for dashboard system |
