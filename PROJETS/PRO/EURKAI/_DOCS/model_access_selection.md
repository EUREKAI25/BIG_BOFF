# Model Access & Selection – Object-Driven, Lab-Governed

Generated on: 2026-02-13T03:06:14.637354 UTC

---

## Goal

Guarantee **portability, upgradability, and reliability** by ensuring that:
- Objects describe **needs**, never vendor/model names.
- A dedicated **Lab** continuously maintains the best available model options (via monitoring + benchmarks + regression tests).
- The runtime selects models through a **resolver**, not direct calls.

---

## Core Principles

### 1) No Direct Model Calls (Hard Rule)
No object, scenario, or agent may call a specific model (e.g. `claude-…`, `gpt-…`, `kimi-…`) directly.

**Only** the runtime / orchestration layer may select and invoke a model via an indirection mechanism.

Why:
- Providers and models change frequently (availability, pricing, quality, deprecations).
- You want repeatability, rollbacks, and safe upgrades.
- You want a single point to enforce governance (budgets, safety, logs, residency).

---

### 2) Objects Declare Capability Needs
Each object must declare:
- **Required modality**: text / code / image / video / audio / multimodal / judge
- **Operation class**: generate / transform / inpaint / upscale / animate / summarize / validate / classify, etc.
- **Exigence level** (quality & reliability targets)
- **Constraints**: latency, budget, determinism, context length, tool-use requirements, structured output requirements
- **Risk class**: low/medium/high (impacts validation depth and model choice)

Objects declare **what** they need, not **who** will do it.

---

## Model Taxonomy (Objects)

You mentioned a typed hierarchy such as:

- `ImageModel:Text2ImageModel`
- `ImageModel:Image2ImageModel`

Extend this consistently to all modalities, for example:

- `TextModel:ChatModel`
- `TextModel:ReasoningModel`
- `CodeModel:CodeAssistantModel`
- `JudgeModel:ValidationModel`
- `VideoModel:Text2VideoModel`
- `VideoModel:Image2VideoModel`
- `VideoModel:Video2VideoModel`
- `AudioModel:Text2SpeechModel`
- `AudioModel:Speech2TextModel`
- `MultimodalModel:VisionLanguageModel`

Each typed model class defines **supported operations** and **capability contracts**.

---

## Exigence Levels (Quality Tiers)

Define a small set of tiers used everywhere, e.g.:

- `draft` – cheap/fast, acceptable imperfections
- `standard` – balanced quality/cost
- `premium` – highest quality + strong consistency requirements
- `critical` – high reliability, strict formats, double validation, tight budgets & audit

Objects reference a tier; the Lab maps tiers to real models.

---

## The Resolver Pattern (Indirection)

Runtime uses a **ModelResolver** that takes:
- object type
- modality
- operation
- exigence tier
- constraints (budget/latency/region)
- risk class
- required features (tool-use, JSON schema, long context, reference locking, etc.)

and returns:
- `model_candidate_set` (ranked list)
- `policy` (fallback, retries, temperature, seed strategy)
- `version tag` (for reproducibility)

The runtime calls the **top candidate**, with defined fallback behavior.

---

## The Lab (Continuous Improvement Loop)

The Lab is responsible for:
1) **Monitoring / veille** (new models, deprecations, pricing, safety changes)
2) **Benchmarking** per object family and operation
3) **Regression tests** on canonical corpora (golden tasks)
4) **Selection policies** and periodic updates to the resolver registry
5) **Rollback** when regressions detected
6) **Documentation** of why a mapping exists (traceability)

The Lab output is a versioned **Model Registry** + **Capability Matrix**.

---

## Reproducibility & Audit

To support “what happened?” and “can we replay?”:
- Every execution stores:
  - resolver input (needs/constraints)
  - chosen model + provider
  - config (temperature/seed/tools)
  - prompts (or hashed prompts if sensitive)
  - artifacts and evidences
  - validation results (L1/L2/L3 when applicable)
- A **replay mode** can pin the chosen model version, or re-resolve to “best current.”

---

## Safety, Budget & Policy Gates (Centralized)

Because model calls are centralized, you can enforce:
- spend caps per project/agent/object type
- disallow certain providers for high-risk tasks
- data residency requirements
- timeouts / retry policies
- redaction rules (e.g. secrets never leave sandbox)
- “two-model rule” for critical outputs (generator + judge) or “panel experts” (L1)

---

## Relationship with Validation

Model selection and validation interact through risk & tier:
- higher risk → stronger validators / more judges / stricter schema
- premium/critical tiers → often require multi-judge or second-opinion
- idempotent low-risk tasks → cheaper validators or bypass levels according to policy

---

## What to Add Next (Recommended Specs)

1) A shared vocabulary for object needs:
   - modality, operation, tier, risk_class, constraints

2) A minimal “capability contract” per ModelType:
   - e.g. supports tool-use, supports JSON schema, supports references, max context, cost/latency profiles

3) A Lab update protocol:
   - propose → benchmark → stage → canary → promote → rollback

4) A resolver output contract:
   - ranked candidates + fallback + version tag

---

End of document.
