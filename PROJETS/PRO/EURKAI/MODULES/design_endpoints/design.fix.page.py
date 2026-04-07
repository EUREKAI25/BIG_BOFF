"""
design.fix.page
Endpoint : applique un patch CSS correctif sur une page HTML depuis les résultats d'audit.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from auto_fix_engine.src.auto_fix_engine import AutoFixEngine
from vision_audit.src.vision_audit import AuditResult, AuditIssue

NAME     = "design.fix.page"
CATEGORY = "design"
OBJECT   = "fix"
ACTION   = "page"
VERSION  = "1.0.0"

INPUTS = {
    "html":           {"type": "str",       "required": True,  "description": "HTML depuis design.render.page output['html']"},
    "audit_results":  {"type": "list[dict]","required": True,  "description": "Résultats depuis design.audit.page output['results']"},
    "iteration":      {"type": "int",       "required": False, "description": "Itération courante (default: 1)"},
    "target_score":   {"type": "int",       "required": False, "description": "Score cible (default: 70)"},
}

OUTPUTS = {
    "html":         {"type": "str",        "description": "HTML corrigé avec patch CSS appliqué"},
    "converged":    {"type": "bool",       "description": "True si toutes les zones passent déjà"},
    "iteration":    {"type": "int",        "description": "Echo de l'itération"},
    "final_scores": {"type": "dict",       "description": "zone → global_score avant patch"},
    "patch_zones":  {"type": "list[str]",  "description": "Zones où un patch a été appliqué"},
}


def _reconstruct_audit_result(d: dict) -> AuditResult:
    """Reconstruit un AuditResult depuis un dict sérialisé."""
    issues = [
        AuditIssue(
            zone=i.get("zone", ""),
            problem=i.get("problem", ""),
            severity=i.get("severity", "medium"),
            confidence=float(i.get("confidence", 0.5)),
            suggested_fix=i.get("suggested_fix", ""),
        )
        for i in d.get("issues", [])
    ]
    return AuditResult(
        readability_pass=d.get("readability_pass", False),
        global_score=int(d.get("global_score", 0)),
        issues=issues,
        quick_fixes=d.get("quick_fixes", []),
        zone=d.get("zone", ""),
        viewport=d.get("viewport", "desktop"),
        image_path=d.get("image_path", ""),
    )


def run(
    html: str,
    audit_results: list[dict],
    iteration: int = 1,
    target_score: int = 70,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS

    Calcule et applique un patch correctif (1 passe).
    Pour la boucle complète, utiliser le scenario design.page.fix.
    """
    ar = [_reconstruct_audit_result(d) for d in audit_results]

    converged = all(r.readability_pass for r in ar)
    final_scores = {r.zone: r.global_score for r in ar}

    if converged:
        return {
            "html":         html,
            "converged":    True,
            "iteration":    iteration,
            "final_scores": final_scores,
            "patch_zones":  [],
        }

    engine = AutoFixEngine(max_iterations=3, target_score=target_score)
    patch, _log = engine.compute_patch(audit_results=ar, iteration=iteration)
    fixed_html  = engine.apply_patch(html, patch)

    return {
        "html":         fixed_html,
        "converged":    False,
        "iteration":    iteration,
        "final_scores": final_scores,
        "patch_zones":  list(patch.zones.keys()),
    }
