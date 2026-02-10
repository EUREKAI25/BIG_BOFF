"""
EUREKAI C2/2 — Tests et Exemples MetaRules
==========================================
Démonstration et validation du système de MetaRules.
"""

import sys
sys.path.insert(0, '/home/claude/C1_extracted')

from lineage_suggester import FractalObject, ObjectType
from metarules_engine import (
    MetaRuleEngine, MetaRule, Violation, AuditResult, Severity,
    RuleCategory,
    # Règles d'identité
    RequireId, RequireName, RequireType, UniqueId,
    # Règles de structure
    RequireLineage, NoCycleInLineage, LineageMatchesParent,
    MaxDepth, OrphanWarning,
    # Règles de bundle
    RequireAttribute, RequireMethodForAgent, RequireRelationDependsOn,
    # Règles de cohérence
    LineageSegmentsExist, TypeConsistencyInHierarchy,
    # API
    check_metarules, audit_store
)


# =============================================================================
# STORE DE TEST VALIDE
# =============================================================================

def create_valid_store() -> dict:
    """Crée un store fractal valide (sans violations)."""
    
    objects = [
        # ===== Racines =====
        FractalObject(
            id="core",
            name="Core",
            lineage="Core",
            parent_id=None,
            depth=1,
            object_type=ObjectType.IDENTITY,
            tags=["root", "system"]
        ),
        FractalObject(
            id="agency",
            name="Agency",
            lineage="Agency",
            parent_id=None,
            depth=1,
            object_type=ObjectType.CONTEXT,
            tags=["root", "agency"]
        ),
        
        # ===== Branche Core:Agent =====
        FractalObject(
            id="core_agent",
            name="Agent",
            lineage="Core:Agent",
            parent_id="core",
            depth=2,
            object_type=ObjectType.IDENTITY,
            tags=["agent"],
            metadata={
                "methods": ["prompt", "execute", "validate"]
            }
        ),
        FractalObject(
            id="core_agent_llm",
            name="LLM",
            lineage="Core:Agent:LLM",
            parent_id="core_agent",
            depth=3,
            object_type=ObjectType.IDENTITY,
            tags=["ai", "llm"],
            metadata={
                "methods": ["prompt", "generate"]
            }
        ),
        
        # ===== Branche Core:Config =====
        FractalObject(
            id="core_config",
            name="Config",
            lineage="Core:Config",
            parent_id="core",
            depth=2,
            object_type=ObjectType.OPTION,
            tags=["config"]
        ),
        
        # ===== Branche Agency:Project =====
        FractalObject(
            id="agency_project",
            name="Project",
            lineage="Agency:Project",
            parent_id="agency",
            depth=2,
            object_type=ObjectType.CONTEXT,
            tags=["project"],
            metadata={
                "relations": {
                    "depends_on": ["Core:Config"]
                }
            }
        ),
    ]
    
    return {obj.id: obj for obj in objects}


# =============================================================================
# STORES AVEC VIOLATIONS SPÉCIFIQUES
# =============================================================================

def create_store_with_missing_id() -> dict:
    """Store avec un objet sans ID."""
    store = create_valid_store()
    store["broken"] = FractalObject(
        id="",  # ID vide!
        name="BrokenObject",
        lineage="Core:Broken",
        depth=2
    )
    return store


def create_store_with_cycle() -> dict:
    """Store avec un cycle dans le lineage."""
    store = create_valid_store()
    
    # Créer un cycle: A -> B -> C -> A
    store["cycle_a"] = FractalObject(
        id="cycle_a",
        name="CycleA",
        lineage="Cycle:A",
        parent_id="cycle_c",  # Pointe vers C qui pointe vers B qui pointe vers A
        depth=2
    )
    store["cycle_b"] = FractalObject(
        id="cycle_b",
        name="CycleB",
        lineage="Cycle:B",
        parent_id="cycle_a",
        depth=2
    )
    store["cycle_c"] = FractalObject(
        id="cycle_c",
        name="CycleC",
        lineage="Cycle:C",
        parent_id="cycle_b",
        depth=2
    )
    return store


