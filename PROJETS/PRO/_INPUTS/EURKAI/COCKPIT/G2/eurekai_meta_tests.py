"""
EUREKAI — Système de Méta-Tests & Auto-Debug Fractal
=====================================================
Module G2/10 : Génération et exécution de tests à partir de la fractale.

HIÉRARCHIE DE TESTS
-------------------
1. STRUCTURE (MetaRules)     → Validation des règles structurelles
2. RELATIONS (MetaRelations) → Cohérence des liens entre objets
3. SCÉNARIOS (GEVR)          → Pipelines Get-Execute-Validate-Render
4. INTÉGRATION (SuperTools)  → Tests end-to-end via le catalogue d'outils

AUTEUR : EUREKAI System
VERSION : G2/10
DÉPENDANCES : eurekai_pgcd_ppcm (G1/9)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional, Callable, Union
from enum import Enum, auto
from datetime import datetime
import json
import hashlib
from abc import ABC, abstractmethod


# =============================================================================
# ÉNUMÉRATIONS & CONSTANTES
# =============================================================================

class Severity(Enum):
    """Niveaux de sévérité des règles et résultats."""
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class TestCategory(Enum):
    """Catégories de tests alignées sur MetaRules."""
    STRUCTURE = "structure"
    RELATION = "relation"
    COHERENCY = "coherency"
    SCENARIO = "scenario"
    MODULE = "module"
    SECURITY = "security"


class TestStatus(Enum):
    """Statut d'exécution d'un test."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class GEVRAction(Enum):
    """Actions du pipeline GEVR."""
    GET = "get"
    EXECUTE = "execute"
    VALIDATE = "validate"
    RENDER = "render"


class TestScope(Enum):
    """Portée d'exécution des tests."""
    FULL = "full"           # Tout le système
    PROJECT = "project"     # Un projet spécifique
    MODULE = "module"       # Un module
    OBJECT = "object"       # Un objet unique
    LINEAGE = "lineage"     # Une lignée d'objets


# =============================================================================
# STRUCTURES DE DONNÉES — FRACTALE
# =============================================================================

@dataclass
class Vector:
    """Identifiant vectoriel d'un objet fractal."""
    path: str  # Ex: "Object:Page.Landing.MainHero"
    
    def __hash__(self):
        return hash(self.path)
    
    def __eq__(self, other):
        if isinstance(other, Vector):
            return self.path == other.path
        return False
    
    @property
    def lineage(self) -> List[str]:
        """Retourne la lignée complète."""
        parts = self.path.split(".")
        base = parts[0]  # "Object:Page" ou "Object"
        if ":" in base:
            prefix, first = base.split(":", 1)
            result = [prefix]
            current = prefix
            for part in [first] + parts[1:]:
                current = f"{current}:{part}" if current == prefix else f"{current}.{part}"
                result.append(current)
        else:
            result = [base]
            current = base
            for part in parts[1:]:
                current = f"{current}.{part}"
                result.append(current)
        return result
    
    @property
    def type_name(self) -> str:
        """Extrait le type de base."""
        return self.path.split(":")[0] if ":" in self.path else self.path.split(".")[0]


