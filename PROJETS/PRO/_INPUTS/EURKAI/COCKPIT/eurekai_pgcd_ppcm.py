"""
EUREKAI — Module PGCD/PPCM Logiques
====================================
Outils d'optimisation structurelle pour l'analyse fractale.

DÉFINITIONS OPÉRATIONNELLES
---------------------------

PGCD LOGIQUE (Plus Grand Commun Diviseur)
    Le PGCD logique d'un ensemble d'objets EUREKAI représente le NOYAU COMMUN
    maximal partagé par tous ces objets. C'est l'intersection des :
    - Définitions (D) : propriétés structurelles communes
    - Règles (R) : contraintes partagées
    - Options (O) : configurations par défaut identiques
    
    Formellement : PGCD(O₁, O₂, ..., Oₙ) = ∩ᵢ Oᵢ (intersection structurelle)
    
    Usage : Factorisation → extraction d'une classe parente ou d'un trait commun.

PPCM LOGIQUE (Plus Petit Commun Multiple)
    Le PPCM logique d'un ensemble de méthodes/règles représente l'ENSEMBLE MINIMAL
    qui couvre tous les besoins de tous les cas considérés. C'est la couverture
    minimale sans redondance.
    
    Formellement : PPCM(M₁, M₂, ..., Mₙ) = couverture_minimale(∪ᵢ besoins(Mᵢ))
    
    Usage : Optimisation → réduction du nombre de méthodes à implémenter.

AUTEUR : EUREKAI System
VERSION : G1/9
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional, Tuple
from collections import defaultdict
import json


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================

@dataclass
class ObjectDefinition:
    """
    Représentation d'un objet EUREKAI selon IVC×DRO.
    
    IVC = Identity, View, Context (axes de navigation)
    DRO = Definition, Rule, Option (composantes structurelles)
    """
    identity: str
    definitions: Dict[str, Any] = field(default_factory=dict)  # D : propriétés
    rules: Dict[str, Any] = field(default_factory=dict)        # R : contraintes
    options: Dict[str, Any] = field(default_factory=dict)      # O : configurations
    methods: Set[str] = field(default_factory=set)             # Méthodes disponibles
    
    def to_dict(self) -> Dict:
        return {
            "identity": self.identity,
            "definitions": self.definitions,
            "rules": self.rules,
            "options": self.options,
            "methods": list(self.methods)
        }


@dataclass
class CoreDefinition:
    """
    Résultat d'un calcul de PGCD logique.
    Représente le noyau commun extrait.
    """
    common_definitions: Dict[str, Any]
    common_rules: Dict[str, Any]
    common_options: Dict[str, Any]
    common_methods: Set[str]
    source_objects: List[str]
    coverage_ratio: float  # Pourcentage de factorisation réussie
    
    def summary(self) -> str:
        return (
            f"PGCD Logique ({len(self.source_objects)} objets)\n"
            f"├─ Définitions communes : {len(self.common_definitions)}\n"
            f"├─ Règles communes : {len(self.common_rules)}\n"
            f"├─ Options communes : {len(self.common_options)}\n"
            f"├─ Méthodes communes : {len(self.common_methods)}\n"
            f"└─ Taux de factorisation : {self.coverage_ratio:.1%}"
        )


@dataclass 
class MinimalMethodSet:
    """
    Résultat d'un calcul de PPCM logique.
    Représente l'ensemble minimal de méthodes couvrant tous les besoins.
    """
    methods: Set[str]
    coverage_map: Dict[str, Set[str]]  # méthode → cas couverts
    uncovered_cases: Set[str]          # cas non couverts (si any)
    optimization_ratio: float          # réduction vs union naïve
    
    def summary(self) -> str:
        return (
            f"PPCM Logique\n"
            f"├─ Méthodes minimales : {len(self.methods)}\n"
            f"├─ Cas couverts : {sum(len(v) for v in self.coverage_map.values())}\n"
            f"├─ Cas non couverts : {len(self.uncovered_cases)}\n"
            f"└─ Taux d'optimisation : {self.optimization_ratio:.1%}"
        )


# =============================================================================
# FONCTIONS D'ANALYSE — PGCD LOGIQUE
# =============================================================================

def compute_logical_pgcd(objects: List[ObjectDefinition]) -> CoreDefinition:
    """
    Calcule le PGCD logique d'un ensemble d'objets EUREKAI.
    
    Algorithme :
    1. Intersection des clés de définitions
    2. Pour chaque clé commune, vérifier l'égalité des valeurs
    3. Répéter pour rules et options
    4. Intersection des méthodes
    
    Args:
        objects: Liste d'objets à analyser
        
    Returns:
        CoreDefinition contenant le noyau commun
    """
    if not objects:
        return CoreDefinition({}, {}, {}, set(), [], 0.0)
    
    if len(objects) == 1:
        obj = objects[0]
        return CoreDefinition(
            common_definitions=obj.definitions.copy(),
            common_rules=obj.rules.copy(),
            common_options=obj.options.copy(),
            common_methods=obj.methods.copy(),
            source_objects=[obj.identity],
            coverage_ratio=1.0
        )
    
    # Intersection des définitions
    common_defs = _intersect_dicts([o.definitions for o in objects])
    
    # Intersection des règles
    common_rules = _intersect_dicts([o.rules for o in objects])
    
    # Intersection des options
    common_opts = _intersect_dicts([o.options for o in objects])
    
    # Intersection des méthodes
    common_methods = set.intersection(*[o.methods for o in objects]) if objects else set()
    
    # Calcul du taux de factorisation
    total_elements = sum(
        len(o.definitions) + len(o.rules) + len(o.options) + len(o.methods)
        for o in objects
    )
    common_elements = (
        len(common_defs) + len(common_rules) + 
        len(common_opts) + len(common_methods)
    ) * len(objects)
    
    coverage = common_elements / total_elements if total_elements > 0 else 0.0
    
    return CoreDefinition(
        common_definitions=common_defs,
        common_rules=common_rules,
        common_options=common_opts,
        common_methods=common_methods,
        source_objects=[o.identity for o in objects],
        coverage_ratio=coverage
    )


def _intersect_dicts(dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intersection de dictionnaires : garde les clés présentes partout
    avec des valeurs identiques.
    """
    if not dicts:
        return {}
    
    # Commencer avec les clés du premier dictionnaire
    common_keys = set(dicts[0].keys())
    
    # Intersection des clés
    for d in dicts[1:]:
        common_keys &= set(d.keys())
    
    # Vérifier l'égalité des valeurs
    result = {}
    for key in common_keys:
        values = [d[key] for d in dicts]
        if all(v == values[0] for v in values):
            result[key] = values[0]
    
    return result


