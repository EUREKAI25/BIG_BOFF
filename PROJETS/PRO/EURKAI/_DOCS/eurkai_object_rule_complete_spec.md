# Eurkai -- Object:Rule (Complete Specification)

## 1. Object:Rule -- General Definition

`Object:Rule` is a normative Object that constrains, governs, or
structures other Objects.

A Rule does not perform actions. A Rule imposes conditions.

All Rules are Objects. All Rules participate in fractal inheritance
(inherited / injected / owned / overridden).

------------------------------------------------------------------------

# 2. Taxonomy of Rules

## 2.1 Top-Level Classification

### A) FormatRule

Concerned with representation and structure form.

Includes: - StructuralRule - NomenclatureRule

### B) NormativeRule

Concerned with obligations, commitments, semantics and governance.

Includes: - ConstitutionalRule - SchemaRule - ContractRule -
PolicyRule - MetaRule

------------------------------------------------------------------------

# 3. FormatRule

## 3.1 StructuralRule

Defines structural constraints: - cardinality - membership -
containment - composition requirements

Applies in ViewRuleDimension.

## 3.2 NomenclatureRule

Defines naming conventions: - naming patterns - identifier rules -
semantic prefixes/suffixes

Applies in ViewRuleDimension.

------------------------------------------------------------------------

# 4. NormativeRule

## 4.1 ConstitutionalRule

Defines foundational invariants of the system.

Examples: - Everything is Object. - Every execution passes through
MRG. - Every method returns a Result. - Every Rule is an Object.

ConstitutionalRules are not modified. They may be extended via
mode-based presets.

ConstitutionalRules = Base + Addons.

------------------------------------------------------------------------

## 4.2 SchemaRule

Defines compatibility and type constraints: - inheritance validity -
schema conformity - compatibility between parent and instance

Applies in ContextRuleDimension.

------------------------------------------------------------------------

## 4.3 PolicyRule

Defines operational or strategic constraints.

Examples: - throttle limits - dispatch thresholds - commerce
restrictions - SLA guarantees

Charter and CGV are instances of PolicyRule.

------------------------------------------------------------------------

## 4.4 ContractRule

Defines formal commitments between Objects or Methods.

A ContractRule expresses:

-   obligation
-   guarantee
-   behavioral commitment
-   relational integrity

Examples:

-   Instance must conform to parent module schema.
-   If Read.get fails with EmptyResult → GetCreate must trigger Create.
-   If Result.success=false → error must exist.

Contracts do not modify behavior. They define obligations whose
violation triggers FailureScenarios.

ContractRules are overrideable by children. ContractRuleList is defined
by the instance manifest.

------------------------------------------------------------------------

# 5. MetaRule -- Governance of Rules

MetaRule governs the active RuleSets.

MetaRule does NOT modify rules. MetaRule may:

-   Activate a rule
-   Deactivate a rule
-   Replace one rule with another (substitution)
-   Add contextual rule extensions
-   Control priority or resolution behavior

MetaRule operates via presets.

MetaRule ∈ NormativeRule MetaRule IN Rule.rulelist (System level)

------------------------------------------------------------------------

# 6. Preset Mechanism

System.config.mode ∈ { default, orsec }

Each mode activates a RulePreset:

-   preset.default
-   preset.orsec

Each preset defines:

-   active ConstitutionalRules
-   active PolicyRules
-   active ContractRules
-   optional substitutions
-   optional extensions (addons)

ConstitutionalRules are composed as:

Base ConstitutionalRules + Addons activated by preset

Example Addons: - temporary commerce ban (country X) - infrastructure
failure clauses - emergency SLA override

------------------------------------------------------------------------

# 7. Rule Activation Model

Rules become active through declarations:

Rule:XRule IN `<object>`{=html}.rulelist.`<rule_type>`{=html}

From these declarations, a TriggerList is generated.

Rule activation flow:

1.  Object exposes candidate rulelists.
2.  MetaRule applies preset (filter/replace/add).
3.  Active RuleList is constructed.
4.  TriggerList is generated from active rules.
5.  Rules evaluated during execution.

------------------------------------------------------------------------

# 8. Contracts in Practice

Contracts may apply to:

-   Method ↔ Object
-   Object ↔ Object
-   Instance ↔ Parent
-   Scenario ↔ Result
-   Policy ↔ Scope

Contract violation triggers:

Scenario:FailureScenario:ResultError or
Scenario:FailureScenario:SystemError

Contracts do not execute corrections. They define the obligation whose
violation is handled by scenarios.

------------------------------------------------------------------------

# 9. Constitutional vs ORSEC Mode

ConstitutionalRules are not altered. They are composed.

Mode-specific composition:

default: BaseConstitution

orsec: BaseConstitution + EmergencyAddons + Policy substitutions

MetaRule selects the preset based on System.config.mode.

------------------------------------------------------------------------

# 10. Summary

Object:Rule taxonomy:

FormatRule - StructuralRule - NomenclatureRule

NormativeRule - ConstitutionalRule - SchemaRule - ContractRule -
PolicyRule - MetaRule

MetaRule governs which rules are active. Contracts define obligations.
Policies define contextual constraints. Schema defines compatibility.
Format defines structure and naming.

All Rules are Objects. All Rules are fractal. All Rules are governed by
MetaRule presets.

------------------------------------------------------------------------

End of Object:Rule specification.