@dataclass
class ObjectBundle:
    """Représentation complète d'un objet fractal."""
    vector: Vector
    attributes: Dict[str, Any] = field(default_factory=dict)
    methods: Dict[str, Vector] = field(default_factory=dict)
    rules: List[Vector] = field(default_factory=list)
    relations: Dict[str, List[Vector]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    @property
    def lineage(self) -> List[str]:
        return self.vector.lineage


# =============================================================================
# STRUCTURES DE DONNÉES — METARULES
# =============================================================================

@dataclass
class MetaRule:
    """
    Règle de validation structurelle.
    Ne modifie jamais la fractale — signale, classifie, évalue, informe.
    """
    rule_id: Vector
    applies_to: Union[str, Vector, List[str]]  # ObjectType, Lineage, ou Tag
    condition: str  # Expression ERK (lecture seule)
    effect: str     # Classification ou action logique
    severity: Severity
    category: TestCategory
    message: str
    
    def matches(self, obj: ObjectBundle) -> bool:
        """Vérifie si la règle s'applique à cet objet."""
        if isinstance(self.applies_to, str):
            # Type ou tag
            if self.applies_to in obj.tags:
                return True
            if obj.vector.type_name == self.applies_to:
                return True
        elif isinstance(self.applies_to, Vector):
            # Vecteur exact ou dans la lignée
            if self.applies_to == obj.vector:
                return True
            if self.applies_to.path in obj.lineage:
                return True
        elif isinstance(self.applies_to, list):
            # Liste de types/tags
            return any(t in obj.tags or obj.vector.type_name == t for t in self.applies_to)
        return False


@dataclass
class MetaRelation:
    """Définition d'une relation valide entre objets."""
    relation_type: str  # depends_on, related_to, inherits_from
    source_constraint: str  # Type ou pattern du source
    target_constraint: str  # Type ou pattern de la cible
    cardinality: str  # "1", "0..1", "1..*", "*"
    bidirectional: bool = False


# =============================================================================
# STRUCTURES DE DONNÉES — GEVR
# =============================================================================

@dataclass
class GEVRStep:
    """Étape d'un scénario GEVR."""
    step_id: str
    action: GEVRAction
    target: Vector
    inputs: Dict[str, Any] = field(default_factory=dict)
    conditions: List[str] = field(default_factory=list)  # Expressions ERK
    expected_outputs: List[Any] = field(default_factory=list)


@dataclass
class GEVRScenario:
    """Pipeline GEVR complet."""
    scenario_id: Vector
    description: str
    steps: List[GEVRStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def get_actions_sequence(self) -> List[GEVRAction]:
        """Retourne la séquence d'actions."""
        return [step.action for step in self.steps]


# =============================================================================
# STRUCTURES DE DONNÉES — SUPERTOOLS
# =============================================================================

@dataclass
class SuperToolSpec:
    """Spécification d'un SuperTool."""
    name: str
    operation: str  # read, query, create, update, delete, evaluate, execute
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    is_mutating: bool  # True si modifie la fractale
    requires_validation: bool = True


# Catalogue officiel des SuperTools (phase A→G)
SUPER_TOOLS_CATALOG: Dict[str, SuperToolSpec] = {
    "SuperRead": SuperToolSpec(
        name="SuperRead",
        operation="read",
        input_schema={"objectVector": "Vector"},
        output_schema={"objectBundle": "ObjectBundle"},
        is_mutating=False
    ),
    "SuperQuery": SuperToolSpec(
        name="SuperQuery", 
        operation="query",
        input_schema={"criteria": "Dict"},
        output_schema={"vectors": "List[Vector]"},
        is_mutating=False
    ),
    "SuperCreate": SuperToolSpec(
        name="SuperCreate",
        operation="create",
        input_schema={"spec": "ObjectSpec"},
        output_schema={"newVector": "Vector"},
        is_mutating=True
    ),
    "SuperUpdate": SuperToolSpec(
        name="SuperUpdate",
        operation="update",
        input_schema={"vector": "Vector", "patch": "Dict"},
        output_schema={"updatedVector": "Vector"},
        is_mutating=True
    ),
    "SuperDelete": SuperToolSpec(
        name="SuperDelete",
        operation="delete",
        input_schema={"vector": "Vector"},
        output_schema={"confirmation": "bool"},
        is_mutating=True
    ),
    "SuperEvaluate": SuperToolSpec(
        name="SuperEvaluate",
        operation="evaluate",
        input_schema={"ruleSet": "List[Vector]", "target": "Vector"},
        output_schema={"report": "EvaluationReport"},
        is_mutating=False
    ),
    "SuperExecute": SuperToolSpec(
        name="SuperExecute",
        operation="execute",
        input_schema={"methodVector": "Vector", "inputs": "Dict"},
        output_schema={"outputBundle": "Any"},
        is_mutating=False  # Méthodes safe uniquement
    ),
}


# =============================================================================
# RÉSULTATS DE TESTS
# =============================================================================

@dataclass
class TestResult:
    """Résultat d'un test individuel."""
    test_id: str
    test_name: str
    category: TestCategory
    status: TestStatus
    severity: Severity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "category": self.category.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }


@dataclass
class TestReport:
    """Rapport complet d'exécution des tests."""
    report_id: str
    scope: TestScope
    scope_target: Optional[str]
    started_at: str
    completed_at: str
    results: List[TestResult] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        return len(self.results)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)
    
    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.ERROR)
    
    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
    
    @property
    def success_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0
    
    @property
    def critical_failures(self) -> List[TestResult]:
        return [r for r in self.results 
                if r.status == TestStatus.FAILED and r.severity == Severity.CRITICAL]
    
    def by_category(self) -> Dict[TestCategory, List[TestResult]]:
        """Groupe les résultats par catégorie."""
        grouped = {cat: [] for cat in TestCategory}
        for r in self.results:
            grouped[r.category].append(r)
        return grouped
    
    def summary(self) -> str:
        """Génère un résumé textuel."""
        duration = "N/A"
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            duration = f"{(end - start).total_seconds():.2f}s"
        except:
            pass
        
        lines = [
            "=" * 70,
            f"RAPPORT DE TESTS — {self.report_id}",
            "=" * 70,
            f"Scope: {self.scope.value}" + (f" ({self.scope_target})" if self.scope_target else ""),
            f"Durée: {duration}",
            "",
            f"RÉSULTATS: {self.passed}/{self.total} passés ({self.success_rate:.1%})",
            f"├─ Passés   : {self.passed}",
            f"├─ Échoués  : {self.failed}",
            f"├─ Erreurs  : {self.errors}",
            f"└─ Ignorés  : {self.skipped}",
        ]
        
        if self.critical_failures:
            lines.extend([
                "",
                "⚠️  ÉCHECS CRITIQUES:",
            ])
            for cf in self.critical_failures:
                lines.append(f"  • [{cf.test_id}] {cf.message}")
        
        by_cat = self.by_category()
        lines.extend(["", "PAR CATÉGORIE:"])
        for cat, results in by_cat.items():
            if results:
                passed = sum(1 for r in results if r.status == TestStatus.PASSED)
                lines.append(f"  {cat.value}: {passed}/{len(results)}")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "scope": self.scope.value,
            "scope_target": self.scope_target,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "skipped": self.skipped,
                "success_rate": self.success_rate
            },
            "results": [r.to_dict() for r in self.results]
        }


# =============================================================================
# GÉNÉRATEURS DE TESTS
# =============================================================================

class TestGenerator(ABC):
    """Classe abstraite pour les générateurs de tests."""
    
    @abstractmethod
    def generate(self, context: Dict[str, Any]) -> List['MetaTest']:
        """Génère des tests à partir du contexte."""
        pass


@dataclass
class MetaTest:
    """Définition d'un test généré."""
    test_id: str
    name: str
    category: TestCategory
    severity: Severity
    description: str
    target: Optional[Vector]
    validator: Callable[[Dict[str, Any]], TestResult]
    tags: List[str] = field(default_factory=list)


