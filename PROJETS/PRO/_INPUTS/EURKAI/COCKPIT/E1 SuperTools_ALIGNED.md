# E1/7 — SPÉCIFICATION DES SUPERTOOLS CENTRAUX (ALIGNÉE)

> **Version alignée sur D1-D3 (GEVR/Orchestrate) et F3 (Bootstrap)**

## Vue d'ensemble

Les SuperTools constituent la **façade unifiée** d'EUREKAI, encapsulant les opérations CRUD et métier tout en déléguant l'exécution au pipeline GEVR existant et à l'Orchestrateur D3.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SUPER LAYER (E1)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │  Create  │ │   Read   │ │  Update  │ │  Delete  │               │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘               │
│       │            │            │            │                      │
│       └────────────┴─────┬──────┴────────────┘                      │
│                          │                                          │
│  ┌──────────┐      ┌─────┴─────┐      ┌──────────┐                 │
│  │ Evaluate │──────│   Super   │──────│Orchestrate│                 │
│  └──────────┘      │  Router   │      └──────────┘                 │
│                    └─────┬─────┘                                    │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATE LAYER (D3)                           │
│         ScenarioCatalog → ScenarioSelector → OrchestrationPlan      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GEVR ENGINE (D1)                               │
│              Get → Execute → Validate → Render                      │
│                    HandlerRegistry                                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ERK (B3) + MetaRelations (C3)                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. INTÉGRATION AVEC L'EXISTANT

### 1.1 Imports requis

```python
# GEVR Engine (D1)
from gevr.engine import (
    GEVREngine, ExecutionContext, ActionHandler,
    get_engine, run_scenario, register_handler
)
from gevr.scenario import (
    GEVRScenario, GEVRPhase, StepDefinition,
    ScenarioResult, ScenarioStatus
)

# Orchestrate (D3)
from gevr.orchestrate import (
    Orchestrate, OrchestrationResult, OrchestrationPlan,
    OrchestrationStatus, RequestType, ErrorRecoveryAction,
    ScenarioCatalog, ScenarioCatalogEntry,
    MissingInfo, Hypothesis, ScenarioExecution,
    get_orchestrate, run
)

# Handlers existants (D1)
from gevr.handlers import (
    handler_load_bundle, handler_load_template,
    handler_run_metarules, handler_apply_erk,
    handler_validate_schema, handler_render_report
)
```

### 1.2 Principes d'intégration

| Principe | Description |
|----------|-------------|
| **Non-réimplémentation** | Les SuperTools encapsulent, ne réimplémentent pas |
| **Délégation** | Toute exécution passe par GEVR/Orchestrate |
| **Extension** | Nouveaux scénarios dans ScenarioCatalog |
| **Handlers** | Spécialisations dans HandlerRegistry |

---

## 2. SUPERCREATE

### 2.1 Rôle

SuperCreate crée des objets fractals en invoquant le scénario `Scenario.Create` via GEVR.

### 2.2 Signature

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class ObjectType(Enum):
    """Types d'objets fractals EUREKAI."""
    PROJECT = "project"
    AGENT = "agent"
    SERVICE = "service"
    VIEW = "view"
    BUNDLE = "bundle"
    TASK = "task"
    ASSET = "asset"
    CONFIG = "config"

@dataclass
class SuperCreateParams:
    type: ObjectType
    data: Dict[str, Any]
    parent_id: Optional[str] = None
    bundle_id: Optional[str] = None
    template_id: Optional[str] = None
    dry_run: bool = False
    skip_hooks: bool = False

@dataclass
class SuperCreateResult:
    success: bool
    object_id: Optional[str] = None
    object: Optional[Dict] = None
    lineage: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    gevr_result: Optional[ScenarioResult] = None