def compute_hierarchical_pgcd(
    objects: List[ObjectDefinition],
    threshold: float = 0.5
) -> List[Tuple[CoreDefinition, List[str]]]:
    """
    Calcule le PGCD de manière hiérarchique, identifiant des sous-groupes
    ayant des noyaux communs significatifs.
    
    Args:
        objects: Liste d'objets à analyser
        threshold: Seuil minimal de factorisation pour former un groupe
        
    Returns:
        Liste de (CoreDefinition, [identities des objets du groupe])
    """
    if len(objects) <= 1:
        if objects:
            pgcd = compute_logical_pgcd(objects)
            return [(pgcd, [objects[0].identity])]
        return []
    
    # Matrice de similarité
    n = len(objects)
    similarity = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            pgcd = compute_logical_pgcd([objects[i], objects[j]])
            similarity[i][j] = similarity[j][i] = pgcd.coverage_ratio
    
    # Clustering simple par seuil
    groups = []
    used = set()
    
    for i in range(n):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, n):
            if j not in used and similarity[i][j] >= threshold:
                group.append(j)
        
        if len(group) > 1:
            for idx in group:
                used.add(idx)
            group_objects = [objects[idx] for idx in group]
            pgcd = compute_logical_pgcd(group_objects)
            groups.append((pgcd, [objects[idx].identity for idx in group]))
    
    # Objets isolés
    for i in range(n):
        if i not in used:
            pgcd = compute_logical_pgcd([objects[i]])
            groups.append((pgcd, [objects[i].identity]))
    
    return groups


