"""
brand_generator.direction_builder
───────────────────────────────────
Construit le prompt LLM pour générer 3 directions créatives distinctes.
Parse la réponse JSON du LLM en objets BrandDirection.

Le prompt injecte :
- Le contexte créatif (CreativeContext)
- Les axes de contraste attendus entre les 3 directions
- Le schéma JSON attendu en sortie
- Les valeurs autorisées pour chaque champ enum
"""

from __future__ import annotations
import json
import re
from typing import Optional

from .analyzer import CreativeContext
from .schemas import BrandDirection, PaletteProfile, TypographyProfile, LogoStructure


# ─── Valeurs autorisées (guide le LLM) ───────────────────────────────────────

_ALLOWED_VALUES = {
    "palette_type":        ["monochromatic", "complementary", "triadic", "analogous", "neutral", "duotone", "split_complementary"],
    "saturation_level":    ["low", "medium", "high", "vivid"],
    "contrast_level":      ["low", "medium", "high", "extreme"],
    "motion_energy":       ["none", "subtle", "moderate", "dynamic"],
    "layout_density":      ["compact", "comfortable", "spacious"],
    "whitespace_level":    ["minimal", "medium", "generous"],
    "grid_style":          ["strict", "standard", "fluid", "asymmetric"],
    "component_roundness": ["sharp", "medium", "rounded", "pill"],
    "logo_structure":      [e.value for e in LogoStructure],
    "icon_complexity":     ["minimal", "moderate", "expressive", "detailed"],
    "weight_range":        ["light to medium", "light to bold", "regular to bold", "bold only", "variable"],
    "optical_size":        ["compact", "standard", "display"],
}


# ─── Construction du prompt ───────────────────────────────────────────────────

def build_prompt(ctx: CreativeContext) -> str:
    constraints_block = "\n".join(f"- {c}" for c in ctx.constraints) if ctx.constraints else "- none"
    axes_block = "\n".join(f"- Direction {chr(65+i)}: {ax}" for i, ax in enumerate(ctx.contrast_axes[:3]))

    allowed_block = "\n".join(
        f'  "{k}": one of {json.dumps(v)}'
        for k, v in _ALLOWED_VALUES.items()
    )

    sector_line   = f"Sector: {ctx.sector}" if ctx.sector else ""
    audience_line = f"Target audience: {ctx.audience}" if ctx.audience else ""
    position_line = f"Positioning: {ctx.positioning}" if ctx.positioning else ""

    return f"""You are a senior brand strategist and creative director.

Generate exactly 3 brand creative directions for the following project.
Each direction must be visually and stylistically DISTINCT from the others.
Each direction must be INTERNALLY COHERENT and directly usable by downstream design modules.

---
BRAND: {ctx.brand_name}
{sector_line}
{audience_line}
{position_line}

BRIEF:
{ctx.brief_summary}

EXISTING BRAND CONSTRAINTS:
{constraints_block}

CONTRAST AXES TO APPLY:
{axes_block}

---
RULES:
- The 3 directions must differ clearly in: typography personality, color palette type, icon style, composition, visual energy.
- Each direction must be self-consistent — all fields should feel like a unified visual system.
- Do NOT repeat style_tags or mood_keywords across directions.
- logo_structure must be different across directions when possible.
- component_roundness and composition_style must contrast across directions.

ALLOWED VALUES FOR ENUM FIELDS:
{allowed_block}

---
Return a valid JSON object with exactly this structure. No markdown, no explanation, just JSON:

{{
  "direction_A": {{
    "name": "...",
    "description": "...",
    "design_intent": "...",
    "style_tags": ["...", "...", "..."],
    "mood_keywords": ["...", "...", "..."],
    "palette_profile": {{
      "palette_type": "...",
      "dominant_hue": "...",
      "saturation_level": "...",
      "contrast_level": "...",
      "mood": "..."
    }},
    "typography_profile": {{
      "personality": "...",
      "primary_font_style": "...",
      "secondary_font_style": "...",
      "weight_range": "...",
      "optical_size": "..."
    }},
    "icon_style": "...",
    "illustration_style": "...",
    "image_style": "...",
    "composition_style": "...",
    "motion_energy": "...",
    "logo_structure": "...",
    "symbol_preference": "...",
    "wordmark_weight": "...",
    "icon_complexity": "...",
    "layout_density": "...",
    "whitespace_level": "...",
    "grid_style": "...",
    "component_roundness": "...",
    "contrast_level": "..."
  }},
  "direction_B": {{ ... }},
  "direction_C": {{ ... }}
}}
"""


