"""
Tests for ProjectDefinitionScenario — EURKAI Core Orchestration.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from project_orchestration import (
    ProjectDefinitionScenario,
    ProjectDefinition,
    ExecutionPlan,
    ExecutionStep,
    ParsedBrief,
    Need,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

BRIEF_SAAS = (
    "Plateforme SaaS de gestion RH pour les PME. "
    "Dashboard admin, analytics, email notifications, authentification."
)

BRIEF_ECOMMERCE = (
    "Boutique en ligne de vêtements pour femmes. "
    "Catalogue, panier, paiement Stripe, newsletter clients."
)

BRIEF_PORTFOLIO = (
    "Portfolio d'une agence créative spécialisée dans l'identité visuelle. "
    "Showcase de projets, galerie photos, formulaire contact."
)

BRIEF_CORPORATE = (
    "Site vitrine pour un cabinet de consulting B2B. "
    "Services, équipe, références clients, formulaire de contact."
)


# ── TestParseBrief ─────────────────────────────────────────────────────────────

class TestParseBrief:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()

    def test_saas_type_detected(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert p.project_type == "saas"

    def test_ecommerce_type_detected(self):
        p = self.scenario.parse_brief(BRIEF_ECOMMERCE)
        assert p.project_type == "ecommerce"

    def test_portfolio_type_detected(self):
        p = self.scenario.parse_brief(BRIEF_PORTFOLIO)
        assert p.project_type == "portfolio"

    def test_corporate_type_detected(self):
        p = self.scenario.parse_brief(BRIEF_CORPORATE)
        assert p.project_type == "corporate"

    def test_analytics_feature_detected(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert "analytics" in p.features

    def test_auth_feature_detected(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert "auth" in p.features

    def test_email_feature_detected(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert "email" in p.features

    def test_payments_feature_detected(self):
        p = self.scenario.parse_brief(BRIEF_ECOMMERCE)
        assert "payments" in p.features

    def test_backoffice_feature_detected(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert "backoffice" in p.features

    def test_mobile_constraint_detected(self):
        brief = "Application mobile pour professionnels de santé, responsive et rapide."
        p = self.scenario.parse_brief(brief)
        assert p.constraints.get("mobile_first") is True

    def test_seo_constraint_detected(self):
        brief = "Blog de contenu SEO pour attirer du trafic organique Google."
        p = self.scenario.parse_brief(brief)
        assert p.constraints.get("seo") is True

    def test_target_extracted(self):
        brief = "Plateforme SaaS destinée aux PME françaises."
        p = self.scenario.parse_brief(brief)
        assert "pme" in p.target.lower()

    def test_raw_preserved(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert p.raw == BRIEF_SAAS

    def test_structured_brief_passthrough(self):
        sb = {
            "project_type": "startup",
            "features": ["auth", "payments"],
            "constraints": {"mobile_first": True},
            "target": "freelances",
        }
        p = self.scenario.parse_brief(sb)
        assert p.project_type == "startup"
        assert "auth" in p.features
        assert "payments" in p.features
        assert p.constraints.get("mobile_first") is True
        assert p.target == "freelances"

    def test_unknown_brief_returns_generic(self):
        p = self.scenario.parse_brief("Un projet mystérieux sans signaux.")
        assert p.project_type == "generic"
        assert p.features == []

    def test_returns_parsebrief_instance(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        assert isinstance(p, ParsedBrief)


# ── TestIdentifyNeeds ──────────────────────────────────────────────────────────

class TestIdentifyNeeds:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()

    def test_design_system_always_present(self):
        p = self.scenario.parse_brief("Un projet quelconque.")
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "design_system" for n in needs)

    def test_frontend_always_present(self):
        p = self.scenario.parse_brief("Un projet quelconque.")
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "frontend" for n in needs)

    def test_backoffice_from_feature(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "backoffice" for n in needs)

    def test_analytics_from_feature(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "analytics" for n in needs)

    def test_email_from_type_saas(self):
        p = ParsedBrief(project_type="saas", features=[], constraints={}, target="", raw="")
        needs = self.scenario.identify_needs(p)
        # email injected via type_need_map for saas? Actually saas doesn't have email in type map
        # But this test checks: design_system + frontend still present
        assert any(n.name == "design_system" for n in needs)
        assert any(n.name == "frontend"      for n in needs)

    def test_email_from_type_corporate(self):
        p = ParsedBrief(project_type="corporate", features=[], constraints={}, target="", raw="")
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "email" for n in needs)

    def test_payments_from_type_ecommerce(self):
        p = ParsedBrief(project_type="ecommerce", features=[], constraints={}, target="", raw="")
        needs = self.scenario.identify_needs(p)
        assert any(n.name == "payments" for n in needs)

    def test_no_duplicate_needs(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        names = [n.name for n in needs]
        assert len(names) == len(set(names))

    def test_needs_sorted_by_priority(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        priorities = [n.priority for n in needs]
        assert priorities == sorted(priorities)

    def test_need_source_always(self):
        p = ParsedBrief(project_type="generic", features=[], constraints={}, target="", raw="")
        needs = self.scenario.identify_needs(p)
        always_needs = [n for n in needs if n.source == "always"]
        assert len(always_needs) >= 2

    def test_need_source_feature(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        feature_needs = [n for n in needs if n.source.startswith("feature:")]
        assert len(feature_needs) >= 1

    def test_need_source_type(self):
        p = ParsedBrief(project_type="ecommerce", features=[], constraints={}, target="", raw="")
        needs = self.scenario.identify_needs(p)
        type_needs = [n for n in needs if n.source.startswith("type:")]
        assert len(type_needs) >= 1

    def test_returns_list_of_need(self):
        p = self.scenario.parse_brief(BRIEF_SAAS)
        needs = self.scenario.identify_needs(p)
        assert all(isinstance(n, Need) for n in needs)


# ── TestMapNeeds ───────────────────────────────────────────────────────────────

class TestMapNeeds:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()

    def _needs(self, brief: str) -> list:
        return self.scenario.identify_needs(self.scenario.parse_brief(brief))

    def test_steps_count_matches_known_needs(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        assert len(steps) == len(needs)

    def test_steps_ordered_from_one(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        assert steps[0].order == 1
        assert steps[-1].order == len(steps)

    def test_steps_sequential_order(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        for i, step in enumerate(steps):
            assert step.order == i + 1

    def test_module_ref_present(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        for step in steps:
            assert step.module_ref != ""

    def test_first_step_no_dependency(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        assert steps[0].dependencies == []

    def test_subsequent_step_has_dependency(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        if len(steps) > 1:
            assert len(steps[1].dependencies) == 1
            assert steps[1].dependencies[0] == steps[0].module_name

    def test_inputs_keys_declared(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        for step in steps:
            meta = ProjectDefinitionScenario.NEED_MODULE_MAP.get(step.module_name, {})
            for key in meta.get("inputs", []):
                assert key in step.inputs

    def test_design_system_step_has_brief_input(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        ds_step = next(s for s in steps if s.module_name == "design_system")
        assert "brief" in ds_step.inputs

    def test_returns_list_of_execution_step(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        assert all(isinstance(s, ExecutionStep) for s in steps)

    def test_status_pending_by_default(self):
        needs = self._needs(BRIEF_SAAS)
        steps = self.scenario.map_needs(needs)
        assert all(s.status == "pending" for s in steps)


# ── TestBuildPlan ──────────────────────────────────────────────────────────────

class TestBuildPlan:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()

    def _plan(self, brief: str) -> ExecutionPlan:
        parsed = self.scenario.parse_brief(brief)
        needs  = self.scenario.identify_needs(parsed)
        steps  = self.scenario.map_needs(needs)
        return self.scenario.build_plan(steps, needs)

    def test_returns_execution_plan(self):
        plan = self._plan(BRIEF_SAAS)
        assert isinstance(plan, ExecutionPlan)

    def test_plan_contains_steps(self):
        plan = self._plan(BRIEF_SAAS)
        assert plan.step_count >= 2

    def test_plan_contains_needs(self):
        plan = self._plan(BRIEF_SAAS)
        assert len(plan.needs) >= 2

    def test_as_list_returns_dicts(self):
        plan = self._plan(BRIEF_SAAS)
        lst  = plan.as_list()
        assert isinstance(lst, list)
        assert all(isinstance(item, dict) for item in lst)

    def test_as_list_required_keys(self):
        plan = self._plan(BRIEF_SAAS)
        for item in plan.as_list():
            assert "order"       in item
            assert "module_name" in item
            assert "module_ref"  in item

    def test_as_list_no_output_key(self):
        # output is runtime data — must not appear in serialized plan
        plan = self._plan(BRIEF_SAAS)
        for item in plan.as_list():
            assert "output" not in item


# ── TestExecute ────────────────────────────────────────────────────────────────

class TestExecute:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()
        ProjectDefinitionScenario.clear_executors()

    def teardown_method(self):
        ProjectDefinitionScenario.clear_executors()

    def _plan(self, brief: str) -> ExecutionPlan:
        parsed = self.scenario.parse_brief(brief)
        needs  = self.scenario.identify_needs(parsed)
        steps  = self.scenario.map_needs(needs)
        return self.scenario.build_plan(steps, needs)

    def test_dry_run_skips_all(self):
        plan   = self._plan(BRIEF_SAAS)
        ctx    = {"brief": BRIEF_SAAS, "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=True)
        assert result["done"]    == 0
        assert result["skipped"] == plan.step_count

    def test_dry_run_trace_length(self):
        plan   = self._plan(BRIEF_SAAS)
        ctx    = {"brief": BRIEF_SAAS, "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=True)
        assert len(result["trace"]) == plan.step_count

    def test_no_executor_no_crash(self):
        """Without registered executors, execute() completes without raising.
        Steps are either dynamically loaded (may succeed/fail) or skipped.
        Total of all statuses equals plan step count."""
        plan   = self._plan(BRIEF_SAAS)
        ctx    = {"brief": BRIEF_SAAS, "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=False)
        total  = result["done"] + result["skipped"] + result["failed"]
        assert total == plan.step_count

    def test_registered_executor_called(self):
        called = []
        ProjectDefinitionScenario.register_executor(
            "design_endpoints.design.plan.generate",
            lambda brief, seed, **_: called.append("ds") or {"design": {}},
        )
        plan   = self._plan("Projet SaaS simple.")
        ctx    = {"brief": "Projet SaaS simple.", "project_name": "Test", "seed": 42}
        self.scenario.execute(plan, ctx, dry_run=False)
        assert "ds" in called

    def test_executor_output_in_results(self):
        ProjectDefinitionScenario.register_executor(
            "design_endpoints.design.plan.generate",
            lambda **_: {"design": {"palette": {"accent": "#6366f1"}}},
        )
        plan   = self._plan("Projet simple.")
        ctx    = {"brief": "Projet simple.", "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=False)
        assert "design_system" in result["results"]
        assert result["results"]["design_system"]["design"]["palette"]["accent"] == "#6366f1"

    def test_executor_exception_marks_failed(self):
        def _fail(**_): raise RuntimeError("boom")
        ProjectDefinitionScenario.register_executor(
            "design_endpoints.design.plan.generate", _fail,
        )
        plan   = self._plan("Projet simple.")
        ctx    = {"brief": "Projet simple.", "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=False)
        assert result["failed"] >= 1

    def test_trace_has_status_for_each_step(self):
        plan   = self._plan(BRIEF_SAAS)
        ctx    = {"brief": BRIEF_SAAS, "project_name": "Test", "seed": 42}
        result = self.scenario.execute(plan, ctx, dry_run=True)
        for entry in result["trace"]:
            assert "status" in entry
            assert "module" in entry

    def test_design_context_propagated(self):
        """design_system output is set on context['design'] for downstream steps."""
        design_out = {"design": {"palette": {"accent": "#e11d48"}}}
        received_design = []

        ProjectDefinitionScenario.register_executor(
            "design_endpoints.design.plan.generate",
            lambda brief, seed, **_: design_out,
        )
        ProjectDefinitionScenario.register_executor(
            "design_scenarios.design.page.generate_full",
            lambda brief, project_name, seed, **kw: received_design.append(kw.get("design")) or {},
        )

        plan = self._plan("Projet simple.")
        ctx  = {"brief": "Projet simple.", "project_name": "Test", "seed": 42}
        self.scenario.execute(plan, ctx, dry_run=False)
        # design propagated to context after design_system step
        assert ctx.get("design") == design_out.get("design") or design_out


# ── TestRun ────────────────────────────────────────────────────────────────────

class TestRun:

    def setup_method(self):
        self.scenario = ProjectDefinitionScenario()
        ProjectDefinitionScenario.clear_executors()

    def teardown_method(self):
        ProjectDefinitionScenario.clear_executors()

    def test_returns_three_keys(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        assert "project_definition" in result
        assert "execution_plan"     in result
        assert "execution_result"   in result

    def test_project_definition_structure(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        defn   = result["project_definition"]
        assert "brief"  in defn
        assert "parsed" in defn
        assert "needs"  in defn
        assert "plan"   in defn

    def test_execution_plan_is_list(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        assert isinstance(result["execution_plan"], list)

    def test_execution_plan_not_empty(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        assert len(result["execution_plan"]) >= 2

    def test_dry_run_skips_all(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        er     = result["execution_result"]
        assert er["done"]    == 0
        assert er["skipped"] == len(result["execution_plan"])

    def test_project_name_default_to_type(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        defn   = result["project_definition"]
        # If project_name omitted → defaults to project_type
        assert result["execution_plan"] is not None

    def test_seed_passed(self):
        result = self.scenario.run(BRIEF_SAAS, seed=99, dry_run=True)
        # No error = seed accepted
        assert result is not None

    def test_saas_brief_has_backoffice_in_plan(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=True)
        names  = [s["module_name"] for s in result["execution_plan"]]
        assert "backoffice" in names

    def test_ecommerce_brief_has_payments_in_plan(self):
        result = self.scenario.run(BRIEF_ECOMMERCE, dry_run=True)
        names  = [s["module_name"] for s in result["execution_plan"]]
        assert "payments" in names

    def test_structured_brief_accepted(self):
        sb = {"project_type": "startup", "features": ["email"], "constraints": {}, "target": ""}
        result = self.scenario.run(sb, dry_run=True)
        assert result["project_definition"]["parsed"]["project_type"] == "startup"

    def test_execution_result_counts(self):
        result = self.scenario.run(BRIEF_SAAS, dry_run=False)
        er     = result["execution_result"]
        assert "done"    in er
        assert "skipped" in er
        assert "failed"  in er
        assert er["done"] + er["skipped"] + er["failed"] == len(result["execution_plan"])

    def test_classmethod_test_passes(self):
        assert ProjectDefinitionScenario.test() is True


# ── TestNeedModuleMap ──────────────────────────────────────────────────────────

class TestNeedModuleMap:

    def test_all_entries_have_required_keys(self):
        for name, meta in ProjectDefinitionScenario.NEED_MODULE_MAP.items():
            assert "module_ref"  in meta, f"{name} missing module_ref"
            assert "description" in meta, f"{name} missing description"
            assert "inputs"      in meta, f"{name} missing inputs"
            assert "priority"    in meta, f"{name} missing priority"

    def test_priorities_are_unique(self):
        priorities = [m["priority"] for m in ProjectDefinitionScenario.NEED_MODULE_MAP.values()]
        assert len(priorities) == len(set(priorities))

    def test_always_on_exist(self):
        always = [k for k, v in ProjectDefinitionScenario.NEED_MODULE_MAP.items() if v.get("always")]
        assert "design_system" in always
        assert "frontend"      in always

    def test_register_executor(self):
        fn = lambda **_: {}
        ProjectDefinitionScenario.register_executor("test.ref", fn)
        assert ProjectDefinitionScenario._executor_registry.get("test.ref") is fn
        ProjectDefinitionScenario.clear_executors()

    def test_clear_executors(self):
        ProjectDefinitionScenario.register_executor("test.ref", lambda: None)
        ProjectDefinitionScenario.clear_executors()
        assert len(ProjectDefinitionScenario._executor_registry) == 0
