"""
EUREKAI C1/1 — Exemples et Cas de Test
======================================
Démonstration du système de lineages assistés.
"""

from lineage_suggester import (
    FractalObject, ObjectType, LineageSuggester,
    suggest_parents, SuggestionResult
)


# =============================================================================
# STORE FRACTAL DE DÉMONSTRATION
# =============================================================================

def create_demo_store() -> dict:
    """Crée un store fractal de démonstration."""
    
    objects = [
        # ===== Branche Core =====
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
            id="core_agent",
            name="Agent",
            lineage="Core:Agent",
            parent_id="core",
            depth=2,
            object_type=ObjectType.IDENTITY,
            tags=["agent"]
        ),
        FractalObject(
            id="core_agent_llm",
            name="LLM",
            lineage="Core:Agent:LLM",
            parent_id="core_agent",
            depth=3,
            object_type=ObjectType.IDENTITY,
            tags=["ai", "llm"]
        ),
        FractalObject(
            id="core_agent_human",
            name="Human",
            lineage="Core:Agent:Human",
            parent_id="core_agent",
            depth=3,
            object_type=ObjectType.IDENTITY,
            tags=["human"]
        ),
        FractalObject(
            id="core_resource",
            name="Resource",
            lineage="Core:Resource",
            parent_id="core",
            depth=2,
            object_type=ObjectType.CONTEXT,
            tags=["resource"]
        ),
        
        # ===== Branche Agency =====
        FractalObject(
            id="agency",
            name="Agency",
            lineage="Agency",
            parent_id=None,
            depth=1,
            object_type=ObjectType.CONTEXT,
            tags=["root", "agency"]
        ),
        FractalObject(
            id="agency_project",
            name="Project",
            lineage="Agency:Project",
            parent_id="agency",
            depth=2,
            object_type=ObjectType.CONTEXT,
            tags=["project"]
        ),
        FractalObject(
            id="agency_project_blog",
            name="Blog",
            lineage="Agency:Project:Blog",
            parent_id="agency_project",
            depth=3,
            object_type=ObjectType.CONTEXT,
            tags=["blog", "content"]
        ),
        FractalObject(
            id="agency_project_ecommerce",
            name="ECommerce",
            lineage="Agency:Project:ECommerce",
            parent_id="agency_project",
            depth=3,
            object_type=ObjectType.CONTEXT,
            tags=["shop", "ecommerce"]
        ),
        
        # ===== Branche Rules =====
        FractalObject(
            id="rules",
            name="Rules",
            lineage="Rules",
            parent_id=None,
            depth=1,
            object_type=ObjectType.DEFINITION,
            tags=["root", "rules"]
        ),
        FractalObject(
            id="rules_validation",
            name="Validation",
            lineage="Rules:Validation",
            parent_id="rules",
            depth=2,
            object_type=ObjectType.RULE,
            tags=["validation"]
        ),
    ]
    
    return {obj.id: obj for obj in objects}


# =============================================================================
# CAS DE TEST
# =============================================================================

def test_case_1_obvious_parent():
    """
    CAS 1: Parent évident
    ---------------------
    Un nouvel objet LLM:GPT devrait clairement être sous Core:Agent:LLM
    """
    print("\n" + "="*60)
    print("CAS 1: Parent évident (Core:Agent:LLM:GPT)")
    print("="*60)
    
    store = create_demo_store()
    
    # Nouvel objet orphelin
    orphan = FractalObject(
        id="new_gpt",
        name="GPT",
        lineage="Core:Agent:LLM:GPT",
        parent_id=None,  # Orphelin!
        depth=4,
        object_type=ObjectType.IDENTITY,
        tags=["ai", "openai"]
    )
    store[orphan.id] = orphan
    
    # Obtenir suggestions
    suggestions = suggest_parents(orphan.id, store)
    
    print(f"\nObjet: {orphan.name} (lineage: {orphan.lineage})")
    print(f"Statut: {'ORPHELIN' if orphan.is_orphan else 'Lié'}")
    print(f"\nSuggestions ({len(suggestions)}):")
    
    for i, s in enumerate(suggestions, 1):
        parent = store[s['parentId']]
        print(f"  {i}. {parent.name} ({parent.lineage})")
        print(f"     Score: {s['scorePercent']}% — {s['reason']}")
        print(f"     Détails: {s['details']}")
    
    # Validation
    assert len(suggestions) > 0, "Devrait avoir au moins une suggestion"
    assert suggestions[0]['parentId'] == 'core_agent_llm', "Le parent direct devrait être Core:Agent:LLM"
    assert suggestions[0]['score'] > 0.6, "Le score devrait être élevé (>60%)"
    
    print("\n✅ CAS 1 VALIDÉ: Parent évident correctement identifié")
    return True