# =============================================================================
# FONCTIONS D'ANALYSE — PPCM LOGIQUE  
# =============================================================================

@dataclass
class MethodRequirement:
    """
    Représente les besoins en méthodes d'un cas d'usage.
    """
    case_id: str
    required_methods: Set[str]
    optional_methods: Set[str] = field(default_factory=set)


def compute_logical_ppcm(requirements: List[MethodRequirement]) -> MinimalMethodSet:
    """
    Calcule le PPCM logique : ensemble minimal de méthodes couvrant
    tous les besoins requis.
    
    Algorithme (Set Cover Problem - approche gloutonne) :
    1. Union de tous les besoins requis
    2. Sélection itérative de la méthode couvrant le plus de besoins restants
    3. Jusqu'à couverture complète
    
    Args:
        requirements: Liste des besoins par cas d'usage
        
    Returns:
        MinimalMethodSet avec les méthodes sélectionnées
    """
    if not requirements:
        return MinimalMethodSet(set(), {}, set(), 1.0)
    
    # Construire la matrice méthode → cas couverts
    method_to_cases: Dict[str, Set[str]] = defaultdict(set)
    all_cases = set()
    all_required: Set[str] = set()
    
    for req in requirements:
        all_cases.add(req.case_id)
        all_required.update(req.required_methods)
        for method in req.required_methods:
            method_to_cases[method].add(req.case_id)
    
    # Algorithme glouton de couverture
    selected_methods: Set[str] = set()
    coverage_map: Dict[str, Set[str]] = {}
    covered_needs: Set[str] = set()
    
    # Pour chaque cas, on doit avoir TOUTES ses méthodes requises
    for req in requirements:
        for method in req.required_methods:
            if method not in selected_methods:
                selected_methods.add(method)
                coverage_map[method] = method_to_cases[method].copy()
    
    # Vérification de couverture
    uncovered = set()
    for req in requirements:
        if not req.required_methods.issubset(selected_methods):
            uncovered.add(req.case_id)
    
    # Ratio d'optimisation (vs union naïve de toutes les méthodes)
    naive_union = set()
    for req in requirements:
        naive_union.update(req.required_methods)
        naive_union.update(req.optional_methods)
    
    optimization = 1.0 - (len(selected_methods) / len(naive_union)) if naive_union else 1.0
    
    return MinimalMethodSet(
        methods=selected_methods,
        coverage_map=coverage_map,
        uncovered_cases=uncovered,
        optimization_ratio=optimization
    )


def compute_optimal_ppcm(
    requirements: List[MethodRequirement],
    available_methods: Set[str]
) -> MinimalMethodSet:
    """
    Version optimisée du PPCM qui tient compte des méthodes polyvalentes
    pouvant couvrir plusieurs besoins.
    
    Args:
        requirements: Liste des besoins par cas
        available_methods: Méthodes disponibles dans le système
        
    Returns:
        MinimalMethodSet optimisé
    """
    # Mapping méthode → besoins qu'elle peut satisfaire
    method_capabilities: Dict[str, Set[str]] = defaultdict(set)
    all_needs: Set[str] = set()
    
    for req in requirements:
        for method in req.required_methods:
            if method in available_methods:
                method_capabilities[method].add(f"{req.case_id}:{method}")
                all_needs.add(f"{req.case_id}:{method}")
    
    # Algorithme glouton optimisé
    selected: Set[str] = set()
    covered: Set[str] = set()
    coverage_map: Dict[str, Set[str]] = {}
    
    while covered != all_needs:
        # Trouver la méthode couvrant le plus de besoins non couverts
        best_method = None
        best_coverage = set()
        
        for method, capabilities in method_capabilities.items():
            if method not in selected:
                new_coverage = capabilities - covered
                if len(new_coverage) > len(best_coverage):
                    best_method = method
                    best_coverage = new_coverage
        
        if best_method is None:
            break  # Plus de progression possible
            
        selected.add(best_method)
        covered.update(best_coverage)
        coverage_map[best_method] = {c.split(":")[0] for c in best_coverage}
    
    uncovered_cases = {
        need.split(":")[0] for need in (all_needs - covered)
    }
    
    naive_size = len(set().union(*[r.required_methods for r in requirements]))
    optimization = 1.0 - (len(selected) / naive_size) if naive_size else 1.0
    
    return MinimalMethodSet(
        methods=selected,
        coverage_map=coverage_map,
        uncovered_cases=uncovered_cases,
        optimization_ratio=optimization
    )


