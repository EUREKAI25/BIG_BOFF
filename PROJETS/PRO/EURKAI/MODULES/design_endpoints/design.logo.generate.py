"""
design.logo.generate — EURKAI Design Endpoint
Catégorie : design | Objet : logo | Action : generate

Génère uniquement la section logo (type + style + construction + variations + generation_prompt + svg_spec).
"""
from __future__ import annotations

import sys
from pathlib import Path

import importlib.util as _ilu

_ROOT   = Path(__file__).parents[2]
_BI_PY  = _ROOT / "MODULES" / "brand_identity" / "src" / "brand_identity.py"

_spec = _ilu.spec_from_file_location("_brand_identity_core", _BI_PY)
_mod  = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
generate_brand_identity = _mod.generate_brand_identity

# ── Metadata ──────────────────────────────────────────────────────────────────

NAME     = "design.logo.generate"
CATEGORY = "design"
OBJECT   = "logo"
ACTION   = "generate"
VERSION  = "1.0.0"

INPUTS: dict = {
    "brief":         {"type": "str",       "required": True,  "description": "Brand/project description"},
    "visual_intent": {"type": "dict",      "required": True,  "description": "From design.visual_intent.generate"},
    "palette":       {"type": "dict",      "required": True,  "description": "From design.palette.generate"},
    "context":       {"type": "dict",      "required": True,  "description": "{name, mode, family, ...}"},
    "reference":     {"type": "dict|None", "required": False, "description": "reference_analysis from CASE 3"},
}

OUTPUTS: dict = {
    "type":              {"type": "str",  "description": "symbol | logotype | combination"},
    "style":             {"type": "str",  "description": "Style descriptor"},
    "construction":      {"type": "str",  "description": "Construction instructions"},
    "variations":        {"type": "list", "description": "light, dark, icon_only, ..."},
    "generation_prompt": {"type": "str",  "description": "Recraft/SD-compatible generation prompt"},
    "svg_spec":          {"type": "dict", "description": "shape, rotation, style, primary_color, background, viewport"},
}


# ── Endpoint ──────────────────────────────────────────────────────────────────

def run(
    brief: str,
    visual_intent: dict,
    palette: dict,
    context: dict,
    reference: dict | None = None,
) -> dict:
    """
    Génère uniquement la section logo du système d'identité.

    Returns:
        dict — logo complet avec generation_prompt et svg_spec
    """
    bi = generate_brand_identity(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=context,
        reference=reference,
    )
    return bi["logo"]