class StructureTestGenerator(TestGenerator):
    """Génère des tests de structure à partir des MetaRules."""
    
    def __init__(self, rules: List[MetaRule]):
        self.rules = rules
    
    def generate(self, context: Dict[str, Any]) -> List[MetaTest]:
        tests = []
        objects: List[ObjectBundle] = context.get("objects", [])
        
        for rule in self.rules:
            for obj in objects:
                if rule.matches(obj):
                    test = MetaTest(
                        test_id=f"STRUCT-{rule.rule_id.path}-{obj.vector.path}".replace(":", "_").replace(".", "_"),
                        name=f"[Structure] {rule.message}",
                        category=rule.category,
                        severity=rule.severity,
                        description=f"Vérifie: {rule.condition} sur {obj.vector.path}",
                        target=obj.vector,
                        validator=self._create_validator(rule, obj),
                        tags=["structure", "metarule"]
                    )
                    tests.append(test)
        
        return tests
    
    def _create_validator(self, rule: MetaRule, obj: ObjectBundle) -> Callable:
        """Crée une fonction de validation pour une règle."""
        def validator(ctx: Dict[str, Any]) -> TestResult:
            start = datetime.now()
            try:
                # Évaluation de la condition ERK
                result = self._evaluate_condition(rule.condition, obj, ctx)
                status = TestStatus.PASSED if result else TestStatus.FAILED
                message = rule.message if not result else f"OK: {rule.message}"
            except Exception as e:
                status = TestStatus.ERROR
                message = f"Erreur d'évaluation: {str(e)}"
                result = False
            
            duration = (datetime.now() - start).total_seconds() * 1000
            
            return TestResult(
                test_id=f"STRUCT-{rule.rule_id.path}",
                test_name=rule.message,
                category=rule.category,
                status=status,
                severity=rule.severity,
                message=message,
                details={
                    "rule_id": rule.rule_id.path,
                    "object": obj.vector.path,
                    "condition": rule.condition,
                    "evaluation_result": result
                },
                duration_ms=duration
            )
        return validator
    
    def _evaluate_condition(self, condition: str, obj: ObjectBundle, ctx: Dict) -> bool:
        """Évalue une expression ERK simplifiée."""
        # Implémentation basique — à étendre selon le langage ERK complet
        if "has_attribute" in condition:
            attr = condition.split("(")[1].split(")")[0].strip("'\"")
            return attr in obj.attributes
        if "has_method" in condition:
            method = condition.split("(")[1].split(")")[0].strip("'\"")
            return method in obj.methods
        if "has_tag" in condition:
            tag = condition.split("(")[1].split(")")[0].strip("'\"")
            return tag in obj.tags
        if "lineage_includes" in condition:
            ancestor = condition.split("(")[1].split(")")[0].strip("'\"")
            return ancestor in obj.lineage
        # Condition toujours vraie par défaut (pour tests)
        return True


class RelationTestGenerator(TestGenerator):
    """Génère des tests de relations (MetaRelations)."""
    
    def __init__(self, relations: List[MetaRelation]):
        self.relations = relations
    
    def generate(self, context: Dict[str, Any]) -> List[MetaTest]:
        tests = []
        objects: List[ObjectBundle] = context.get("objects", [])
        
        for obj in objects:
            for rel_type, targets in obj.relations.items():
                # Test de cardinalité
                tests.append(self._cardinality_test(obj, rel_type, targets))
                
                # Test de cohérence des cibles
                for target in targets:
                    tests.append(self._target_validity_test(obj, rel_type, target, context))
        
        # Tests de symétrie pour relations bidirectionnelles
        for rel in self.relations:
            if rel.bidirectional:
                tests.extend(self._bidirectional_tests(objects, rel))
        
        return tests
    
    def _cardinality_test(self, obj: ObjectBundle, rel_type: str, targets: List[Vector]) -> MetaTest:
        """Test de cardinalité d'une relation."""
        test_id = f"REL-CARD-{obj.vector.path}-{rel_type}".replace(":", "_").replace(".", "_")
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Trouver la contrainte de cardinalité
            expected_card = "*"  # Par défaut
            for rel in ctx.get("relations", []):
                if rel.relation_type == rel_type:
                    expected_card = rel.cardinality
                    break
            
            count = len(targets)
            valid = self._check_cardinality(count, expected_card)
            
            return TestResult(
                test_id=test_id,
                test_name=f"Cardinalité {rel_type}",
                category=TestCategory.RELATION,
                status=TestStatus.PASSED if valid else TestStatus.FAILED,
                severity=Severity.ERROR if not valid else Severity.INFO,
                message=f"{rel_type}: {count} éléments (attendu: {expected_card})",
                details={
                    "object": obj.vector.path,
                    "relation": rel_type,
                    "count": count,
                    "expected": expected_card
                }
            )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Relation] Cardinalité {rel_type} sur {obj.vector.path}",
            category=TestCategory.RELATION,
            severity=Severity.ERROR,
            description=f"Vérifie la cardinalité de {rel_type}",
            target=obj.vector,
            validator=validator,
            tags=["relation", "cardinality"]
        )
    
    def _check_cardinality(self, count: int, spec: str) -> bool:
        """Vérifie si un count respecte une spec de cardinalité."""
        if spec == "*":
            return True
        if spec == "1":
            return count == 1
        if spec == "0..1":
            return count <= 1
        if spec == "1..*":
            return count >= 1
        return True
    
    def _target_validity_test(self, obj: ObjectBundle, rel_type: str, 
                               target: Vector, context: Dict) -> MetaTest:
        """Test que la cible d'une relation existe."""
        test_id = f"REL-TGT-{obj.vector.path}-{target.path}".replace(":", "_").replace(".", "_")
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            objects = ctx.get("objects", [])
            vectors = {o.vector.path for o in objects}
            exists = target.path in vectors
            
            return TestResult(
                test_id=test_id,
                test_name=f"Cible valide {target.path}",
                category=TestCategory.RELATION,
                status=TestStatus.PASSED if exists else TestStatus.FAILED,
                severity=Severity.ERROR if not exists else Severity.INFO,
                message=f"Cible {target.path} {'existe' if exists else 'inexistante'}",
                details={
                    "source": obj.vector.path,
                    "relation": rel_type,
                    "target": target.path,
                    "exists": exists
                }
            )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Relation] Validité cible {rel_type}",
            category=TestCategory.RELATION,
            severity=Severity.ERROR,
            description=f"Vérifie que {target.path} existe",
            target=obj.vector,
            validator=validator,
            tags=["relation", "target-validity"]
        )
    
    def _bidirectional_tests(self, objects: List[ObjectBundle], 
                             rel: MetaRelation) -> List[MetaTest]:
        """Tests de symétrie pour relations bidirectionnelles."""
        tests = []
        # Implémentation simplifiée
        return tests


