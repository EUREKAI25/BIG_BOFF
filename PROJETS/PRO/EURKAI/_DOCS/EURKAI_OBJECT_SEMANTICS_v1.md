# EURKAI — Object Semantics & Catalog v1.0
**2026-03-28 — Foundational reference. Strict. No ambiguity. No overlap.**

---

## PART 1 — STRICT DEFINITIONS

### Schema

**Definition:**
Defines the ontology of an object — its nature, attributes, relationships, and composition rules.
A schema answers: *what kind of thing is this, what can it contain, and how are its parts related?*

**Role:** Structural authority. Governs what is valid and what is not.

**Contains:**
- Attribute declarations (name, type, optionality)
- Composition rules (which sub-objects a schema admits)
- Relationship declarations (parent/child, ordered/unordered)
- Constraints (cardinality, exclusions, co-dependencies)

**Must NOT contain:**
- Values or defaults
- Layout or placement logic
- Rendering instructions
- Instance data

**Relation to others:**
Schema is the foundation. Template, Seed, Manifest, and Instance are all produced within the constraints the schema defines. Nothing outside the schema space is valid.

---

### Template

**Definition:**
Defines the placement matrix of an object's components — how and where structural elements are arranged relative to each other.
A template answers: *where does each component live in the composition?*

**Role:** Spatial authority. Governs arrangement, not content.

**Contains:**
- Named placement zones (hero, sidebar, header, body, footer…)
- Slot declarations and their order
- Layout variants (e.g. split, stacked, grid, single-column)
- Composition modes (zones that are mandatory vs. optional in this arrangement)

**Must NOT contain:**
- Values, defaults, or configuration
- Rendering styles or visual parameters
- Instance data
- Schema rules

**Relation to others:**
Template operates within the schema (only schema-declared components can be placed). Template is consumed by Manifest to resolve *where* each value goes. Multiple templates can exist for one schema.

---

### Seed

**Definition:**
The canonical initial configuration of an object within the schema space — default parameter values only, with no structure, no children, and no ontology.
A seed answers: *what are the sensible defaults for this object?*

**Role:** Default authority. Provides the starting point for configuration.

**Contains:**
- Default values for scalar parameters declared in the schema
- Enumerated choices (e.g. `cta_strategy: repeated`)
- Numeric defaults (e.g. `density: low`, `section_count: 4`)

**Must NOT contain:**
- Structure or composition rules
- Child object definitions
- Layout or placement logic
- Resolved or contextual values

**Relation to others:**
Seed is a point in the schema parameter space. It is one possible input to the Manifest resolution process. A Manifest may override any or all seed values.

---

### Manifest

**Definition:**
The fully resolved, concrete configuration of a specific object instance — the complete specification before production.
A manifest answers: *what, exactly, will be produced?*

**Role:** Resolution authority. Bridges schema/template/seed/context into a deployable specification.

**Contains:**
- All resolved parameter values (from seed + context overrides)
- Selected template reference
- Resolved component configuration (one level, no recursion)
- Provenance metadata (which seed, which template, which context were used)

