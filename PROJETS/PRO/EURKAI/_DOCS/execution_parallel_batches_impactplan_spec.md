# Eurkai — Execution Architecture Notes (Parallel Runs, Batch Cycles, Contention, Dispatch, ImpactPlan)
Generated on: 2026-02-14T09:41:39.459149 UTC

> Scope: This document consolidates what we fixed/clarified about **parallel execution**, **batch cycles (looped sequence)**,
> **contention**, **queueing**, **dispatch**, **atomic writes**, **KPITrigger**, and **ImpactResolve/ImpactPlan**.
> It is written to be integrated into the exhaustive Eurkai documentation.

---

## 1) Batches and the Execution Loop (no calendar planning)

### 1.1 Principle fixed
Instead of scheduling tasks by real-world timetable (“school schedule”), we define a **sequence** that runs in loop.

At each iteration:
- collect everything “waiting”
- execute in parallel up to safe thresholds
- advance system state
- repeat

This keeps execution stable and actionnable while remaining fully dynamic.

### 1.2 Why it fits Eurkai
- simple mental model
- consistent with Pulse-driven autonomy
- supports constant-ish execution time under growth
- naturally supports scaling/dispatch when thresholds are exceeded

---

## 2) Parallel execution vs option explosion (clarified)

We clarified a misunderstanding:
- Parallel execution does **not** imply generating more options/branches.
- If scripts define a fixed set of tasks, parallel vs sequential execution does not increase the number of validations “per case”.

The remaining concern is **contention** and shared-state consistency.

---

## 3) Contention (what it is)

Contention = multiple runs try to use the same resource at the same time:
- CPU/RAM
- disk writes (logs/artifacts)
- database locks
- API rate limits
- shared file/object updates

Consequences:
- slowdown
- retries
- non-deterministic failures (timing-dependent)

### 3.1 “Parallel execute, sequential finalize” pattern
We discussed a practical mitigation:
- run the “compute” parts in parallel
- but serialize “finalization / commits” (logs, shared state writes)

However, complex scenarios can interleave sub-scenarios; pure separation is not always optimal, hence the loop+threshold approach.

---

## 4) Queueing vs limiting parallelism (clarified)

You initially preferred controlling delay by limiting **queue length** rather than limiting parallelism.

We clarified:
- queue length cap is a valid “brake”
- but without any throttle, systems tend to compensate by launching too much in parallel, increasing contention and variability

So even if you prefer queue_max as the primary brake, a practical system still needs:
- either an explicit parallelism cap
- or an implicit throttle policy that effectively acts as a cap

---

## 5) KPITrigger (fixed proposal)

You proposed a key KPI to regulate and optimize the system:

- `KPITrigger = waiting_triggers / active_runs`

This KPI is:
- easy to observe
- suitable for optimization
- can be extended per scope (agency/project/object-type)
- can be tracked in derivatives (momentum) if needed

---

## 6) Dispatch / Scaling when a critical threshold is reached

### 6.1 Trigger to dispatch
When a “critical threshold” is reached (e.g., too many parallel triggers / too many waiting triggers / KPITrigger crossing a bound):
- dispatch work across additional workers/servers

### 6.2 Dispatch options (incremental)
1) multiple workers on one machine
2) multiple machines (horizontal scale) pulling from a shared queue
3) partition by scope (“zones of responsibility”)

### 6.3 Partitioning (“sharding”) clarified
We clarified “sharding” as:
- splitting state into zones (e.g., per client or per project)
- assigning each zone to one worker for writes

This reduces collisions on shared state and increases determinism.

> Important: JSON storage does not remove write-collision risk; it only removes SQL-type constraints. Concurrency and coherence remain system invariants.

---

## 7) Atomic writes (fixed)

We fixed a practical atomicity approach for JSON/object storage:
- write to a temporary file
- then atomically rename

This supports:
- “all or nothing” writes
- reduced partial-state risk in crashes

---

## 8) Hooks naming clarification (fixed mapping)

We fixed the canonical form:
- `Scenario.hook_list.success_hook` is the base hook container
- `onsuccess` is an alias used as a trigger name

Mapping fixed:
- `Scenario@onsuccess = Scenario.hook_list.success_hook`

Therefore, Impact resolution is referenced as:
- `Scenario.hook_list.success_hook.impact_resolve`

(not `onsuccess` as the base container)

---

## 9) ImpactResolve & ImpactPlan (fixed)

### 9.1 Purpose
We converged on:
- `impact_resolve` (or `Orchestrate.impact_resolve`) is responsible for **side effects** resolution.
- It goes beyond “state propagation”: it lists the consequences and adjustments required across related objects.

Crucially:
- `impact_resolve` does not execute changes.
- It outputs a plan.

### 9.2 Why it belongs to Orchestrate
You clarified:
- `impact_resolve` is fundamentally an orchestration capability: it **lists** modifications to perform in consequence.
- Actual modifications are then performed by Create/Update/Delete/Connect scenarios.

Thus:
- `Orchestrate.secondary_method_list.impact_resolve`

### 9.3 Naming fixed
- preferred: `impact_resolve`
- acceptable explicit form: `Orchestrate.impact_resolve`
- rejected: `orchestrate_impact_resolve` (too verbose)

### 9.4 Hook usage fixed
- `Scenario.hook_list.success_hook.impact_resolve`

### 9.5 ImpactPlan structure (fixed)
`impact_resolve` returns an `ImpactPlan` (canonical fields):

- `source_run_id`
- `source_object_id`
- `delta_summary`
- `impact_action_list` (ordered list)
  - `action_type` (create/update/delete/connect/task_create/...)
  - `target_object_type`
  - `target_object_id` (optional)
  - `scenario_ref`
  - `priority`
  - `reason`
  - `rule_ref_list`
  - `idempotency_key`
- `revalidation_required_list`
- `risk_flag`
- `message`

### 9.6 Idempotence requirement (fixed)
Impact resolution must be idempotent by design:
- rerunning `impact_resolve` must not duplicate actions or tasks
- `idempotency_key` supports deduplication

---

## 10) Summary of the execution model fixed in this segment

- Execution is controlled by a **looped sequence** (not calendar planning).
- Parallelism is used for throughput, while contention is controlled by thresholds and/or throttles.
- Dispatch (scale-out) is triggered when critical thresholds are met.
- Atomic writes are ensured via temp-write + rename.
- Success hook naming is canonical: `success_hook` is base; `onsuccess` is alias.
- Side effects are handled by `impact_resolve` (Orchestrate secondary) producing an `ImpactPlan`.

---

End of document.
