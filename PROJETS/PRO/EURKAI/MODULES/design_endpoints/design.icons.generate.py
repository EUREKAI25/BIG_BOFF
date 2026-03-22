"""
design.icons.generate — EURKAI Design Endpoint
Catégorie : design | Objet : icons | Action : generate

Génère uniquement le système d'icônes (style + stroke + corner_style + consistency_rules + generation_prompt + examples).
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

NAME     = "design.icons.generate"
CATEGORY = "design"
OBJECT   = "icons"
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
    "style":             {"type": "str",       "description": "filled | line | filled soft | ..."},
    "stroke":            {"type": "str",       "description": "none | 1px | 1.5px | 2px"},
    "corner_style":      {"type": "str",       "description": "sharp | slightly rounded | fully rounded"},
    "consistency_rules": {"type": "list[str]", "description": "Règles d'application pour le set d'icônes"},
    "generation_prompt": {"type": "str",       "description": "Prompt de génération pour Recraft/SD"},
    "examples":          {"type": "list[str]", "description": "Exemples d'icônes contextuelles"},
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
    Génère uniquement le système d'icônes de l'identité.

    Returns:
        dict — icons avec consistency_rules, generation_prompt, examples
    """
    bi = generate_brand_identity(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=context,
        reference=reference,
    )
    return bi["icons"]
