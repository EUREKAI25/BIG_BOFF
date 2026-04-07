# Validation Architecture -- Multi-Level Constitutional System

Generated on: 2026-02-13T02:53:10.652563 UTC

------------------------------------------------------------------------

## Overview

This document formalizes the multi-level validation system discussed.

The validation system is structured around three conditional levels:

-   **L1 -- Expert Panel Validation**
-   **L2 -- Meta-Validation (Validation of Validation)**
-   **L3 -- Constitutional Court (Fundamental Rules)**

Validation is governed by *objects*, each embedding: - Its qualified
expert domains - Its validation policy - Its constitutional
constraints - Its rubric and weighting logic

------------------------------------------------------------------------

# Core Architectural Principles

## 1. Separation of Responsibilities

-   `engage()` → produces outputs (generation, proposal, expert opinion)
-   `orchestrate()` → controls flow and decisions
-   `validate()` → governance function belonging to `orchestrate()`
-   Scenarios are declarative only (never executable)

Validation never executes actions. It evaluates, scores, and optionally
proposes a fix plan.

------------------------------------------------------------------------

# Level 1 -- Expert Panel Validation

Each object declares: - A list of qualified expert domains - A weighting
model per role and phase (conception vs optimisation)

Each expert must: - Provide justification - Cite verifiable evidence -
Provide both: - Conformity score - Optimisation score

Unanimity may bypass higher levels only if: - Risk class is low - Object
is idempotent - No constitutional suspicion is raised

------------------------------------------------------------------------

# Level 2 -- Meta-Validation

Triggered only when: - Expert disagreement exists - Object type requires
careful review - Risk class is elevated

Responsibilities: - Diagnose the source of disagreement - Evaluate
evidence sufficiency - Confirm or refute expert conclusions - Propose
procedural correction if needed

L2 must diagnose before deciding.

------------------------------------------------------------------------

# Level 3 -- Constitutional Court

Triggered when: - No unanimity AND risk ≥ medium - Suspicion of
constitutional violation - High-risk object type - Explicit flag raised
by lower level

L3 does not score or optimise.

It only determines:

constitutional_status: valid \| invalid\
violated_rules: \[list\]

L3 cannot be overridden by consensus.

------------------------------------------------------------------------

# Risk-Based Validation Policy

Validation depth depends on:

-   Idempotence
-   Blast radius
-   Reversibility
-   Novelty
-   Risk class

High-risk objects automatically escalate.

------------------------------------------------------------------------

# Anti-Loop Safeguards

To prevent infinite cycles: - Max iteration per level - Escalation to
policy decision after threshold - Fix-plan must target cause, not
re-generate blindly

------------------------------------------------------------------------

# Evidence Requirements

All validation decisions must: - Cite verifiable evidence - Mark
uncertainty as `unknown` - Avoid hallucinated claims

Evidence may include: - Line references - Artifact IDs - Timestamps -
Hashes - Explicit input references

------------------------------------------------------------------------

# Naming Convention

Rules follow format:

`<objectattribute>`{=html}\_`<object>`{=html}

Each rule contains attributes:

-   prompt_validation_rule:lX_prompt_validation_rule
-   prompt_validation_rule_validation

Where X corresponds to validation level.

------------------------------------------------------------------------

# Constitutional Rule Set (N3)

Rules are universal and non-negotiable.

See structured list in system definition.

------------------------------------------------------------------------

End of document.