```

### 2.3 Implémentation

```python
class SuperCreate:
    """
    SuperTool de création d'objets fractals.
    Délègue à GEVR via le scénario Scenario.Create.
    """
    
    SCENARIO_ID = "Scenario.Create"
    
    def __init__(self, engine: GEVREngine = None):
        self.engine = engine or get_engine()
        self._ensure_scenario_registered()
    
    def _ensure_scenario_registered(self):
        """Enregistre le scénario de création si absent."""
        if self.engine.get_scenario(self.SCENARIO_ID):
            return
        
        scenario = GEVRScenario(
            id=self.SCENARIO_ID,
            name="Create Object",
            description="Crée un objet fractal EUREKAI",
            steps=[
                # GET: Charger le template et résoudre le parent
                StepDefinition(
                    phase=GEVRPhase.GET,
                    action="resolve_parent",
                    params={"parent_id": "${parent_id}"}
                ),
                StepDefinition(
                    phase=GEVRPhase.GET,
                    action="load_template",
                    params={"template_id": "${template_id}"},
                    required=False
                ),
                # EXECUTE: Construire l'objet
                StepDefinition(
                    phase=GEVRPhase.EXECUTE,
                    action="build_object",
                    params={
                        "type": "${type}",
                        "data": "${data}",
                        "template": "${template}"
                    }
                ),
                StepDefinition(
                    phase=GEVRPhase.EXECUTE,
                    action="apply_erk",
                    params={"rules": ["creation_rules"]}
                ),
                # VALIDATE: Vérifier la cohérence
                StepDefinition(
                    phase=GEVRPhase.VALIDATE,
                    action="validate_schema",
                    params={"schema": "${type}_schema"}
                ),
                # RENDER: Persister et retourner
                StepDefinition(
                    phase=GEVRPhase.RENDER,
                    action="persist_object",
                    params={"dry_run": "${dry_run}"}
                )
            ]
        )
        self.engine.register_scenario(scenario)
    
    def execute(self, params: SuperCreateParams) -> SuperCreateResult:
        """Exécute la création via GEVR."""
        input_data = {
            "type": params.type.value,
            "data": params.data,
            "parent_id": params.parent_id,
            "bundle_id": params.bundle_id,
            "template_id": params.template_id,
            "dry_run": params.dry_run
        }
        
        gevr_result = self.engine.run_scenario(
            self.SCENARIO_ID,
            input_data,
            options={"skip_hooks": params.skip_hooks}
        )
        
        return SuperCreateResult(
            success=gevr_result.status == ScenarioStatus.COMPLETED,
            object_id=gevr_result.output.get("id") if gevr_result.output else None,
            object=gevr_result.output,
            lineage=gevr_result.output.get("lineage", []) if gevr_result.output else [],
            warnings=[log for log in gevr_result.logs if "WARNING" in log],
            errors=[str(e) for e in gevr_result.context.get("errors", [])],
            gevr_result=gevr_result
        )
```

### 2.4 Handlers spécifiques à enregistrer

```python
def handler_resolve_parent(params: Dict, context: ExecutionContext) -> Any:
    """GET: Résout le parent dans le lineage."""
    parent_id = params.get("parent_id")
    if not parent_id:
        context.set("parent", None)
        context.set("lineage", [])
        return {"parent": None, "lineage": []}
    
    if context.store:
        parent = context.store.get(parent_id)
        if not parent:
            raise ValueError(f"Parent not found: {parent_id}")
        parent_lineage = parent.get("metadata", {}).get("lineage", [])
        lineage = parent_lineage + [parent_id]
        context.set("parent", parent)
        context.set("lineage", lineage)
        return {"parent": parent, "lineage": lineage}
    
    # Mode simulation
    context.set("lineage", [parent_id])
    return {"parent_id": parent_id, "lineage": [parent_id]}


def handler_build_object(params: Dict, context: ExecutionContext) -> Any:
    """EXECUTE: Construit l'objet fractal."""
    import uuid
    from datetime import datetime
    
    obj_type = params.get("type")
    data = params.get("data", {})
    template = context.get("template")
    
    object_id = f"{obj_type.capitalize()}.{uuid.uuid4().hex[:8]}"
    
    merged_data = {}
    if template:
        merged_data.update(template.get("defaults", {}))
    merged_data.update(data)
    
    obj = {
        "id": object_id,
        "type": obj_type,
        "data": merged_data,
        "metadata": {
            "created_at": datetime.utcnow().isoformat(),
            "lineage": context.get("lineage", []) + [object_id],
            "parent_id": context.get("parent", {}).get("id") if context.get("parent") else None,
            "version": 1
        }
    }
    
    context.set("object", obj)
    context.log(f"Built object: {object_id}", GEVRPhase.EXECUTE)
    return obj


