# Validation Naming Convention – Fixed Specification

Generated on: 2026-02-13T07:26:58.210469 UTC

---

# Scope

This document formalizes what has been fixed regarding the naming convention for validation rules within the multi-level validation system (L1, L2, L3).

It reflects only what has been explicitly validated and agreed upon.

---

# 1. Rule Naming Structure

All validation rules follow the strict format:

<objectattribute>_<object>

Examples:

- forbidden_execution_scenario
- declarative_method_scenario
- evidence_required_validation
- strict_io_schema_object
- role_scope_respected_agent

No validation level (L1, L2, L3) appears in the rule name.

The rule name remains level-agnostic.

---

# 2. Rule Attributes Structure

Each rule contains exactly two attributes for validation prompting:

- prompt_validation_rule:lX_prompt_validation_rule
- prompt_validation_rule_validation

Where:

- X ∈ (1, 2, 3)
- X represents the validation level (L1, L2, L3)

Example:

forbidden_execution_scenario

  prompt_validation_rule:l3_prompt_validation_rule:
    A scenario must never execute real actions.

  prompt_validation_rule_validation:
    Does the scenario contain any real execution instruction?

---

# 3. Level Positioning

Validation level (L1, L2, L3):

- Is encoded only inside the attribute name.
- Is never included in the rule identifier.
- Does not alter the semantic identity of the rule.

Thus:

forbidden_execution_scenario  
remains the same rule across all levels.

Only its lX_prompt_validation_rule content differs by level.

---

# 4. Object and Attribute Semantics

- <object> = the entity being constrained (scenario, object, agent, validation, process, etc.)
- <objectattribute> = the constrained property or constraint applied to the object (forbidden_execution, declarative_method, strict_io_schema, traceability_required, etc.)

The rule name expresses:

"Constraint applied to object"

---

# 5. Constitutional Positioning

- L1 rules = Expert evaluation behavior rules
- L2 rules = Meta-validation and procedural integrity rules
- L3 rules = Constitutional, non-overridable rules

However, rule identity does not encode level.
Level is contextual.

---

# 6. Final Fixed Decisions

The following decisions are now fixed:

1. Rule name format is immutable: <objectattribute>_<object>
2. Validation level is encoded only in prompt_validation_rule:lX_prompt_validation_rule
3. prompt_validation_rule_validation remains level-neutral
4. No validation rule includes direct model references
5. Rule identity is independent of validation depth

---

End of document.