def create_store_with_orphans() -> dict:
    """Store avec des objets orphelins profonds."""
    store = create_valid_store()
    
    store["orphan_deep"] = FractalObject(
        id="orphan_deep",
        name="DeepOrphan",
        lineage="Core:Agent:LLM:GPT:Turbo",
        parent_id=None,  # Orphelin!
        depth=5,
        object_type=ObjectType.IDENTITY
    )
    return store


def create_store_with_lineage_mismatch() -> dict:
    """Store avec incohérence lineage/parent."""
    store = create_valid_store()
    
    store["mismatch"] = FractalObject(
        id="mismatch",
        name="Mismatch",
        lineage="Agency:Something",  # Dit Agency
        parent_id="core",            # Mais parent est Core!
        depth=2,
        object_type=ObjectType.CONTEXT
    )
    return store


def create_store_with_missing_segments() -> dict:
    """Store avec segments de lineage manquants."""
    store = create_valid_store()
    
    # Objet avec lineage Core:Agent:LLM:GPT mais GPT n'a pas de parent Core:Agent:LLM:GPT existant
    # (en fait Core:Agent:LLM existe, donc on crée un cas où le segment intermédiaire manque)
    store["gap_object"] = FractalObject(
        id="gap_object",
        name="GapObject",
        lineage="Core:Missing:Something",  # Core:Missing n'existe pas
        parent_id="core",
        depth=3,
        object_type=ObjectType.IDENTITY
    )
    return store


def create_store_with_type_issues() -> dict:
    """Store avec incohérences de types."""
    store = create_valid_store()
    
    # Un objet RULE sous un parent IDENTITY (peu cohérent)
    store["bad_type"] = FractalObject(
        id="bad_type",
        name="BadTypeRule",
        lineage="Core:Agent:SomeRule",
        parent_id="core_agent",  # IDENTITY parent
        depth=3,
        object_type=ObjectType.RULE  # RULE enfant - incohérent
    )
    return store


def create_store_agent_without_prompt() -> dict:
    """Store avec un agent sans méthode prompt."""
    store = create_valid_store()
    
    store["broken_agent"] = FractalObject(
        id="broken_agent",
        name="BrokenAgent",
        lineage="Core:Agent:Broken",
        parent_id="core_agent",
        depth=3,
        object_type=ObjectType.IDENTITY,
        tags=["agent"],
        metadata={
            "methods": ["execute", "validate"]  # Pas de 'prompt'!
        }
    )
    return store


# =============================================================================
# CAS DE TEST
# =============================================================================

def test_valid_store():
    """
    TEST 1: Store Valide
    --------------------
    Un store bien formé ne doit générer aucune violation critique/error.
    """
    print("\n" + "="*60)
    print("TEST 1: Store valide (aucune violation attendue)")
    print("="*60)
    
    store = create_valid_store()
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    print(f"\nObjets vérifiés: {result.stats['objects_checked']}")
    print(f"Règles appliquées: {result.stats['rules_applied']}")
    print(f"Violations: {result.stats['total_violations']}")
    
    # Afficher les éventuels warnings/info
    for v in result.violations:
        print(f"  {v}")
    
    # Validation
    critical_errors = result.stats.get('critical', 0) + result.stats.get('errors', 0)
    assert critical_errors == 0, f"Store valide devrait avoir 0 erreurs critiques, got {critical_errors}"
    assert result.ok, "result.ok devrait être True pour un store valide"
    
    print("\n✅ TEST 1 VALIDÉ: Store valide accepté")
    return True


def test_missing_id():
    """
    TEST 2: ID Manquant
    -------------------
    La règle RequireId doit détecter les objets sans ID.
    """
    print("\n" + "="*60)
    print("TEST 2: Détection ID manquant")
    print("="*60)
    
    store = create_store_with_missing_id()
    result = check_metarules(store)
    
    print(f"\nViolations trouvées: {len(result['errors'])}")
    
    # Chercher la violation spécifique
    id_violations = [
        e for e in result['errors']
        if e['ruleId'] == 'require_id'
    ]
    
    print(f"Violations 'require_id': {len(id_violations)}")
    for v in id_violations:
        print(f"  🔴 {v['message']}")
    
    assert len(id_violations) >= 1, "Devrait détecter l'ID manquant"
    assert not result['ok'], "result.ok devrait être False"
    
    print("\n✅ TEST 2 VALIDÉ: ID manquant détecté")
    return True