def handler_persist_object(params: Dict, context: ExecutionContext) -> Any:
    """RENDER: Persiste l'objet dans le store."""
    dry_run = params.get("dry_run", False)
    obj = context.get("object")
    
    if not obj:
        raise ValueError("No object to persist")
    
    if dry_run:
        context.log(f"DRY RUN: Would persist {obj['id']}", GEVRPhase.RENDER)
        return {"persisted": False, "dry_run": True, **obj}
    
    if context.store and hasattr(context.store, 'set'):
        context.store.set(obj["id"], obj)
    
    return {"persisted": True, **obj}


def register_create_handlers(engine: GEVREngine):
    """Enregistre les handlers de création."""
    engine.register_handler("resolve_parent", handler_resolve_parent, GEVRPhase.GET)
    engine.register_handler("build_object", handler_build_object, GEVRPhase.EXECUTE)
    engine.register_handler("persist_object", handler_persist_object, GEVRPhase.RENDER)
```

### 2.5 Exemples

```python
create = SuperCreate()

# Simple
result = create.execute(SuperCreateParams(
    type=ObjectType.PROJECT,
    data={"name": "Site ACME", "description": "Refonte corporate"}
))

# Avec parent
result = create.execute(SuperCreateParams(
    type=ObjectType.TASK,
    data={"name": "Maquettes"},
    parent_id="Project.acme123"
))

# Dry run
result = create.execute(SuperCreateParams(
    type=ObjectType.AGENT,
    data={"name": "Analyzer"},
    template_id="agent.minimal",
    dry_run=True
))
```

---

## 3. SUPERREAD

### 3.1 Signature

```python
@dataclass
class QuerySpec:
    type: Optional[ObjectType] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
    sort: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class LineageQuery:
    root_id: str
    direction: str = "down"
    depth: int = -1
    include_root: bool = True

@dataclass 
class SuperReadParams:
    id: Optional[str] = None
    path: Optional[str] = None
    query: Optional[QuerySpec] = None
    lineage: Optional[LineageQuery] = None
    include_children: bool = False
    resolve_refs: bool = True
    fields: Optional[List[str]] = None

@dataclass
class SuperReadResult:
    success: bool
    data: Any = None
    total_count: Optional[int] = None
    lineage: Optional[List[str]] = None
    errors: List[str] = field(default_factory=list)
    gevr_result: Optional[ScenarioResult] = None
```

### 3.2 Implémentation (utilise handler_load_bundle existant)

```python
class SuperRead:
    """Utilise les handlers GET existants de gevr/handlers.py."""
    
    SCENARIO_ID = "Scenario.Read"
    
    def __init__(self, engine: GEVREngine = None):
        self.engine = engine or get_engine()
        self._ensure_scenario_registered()
    
    def execute(self, params: SuperReadParams) -> SuperReadResult:
        input_data = {
            "id": params.id,
            "query": params.query.__dict__ if params.query else None,
            "lineage": params.lineage.__dict__ if params.lineage else None,
            "include_children": params.include_children,
            "resolve_refs": params.resolve_refs,
            "fields": params.fields,
            "depth": 1 if params.include_children else 0
        }
        
        gevr_result = self.engine.run_scenario(self.SCENARIO_ID, input_data)
        
        return SuperReadResult(
            success=gevr_result.status == ScenarioStatus.COMPLETED,
            data=gevr_result.output.get("data") if gevr_result.output else None,
            total_count=gevr_result.output.get("total_count") if gevr_result.output else None,
            lineage=gevr_result.output.get("lineage") if gevr_result.output else None,
            errors=[str(e) for e in gevr_result.context.get("errors", [])],
            gevr_result=gevr_result
        )
```

---

## 4. SUPERUPDATE

### 4.1 Signature

```python
@dataclass
class UpdateChanges:
    set: Optional[Dict[str, Any]] = None
    unset: Optional[List[str]] = None
    push: Optional[Dict[str, Any]] = None
    pull: Optional[Dict[str, Any]] = None
    move_to: Optional[str] = None

