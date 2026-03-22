"""
design.brand.generate_from_reference — EURKAI Design Scenario
Scénario : brand identity depuis brief + mockup/screenshot de référence (CASE 3).

Pipeline :
    1. design.visual_intent.generate
    2. design.palette.generate
    3. design.coherence.apply (CASE 3 — design_reference_drives_plan)
    4. design.brand.generate  (avec reference_analysis overrides)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[3]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _ep_loader import load_endpoint  # noqa

# ── Metadata ──────────────────────────────────────────────────────────────────

NAME    = "design.brand.generate_from_reference"
VERSION = "1.0.0"

STEPS: list[dict] = [
    {"step": 1, "endpoint": "design.visual_intent.generate",
     "description": "Générer le visual intent depuis le brief"},
    {"step": 2, "endpoint": "design.palette.generate",
     "description": "Générer la palette couleur"},
    {"step": 3, "endpoint": "design.coherence.apply",
     "description": "Analyser la référence (CASE 3 — design_reference_drives_plan)"},
    {"step": 4, "endpoint": "design.brand.generate",
     "description": "Générer l'identité avec overrides depuis la reference_analysis"},
]

INPUTS: dict = {
    "brief":            {"type": "str", "required": True,  "description": "Brand/project description"},
    "context":          {"type": "dict","required": True,  "description": "{name, mode, family, ...}"},
    "reference_image":  {"type": "str", "required": True,  "description": "Chemin vers mockup ou screenshot"},
    "reference_type":   {"type": "str", "required": False, "description": "mockup | screenshot (default: mockup)"},
}

OUTPUTS: dict = {
    "brand_identity":    {"type": "dict", "description": "Identité complète avec overrides de référence"},
    "visual_intent":     {"type": "dict", "description": "Visual intent"},
    "palette":           {"type": "dict", "description": "Palette"},
    "coherence":         {"type": "dict", "description": "Cohérence + reference_analysis"},
    "reference_analysis":{"type": "dict", "description": "dominance, density, hierarchy, spacing..."},
    "reference_mode":    {"type": "str",  "description": "Toujours design_reference_drives_plan"},
    "trace":             {"type": "list", "description": "Trace d'exécution"},
}

# ── Lazy load ──────────────────────────────────────────────────────────────────

_ep_vi    = None
_ep_pal   = None
_ep_coh   = None
_ep_brand = None


def _get_eps():
    global _ep_vi, _ep_pal, _ep_coh, _ep_brand
    if _ep_vi is None:
        _ep_vi    = load_endpoint("design.visual_intent.generate")
        _ep_pal   = load_endpoint("design.palette.generate")
        _ep_coh   = load_endpoint("design.coherence.apply")
        _ep_brand = load_endpoint("design.brand.generate")
    return _ep_vi, _ep_pal, _ep_coh, _ep_brand


# ── Scenario ──────────────────────────────────────────────────────────────────

def run(
    brief: str,
    context: dict,
    reference_image: str,
    reference_type: str = "mockup",
) -> dict:
    """
    Pipeline brand identity avec référence mockup/screenshot.

    CASE 3 — design_reference_drives_plan :
    La référence analyse la structure (dominance/density/hierarchy/spacing)
    et adapte l'identité visuelle SANS copier le style source.

    Args:
        brief          : str  — description de la marque
        context        : dict — {name, mode, family, ...}
        reference_image: str  — chemin vers mockup ou screenshot
        reference_type : str  — mockup | screenshot (default: mockup)

    Returns:
        dict — brand_identity, visual_intent, palette, coherence, reference_analysis, trace
    """
    ep_vi, ep_pal, ep_coh, ep_brand = _get_eps()
    trace: list[dict] = []
    ctx = dict(context)

    # Step 1 — visual_intent
    visual_intent = ep_vi.run(brief=brief)
    trace.append({"step": 1, "endpoint": "design.visual_intent.generate", "ok": True})

    # Step 2 — palette
    palette = ep_pal.run(visual_intent=visual_intent, context=ctx)
    trace.append({"step": 2, "endpoint": "design.palette.generate", "ok": True})

    # Step 3 — coherence CASE 3 (reference_type = mockup → design_reference_drives_plan)
    coherence = ep_coh.run(
        visual_intent=visual_intent,
        context=ctx,
        palette=palette,
        reference_image=reference_image,
        reference_type=reference_type,
    )
    reference_analysis = coherence.get("reference_analysis", {})
    trace.append({
        "step": 3,
        "endpoint": "design.coherence.apply",
        "reference_mode": coherence.get("reference_mode", "design_reference_drives_plan"),
        "ok": True,
    })

    # Step 4 — brand identity avec reference_analysis overrides
    brand_identity = ep_brand.run(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=ctx,
        reference=reference_analysis,
    )
    trace.append({"step": 4, "endpoint": "design.brand.generate", "ok": True})

    return {
        "brand_identity":    brand_identity,
        "visual_intent":     visual_intent,
        "palette":           palette,
        "coherence":         coherence,
        "reference_analysis":reference_analysis,
        "reference_mode":    coherence.get("reference_mode", "design_reference_drives_plan"),
        "trace":             trace,
    }
