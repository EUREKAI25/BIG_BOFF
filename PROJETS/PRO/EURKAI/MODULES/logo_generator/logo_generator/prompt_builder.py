"""
logo_generator.prompt_builder
──────────────────────────────
Construit les prompts Recraft v3 à partir d'un LogoDNA + LogoStructure.
Les règles de composition par structure sont intégrées directement dans les prompts.
"""

from __future__ import annotations
from typing import List

from .schemas import LogoDNA, LogoStructure, BackgroundMode


# ─── Règles de composition par structure ──────────────────────────────────────

# Chaque structure définit :
#   base    : fragment de description de composition (injecté dans le prompt)
#   rules   : règles spécifiques intégrées dans le prompt
#   variants: quelles variantes ont du sens (guide exporter, pas contrainte rigide)

STRUCTURE_RULES: dict[LogoStructure, dict] = {
    LogoStructure.WORDMARK: {
        "base": "wordmark logo, text-only, distinctive typography",
        "rules": "focus on letterforms, strong kerning, ligatures, no icon or symbol",
        "variants_hint": "logo, logo_horizontal, logo_monochrome, favicon",
    },
    LogoStructure.MONOGRAM: {
        "base": "monogram logo, letter combination symbol",
        "rules": "geometric letter construction, balanced letter spacing, simple scalable symbol, initials-based",
        "variants_hint": "logo, logo_icon, logo_monochrome, favicon",
    },
    LogoStructure.ICON_WORDMARK: {
        "base": "combination logo, icon + wordmark",
        "rules": "icon left of or above wordmark, spacing proportional to cap height, icon visually aligned with text",
        "variants_hint": "logo, logo_horizontal, logo_icon, logo_monochrome, favicon",
    },
    LogoStructure.EMBLEM: {
        "base": "emblem logo, text inside symbol or shape",
        "rules": "circular or shield structure, integrated typography inside the shape, strong visual container",
        "variants_hint": "logo, logo_monochrome, favicon",
    },
    LogoStructure.BADGE: {
        "base": "badge logo, contained inside decorative shape",
        "rules": "strong outer frame, internal text hierarchy, balanced symmetry, decorative border",
        "variants_hint": "logo, logo_monochrome, favicon",
    },
    LogoStructure.MASCOT: {
        "base": "mascot logo, character or illustrated symbol",
        "rules": "expressive character illustration, playful shapes, optional wordmark below or beside",
        "variants_hint": "logo, logo_icon, logo_monochrome, favicon",
    },
    LogoStructure.ABSTRACT_SYMBOL: {
        "base": "abstract symbol logo, geometric mark",
        "rules": "minimal abstract symbol, strong geometric identity, highly scalable, no literal representation",
        "variants_hint": "logo, logo_icon, logo_monochrome, favicon",
    },
    LogoStructure.STACKED: {
        "base": "stacked logo, text elements stacked vertically",
        "rules": "centered alignment, strong vertical rhythm, typography-driven, elements stacked on multiple lines",
        "variants_hint": "logo, logo_monochrome, favicon",
    },
    LogoStructure.LETTERMARK: {
        "base": "lettermark logo, single stylized letter",
        "rules": "single letter highly stylized, optimized for small sizes and favicon, bold and distinctive",
        "variants_hint": "logo, logo_icon, logo_monochrome, favicon",
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _style_clause(dna: LogoDNA) -> str:
    parts = []
    if dna.style_tags:
        parts.append(", ".join(dna.style_tags))
    if dna.tone:
        parts.append(dna.tone)
    if dna.sector:
        parts.append(f"sector: {dna.sector}")
    return ", ".join(parts) if parts else "professional"


def _palette_clause(dna: LogoDNA) -> str:
    if not dna.palette:
        return ""
    return "color palette: " + ", ".join(dna.palette[:3])


def _bg_clause(dna: LogoDNA) -> str:
    if dna.background_mode == BackgroundMode.TRANSPARENT:
        return "transparent background, no background fill"
    if dna.background_mode == BackgroundMode.WHITE:
        return "white background"
    if dna.palette:
        return f"solid background color {dna.palette[0]}"
    return "transparent background"


def _typography_clause(dna: LogoDNA) -> str:
    parts = []
    if dna.typography:
        parts.append(f"typography inspired by {dna.typography[0]}")
    if dna.wordmark_weight:
        parts.append(f"{dna.wordmark_weight} weight")
    return ", ".join(parts) if parts else ""


def _icon_clause(dna: LogoDNA) -> str:
    parts = []
    if dna.symbol_preference:
        parts.append(f"{dna.symbol_preference} symbol")
    if dna.icon_complexity:
        parts.append(f"{dna.icon_complexity} complexity")
    if dna.composition_style:
        parts.append(f"{dna.composition_style} composition")
    return ", ".join(parts) if parts else ""


def _resolve_structure(dna: LogoDNA) -> LogoStructure:
    """Retourne la structure du DNA, avec fallback sur ICON_WORDMARK."""
    return dna.logo_structure or LogoStructure.ICON_WORDMARK


# ─── Prompts de concept ───────────────────────────────────────────────────────

# Variations sémantiques pour diversifier les N concepts
_CONCEPT_VARIATIONS = [
    "clean and modern approach",
    "bold and distinctive approach",
    "elegant and refined approach",
    "dynamic and energetic approach",
    "minimal and timeless approach",
]


def build_concept_prompts(dna: LogoDNA, n: int = 5) -> List[str]:
    """
    Génère n prompts de concept distincts intégrant les règles de structure.
    La LogoStructure du DNA pilote la composition.
    """
    structure = _resolve_structure(dna)
    rules = STRUCTURE_RULES[structure]

    slogan_clause = f", tagline '{dna.slogan}'" if dna.slogan else ""
    typography_clause = _typography_clause(dna)
    icon_clause = _icon_clause(dna)
    palette_clause = _palette_clause(dna)

    # Assemblage du prompt de base
    base_parts = [
        f"minimal vector logo",
        rules["base"],
        f"brand name '{dna.brand_name}'" + slogan_clause,
        rules["rules"],
        _style_clause(dna),
    ]
    if typography_clause:
        base_parts.append(typography_clause)
    if icon_clause:
        base_parts.append(icon_clause)
    if palette_clause:
        base_parts.append(palette_clause)

    base_parts.extend([
        _bg_clause(dna),
        "clean SVG vector, no gradients, no raster effects",
    ])

    base = ", ".join(p for p in base_parts if p)

    prompts = []
    for i in range(min(n, len(_CONCEPT_VARIATIONS))):
        prompts.append(f"{base}, {_CONCEPT_VARIATIONS[i]}")

    return prompts


# ─── Prompts de variante ──────────────────────────────────────────────────────

_VARIANT_SPECS: dict[str, dict] = {
    "logo": {
        "description": "primary logo, standard layout",
        "extra": "",
    },
    "logo_horizontal": {
        "description": "horizontal variant, single line, icon left of wordmark",
        "extra": "",
    },
    "logo_icon": {
        "description": "icon or symbol only, no text, optimized for small sizes",
        "extra": ", maximum simplification, remove all text elements, symbol only",
    },
    "logo_monochrome": {
        "description": "monochrome version, single color black",
        "extra": ", single color black, no color fills, solid black or outline only",
    },
    "favicon": {
        "description": "favicon variant, ultra-simplified, bold, visible at 16x16px",
        "extra": ", extreme simplification, no text, single bold shape, visible at 16px",
    },
}


def build_variant_prompts(dna: LogoDNA, concept_prompt: str) -> dict[str, str]:
    """
    Génère un prompt par variante à partir du concept sélectionné.
    La structure pilote la composition des variantes.
    Retourne un dict {variant_name: prompt}.
    """
    structure = _resolve_structure(dna)
    rules = STRUCTURE_RULES[structure]

    base = (
        f"SVG vector logo for '{dna.brand_name}'"
        f", {rules['base']}"
        f", {_style_clause(dna)}"
        f", {_bg_clause(dna)}"
        f", derived from concept: [{concept_prompt}]"
    )
    if _palette_clause(dna):
        base += f", {_palette_clause(dna)}"

    variant_prompts = {}
    for variant_name, spec in _VARIANT_SPECS.items():
        prompt = f"{base}, {spec['description']}{spec['extra']}"
        variant_prompts[variant_name] = prompt

    return variant_prompts