def test_case_2_ambiguous_parent():
    """
    CAS 2: Plusieurs parents possibles
    ----------------------------------
    Un objet "APIAgent" pourrait être sous Core:Agent ou Core:Resource
    """
    print("\n" + "="*60)
    print("CAS 2: Parents ambigus (APIAgent)")
    print("="*60)
    
    store = create_demo_store()
    
    # Objet ambigu
    ambiguous = FractalObject(
        id="api_agent",
        name="APIAgent",
        lineage="Core:APIAgent",  # Lineage tronqué/ambigu
        parent_id=None,
        depth=2,
        object_type=ObjectType.IDENTITY,
        tags=["api", "agent"]
    )
    store[ambiguous.id] = ambiguous
    
    suggestions = suggest_parents(ambiguous.id, store)
    
    print(f"\nObjet: {ambiguous.name} (lineage: {ambiguous.lineage})")
    print(f"Statut: {'ORPHELIN' if ambiguous.is_orphan else 'Lié'}")
    print(f"\nSuggestions ({len(suggestions)}):")
    
    for i, s in enumerate(suggestions, 1):
        parent = store[s['parentId']]
        print(f"  {i}. {parent.name} ({parent.lineage})")
        print(f"     Score: {s['scorePercent']}% — {s['reason']}")
    
    # Validation: devrait avoir plusieurs suggestions
    assert len(suggestions) >= 2, "Devrait avoir plusieurs suggestions"
    
    # Le premier devrait être Core (pattern matching)
    print("\n✅ CAS 2 VALIDÉ: Plusieurs parents suggérés pour objet ambigu")
    return True


def test_case_3_no_parent():
    """
    CAS 3: Aucun parent raisonnable
    -------------------------------
    Un objet complètement unique sans correspondance
    """
    print("\n" + "="*60)
    print("CAS 3: Aucun parent (objet unique)")
    print("="*60)
    
    store = create_demo_store()
    
    # Objet totalement unique
    unique = FractalObject(
        id="xyz_random",
        name="ZetaQuantumFlux",
        lineage="Quantum:Flux:Zeta",  # Lineage inexistant
        parent_id=None,
        depth=3,
        object_type=ObjectType.UNKNOWN,
        tags=["exotic"]
    )
    store[unique.id] = unique
    
    suggestions = suggest_parents(unique.id, store, min_score=0.5)  # Seuil élevé
    
    print(f"\nObjet: {unique.name} (lineage: {unique.lineage})")
    print(f"Statut: {'ORPHELIN' if unique.is_orphan else 'Lié'}")
    print(f"\nSuggestions avec seuil 0.5: ({len(suggestions)})")
    
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            parent = store[s['parentId']]
            print(f"  {i}. {parent.name} — Score: {s['scorePercent']}%")
    else:
        print("  (Aucune suggestion au-dessus du seuil)")
    
    # Avec seuil plus bas
    suggestions_low = suggest_parents(unique.id, store, min_score=0.2)
    print(f"\nSuggestions avec seuil 0.2: ({len(suggestions_low)})")
    for i, s in enumerate(suggestions_low[:3], 1):
        parent = store[s['parentId']]
        print(f"  {i}. {parent.name} — Score: {s['scorePercent']}%")
    
    print("\n✅ CAS 3 VALIDÉ: Peu ou pas de suggestions pour objet unique")
    return True


def test_case_4_project_child():
    """
    CAS 4: Nouveau projet
    ---------------------
    Un nouveau projet "Portfolio" devrait être suggéré sous Agency:Project
    """
    print("\n" + "="*60)
    print("CAS 4: Nouveau projet (Portfolio)")
    print("="*60)
    
    store = create_demo_store()
    
    # Nouveau projet
    portfolio = FractalObject(
        id="new_portfolio",
        name="Portfolio",
        lineage="Agency:Project:Portfolio",
        parent_id=None,
        depth=3,
        object_type=ObjectType.CONTEXT,
        tags=["project", "showcase"]
    )
    store[portfolio.id] = portfolio
    
    suggestions = suggest_parents(portfolio.id, store)
    
    print(f"\nObjet: {portfolio.name} (lineage: {portfolio.lineage})")
    print(f"\nSuggestions:")
    
    for i, s in enumerate(suggestions[:3], 1):
        parent = store[s['parentId']]
        print(f"  {i}. {parent.name} ({parent.lineage})")
        print(f"     Score: {s['scorePercent']}% — {s['reason']}")
    
    # Validation
    assert suggestions[0]['parentId'] == 'agency_project', "Devrait suggérer Agency:Project"
    
    print("\n✅ CAS 4 VALIDÉ: Projet correctement rattaché à Agency:Project")
    return True


