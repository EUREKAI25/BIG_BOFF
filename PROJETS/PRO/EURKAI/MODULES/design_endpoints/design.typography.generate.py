"""
design.typography.generate — EURKAI Design Endpoint
Catégorie : design | Objet : typography | Action : generate

Génère uniquement le système typographique (primary_font + secondary_font + fallbacks + style + pairing_logic).
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

NAME     = "design.typography.generate"
CATEGORY = "design"
OBJECT   = "typography"
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
    "primary_font":         {"type": "str",  "description": "Police d'affichage principale"},
    "secondary_font":       {"type": "str",  "description": "Police de corps de texte"},
    "fallbacks":            {"type": "list", "description": "Polices de substitution système"},
    "style":                {"type": "str",  "description": "Descripteur du style typographique"},
    "pairing_logic":        {"type": "str",  "description": "Logique d'association des polices"},
    "custom_font_possible": {"type": "bool", "description": "True si une police custom est recommandée"},
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
    Génère uniquement le système typographique de l'identité.

    Returns:
        dict — typography avec primary_font, secondary_font, fallbacks, style, pairing_logic
    """
    bi = generate_brand_identity(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=context,
        reference=reference,
    )
    return bi["typography"]