def test_cycle_detection():
    """
    TEST 3: Détection de Cycles
    ---------------------------
    La règle NoCycleInLineage doit détecter les cycles parent.
    """
    print("\n" + "="*60)
    print("TEST 3: Détection de cycles")
    print("="*60)
    
    store = create_store_with_cycle()
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    cycle_violations = result.filter_by_rule('no_cycle_lineage')
    
    print(f"\nCycles détectés: {len(cycle_violations)}")
    for v in cycle_violations:
        print(f"  🔴 {v.object_id}: {v.message}")
        if v.context.get('chain'):
            print(f"      Chain: {' → '.join(v.context['chain'])}")
    
    assert len(cycle_violations) >= 1, "Devrait détecter au moins un cycle"
    
    print("\n✅ TEST 3 VALIDÉ: Cycles détectés")
    return True


def test_orphan_warning():
    """
    TEST 4: Avertissement Orphelins
    --------------------------------
    La règle OrphanWarning doit signaler les orphelins profonds.
    """
    print("\n" + "="*60)
    print("TEST 4: Avertissement orphelins profonds")
    print("="*60)
    
    store = create_store_with_orphans()
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    orphan_warnings = [
        v for v in result.violations
        if v.rule_id == 'orphan_warning'
    ]
    
    print(f"\nOrphelins signalés: {len(orphan_warnings)}")
    for v in orphan_warnings:
        print(f"  🟡 {v.object_id}: {v.message}")
    
    assert len(orphan_warnings) >= 1, "Devrait détecter l'orphelin profond"
    
    # Vérifier que c'est bien un WARNING, pas une ERROR
    assert all(v.severity == Severity.WARNING for v in orphan_warnings)
    
    print("\n✅ TEST 4 VALIDÉ: Orphelins signalés en warning")
    return True


def test_lineage_parent_mismatch():
    """
    TEST 5: Incohérence Lineage/Parent
    ----------------------------------
    La règle LineageMatchesParent doit détecter les incohérences.
    """
    print("\n" + "="*60)
    print("TEST 5: Incohérence lineage/parent")
    print("="*60)
    
    store = create_store_with_lineage_mismatch()
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    mismatch_violations = result.filter_by_rule('lineage_matches_parent')
    
    print(f"\nIncohérences détectées: {len(mismatch_violations)}")
    for v in mismatch_violations:
        print(f"  🟠 {v.object_id}: {v.message}")
        if v.suggestion:
            print(f"      💡 {v.suggestion}")
    
    assert len(mismatch_violations) >= 1, "Devrait détecter l'incohérence"
    
    print("\n✅ TEST 5 VALIDÉ: Incohérence lineage/parent détectée")
    return True


def test_type_coherence():
    """
    TEST 6: Cohérence des Types
    ---------------------------
    La règle TypeConsistencyInHierarchy doit signaler les types incohérents.
    """
    print("\n" + "="*60)
    print("TEST 6: Cohérence des types IVC×DRO")
    print("="*60)
    
    store = create_store_with_type_issues()
    engine = MetaRuleEngine()
    result = engine.check_all(store)
    
    type_violations = result.filter_by_rule('type_consistency_hierarchy')
    
    print(f"\nIncohérences de type: {len(type_violations)}")
    for v in type_violations:
        print(f"  🔵 {v.object_id}: {v.message}")
        ctx = v.context
        print(f"      Parent: {ctx.get('parent_type')}, Enfant: {ctx.get('child_type')}")
        print(f"      Types compatibles: {ctx.get('compatible')}")
    
    assert len(type_violations) >= 1, "Devrait détecter l'incohérence de type"
    
    print("\n✅ TEST 6 VALIDÉ: Incohérence de type détectée")
    return True


