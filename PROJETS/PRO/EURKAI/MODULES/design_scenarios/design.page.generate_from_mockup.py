"""
design.page.generate_from_mockup
Scénario : brief + mockup/screenshot → visual_intent → palette → coherence (CASE 3) → plan → render

La référence design pilote la structure du plan (design_reference_drives_plan).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from design_scenarios._ep_loader import load_endpoint

_ep_vi        = load_endpoint("design.visual_intent.generate")
_ep_palette   = load_endpoint("design.palette.generate")
_ep_coherence = load_endpoint("design.coherence.apply")
_ep_plan      = load_endpoint("design.plan.generate")
_ep_render    = load_endpoint("design.render.page")

NAME     = "design.page.generate_from_mockup"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "generate_from_mockup"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.visual_intent.generate"},
    {"order": 2, "endpoint": "design.palette.generate"},
    {"order": 3, "endpoint": "design.coherence.apply",   "note": "CASE 3 — design_reference_drives_plan"},
    {"order": 4, "endpoint": "design.plan.generate",     "note": "reference_analysis appliqué en hard overrides"},
    {"order": 5, "endpoint": "design.render.page"},
]

INPUTS = {
    "brief":           {"type": "str", "required": True,  "description": "Brand/project description"},
    "project_name":    {"type": "str", "required": True,  "description": "Brand/project name"},
    "reference_image": {"type": "str", "required": True,  "description": "Chemin vers mockup ou screenshot de référence"},
    "reference_type":  {"type": "str", "required": False, "description": "mockup | screenshot (default: mockup)"},
    "seed":            {"type": "int", "required": False, "description": "Seed de rendu (default: 42)"},
    "site_family":     {"type": "str", "required": False, "description": "Famille de template"},
}

OUTPUTS = {
    "html":             {"type": "str",  "description": "HTML rendu"},
    "visual_intent":    {"type": "dict", "description": "Visual intent généré"},
    "palette":          {"type": "dict", "description": "Palette couleurs"},
    "coherence":        {"type": "dict", "description": "Résultat cohérence — reference_mode=design_reference_drives_plan"},
    "reference_analysis":{"type": "dict","description": "Analyse structurelle extraite de la référence"},
    "plan":             {"type": "dict", "description": "Design plan avec overrides de la référence"},
    "trace":            {"type": "list", "description": "Trace d'exécution des étapes"},
}


def run(
    brief: str,
    project_name: str,
    reference_image: str,
    reference_type: str = "mockup",
    seed: int = 42,
    site_family: str = "",
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    trace   = []
    context = {"mode": "light", "name": project_name}

    # Étape 1 — visual_intent
    vi = _ep_vi.run(brief=brief)
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Étape 2 — palette
    palette = _ep_palette.run(visual_intent=vi, context=context)
    trace.append({"step": 2, "endpoint": "design.palette.generate", "ok": True})

    # Étape 3 — coherence CASE 3 : design reference → reference_analysis
    coherence = _ep_coherence.run(
        visual_intent=vi,
        context=context,
        palette=palette,
        reference_image=reference_image,
        reference_type=reference_type,
    )
    reference_analysis = coherence.get("reference_analysis", {})
    trace.append({
        "step": 3, "endpoint": "design.coherence.apply", "ok": True,
        "reference_mode":   coherence.get("reference_mode"),
        "reference_source": reference_analysis.get("_source"),
        "conflicts":        coherence.get("conflicts", []),
    })

    # Étape 4 — plan (reference_analysis = hard overrides sur profile/density/tension)
    plan = _ep_plan.run(
        brief=brief,
        seed=seed,
        visual_intent=vi,
        reference_analysis=reference_analysis if reference_analysis else None,
    )
    trace.append({"step": 4, "endpoint": "design.plan.generate", "ok": True})

    # Étape 5 — render (Eurkai DOM Library)
    render = _ep_render.run(
        project_name=project_name,
        brief_text=brief,
        site_family=site_family,
        seed=seed,
        cp_palette=coherence.get("palette"),
        visual_intent=vi,
        plan=plan,
    )
    trace.append({"step": 5, "endpoint": "design.render.page", "ok": True})

    return {
        "html":              render["html"],
        "visual_intent":     vi,
        "palette":           coherence.get("palette"),
        "coherence":         coherence,
        "reference_analysis": reference_analysis,
        "plan":              plan,
        "trace":             trace,
    }
