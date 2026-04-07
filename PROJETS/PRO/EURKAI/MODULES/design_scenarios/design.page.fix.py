"""
design.page.fix
Scénario : html + audit_results → fix (boucle) → HTML corrigé

Boucle de correction jusqu'à convergence ou max_iterations.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_scenarios._ep_loader import load_endpoint

_ep_fix = load_endpoint("design.fix.page")

NAME     = "design.page.fix"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "fix"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.fix.page", "note": "Répété jusqu'à convergence ou max_iterations"},
]

INPUTS = {
    "html":           {"type": "str",        "required": True,  "description": "HTML depuis design.render.page"},
    "audit_results":  {"type": "list[dict]", "required": True,  "description": "Résultats depuis design.audit.page output['results']"},
    "max_iterations": {"type": "int",        "required": False, "description": "Max itérations (default: 3)"},
    "target_score":   {"type": "int",        "required": False, "description": "Score cible (default: 70)"},
}

OUTPUTS = {
    "html":           {"type": "str",  "description": "HTML final corrigé"},
    "converged":      {"type": "bool", "description": "True si convergence atteinte"},
    "iterations_run": {"type": "int",  "description": "Nombre d'itérations exécutées"},
    "final_scores":   {"type": "dict", "description": "zone → score final"},
    "trace":          {"type": "list", "description": "Trace d'exécution"},
}


def run(
    html: str,
    audit_results: list[dict],
    max_iterations: int = 3,
    target_score: int = 70,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS

    Exécute design.fix.page en boucle jusqu'à :
    - convergence (toutes zones passent), ou
    - max_iterations atteint
    """
    trace         = []
    current_html  = html
    current_audit = audit_results
    converged     = False
    final_scores  = {}

    for i in range(1, max_iterations + 1):
        result = _ep_fix.run(
            html=current_html,
            audit_results=current_audit,
            iteration=i,
            target_score=target_score,
        )
        trace.append({
            "step":         i,
            "endpoint":     "design.fix.page",
            "ok":           True,
            "converged":    result["converged"],
            "patch_zones":  result["patch_zones"],
            "final_scores": result["final_scores"],
        })

        current_html = result["html"]
        final_scores = result["final_scores"]

        if result["converged"]:
            converged = True
            break

        # Si aucun patch appliqué, impossible de progresser
        if not result["patch_zones"]:
            break

    return {
        "html":           current_html,
        "converged":      converged,
        "iterations_run": len(trace),
        "final_scores":   final_scores,
        "trace":          trace,
    }
