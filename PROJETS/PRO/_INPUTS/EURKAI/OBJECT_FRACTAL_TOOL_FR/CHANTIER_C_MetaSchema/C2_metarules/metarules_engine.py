"""
EUREKAI C2/2 — MetaRules de Structure
=====================================
Système de définition et vérification d'invariants structurels
pour la fractale EUREKAI.

Architecture:
- MetaRule: Classe de base pour toutes les règles structurelles
- MetaRuleEngine: Orchestrateur de vérification
- Violation: Structure de rapport d'erreur
- Formalisme ERK-like pour exprimer les contraintes
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    List, Dict, Optional, Tuple, Callable, 
    Any, Set, Type, Union, Pattern
)
from enum import Enum
import re
from datetime import datetime

# Import du système C1 pour compatibilité
import sys
sys.path.insert(0, '/home/claude/C1_extracted')
from lineage_suggester import FractalObject, ObjectType


# =============================================================================
# ÉNUMÉRATIONS ET CONSTANTES
# =============================================================================

class Severity(Enum):
    """Niveau de sévérité d'une violation."""
    CRITICAL = "critical"   # Bloquant pour le déploiement
    ERROR = "error"         # Doit être corrigé
    WARNING = "warning"     # À surveiller
    INFO = "info"           # Information seulement


class RuleCategory(Enum):
    """Catégorie de règle pour organisation."""
    IDENTITY = "identity"           # Règles sur id, name, type
    STRUCTURE = "structure"         # Règles sur lineage, parent
    BUNDLE = "bundle"               # Règles sur attributes, methods
    RELATION = "relation"           # Règles sur les relations
    CONSISTENCY = "consistency"     # Règles de cohérence globale


# =============================================================================
# STRUCTURE DES VIOLATIONS
# =============================================================================

@dataclass
class Violation:
    """
    Représente une violation d'une MetaRule.
    
    Attributes:
        rule_id: Identifiant unique de la règle violée
        rule_name: Nom humain de la règle
        object_id: ID de l'objet concerné
        object_lineage: Lineage pour contexte
        severity: Niveau de sévérité
        message: Description claire de la violation
        suggestion: Correction suggérée (optionnel)
        context: Données additionnelles pour debug
    """
    rule_id: str
    rule_name: str
    object_id: str
    object_lineage: str
    severity: Severity
    message: str
    suggestion: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Sérialisation pour API/JSON."""
        return {
            "ruleId": self.rule_id,
            "ruleName": self.rule_name,
            "objectId": self.object_id,
            "objectLineage": self.object_lineage,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "context": self.context
        }
    
    def __str__(self) -> str:
        icon = {
            Severity.CRITICAL: "🔴",
            Severity.ERROR: "🟠",
            Severity.WARNING: "🟡",
            Severity.INFO: "🔵"
        }.get(self.severity, "⚪")
        return f"{icon} [{self.rule_id}] {self.object_lineage}: {self.message}"


@dataclass
class AuditResult:
    """
    Résultat complet d'un audit MetaRules.
    
    Attributes:
        ok: True si aucune violation critique/error
        violations: Liste de toutes les violations
        stats: Statistiques de l'audit
        timestamp: Date/heure de l'audit
    """
    ok: bool
    violations: List[Violation]
    stats: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "errors": [v.to_dict() for v in self.violations],
            "stats": self.stats,
            "timestamp": self.timestamp.isoformat()
        }
    
    def filter_by_severity(self, severity: Severity) -> List[Violation]:
        """Filtre les violations par sévérité."""
        return [v for v in self.violations if v.severity == severity]
    
    def filter_by_object(self, object_id: str) -> List[Violation]:
        """Filtre les violations par objet."""
        return [v for v in self.violations if v.object_id == object_id]
    
    def filter_by_rule(self, rule_id: str) -> List[Violation]:
        """Filtre les violations par règle."""
        return [v for v in self.violations if v.rule_id == rule_id]
    
    def summary(self) -> str:
        """Résumé textuel de l'audit."""
        lines = [
            f"{'✅' if self.ok else '❌'} Audit {'OK' if self.ok else 'FAILED'}",
            f"   Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"   Objets analysés: {self.stats.get('objects_checked', 0)}",
            f"   Règles appliquées: {self.stats.get('rules_applied', 0)}",
            "",
            "   Violations par sévérité:"
        ]
        for sev in Severity:
            count = len(self.filter_by_severity(sev))
            if count > 0:
                lines.append(f"     {sev.value}: {count}")
        
        return "\n".join(lines)