# ─── Parse de la réponse LLM ──────────────────────────────────────────────────

def _parse_direction(data: dict) -> BrandDirection:
    pp_data = data.get("palette_profile") or {}
    tp_data = data.get("typography_profile") or {}

    palette_profile = PaletteProfile(
        palette_type=pp_data.get("palette_type", "neutral"),
        dominant_hue=pp_data.get("dominant_hue"),
        saturation_level=pp_data.get("saturation_level", "medium"),
        contrast_level=pp_data.get("contrast_level", "medium"),
        mood=pp_data.get("mood"),
    ) if pp_data else None

    typography_profile = TypographyProfile(
        personality=tp_data.get("personality", "sans-serif"),
        primary_font_style=tp_data.get("primary_font_style", "sans-serif"),
        secondary_font_style=tp_data.get("secondary_font_style"),
        weight_range=tp_data.get("weight_range", "regular to bold"),
        optical_size=tp_data.get("optical_size", "standard"),
    ) if tp_data else None

    # logo_structure : valider et convertir en enum
    logo_structure_raw = data.get("logo_structure")
    logo_structure: Optional[LogoStructure] = None
    if logo_structure_raw:
        try:
            logo_structure = LogoStructure(logo_structure_raw)
        except ValueError:
            logo_structure = None

    return BrandDirection(
        name=data.get("name", "Unnamed direction"),
        description=data.get("description", ""),
        design_intent=data.get("design_intent", ""),
        style_tags=data.get("style_tags", []),
        mood_keywords=data.get("mood_keywords", []),
        palette_profile=palette_profile,
        typography_profile=typography_profile,
        icon_style=data.get("icon_style", "minimal"),
        illustration_style=data.get("illustration_style"),
        image_style=data.get("image_style"),
        composition_style=data.get("composition_style", "balanced"),
        motion_energy=data.get("motion_energy", "subtle"),
        logo_structure=logo_structure,
        symbol_preference=data.get("symbol_preference"),
        wordmark_weight=data.get("wordmark_weight"),
        icon_complexity=data.get("icon_complexity", "minimal"),
        layout_density=data.get("layout_density", "comfortable"),
        whitespace_level=data.get("whitespace_level", "medium"),
        grid_style=data.get("grid_style", "standard"),
        component_roundness=data.get("component_roundness", "medium"),
        contrast_level=data.get("contrast_level", "medium"),
    )


def parse_llm_response(raw: str) -> tuple[BrandDirection, BrandDirection, BrandDirection]:
    """
    Parse la réponse JSON du LLM.
    Extrait les 3 directions et les convertit en BrandDirection.
    Lève ValueError si le JSON est invalide ou incomplet.
    """
    # Extraire le JSON même si le LLM a ajouté du texte autour
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if not json_match:
        raise ValueError("Aucun JSON trouvé dans la réponse LLM.")

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide dans la réponse LLM : {e}") from e

    missing = [k for k in ("direction_A", "direction_B", "direction_C") if k not in data]
    if missing:
        raise ValueError(f"Directions manquantes dans la réponse : {missing}")

    return (
        _parse_direction(data["direction_A"]),
        _parse_direction(data["direction_B"]),
        _parse_direction(data["direction_C"]),
    )
