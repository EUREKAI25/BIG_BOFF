# EURKAI — System Map v2.0
**2026-03-27 — Canonical reference. No marketing. No duplication.**

---

## PART 1 — SYSTEM MAP

### 1. Input Layer

| Object | Module | Format |
|---|---|---|
| `idea` | — | free text |
| `ConversationalBrief` | `conversational_brief` | guided Q&A → structured JSON spec |
| `structured_brief` | — | `{project_type, features, constraints, target, name}` |
| `ParsedBrief` | `project_orchestration` | typed output of `parse_brief()` |

**Objects:** `ParsedBrief`
**Modules:** `conversational_brief`
**Scenarios:** none at this layer — input only

---

### 2. Orchestration Layer

| Object | Module | Role |
|---|---|---|
| `Need` | `project_orchestration` | single identified project need with priority + source |
| `ExecutionStep` | `project_orchestration` | one module call: module_name + module_ref + inputs + dependencies |
| `ExecutionChain` | `project_orchestration` | ordered steps for one need |
| `ExecutionPlan` | `project_orchestration` | ordered chains across all needs |
| `ProjectDefinition` | `project_orchestration` | brief + parsed + needs + plan |
| `NEED_MODULE_MAP` | `project_orchestration` | canonical need → chain mapping table |

**Objects:** `Need`, `ExecutionStep`, `ExecutionChain`, `ExecutionPlan`, `ProjectDefinition`, `ParsedBrief`
**Modules:** `project_orchestration`
**Scenarios:** `ProjectDefinitionScenario`, `ProjectBuildScenario` *(to build)*

---

### 3. Design Layer

**Engines:**

| Module | Main Function | Input → Output |
|---|---|---|
| `visual_intent_engine` | `generate_visual_intent()` | brief → visual_intent |
| `design_dna_resolver` | `resolve()` | brief → DesignDNA (zero-LLM) |
| `color_palette` | `generate_palette()` | visual_intent → palette (WCAG AA) |
| `design_plan` | `generate_design_plan()` | brief + visual_intent → DesignPlan |
| `visual_coherence_engine` | `run()` | visual_intent + palette + reference → coherence |
| `visual_decorators` | `generate_visual_decorators()` | visual_intent → decorative layer |
| `design_exploration_engine` | `explore()` | DesignDNA → N design directions |
| `brand_identity` | `generate_brand_identity()` | brief + visual_intent + palette → full identity |
| `logo_generator` | `generate_concepts()` | LogoDNA → SVG variants |
| `page_builder` | HTML renderer | project_name + palette + seed + brief → HTML |
| `screenshot_capture` | `ScreenshotCapture` | URL → captures (Playwright) |
| `vision_audit` | `audit_page()` | captures → AuditResult (readability, zones, score) |
| `auto_fix_engine` | `run_correction_loop()` | HTML + AuditResult → patched HTML |
| `design_validator` | `validate_layout()` | DesignPlan → PASS/FAIL + score 0–100 |
| `design_learning` | `DesignLearning` | audit results → preemptive corrections |

**Objects:** `DesignDNA`, `VisualIntent`, `DesignPlan`, `BrandIdentity`, `AuditResult`, `LoopResult`
**Modules:** 15 listed above
**Endpoints (atomic):** 12 — `design.visual_intent.generate`, `design.palette.generate`, `design.coherence.apply`, `design.plan.generate`, `design.render.page`, `design.capture.page`, `design.audit.page`, `design.fix.page`, `design.brand.generate`, `design.logo.generate`, `design.icons.generate`, `design.typography.generate`
**Scenarios (composite):** 8 — `design.page.generate_basic/from_image/from_mockup/full`, `design.page.audit`, `design.page.fix`, `design.brand.generate_full/from_reference`

---

### 4. Document Layer

All objects own their `render()` method. No adapter.

**Base types (`document_base`):**
`DocumentIssuer`, `DocumentClient`, `DocumentLineItem`, `DocumentPageHeader`, `DocumentPageFooter`, `BankDetails`, `DeliveryInfo`, `render_business_doc()`