@dataclass
class SuperUpdateParams:
    id: str
    changes: UpdateChanges
    dry_run: bool = False
    create_version: bool = True
    propagate: bool = True

@dataclass
class SuperUpdateResult:
    success: bool
    object: Optional[Dict] = None
    version_id: Optional[str] = None
    changes_applied: Dict = field(default_factory=dict)
    propagated_to: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    gevr_result: Optional[ScenarioResult] = None
```

---

## 5. SUPERDELETE

### 5.1 Signature

```python
class DeleteStrategy(Enum):
    CASCADE = "cascade"
    ORPHAN = "orphan"
    PROTECT = "protect"
    NULLIFY = "nullify"

@dataclass
class SuperDeleteParams:
    id: str
    mode: str = "soft"
    strategy: DeleteStrategy = DeleteStrategy.CASCADE
    dry_run: bool = False
    archive: bool = True

@dataclass
class SuperDeleteResult:
    success: bool
    deleted_ids: List[str] = field(default_factory=list)
    orphaned_ids: List[str] = field(default_factory=list)
    archive_id: Optional[str] = None
    blocked_by: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    gevr_result: Optional[ScenarioResult] = None
```

---

## 6. SUPEREVALUATE

### 6.1 Rôle

Utilise les scénarios D3 existants: `Scenario.AnalyzeObject`, `Scenario.ValidateProject`.

### 6.2 Signature

```python
EVALUATORS = {
    "schema_compliance": "Scenario.ValidateSchema",
    "completeness": "Scenario.CheckCompleteness",
    "consistency": "Scenario.AnalyzeConsistency",
    "business_rules": "Scenario.ValidateProject",
    "metarelations": "Scenario.AnalyzeObject",
}

@dataclass
class SuperEvaluateParams:
    target_id: str
    evaluators: List[str] = field(default_factory=lambda: ["completeness"])
    scope: str = "object"
    depth: int = 1
    threshold: Optional[float] = None

@dataclass
class EvaluationDetail:
    evaluator: str
    score: float
    passed: bool
    details: Dict[str, Any]
    issues: List[Dict]

@dataclass
class SuperEvaluateResult:
    success: bool
    overall_score: float = 0.0
    evaluations: Dict[str, EvaluationDetail] = field(default_factory=dict)
    issues: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    orchestration_result: Optional[OrchestrationResult] = None
```

### 6.3 Implémentation

```python
class SuperEvaluate:
    """Délègue à l'Orchestrateur D3 pour les analyses."""
    
    def __init__(self, orchestrate: Orchestrate = None):
        self.orchestrate = orchestrate or get_orchestrate()
    
    def execute(self, params: SuperEvaluateParams) -> SuperEvaluateResult:
        evaluations = {}
        all_issues = []
        
        for evaluator in params.evaluators:
            request = {
                "type": "analyze" if "analyze" in evaluator.lower() else "validate",
                "object_id": params.target_id,
                "evaluator": evaluator,
                "scope": params.scope,
                "depth": params.depth
            }
            
            orch_result = self.orchestrate.run(request)
            
            output = orch_result.final_output or {}
            score = output.get("score", 0.5)
            issues = output.get("issues", [])
            
            evaluations[evaluator] = EvaluationDetail(
                evaluator=evaluator,
                score=score,
                passed=score >= (params.threshold or 0.5),
                details=output,
                issues=issues
            )
            all_issues.extend(issues)
        
        overall_score = sum(e.score for e in evaluations.values()) / len(evaluations) if evaluations else 0.0
        
        return SuperEvaluateResult(
            success=all(e.passed for e in evaluations.values()),
            overall_score=overall_score,
            evaluations=evaluations,
            issues=all_issues,
            recommendations=self._generate_recommendations(all_issues),
            orchestration_result=orch_result
        )
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        return [
            f"Corriger: {i.get('message', '')}" 
            for i in issues 
            if i.get("severity") == "critical"
        ][:5]
