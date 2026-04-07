# Hooks, Triggers, Tasks & Cron Architecture – Fixed Specification

Generated on: 2026-02-13T23:41:29.398424 UTC

---

# Scope

This document consolidates what has been agreed regarding:

- Hooks
- Triggers
- Scenario execution flow
- Task lifecycle
- Cron execution via Pulse
- Run & instance behavior

This reflects architectural decisions validated during discussion.

---

# 1. Pulse

Pulse is a neutral heartbeat.

- Executes every <x> ms.
- Contains no business rules.
- Does not decide execution.
- Simply triggers scenarios that define their own behavior.

All decision logic belongs to scenarios and methods.

---

# 2. Scenario Execution Hooks

Base execution pipeline:

- before
- execute
- validate
- render
- onsuccess
- onfailure
- (optional) onvalidationfailure

The `get` hook is not required.

Dependency resolution is handled upstream by SuperTool.prepare which builds execution vectors (what, how).

---

# 3. Hook Behavior

Each hook execution produces a standard MethodResult:

{
  success: bool,
  output: dict,
  message: string|null,
  error: string|null,
  details: dict|null
}

details may contain:

- evidence_ids
- justifications
- suggestions
- trace_id
- run_id

Duration is calculated using:

- startsat
- endsat

duration may be stored for convenience.

---

# 4. Triggers

Any hook may act as a trigger.

Aliases are auto-generated:

- on<scenario>success
- on<scenario>failure
- on<scenariotype>success
- on<scenariotype>failure

Trigger resolution occurs during:

SuperTool.execute.beforehook → Trigger.resolve

Trigger resolution produces a unified HookExecutionPlan (ordered).

No hook/trigger double-execution ambiguity.

---

# 5. Validate Behavior

Validate returns:

- success: bool
- message: { suggestion|null, brief|null }

Validate may indirectly require a FixAgent team via OrchestratorAgent.

FailureHook decides whether to apply fix plan.

Validate never executes fixes directly.

---

# 6. Task Architecture

Task inherits Object.priority.

Task overrides priority as integer when necessary.

Task.lifecycle ∈

- todo (default)
- pending
- missing
- complete

State transitions:

- todo → pending via Task.orchestratescenario.secondarymethod
- pending → missing when blocker detected
- missing → pending when blocker resolved
- pending → complete on Scenario.render.onsuccess

---

# 7. Blockers

Status:missingStatus.blockerlist contains Blocker objects.

Blocker is a generic Object.

Blocker may represent:

- missing data
- dependency artifact
- approval needed
- external wait

Blocker resolution may occur via:

- scenario execution
- Pulse-based checks
- artifact arrival detection

---

# 8. Execution Modes

Project.owner.execution_mode defines default behavior.

Task.execution_mode overrides if present.

Modes:

- manual
- assisted
- autonomous

---

# 9. Run & Instance Behavior

Each execution attempt is a Run instance.

Run.instance.lock prevents concurrent execution of the same run.

Run does not prevent monitoring.

Pulse may continue checking while run is active.

Traceability:

- trace_id → full causal chain
- run_id → specific execution attempt

---

# 10. Cron & Repeat

Cron execution is triggered via Pulse.

Task.rule:Policy:RepeatPolicy defines repetition behavior.

Two distinct concepts:

- due_at → task eligibility for processing
- repeat_policy → recurrence pattern

Pulse only triggers scenarios.

Scenarios evaluate eligibility.

---

# 11. Key Fixed Principles

1. Pulse is neutral.
2. Hooks are structured execution stages.
3. Triggers resolve into ordered execution plans.
4. Validate returns decision, not execution.
5. Tasks are state machines.
6. Blockers are explicit objects.
7. Run prevents concurrency, not monitoring.
8. No direct model invocation inside scenarios.
9. All business logic resides in scenarios and methods.

---

End of document.