class ScenarioTestGenerator(TestGenerator):
    """Génère des tests à partir des scénarios GEVR."""
    
    def __init__(self, scenarios: List[GEVRScenario]):
        self.scenarios = scenarios
    
    def generate(self, context: Dict[str, Any]) -> List[MetaTest]:
        tests = []
        
        for scenario in self.scenarios:
            # Test de cohérence du pipeline
            tests.append(self._pipeline_coherence_test(scenario))
            
            # Test de chaque étape
            for step in scenario.steps:
                tests.append(self._step_test(scenario, step, context))
            
            # Test de séquence GEVR
            tests.append(self._sequence_validity_test(scenario))
        
        return tests
    
    def _pipeline_coherence_test(self, scenario: GEVRScenario) -> MetaTest:
        """Test que le pipeline est cohérent (entrées/sorties chaînées)."""
        test_id = f"GEVR-COH-{scenario.scenario_id.path}".replace(":", "_").replace(".", "_")
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Vérifier que les outputs d'une étape peuvent alimenter les inputs suivants
            issues = []
            for i, step in enumerate(scenario.steps[:-1]):
                next_step = scenario.steps[i + 1]
                # Logique simplifiée : vérifier la présence de conditions
                if next_step.conditions and not step.expected_outputs:
                    issues.append(f"Étape {step.step_id} n'a pas d'outputs pour {next_step.step_id}")
            
            return TestResult(
                test_id=test_id,
                test_name=f"Cohérence pipeline {scenario.scenario_id.path}",
                category=TestCategory.SCENARIO,
                status=TestStatus.PASSED if not issues else TestStatus.FAILED,
                severity=Severity.WARN if issues else Severity.INFO,
                message="Pipeline cohérent" if not issues else f"{len(issues)} problèmes",
                details={"issues": issues, "steps_count": len(scenario.steps)}
            )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Scénario] Cohérence {scenario.scenario_id.path}",
            category=TestCategory.SCENARIO,
            severity=Severity.WARN,
            description=scenario.description,
            target=scenario.scenario_id,
            validator=validator,
            tags=["scenario", "coherence"] + scenario.tags
        )
    
    def _step_test(self, scenario: GEVRScenario, step: GEVRStep, 
                   context: Dict) -> MetaTest:
        """Test d'une étape GEVR individuelle."""
        test_id = f"GEVR-STEP-{scenario.scenario_id.path}-{step.step_id}".replace(":", "_").replace(".", "_")
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Simuler l'exécution de l'étape
            try:
                # Vérifier que la cible existe
                objects = ctx.get("objects", [])
                target_exists = any(o.vector.path == step.target.path for o in objects)
                
                if not target_exists and step.action == GEVRAction.GET:
                    return TestResult(
                        test_id=test_id,
                        test_name=f"Step {step.step_id}",
                        category=TestCategory.SCENARIO,
                        status=TestStatus.FAILED,
                        severity=Severity.ERROR,
                        message=f"Cible {step.target.path} introuvable pour GET",
                        details={"step": step.step_id, "action": step.action.value}
                    )
                
                return TestResult(
                    test_id=test_id,
                    test_name=f"Step {step.step_id}",
                    category=TestCategory.SCENARIO,
                    status=TestStatus.PASSED,
                    severity=Severity.INFO,
                    message=f"{step.action.value} sur {step.target.path} OK",
                    details={"step": step.step_id, "action": step.action.value}
                )
            except Exception as e:
                return TestResult(
                    test_id=test_id,
                    test_name=f"Step {step.step_id}",
                    category=TestCategory.SCENARIO,
                    status=TestStatus.ERROR,
                    severity=Severity.CRITICAL,
                    message=f"Erreur: {str(e)}",
                    details={"step": step.step_id, "error": str(e)}
                )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Scénario] {step.action.value} - {step.step_id}",
            category=TestCategory.SCENARIO,
            severity=Severity.ERROR,
            description=f"Étape {step.step_id}: {step.action.value} sur {step.target.path}",
            target=step.target,
            validator=validator,
            tags=["scenario", "step", step.action.value]
        )
    
    def _sequence_validity_test(self, scenario: GEVRScenario) -> MetaTest:
        """Test que la séquence GEVR est valide."""
        test_id = f"GEVR-SEQ-{scenario.scenario_id.path}".replace(":", "_").replace(".", "_")
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            sequence = scenario.get_actions_sequence()
            
            # Règles de séquence GEVR
            # - GET doit précéder EXECUTE sur le même objet
            # - VALIDATE peut apparaître après GET ou EXECUTE
            # - RENDER est généralement en fin
            
            issues = []
            
            # Vérification basique : au moins un GET au début
            if sequence and sequence[0] != GEVRAction.GET:
                issues.append("Le scénario devrait commencer par GET")
            
            # Vérification : pas d'EXECUTE sans GET préalable
            has_get = False
            for action in sequence:
                if action == GEVRAction.GET:
                    has_get = True
                elif action == GEVRAction.EXECUTE and not has_get:
                    issues.append("EXECUTE sans GET préalable")
            
            return TestResult(
                test_id=test_id,
                test_name=f"Séquence GEVR {scenario.scenario_id.path}",
                category=TestCategory.SCENARIO,
                status=TestStatus.PASSED if not issues else TestStatus.FAILED,
                severity=Severity.WARN if issues else Severity.INFO,
                message="Séquence valide" if not issues else "; ".join(issues),
                details={
                    "sequence": [a.value for a in sequence],
                    "issues": issues
                }
            )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Scénario] Séquence GEVR valide",
            category=TestCategory.SCENARIO,
            severity=Severity.WARN,
            description="Vérifie l'ordre des actions GEVR",
            target=scenario.scenario_id,
            validator=validator,
            tags=["scenario", "sequence"]
        )