# =============================================================================
# CLASSE DE BASE METARULE
# =============================================================================

class MetaRule(ABC):
    """
    Classe de base pour toutes les MetaRules.
    
    Une MetaRule définit un invariant structurel sur la fractale.
    Elle peut cibler:
    - Tous les objets (scope=ALL)
    - Un type spécifique (scope=ObjectType)
    - Un pattern de lineage (scope=pattern)
    
    Syntaxe ERK-like:
        FOR ALL ObjectType: require attribute "id"
        FOR Core:Agent:*: require method "prompt"
        FOR ALL: forbid cycle in lineage
    """
    
    # Identifiant unique (auto-généré si None)
    id: str = None
    
    # Nom humain de la règle
    name: str = "Unnamed Rule"
    
    # Description détaillée
    description: str = ""
    
    # Catégorie pour organisation
    category: RuleCategory = RuleCategory.CONSISTENCY
    
    # Sévérité par défaut des violations
    default_severity: Severity = Severity.ERROR
    
    # Scope: ALL, ObjectType, ou pattern regex
    scope: Union[str, ObjectType, None] = "ALL"
    
    # Enabled/Disabled
    enabled: bool = True
    
    def __init__(self, **kwargs):
        """Permet de surcharger les attributs à l'instanciation."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Auto-générer l'ID si non fourni
        if self.id is None:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Génère un ID basé sur le nom de classe."""
        name = self.__class__.__name__
        # CamelCase → snake_case
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def matches_scope(self, obj: FractalObject) -> bool:
        """Vérifie si l'objet est dans le scope de la règle."""
        if self.scope == "ALL":
            return True
        
        if isinstance(self.scope, ObjectType):
            return obj.object_type == self.scope
        
        if isinstance(self.scope, str):
            # Pattern de lineage avec wildcard
            pattern = self.scope.replace("*", ".*")
            return bool(re.match(pattern, obj.lineage, re.IGNORECASE))
        
        return False
    
    @abstractmethod
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        """
        Vérifie la règle sur un objet.
        
        Args:
            obj: L'objet à vérifier
            store: Le store complet pour contexte
            
        Returns:
            Liste de violations (vide si OK)
        """
        pass
    
    def create_violation(
        self,
        obj: FractalObject,
        message: str,
        suggestion: Optional[str] = None,
        severity: Optional[Severity] = None,
        context: Optional[Dict] = None
    ) -> Violation:
        """Helper pour créer une violation standardisée."""
        return Violation(
            rule_id=self.id,
            rule_name=self.name,
            object_id=obj.id,
            object_lineage=obj.lineage,
            severity=severity or self.default_severity,
            message=message,
            suggestion=suggestion,
            context=context or {}
        )
    
    def erk_expression(self) -> str:
        """Retourne l'expression ERK de la règle."""
        scope_str = "ALL" if self.scope == "ALL" else str(self.scope)
        return f"FOR {scope_str}: {self.description}"
    
    def __repr__(self) -> str:
        return f"<MetaRule:{self.id} ({self.name})>"


# =============================================================================
# RÈGLES D'IDENTITÉ FONDAMENTALES
# =============================================================================

class RequireId(MetaRule):
    """Tout objet doit avoir un id non vide."""
    
    id = "require_id"
    name = "ID Obligatoire"
    description = "require attribute 'id' non-empty"
    category = RuleCategory.IDENTITY
    default_severity = Severity.CRITICAL
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not obj.id or not obj.id.strip():
            return [self.create_violation(
                obj,
                "L'objet n'a pas d'identifiant (id vide ou manquant)",
                suggestion="Définir un id unique pour cet objet"
            )]
        return []


class RequireName(MetaRule):
    """Tout objet doit avoir un nom non vide."""
    
    id = "require_name"
    name = "Name Obligatoire"
    description = "require attribute 'name' non-empty"
    category = RuleCategory.IDENTITY
    default_severity = Severity.ERROR
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not obj.name or not obj.name.strip():
            return [self.create_violation(
                obj,
                "L'objet n'a pas de nom",
                suggestion="Définir un nom descriptif"
            )]
        return []