**Surface objects (v1.0):**

| Object | Output |
|---|---|
| `SheetDoc` | generic sheet — invoice / quote / order / credit note |
| `EmailSignature` | HTML email signature, inline styles, 2-column |
| `TextDoc` | composable doc — heading / paragraph / callout / code / quote |
| `DashboardPage` | backoffice page — sidebar + stat_cards + sections |

**Specialized business documents (v1.1):**

| Object | Specific blocks |
|---|---|
| `InvoiceDoc` | PO ref + payment terms + bank details + late payment clause |
| `QuoteDoc` | validity callout + conditions + acceptance/signature block |
| `PurchaseOrderDoc` | delivery block + order/supplier refs + confirmation block |

**Template factories (v1.1):** `BrandDefinition`, `InvoiceTemplate`, `QuoteTemplate`, `PurchaseOrderTemplate`, `TextDocTemplate`, `SheetDocTemplate`
Each exposes `create()` and `generate_install_script()`.

**Objects:** all above
**Module:** `document_objects`
**Scenarios:** none yet — `generate_invoice`, `generate_quote` to build

---

### 5. Dashboard Layer

All in `document_objects.dashboard_widgets`.

**Low-level data:**

| Object | Role |
|---|---|
| `DataPoint` | atomic unit: label, value, dimension, series, meta, previous_value |
| `DataSeries` | named group of DataPoints with optional color |
| `auto_detect_type()` | data → viz type (time→line, stage→funnel, meta→table, multi-series→bar, ≤6→pie, >15→list, 1→kpi_card) |

**Business data (first-class):**

| Object | Key methods |
|---|---|
| `Metric` | `validate()`, `to_widget()`, `render()` — single KPI with explicit trend |
| `Dataset` | `validate()`, `to_data_points()`, `to_widget()`, `render()`, `combine()` |

**Widget system:**

| Object | Role |
|---|---|
| `WidgetConfig` | title, subtitle, height, format, unit, show_legend, columns |
| `DashboardWidget` | owns `render()` — dispatches to 7 viz types |
| `WidgetSection` | multi-widget container with layout + design propagation |

**Visualization types:**

| Type | Trigger | Rendering |
|---|---|---|
| `kpi_card` | 1 data point | trend ↑↓, format, unit |
| `line_chart` | dimension=time | SVG polyline, multi-series, area fill |
| `bar_chart` | multi-series category | SVG grouped rects + labels |
| `pie_chart` | ≤6 points, no series | SVG donut + % labels |
| `table` | points with meta | thead/tbody, zebra |
| `list` | >15 points | rank + label + progress bar |
| `funnel` | dimension=stage | SVG trapezoids + conversion % |

**Objects:** all above
**Module:** `document_objects` (dashboard_widgets.py)
**Scenarios:** none yet

---

## PART 2 — CANONICAL NEEDS

| Need | Priority | Always? | Description |
|---|---|---|---|
| `design_system` | 1 | ✓ | Visual direction: palette + plan + decorators |
| `frontend` | 2 | ✓ | Public-facing HTML page |
| `backoffice` | 3 | — | Admin dashboard: stats, tables, charts |
| `analytics` | 4 | — | KPI cards, charts, datasets |
| `documents` | 5 | — | Invoices, quotes, purchase orders, proposals |
| `email` | 6 | — | Signatures, transactional, campaigns |
| `crm` | 7 | — | Lead management, pipeline, contact tracking |
| `payments` | 8 | — | Stripe checkout, subscriptions |
| `auth` | 9 | — | User authentication, sessions |
| `api` | 10 | — | FastAPI endpoints, webhooks |
| `search` | 11 | — | Catalogue search, filters |
| `brand` | 12 | — | Logo, icons, typography, visual identity |
| `communication` | 13 | — | Warming, outbound campaigns, automation |

**Type inference (auto-inject based on project_type):**

| project_type | Injected needs |
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

Each need maps to an ordered chain. Outputs of earlier steps are passed as inputs to later steps within the same chain.

---