**Must NOT contain:**
- Abstract structural definitions (that is the schema's role)
- Unresolved placeholders or conditionals
- Rendered output

**Relation to others:**
```
manifest = resolve(schema, template, seed, context)
```
Manifest is the final input to instantiation. Every field must be resolved. No manifest → no instance.

---

### Instance

**Definition:**
The final produced object — the concrete artifact resulting from instantiating a manifest.
An instance answers: *what was built?*

**Role:** Production authority. Immutable output.

**Contains:**
- The rendered artifact (HTML, JSON, PDF-ready, SVG…)
- Provenance reference (manifest ID or hash)
- Production metadata (timestamp, version, scenario name)

**Must NOT contain:**
- Unresolved parameters
- Schema or template logic
- Mutable state

**Relation to others:**
```
instance = instantiate(schema, manifest)
```
Instance is the terminal node. It cannot be further configured — only replaced by a new instance with a different manifest.

---

## PART 2 — ANTI-CONFUSION RULES

### Responsibility split

| Object | Single responsibility |
|---|---|
| Schema | Structure and composition — *what can exist* |
| Template | Placement — *where components live* |
| Seed | Default parameters — *starting values only* |
| Manifest | Resolved configuration — *exact specification* |
| Instance | Produced artifact — *the thing itself* |

### Seed

**Seed handles default parameter selection ONLY.**

Seed MUST NOT:
- Define structure or composition (that is the schema's role)
- Declare child components or sub-objects
- Duplicate attribute definitions already in the schema
- Contain layout or placement logic (that is the template's role)
- Contain resolved contextual data (that is the manifest's role)

A seed that declares `sections: [hero, features, cta]` is wrong — it is defining structure. The correct seed declares `section_count: 3` if that is a tunable parameter, or declares nothing if sections are structurally fixed by the schema.

### Template

**Template handles placement ONLY.**

Template MUST NOT:
- Be treated as configuration (template is not a config file)
- Be treated as a seed (template has no values, only slot declarations)
- Define the ontology of its components (that is the schema's role)
- Contain styling or visual parameters (those belong in manifest)

A template that says `hero_background: dark_gradient` is wrong — it is acting as configuration. The correct template says `zone: hero, position: top, full-width: true`.

### Schema vs. Manifest

Schema is abstract and permanent. Manifest is concrete and specific.
Schema defines that `invoice.issuer` is a `DocumentIssuer`. Manifest defines that `invoice.issuer.name = "Acme Corp"`.

---

## PART 3 — CATALOG

### `landing_page`

**Definition:** A single public-facing HTML page designed to produce a specific user action.

**Key question:** *What is the single action we want the user to take?*

| Layer | Role |
|---|---|
| **Schema** | Declares: hero section, nav, body sections (features, proof, pricing, FAQ), CTA block, footer. Composition rules: exactly one hero, 1–6 body sections, at least one CTA. |
| **Template** | Defines arrangement variant: `hero_split` (text left, visual right), `hero_centered` (full-width, text centered), `hero_overlay` (image background + overlay text). Declares zones: top_nav / hero / sections[] / sticky_cta / footer. |
| **Seed** | Default parameters: `hero_type: centered`, `density: low`, `cta_strategy: repeated`, `section_count: 4`, `tone: confident`. |
| **Manifest** | Resolved: brand palette + typography, project name, hero headline and subtext, CTA label and URL, section content and order, footer links. |
| **Instance** | HTML page. Self-contained. Inline CSS. Responsive. |

---

### `dashboard`

**Definition:** A data-driven admin interface enabling decisions based on aggregated metrics and tables.

**Key question:** *What decisions should this data enable?*

| Layer | Role |
|---|---|
| **Schema** | Declares: sidebar (nav), header (title, filters), stat card row, widget sections (charts, tables, funnels), action bar. DashboardPage contains: `NavItem`, `StatCard`, `TableSection`, `CardGridSection`, `FiltersBar`, `WidgetSection`. |
| **Template** | Defines arrangement: `sidebar_left` (fixed nav left, content right), `top_nav` (horizontal nav, full-width content), `focused` (no nav, single view). Zone map: sidebar / header / stats_row / body_grid / footer. |
| **Seed** | Default parameters: `layout: sidebar_left`, `stat_card_count: 4`, `default_chart_type: line_chart`, `density: medium`, `show_filters: true`. |
| **Manifest** | Resolved: brand design, navigation items + routes, metric definitions (name, value, trend), dataset definitions, table columns and data, filter options. |
| **Instance** | HTML page. Inline SVG charts. Responsive grid. |

---

### `graphic_chart`

**Definition:** The complete visual identity system of a project — palette, typography, spacing, logo rules, tone.

**Key question:** *What feeling must someone immediately associate with this brand?*

| Layer | Role |
|---|---|
| **Schema** | Declares: `VisualIntent` (emotion, mood, archetype), `Palette` (primary, background, accent, text), `Typography` (heading font, body font, scale), `LogoRules` (clearspace, variants), `SpacingSystem`, `ToneMarkers`. |
| **Template** | Defines charter document layout: title page / palette page / typography page / logo usage page / do-and-don't page. |
| **Seed** | Default parameters: `archetype: startup_clean`, `primary_hue_bias: cool`, `font_category: sans-serif`, `contrast_level: high`, `logo_style: wordmark`. |
| **Manifest** | Resolved: all hex values, specific font names, logo SVG references, spacing scale in px/rem, specific tone language examples. |
| **Instance** | Brand identity document (HTML) + exportable CSS variables + logo SVG variants. |

---

### `invoice_doc`

**Definition:** A formal commercial document recording a transaction and requesting payment.

**Key question:** *What transaction is being formalized, and when is payment due?*

| Layer | Role |
|---|---|
| **Schema** | Declares: `DocumentIssuer`, `DocumentClient`, `DocumentLineItem[]`, totals (HT, TVA, TTC), `BankDetails`, payment terms, optional PO reference, late payment clause. |
| **Template** | Defines document layout: header block (issuer + client + doc number + date) / line items table / totals block / payment block (bank + terms) / footer. |
| **Seed** | Default parameters: `currency: EUR`, `default_vat_rate: 20`, `payment_terms: "30 jours net"`, `show_bank_details: true`, `show_late_payment_clause: true`. |
| **Manifest** | Resolved: issuer identity (name, address, SIRET, VAT number), client identity, line items (description, qty, unit price, VAT rate), computed totals, bank details, due date, optional PO reference. |
| **Instance** | Printable HTML document. Auto-computed totals. Inline styles. Print-optimized. |

---

### `quote_doc`

**Definition:** A commercial offer proposing a price for defined services or goods, valid for a limited period.

**Key question:** *What is being proposed, at what price, and for how long is this offer valid?*

| Layer | Role |
|---|---|
| **Schema** | Declares: same base as invoice (`DocumentIssuer`, `DocumentClient`, `DocumentLineItem[]`, totals), plus `validity_date`, `conditions`, `acceptance_block` (signature zone). |
| **Template** | Defines layout: header / line items table / totals / validity callout / conditions / acceptance/signature grid. |
| **Seed** | Default parameters: `currency: EUR`, `default_vat_rate: 20`, `validity_days: 30`, `show_acceptance_block: true`. |
| **Manifest** | Resolved: all issuer/client/items fields (same as invoice), validity date, conditions text, acceptance block label. |
| **Instance** | Printable HTML. Includes signature zone. |

---

### `purchase_order_doc`

**Definition:** A formal document issued by a buyer to a supplier, authorizing a purchase.

**Key question:** *What is being ordered, from whom, and where should it be delivered by when?*

| Layer | Role |
|---|---|
| **Schema** | Declares: `DocumentIssuer` (buyer), `DocumentClient` (supplier), `DocumentLineItem[]`, totals, `DeliveryInfo` (address, date, contact, instructions), order reference, supplier reference, confirmation block. |
| **Template** | Defines layout: header (buyer + supplier + ref block) / delivery info block / line items table / totals / confirmation block. |
| **Seed** | Default parameters: `currency: EUR`, `default_vat_rate: 20`, `show_confirmation_block: true`, `show_delivery_info: true`. |
| **Manifest** | Resolved: all identity fields, line items, delivery address + date + instructions, order and supplier refs, confirmation block text. |
| **Instance** | Printable HTML. Delivery info clearly separated. |

---

### `text_doc`

**Definition:** A composable narrative document — proposal, specification, report, or client-facing brief.

**Key question:** *What must the reader understand and act on after reading this document?*

| Layer | Role |
|---|---|
| **Schema** | Declares: `title`, `subtitle`, `author`, `date`, `blocks[]` — each block is typed: `heading`, `paragraph`, `callout`, `code`, `quote`, `bullets`, `divider`, `footer`. |
| **Template** | Defines layout variant: `report` (left spine accent, numbered sections), `proposal` (cover header, body, signature), `brief` (compact, high-density). Zones: cover / body_blocks / footer. |
| **Seed** | Default parameters: `density: medium`, `default_block_types: [heading, paragraph, bullets]`, `show_page_numbers: true`, `tone: professional`. |
| **Manifest** | Resolved: title + author + date, all blocks with content, brand design (palette, font), selected template variant, footer content. |
| **Instance** | HTML document. Print-optimized. Inline styles. |

---

### `email_signature`

**Definition:** An HTML email footer block encoding professional identity and brand.

**Key question:** *What is the one action or impression this signature must leave?*

| Layer | Role |
|---|---|
| **Schema** | Declares: `name`, `title`, `company`, `email`, `phone`, `website`, optional `photo`, `social_links[]` (platform + url), optional `cta` (label + url), `brand_colors`. |
| **Template** | Defines layout: `two_column` (photo/logo left, info right), `stacked` (top logo, info below), `compact` (single line, minimal). Zones: identity_block / contact_block / social_block / cta_block. |
| **Seed** | Default parameters: `layout: two_column`, `show_photo: false`, `show_social: true`, `cta_style: pill`, `font_size: 13px`. |
| **Manifest** | Resolved: name, title, company, contact info, brand colors (primary, accent), social links, optional CTA label and URL, selected layout. |
| **Instance** | Inline-styled HTML. 600px max-width. Email-client compatible (no external CSS). |

---

## PART 4 — KEY QUESTIONS (SUMMARY)

Every object in the EURKAI catalog must carry a key question. This question is mandatory — it defines the object's purpose and must be answered before any manifest is produced.

| Object | Key question |
|---|---|
| `landing_page` | What is the single action we want the user to take? |
| `dashboard` | What decisions should this data enable? |
| `graphic_chart` | What feeling must someone immediately associate with this brand? |
| `invoice_doc` | What transaction is being formalized, and when is payment due? |
| `quote_doc` | What is being proposed, at what price, and for how long is this offer valid? |
| `purchase_order_doc` | What is being ordered, from whom, and where should it be delivered by when? |
| `text_doc` | What must the reader understand and act on after reading this document? |
| `email_signature` | What is the one action or impression this signature must leave? |

The key question is not decorative. It is the constraint that governs content decisions at manifest resolution time. If the manifest cannot be read as an answer to the key question, the manifest is incomplete.

---

## PART 5 — SEED CONTENT REFERENCE

Seeds contain default values only. No structure. No children.

### `landing_page.seed`
```
hero_type:       centered
density:         low
cta_strategy:    repeated
section_count:   4
tone:            confident
nav_style:       minimal
```

### `dashboard.seed`
```
layout:              sidebar_left
stat_card_count:     4
default_chart_type:  line_chart
density:             medium
show_filters:        true
table_row_count:     10
```

### `graphic_chart.seed`
```
archetype:         startup_clean
primary_hue_bias:  cool
font_category:     sans-serif
contrast_level:    high
logo_style:        wordmark
spacing_unit:      8px
```

### `invoice_doc.seed`
```
currency:                   EUR
default_vat_rate:           20
payment_terms:              30 jours net
show_bank_details:          true
show_late_payment_clause:   true
show_purchase_order_ref:    false
```

### `quote_doc.seed`
```
currency:               EUR
default_vat_rate:       20
validity_days:          30
show_acceptance_block:  true
```

### `purchase_order_doc.seed`
```
currency:                  EUR
default_vat_rate:          20
show_confirmation_block:   true
show_delivery_info:        true
```

### `text_doc.seed`
```
density:              medium
default_block_types:  [heading, paragraph, bullets]
show_page_numbers:    true
tone:                 professional
```

### `email_signature.seed`
```
layout:        two_column
show_photo:    false
show_social:   true
cta_style:     pill
font_size:     13px
```

---

## PART 6 — NAMING CONVENTIONS

### Canonical form

```
<object>.<layer>
```

| Name | Meaning |
|---|---|
| `landing_page.schema` | ontology of landing_page |
| `landing_page.template` | placement matrix for landing_page |
| `landing_page.seed` | default parameters for landing_page |
| `landing_page.manifest` | resolved specification for a specific landing_page |
| `landing_page.instance` | produced artifact |

### Named seed variants

```
landing_page.seed.minimal
landing_page.seed.dense
landing_page.seed.saas
```

These are valid. A named seed is a named point in the parameter space, not a different layer. The layer is still `seed`.

### `landing_page.seed.params`

**Valid.** `params` is a sub-namespace within the seed layer. It clarifies that the file contains parameter defaults specifically (as opposed to, say, `landing_page.seed.meta` for seed metadata). Preferred form remains `landing_page.seed` unless disambiguation is necessary.

### Invalid forms

| Invalid | Why |
|---|---|
| `landing_page.config` | config is not a canonical layer — use manifest |
| `landing_page.preset` | preset is ambiguous — use seed or named seed variant |
| `landing_page.schema.template` | layers cannot be nested |
| `template.landing_page` | layer is always the suffix, not the prefix |

---

## PART 7 — FINAL MODEL

### Resolution formula

```
manifest = resolve(schema, template, seed, context)
```

| Input | Contribution |
|---|---|
| `schema` | Defines which fields exist, their types, and what is required |
| `template` | Defines which zones exist and their arrangement |
| `seed` | Provides default values for all scalar parameters |
| `context` | Provides override values (project name, brand, client, actual data) |

Resolution is deterministic. Given the same (schema, template, seed, context), the manifest is identical.

Context always overrides seed. Seed fills gaps not covered by context. Schema rejects any field not in its attribute declarations. Template constrains which zones are resolvable.

### Instantiation formula

```
instance = instantiate(schema, manifest)
```

| Input | Contribution |
|---|---|
| `schema` | Governs structural validity during instantiation (guard) |
| `manifest` | Provides all resolved values and component configurations |

The renderer is not part of this formula. Instantiation produces a structured, renderable object. Rendering is a separate concern.

### Complete flow

```
brief
  → key_question answered
  → context assembled

schema        ← defines the space
template      ← defines the arrangement
seed          ← provides defaults
context       ← provides specifics

↓ resolve()

manifest      ← fully resolved specification

↓ instantiate()

instance      ← produced artifact
```

### What happens at each transition

**brief → context:** The brief is parsed and the key question is answered. This produces the contextual values (project name, brand, target, specific content).

**resolve():** Schema is validated against (seed ∪ context). Template is selected. All fields are resolved: context values take priority, seed fills remaining gaps, schema rejects invalid or missing required fields.

**instantiate():** Manifest is passed to the object's own `render()` method. Schema acts as a guard (validation). Output is immutable.

---

## APPENDIX — OBJECT CATALOG SUMMARY TABLE

| Object | Key question | Schema anchor | Seed pivot | Instance format |
|---|---|---|---|---|
| `landing_page` | Single action to take | hero, sections[], CTA | density, hero_type | HTML |
| `dashboard` | Decisions to enable | StatCard, WidgetSection | layout, chart_type | HTML |
| `graphic_chart` | Brand feeling | VisualIntent, Palette, Typography | archetype, hue_bias | HTML + CSS vars |
| `invoice_doc` | Transaction formalized | Issuer, Client, LineItem[], BankDetails | currency, vat_rate | HTML (print) |
| `quote_doc` | Proposal terms | Issuer, Client, LineItem[], validity | currency, validity_days | HTML (print) |
| `purchase_order_doc` | Order authorization | Issuer, Supplier, LineItem[], DeliveryInfo | currency, show_delivery | HTML (print) |
| `text_doc` | Reader understanding + action | title, blocks[] | density, tone | HTML (print) |
| `email_signature` | Identity + action | name, title, social[], CTA | layout, cta_style | Inline HTML |
