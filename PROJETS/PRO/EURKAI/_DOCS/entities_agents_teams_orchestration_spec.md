# Eurkai — Entities, Agents, Teams & Orchestration (Fixed Notes)
Generated on: 2026-02-14T09:41:39.459149 UTC

> Scope: This document consolidates what we fixed in this thread about **Entity**, **Agent**, **User/Visitor**, **Company roles**, **Statuses**, **Contracts**, **Teams**, and **Orchestration**.
> It is written to be integrated into the exhaustive Eurkai documentation.

---

## 1) Core Ontology: `Object:Entity`

### 1.1 Definition
`Object:Entity` groups all “actors” (physical or moral) that can participate in Eurkai processes.

Eurkai avoids multiplying “entity types” when a concept is better represented as a **status** or a **role option**.

### 1.2 Minimal Entity Set (as discussed)
- `Entity:Agent`
  - `Agent:HumanAgent`
  - `Agent:AIAgent`
- `Entity:Company`
- `Entity:Contact` (preferred over `Entity:Identity` in this discussion)
  - A “contact point / entry” object used for CRM-style flows (can represent a person, a company contact point, a channel, etc.).

> Note: We explicitly rejected introducing `Person` and also rejected duplicating “human” types (no `ExternalHuman`).

---

## 2) Statuses (not entity types)

### 2.1 Principle
Concepts like **visitor**, **user**, **prospect**, **client** are not new entity classes. They are **statuses** (often multi-valued) attached to an entity (typically `Contact` and/or `Company`).

### 2.2 Access / Interaction
- `Status:AccessStatus.lifecycle` (example)
  - `visitor → user → authenticated → (owner|admin|...)`

**Key point fixed:** a same actor can be both:
- `AccessStatus = visitor` and `CommercialStatus = suspect`
- `AccessStatus = authenticated` and `CommercialStatus = client`

### 2.3 Commercial
- `Status:CommercialStatus.lifecycle`
  - `contact → suspect → prospect → client`

**Key point fixed:** we do **not** create `ClientCompany` or `Provider` entity types. A company can carry multiple commercial roles simultaneously.

### 2.4 Multi-Status Storage Choice (fixed)
We fixed the preference for:
- `Entity.commercialstatus.optionlist` (multi-valued, more readable, no redundancy)

> If contextualization is needed later (per project/product), each item can evolve into a small object `{status, scope_ref}` while keeping the “optionlist” approach.

---

## 3) Subscription / “Subscriber”

### 3.1 “Subscriber” is not a commercial status
Subscriber is an effect of a **contract + product model**, not a separate entity type.

### 3.2 Product model
- `Product.marketing_model = subscription` (context)

### 3.3 Contract state
Subscriber is expressed via:
- `Status:ContractStatus.lifecycle` (example)
  - `trial → active → paused → cancelled`

### 3.4 “Client” location in the model
- “Client” = `CommercialStatus = client`
- “Subscriber” = `CommercialStatus = client` + `ContractStatus = active` in a subscription context

---

## 4) Contracts

We agreed that Contract deserves explicit specialization.

### 4.1 Commercial contract
- `Contract:CommercialContract`
  - Links an entity (company/contact) ↔ a product/offer
  - Stores subscription/billing context and `ContractStatus`

### 4.2 Rule contract
- `Contract:RuleContract`
  - Expresses constraints, limits, obligations applicable to a scope
  - Used to attach **rules** without hardcoding them everywhere

---

## 5) Agents vs Teams

### 5.1 Agent is not Team (but Team can contain one agent)
- `Agent` = individual capability container (human or AI)
- `Team` = a collection of agents, even if size=1 is allowed

We keep the conceptual elegance “team of one is possible”, but without collapsing the types.

### 5.2 Orchestrator presence (fixed)
Orchestrator is **conditional**, not mandatory for all operations.

Orchestrator intervenes when needed (examples):
- coordination > 1 agent
- composition of milestones/steps
- arbitration / disagreement
- complex multi-agent work (brainstorming, meeting, etc.)

---

## 6) Validation Levels (L1 / L2 / L3)

We fixed the meaning as:

- **L1**: collect expert opinions (each opinion justified)
- **L2**: arbitrate/weight based on L1 opinions (justified)
- **L3**: “cassation” (final validation in all cases; decisive when no unanimity)

Each level has its own resources to support decisions:
- Charter (always)
- Domain rules (expertise-specific)
- Documentation outside rules (guides, whitepapers, tutorials)

The “justification corpus” is a signature asset of Eurkai and later feeds publishing/knowledge (blog).

---

## 7) Work Decomposition for Team Creation (get/create teams)

When a team is required and/or a new “team seed” is needed:
1. list milestones
2. split into steps
3. organize sequential/parallel
4. determine which expert types are required per step (and per validation requirement)
5. form teams accordingly
6. apply L1/L2/L3 as needed (not always)

**Note fixed:** “seed” is tied to object type: it exists or it doesn’t; it evolves via versioning rather than proliferating.

---

## 8) Team Modalities (fixed framing)

We corrected the model: do not confuse “what the team does” with “how it intervenes”.

### 8.1 Team is best described by modalities
The primary distinction you fixed is modal:

- `Team.mode = free`
  - agents act freely (parallel, whenever allowed)
- `Team.mode = organized`
  - orchestration defines chronology and constraints

### 8.2 Trigger-based constraints on intervention
Actions may be parallel but **blocked** until a condition is met (historical triggers, event triggers, start triggers).
Unlocking can be:
- successive (step-by-step)
- collective (all-at-once)

This supports “parallel potential” with controlled realization.

---

## 9) Priority / Urgency / Importance (discussion outcome)

We fixed the intention:
- urgency and importance should both matter
- ordering defaults to arrival order when priorities tie

We discussed that coefficients must be:
- defaulted
- but dynamically tunable by optimization (Lab) and validated by agency governance

(Exact formulas are kept as configurable policies; not frozen here.)

---

## 10) Connect vs Engage (fixed direction)

- Engage started as “interaction with external”.
- We recognized: “everything is object”, so external interaction is a special case of object↔object interaction.

**Decision direction:** introduce `Connect` as the central method for object↔object interaction.  
Engage becomes unnecessary (or could be a non-essential specialization of Connect, but we do not keep it as a core pillar).

---

End of document.