### `design_system`
```
1. visual_intent_engine.generate_visual_intent()     brief → visual_intent
2. color_palette.generate_palette()                  visual_intent → palette
3. design_plan.generate_design_plan()                brief + visual_intent → DesignPlan
4. visual_decorators.generate_visual_decorators()    visual_intent → decorators
5. design_validator.validate_layout()                DesignPlan → PASS/FAIL
```
Optional path (with reference image):
```
   visual_coherence_engine.run()                     between steps 2 and 3
```
Output propagated to: `frontend`, `backoffice`, `analytics`, `documents`, `email`, `brand`

---

### `frontend`
```
1. page_builder (design.render.page)                 brief + palette + seed → HTML
2. screenshot_capture                                HTML → captures
3. vision_audit                                      captures → AuditResult
4. auto_fix_engine (if score < 70)                   HTML + audit → patched HTML (max 3 iter.)
5. design_learning                                   audit → preemptive corrections for next run
```
Depends on: `design_system`

---

### `brand`
```
1. brand_identity.generate_brand_identity()          brief + visual_intent + palette → identity
2. logo_generator.generate_concepts()                LogoDNA → SVG concepts
3. logo_generator.export_variants()                  concept → 5 SVG variants
```
Depends on: `design_system`

---

### `backoffice`
```
1. DashboardPage(sections=[...])
   ├── StatCard(...)                                 KPI stats row
   ├── TableSection(...)                             data table
   ├── CardGridSection(...)                          card grid
   ├── FiltersBar(...)                               filters
   └── WidgetSection(widgets=[...])                  chart widgets
2. DashboardPage.render()                            → HTML
```
Depends on: `design_system`

---

### `analytics`
```
Via Dataset:
1. Dataset(name, dimension, labels, values)
2. Dataset.to_data_points()                          → [DataPoint]
3. auto_detect_type()                                → VisualizationType
4. DashboardWidget(type, data, config, design)
5. DashboardWidget.render()                          → chart HTML

Via Metric:
1. Metric(name, value, unit, trend, trend_pct)
2. Metric.to_widget()                                → DashboardWidget (kpi_card)
3. Metric.render()                                   → HTML
```
Depends on: `design_system`

---

### `documents`
```
With template:
1. BrandDefinition(name, design, issuer, ...)
2. InvoiceTemplate.create(client, items, ...)        → InvoiceDoc
3. InvoiceDoc.validate()
4. InvoiceDoc.render()                               → printable HTML

Without template (direct):
1. InvoiceDoc(input)  /  QuoteDoc(input)  /  PurchaseOrderDoc(input)  /  TextDoc(blocks)
2. [Doc].validate()
3. [Doc].render()                                    → HTML
```
Depends on: `design_system` (for brand design injection)

---

### `email`
```
Signature:
1. EmailSignature(input)
2. EmailSignature.render_full()                      → standalone HTML

Campaigns:
1. OUTBOUND_EMAIL_MODULE.execute_send_batch()
2. EMAIL_WARMING_MODULE.WarmingEngine
3. MARKETING_MODULE FastAPI /mkt
```
Depends on: `design_system`, `brand`

---

### `crm`
```
[Not yet implemented]
Module ref: crm.lead_management
```

---

### `payments`
```
[Not yet implemented]
Module ref: payments.stripe_integration
```

---

### `auth`
```
[Not yet implemented]
Module ref: auth.user_auth
```

---

### `api`
```
[Not yet implemented]
Module ref: api.fastapi_app
```

---

### `search`
```
[Not yet implemented]
Module ref: search.catalogue_search
```

---

### `communication`
```
1. MARKETING_MODULE     campaigns, scheduling, CRM webhooks
2. OUTBOUND_EMAIL_MODULE  compliance, warmup progression, batch send
3. EMAIL_WARMING_MODULE   pool management, bidirectional warming
```

---

## PART 4 — CORE PIPELINES

### Pipeline 1 — `idea_to_brief`

**Input:** free text idea
**Output:** structured brief `{project_type, features, constraints, target, name}`

| Step | Module | Action |
|---|---|---|
| 1 | `conversational_brief` | guided Q&A from checklist |
| 2 | `conversational_brief.extract_spec()` | extract structured JSON from conversation |