```

---

## 7. SUPERORCHESTRATE

### 7.1 Rôle

**Façade vers l'Orchestrateur D3 existant** avec raccourcis et workflows custom.

### 7.2 Signature

```python
@dataclass
class WorkflowStep:
    id: str
    action: str  # "create", "read", "update", "delete", "evaluate"
    params: Dict[str, Any]
    condition: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    on_error: str = "stop"

@dataclass
class SuperOrchestrateParams:
    scenario: Optional[str] = None          # Mode 1: scénario D3
    steps: Optional[List[WorkflowStep]] = None  # Mode 2: workflow custom
    context: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

@dataclass
class SuperOrchestrateResult:
    success: bool
    status: OrchestrationStatus
    execution_id: str = ""
    steps_completed: List[str] = field(default_factory=list)
    steps_failed: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    missing_info: List[MissingInfo] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    orchestration_result: Optional[OrchestrationResult] = None
```

### 7.3 Implémentation

```python
class SuperOrchestrate:
    """Façade vers l'Orchestrateur D3."""
    
    def __init__(self, orchestrate: Orchestrate = None, engine: GEVREngine = None):
        self.orchestrate = orchestrate or get_orchestrate(engine)
        self.engine = engine or get_engine()
    
    def execute(self, params: SuperOrchestrateParams) -> SuperOrchestrateResult:
        import uuid
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        if params.scenario:
            return self._execute_scenario(params, execution_id)
        
        if params.steps:
            return self._execute_workflow(params, execution_id)
        
        return SuperOrchestrateResult(
            success=False,
            status=OrchestrationStatus.FAILED,
            execution_id=execution_id,
            errors=["No scenario or workflow specified"]
        )
    
    def _execute_scenario(self, params: SuperOrchestrateParams, exec_id: str) -> SuperOrchestrateResult:
        """Délègue au D3 existant."""
        request = {**params.context}
        
        # Mapper scénario → RequestType si connu
        scenario_to_type = {
            "Scenario.ProjetEURKAI": RequestType.IDEA,
            "Scenario.AnalyzeObject": RequestType.ANALYZE,
            "Scenario.ValidateProject": RequestType.VALIDATE,
            "Scenario.TransformProject": RequestType.TRANSFORM,
        }
        
        if params.scenario in scenario_to_type:
            request["type"] = scenario_to_type[params.scenario].value
        
        orch_result = self.orchestrate.run(request)
        
        return SuperOrchestrateResult(
            success=orch_result.ok,
            status=orch_result.status,
            execution_id=exec_id,
            steps_completed=[e.scenario_id for e in orch_result.executions if e.ok],
            steps_failed=[e.scenario_id for e in orch_result.executions if not e.ok],
            outputs={"final": orch_result.final_output},
            missing_info=orch_result.missing_info,
            hypotheses=orch_result.hypotheses,
            errors=orch_result.errors,
            orchestration_result=orch_result
        )
    
    def _execute_workflow(self, params: SuperOrchestrateParams, exec_id: str) -> SuperOrchestrateResult:
        """Exécute un workflow custom via les SuperTools."""
        outputs = {}
        completed = []
        failed = []
        context = dict(params.context)
        
        for step in params.steps:
            # Vérifier dépendances
            if not all(dep in completed for dep in step.depends_on):
                if step.on_error == "stop":
                    failed.append(step.id)
                    break
                continue
            
            # Évaluer condition
            if step.condition and not self._eval_condition(step.condition, outputs):
                continue
            
            # Exécuter
            try:
                resolved = self._resolve_params(step.params, context, outputs)
                result = self._execute_action(step.action, resolved)
                outputs[step.id] = result
                completed.append(step.id)
                if isinstance(result, dict):
                    context.update(result)
            except Exception as e:
                failed.append(step.id)
                if step.on_error == "stop":
                    break
        
        success = len(failed) == 0
        status = (
            OrchestrationStatus.COMPLETED if success
            else OrchestrationStatus.PARTIAL if completed
            else OrchestrationStatus.FAILED
        )
        
        return SuperOrchestrateResult(
            success=success,
            status=status,
            execution_id=exec_id,
            steps_completed=completed,
            steps_failed=failed,
            outputs=outputs,
            errors=[f"Step {s} failed" for s in failed]
        )
    
    def _execute_action(self, action: str, params: Dict) -> Dict:
        """Route vers le SuperTool approprié."""
        if action == "create":
            return SuperCreate(self.engine).execute(SuperCreateParams(**params)).__dict__
        elif action == "read":
            return SuperRead(self.engine).execute(SuperReadParams(**params)).__dict__
        elif action == "update":
            return SuperUpdate(self.engine).execute(SuperUpdateParams(**params)).__dict__
        elif action == "delete":
            return SuperDelete(self.engine).execute(SuperDeleteParams(**params)).__dict__
        elif action == "evaluate":
            return SuperEvaluate(self.orchestrate).execute(SuperEvaluateParams(**params)).__dict__
        raise ValueError(f"Unknown action: {action}")
    
    def _eval_condition(self, condition: str, outputs: Dict) -> bool:
        try:
            expr = condition
            for key, val in outputs.items():
                if isinstance(val, dict):
                    for k, v in val.items():
                        expr = expr.replace(f"{{{{outputs.{key}.{k}}}}}", str(v))
            return eval(expr.replace("true", "True").replace("false", "False"))
        except:
            return True
    
    def _resolve_params(self, params: Dict, context: Dict, outputs: Dict) -> Dict:
        import re
        resolved = {}
        for key, val in params.items():
            if isinstance(val, str) and "{{" in val:
                for m in re.findall(r'\{\{outputs\.(\w+)\.(\w+)\}\}', val):
                    if m[0] in outputs and isinstance(outputs[m[0]], dict):
                        val = val.replace(f"{{{{outputs.{m[0]}.{m[1]}}}}}", str(outputs[m[0]].get(m[1], "")))
                for m in re.findall(r'\{\{context\.(\w+)\}\}', val):
                    val = val.replace(f"{{{{context.{m}}}}}", str(context.get(m, "")))
            resolved[key] = val
        return resolved