class RequireType(MetaRule):
    """Tout objet doit avoir un type IVC×DRO défini."""
    
    id = "require_type"
    name = "Type IVC×DRO Obligatoire"
    description = "require attribute 'object_type' != UNKNOWN"
    category = RuleCategory.IDENTITY
    default_severity = Severity.WARNING
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if obj.object_type == ObjectType.UNKNOWN:
            return [self.create_violation(
                obj,
                "Type IVC×DRO non défini (UNKNOWN)",
                suggestion="Classifier l'objet: I (Identity), V (View), C (Context), D (Definition), R (Rule), O (Option)"
            )]
        return []


class UniqueId(MetaRule):
    """Les IDs doivent être uniques dans le store."""
    
    id = "unique_id"
    name = "Unicité des IDs"
    description = "forbid duplicate 'id' values"
    category = RuleCategory.IDENTITY
    default_severity = Severity.CRITICAL
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._checked_ids: Set[str] = set()
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        # Note: cette règle vérifie les doublons au niveau du store
        # En pratique, un dict Python ne peut avoir de clés dupliquées
        # Mais on vérifie quand même pour les cas de merge/import
        
        duplicates = [
            other_id for other_id, other in store.items()
            if other_id == obj.id and other is not obj
        ]
        
        if duplicates:
            return [self.create_violation(
                obj,
                f"ID dupliqué: '{obj.id}' existe déjà",
                suggestion="Renommer l'objet avec un ID unique",
                context={"duplicates": duplicates}
            )]
        return []


# =============================================================================
# RÈGLES DE STRUCTURE (LINEAGE)
# =============================================================================

class RequireLineage(MetaRule):
    """Tout objet doit avoir un lineage non vide."""
    
    id = "require_lineage"
    name = "Lineage Obligatoire"
    description = "require attribute 'lineage' non-empty"
    category = RuleCategory.STRUCTURE
    default_severity = Severity.ERROR
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not obj.lineage or not obj.lineage.strip():
            return [self.create_violation(
                obj,
                "Lineage manquant ou vide",
                suggestion="Définir le chemin hiérarchique (ex: Core:Agent:LLM)"
            )]
        return []


class NoCycleInLineage(MetaRule):
    """Aucun cycle de lineage n'est toléré."""
    
    id = "no_cycle_lineage"
    name = "Pas de Cycle de Lineage"
    description = "forbid cycle in lineage (parent chain)"
    category = RuleCategory.STRUCTURE
    default_severity = Severity.CRITICAL
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        visited = set()
        current = obj
        chain = [obj.id]
        
        while current and current.parent_id:
            if current.parent_id in visited:
                return [self.create_violation(
                    obj,
                    f"Cycle détecté dans le lineage: {' → '.join(chain)} → {current.parent_id}",
                    suggestion="Corriger la chaîne parent pour éliminer le cycle",
                    context={"chain": chain, "cycle_at": current.parent_id}
                )]
            
            visited.add(current.id)
            chain.append(current.parent_id)
            current = store.get(current.parent_id)
        
        return []


class LineageMatchesParent(MetaRule):
    """Le lineage doit être cohérent avec le parent déclaré."""
    
    id = "lineage_matches_parent"
    name = "Cohérence Lineage/Parent"
    description = "require lineage prefix matches parent lineage"
    category = RuleCategory.STRUCTURE
    default_severity = Severity.ERROR
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not obj.parent_id:
            return []  # Pas de parent, pas de vérification
        
        parent = store.get(obj.parent_id)
        if not parent:
            return [self.create_violation(
                obj,
                f"Parent référencé '{obj.parent_id}' introuvable dans le store",
                suggestion="Vérifier l'ID du parent ou créer l'objet parent",
                severity=Severity.ERROR
            )]
        
        # Le lineage de l'objet doit commencer par le lineage du parent
        if not obj.lineage.lower().startswith(parent.lineage.lower()):
            return [self.create_violation(
                obj,
                f"Incohérence lineage/parent: '{obj.lineage}' ne commence pas par '{parent.lineage}'",
                suggestion=f"Le lineage devrait être '{parent.lineage}:{obj.name}' ou similaire"
            )]
        
        return []