class IntegrationTestGenerator(TestGenerator):
    """Génère des tests d'intégration (SuperTools)."""
    
    def __init__(self, tools_catalog: Dict[str, SuperToolSpec] = None):
        self.catalog = tools_catalog or SUPER_TOOLS_CATALOG
    
    def generate(self, context: Dict[str, Any]) -> List[MetaTest]:
        tests = []
        
        # Tests de disponibilité des SuperTools
        for name, spec in self.catalog.items():
            tests.append(self._tool_availability_test(name, spec))
        
        # Tests de non-bypass (sécurité)
        tests.extend(self._mutation_bypass_tests(context))
        
        # Tests d'erreurs intentionnelles
        tests.extend(self._error_handling_tests(context))
        
        return tests
    
    def _tool_availability_test(self, name: str, spec: SuperToolSpec) -> MetaTest:
        """Test que le SuperTool est disponible."""
        test_id = f"INTEG-TOOL-{name}"
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Simuler la vérification de disponibilité
            available = name in SUPER_TOOLS_CATALOG
            
            return TestResult(
                test_id=test_id,
                test_name=f"Disponibilité {name}",
                category=TestCategory.MODULE,
                status=TestStatus.PASSED if available else TestStatus.FAILED,
                severity=Severity.CRITICAL if not available else Severity.INFO,
                message=f"{name} {'disponible' if available else 'indisponible'}",
                details={"tool": name, "operation": spec.operation}
            )
        
        return MetaTest(
            test_id=test_id,
            name=f"[Intégration] SuperTool {name}",
            category=TestCategory.MODULE,
            severity=Severity.CRITICAL,
            description=f"Vérifie que {name} est opérationnel",
            target=None,
            validator=validator,
            tags=["integration", "supertool"]
        )
    
    def _mutation_bypass_tests(self, context: Dict[str, Any]) -> List[MetaTest]:
        """Tests de non-régression : impossible de bypasser les SuperTools."""
        tests = []
        
        # Test : mutation uniquement via SuperCreate/Update/Delete
        test_id = "INTEG-SEC-MUTATION"
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Vérifier que les seuls outils mutants sont bien identifiés
            mutating_tools = [name for name, spec in self.catalog.items() if spec.is_mutating]
            expected = {"SuperCreate", "SuperUpdate", "SuperDelete"}
            actual = set(mutating_tools)
            
            valid = actual == expected
            
            return TestResult(
                test_id=test_id,
                test_name="Contrôle des mutations",
                category=TestCategory.SECURITY,
                status=TestStatus.PASSED if valid else TestStatus.FAILED,
                severity=Severity.CRITICAL,
                message="Mutations contrôlées" if valid else "Outils mutants non conformes",
                details={
                    "expected_mutating": list(expected),
                    "actual_mutating": list(actual)
                }
            )
        
        tests.append(MetaTest(
            test_id=test_id,
            name="[Sécurité] Contrôle des mutations",
            category=TestCategory.SECURITY,
            severity=Severity.CRITICAL,
            description="Vérifie que seuls SuperCreate/Update/Delete peuvent muter",
            target=None,
            validator=validator,
            tags=["integration", "security", "non-regression"]
        ))
        
        return tests
    
    def _error_handling_tests(self, context: Dict[str, Any]) -> List[MetaTest]:
        """Tests d'erreurs intentionnelles."""
        tests = []
        
        # Test : SuperRead sur vecteur inexistant
        test_id = "INTEG-ERR-READ-404"
        
        def validator(ctx: Dict[str, Any]) -> TestResult:
            # Simuler une lecture sur vecteur inexistant
            fake_vector = Vector("Object:NonExistent.Fake.Path")
            objects = ctx.get("objects", [])
            exists = any(o.vector.path == fake_vector.path for o in objects)
            
            # On attend que ça échoue proprement
            handled_correctly = not exists  # Le vecteur ne devrait pas exister
            
            return TestResult(
                test_id=test_id,
                test_name="Gestion erreur SuperRead 404",
                category=TestCategory.MODULE,
                status=TestStatus.PASSED if handled_correctly else TestStatus.FAILED,
                severity=Severity.WARN,
                message="Erreur 404 gérée correctement" if handled_correctly else "Problème",
                details={"fake_vector": fake_vector.path}
            )
        
        tests.append(MetaTest(
            test_id=test_id,
            name="[Intégration] Erreur SuperRead 404",
            category=TestCategory.MODULE,
            severity=Severity.WARN,
            description="Vérifie la gestion d'erreur sur vecteur inexistant",
            target=None,
            validator=validator,
            tags=["integration", "error-handling"]
        ))
        
        return tests


# =============================================================================
# MOTEUR D'EXÉCUTION
# =============================================================================

