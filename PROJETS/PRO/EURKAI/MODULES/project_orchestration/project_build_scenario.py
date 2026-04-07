"""
project_build_scenario — EURKAI Execution Layer

Counterpart of ProjectDefinitionScenario.
Receives an execution_plan, executes each need's module chain in order,
propagates context between chains, and returns structured deliverables.

Objects:
    ChainStep       — one module call within a chain
    ExecutionChain  — ordered steps for one need (need_name + steps + deps + outputs)
    BuildResult     — final structured output

Scenario:
    ProjectBuildScenario
        .build_chains(execution_plan)           → List[ExecutionChain]
        .execute(chains, context, dry_run)      → BuildResult
        .run(execution_plan, initial_context)   → dict  ← main entry point

Executor model:
    - dynamic loading via _try_load() when module exists on disk
    - injectable via register_executor(module_ref, fn) for tests / agents
    - steps without an executor are skipped (not failed)

Dry run:
    - resolves chains and dependencies
    - returns simulation without calling any module
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Data models ────────────────────────────────────────────────────────────────

class ChainStep(BaseModel):
    """One module call within an ExecutionChain."""
    step_name:  str
    module_ref: str
    input_map:  Dict[str, str]  = Field(default_factory=dict)
    # {arg_name: context_key} — maps function argument names to context keys
    output_key: str             = ""     # key under which output is stored in context
    optional:   bool            = False  # if True, failure does not fail the chain
    status:     Literal["pending", "running", "done", "skipped", "failed"] = "pending"
    output:     Optional[Any]   = None
    error:      Optional[str]   = None

    model_config = {"arbitrary_types_allowed": True}


class ExecutionChain(BaseModel):
    """Ordered module calls for one need."""
    need_name:    str
    steps:        List[ChainStep]  = Field(default_factory=list)
    dependencies: List[str]        = Field(default_factory=list)
    # other need_names that must be done before this chain runs
    status:       Literal["pending", "running", "done", "skipped", "failed"] = "pending"
    outputs:      Dict[str, Any]   = Field(default_factory=dict)
    # final accumulated outputs after all steps complete

    model_config = {"arbitrary_types_allowed": True}


class BuildResult(BaseModel):
    """Structured output of ProjectBuildScenario.execute()."""
    success:       bool
    chains:        List[ExecutionChain]   = Field(default_factory=list)
    artifacts:     Dict[str, Any]         = Field(default_factory=dict)
    # artifacts[need_name] = chain outputs
    final_context: Dict[str, Any]         = Field(default_factory=dict)
    errors:        List[Dict[str, Any]]   = Field(default_factory=list)
    done:          int = 0
    skipped:       int = 0
    failed:        int = 0

    model_config = {"arbitrary_types_allowed": True}


# ── Scenario ───────────────────────────────────────────────────────────────────

class ProjectBuildScenario:
    """
    Execution counterpart of ProjectDefinitionScenario.

    Receives an execution_plan (list of dicts from ProjectDefinitionScenario),
    builds ExecutionChain objects from NEED_MODULE_CHAINS, executes them in
    dependency order, propagates context, and collects deliverables.

    Does NOT:
        - Parse briefs
        - Identify needs
        - Implement feature logic
        - Know about specific business domains

    Extensibility:
        - NEED_MODULE_CHAINS — define / override chains per need
        - register_executor(module_ref, fn) — inject callables
        - CONTEXT_PROPAGATION_KEYS — control what is shared across chains
    """

    VERSION = "1.0.0"
    NAME    = "project.build"

    # ── Canonical need → module chain definitions ─────────────────────────────
    #
    # Each entry: list of step dicts with:
    #   step_name   : str                 — logical name
    #   module_ref  : str                 — path to loadable module or registered executor
    #   input_map   : Dict[str, str]      — {arg_name: context_key}
    #   output_key  : str                 — key to store result under in context
    #   optional    : bool                — failure does not fail chain (default False)
    # ─────────────────────────────────────────────────────────────────────────

    NEED_MODULE_CHAINS: Dict[str, List[Dict[str, Any]]] = {

        "design_system": [
            {
                "step_name":  "visual_intent",
                "module_ref": "design_endpoints.design.visual_intent.generate",
                "input_map":  {"brief": "brief"},
                "output_key": "visual_intent",
            },
            {
                "step_name":  "palette",
                "module_ref": "design_endpoints.design.palette.generate",
                "input_map":  {"visual_intent": "visual_intent"},
                "output_key": "palette",
            },
            {
                "step_name":  "design_plan",
                "module_ref": "design_endpoints.design.plan.generate",
                "input_map":  {"brief": "brief", "seed": "seed", "visual_intent": "visual_intent"},
                "output_key": "design_plan",
            },
        ],

        "frontend": [
            {
                "step_name":  "render",
                "module_ref": "design_endpoints.design.render.page",
                "input_map":  {
                    "project_name": "project_name",
                    "brief_text":   "brief",
                    "seed":         "seed",
                    "cp_palette":   "palette",
                },
                "output_key": "render_result",
            },
            {
                "step_name":  "capture",
                "module_ref": "design_endpoints.design.capture.page",
                "input_map":  {"url": "url", "site": "project_name", "page": "page"},
                "output_key": "capture_result",
                "optional":   True,
            },
            {
                "step_name":  "audit",
                "module_ref": "design_endpoints.design.audit.page",
                "input_map":  {"captures": "captures", "api_key": "api_key"},
                "output_key": "audit_result",
                "optional":   True,
            },
            {
                "step_name":  "fix",
                "module_ref": "design_endpoints.design.fix.page",
                "input_map":  {"html": "html", "audit_results": "audit_result"},
                "output_key": "fix_result",
                "optional":   True,
            },
        ],

        "brand": [
            {
                "step_name":  "brand_identity",
                "module_ref": "brand_identity.generate_brand_identity",
                "input_map":  {
                    "brief":         "brief",
                    "visual_intent": "visual_intent",
                    "palette":       "palette",
                },
                "output_key": "brand_identity",
            },
        ],

        "backoffice": [
            {
                "step_name":  "dashboard",
                "module_ref": "document_objects.DashboardPage",
                "input_map":  {"project_name": "project_name", "design": "design_plan"},
                "output_key": "dashboard_html",
                "optional":   True,
            },
        ],

        "analytics": [
            {
                "step_name":  "widgets",
                "module_ref": "document_objects.DashboardWidget",
                "input_map":  {"datasets": "datasets", "design": "design_plan"},
                "output_key": "analytics_html",
                "optional":   True,
            },
        ],

        "documents": [
            {
                "step_name":  "invoice",
                "module_ref": "document_objects.InvoiceDoc",
                "input_map":  {"project_name": "project_name", "design": "design_plan"},
                "output_key": "invoice_html",
                "optional":   True,
            },
            {
                "step_name":  "quote",
                "module_ref": "document_objects.QuoteDoc",
                "input_map":  {"project_name": "project_name", "design": "design_plan"},
                "output_key": "quote_html",
                "optional":   True,
            },
        ],

        "email": [
            {
                "step_name":  "signature",
                "module_ref": "document_objects.EmailSignature",
                "input_map":  {"project_name": "project_name", "design": "design_plan"},
                "output_key": "email_signature_html",
                "optional":   True,
            },
        ],

        # Unimplemented — require executor injection
        "crm":      [],
        "payments": [],
        "auth":     [],
        "api":      [],
        "search":   [],
        "communication": [],
    }

    # ── Context propagation rules ─────────────────────────────────────────────
    #
    # After each chain completes, listed output keys are injected into
    # shared_context so downstream chains can consume them.
    # ─────────────────────────────────────────────────────────────────────────

    CONTEXT_PROPAGATION_KEYS: Dict[str, List[str]] = {
        "design_system": ["visual_intent", "palette", "design_plan"],
        "frontend":      ["html", "render_result"],
        "brand":         ["brand_identity"],
    }

    # ── Executor registry ─────────────────────────────────────────────────────

    _executor_registry: Dict[str, Any] = {}

    @classmethod
    def register_executor(cls, module_ref: str, executor: Any) -> None:
        """
        Register a callable for a module_ref.
        Callable signature: fn(**resolved_inputs) → Any
        Used in tests or injected by future agents.
        """
        cls._executor_registry[module_ref] = executor

    @classmethod
    def clear_executors(cls) -> None:
        cls._executor_registry.clear()

    # ── Step 1 — Build chains from flat execution_plan ────────────────────────

    def build_chains(
        self,
        execution_plan: List[Dict[str, Any]],
    ) -> List[ExecutionChain]:
        """
        Convert a flat execution_plan (from ProjectDefinitionScenario) into
        List[ExecutionChain] using NEED_MODULE_CHAINS.

        For each step in execution_plan:
          - look up canonical chain in NEED_MODULE_CHAINS
          - if found: use defined multi-step chain
          - if not found: fall back to single-step chain using the step's module_ref
        """
        chains: List[ExecutionChain] = []

        for plan_step in execution_plan:
            need_name  = plan_step.get("module_name", "")
            chain_defs = self.NEED_MODULE_CHAINS.get(need_name)
            deps       = plan_step.get("dependencies", [])

            if chain_defs is not None:
                steps = [
                    ChainStep(
                        step_name  = d["step_name"],
                        module_ref = d["module_ref"],
                        input_map  = d.get("input_map", {}),
                        output_key = d.get("output_key", d["step_name"]),
                        optional   = d.get("optional", False),
                    )
                    for d in chain_defs
                ]
            else:
                # Fallback: single step from the plan's module_ref
                module_ref = plan_step.get("module_ref", "")
                input_keys = list((plan_step.get("inputs") or {}).keys())
                steps = [
                    ChainStep(
                        step_name  = need_name,
                        module_ref = module_ref,
                        input_map  = {k: k for k in input_keys},
                        output_key = need_name,
                    )
                ]

            chains.append(ExecutionChain(
                need_name    = need_name,
                steps        = steps,
                dependencies = deps,
            ))

        return chains

    # ── Step 2 — Input resolution ─────────────────────────────────────────────

    def _resolve_inputs(
        self,
        step: ChainStep,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve concrete input values for a step from shared context.

        input_map = {arg_name: context_key}
        Only passes args whose context_key is present in context.
        """
        return {
            arg_name: context[ctx_key]
            for arg_name, ctx_key in step.input_map.items()
            if ctx_key in context
        }

    # ── Step 3 — Single step execution ───────────────────────────────────────

    def _execute_step(
        self,
        step:    ChainStep,
        context: Dict[str, Any],
    ) -> None:
        """
        Execute one ChainStep. Mutates step.status and step.output in place.
        On success: propagates output into context under step.output_key
                    and also flattens top-level dict keys into context.
        """
        executor = (
            self._executor_registry.get(step.module_ref)
            or self._try_load(step.module_ref)
        )

        if executor is None:
            step.status = "skipped"
            return

        step.status = "running"
        inputs = self._resolve_inputs(step, context)

        try:
            output       = executor(**inputs)
            step.status  = "done"
            step.output  = output

            key = step.output_key or step.step_name
            context[key] = output

            # Flatten top-level dict keys into context for easy downstream access
            if isinstance(output, dict):
                for k, v in output.items():
                    if k not in context:
                        context[k] = v

        except Exception as exc:
            step.status = "failed"
            step.error  = str(exc)

    # ── Step 4 — Chain execution ──────────────────────────────────────────────

    def _execute_chain(
        self,
        chain:   ExecutionChain,
        context: Dict[str, Any],
    ) -> None:
        """
        Execute all steps in a chain. Mutates chain in place.

        Failure rules:
          - required step fails → chain status = failed, remaining required steps skipped
          - optional step fails → logged, chain continues
          - chain completes with all required steps done → chain status = done
        """
        chain.status = "running"
        chain_failed = False

        for step in chain.steps:
            if chain_failed and not step.optional:
                step.status = "skipped"
                continue

            self._execute_step(step, context)

            if step.status == "failed" and not step.optional:
                chain_failed = True
                chain.outputs["__error__"] = step.error

        chain.status = "failed" if chain_failed else "done"

        # Collect all step outputs into chain.outputs
        for step in chain.steps:
            if step.output is not None:
                chain.outputs[step.output_key or step.step_name] = step.output

    # ── Step 5 — Execute all chains ───────────────────────────────────────────

    def execute(
        self,
        chains:    List[ExecutionChain],
        context:   Dict[str, Any],
        dry_run:   bool = False,
    ) -> BuildResult:
        """
        Execute chains in order, respecting cross-chain dependencies.

        dry_run=True: marks all steps as skipped without calling any module.

        Context propagation:
          After each chain completes, keys listed in CONTEXT_PROPAGATION_KEYS
          are merged into shared context for downstream chains.
        """
        completed:  Dict[str, str] = {}   # need_name → "done" | "failed" | "skipped"
        artifacts:  Dict[str, Any] = {}
        errors:     List[Dict]     = []

        for chain in chains:

            # Dependency check
            dep_failed = [
                dep for dep in chain.dependencies
                if completed.get(dep) in ("failed", "skipped")
            ]
            if dep_failed:
                chain.status = "skipped"
                completed[chain.need_name] = "skipped"
                errors.append({
                    "chain":  chain.need_name,
                    "reason": f"dependency failed or skipped: {dep_failed}",
                })
                continue

            if dry_run:
                for step in chain.steps:
                    step.status = "skipped"
                chain.status = "skipped"
                completed[chain.need_name] = "skipped"
                continue

            # No steps defined → skip silently
            if not chain.steps:
                chain.status = "skipped"
                completed[chain.need_name] = "skipped"
                continue

            self._execute_chain(chain, context)
            completed[chain.need_name] = chain.status

            if chain.status == "failed":
                errors.append({
                    "chain": chain.need_name,
                    "error": chain.outputs.get("__error__", "unknown"),
                })

            # Propagate listed keys into shared context
            prop_keys = self.CONTEXT_PROPAGATION_KEYS.get(chain.need_name, [])
            for key in prop_keys:
                if key in context:
                    context[key] = context[key]   # already in context from step execution
            # Also propagate all chain outputs into context
            for k, v in chain.outputs.items():
                if k != "__error__" and k not in context:
                    context[k] = v

            # Record artifacts
            if chain.outputs:
                artifacts[chain.need_name] = {
                    k: v for k, v in chain.outputs.items() if k != "__error__"
                }

        done    = sum(1 for c in chains if c.status == "done")
        skipped = sum(1 for c in chains if c.status == "skipped")
        failed  = sum(1 for c in chains if c.status == "failed")

        return BuildResult(
            success       = failed == 0,
            chains        = chains,
            artifacts     = artifacts,
            final_context = dict(context),
            errors        = errors,
            done          = done,
            skipped       = skipped,
            failed        = failed,
        )

    # ── Main entry point ──────────────────────────────────────────────────────

    def run(
        self,
        execution_plan:  List[Dict[str, Any]],
        initial_context: Optional[Dict[str, Any]] = None,
        dry_run:         bool = False,
    ) -> Dict[str, Any]:
        """
        Full build pipeline: execution_plan → chains → execute → deliverables.

        execution_plan: output of ProjectDefinitionScenario.run()["execution_plan"]

        Returns:
            success       : bool
            artifacts     : dict  — deliverables per need
            final_context : dict  — accumulated context after all chains
            errors        : list  — chain-level error records
            chains        : list  — full chain status (for tracing)
            done/skipped/failed : int counts
        """
        context = dict(initial_context or {})
        chains  = self.build_chains(execution_plan)
        result  = self.execute(chains, context, dry_run=dry_run)

        return {
            "success":       result.success,
            "artifacts":     result.artifacts,
            "final_context": result.final_context,
            "errors":        result.errors,
            "chains": [
                {
                    "need":   c.need_name,
                    "status": c.status,
                    "steps":  [
                        {
                            "step":   s.step_name,
                            "status": s.status,
                            **( {"error": s.error} if s.error else {} ),
                        }
                        for s in c.steps
                    ],
                }
                for c in result.chains
            ],
            "done":    result.done,
            "skipped": result.skipped,
            "failed":  result.failed,
        }

    # ── Dynamic module loading ────────────────────────────────────────────────

    def _try_load(self, module_ref: str):
        """
        Attempt to load an executor from MODULES/ by module_ref string.

        Patterns supported:
          A. "design_endpoints.design.visual_intent.generate"
             → MODULES/design_endpoints/design.visual_intent.generate.py → run()

          B. "brand_identity.generate_brand_identity"
             → MODULES/brand_identity/__init__.py import → getattr(generate_brand_identity)

        Returns callable or None.
        """
        modules_root = Path(__file__).parents[1]

        # Pattern A: "pkg.dotted.file.name" → pkg/dotted.file.name.py → run()
        parts = module_ref.split(".", 1)
        if len(parts) == 2:
            pkg, rest = parts
            path = modules_root / pkg / f"{rest}.py"
            if path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(module_ref, path)
                    mod  = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    return getattr(mod, "run", None)
                except Exception:
                    return None

        # Pattern B: "pkg.attribute" → importlib → getattr (functions only, not types)
        parts = module_ref.rsplit(".", 1)
        if len(parts) == 2:
            pkg_name, attr = parts
            pkg_path = modules_root / pkg_name
            if (pkg_path / "__init__.py").exists():
                try:
                    if str(modules_root) not in sys.path:
                        sys.path.insert(0, str(modules_root))
                    import importlib as il
                    mod   = il.import_module(pkg_name)
                    value = getattr(mod, attr, None)
                    # Return only plain functions/callables, not types/classes
                    # (document object classes like EmailSignature require explicit executor injection)
                    if value is not None and callable(value) and not isinstance(value, type):
                        return value
                except Exception:
                    return None

        return None

    # ── Self-test ─────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        scenario = cls()
        cls.clear_executors()

        # ── Minimal execution_plan (as produced by ProjectDefinitionScenario) ──
        plan = [
            {
                "order": 1, "module_name": "design_system",
                "module_ref": "design_endpoints.design.plan.generate",
                "inputs": {"brief": None, "seed": None}, "dependencies": [],
            },
            {
                "order": 2, "module_name": "frontend",
                "module_ref": "design_endpoints.design.render.page",
                "inputs": {"brief": None, "project_name": None}, "dependencies": ["design_system"],
            },
        ]

        # dry_run → nothing executed
        result = scenario.run(plan, dry_run=True)
        assert result["done"] == 0
        assert result["skipped"] >= 1
        assert result["success"] is True  # no failures

        # inject executors
        vi_output  = {"emotion": "calm", "mood": "neutral", "archetype": "startup"}
        pal_output = {"primary": "#1a1a2e", "accent": "#6366f1", "background": "#f8fafc"}
        dp_output  = {"layout_strategy": "editorial", "hero": "centered"}
        rend_output = {"html": "<html>ok</html>", "project_name": "test", "seed": 42}

        cls.register_executor("design_endpoints.design.visual_intent.generate",
                               lambda brief, **_: vi_output)
        cls.register_executor("design_endpoints.design.palette.generate",
                               lambda visual_intent, **_: pal_output)
        cls.register_executor("design_endpoints.design.plan.generate",
                               lambda brief, seed=42, visual_intent=None, **_: dp_output)
        cls.register_executor("design_endpoints.design.render.page",
                               lambda project_name="", brief_text="", seed=42, cp_palette=None, **_: rend_output)

        ctx = {"brief": "SaaS RH pour PME", "project_name": "MonSaaS", "seed": 42}
        result2 = scenario.run(plan, initial_context=ctx, dry_run=False)

        assert result2["done"] >= 1
        assert "design_system" in result2["artifacts"]
        assert result2["final_context"].get("visual_intent") == vi_output
        assert result2["final_context"].get("palette")       == pal_output

        cls.clear_executors()
        return True