class MaxDepth(MetaRule):
    """Limite de profondeur du lineage."""
    
    id = "max_depth"
    name = "Profondeur Maximale"
    description = "forbid lineage depth > MAX_DEPTH"
    category = RuleCategory.STRUCTURE
    default_severity = Severity.WARNING
    
    max_depth: int = 10
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        segments = obj.lineage_segments
        if len(segments) > self.max_depth:
            return [self.create_violation(
                obj,
                f"Profondeur excessive: {len(segments)} niveaux (max: {self.max_depth})",
                suggestion="Restructurer la hiérarchie pour réduire la profondeur",
                context={"depth": len(segments), "max": self.max_depth}
            )]
        return []


class OrphanWarning(MetaRule):
    """Alerte sur les objets orphelins (sans parent)."""
    
    id = "orphan_warning"
    name = "Objet Orphelin"
    description = "warn if object has no parent and depth > 1"
    category = RuleCategory.STRUCTURE
    default_severity = Severity.WARNING
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        # Les objets racine (depth=1) peuvent être orphelins légitimement
        if obj.is_orphan and obj.depth > 1:
            return [self.create_violation(
                obj,
                f"Objet orphelin: pas de parent défini pour profondeur {obj.depth}",
                suggestion="Définir un parent ou utiliser le système de suggestions C1/1"
            )]
        return []


# =============================================================================
# RÈGLES DE BUNDLE (ATTRIBUTES, METHODS)
# =============================================================================

class RequireAttribute(MetaRule):
    """Vérifie la présence d'un attribut spécifique."""
    
    id = "require_attribute"
    name = "Attribut Obligatoire"
    description = "require attribute '{attribute_name}'"
    category = RuleCategory.BUNDLE
    
    attribute_name: str = ""
    in_metadata: bool = True
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not self.attribute_name:
            return []
        
        if self.in_metadata:
            if self.attribute_name not in obj.metadata:
                return [self.create_violation(
                    obj,
                    f"Attribut manquant: '{self.attribute_name}' absent de metadata",
                    suggestion=f"Ajouter metadata['{self.attribute_name}'] = ..."
                )]
        else:
            if not hasattr(obj, self.attribute_name):
                return [self.create_violation(
                    obj,
                    f"Attribut manquant: '{self.attribute_name}' non défini",
                    suggestion=f"Définir l'attribut '{self.attribute_name}'"
                )]
        
        return []


class RequireMethodForAgent(MetaRule):
    """Les agents doivent avoir une méthode 'prompt' définie."""
    
    id = "agent_require_prompt"
    name = "Agent: Méthode prompt"
    description = "require method 'prompt' for type Agent"
    category = RuleCategory.BUNDLE
    scope = ObjectType.IDENTITY
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        # Vérifier si c'est un agent (par nom ou tags)
        is_agent = (
            "agent" in obj.name.lower() or
            "agent" in [t.lower() for t in obj.tags]
        )
        
        if not is_agent:
            return []
        
        # Vérifier la présence de 'prompt' dans metadata.methods
        methods = obj.metadata.get("methods", [])
        if "prompt" not in methods:
            return [self.create_violation(
                obj,
                "Agent sans méthode 'prompt' définie",
                suggestion="Ajouter 'prompt' à la liste des méthodes: metadata['methods'] = ['prompt', ...]"
            )]
        
        return []


class RequireRelationDependsOn(MetaRule):
    """Certains objets doivent dépendre d'une configuration."""
    
    id = "require_depends_on_config"
    name = "Dépendance Config"
    description = "require relation 'depends_on' Core:Config"
    category = RuleCategory.RELATION
    scope = "Project"  # S'applique aux objets dont le nom contient 'Project'
    
    def matches_scope(self, obj: FractalObject) -> bool:
        return "project" in obj.name.lower()
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        relations = obj.metadata.get("relations", {})
        depends_on = relations.get("depends_on", [])
        
        # Vérifier si Core:Config est dans les dépendances
        has_config_dep = any(
            "config" in dep.lower() 
            for dep in depends_on
        )
        
        if not has_config_dep:
            return [self.create_violation(
                obj,
                "Project sans dépendance vers une configuration",
                suggestion="Ajouter une relation depends_on vers Core:Config ou équivalent",
                severity=Severity.WARNING
            )]
        
        return []


# =============================================================================
# RÈGLES DE COHÉRENCE GLOBALE
# =============================================================================

