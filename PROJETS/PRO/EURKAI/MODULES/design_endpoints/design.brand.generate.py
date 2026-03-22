"""
design.brand.generate — EURKAI Design Endpoint
Catégorie : design | Objet : brand | Action : generate

Génère un système d'identité visuelle complet (brand_core + logo + icons + typography + visual_signature)
depuis brief + visual_intent + palette + context.
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

NAME     = "design.brand.generate"
CATEGORY = "design"
OBJECT   = "brand"
ACTION   = "generate"
VERSION  = "1.0.0"

INPUTS: dict = {
    "brief":         {"type": "str",       "required": True,  "description": "Brand/project description"},
    "visual_intent": {"type": "dict",      "required": True,  "description": "From design.visual_intent.generate"},
    "palette":       {"type": "dict",      "required": True,  "description": "From design.palette.generate"},
    "context":       {"type": "dict",      "required": True,  "description": "{name, mode, family, product_type, ...}"},
    "reference":     {"type": "dict|None", "required": False, "description": "reference_analysis from design.coherence.apply (CASE 3)"},
}

OUTPUTS: dict = {
    "brand_core":       {"type": "dict", "description": "name, tone, personality, positioning"},
    "logo":             {"type": "dict", "description": "type, style, construction, variations, generation_prompt, svg_spec"},
    "icons":            {"type": "dict", "description": "style, stroke, corner_style, consistency_rules, generation_prompt, examples"},
    "typography":       {"type": "dict", "description": "primary_font, secondary_font, fallbacks, style, pairing_logic"},
    "visual_signature": {"type": "dict", "description": "motifs, borders, patterns, composition_rules"},
    "_meta":            {"type": "dict", "description": "context_key, version, generated_at"},
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
    Génère un système d'identité visuelle complet.

    Returns:
        dict — brand_core, logo, icons, typography, visual_signature, _meta
    """
    return generate_brand_identity(
        brief=brief,
        visual_intent=visual_intent,
        palette=palette,
        context=context,
        reference=reference,
    )