def test_agent_method_rule():
    """
    TEST 7: Méthode Agent
    ---------------------
    La règle RequireMethodForAgent doit vérifier 'prompt' sur les agents.
    """
    print("\n" + "="*60)
    print("TEST 7: Méthode 'prompt' obligatoire pour agents")
    print("="*60)
    
    store = create_store_agent_without_prompt()
    
    # Ajouter la règle spécifique
    engine = MetaRuleEngine()
    engine.add_rule(RequireMethodForAgent())
    
    result = engine.check_all(store)
    
    agent_violations = result.filter_by_rule('agent_require_prompt')
    
    print(f"\nAgents sans 'prompt': {len(agent_violations)}")
    for v in agent_violations:
        print(f"  🟠 {v.object_id}: {v.message}")
    
    assert len(agent_violations) >= 1, "Devrait détecter l'agent sans prompt"
    
    print("\n✅ TEST 7 VALIDÉ: Agent sans 'prompt' détecté")
    return True


def test_custom_rule():
    """
    TEST 8: Règle Personnalisée
    ---------------------------
    Démonstration de création d'une règle custom.
    """
    print("\n" + "="*60)
    print("TEST 8: Règle personnalisée")
    print("="*60)
    
    # Créer une règle custom
    class RequireDescription(MetaRule):
        """Tous les objets doivent avoir une description."""
        
        id = "custom_require_description"
        name = "Description Obligatoire"
        description = "require attribute 'description' in metadata"
        category = RuleCategory.BUNDLE
        default_severity = Severity.INFO
        
        def check(self, obj, store):
            if "description" not in obj.metadata:
                return [self.create_violation(
                    obj,
                    "Pas de description définie",
                    suggestion="Ajouter metadata['description'] = '...'"
                )]
            return []
    
    store = create_valid_store()
    engine = MetaRuleEngine()
    engine.add_rule(RequireDescription())
    
    result = engine.check_all(store)
    
    desc_violations = result.filter_by_rule('custom_require_description')
    
    print(f"\nObjets sans description: {len(desc_violations)}")
    for v in desc_violations[:3]:  # Limiter l'affichage
        print(f"  🔵 {v.object_id}")
    if len(desc_violations) > 3:
        print(f"  ... et {len(desc_violations) - 3} autres")
    
    # Tous nos objets de test n'ont pas de description
    assert len(desc_violations) > 0, "Devrait détecter les objets sans description"
    
    print("\n✅ TEST 8 VALIDÉ: Règle personnalisée fonctionne")
    return True


def test_enable_disable_rules():
    """
    TEST 9: Activation/Désactivation des Règles
    -------------------------------------------
    Vérifier le contrôle des règles.
    """
    print("\n" + "="*60)
    print("TEST 9: Activation/Désactivation des règles")
    print("="*60)
    
    store = create_store_with_orphans()
    engine = MetaRuleEngine()
    
    # Vérifier avec la règle active
    result1 = engine.check_all(store)
    orphan_count1 = len(result1.filter_by_rule('orphan_warning'))
    print(f"\nAvec OrphanWarning activé: {orphan_count1} violations")
    
    # Désactiver la règle
    engine.disable_rule('orphan_warning')
    result2 = engine.check_all(store)
    orphan_count2 = len(result2.filter_by_rule('orphan_warning'))
    print(f"Avec OrphanWarning désactivé: {orphan_count2} violations")
    
    assert orphan_count2 == 0, "Règle désactivée ne devrait pas générer de violations"
    
    # Réactiver
    engine.enable_rule('orphan_warning')
    result3 = engine.check_all(store)
    orphan_count3 = len(result3.filter_by_rule('orphan_warning'))
    print(f"Avec OrphanWarning réactivé: {orphan_count3} violations")
    
    assert orphan_count3 == orphan_count1, "Règle réactivée devrait retrouver les violations"
    
    print("\n✅ TEST 9 VALIDÉ: Contrôle des règles fonctionne")
    return True


def test_erk_export():
    """
    TEST 10: Export Format ERK
    --------------------------
    Vérifier l'export des règles en format ERK.
    """
    print("\n" + "="*60)
    print("TEST 10: Export format ERK")
    print("="*60)
    
    engine = MetaRuleEngine()
    erk_output = engine.export_rules_erk()
    
    print("\nExport ERK:")
    print("-" * 40)
    print(erk_output)
    print("-" * 40)
    
    assert "# EUREKAI MetaRules" in erk_output
    assert "FOR ALL" in erk_output or "FOR" in erk_output
    
    print("\n✅ TEST 10 VALIDÉ: Export ERK généré")
    return True