class LineageSegmentsExist(MetaRule):
    """Chaque segment du lineage doit correspondre à un objet existant."""
    
    id = "lineage_segments_exist"
    name = "Segments de Lineage Valides"
    description = "require all lineage segments to exist as objects"
    category = RuleCategory.CONSISTENCY
    default_severity = Severity.WARNING
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        segments = obj.lineage_segments
        if len(segments) <= 1:
            return []  # Racine, pas de vérification
        
        violations = []
        
        # Construire les lineages partiels et vérifier leur existence
        for i in range(1, len(segments)):
            partial_lineage = ":".join(segments[:i])
            
            # Chercher un objet avec ce lineage
            exists = any(
                o.lineage.lower() == partial_lineage.lower()
                for o in store.values()
            )
            
            if not exists:
                violations.append(self.create_violation(
                    obj,
                    f"Segment de lineage orphelin: '{partial_lineage}' n'existe pas",
                    suggestion=f"Créer un objet avec lineage='{partial_lineage}'",
                    context={"missing_lineage": partial_lineage}
                ))
        
        return violations


class TypeConsistencyInHierarchy(MetaRule):
    """Les types IVC×DRO doivent être cohérents dans la hiérarchie."""
    
    id = "type_consistency_hierarchy"
    name = "Cohérence Types Hiérarchique"
    description = "warn if child type is incompatible with parent type"
    category = RuleCategory.CONSISTENCY
    default_severity = Severity.INFO
    
    # Matrice de compatibilité (parent_type -> child_types_ok)
    COMPATIBLE_TYPES = {
        ObjectType.IDENTITY: {ObjectType.IDENTITY, ObjectType.VIEW, ObjectType.CONTEXT},
        ObjectType.DEFINITION: {ObjectType.DEFINITION, ObjectType.RULE, ObjectType.OPTION},
        ObjectType.CONTEXT: {ObjectType.CONTEXT, ObjectType.VIEW, ObjectType.OPTION},
        ObjectType.VIEW: {ObjectType.VIEW},
        ObjectType.RULE: {ObjectType.RULE, ObjectType.OPTION},
        ObjectType.OPTION: {ObjectType.OPTION},
    }
    
    def check(self, obj: FractalObject, store: Dict[str, FractalObject]) -> List[Violation]:
        if not obj.parent_id:
            return []
        
        parent = store.get(obj.parent_id)
        if not parent or parent.object_type == ObjectType.UNKNOWN:
            return []
        
        compatible = self.COMPATIBLE_TYPES.get(parent.object_type, set())
        
        if obj.object_type not in compatible and obj.object_type != ObjectType.UNKNOWN:
            return [self.create_violation(
                obj,
                f"Type potentiellement incohérent: {obj.object_type.value} sous parent {parent.object_type.value}",
                suggestion=f"Vérifier la classification ou restructurer la hiérarchie",
                context={
                    "parent_type": parent.object_type.value,
                    "child_type": obj.object_type.value,
                    "compatible": [t.value for t in compatible]
                }
            )]
        
        return []


# =============================================================================
# MOTEUR DE VÉRIFICATION
# =============================================================================