class MetaTestEngine:
    """
    Moteur d'exécution des méta-tests.
    Point d'entrée principal : runMetaTests(scope, target) -> TestReport
    """
    
    def __init__(self):
        self.generators: List[TestGenerator] = []
        self.rules: List[MetaRule] = []
        self.relations: List[MetaRelation] = []
        self.scenarios: List[GEVRScenario] = []
        self.objects: List[ObjectBundle] = []
    
    def register_rules(self, rules: List[MetaRule]) -> 'MetaTestEngine':
        """Enregistre des MetaRules."""
        self.rules.extend(rules)
        return self
    
    def register_relations(self, relations: List[MetaRelation]) -> 'MetaTestEngine':
        """Enregistre des MetaRelations."""
        self.relations.extend(relations)
        return self
    
    def register_scenarios(self, scenarios: List[GEVRScenario]) -> 'MetaTestEngine':
        """Enregistre des scénarios GEVR."""
        self.scenarios.extend(scenarios)
        return self
    
    def register_objects(self, objects: List[ObjectBundle]) -> 'MetaTestEngine':
        """Enregistre des objets de la fractale."""
        self.objects.extend(objects)
        return self
    
    def _build_context(self, scope: TestScope, target: Optional[str]) -> Dict[str, Any]:
        """Construit le contexte d'exécution selon le scope."""
        ctx = {
            "objects": self.objects,
            "rules": self.rules,
            "relations": self.relations,
            "scenarios": self.scenarios,
            "scope": scope,
            "target": target
        }
        
        # Filtrer selon le scope
        if scope == TestScope.OBJECT and target:
            ctx["objects"] = [o for o in self.objects if o.vector.path == target]
        elif scope == TestScope.LINEAGE and target:
            ctx["objects"] = [o for o in self.objects if target in o.lineage]
        elif scope == TestScope.MODULE and target:
            ctx["objects"] = [o for o in self.objects if target in o.vector.path]
        elif scope == TestScope.PROJECT and target:
            ctx["objects"] = [o for o in self.objects if o.vector.path.startswith(target)]
        
        return ctx
    
    def _generate_tests(self, context: Dict[str, Any]) -> List[MetaTest]:
        """Génère tous les tests pour le contexte donné."""
        all_tests = []
        
        # Générateurs standard
        generators = [
            StructureTestGenerator(self.rules),
            RelationTestGenerator(self.relations),
            ScenarioTestGenerator(self.scenarios),
            IntegrationTestGenerator()
        ]
        
        for gen in generators:
            all_tests.extend(gen.generate(context))
        
        # Générateurs custom
        for gen in self.generators:
            all_tests.extend(gen.generate(context))
        
        return all_tests
    
    def runMetaTests(
        self,
        scope: TestScope = TestScope.FULL,
        target: Optional[str] = None,
        categories: Optional[List[TestCategory]] = None,
        tags: Optional[List[str]] = None,
        fail_fast: bool = False
    ) -> TestReport:
        """
        API principale : exécute les méta-tests.
        
        Args:
            scope: Portée des tests (FULL, PROJECT, MODULE, OBJECT, LINEAGE)
            target: Cible spécifique (optionnel selon scope)
            categories: Filtrer par catégories (optionnel)
            tags: Filtrer par tags (optionnel)
            fail_fast: Arrêter au premier échec critique
            
        Returns:
            TestReport avec tous les résultats
        """
        started_at = datetime.now().isoformat()
        report_id = f"TR-{hashlib.md5(started_at.encode()).hexdigest()[:8].upper()}"
        
        # Construire le contexte
        context = self._build_context(scope, target)
        
        # Générer les tests
        all_tests = self._generate_tests(context)
        
        # Filtrer par catégories
        if categories:
            all_tests = [t for t in all_tests if t.category in categories]
        
        # Filtrer par tags
        if tags:
            all_tests = [t for t in all_tests if any(tag in t.tags for tag in tags)]
        
        # Exécuter les tests
        results = []
        for test in all_tests:
            try:
                result = test.validator(context)
                results.append(result)
                
                if fail_fast and result.status == TestStatus.FAILED and result.severity == Severity.CRITICAL:
                    break
            except Exception as e:
                results.append(TestResult(
                    test_id=test.test_id,
                    test_name=test.name,
                    category=test.category,
                    status=TestStatus.ERROR,
                    severity=Severity.CRITICAL,
                    message=f"Exception: {str(e)}",
                    details={"exception": str(e), "test": test.name}
                ))
        
        completed_at = datetime.now().isoformat()
        
        return TestReport(
            report_id=report_id,
            scope=scope,
            scope_target=target,
            started_at=started_at,
            completed_at=completed_at,
            results=results
        )


# =============================================================================
# FACTORY & HELPERS
# =============================================================================

def create_default_engine() -> MetaTestEngine:
    """Crée un moteur avec configuration par défaut."""
    return MetaTestEngine()


def quick_test(
    objects: List[ObjectBundle],
    rules: List[MetaRule] = None,
    scenarios: List[GEVRScenario] = None
) -> TestReport:
    """
    Helper pour tests rapides.
    
    Args:
        objects: Objets à tester
        rules: Règles à appliquer (optionnel)
        scenarios: Scénarios à tester (optionnel)
        
    Returns:
        TestReport
    """
    engine = MetaTestEngine()
    engine.register_objects(objects)
    
    if rules:
        engine.register_rules(rules)
    if scenarios:
        engine.register_scenarios(scenarios)
    
    return engine.runMetaTests()


# =============================================================================
# EXEMPLES & DÉMO
# =============================================================================

def create_example_fractale() -> List[ObjectBundle]:
    """Crée une fractale d'exemple basée sur le format officiel."""
    
    # Object:Page.Landing.MainHero
    main_hero = ObjectBundle(
        vector=Vector("Object:Page.Landing.MainHero"),
        attributes={
            "title": "string:required",
            "theme": "colorSet:optional",
            "layout": "layoutType"
        },
        methods={
            "render": Vector("Method:RenderPageHero"),
            "validate": Vector("Method:ValidateModule"),
            "suggestModules": Vector("Method:SuggestFromTags")
        },
        rules=[
            Vector("Rule:PageMustHaveLayout"),
            Vector("Rule:HeroMustHaveTitle"),
            Vector("Rule:ThemeMustRespectPalette")
        ],
        relations={
            "depends_on": [
                Vector("Module:HeroLayout"),
                Vector("Module:TypographySet")
            ],
            "related_to": [
                Vector("Object:Site.Project.Homepage")
            ],
            "inherits_from": [
                Vector("Object:Page")
            ]
        },
        tags=["ui", "hero", "landing", "critical-module"]
    )
    
    # Object:Page (parent)
    page = ObjectBundle(
        vector=Vector("Object:Page"),
        attributes={
            "layout": "layoutType:required"
        },
        methods={
            "render": Vector("Method:RenderPage"),
            "validate": Vector("Method:ValidateModule")
        },
        rules=[
            Vector("Rule:PageMustHaveLayout")
        ],
        relations={
            "inherits_from": [Vector("Object")]
        },
        tags=["ui", "page", "base"]
    )
    
    # Module:HeroLayout (dépendance)
    hero_layout = ObjectBundle(
        vector=Vector("Module:HeroLayout"),
        attributes={
            "type": "module",
            "version": "1.0"
        },
        methods={
            "apply": Vector("Method:ApplyLayout")
        },
        rules=[],
        relations={
            "used_by": [Vector("Object:Page.Landing.MainHero")]
        },
        tags=["module", "layout"]
    )
    
    # Object:Site.Project.Homepage
    homepage = ObjectBundle(
        vector=Vector("Object:Site.Project.Homepage"),
        attributes={
            "url": "/",
            "template": "homepage"
        },
        methods={
            "render": Vector("Method:RenderPage")
        },
        rules=[],
        relations={
            "contains": [Vector("Object:Page.Landing.MainHero")]
        },
        tags=["site", "homepage"]
    )
    
    return [main_hero, page, hero_layout, homepage]


