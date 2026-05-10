"""
Tests — brief_team_orchestrator

Tests :
  1. tous les agents répondent avec la structure attendue
  2. la synthèse contient les 13 sections obligatoires
  3. scope_v0 et out_of_scope_v0 sont non vides et distincts
  4. aucune génération de code final déclenchée
  5. le module fonctionne sans LLM (mode stub, déterministe)
  6. backward compat : idea vide → failure propre
  7. idée EURKAI produit un brief cohérent avec les domaines détectés
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.brief_team_orchestrator import (
    run, AGENT_NAMES, _BRIEF_REQUIRED_FIELDS, MANIFEST
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_SIMPLE_IDEA = "Create a SaaS platform for freelancers to track invoices and payments."

_EURKAI_IDEA = (
    "EURKAI est un écosystème autonome d'orchestration, génération, validation "
    "et amélioration de projets numériques. "
    "Son objectif est de transformer une idée, un brief ou un niveau d'avancement "
    "quelconque en projet exploitable, en s'appuyant sur une architecture fractale "
    "où tout est objet, où les scénarios orchestrent les méthodes, où les règles et "
    "ressources sont injectées comme contexte, et où chaque projet peut être généré, "
    "testé, validé, documenté, déployé puis amélioré progressivement. "
    "EURKAI v0 doit être une version pure, minimale et complète dans son périmètre : "
    "elle doit remplir 100% de ses contrats, fonctionner en mode skeleton/stub, "
    "intégrer les objets essentiels, les scénarios de création projet, le catalogue, "
    "les validations, les structures Agency/Lab/Library/Blog, sans couche "
    "d'optimisation, de sécurité avancée ou de sur-ingénierie. "
    "Ces couches devront être ajoutées plus tard sous forme de plugins."
)

_CODE_GENERATION_MARKERS = [
    # Marqueurs Python non ambigus (ne peuvent pas apparaître dans du texte courant fr/en)
    "#!/usr/bin/env",
    "```python",
    "```javascript",
    "if __name__",
    "return {",
    "return [",
]


# ── Test 1 — Tous les agents répondent avec la structure attendue ─────────────

def test_all_agents_respond():
    result = run(_SIMPLE_IDEA, mode="stub", verbose=False)

    assert result["status"] == "success"
    assert "reports" in result

    reports = result["reports"]
    assert set(reports.keys()) == set(AGENT_NAMES), \
        f"Agents manquants: {set(AGENT_NAMES) - set(reports.keys())}"

    required_keys = {"agent", "focus", "recommendations", "questions", "risks", "brief_additions"}
    for agent_name, report in reports.items():
        missing = required_keys - set(report.keys())
        assert not missing, f"{agent_name} manque : {missing}"
        assert isinstance(report["recommendations"], list), f"{agent_name}.recommendations doit être une liste"
        assert isinstance(report["questions"],       list), f"{agent_name}.questions doit être une liste"
        assert isinstance(report["risks"],            list), f"{agent_name}.risks doit être une liste"
        assert isinstance(report["brief_additions"],  dict), f"{agent_name}.brief_additions doit être un dict"
        assert report["agent"] == agent_name, f"agent name mismatch: {report['agent']} ≠ {agent_name}"

    print("  [PASS] test_all_agents_respond")


# ── Test 2 — Brief contient les 13 sections obligatoires ─────────────────────

def test_brief_has_all_required_sections():
    result = run(_SIMPLE_IDEA, mode="stub", verbose=False)

    assert result["status"] == "success"
    brief = result["brief"]

    for field in _BRIEF_REQUIRED_FIELDS:
        assert field in brief, f"Champ manquant dans le brief : '{field}'"

    # Types
    assert isinstance(brief["project_name"],      str),  "project_name doit être str"
    assert isinstance(brief["vision"],             str),  "vision doit être str"
    assert isinstance(brief["objective"],          str),  "objective doit être str"
    assert isinstance(brief["target_users"],       list), "target_users doit être list"
    assert isinstance(brief["core_capabilities"],  list), "core_capabilities doit être list"
    assert isinstance(brief["expected_workflows"], list), "expected_workflows doit être list"
    assert isinstance(brief["key_objects"],        list), "key_objects doit être list"
    assert isinstance(brief["key_scenarios"],      list), "key_scenarios doit être list"
    assert isinstance(brief["constraints"],        list), "constraints doit être list"
    assert isinstance(brief["success_criteria"],   list), "success_criteria doit être list"
    assert isinstance(brief["open_questions"],     list), "open_questions doit être list"
    assert isinstance(brief["scope_v0"],           list), "scope_v0 doit être list"
    assert isinstance(brief["out_of_scope_v0"],    list), "out_of_scope_v0 doit être list"

    # Non vides
    assert brief["project_name"].strip(), "project_name ne doit pas être vide"
    assert brief["vision"].strip(),       "vision ne doit pas être vide"
    assert brief["objective"].strip(),    "objective ne doit pas être vide"

    print("  [PASS] test_brief_has_all_required_sections")


# ── Test 3 — scope_v0 et out_of_scope_v0 non vides et distincts ──────────────

def test_scope_v0_and_out_of_scope_v0_are_separate():
    result = run(_EURKAI_IDEA, mode="stub", verbose=False)

    assert result["status"] == "success"
    brief = result["brief"]

    scope     = brief["scope_v0"]
    outscope  = brief["out_of_scope_v0"]

    assert len(scope) >= 1,    f"scope_v0 doit contenir au moins 1 élément, a {len(scope)}"
    assert len(outscope) >= 1, f"out_of_scope_v0 doit contenir au moins 1 élément, a {len(outscope)}"

    # Aucun chevauchement exact (insensible à la casse)
    scope_lower    = {s.lower() for s in scope}
    outscope_lower = {s.lower() for s in outscope}
    overlap = scope_lower & outscope_lower
    assert not overlap, f"Chevauchement entre scope_v0 et out_of_scope_v0 : {overlap}"

    print(f"  [PASS] test_scope_v0_and_out_of_scope_v0_are_separate "
          f"(scope={len(scope)}, out={len(outscope)})")


# ── Test 4 — Aucune génération de code final déclenchée ──────────────────────

def test_no_code_generation():
    result = run(_EURKAI_IDEA, mode="stub", verbose=False)

    assert result["status"] == "success"
    brief = result["brief"]

    # Vérifier que le brief ne contient pas de fragments de code Python/JS
    brief_str = str(brief)
    for marker in _CODE_GENERATION_MARKERS:
        assert marker not in brief_str, \
            f"Fragment de code interdit trouvé dans le brief : '{marker}'"

    # Vérifier que les rapports agents ne déclenchent pas de génération de code
    reports_str = str(result["reports"])
    assert "def " not in reports_str or "Définir" in reports_str, \
        "Les rapports agents ne doivent pas contenir de code Python"

    print("  [PASS] test_no_code_generation")


# ── Test 5 — Fonctionne sans LLM (mode stub, déterministe) ───────────────────

def test_works_without_llm():
    # Deux appels identiques doivent donner le même résultat (déterministe)
    r1 = run(_SIMPLE_IDEA, mode="stub", verbose=False)
    r2 = run(_SIMPLE_IDEA, mode="stub", verbose=False)

    assert r1["status"] == "success"
    assert r2["status"] == "success"

    # Même project_name (déterministe)
    assert r1["brief"]["project_name"] == r2["brief"]["project_name"]

    # Même nombre d'agents consultés
    assert r1["meta"]["agents_called"] == r2["meta"]["agents_called"]

    # Mode "real" identique à "stub" en v0
    r3 = run(_SIMPLE_IDEA, mode="real", verbose=False)
    assert r3["status"] == "success", "mode='real' doit fonctionner sans LLM en v0"

    print("  [PASS] test_works_without_llm")


# ── Test 6 — Input vide → failure propre ──────────────────────────────────────

def test_empty_idea_returns_failure():
    for bad_input in ["", "  ", None]:
        r = run(bad_input, mode="stub", verbose=False)
        assert r["status"] == "failure", f"Input '{bad_input!r}' devrait retourner failure"
        assert r["brief"] is None
        assert r["meta"]["error"] == "idea_empty"

    print("  [PASS] test_empty_idea_returns_failure")


# ── Test 7 — Idée EURKAI produit un brief cohérent ───────────────────────────

def test_eurkai_idea_produces_coherent_brief():
    result = run(_EURKAI_IDEA, mode="stub", verbose=False)

    assert result["status"] == "success"
    brief = result["brief"]

    # project_name doit contenir EURKAI (identifiant ALL_CAPS présent dans l'idée)
    assert "EURKAI" in brief["project_name"], \
        f"project_name devrait contenir 'EURKAI', got: '{brief['project_name']}'"

    # vision non triviale (au moins 20 caractères)
    assert len(brief["vision"]) >= 20, f"vision trop courte: '{brief['vision']}'"

    # Core capabilities reflètent le domaine (orchestration, génération, validation)
    caps_lower = " ".join(brief["core_capabilities"]).lower()
    domain_terms = ["orchestrat", "génér", "valid", "modèle", "catalog", "pipeline"]
    found = [t for t in domain_terms if t in caps_lower]
    assert len(found) >= 2, \
        f"core_capabilities devrait refléter le domaine EURKAI — trouvé: {found}"

    # open_questions contient des questions de plusieurs agents
    assert len(brief["open_questions"]) >= 5, \
        f"open_questions devrait contenir ≥5 questions, a {len(brief['open_questions'])}"

    # Agents consultés : exactement AGENT_NAMES
    assert set(result["meta"]["agents_called"]) == set(AGENT_NAMES)
    assert len(result["meta"]["steps"]) == len(AGENT_NAMES) + 2  # select + agents + synthesis

    print(f"  [PASS] test_eurkai_idea_produces_coherent_brief "
          f"(project='{brief['project_name']}', "
          f"{len(brief['core_capabilities'])} caps, "
          f"{len(brief['open_questions'])} questions)")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_all_agents_respond,
        test_brief_has_all_required_sections,
        test_scope_v0_and_out_of_scope_v0_are_separate,
        test_no_code_generation,
        test_works_without_llm,
        test_empty_idea_returns_failure,
        test_eurkai_idea_produces_coherent_brief,
    ]

    print("=" * 65)
    print("  test_brief_team_orchestrator")
    print("=" * 65)

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__} : {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__} : {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed")
    print("=" * 65)