class MetaRuleEngine:
    """
    Orchestrateur pour la vérification des MetaRules.
    
    Usage:
        engine = MetaRuleEngine()
        engine.add_rule(RequireId())
        engine.add_rule(NoCycleInLineage())
        
        result = engine.check_all(store)
        if not result.ok:
            for v in result.violations:
                print(v)
    """
    
    # Règles par défaut activées
    DEFAULT_RULES: List[Type[MetaRule]] = [
        RequireId,
        RequireName,
        RequireType,
        RequireLineage,
        NoCycleInLineage,
        LineageMatchesParent,
        MaxDepth,
        OrphanWarning,
        TypeConsistencyInHierarchy,
    ]
    
    def __init__(
        self,
        rules: Optional[List[MetaRule]] = None,
        include_defaults: bool = True
    ):
        self.rules: Dict[str, MetaRule] = {}
        
        if include_defaults:
            for rule_class in self.DEFAULT_RULES:
                self.add_rule(rule_class())
        
        if rules:
            for rule in rules:
                self.add_rule(rule)
    
    def add_rule(self, rule: MetaRule) -> None:
        """Ajoute une règle au moteur."""
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Supprime une règle par son ID."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Active une règle."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Désactive une règle."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def check_object(
        self,
        obj: FractalObject,
        store: Dict[str, FractalObject]
    ) -> List[Violation]:
        """
        Vérifie toutes les règles sur un objet.
        
        Returns:
            Liste des violations trouvées
        """
        violations = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if not rule.matches_scope(obj):
                continue
            
            try:
                rule_violations = rule.check(obj, store)
                violations.extend(rule_violations)
            except Exception as e:
                # En cas d'erreur dans une règle, on log mais on continue
                violations.append(Violation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    object_id=obj.id,
                    object_lineage=obj.lineage,
                    severity=Severity.ERROR,
                    message=f"Erreur lors de la vérification: {str(e)}",
                    context={"exception": str(type(e).__name__)}
                ))
        
        return violations
    
    def check_all(self, store: Dict[str, FractalObject]) -> AuditResult:
        """
        Vérifie toutes les règles sur tous les objets du store.
        
        Returns:
            AuditResult complet
        """
        all_violations = []
        objects_checked = 0
        rules_applied = 0
        
        for obj in store.values():
            objects_checked += 1
            violations = self.check_object(obj, store)
            all_violations.extend(violations)
            rules_applied += len([r for r in self.rules.values() if r.enabled])
        
        # Déterminer si OK (pas de CRITICAL ou ERROR)
        ok = not any(
            v.severity in (Severity.CRITICAL, Severity.ERROR)
            for v in all_violations
        )
        
        # Stats par sévérité
        stats = {
            "objects_checked": objects_checked,
            "rules_applied": len([r for r in self.rules.values() if r.enabled]),
            "total_violations": len(all_violations),
            "critical": len([v for v in all_violations if v.severity == Severity.CRITICAL]),
            "errors": len([v for v in all_violations if v.severity == Severity.ERROR]),
            "warnings": len([v for v in all_violations if v.severity == Severity.WARNING]),
            "info": len([v for v in all_violations if v.severity == Severity.INFO]),
        }
        
        return AuditResult(
            ok=ok,
            violations=all_violations,
            stats=stats
        )
    
    def list_rules(self) -> List[Dict]:
        """Liste toutes les règles enregistrées."""
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "category": r.category.value,
                "severity": r.default_severity.value,
                "enabled": r.enabled,
                "erk": r.erk_expression()
            }
            for r in self.rules.values()
        ]
    
    def export_rules_erk(self) -> str:
        """Exporte toutes les règles au format ERK."""
        lines = ["# EUREKAI MetaRules (ERK Format)", ""]
        
        # Grouper par catégorie
        by_category = {}
        for rule in self.rules.values():
            cat = rule.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(rule)
        
        for category, rules in by_category.items():
            lines.append(f"## {category.upper()}")
            for rule in rules:
                status = "✓" if rule.enabled else "✗"
                lines.append(f"  [{status}] {rule.erk_expression()}")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# API SIMPLIFIÉE
# =============================================================================

def check_metarules(
    store: Dict[str, FractalObject],
    rules: Optional[List[MetaRule]] = None,
    include_defaults: bool = True
) -> Dict:
    """
    API simplifiée pour vérifier les MetaRules.
    
    Args:
        store: Store fractal (dict id → FractalObject)
        rules: Règles additionnelles (optionnel)
        include_defaults: Inclure les règles par défaut
    
    Returns:
        Dictionnaire {ok, errors[], stats}
    """
    engine = MetaRuleEngine(rules=rules, include_defaults=include_defaults)
    result = engine.check_all(store)
    return result.to_dict()


def audit_store(store: Dict[str, FractalObject]) -> None:
    """
    Lance un audit complet et affiche le résultat.
    
    Usage en console:
        from metarules_engine import audit_store
        audit_store(my_store)
    """
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    print("\n" + "="*60)
    print("  EUREKAI METARULES AUDIT")
    print("="*60)
    print(result.summary())
    
    if result.violations:
        print("\n" + "-"*60)
        print("  VIOLATIONS DÉTAILLÉES")
        print("-"*60)
        
        for v in result.violations:
            print(f"\n{v}")
            if v.suggestion:
                print(f"   💡 {v.suggestion}")
    
    print("\n" + "="*60)