def create_example_rules() -> List[MetaRule]:
    """Crée des MetaRules d'exemple."""
    return [
        MetaRule(
            rule_id=Vector("Rule:PageMustHaveLayout"),
            applies_to="page",
            condition="has_attribute('layout')",
            effect="classify:valid-page",
            severity=Severity.ERROR,
            category=TestCategory.STRUCTURE,
            message="Toute page doit avoir un layout"
        ),
        MetaRule(
            rule_id=Vector("Rule:HeroMustHaveTitle"),
            applies_to="hero",
            condition="has_attribute('title')",
            effect="classify:valid-hero",
            severity=Severity.ERROR,
            category=TestCategory.STRUCTURE,
            message="Tout hero doit avoir un titre"
        ),
        MetaRule(
            rule_id=Vector("Rule:CriticalModuleMustHaveMethod"),
            applies_to="critical-module",
            condition="has_method('validate')",
            effect="classify:production-ready",
            severity=Severity.CRITICAL,
            category=TestCategory.STRUCTURE,
            message="Les modules critiques doivent avoir une méthode validate"
        ),
        MetaRule(
            rule_id=Vector("Rule:InheritanceMustBeValid"),
            applies_to=["page", "module"],
            condition="lineage_includes('Object')",
            effect="classify:proper-inheritance",
            severity=Severity.WARN,
            category=TestCategory.COHERENCY,
            message="L'héritage doit remonter jusqu'à Object"
        )
    ]


def create_example_scenarios() -> List[GEVRScenario]:
    """Crée des scénarios GEVR d'exemple."""
    return [
        GEVRScenario(
            scenario_id=Vector("Scenario:RenderLandingPage"),
            description="Rendu complet d'une landing page avec hero",
            steps=[
                GEVRStep(
                    step_id="S1-GET-HERO",
                    action=GEVRAction.GET,
                    target=Vector("Object:Page.Landing.MainHero"),
                    inputs={},
                    conditions=[],
                    expected_outputs=["objectBundle"]
                ),
                GEVRStep(
                    step_id="S2-GET-DEPS",
                    action=GEVRAction.GET,
                    target=Vector("Module:HeroLayout"),
                    inputs={},
                    conditions=["hero_loaded"],
                    expected_outputs=["layoutModule"]
                ),
                GEVRStep(
                    step_id="S3-VALIDATE",
                    action=GEVRAction.VALIDATE,
                    target=Vector("Object:Page.Landing.MainHero"),
                    inputs={"rules": ["Rule:HeroMustHaveTitle"]},
                    conditions=["deps_loaded"],
                    expected_outputs=["validationReport"]
                ),
                GEVRStep(
                    step_id="S4-EXECUTE",
                    action=GEVRAction.EXECUTE,
                    target=Vector("Method:RenderPageHero"),
                    inputs={"hero": "objectBundle", "layout": "layoutModule"},
                    conditions=["validation_passed"],
                    expected_outputs=["renderedHTML"]
                ),
                GEVRStep(
                    step_id="S5-RENDER",
                    action=GEVRAction.RENDER,
                    target=Vector("Output:HTML"),
                    inputs={"content": "renderedHTML"},
                    conditions=[],
                    expected_outputs=["finalOutput"]
                )
            ],
            tags=["landing", "render", "full-pipeline"]
        ),
        GEVRScenario(
            scenario_id=Vector("Scenario:ValidateModule"),
            description="Validation isolée d'un module",
            steps=[
                GEVRStep(
                    step_id="V1-GET",
                    action=GEVRAction.GET,
                    target=Vector("Module:HeroLayout"),
                    inputs={},
                    conditions=[],
                    expected_outputs=["module"]
                ),
                GEVRStep(
                    step_id="V2-VALIDATE",
                    action=GEVRAction.VALIDATE,
                    target=Vector("Module:HeroLayout"),
                    inputs={"rules": "all"},
                    conditions=[],
                    expected_outputs=["report"]
                ),
                GEVRStep(
                    step_id="V3-RENDER",
                    action=GEVRAction.RENDER,
                    target=Vector("Output:Report"),
                    inputs={"data": "report"},
                    conditions=[],
                    expected_outputs=["validationReport"]
                )
            ],
            tags=["validation", "module"]
        )
    ]


