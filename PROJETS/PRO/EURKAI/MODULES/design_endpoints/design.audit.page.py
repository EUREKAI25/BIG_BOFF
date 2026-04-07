"""
design.audit.page
Endpoint : audite la lisibilité d'une page via vision API (Anthropic Haiku).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from vision_audit.src.vision_audit import audit_page as _fn, summarize_results

NAME     = "design.audit.page"
CATEGORY = "design"
OBJECT   = "audit"
ACTION   = "page"
VERSION  = "1.0.0"

INPUTS = {
    "captures": {"type": "list[dict]", "required": True,  "description": "From design.capture.page output['captures']"},
    "api_key":  {"type": "str|None",   "required": False, "description": "Anthropic API key (uses env ANTHROPIC_API_KEY if None)"},
}

OUTPUTS = {
    "results": {"type": "list[dict]", "description": "AuditResult par zone: readability_pass, global_score, issues, quick_fixes, zone, viewport, image_path"},
    "summary": {"type": "dict",       "description": "Résumé: pass, fail, avg_score, total, high_issues"},
    "pass":    {"type": "bool",       "description": "True si toutes les zones passent"},
    "score":   {"type": "int",        "description": "Score moyen global (0–100)"},
}


def run(
    captures: list[dict],
    api_key: str | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS

    Nécessite une clé API Anthropic valide.
    Seuil de passage : score ≥ 70.
    """
    results = _fn(captures=captures, api_key=api_key)
    summary = summarize_results(results)
    return {
        "results": [r.to_dict() for r in results],
        "summary": summary,
        "pass":    summary.get("fail", 0) == 0,
        "score":   summary.get("avg_score", 0),
    }