```

### 7.4 Exemples

```python
orch = SuperOrchestrate()

# Scénario D3 existant
result = orch.execute(SuperOrchestrateParams(
    scenario="Scenario.ProjetEURKAI",
    context={"data": "Je veux un blog"}
))

# Workflow custom
result = orch.execute(SuperOrchestrateParams(
    steps=[
        WorkflowStep(id="create", action="create", params={
            "type": "project", "data": {"name": "{{context.name}}"}
        }),
        WorkflowStep(id="eval", action="evaluate", params={
            "target_id": "{{outputs.create.object_id}}"
        }, depends_on=["create"]),
    ],
    context={"name": "Test Project"}
))

# Gestion infos manquantes (propagé de D3)
result = orch.execute(SuperOrchestrateParams(
    scenario="Scenario.Deploy",
    context={"target": "production"}
))
if result.status == OrchestrationStatus.WAITING_INPUT:
    for m in result.missing_info:
        print(f"Requis: {m.field}")
```

---

## 8. API UNIFIÉE

```python
class Super:
    """Point d'entrée unifié."""
    
    _engine: GEVREngine = None
    _orchestrate: Orchestrate = None
    
    @classmethod
    def _get_engine(cls) -> GEVREngine:
        if cls._engine is None:
            cls._engine = get_engine()
        return cls._engine
    
    @classmethod
    def _get_orchestrate(cls) -> Orchestrate:
        if cls._orchestrate is None:
            cls._orchestrate = get_orchestrate(cls._get_engine())
        return cls._orchestrate
    
    @classmethod
    def create(cls, params: SuperCreateParams) -> SuperCreateResult:
        return SuperCreate(cls._get_engine()).execute(params)
    
    @classmethod
    def read(cls, params: SuperReadParams) -> SuperReadResult:
        return SuperRead(cls._get_engine()).execute(params)
    
    @classmethod
    def update(cls, params: SuperUpdateParams) -> SuperUpdateResult:
        return SuperUpdate(cls._get_engine()).execute(params)
    
    @classmethod
    def delete(cls, params: SuperDeleteParams) -> SuperDeleteResult:
        return SuperDelete(cls._get_engine()).execute(params)
    
    @classmethod
    def evaluate(cls, params: SuperEvaluateParams) -> SuperEvaluateResult:
        return SuperEvaluate(cls._get_orchestrate()).execute(params)
    
    @classmethod
    def orchestrate(cls, params: SuperOrchestrateParams) -> SuperOrchestrateResult:
        return SuperOrchestrate(cls._get_orchestrate(), cls._get_engine()).execute(params)