# =============================================================================
# UTILITAIRES D'ANALYSE
# =============================================================================

def analyze_factorization_potential(objects: List[ObjectDefinition]) -> Dict:
    """
    Analyse le potentiel de factorisation d'un ensemble d'objets.
    
    Returns:
        Dictionnaire avec métriques et recommandations
    """
    if len(objects) < 2:
        return {"status": "insufficient_objects", "recommendation": None}
    
    pgcd = compute_logical_pgcd(objects)
    hierarchical = compute_hierarchical_pgcd(objects)
    
    # Analyse des définitions uniques vs partagées
    all_def_keys = set()
    for obj in objects:
        all_def_keys.update(obj.definitions.keys())
    
    shared_ratio = len(pgcd.common_definitions) / len(all_def_keys) if all_def_keys else 0
    
    recommendations = []
    
    if pgcd.coverage_ratio > 0.6:
        recommendations.append({
            "action": "CREATE_PARENT_CLASS",
            "rationale": f"Fort taux de factorisation ({pgcd.coverage_ratio:.1%})",
            "elements": list(pgcd.common_definitions.keys())
        })
    
    if len(hierarchical) > 1 and len(hierarchical) < len(objects):
        recommendations.append({
            "action": "CREATE_TRAIT_HIERARCHY",
            "rationale": f"{len(hierarchical)} groupes naturels identifiés",
            "groups": [(g[0].source_objects, g[0].coverage_ratio) for g in hierarchical]
        })
    
    return {
        "global_pgcd": pgcd.to_dict() if hasattr(pgcd, 'to_dict') else pgcd.summary(),
        "coverage_ratio": pgcd.coverage_ratio,
        "shared_definitions_ratio": shared_ratio,
        "natural_groups": len(hierarchical),
        "recommendations": recommendations
    }


def suggest_method_consolidation(
    requirements: List[MethodRequirement]
) -> Dict:
    """
    Suggère des consolidations de méthodes basées sur l'analyse PPCM.
    """
    ppcm = compute_logical_ppcm(requirements)
    
    # Identifier les méthodes redondantes
    all_methods = set()
    for req in requirements:
        all_methods.update(req.required_methods)
    
    redundant = all_methods - ppcm.methods
    
    # Identifier les méthodes critiques (couvrant beaucoup de cas)
    critical = sorted(
        ppcm.coverage_map.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:5]
    
    return {
        "minimal_set_size": len(ppcm.methods),
        "total_methods": len(all_methods),
        "redundant_methods": list(redundant),
        "critical_methods": [(m, list(cases)) for m, cases in critical],
        "optimization_ratio": ppcm.optimization_ratio,
        "summary": ppcm.summary()
    }


# =============================================================================
# EXEMPLES ET CAS DE TEST
# =============================================================================

