"""
demo_brief_team_orchestrator.py
Démo du module EURKAI modules/brief_team_orchestrator.

Scénarios :
  1. EURKAI v0         — l'idée centrale EURKAI (idée riche, multilingue fr)
  2. SaaS freelance    — cas SaaS classique
  3. Idée vague        — robustesse sur input court
  4. Idée anglaise     — détection bilingue
  5. Input vide        — retour failure propre

Génère : output_brief_team_orchestrator_demo.json
         EurkaiV0_Brief.json  (brief EURKAI uniquement)

Usage :
  python modules/demo_brief_team_orchestrator.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.brief_team_orchestrator import run


# ── Idée centrale EURKAI ──────────────────────────────────────────────────────

EURKAI_IDEA = (
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _print_brief(brief):
    if brief is None:
        print("  (no brief)")
        return
    print(f"  project_name      : {brief['project_name']}")
    print(f"  vision            : {brief['vision'][:100]}...")
    print(f"  objective         : {brief['objective'][:100]}...")
    print(f"  target_users ({len(brief['target_users'])})   : {', '.join(brief['target_users'])}")
    print(f"  core_capabilities : {len(brief['core_capabilities'])} items")
    for cap in brief["core_capabilities"][:3]:
        print(f"    · {cap}")
    print(f"  key_objects ({len(brief['key_objects'])})    : {', '.join(brief['key_objects'][:5])}")
    print(f"  key_scenarios ({len(brief['key_scenarios'])}) :")
    for sc in brief["key_scenarios"][:3]:
        print(f"    · {sc}")
    print(f"  constraints ({len(brief['constraints'])})    :")
    for c in brief["constraints"][:3]:
        print(f"    · {c}")
    print(f"  success_criteria ({len(brief['success_criteria'])}) :")
    for sc in brief["success_criteria"][:3]:
        print(f"    · {sc}")
    print(f"  open_questions ({len(brief['open_questions'])}) :")
    for q in brief["open_questions"][:3]:
        print(f"    ? {q}")
    print(f"  scope_v0 ({len(brief['scope_v0'])})          :")
    for s in brief["scope_v0"][:4]:
        print(f"    ✓ {s}")
    print(f"  out_of_scope_v0 ({len(brief['out_of_scope_v0'])}) :")
    for o in brief["out_of_scope_v0"][:3]:
        print(f"    ✗ {o}")


def step(label, idea, context=None, mode="stub"):
    print(f"\n{'─' * 65}")
    print(f"  {label}")
    print(f"{'─' * 65}")
    result = run(idea, context=context, mode=mode, verbose=False)
    icon = "✓" if result["status"] == "success" else "✗"
    n_agents = len(result["meta"].get("agents_called", []))
    print(f"  {icon}  status: {result['status']} — {n_agents} agents consultés")
    if result["status"] == "success":
        _print_brief(result["brief"])
    else:
        print(f"  error: {result['meta'].get('error')}")
    return result


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    output = {}

    print()
    print("=" * 65)
    print("  EURKAI — brief_team_orchestrator v0.1.0 — Démo")
    print("=" * 65)

    # ── 1. EURKAI — idée centrale ─────────────────────────────────────────────
    print("\n\n══ Cas 1 : EURKAI v0 — idée centrale (fr, riche, multi-domaines)")
    r1 = step("EURKAI v0 — idée centrale", EURKAI_IDEA, mode="stub")
    output["cas1_eurkai_v0"] = r1

    # Exporter le brief EURKAI séparément
    if r1["status"] == "success":
        eurkai_brief_path = Path(__file__).parent.parent / "_OUTPUTS" / "EurkaiV0_Brief.json"
        eurkai_brief_path.parent.mkdir(exist_ok=True)
        eurkai_brief_path.write_text(
            json.dumps(r1["brief"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n  → EurkaiV0_Brief.json exporté : {eurkai_brief_path}")

    # ── 2. SaaS freelance ─────────────────────────────────────────────────────
    print("\n\n══ Cas 2 : SaaS freelance (cas classique)")
    r2 = step(
        "SaaS freelance invoices",
        "Create a SaaS platform that helps freelancers track invoices, payments "
        "and client contracts. The system should generate PDF invoices, send reminders, "
        "and provide a dashboard with revenue analytics.",
        context={"project_name": "FreelanceTrack"},
        mode="stub",
    )
    output["cas2_saas_freelance"] = r2

    # ── 3. Idée vague ─────────────────────────────────────────────────────────
    print("\n\n══ Cas 3 : Idée vague (robustesse)")
    r3 = step("Idée vague — peu de signaux", "Je veux créer un outil pour mon équipe.", mode="stub")
    output["cas3_vague"] = r3

    # ── 4. Idée anglaise ──────────────────────────────────────────────────────
    print("\n\n══ Cas 4 : Idée en anglais (bilingue)")
    r4 = step(
        "Knowledge base with AI agents",
        "Build an autonomous AI agent platform where multiple specialized agents "
        "collaborate to analyze documents, extract knowledge, generate reports, "
        "and deploy validated artifacts to a content library.",
        mode="stub",
    )
    output["cas4_english_agents"] = r4

    # ── 5. Input vide ─────────────────────────────────────────────────────────
    print("\n\n══ Cas 5 : Input vide → failure propre")
    r5 = step("Input vide — erreur attendue", "", mode="stub")
    output["cas5_empty"] = r5

    # ── Export global ─────────────────────────────────────────────────────────
    out_path = Path(__file__).parent / "output_brief_team_orchestrator_demo.json"
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n{'=' * 65}")
    print(f"  Output exporté → {out_path}")
    print(f"  EurkaiV0_Brief → _OUTPUTS/EurkaiV0_Brief.json")
    print("=" * 65)


if __name__ == "__main__":
    main()
