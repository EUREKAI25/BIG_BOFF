"""
design.page.audit
Scénario : url → capture → audit

Audite une page déjà servie (URL locale ou distante).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_scenarios._ep_loader import load_endpoint

_ep_capture = load_endpoint("design.capture.page")
_ep_audit   = load_endpoint("design.audit.page")

NAME     = "design.page.audit"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "audit"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.capture.page", "note": "Requiert Playwright"},
    {"order": 2, "endpoint": "design.audit.page",   "note": "Requiert API Anthropic"},
]

INPUTS = {
    "url":         {"type": "str",       "required": True,  "description": "URL de la page à auditer"},
    "site":        {"type": "str",       "required": True,  "description": "Identifiant site"},
    "page":        {"type": "str",       "required": False, "description": "Identifiant page (default: audit)"},
    "output_root": {"type": "str",       "required": False, "description": "Répertoire captures"},
    "viewport":    {"type": "str",       "required": False, "description": "desktop | tablet | mobile"},
    "zones":       {"type": "list|None", "required": False, "description": "Zones à capturer (None = toutes)"},
    "api_key":     {"type": "str|None",  "required": False, "description": "Clé API Anthropic"},
}

OUTPUTS = {
    "captures": {"type": "list", "description": "Captures screenshots"},
    "audit":    {"type": "dict", "description": "Résultat audit: results, summary, pass, score"},
    "trace":    {"type": "list", "description": "Trace d'exécution"},
}


def run(
    url: str,
    site: str,
    page: str = "audit",
    output_root: str = "output/captures",
    viewport: str = "desktop",
    zones: list[str] | None = None,
    api_key: str | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    trace = []

    # Étape 1 — capture
    captures_result = _ep_capture.run(
        url=url, site=site, page=page,
        output_root=output_root, viewport=viewport, zones=zones,
    )
    trace.append({
        "step": 1, "endpoint": "design.capture.page", "ok": True,
        "ok_count": captures_result["ok_count"],
        "fail_count": captures_result["fail_count"],
    })

    # Étape 2 — audit
    audit_result = _ep_audit.run(
        captures=captures_result["captures"],
        api_key=api_key,
    )
    trace.append({
        "step": 2, "endpoint": "design.audit.page", "ok": True,
        "score": audit_result["score"],
        "pass":  audit_result["pass"],
    })

    return {
        "captures": captures_result["captures"],
        "audit":    audit_result,
        "trace":    trace,
    }
