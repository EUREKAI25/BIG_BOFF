"""
project_definition_scenario — EURKAI Core Orchestration

Scenario: brief → project_definition → execution_plan → execute()

This is NOT a renderer.
This is NOT a feature module.

It parses a brief, identifies project needs, maps those needs to EURKAI modules,
builds an ordered execution plan, and runs it.

Objects:
    ParsedBrief         — structured output of brief parsing
    Need                — a single identified project need
    ExecutionStep       — one step in the plan (module_name, inputs, dependencies)
    ExecutionPlan       — ordered list of ExecutionSteps
    ProjectDefinition   — full definition: brief + needs + plan

Scenario:
    ProjectDefinitionScenario
        .parse_brief(brief)   → ParsedBrief
        .identify_needs(parsed) → List[Need]
        .map_needs(needs)     → List[ExecutionStep]
        .build_plan(steps)    → ExecutionPlan
        .execute(plan, ctx)   → Dict
        .run(brief)           → Dict  ← main entry point
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Data models ────────────────────────────────────────────────────────────────

class ParsedBrief(BaseModel):
    """Structured output of brief parsing."""
    project_type: str
    features: List[str]
    constraints: Dict[str, Any]
    target: str
    raw: str


class Need(BaseModel):
    """A single identified project need."""
    name: str
    priority: int = 1
    source: str = ""

    def __eq__(self, other: object) -> bool:
        return self.name == other.name if isinstance(other, Need) else NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)


class ExecutionStep(BaseModel):
    """One step in the execution plan."""
    order: int
    module_name: str
    module_ref: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    status: Literal["pending", "running", "done", "skipped", "failed"] = "pending"
    output: Optional[Any] = None
    error: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class ExecutionPlan(BaseModel):
    """Ordered list of execution steps."""
    steps: List[ExecutionStep]
    needs: List[Need]

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def as_list(self) -> List[Dict[str, Any]]:
        return [
            {k: v for k, v in s.model_dump(exclude_none=True).items() if k != "output"}
            for s in self.steps
        ]


class ProjectDefinition(BaseModel):
    """Full project definition: brief + needs + plan."""
    brief: str
    parsed: ParsedBrief
    needs: List[Need]
    plan: ExecutionPlan

    model_config = {"arbitrary_types_allowed": True}


# ── Scenario ───────────────────────────────────────────────────────────────────

class ProjectDefinitionScenario:
    """
    Core orchestration scenario — brief → definition → plan → execute.

    Does NOT implement features.
    Delegates everything to modules via NEED_MODULE_MAP.

    Extensibility:
        - Add entries to NEED_MODULE_MAP to support new needs.
        - Call register_executor(module_ref, fn) to inject custom executors
          (used in tests and by future INTAKE/ARCHITECT agents).
    """

    VERSION = "1.0.0"
    NAME    = "project.define"

    # ── Brief parsing — keyword signal tables ─────────────────────────────────

    _TYPE_SIGNALS: Dict[str, List[str]] = {
        "saas":       ["saas", "platform", "plateforme", "software", "logiciel",
                       "abonnement", "subscription", "dashboard"],
        "ecommerce":  ["boutique", "shop", "produit", "catalogue", "panier",
                       "vente en ligne", "e-commerce", "ecommerce"],
        "portfolio":  ["portfolio", "agence", "créatif", "showcase",
                       "galerie", "artiste", "photographe"],
        "landing":    ["landing", "page d'accueil", "conversion",
                       "lead generation", "inscription", "squeeze"],
        "startup":    ["startup", "mvp", "lancement", "financement", "seed", "levée"],
        "corporate":  ["entreprise", "corporate", "b2b", "services",
                       "consulting", "cabinet", "institutionnel"],
        "blog":       ["blog", "contenu", "articles", "médias", "publication", "rédaction"],
    }

    _FEATURE_SIGNALS: Dict[str, List[str]] = {
        "backoffice":   ["admin", "backoffice", "back-office", "gestion",
                         "tableau de bord", "management", "panneau"],
        "crm":          ["client", "lead", "contact", "crm",
                         "pipeline vente", "suivi commercial", "prospects"],
        "analytics":    ["analytics", "statistiques", "reporting",
                         "métriques", "kpi", "data", "données"],
        "email":        ["email", "newsletter", "notification",
                         "mailing", "campagne", "emailing"],
        "auth":         ["connexion", "login", "authentification",
                         "compte", "utilisateur", "membre", "inscription"],
        "payments":     ["paiement", "stripe", "facturation",
                         "abonnement", "checkout", "achat"],
        "api":          ["api", "intégration", "webhook",
                         "rest", "json", "endpoint"],
        "multilingual": ["multilingue", "international", "i18n",
                         "traduction", "multi-langue", "langues"],
        "search":       ["recherche", "search", "filtres", "catalogue", "indexation"],
    }

    _CONSTRAINT_SIGNALS: Dict[str, List[str]] = {
        "mobile_first":  ["mobile", "responsive", "smartphone", "pwa", "tablette"],
        "performance":   ["rapide", "performance", "vitesse", "optimisé", "core web vitals"],
        "accessibility": ["accessibilité", "a11y", "wcag", "handicap", "inclusion"],
        "seo":           ["seo", "référencement", "google", "indexation", "organique"],
        "gdpr":          ["rgpd", "gdpr", "conformité", "données personnelles", "cookies"],
    }

    # Project type → additional needs inferred from type alone
    _TYPE_NEED_MAP: Dict[str, List[str]] = {
        "saas":       ["backoffice", "analytics", "auth", "payments"],
        "ecommerce":  ["backoffice", "payments", "search", "email"],
        "startup":    ["email"],
        "corporate":  ["email"],
        "landing":    [],
        "portfolio":  [],
        "blog":       ["email"],
        "generic":    [],
    }

    # ── Need → Module mapping (extensible) ────────────────────────────────────

    NEED_MODULE_MAP: Dict[str, Dict[str, Any]] = {
        "design_system": {
            "module_ref":  "design_endpoints.design.plan.generate",
            "description": "Génère palette + design plan à partir du brief",
            "inputs":      ["brief", "seed"],
            "always":      True,
            "priority":    1,
        },
        "frontend": {
            "module_ref":  "design_scenarios.design.page.generate_full",
            "description": "Génère la landing page HTML complète",
            "inputs":      ["brief", "project_name", "seed"],
            "always":      True,
            "priority":    2,
        },
        "backoffice": {
            "module_ref":  "document_objects.DashboardPage",
            "description": "Génère le dashboard backoffice",
            "inputs":      ["project_name", "design"],
            "always":      False,
            "priority":    3,
        },
        "analytics": {
            "module_ref":  "document_objects.DashboardWidget",
            "description": "Génère les widgets analytics / KPIs",
            "inputs":      ["datasets", "design"],
            "always":      False,
            "priority":    4,
        },
        "crm": {
            "module_ref":  "crm.lead_management",           # à implémenter
            "description": "Module CRM — gestion leads + pipeline commercial",
            "inputs":      ["project_name"],
            "always":      False,
            "priority":    5,
        },
        "email": {
            "module_ref":  "document_objects.EmailSignature",
            "description": "Génère la signature email de marque",
            "inputs":      ["project_name", "design"],
            "always":      False,
            "priority":    6,
        },
        "payments": {
            "module_ref":  "payments.stripe_integration",   # à implémenter
            "description": "Intégration paiement Stripe (checkout, abonnements)",
            "inputs":      ["project_name"],
            "always":      False,
            "priority":    7,
        },
        "auth": {
            "module_ref":  "auth.user_auth",                # à implémenter
            "description": "Système d'authentification utilisateur",
            "inputs":      ["project_name"],
            "always":      False,
            "priority":    8,
        },
        "api": {
            "module_ref":  "api.fastapi_app",               # à implémenter
            "description": "Génération app FastAPI avec endpoints",
            "inputs":      ["project_name", "features"],
            "always":      False,
            "priority":    9,
        },
        "search": {
            "module_ref":  "search.catalogue_search",       # à implémenter
            "description": "Moteur de recherche / filtres catalogue",
            "inputs":      ["project_name"],
            "always":      False,
            "priority":    10,
        },
    }

    # Executor registry — injectable for tests and future agents
    _executor_registry: Dict[str, Any] = {}

    @classmethod
    def register_executor(cls, module_ref: str, executor: Any) -> None:
        """
        Register a callable executor for a module_ref.
        Used in tests or by INTAKE/ARCHITECT agents to inject real implementations.

        executor(brief=..., project_name=..., **inputs) → Any
        """
        cls._executor_registry[module_ref] = executor

    @classmethod
    def clear_executors(cls) -> None:
        """Reset executor registry (used between tests)."""
        cls._executor_registry.clear()

    # ── Step 1 — Parse Brief ──────────────────────────────────────────────────

    def parse_brief(self, brief: str | Dict[str, Any]) -> ParsedBrief:
        """
        Extract project_type, features, constraints, target from a brief.

        Accepts:
            str  → keyword-signal analysis
            dict → used as-is (structured brief from upstream agent)
        """
        if isinstance(brief, dict):
            return ParsedBrief(
                project_type=brief.get("project_type", "generic"),
                features=brief.get("features", []),
                constraints=brief.get("constraints", {}),
                target=brief.get("target", ""),
                raw=str(brief),
            )

        raw  = brief
        text = brief.lower()

        # project_type — highest signal-count wins
        project_type = "generic"
        best_score   = 0
        for ptype, signals in self._TYPE_SIGNALS.items():
            score = sum(1 for s in signals if s in text)
            if score > best_score:
                best_score   = score
                project_type = ptype

        # features — any match triggers the need
        features: List[str] = [
            feat for feat, signals in self._FEATURE_SIGNALS.items()
            if any(s in text for s in signals)
        ]

        # constraints
        constraints: Dict[str, Any] = {
            c: True
            for c, signals in self._CONSTRAINT_SIGNALS.items()
            if any(s in text for s in signals)
        }

        # target — simple regex on "pour …", "destiné à …", "cible : …"
        target = ""
        for pat in [
            r"pour\s+([\w\s\-]+?)(?:\.|,|;|\n|$)",
            r"destinée?\s+(?:à|au|aux)\s+([\w\s\-]+?)(?:\.|,|;|\n|$)",
            r"cible\s*[:\-]\s*([\w\s\-]+?)(?:\.|,|;|\n|$)",
            r"à destination\s+(?:de|des)\s+([\w\s\-]+?)(?:\.|,|;|\n|$)",
        ]:
            m = re.search(pat, text)
            if m:
                target = m.group(1).strip()
                break

        return ParsedBrief(
            project_type=project_type,
            features=features,
            constraints=constraints,
            target=target,
            raw=raw,
        )

    # ── Step 2 — Identify Needs ───────────────────────────────────────────────

    def identify_needs(self, parsed: ParsedBrief) -> List[Need]:
        """
        Convert a ParsedBrief into a prioritized list of Needs.

        Sources:
            always      — injected regardless (design_system, frontend)
            feature     — explicit signal in brief text
            type        — inferred from project_type
        """
        seen: set[str] = set()
        needs: List[Need] = []

        def _add(name: str, source: str) -> None:
            if name in seen or name not in self.NEED_MODULE_MAP:
                return
            seen.add(name)
            needs.append(Need(
                name=name,
                priority=self.NEED_MODULE_MAP[name]["priority"],
                source=source,
            ))

        # Always-on
        for name, meta in self.NEED_MODULE_MAP.items():
            if meta.get("always"):
                _add(name, "always")

        # Feature-based
        for feature in parsed.features:
            _add(feature, f"feature:{feature}")

        # Type-based
        for extra in self._TYPE_NEED_MAP.get(parsed.project_type, []):
            _add(extra, f"type:{parsed.project_type}")

        return sorted(needs, key=lambda n: n.priority)

    # ── Step 3 — Map Needs to Modules ─────────────────────────────────────────

    def map_needs(self, needs: List[Need]) -> List[ExecutionStep]:
        """
        Map a list of Needs to ExecutionSteps using NEED_MODULE_MAP.

        Each step:
            - has an order (1-based)
            - specifies module_name + module_ref
            - declares input keys (values resolved at execution time)
            - depends on the immediately preceding step
        """
        steps: List[ExecutionStep] = []

        for need in needs:
            meta = self.NEED_MODULE_MAP.get(need.name)
            if not meta:
                continue

            # Input keys declared as placeholders — resolved in execute()
            inputs = {k: None for k in meta.get("inputs", [])}

            # Each step depends on the previous one (simple linear chain)
            deps = [steps[-1].module_name] if steps else []

            steps.append(ExecutionStep(
                order=len(steps) + 1,
                module_name=need.name,
                module_ref=meta["module_ref"],
                inputs=inputs,
                dependencies=deps,
            ))

        return steps

    # ── Step 4 — Build Execution Plan ─────────────────────────────────────────

    def build_plan(
        self,
        steps: List[ExecutionStep],
        needs: List[Need],
    ) -> ExecutionPlan:
        return ExecutionPlan(steps=steps, needs=needs)

    # ── Step 5 — Execute ──────────────────────────────────────────────────────

    def execute(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Loop through execution_plan and call each module.

        context — runtime values available to all steps:
            brief        : str
            project_name : str
            seed         : int
            design       : dict  (optional, populated by design_system step)

        dry_run=True — skips all execution, returns plan summary only.

        Module resolution order:
            1. _executor_registry (injected via register_executor)
            2. Dynamic load from MODULES/ directory
            3. Skip (module not yet implemented)
        """
        results: Dict[str, Any] = {}
        trace:   List[Dict[str, Any]] = []

        for step in plan.steps:
            if dry_run:
                step.status = "skipped"
                trace.append({
                    "order":  step.order,
                    "module": step.module_name,
                    "ref":    step.module_ref,
                    "status": "skipped",
                })
                continue

            step.status = "running"

            executor = (
                self._executor_registry.get(step.module_ref)
                or self._try_load(step.module_ref)
            )

            if executor is None:
                step.status = "skipped"
                trace.append({
                    "order":  step.order,
                    "module": step.module_name,
                    "ref":    step.module_ref,
                    "status": "skipped",
                    "reason": "module not implemented",
                })
                continue

            try:
                inputs = self._resolve_inputs(step, context, results)
                output = executor(**inputs)
                step.status = "done"
                step.output = output
                results[step.module_name] = output
                # Propagate design output so downstream steps can use it
                if step.module_name == "design_system" and isinstance(output, dict):
                    context.setdefault("design", output.get("design") or output)
                trace.append({
                    "order":  step.order,
                    "module": step.module_name,
                    "status": "done",
                })
            except Exception as exc:
                step.status = "failed"
                step.error  = str(exc)
                trace.append({
                    "order":  step.order,
                    "module": step.module_name,
                    "status": "failed",
                    "error":  str(exc),
                })

        return {
            "results": results,
            "trace":   trace,
            "done":    sum(1 for s in plan.steps if s.status == "done"),
            "skipped": sum(1 for s in plan.steps if s.status == "skipped"),
            "failed":  sum(1 for s in plan.steps if s.status == "failed"),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _try_load(self, module_ref: str):
        """
        Attempt dynamic load of a module by ref string.

        Convention:
            "design_scenarios.design.page.generate_full"
            → MODULES/design_scenarios/design.page.generate_full.py → run()

            "document_objects.DashboardPage"
            → importlib.import_module("document_objects") → getattr(DashboardPage)
        """
        modules_root = Path(__file__).parents[1]

        # Pattern A: "pkg.file" where file contains a run() function
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

        # Pattern B: "pkg.ClassName" — importable package
        parts = module_ref.rsplit(".", 1)
        if len(parts) == 2:
            pkg_name, attr = parts
            pkg_path = modules_root / pkg_name
            init = pkg_path / "__init__.py"
            if init.exists():
                try:
                    import sys
                    if str(modules_root) not in sys.path:
                        sys.path.insert(0, str(modules_root))
                    import importlib as il
                    mod = il.import_module(pkg_name)
                    return getattr(mod, attr, None)
                except Exception:
                    return None

        return None

    def _resolve_inputs(
        self,
        step: ExecutionStep,
        context: Dict[str, Any],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build concrete inputs for a step from context + previous results.
        Only passes keys declared in NEED_MODULE_MAP["inputs"].
        """
        meta     = self.NEED_MODULE_MAP.get(step.module_name, {})
        resolved = {}
        for key in meta.get("inputs", []):
            if key in context:
                resolved[key] = context[key]
            elif key in results:
                resolved[key] = results[key]
            # else: omit — module must handle missing optional inputs itself
        return resolved

    # ── Main entry point ──────────────────────────────────────────────────────

    def run(
        self,
        brief: str | Dict[str, Any],
        project_name: str = "",
        seed: int = 42,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Full pipeline: brief → definition → plan → execute.

        Args:
            brief        : free-text or structured dict
            project_name : human name for the project
            seed         : determinism seed passed to renderer
            dry_run      : if True, build plan but skip execution

        Returns:
            project_definition : dict  (ParsedBrief + Needs + Plan)
            execution_plan     : list  (ordered steps)
            execution_result   : dict  (results, trace, done/skipped/failed counts)
        """
        parsed     = self.parse_brief(brief)
        needs      = self.identify_needs(parsed)
        steps      = self.map_needs(needs)
        plan       = self.build_plan(steps, needs)
        definition = ProjectDefinition(
            brief=str(brief), parsed=parsed, needs=needs, plan=plan,
        )

        context: Dict[str, Any] = {
            "brief":        str(brief),
            "project_name": project_name or parsed.project_type,
            "seed":         seed,
        }

        execution_result = self.execute(plan, context, dry_run=dry_run)

        return {
            "project_definition": definition.model_dump(),
            "execution_plan":     plan.as_list(),
            "execution_result":   execution_result,
        }

    # ── Self-test ─────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        scenario = cls()

        # Structured brief
        sb = {
            "project_type": "saas",
            "features": ["backoffice", "analytics"],
            "constraints": {"mobile_first": True},
            "target": "PME",
        }
        parsed = scenario.parse_brief(sb)
        assert parsed.project_type == "saas"
        assert "backoffice" in parsed.features

        # Text brief — SaaS
        brief = (
            "Plateforme SaaS de gestion RH pour les PME. "
            "Dashboard admin, analytics, email notifications, authentification."
        )
        result = scenario.run(brief, project_name="MonSaaS", dry_run=True)

        defn = result["project_definition"]
        assert defn["parsed"]["project_type"] == "saas"
        need_names = [n["name"] for n in defn["needs"]]
        assert "design_system" in need_names
        assert "frontend"      in need_names
        assert "backoffice"    in need_names
        assert "analytics"     in need_names

        plan = result["execution_plan"]
        assert len(plan) >= 2
        for step in plan:
            assert "order"       in step
            assert "module_name" in step
            assert "module_ref"  in step

        # dry_run → nothing executed
        assert result["execution_result"]["done"]    == 0
        assert result["execution_result"]["skipped"] == len(plan)

        # Executor injection + execute
        called = []
        cls.register_executor(
            "design_endpoints.design.plan.generate",
            lambda brief, seed, **_: called.append("design_system") or {"design": {}},
        )
        result2 = scenario.run(brief, project_name="MonSaaS", dry_run=False)
        assert "design_system" in called
        cls.clear_executors()

        return True