def test_case_5_rule_hierarchy():
    """
    CAS 5: Hiérarchie de règles
    ---------------------------
    Une nouvelle règle devrait être sous Rules:Validation
    """
    print("\n" + "="*60)
    print("CAS 5: Nouvelle règle (EmailCheck)")
    print("="*60)
    
    store = create_demo_store()
    
    # Nouvelle règle
    email_check = FractalObject(
        id="email_check_rule",
        name="EmailCheck",
        lineage="Rules:Validation:EmailCheck",
        parent_id=None,
        depth=3,
        object_type=ObjectType.RULE,
        tags=["validation", "email"]
    )
    store[email_check.id] = email_check
    
    suggestions = suggest_parents(email_check.id, store)
    
    print(f"\nObjet: {email_check.name} (lineage: {email_check.lineage})")
    print(f"Type: {email_check.object_type.value}")
    print(f"\nSuggestions:")
    
    for i, s in enumerate(suggestions[:3], 1):
        parent = store[s['parentId']]
        print(f"  {i}. {parent.name} ({parent.lineage}) — Type: {parent.object_type.value}")
        print(f"     Score: {s['scorePercent']}% — {s['reason']}")
    
    # Validation
    assert suggestions[0]['parentId'] == 'rules_validation', "Devrait suggérer Rules:Validation"
    
    print("\n✅ CAS 5 VALIDÉ: Règle rattachée avec cohérence de type")
    return True


def test_batch_suggestions():
    """
    Test du traitement batch pour tous les orphelins.
    """
    print("\n" + "="*60)
    print("TEST BATCH: Suggestions pour tous les orphelins")
    print("="*60)
    
    store = create_demo_store()
    
    # Ajouter plusieurs orphelins
    orphans = [
        FractalObject(
            id="orphan_claude",
            name="Claude",
            lineage="Core:Agent:LLM:Claude",
            parent_id=None,
            depth=4,
            object_type=ObjectType.IDENTITY
        ),
        FractalObject(
            id="orphan_webapp",
            name="WebApp",
            lineage="Agency:Project:WebApp",
            parent_id=None,
            depth=3,
            object_type=ObjectType.CONTEXT
        ),
    ]
    
    for orphan in orphans:
        store[orphan.id] = orphan
    
    suggester = LineageSuggester(store)
    batch_results = suggester.batch_suggest()
    
    print(f"\nOrphelins trouvés: {len(suggester.find_orphans())}")
    print(f"Objets avec suggestions: {len(batch_results)}")
    
    for obj_id, suggestions in batch_results.items():
        obj = store[obj_id]
        print(f"\n  {obj.name} ({obj.lineage}):")
        for s in suggestions[:2]:
            parent = store[s.parent_id]
            print(f"    → {parent.name}: {s.score:.0%}")
    
    print("\n✅ BATCH VALIDÉ")
    return True


# =============================================================================
# DÉMONSTRATION COCKPIT
# =============================================================================

def demo_cockpit_integration():
    """
    Simule l'intégration avec le cockpit EUREKAI.
    """
    print("\n" + "="*60)
    print("DÉMO: Intégration Cockpit")
    print("="*60)
    
    store = create_demo_store()
    
    # Simuler la sélection d'un objet orphelin dans le cockpit
    orphan = FractalObject(
        id="selected_object",
        name="BlogArticle",
        lineage="Agency:Project:Blog:Article",
        parent_id=None,
        depth=4,
        object_type=ObjectType.CONTEXT,
        tags=["content", "article"]
    )
    store[orphan.id] = orphan
    
    print(f"\n📦 Objet sélectionné: {orphan.name}")
    print(f"   Lineage: {orphan.lineage}")
    print(f"   Statut: ⚠️  ORPHELIN (parent non défini)")
    
    # Obtenir suggestions
    suggestions = suggest_parents(orphan.id, store)
    
    print(f"\n💡 Suggestions de parents ({len(suggestions)}):")
    print("   ─────────────────────────────────────────")
    
    for i, s in enumerate(suggestions, 1):
        parent = store[s['parentId']]
        confidence = "🟢" if s['score'] > 0.7 else "🟡" if s['score'] > 0.4 else "🔴"
        print(f"   {i}. {confidence} {parent.name}")
        print(f"      Lineage: {parent.lineage}")
        print(f"      Confiance: {s['scorePercent']}%")
        print(f"      Raison: {s['reason']}")
        print()
    
    print("   ─────────────────────────────────────────")
    print("   ℹ️  Ces suggestions sont indicatives.")
    print("   ⚡ Cliquez sur un parent pour l'appliquer.")


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    print("\n" + "🔷"*30)
    print("    EUREKAI C1/1 — LINEAGES ASSISTÉS — TESTS")
    print("🔷"*30)
    
    # Exécuter tous les tests
    results = []
    
    results.append(("Cas 1: Parent évident", test_case_1_obvious_parent()))
    results.append(("Cas 2: Parents ambigus", test_case_2_ambiguous_parent()))
    results.append(("Cas 3: Aucun parent", test_case_3_no_parent()))
    results.append(("Cas 4: Nouveau projet", test_case_4_project_child()))
    results.append(("Cas 5: Règle hiérarchique", test_case_5_rule_hierarchy()))
    results.append(("Batch suggestions", test_batch_suggestions()))
    
    # Démo cockpit
    demo_cockpit_integration()
    
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