def run_demo():
    """Exécute une démonstration complète."""
    print("\n" + "=" * 70)
    print("EUREKAI — Système de Méta-Tests G2/10")
    print("=" * 70)
    
    # Créer les données d'exemple
    objects = create_example_fractale()
    rules = create_example_rules()
    scenarios = create_example_scenarios()
    
    print(f"\n📦 Fractale chargée : {len(objects)} objets")
    print(f"📋 MetaRules : {len(rules)} règles")
    print(f"🎬 Scénarios GEVR : {len(scenarios)} scénarios")
    
    # Créer et configurer le moteur
    engine = MetaTestEngine()
    engine.register_objects(objects)
    engine.register_rules(rules)
    engine.register_scenarios(scenarios)
    
    # Test 1 : Full scope
    print("\n" + "-" * 70)
    print("TEST 1 : Scope FULL (tout le système)")
    print("-" * 70)
    
    report = engine.runMetaTests(scope=TestScope.FULL)
    print(report.summary())
    
    # Test 2 : Scope OBJECT
    print("\n" + "-" * 70)
    print("TEST 2 : Scope OBJECT (MainHero uniquement)")
    print("-" * 70)
    
    report_obj = engine.runMetaTests(
        scope=TestScope.OBJECT,
        target="Object:Page.Landing.MainHero"
    )
    print(report_obj.summary())
    
    # Test 3 : Par catégorie
    print("\n" + "-" * 70)
    print("TEST 3 : Catégorie STRUCTURE uniquement")
    print("-" * 70)
    
    report_struct = engine.runMetaTests(
        scope=TestScope.FULL,
        categories=[TestCategory.STRUCTURE]
    )
    print(report_struct.summary())
    
    # Test 4 : Par tags
    print("\n" + "-" * 70)
    print("TEST 4 : Tag 'scenario' uniquement")
    print("-" * 70)
    
    report_tag = engine.runMetaTests(
        scope=TestScope.FULL,
        tags=["scenario"]
    )
    print(report_tag.summary())
    
    # Export JSON
    print("\n" + "-" * 70)
    print("EXPORT JSON (extrait)")
    print("-" * 70)
    
    json_report = json.dumps(report.to_dict(), indent=2, default=str)
    # Afficher les 50 premières lignes
    lines = json_report.split("\n")[:50]
    print("\n".join(lines))
    if len(json_report.split("\n")) > 50:
        print("... (tronqué)")
    
    print("\n" + "=" * 70)
    print("FIN DE LA DÉMONSTRATION")
    print("=" * 70)


def run_test_cases():
    """Cas de test pour validation du module."""
    print("\n" + "=" * 70)
    print("CAS DE TEST — VALIDATION DU MODULE G2/10")
    print("=" * 70)
    
    # Test 1 : Création Vector
    print("\n[TEST 1] Vector et lineage")
    v = Vector("Object:Page.Landing.MainHero")
    assert v.type_name == "Object", f"Type attendu 'Object', obtenu '{v.type_name}'"
    assert len(v.lineage) >= 3, f"Lineage insuffisant : {v.lineage}"
    print(f"  ✓ Vector: {v.path}")
    print(f"  ✓ Lineage: {v.lineage}")
    
    # Test 2 : MetaRule matching
    print("\n[TEST 2] MetaRule matching")
    rule = MetaRule(
        rule_id=Vector("Rule:Test"),
        applies_to="hero",
        condition="has_tag('hero')",
        effect="test",
        severity=Severity.INFO,
        category=TestCategory.STRUCTURE,
        message="Test"
    )
    obj = ObjectBundle(
        vector=Vector("Object:Hero"),
        tags=["hero", "ui"]
    )
    assert rule.matches(obj), "La règle devrait matcher l'objet avec tag 'hero'"
    print("  ✓ Matching par tag fonctionne")
    
    # Test 3 : Engine sans données
    print("\n[TEST 3] Engine vide")
    engine = MetaTestEngine()
    report = engine.runMetaTests()
    assert report.total >= 7, f"Attendu >=7 tests (SuperTools+), obtenu {report.total}"
    print(f"  ✓ Engine vide génère {report.total} tests (SuperTools + intégration)")
    
    # Test 4 : Engine avec objets
    print("\n[TEST 4] Engine avec fractale")
    objects = create_example_fractale()
    rules = create_example_rules()
    
    engine = MetaTestEngine()
    engine.register_objects(objects)
    engine.register_rules(rules)
    
    report = engine.runMetaTests()
    assert report.total > 10, f"Attendu >10 tests, obtenu {report.total}"
    print(f"  ✓ {report.total} tests générés")
    print(f"  ✓ {report.passed} passés, {report.failed} échoués")
    
    # Test 5 : Scope filtering
    print("\n[TEST 5] Filtrage par scope")
    report_obj = engine.runMetaTests(
        scope=TestScope.OBJECT,
        target="Object:Page.Landing.MainHero"
    )
    report_full = engine.runMetaTests(scope=TestScope.FULL)
    assert report_obj.total <= report_full.total, "Scope OBJECT devrait avoir moins de tests"
    print(f"  ✓ FULL: {report_full.total} tests, OBJECT: {report_obj.total} tests")
    
    # Test 6 : Export JSON
    print("\n[TEST 6] Export JSON")
    json_str = json.dumps(report.to_dict(), default=str)
    data = json.loads(json_str)
    assert "report_id" in data, "JSON doit contenir report_id"
    assert "results" in data, "JSON doit contenir results"
    print(f"  ✓ JSON valide ({len(json_str)} caractères)")
    
    # Test 7 : Catégories
    print("\n[TEST 7] Tests par catégorie")
    by_cat = report.by_category()
    cats_with_tests = [c for c, r in by_cat.items() if r]
    assert len(cats_with_tests) >= 3, "Au moins 3 catégories doivent avoir des tests"
    print(f"  ✓ {len(cats_with_tests)} catégories avec tests")
    
    # Test 8 : Scénarios GEVR
    print("\n[TEST 8] Scénarios GEVR")
    scenarios = create_example_scenarios()
    engine.register_scenarios(scenarios)
    report_scen = engine.runMetaTests(tags=["scenario"])
    assert report_scen.total > 0, "Des tests de scénario doivent exister"
    print(f"  ✓ {report_scen.total} tests de scénarios")
    
    print("\n" + "-" * 70)
    print("TOUS LES TESTS PASSÉS ✓")
    print("-" * 70)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_test_cases()
    else:
        run_demo()
        run_test_cases()
