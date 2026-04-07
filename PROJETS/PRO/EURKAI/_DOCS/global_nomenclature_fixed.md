# Global Nomenclature Specification – Fixed Decisions

Generated on: 2026-02-13T08:49:19.117237 UTC

---

# Scope

This document formalizes the global nomenclature rules validated during the architectural discussions.

It covers:

- Rule naming
- Attribute naming
- Validation level encoding
- Object structure conventions
- Model-type naming
- Separation of concerns (orchestrate / engage / validate)
- Constitutional positioning

Only what has been explicitly fixed is included.

---

# 1. Core Naming Grammar

## 1.1 General Pattern

All structural identifiers follow explicit compositional grammar.

Primary rule pattern:

<objectattribute>_<object>

Examples:

- forbidden_execution_scenario
- declarative_method_scenario
- strict_io_schema_object
- evidence_required_validation
- role_scope_respected_agent

The name expresses:

"Constraint or property applied to object"

---

# 2. Validation Rule Structure

Each validation rule contains exactly two attributes:

- prompt_validation_rule:lX_prompt_validation_rule
- prompt_validation_rule_validation

Where:

- X ∈ {1, 2, 3}
- X represents validation level (L1 expert, L2 meta, L3 constitutional)

Important decisions:

- Validation level is encoded ONLY in the attribute.
- Validation level NEVER appears in the rule identifier.
- The rule identity is level-agnostic.

---

# 3. Validation Levels – Functional Definition

L1 – Expert Validation
- Domain-specific assessment
- Must justify decisions
- Must separate conformity vs optimisation

L2 – Meta-Validation
- Diagnoses disagreement
- Verifies evidence sufficiency
- Ensures procedural integrity
- Must diagnose before deciding

L3 – Constitutional Validation
- Verifies respect of fundamental system rules
- Never scores
- Never optimises
- Cannot be overridden by consensus

---

# 4. Object Semantics

<object> represents the entity constrained or governed.

Examples:

- scenario
- object
- agent
- validation
- process

<objectattribute> represents the constrained property.

Examples:

- forbidden_execution
- declarative_method
- strict_io_schema
- traceability_required
- evidence_required

---

# 5. Scenario Rules (Structural)

Scenarios must:

- Be declarative only
- Never execute real actions
- Express steps as object.method(params)
- Never call models directly
- Never perform I/O
- Remain orchestration-neutral

Execution is external to scenarios.

---

# 6. Orchestrate / Engage / Validate Separation

Fixed role separation:

engage()
→ produces outputs (generation, expert opinions)

validate()
→ governance function belonging to orchestrate()

orchestrate()
→ controls flow, state, escalation, retries

Validation belongs to orchestrate.
Engage may be used internally to call a validator model.

---

# 7. Model Naming & Indirection

No object or scenario may reference a concrete model name.

Objects declare needs only:

- modality (text, image, video, code, multimodal, judge)
- operation type
- exigence tier
- risk_class
- constraints

Model types follow typed hierarchy pattern:

<ParentModelType>:<SpecializedModelType>

Examples:

- ImageModel:Text2ImageModel
- ImageModel:Image2ImageModel
- VideoModel:Text2VideoModel
- JudgeModel:ValidationModel

Concrete models are resolved only by the Lab via a resolver.

---

# 8. Constitutional Invariants

Constitutional rules:

- Are non-overridable
- Are level-agnostic in naming
- May exist at L1/L2/L3 but L3 is final authority
- Cannot be bypassed by unanimity

---

# 9. Risk & Validation Depth

Validation escalation depends on:

- idempotence
- blast radius
- reversibility
- novelty
- risk_class

Unanimity may bypass upper levels only if risk is low and no constitutional suspicion exists.

---

# 10. What Is Now Fixed

The following elements are now fixed:

1. Rule naming grammar: <objectattribute>_<object>
2. Validation level encoding inside attribute only
3. Declarative-only scenario architecture
4. Strict separation orchestrate / engage / validate
5. No direct model calls in objects or scenarios
6. Model types declared abstractly, resolved externally
7. Constitutional rules cannot be overridden

---

End of document.