---

### Pipeline 2 — `brief_to_project_definition`

**Input:** brief (str or dict)
**Output:** `ProjectDefinition`

| Step | Module | Action |
|---|---|---|
| 1 | `ProjectDefinitionScenario.parse_brief()` | extract project_type, features, constraints, target |
| 2 | `ProjectDefinitionScenario.identify_needs()` | produce prioritized Need list |
| 3 | `ProjectDefinitionScenario.map_needs()` | map each Need → ExecutionChain via NEED_MODULE_MAP |
| 4 | `ProjectDefinitionScenario.build_plan()` | assemble ExecutionPlan |

---

### Pipeline 3 — `project_definition_to_execution_plan`

**Input:** `ProjectDefinition`
**Output:** validated `ExecutionPlan`

| Step | Module | Action |
|---|---|---|
| 1 | `NEED_MODULE_MAP` lookup | resolve module chain for each Need |
| 2 | dependency resolution | declare cross-chain dependencies |
| 3 | input declaration | declare input keys per step (resolved at runtime from context) |
| 4 | `pipeline_validator` | check module contract conformance |

---

### Pipeline 4 — `execution_plan_to_deliverables`

**Input:** `ExecutionPlan` + context `{brief, project_name, seed}`
**Output:** deliverables by need

| Chain | Need | Deliverable |
|---|---|---|
| 1 | `design_system` | visual_intent + palette + design_plan |
| 2 | `frontend` | `landing_page.html` |
| 3 | `brand` | logo SVG + typography + visual identity |
| 4 | `backoffice` | `dashboard.html` |
| 5 | `analytics` | chart HTML blocks |
| 6 | `documents` | `invoice.html` / `quote.html` / `purchase_order.html` |
| 7 | `email` | `email_signature.html` |

Context propagation: `design_system` output (visual_intent + palette + design_plan) is injected into all downstream chains.

---

### Pipeline 5 — `deliverables_to_deployment`

**Input:** deliverables dict (HTML + assets)
**Output:** deployment-ready package in `{project_name}/`

| Step | Module | Action |
|---|---|---|
| 1 | `screenshot_capture` | capture all pages |
| 2 | `vision_audit` | audit all pages |
| 3 | `auto_fix_engine` | fix pages with score < 70 |
| 4 | — | assemble output directory |
| 5 | VPS deploy script | SSH push to `/opt/{project_name}` |

---

## PART 5 — MASTER FLOW

```
IDEA
  │
  ▼  [Pipeline 1]
BRIEF  ←  conversational_brief  ←  guided Q&A
  │
  ▼  [Pipeline 2]
PROJECT DEFINITION
  ParsedBrief  +  [Need ×N]  +  ExecutionPlan
  │
  ▼  [Pipeline 3]
EXECUTION PLAN
  [ExecutionChain ×N]
    each chain = [ExecutionStep ×M]
    each step  = module_ref + inputs + dependencies
  │
  ▼  [Pipeline 4]
  │
  ├── design_system chain
  │     visual_intent → palette → design_plan → decorators
  │     output: {visual_intent, palette, design_plan}
  │              ↓ propagated to all chains below
  │
  ├── frontend chain
  │     page_builder → capture → audit → fix
  │     output: landing_page.html
  │
  ├── brand chain
  │     brand_identity → logo_generator
  │     output: logo SVGs + typography + identity
  │
  ├── backoffice chain
  │     DashboardPage + WidgetSection + DashboardWidget
  │     output: dashboard.html
  │
  ├── analytics chain
  │     Dataset/Metric → DashboardWidget → WidgetSection
  │     output: chart HTML blocks
  │
  ├── documents chain
  │     BrandDefinition + InvoiceDoc/QuoteDoc/TextDoc
  │     output: invoice.html, quote.html, proposal.html
  │
  ├── email chain
  │     EmailSignature
  │     output: email_signature.html
  │
  └── [future: payments / auth / api / crm / search]
  │
DELIVERABLES
  {landing_page, dashboard, documents, signature, brand assets}
  │
  ▼  [Pipeline 5]
DEPLOYMENT-READY OUTPUT
  {project_name}/
    landing_page.html
    dashboard.html
    invoice.html / quote.html
    email_signature.html
    brand/ (logo, colors, typography)
    captures/ (screenshots + audit)
```