def example_scenarios():
    """
    Exemples concrets d'utilisation PGCD/PPCM.
    """
    
    print("=" * 70)
    print("EXEMPLE 1 : PGCD sur types d'agents EUREKAI")
    print("=" * 70)
    
    # Définition des agents
    agent_analyzer = ObjectDefinition(
        identity="Agent.Analyzer",
        definitions={
            "type": "agent",
            "execution_model": "GEVR",
            "input_type": "structured",
            "output_type": "analysis"
        },
        rules={
            "requires_context": True,
            "stateless": True,
            "max_iterations": 10
        },
        options={
            "verbose": False,
            "cache_enabled": True
        },
        methods={"analyze", "validate", "report", "get_context", "execute"}
    )
    
    agent_executor = ObjectDefinition(
        identity="Agent.Executor",
        definitions={
            "type": "agent",
            "execution_model": "GEVR",
            "input_type": "command",
            "output_type": "result"
        },
        rules={
            "requires_context": True,
            "stateless": False,
            "max_iterations": 100
        },
        options={
            "verbose": False,
            "cache_enabled": True
        },
        methods={"execute", "validate", "rollback", "get_context", "commit"}
    )
    
    agent_validator = ObjectDefinition(
        identity="Agent.Validator",
        definitions={
            "type": "agent",
            "execution_model": "GEVR",
            "input_type": "structured",
            "output_type": "boolean"
        },
        rules={
            "requires_context": True,
            "stateless": True,
            "max_iterations": 5
        },
        options={
            "verbose": False,
            "cache_enabled": True
        },
        methods={"validate", "check_rules", "get_context", "report"}
    )
    
    agents = [agent_analyzer, agent_executor, agent_validator]
    
    # Calcul PGCD
    pgcd = compute_logical_pgcd(agents)
    print("\n>>> Résultat PGCD :")
    print(pgcd.summary())
    print("\nDéfinitions communes :", pgcd.common_definitions)
    print("Règles communes :", pgcd.common_rules)
    print("Options communes :", pgcd.common_options)
    print("Méthodes communes :", pgcd.common_methods)
    
    print("\n" + "=" * 70)
    print("EXEMPLE 2 : PPCM sur besoins de scénarios")
    print("=" * 70)
    
    # Définition des besoins par scénario
    scenario_deploy = MethodRequirement(
        case_id="scenario.deploy",
        required_methods={"validate", "execute", "commit", "notify"},
        optional_methods={"rollback", "audit"}
    )
    
    scenario_analyze = MethodRequirement(
        case_id="scenario.analyze",
        required_methods={"validate", "analyze", "report"},
        optional_methods={"export"}
    )
    
    scenario_migrate = MethodRequirement(
        case_id="scenario.migrate",
        required_methods={"validate", "execute", "rollback", "commit"},
        optional_methods={"backup", "notify"}
    )
    
    scenario_audit = MethodRequirement(
        case_id="scenario.audit",
        required_methods={"validate", "analyze", "report", "audit"},
        optional_methods={"export", "archive"}
    )
    
    requirements = [scenario_deploy, scenario_analyze, scenario_migrate, scenario_audit]
    
    # Calcul PPCM
    ppcm = compute_logical_ppcm(requirements)
    print("\n>>> Résultat PPCM :")
    print(ppcm.summary())
    print("\nMéthodes sélectionnées :", ppcm.methods)
    print("Carte de couverture :")
    for method, cases in sorted(ppcm.coverage_map.items()):
        print(f"  {method}: {cases}")
    
    print("\n" + "=" * 70)
    print("EXEMPLE 3 : Analyse de potentiel de factorisation")
    print("=" * 70)
    
    analysis = analyze_factorization_potential(agents)
    print("\n>>> Analyse :")
    print(f"Ratio de couverture global : {analysis['coverage_ratio']:.1%}")
    print(f"Ratio définitions partagées : {analysis['shared_definitions_ratio']:.1%}")
    print(f"Groupes naturels : {analysis['natural_groups']}")
    print("\nRecommandations :")
    for rec in analysis['recommendations']:
        print(f"  - {rec['action']}: {rec['rationale']}")
    
    print("\n" + "=" * 70)
    print("EXEMPLE 4 : Consolidation de méthodes")
    print("=" * 70)
    
    consolidation = suggest_method_consolidation(requirements)
    print("\n>>> Suggestions de consolidation :")
    print(f"Taille ensemble minimal : {consolidation['minimal_set_size']}")
    print(f"Total méthodes : {consolidation['total_methods']}")
    print(f"Méthodes redondantes : {consolidation['redundant_methods']}")
    print("Méthodes critiques :")
    for method, cases in consolidation['critical_methods']:
        print(f"  {method}: couvre {cases}")


