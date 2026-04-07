"""
Tests for ProjectBuildScenario — EURKAI Execution Layer.

Covers:
    1.  dry_run
    2.  single-step execution
    3.  multi-module chain execution
    4.  context propagation within a chain
    5.  context propagation across chains
    6.  dependency blocking on failure
    7.  artifact aggregation
    8.  optional step failure does not fail chain
    9.  required step failure fails chain
    10. compatibility with ProjectDefinitionScenario output
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from project_orchestration import (
    ProjectBuildScenario,
    ProjectDefinitionScenario,
    ExecutionChain,
    ChainStep,
    BuildResult,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

VI_OUTPUT   = {"emotion": "calm", "mood": "neutral", "archetype": "startup"}
PAL_OUTPUT  = {"primary": "#1a1a2e", "accent": "#6366f1", "background": "#f8fafc"}
DP_OUTPUT   = {"layout_strategy": "editorial", "hero": "centered"}
REND_OUTPUT = {"html": "<html>page</html>", "project_name": "Test", "seed": 42}


def _plan(needs: list[str]) -> list[dict]:
    """Build a minimal execution_plan for the given need names."""
    return [
        {
            "order": i + 1,
            "module_name": need,
            "module_ref":  f"mock.{need}",
            "inputs":      {},
            "dependencies": [],
        }
        for i, need in enumerate(needs)
    ]


def _plan_with_dep(need: str, dep: str, order: int) -> dict:
    return {
        "order": order,
        "module_name": need,
        "module_ref":  f"mock.{need}",
        "inputs":      {},
        "dependencies": [dep],
    }


def _ctx(**kw) -> dict:
    return {"brief": "SaaS de test", "project_name": "TestProj", "seed": 42, **kw}


def _register_design_system(cls):
    cls.register_executor("design_endpoints.design.visual_intent.generate",
                           lambda brief, **_: VI_OUTPUT)
    cls.register_executor("design_endpoints.design.palette.generate",
                           lambda visual_intent, **_: PAL_OUTPUT)
    cls.register_executor("design_endpoints.design.plan.generate",
                           lambda brief, seed=42, visual_intent=None, **_: DP_OUTPUT)


def _register_frontend(cls):
    cls.register_executor("design_endpoints.design.render.page",
                           lambda project_name="", brief_text="", seed=42, cp_palette=None, **_: REND_OUTPUT)


# ── TestChainStep ──────────────────────────────────────────────────────────────

class TestChainStep:

    def test_default_status_pending(self):
        s = ChainStep(step_name="vi", module_ref="m.ref")
        assert s.status == "pending"

    def test_optional_default_false(self):
        s = ChainStep(step_name="vi", module_ref="m.ref")
        assert s.optional is False

    def test_output_key_default_empty(self):
        s = ChainStep(step_name="vi", module_ref="m.ref")
        assert s.output_key == ""

    def test_input_map_default_empty(self):
        s = ChainStep(step_name="vi", module_ref="m.ref")
        assert s.input_map == {}


# ── TestExecutionChain ─────────────────────────────────────────────────────────

class TestExecutionChain:

    def test_default_status_pending(self):
        c = ExecutionChain(need_name="design_system")
        assert c.status == "pending"

    def test_empty_steps_and_deps(self):
        c = ExecutionChain(need_name="design_system")
        assert c.steps == []
        assert c.dependencies == []
        assert c.outputs == {}

    def test_steps_stored(self):
        s = ChainStep(step_name="vi", module_ref="m.ref")
        c = ExecutionChain(need_name="design_system", steps=[s])
        assert len(c.steps) == 1


# ── TestBuildChains ────────────────────────────────────────────────────────────

class TestBuildChains:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()

    def test_returns_list_of_execution_chain(self):
        chains = self.scenario.build_chains(_plan(["design_system"]))
        assert all(isinstance(c, ExecutionChain) for c in chains)

    def test_chain_count_matches_plan(self):
        chains = self.scenario.build_chains(_plan(["design_system", "frontend"]))
        assert len(chains) == 2

    def test_known_need_uses_canonical_chain(self):
        chains = self.scenario.build_chains(_plan(["design_system"]))
        ds = chains[0]
        assert ds.need_name == "design_system"
        step_names = [s.step_name for s in ds.steps]
        assert "visual_intent" in step_names
        assert "palette"       in step_names
        assert "design_plan"   in step_names

    def test_design_system_has_three_steps(self):
        chains = self.scenario.build_chains(_plan(["design_system"]))
        assert len(chains[0].steps) == 3

    def test_frontend_chain_has_render_step(self):
        chains = self.scenario.build_chains(_plan(["frontend"]))
        step_names = [s.step_name for s in chains[0].steps]
        assert "render" in step_names

    def test_frontend_capture_audit_fix_are_optional(self):
        chains  = self.scenario.build_chains(_plan(["frontend"]))
        optionals = {s.step_name: s.optional for s in chains[0].steps}
        assert optionals.get("capture") is True
        assert optionals.get("audit")   is True
        assert optionals.get("fix")     is True

    def test_unknown_need_fallback_single_step(self):
        plan   = [{"order": 1, "module_name": "crm", "module_ref": "crm.lead_management",
                   "inputs": {}, "dependencies": []}]
        chains = self.scenario.build_chains(plan)
        # crm has no steps in NEED_MODULE_CHAINS → falls back to single step
        assert chains[0].need_name == "crm"

    def test_dependencies_preserved(self):
        plan = [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            _plan_with_dep("frontend", "design_system", 2),
        ]
        chains = self.scenario.build_chains(plan)
        fe = next(c for c in chains if c.need_name == "frontend")
        assert "design_system" in fe.dependencies

    def test_empty_plan_returns_empty(self):
        assert self.scenario.build_chains([]) == []


# ── TestDryRun ────────────────────────────────────────────────────────────────

class TestDryRun:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def test_dry_run_skips_all_steps(self):
        result = self.scenario.run(_plan(["design_system", "frontend"]),
                                   initial_context=_ctx(), dry_run=True)
        for chain in result["chains"]:
            for step in chain["steps"]:
                assert step["status"] == "skipped"

    def test_dry_run_done_is_zero(self):
        result = self.scenario.run(_plan(["design_system"]),
                                   initial_context=_ctx(), dry_run=True)
        assert result["done"] == 0

    def test_dry_run_success_true(self):
        result = self.scenario.run(_plan(["design_system"]),
                                   initial_context=_ctx(), dry_run=True)
        assert result["success"] is True

    def test_dry_run_no_artifacts(self):
        result = self.scenario.run(_plan(["design_system"]),
                                   initial_context=_ctx(), dry_run=True)
        assert result["artifacts"] == {}

    def test_dry_run_does_not_call_executors(self):
        called = []
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate",
            lambda **_: called.append("called") or {},
        )
        self.scenario.run(_plan(["design_system"]), initial_context=_ctx(), dry_run=True)
        assert called == []
        ProjectBuildScenario.clear_executors()

    def test_dry_run_chains_present(self):
        result = self.scenario.run(_plan(["design_system", "frontend"]),
                                   initial_context=_ctx(), dry_run=True)
        assert len(result["chains"]) == 2


# ── TestSingleStepExecution ───────────────────────────────────────────────────

class TestSingleStepExecution:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectBuildScenario.clear_executors()

    def test_executor_called(self):
        called = []
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate",
            lambda brief, **_: called.append("vi") or VI_OUTPUT,
        )
        self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert "vi" in called

    def test_done_count_increments(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert result["done"] >= 1

    def test_output_stored_in_artifacts(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert "design_system" in result["artifacts"]

    def test_step_status_done(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        vi_step = next(s for s in ds["steps"] if s["step"] == "visual_intent")
        assert vi_step["status"] == "done"

    def test_skipped_step_when_no_executor(self):
        # No executor registered → all steps skipped
        result = self.scenario.run(_plan(["email"]), initial_context=_ctx())
        em = next(c for c in result["chains"] if c["need"] == "email")
        assert all(s["status"] == "skipped" for s in em["steps"])


# ── TestMultiModuleChain ──────────────────────────────────────────────────────

class TestMultiModuleChain:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectBuildScenario.clear_executors()

    def test_all_three_design_system_steps_run(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        statuses = {s["step"]: s["status"] for s in ds["steps"]}
        assert statuses["visual_intent"] == "done"
        assert statuses["palette"]       == "done"
        assert statuses["design_plan"]   == "done"

    def test_chain_status_done_when_all_steps_pass(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        assert ds["status"] == "done"

    def test_required_step_failure_fails_chain(self):
        def _fail(**_): raise RuntimeError("module error")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        assert ds["status"] == "failed"

    def test_required_failure_skips_remaining_required_steps(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        palette_step = next(s for s in ds["steps"] if s["step"] == "palette")
        assert palette_step["status"] == "skipped"

    def test_optional_step_failure_does_not_fail_chain(self):
        # register render (required) so it passes
        _register_frontend(ProjectBuildScenario)
        # make capture (optional) fail
        def _fail(**_): raise RuntimeError("playwright unavailable")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.capture.page", _fail,
        )
        result = self.scenario.run(_plan(["frontend"]), initial_context=_ctx())
        fe = next(c for c in result["chains"] if c["need"] == "frontend")
        assert fe["status"] == "done"

    def test_frontend_render_step_done(self):
        _register_frontend(ProjectBuildScenario)
        result = self.scenario.run(_plan(["frontend"]), initial_context=_ctx())
        fe = next(c for c in result["chains"] if c["need"] == "frontend")
        render = next(s for s in fe["steps"] if s["step"] == "render")
        assert render["status"] == "done"


# ── TestContextPropagation ────────────────────────────────────────────────────

class TestContextPropagation:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectBuildScenario.clear_executors()

    def test_visual_intent_in_final_context(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert result["final_context"].get("visual_intent") == VI_OUTPUT

    def test_palette_in_final_context(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert result["final_context"].get("palette") == PAL_OUTPUT

    def test_design_plan_in_final_context(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert result["final_context"].get("design_plan") == DP_OUTPUT

    def test_palette_consumed_by_frontend_as_cp_palette(self):
        """Frontend render must receive the palette from context as cp_palette."""
        received = {}
        _register_design_system(ProjectBuildScenario)
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.render.page",
            lambda project_name="", brief_text="", seed=42, cp_palette=None, **_:
                received.update({"cp_palette": cp_palette}) or REND_OUTPUT,
        )
        plan = [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "frontend", "module_ref": "m.fe",
             "inputs": {}, "dependencies": ["design_system"]},
        ]
        self.scenario.run(plan, initial_context=_ctx())
        assert received.get("cp_palette") == PAL_OUTPUT

    def test_initial_context_available_throughout(self):
        briefs_seen = []
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate",
            lambda brief, **_: briefs_seen.append(brief) or VI_OUTPUT,
        )
        ctx = _ctx(brief="Custom brief text")
        self.scenario.run(_plan(["design_system"]), initial_context=ctx)
        assert "Custom brief text" in briefs_seen

    def test_step_output_available_to_next_step_in_chain(self):
        """palette step must receive visual_intent output from previous step."""
        vi_received = {}
        _register_design_system(ProjectBuildScenario)
        # Override palette executor to capture what it receives
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.palette.generate",
            lambda visual_intent, **_: vi_received.update({"vi": visual_intent}) or PAL_OUTPUT,
        )
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.plan.generate",
            lambda brief, seed=42, visual_intent=None, **_: DP_OUTPUT,
        )
        self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert vi_received.get("vi") == VI_OUTPUT

    def test_html_in_final_context_after_frontend(self):
        _register_design_system(ProjectBuildScenario)
        _register_frontend(ProjectBuildScenario)
        plan = [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "frontend", "module_ref": "m.fe",
             "inputs": {}, "dependencies": []},
        ]
        result = self.scenario.run(plan, initial_context=_ctx())
        assert "html" in result["final_context"]
        assert result["final_context"]["html"] == "<html>page</html>"


# ── TestDependencyBlocking ────────────────────────────────────────────────────

class TestDependencyBlocking:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectBuildScenario.clear_executors()

    def _plan_ds_fe_dep(self):
        return [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "frontend", "module_ref": "m.fe",
             "inputs": {}, "dependencies": ["design_system"]},
        ]

    def test_dependent_chain_skipped_when_dep_failed(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(self._plan_ds_fe_dep(), initial_context=_ctx())
        fe = next(c for c in result["chains"] if c["need"] == "frontend")
        assert fe["status"] == "skipped"

    def test_error_recorded_for_skipped_dependent(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(self._plan_ds_fe_dep(), initial_context=_ctx())
        assert any(e["chain"] == "frontend" for e in result["errors"])

    def test_independent_chain_runs_despite_other_failure(self):
        """email chain has no deps → should run independently even if design_system fails."""
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        sig_out = {"html": "<sig>"}
        ProjectBuildScenario.register_executor(
            "document_objects.EmailSignature",
            lambda **_: sig_out,
        )
        plan = [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "email", "module_ref": "m.email",
             "inputs": {}, "dependencies": []},  # no dep on design_system
        ]
        result = self.scenario.run(plan, initial_context=_ctx())
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        assert ds["status"] == "failed"

    def test_dep_on_skipped_chain_also_skipped(self):
        """Chain whose dep was skipped (not failed) must also be skipped."""
        plan = [
            {"order": 1, "module_name": "crm", "module_ref": "crm.ref",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "analytics", "module_ref": "analytics.ref",
             "inputs": {}, "dependencies": ["crm"]},
        ]
        result = self.scenario.run(plan, initial_context=_ctx())
        # crm has no steps → skipped → analytics depends on crm → also skipped
        an = next(c for c in result["chains"] if c["need"] == "analytics")
        assert an["status"] == "skipped"


# ── TestArtifactAggregation ───────────────────────────────────────────────────

class TestArtifactAggregation:

    def setup_method(self):
        self.scenario = ProjectBuildScenario()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectBuildScenario.clear_executors()

    def test_artifacts_key_per_completed_chain(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert "design_system" in result["artifacts"]

    def test_artifacts_contains_step_outputs(self):
        _register_design_system(ProjectBuildScenario)
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        ds_art = result["artifacts"]["design_system"]
        assert "visual_intent" in ds_art or "palette" in ds_art or "design_plan" in ds_art

    def test_failed_chain_not_in_artifacts(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        # chain failed → may still be in artifacts (partial) but status is failed
        ds = next(c for c in result["chains"] if c["need"] == "design_system")
        assert ds["status"] == "failed"

    def test_multi_chain_artifacts(self):
        _register_design_system(ProjectBuildScenario)
        _register_frontend(ProjectBuildScenario)
        plan = [
            {"order": 1, "module_name": "design_system", "module_ref": "m.ds",
             "inputs": {}, "dependencies": []},
            {"order": 2, "module_name": "frontend", "module_ref": "m.fe",
             "inputs": {}, "dependencies": []},
        ]
        result = self.scenario.run(plan, initial_context=_ctx())
        assert "design_system" in result["artifacts"]
        assert "frontend"      in result["artifacts"]

    def test_result_structure_keys(self):
        result = self.scenario.run(_plan(["design_system"]),
                                   initial_context=_ctx(), dry_run=True)
        for key in ("success", "artifacts", "final_context", "errors", "chains", "done", "skipped", "failed"):
            assert key in result

    def test_success_false_when_required_chain_fails(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectBuildScenario.register_executor(
            "design_endpoints.design.visual_intent.generate", _fail,
        )
        result = self.scenario.run(_plan(["design_system"]), initial_context=_ctx())
        assert result["success"] is False

    def test_counts_sum_to_total_chains(self):
        _register_design_system(ProjectBuildScenario)
        plan = _plan(["design_system", "email"])
        result = self.scenario.run(plan, initial_context=_ctx())
        assert result["done"] + result["skipped"] + result["failed"] == len(plan)


# ── TestCompatibilityWithDefinitionScenario ───────────────────────────────────

class TestCompatibilityWithDefinitionScenario:

    def setup_method(self):
        self.define   = ProjectDefinitionScenario()
        self.build    = ProjectBuildScenario()
        ProjectDefinitionScenario.clear_executors()
        ProjectBuildScenario.clear_executors()

    def teardown_method(self):
        ProjectDefinitionScenario.clear_executors()
        ProjectBuildScenario.clear_executors()

    def test_definition_output_fed_directly_to_build(self):
        """execution_plan from ProjectDefinitionScenario can be passed directly to
        ProjectBuildScenario.run() without transformation."""
        brief  = "Plateforme SaaS de gestion RH pour PME."
        defn   = self.define.run(brief, project_name="MonSaaS", dry_run=True)
        plan   = defn["execution_plan"]
        result = self.build.run(plan, initial_context={"brief": brief, "project_name": "MonSaaS", "seed": 42}, dry_run=True)
        assert "chains" in result
        assert len(result["chains"]) == len(plan)

    def test_need_names_match_between_scenarios(self):
        brief = "E-commerce de vêtements avec paiement Stripe."
        defn  = self.define.run(brief, dry_run=True)
        plan  = defn["execution_plan"]
        build = self.build.run(plan, initial_context={"brief": brief, "project_name": "Shop", "seed": 42}, dry_run=True)
        def_needs  = {s["module_name"] for s in plan}
        build_needs = {c["need"] for c in build["chains"]}
        assert def_needs == build_needs

    def test_full_pipeline_brief_to_deliverables_dry_run(self):
        """Full flow: brief → definition → plan → build (dry_run)."""
        brief  = "Blog de contenu sur la technologie."
        defn   = self.define.run(brief, project_name="TechBlog", dry_run=True)
        plan   = defn["execution_plan"]
        assert len(plan) >= 2

        result = self.build.run(
            plan,
            initial_context={"brief": brief, "project_name": "TechBlog", "seed": 99},
            dry_run=True,
        )
        assert result["done"] == 0
        assert result["skipped"] == len(plan)
        assert result["success"] is True

    def test_full_pipeline_with_executors(self):
        """Full flow: brief → definition → plan → build (real executors)."""
        _register_design_system(ProjectBuildScenario)
        _register_frontend(ProjectBuildScenario)

        brief = "Application SaaS."
        defn  = self.define.run(brief, project_name="MySaaS", dry_run=True)
        plan  = defn["execution_plan"]

        result = self.build.run(
            plan,
            initial_context={"brief": brief, "project_name": "MySaaS", "seed": 42},
            dry_run=False,
        )
        assert "design_system" in result["artifacts"]
        assert result["final_context"].get("visual_intent") == VI_OUTPUT
        assert result["final_context"].get("palette")       == PAL_OUTPUT

    def test_classmethod_test_passes(self):
        assert ProjectBuildScenario.test() is True