---

## PART 6 — SCENARIO ROLES

### `ProjectDefinitionScenario`
**Role:** understanding + planning

- Parses brief → `ParsedBrief`
- Identifies needs → `[Need]`
- Maps needs to chains → `[ExecutionChain]`
- Assembles `ExecutionPlan`
- Runs `execute()` as shallow dispatch (calls module refs)

**Does NOT:** implement feature logic, render output, apply design rules.
**Knows:** which modules exist and what they need as input.
**Output:** `ProjectDefinition` + `ExecutionPlan` + trace.

---

### `ProjectBuildScenario`
**Role:** execution of module chains
**Status:** not yet implemented

- Receives a validated `ExecutionPlan`
- Iterates chains in priority order
- For each chain: iterates steps, calls modules, passes output forward
- Propagates `design_system` output into all downstream chains as shared context
- Collects deliverables per chain
- Handles partial failure: failed steps are logged, independent chains continue
- Returns `{deliverables, trace, status}`

**Does NOT:** parse briefs, identify needs, decide what to build.
**Knows:** how to call each module and wire outputs between steps.

---

### Separation rationale

| | `ProjectDefinitionScenario` | `ProjectBuildScenario` |
|---|---|---|
| Nature | declarative | imperative |
| Input | brief | ExecutionPlan |
| Output | ExecutionPlan | deliverables |
| Module knowledge | refs only | real calls |
| LLM required | no | depends on modules |
| Deterministic | yes | yes (seed-controlled) |
| Dry-run | yes | — |

Separation enables: plan preview before execution, plan serialization + replay, agent injection between phases, partial builds.

---

## PART 7 — EXECUTION MODEL

### Structure

```
ExecutionPlan
  chains: List[ExecutionChain]    ← one per need, ordered by priority

ExecutionChain
  need: str                       ← canonical need name
  steps: List[ExecutionStep]      ← ordered module calls within the chain
  dependencies: List[str]         ← other chains that must complete first
  outputs: Dict[str, Any]         ← collected outputs after execution

ExecutionStep
  order: int
  module_name: str                ← logical name (e.g. "visual_intent")
  module_ref: str                 ← callable path (e.g. "design_endpoints.design.visual_intent.generate")
  inputs: Dict[str, Any]          ← keys declared, values resolved at runtime
  dependencies: List[str]         ← steps within same chain that must complete first
  status: pending | running | done | skipped | failed
  output: Any
```

### Execution loop

```
for chain in plan.chains (ordered by priority):
    if chain.dependencies not all done → skip or defer

    context = shared_context + outputs from dependency chains

    for step in chain.steps:
        inputs = resolve(step.input_keys, context, chain.outputs)
        output = call(step.module_ref, **inputs)
        chain.outputs[step.module_name] = output
        context.update(output)   ← makes output available to next step

    deliverables[chain.need] = chain.outputs
```

### Context propagation rules

| Source | Propagates to |
|---|---|
| `design_system` output | all chains (shared design context) |
| `frontend` output | `deliverables.landing_page` |
| `backoffice` output | `deliverables.dashboard` |
| `documents` output | `deliverables.documents` |
| Each chain output | next steps within same chain |

### Failure handling

| Failure type | Behavior |
|---|---|
| Step fails | mark `failed`, log error, continue chain if remaining steps don't depend on it |
| Chain fails | mark chain `failed`, skip dependent chains, continue independent ones |
| Module not found | mark step `skipped`, continue |
| `dry_run=True` | skip all execution, return plan only |

### Input resolution order

```
1. shared context (brief, project_name, seed, design)
2. outputs from dependency chains
3. outputs from previous steps in same chain
4. declared defaults in NEED_MODULE_MAP
5. omit (module must handle missing optional inputs)
```