def run_test_cases():
    """
    Cas de test pour validation.
    """
    print("\n" + "=" * 70)
    print("CAS DE TEST")
    print("=" * 70)
    
    # Test 1 : PGCD d'objets identiques
    print("\n[TEST 1] PGCD d'objets identiques")
    obj_a = ObjectDefinition(
        identity="A",
        definitions={"x": 1, "y": 2},
        rules={"r1": True},
        options={"o1": "val"},
        methods={"m1", "m2"}
    )
    obj_b = ObjectDefinition(
        identity="B",
        definitions={"x": 1, "y": 2},
        rules={"r1": True},
        options={"o1": "val"},
        methods={"m1", "m2"}
    )
    
    pgcd = compute_logical_pgcd([obj_a, obj_b])
    assert pgcd.coverage_ratio == 1.0, "Objets identiques → ratio 100%"
    assert pgcd.common_definitions == {"x": 1, "y": 2}
    print("  ✓ PASS : ratio 100%, toutes propriétés communes")
    
    # Test 2 : PGCD d'objets disjoints
    print("\n[TEST 2] PGCD d'objets disjoints")
    obj_c = ObjectDefinition(
        identity="C",
        definitions={"a": 1},
        rules={"r_a": True},
        options={},
        methods={"method_a"}
    )
    obj_d = ObjectDefinition(
        identity="D",
        definitions={"b": 2},
        rules={"r_b": False},
        options={},
        methods={"method_b"}
    )
    
    pgcd = compute_logical_pgcd([obj_c, obj_d])
    assert pgcd.common_definitions == {}
    assert pgcd.common_methods == set()
    print("  ✓ PASS : aucune propriété commune")
    
    # Test 3 : PPCM couverture complète
    print("\n[TEST 3] PPCM couverture complète")
    req1 = MethodRequirement("case1", {"m1", "m2"})
    req2 = MethodRequirement("case2", {"m2", "m3"})
    req3 = MethodRequirement("case3", {"m1", "m3"})
    
    ppcm = compute_logical_ppcm([req1, req2, req3])
    assert ppcm.methods == {"m1", "m2", "m3"}
    assert len(ppcm.uncovered_cases) == 0
    print("  ✓ PASS : couverture complète avec {m1, m2, m3}")
    
    # Test 4 : PPCM avec besoins identiques
    print("\n[TEST 4] PPCM avec besoins identiques")
    req_same1 = MethodRequirement("same1", {"m1"})
    req_same2 = MethodRequirement("same2", {"m1"})
    
    ppcm = compute_logical_ppcm([req_same1, req_same2])
    assert ppcm.methods == {"m1"}
    print("  ✓ PASS : une seule méthode suffit")
    
    # Test 5 : Liste vide
    print("\n[TEST 5] Entrées vides")
    pgcd_empty = compute_logical_pgcd([])
    ppcm_empty = compute_logical_ppcm([])
    assert pgcd_empty.coverage_ratio == 0.0
    assert ppcm_empty.methods == set()
    print("  ✓ PASS : gestion correcte des entrées vides")
    
    # Test 6 : Hiérarchie PGCD
    print("\n[TEST 6] PGCD hiérarchique")
    objs = [
        ObjectDefinition("G1-A", {"type": "G1", "x": 1}, {}, {}, {"m1"}),
        ObjectDefinition("G1-B", {"type": "G1", "x": 1}, {}, {}, {"m1"}),
        ObjectDefinition("G2-A", {"type": "G2", "y": 2}, {}, {}, {"m2"}),
        ObjectDefinition("G2-B", {"type": "G2", "y": 2}, {}, {}, {"m2"}),
    ]
    
    groups = compute_hierarchical_pgcd(objs, threshold=0.5)
    assert len(groups) == 2, f"Attendu 2 groupes, obtenu {len(groups)}"
    print(f"  ✓ PASS : {len(groups)} groupes identifiés")
    
    print("\n" + "-" * 70)
    print("TOUS LES TESTS PASSÉS ✓")
    print("-" * 70)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    example_scenarios()
    run_test_cases()