# =============================================================================
# DÉMONSTRATION COCKPIT
# =============================================================================

def demo_cockpit_audit():
    """
    Simulation d'intégration cockpit.
    """
    print("\n" + "="*60)
    print("  DÉMO: Audit Cockpit EUREKAI")
    print("="*60)
    
    # Store avec plusieurs types de violations
    store = create_valid_store()
    
    # Ajouter des problèmes variés
    store["orphan"] = FractalObject(
        id="orphan_obj",
        name="OrphanObject",
        lineage="Core:Agent:LLM:Orphan:Deep",
        parent_id=None,
        depth=5,
        object_type=ObjectType.UNKNOWN
    )
    
    store["no_name"] = FractalObject(
        id="no_name_obj",
        name="",  # Pas de nom!
        lineage="Core:NoName",
        parent_id="core",
        depth=2
    )
    
    # Lancer l'audit
    engine = MetaRuleEngine()
    engine.add_rule(RequireMethodForAgent())
    
    result = engine.check_all(store)
    
    print("\n📊 RAPPORT D'AUDIT")
    print("─" * 50)
    print(result.summary())
    
    if result.violations:
        print("\n📋 DÉTAIL DES VIOLATIONS")
        print("─" * 50)
        
        # Grouper par sévérité
        for sev in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]:
            violations = result.filter_by_severity(sev)
            if violations:
                icon = {"critical": "🔴", "error": "🟠", "warning": "🟡", "info": "🔵"}[sev.value]
                print(f"\n{icon} {sev.value.upper()} ({len(violations)})")
                for v in violations:
                    print(f"   • [{v.rule_id}] {v.object_lineage or v.object_id}")
                    print(f"     {v.message}")
                    if v.suggestion:
                        print(f"     💡 {v.suggestion}")
    
    print("\n" + "─" * 50)
    print(f"{'✅ AUDIT OK' if result.ok else '❌ AUDIT FAILED'}")
    print("─" * 50)


def demo_list_rules():
    """
    Affiche la liste des règles disponibles.
    """
    print("\n" + "="*60)
    print("  CATALOGUE DES METARULES")
    print("="*60)
    
    engine = MetaRuleEngine()
    
    # Ajouter quelques règles supplémentaires
    engine.add_rule(RequireMethodForAgent())
    engine.add_rule(RequireRelationDependsOn())
    engine.add_rule(LineageSegmentsExist())
    
    rules = engine.list_rules()
    
    # Grouper par catégorie
    by_cat = {}
    for r in rules:
        cat = r['category']
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(r)
    
    for cat, cat_rules in sorted(by_cat.items()):
        print(f"\n📁 {cat.upper()}")
        for r in cat_rules:
            status = "✓" if r['enabled'] else "✗"
            severity_icon = {
                "critical": "🔴",
                "error": "🟠",
                "warning": "🟡",
                "info": "🔵"
            }.get(r['severity'], "⚪")
            
            print(f"  [{status}] {severity_icon} {r['id']}")
            print(f"       {r['name']}")
            print(f"       ERK: {r['erk']}")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "🔷"*30)
    print("    EUREKAI C2/2 — METARULES — TESTS")
    print("🔷"*30)
    
    # Exécuter tous les tests
    results = []
    
    results.append(("Test 1: Store valide", test_valid_store()))
    results.append(("Test 2: ID manquant", test_missing_id()))
    results.append(("Test 3: Cycles", test_cycle_detection()))
    results.append(("Test 4: Orphelins", test_orphan_warning()))
    results.append(("Test 5: Lineage/Parent", test_lineage_parent_mismatch()))
    results.append(("Test 6: Types", test_type_coherence()))
    results.append(("Test 7: Agent method", test_agent_method_rule()))
    results.append(("Test 8: Règle custom", test_custom_rule()))
    results.append(("Test 9: Enable/Disable", test_enable_disable_rules()))
    results.append(("Test 10: Export ERK", test_erk_export()))
    
    # Démos
    demo_list_rules()
    demo_cockpit_audit()
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passés")
    print("="*60)
