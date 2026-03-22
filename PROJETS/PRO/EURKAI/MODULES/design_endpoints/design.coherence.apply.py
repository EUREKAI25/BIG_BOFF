"""
design.coherence.apply
Endpoint : applique les règles de cohérence visuelle (3 modes : image↔palette, design reference).
"""
from __future__ import annotations

import importlib.util as _ilu
from pathlib import Path

_ROOT   = Path(__file__).parents[2]
_VCE_PY = _ROOT / "MODULES" / "visual_coherence_engine" / "src" / "visual_coherence_engine.py"

_spec = _ilu.spec_from_file_location("_vce_core", _VCE_PY)
_mod  = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_fn = _mod.run

NAME     = "design.coherence.apply"
CATEGORY = "design"
OBJECT   = "coherence"
ACTION   = "apply"
VERSION  = "1.0.0"

INPUTS = {
    "visual_intent":  {"type": "dict",      "required": True,  "description": "From design.visual_intent.generate"},
    "context":        {"type": "dict",      "required": True,  "description": "{mode, name, family}"},
    "palette":        {"type": "dict|None", "required": False, "description": "From design.palette.generate — required for CASE 2"},
    "reference_image":{"type": "str|None",  "required": False, "description": "Path to image/screenshot/mockup"},
    "reference_type": {"type": "str",       "required": False, "description": "none | image | screenshot | mockup (default: none)"},
}

OUTPUTS = {
    "reference_mode":     {"type": "str",  "description": "image_drives_palette | palette_drives_image | design_reference_drives_plan"},
    "reference_type":     {"type": "str",  "description": "Echo of input reference_type"},
    "reference_analysis": {"type": "dict", "description": "Structural analysis (CASE 3 only): dominance, density, hierarchy, spacing, composition_bias, palette_hint"},
    "palette":            {"type": "dict", "description": "Final palette (extracted from image for CASE 1, input palette for CASE 2)"},
    "image_adjustments":  {"type": "dict", "description": "CSS adjustments: duotone, overlay_color, overlay_opacity, filter, blend_mode"},
    "readability_rules":  {"type": "dict", "description": "WCAG readability: text_on_image, min_overlay_for_wcag, gradient_scrim, recommended_text_color"},
    "conflicts":          {"type": "list", "description": "List of conflict strings (empty if ok)"},
}


def run(
    visual_intent: dict,
    context: dict,
    palette: dict | None = None,
    reference_image: str | None = None,
    reference_type: str = "none",
) -> dict:
    """
    CASE 1 — reference_type="image"       → image_drives_palette
    CASE 2 — reference_type="none"        → palette_drives_image
    CASE 3 — reference_type="screenshot"
             reference_type="mockup"      → design_reference_drives_plan

    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS
    """
    return _fn(
        visual_intent=visual_intent,
        context=context,
        palette=palette,
        reference_image=reference_image,
        reference_type=reference_type,
    )