```

### Raccourcis

```python
def create(type: ObjectType, data: Dict, **kw) -> SuperCreateResult:
    return Super.create(SuperCreateParams(type=type, data=data, **kw))

def read(id: str = None, **kw) -> SuperReadResult:
    return Super.read(SuperReadParams(id=id, **kw))

def update(id: str, changes: UpdateChanges, **kw) -> SuperUpdateResult:
    return Super.update(SuperUpdateParams(id=id, changes=changes, **kw))

def delete(id: str, **kw) -> SuperDeleteResult:
    return Super.delete(SuperDeleteParams(id=id, **kw))

def evaluate(target_id: str, evaluators: List[str] = None, **kw) -> SuperEvaluateResult:
    return Super.evaluate(SuperEvaluateParams(target_id=target_id, evaluators=evaluators or ["completeness"], **kw))

def orchestrate(scenario: str = None, steps: List[WorkflowStep] = None, **kw) -> SuperOrchestrateResult:
    return Super.orchestrate(SuperOrchestrateParams(scenario=scenario, steps=steps, **kw))
```

---

## 9. MAPPING SUPERTOOLS ↔ D3

| SuperTool | RequestType D3 | Scénarios |
|-----------|----------------|-----------|
| SuperCreate | IDEA, BRIEF | Scenario.Create, Scenario.ProjetEURKAI |
| SuperRead | - | Scenario.Read (handlers GET) |
| SuperUpdate | TRANSFORM, ENRICH | Scenario.Update, Scenario.TransformProject |
| SuperDelete | - | Scenario.Delete |
| SuperEvaluate | ANALYZE, VALIDATE | Scenario.AnalyzeObject, Scenario.ValidateProject |
| SuperOrchestrate | COMPOSITE | Tous via OrchestrationPlan |

---

## 10. CAS DE TEST

```python
class TestSuperCreate:
    def test_create_simple(self):
        result = Super.create(SuperCreateParams(
            type=ObjectType.PROJECT,
            data={"name": "Test"}
        ))
        assert result.success
        assert result.object_id is not None
    
    def test_create_with_gevr(self):
        result = Super.create(SuperCreateParams(
            type=ObjectType.TASK,
            data={"name": "Task"}
        ))
        assert result.gevr_result is not None
        assert result.gevr_result.scenario.id == "Scenario.Create"


class TestSuperOrchestrate:
    def test_uses_d3(self):
        result = Super.orchestrate(SuperOrchestrateParams(
            scenario="Scenario.ProjetEURKAI",
            context={"data": "Test"}
        ))
        assert result.orchestration_result is not None
    
    def test_missing_info_propagated(self):
        result = Super.orchestrate(SuperOrchestrateParams(
            scenario="Scenario.Deploy",
            context={"target": "prod"}
        ))
        if result.status == OrchestrationStatus.WAITING_INPUT:
            assert len(result.missing_info) > 0


class TestIntegration:
    def test_workflow_uses_supertools(self):
        result = Super.orchestrate(SuperOrchestrateParams(
            steps=[
                WorkflowStep(id="s1", action="create", params={
                    "type": "project", "data": {"name": "WF Test"}
                })
            ]
        ))
        assert result.success
        assert "s1" in result.steps_completed
```

---

## 11. CHECKLIST

- [x] SuperTools alignés sur GEVREngine (D1)
- [x] SuperOrchestrate utilise Orchestrate (D3)
- [x] Handlers dans HandlerRegistry
- [x] Scénarios dans ScenarioCatalog
- [x] Types D3 réutilisés (RequestType, OrchestrationStatus, MissingInfo, Hypothesis)
- [x] Résultats incluent gevr_result / orchestration_result
- [x] API unifiée `Super.*`
- [x] Raccourcis fonctionnels
- [x] Tests unitaires et intégration
- [x] Exemples
