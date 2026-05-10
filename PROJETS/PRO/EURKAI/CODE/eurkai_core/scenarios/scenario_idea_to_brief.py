"""
scenario_idea_to_brief
Scénario autonome : idea → brief structuré.

Usage direct :
    from scenarios.scenario_idea_to_brief import run
    result = run({"idea": "create a SaaS that helps freelancers track invoices"})

Futur usage via convert() :
    idea.convert("brief")   →  appelle run() avec idea.data

Étapes :
  1. validate_input   — vérifie présence et non-vacuité de "idea"
  2. generate_brief   — appelle agent_brief
  3. normalize_output — garantit la structure des champs brief
  4. assemble_result  — construit le retour standardisé {from/to/data/meta}

Sortie standardisée (compatible futur convert()) :
  {
    "status": "success" | "failure",
    "from":   "idea",
    "to":     "brief",
    "data":   {"brief": {...}},
    "meta":   {"steps": [...], "errors": [...]}
  }
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.runtime.execute import execute


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_idea_to_brief"):
    """
    Transforme une idée en brief structuré.

    input_data : dict — doit contenir la clé "idea" (str)
    verbose    : bool — affiche les logs de progression

    Retourne un dict standardisé {status, from, to, data, meta}.
    Compatible avec le futur mécanisme idea.convert("brief").
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation de l'input ──────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    idea = val["idea"]
    if verbose:
        print(f"  [agent]   {agent_ident} — idea: {idea[:60]}{'...' if len(idea) > 60 else ''}")

    # ── Étape 2 — Génération du brief ─────────────────────────────────────────
    gen = _generate_brief(idea, verbose)
    meta["steps"].append(_step_record("generate_brief", gen["ok"], gen.get("error")))

    if not gen["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — generate_brief : {gen['error']}")
        meta["errors"].append(gen["error"])
        return _assemble_result("failure", None, meta)

    # ── Étape 3 — Normalisation de l'output ──────────────────────────────────
    norm = _normalize_output(gen["brief"])
    meta["steps"].append(_step_record("normalize_output", norm["ok"], norm.get("error")))

    if verbose:
        b = norm["brief"]
        print(f"  [OK]      {agent_ident} — {b['project_type']}:{b['project_name']} priority:{b['priority']}")

    # ── Étape 4 — Assemblage du résultat ─────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))
    return _assemble_result("success", norm["brief"], meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    """
    Vérifie que input_data contient une clé "idea" non vide.
    Retourne : {ok, idea, error}
    """
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}

    idea = input_data.get("idea", "")
    if not idea or not str(idea).strip():
        return {"ok": False, "error": "idea_missing_or_empty"}

    return {"ok": True, "idea": str(idea).strip()}


def _generate_brief(idea, verbose):
    """
    Appelle agent_brief via execute() et retourne le brief brut.
    Retourne : {ok, brief, error}
    """
    exc = execute("agent", "agent_brief", {"input_data": {"idea": idea}})
    if exc["status"] != "ok":
        return {"ok": False, "error": f"agent_brief_execute_failed:{exc['error']}"}

    result = exc["result"]
    if result.get("status") != "success" or not result.get("brief"):
        return {"ok": False, "error": f"agent_brief_failed:{result.get('reason', 'unknown')}"}

    return {"ok": True, "brief": result["brief"]}


def _normalize_output(brief):
    """
    Garantit que tous les champs attendus sont présents et bien typés.
    Complète les champs manquants avec des valeurs par défaut sûres.
    Retourne : {ok, brief}
    """
    _defaults = {
        "project_name":  "Unnamed Project",
        "project_type":  "tool",
        "description":   "",
        "target_users":  "general users",
        "core_features": [],
        "constraints":   {"tech": [], "ux": []},
        "monetization":  "freemium → paid tiers",
        "priority":      "medium",
    }

    normalized = {}
    for field, default in _defaults.items():
        value = brief.get(field, default)

        # Garanties de type
        if field == "core_features" and not isinstance(value, list):
            value = [str(value)] if value else []
        if field == "constraints" and not isinstance(value, dict):
            value = {"tech": [], "ux": []}
        if field in ("project_name", "project_type", "description",
                     "target_users", "monetization", "priority"):
            value = str(value).strip() if value else default

        normalized[field] = value

    return {"ok": True, "brief": normalized}


# ── Assemblage du résultat standardisé ───────────────────────────────────────

def _assemble_result(status, brief, meta):
    """
    Construit le retour standardisé.
    Structure compatible futur idea.convert("brief").
    """
    return {
        "status": status,
        "from":   "idea",
        "to":     "brief",
        "data":   {"brief": brief} if brief else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    """Trace d'une étape pour meta["steps"]."""
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    cases = [
        {
            "label": "✓ SaaS freelance invoicing",
            "input": {"idea": "create a SaaS that helps freelancers track invoices and payments"},
        },
        {
            "label": "✓ E-learning platform",
            "input": {"idea": "an e-learning platform where teachers publish courses and track student progress"},
        },
        {
            "label": "✓ Marketplace",
            "input": {"idea": "a marketplace connecting designers with clients looking for branding"},
        },
        {
            "label": "✗ idea vide",
            "input": {"idea": ""},
        },
        {
            "label": "✗ input invalide",
            "input": "not a dict",
        },
    ]

    print("=" * 65)
    print("  scenario_idea_to_brief — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{case['label']}")
        print(f"  status  : {r['status']}")
        print(f"  from→to : {r['from']} → {r['to']}")
        print(f"  steps   : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if ok:
            b = r["data"]["brief"]
            print(f"  name    : {b['project_name']}")
            print(f"  type    : {b['project_type']}")
            print(f"  users   : {b['target_users']}")
            print(f"  priority: {b['priority']}")
            print(f"  features: {b['core_features'][:2]}")
            passed += 1
        else:
            print(f"  errors  : {r['meta']['errors']}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
