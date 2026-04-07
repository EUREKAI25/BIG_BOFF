"""
design.page.generate_basic
Scénario : brief → visual_intent → palette → plan → render

Pipeline minimal sans référence image.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_scenarios._ep_loader import load_endpoint

_ep_vi      = load_endpoint("design.visual_intent.generate")
_ep_palette = load_endpoint("design.palette.generate")
_ep_plan    = load_endpoint("design.plan.generate")
_ep_render  = load_endpoint("design.render.page")

NAME     = "design.page.generate_basic"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "generate_basic"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.visual_intent.generate"},
    {"order": 2, "endpoint": "design.palette.generate"},
    {"order": 3, "endpoint": "design.plan.generate"},
    {"order": 4, "endpoint": "design.render.page"},
]

INPUTS = {
    "brief":        {"type": "str", "required": True,  "description": "Brand/project description"},
    "project_name": {"type": "str", "required": True,  "description": "Brand/project name"},
    "seed":         {"type": "int", "required": False, "description": "Seed de rendu (default: 42)"},
    "site_family":  {"type": "str", "required": False, "description": "Famille de template"},
}

OUTPUTS = {
    "html":          {"type": "str",  "description": "HTML rendu"},
    "visual_intent": {"type": "dict", "description": "Visual intent généré"},
    "palette":       {"type": "dict", "description": "Palette couleurs générée"},
    "plan":          {"type": "dict", "description": "Design plan généré"},
    "trace":         {"type": "list", "description": "Trace d'exécution des étapes"},
}


def run(
    brief: str,
    project_name: str,
    seed: int = 42,
    site_family: str = "",
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    Retourne la trace complète d'exécution.
    """
    trace = []

    # Étape 1 — visual_intent
    vi = _ep_vi.run(brief=brief)
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Étape 2 — palette
    context = {"mode": "light", "name": project_name}
    palette = _ep_palette.run(visual_intent=vi, context=context)
    trace.append({"step": 2, "endpoint": "design.palette.generate", "ok": True})

    # Étape 3 — plan
    plan = _ep_plan.run(brief=brief, seed=seed, visual_intent=vi)
    trace.append({"step": 3, "endpoint": "design.plan.generate", "ok": True})

    # Étape 4 — render (Eurkai DOM Library)
    render = _ep_render.run(
        project_name=project_name,
        brief_text=brief,
        site_family=site_family,
        seed=seed,
        cp_palette=palette,
        visual_intent=vi,
        plan=plan,
    )
    trace.append({"step": 4, "endpoint": "design.render.page", "ok": True})

    return {
        "html":          render["html"],
        "visual_intent": vi,
        "palette":       palette,
        "plan":          plan,
        "trace":         trace,
    }
