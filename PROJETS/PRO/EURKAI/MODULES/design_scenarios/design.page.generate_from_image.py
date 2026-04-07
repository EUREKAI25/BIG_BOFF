"""
design.page.generate_from_image
Scénario : image → coherence (CASE 1) → visual_intent → plan → render

L'image de référence pilote la palette (image_drives_palette).
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
_ep_coherence = load_endpoint("design.coherence.apply")
_ep_plan      = load_endpoint("design.plan.generate")
_ep_render    = load_endpoint("design.render.page")

NAME     = "design.page.generate_from_image"
CATEGORY = "design"
OBJECT   = "page"
ACTION   = "generate_from_image"
VERSION  = "1.0.0"

STEPS = [
    {"order": 1, "endpoint": "design.visual_intent.generate"},
    {"order": 2, "endpoint": "design.coherence.apply",       "note": "CASE 1 — image_drives_palette"},
    {"order": 3, "endpoint": "design.plan.generate"},
    {"order": 4, "endpoint": "design.render.page"},
]

INPUTS = {
    "brief":           {"type": "str", "required": True,  "description": "Brand/project description"},
    "project_name":    {"type": "str", "required": True,  "description": "Brand/project name"},
    "reference_image": {"type": "str", "required": True,  "description": "Chemin vers l'image de référence"},
    "seed":            {"type": "int", "required": False, "description": "Seed de rendu (default: 42)"},
    "site_family":     {"type": "str", "required": False, "description": "Famille de template"},
}

OUTPUTS = {
    "html":          {"type": "str",  "description": "HTML rendu"},
    "visual_intent": {"type": "dict", "description": "Visual intent généré"},
    "coherence":     {"type": "dict", "description": "Résultat cohérence — reference_mode=image_drives_palette"},
    "plan":          {"type": "dict", "description": "Design plan généré"},
    "trace":         {"type": "list", "description": "Trace d'exécution des étapes"},
}


def run(
    brief: str,
    project_name: str,
    reference_image: str,
    seed: int = 42,
    site_family: str = "",
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    trace   = []
    context = {"mode": "light", "name": project_name}

    # Étape 1 — visual_intent (avec signal image)
    vi = _ep_vi.run(brief=brief, reference_image=reference_image, reference_type="image")
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Étape 2 — coherence CASE 1 : image → palette
    coherence = _ep_coherence.run(
        visual_intent=vi,
        context=context,
        reference_image=reference_image,
        reference_type="image",
    )
    trace.append({
        "step": 2, "endpoint": "design.coherence.apply", "ok": True,
        "reference_mode": coherence.get("reference_mode"),
    })

    # Étape 3 — plan
    plan = _ep_plan.run(brief=brief, seed=seed, visual_intent=vi)
    trace.append({"step": 3, "endpoint": "design.plan.generate", "ok": True})

    # Étape 4 — render (Eurkai DOM Library)
    render = _ep_render.run(
        project_name=project_name,
        brief_text=brief,
        site_family=site_family,
        seed=seed,
        cp_palette=coherence.get("palette"),
        visual_intent=vi,
        plan=plan,
    )
    trace.append({"step": 4, "endpoint": "design.render.page", "ok": True})

    return {
        "html":          render["html"],
        "visual_intent": vi,
        "coherence":     coherence,
        "plan":          plan,
        "trace":         trace,
    }
