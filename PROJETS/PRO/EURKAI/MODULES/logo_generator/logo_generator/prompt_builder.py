"""
logo_generator.prompt_builder
──────────────────────────────
Construit les prompts Recraft v3 à partir d'un LogoDNA.
Un prompt par concept (génération initiale) + un prompt par variante.
"""

from __future__ import annotations
from typing import List

from .schemas import LogoDNA, LogoType, BackgroundMode


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
    colors = ", ".join(dna.palette[:3])
    return f"color palette: {colors}"


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


# ─── Prompts de concept ───────────────────────────────────────────────────────

_CONCEPT_TEMPLATES: dict[LogoType, str] = {
    LogoType.WORDMARK: (
        "Vector logo, wordmark only, brand name '{name}'"
        "{slogan_clause}"
        ", {style}, {typography}"
        ", clean SVG vector, {bg}, no gradients, no raster effects"
    ),
    LogoType.LETTERMARK: (
        "Vector logo, lettermark '{initials}' for brand '{name}'"
        ", {style}, {icon_style}"
        ", clean SVG vector, {bg}, geometric precision"
    ),
    LogoType.SYMBOL: (
        "Vector logo mark, icon only representing '{name}'"
        "{slogan_clause}"
        ", {style}, {icon_style}"
        ", clean SVG vector, {bg}, scalable to 16px"
    ),
    LogoType.COMBINATION: (
        "Vector combination logo, icon + wordmark for '{name}'"
        "{slogan_clause}"
        ", {style}, {icon_style}, {typography}"
        ", clean SVG vector, {bg}, balanced layout"
    ),
    LogoType.EMBLEM: (
        "Vector emblem logo, brand name '{name}' inside a badge/seal shape"
        "{slogan_clause}"
        ", {style}"
        ", clean SVG vector, {bg}, contained composition"
    ),
}


def build_concept_prompts(dna: LogoDNA, logo_type: LogoType, n: int = 5) -> List[str]:
    """Génère n prompts de concept distincts (variation de style/approche)."""
    template = _CONCEPT_TEMPLATES[logo_type]
    slogan_clause = f", tagline '{dna.slogan}'" if dna.slogan else ""
    initials = "".join(w[0].upper() for w in dna.brand_name.split()[:2]) or dna.brand_name[0].upper()

    base_vars = dict(
        name=dna.brand_name,
        initials=initials,
        slogan_clause=slogan_clause,
        style=_style_clause(dna),
        palette=_palette_clause(dna),
        typography=_typography_clause(dna),
        icon_style=_icon_clause(dna),
        bg=_bg_clause(dna),
    )

    # Variations sémantiques pour les n concepts
    variations = [
        "concept 1: clean and modern",
        "concept 2: bold and distinctive",
        "concept 3: elegant and refined",
        "concept 4: dynamic and energetic",
        "concept 5: minimal and timeless",
    ]

    prompts = []
    for i in range(min(n, len(variations))):
        variation = variations[i]
        prompt = template.format(**base_vars)
        prompt = f"{prompt}, {variation}"
        if base_vars["palette"]:
            prompt = f"{prompt}, {base_vars['palette']}"
        prompts.append(prompt)

    return prompts


# ─── Prompts de variante ──────────────────────────────────────────────────────

_VARIANT_DESCRIPTIONS: dict[str, str] = {
    "logo":             "primary logo, standard horizontal layout",
    "logo_horizontal":  "horizontal variant, icon left of wordmark, single line",
    "logo_icon":        "icon/symbol only, no text, optimized for small sizes",
    "logo_monochrome":  "monochrome version, single color, no fills except black",
    "favicon":          "favicon variant, icon only, extremely simplified, bold, visible at 16x16px",
}


def build_variant_prompts(dna: LogoDNA, concept_prompt: str, logo_type: LogoType) -> dict[str, str]:
    """
    Génère un prompt par variante à partir du concept sélectionné.
    Retourne un dict {variant_name: prompt}.
    """
    base = (
        f"SVG vector logo for '{dna.brand_name}', {_style_clause(dna)}, "
        f"{_bg_clause(dna)}, derived from: [{concept_prompt}]"
    )
    if _palette_clause(dna):
        base += f", {_palette_clause(dna)}"

    variant_prompts = {}
    for variant_name, description in _VARIANT_DESCRIPTIONS.items():
        # favicon et logo_icon : forcer simplification maximale
        if variant_name in ("favicon", "logo_icon"):
            extra = ", maximum simplification, no text, geometric reduction, bold shapes only"
        elif variant_name == "logo_monochrome":
            extra = ", single color black, remove all color fills, outline only or solid black"
        else:
            extra = ""
        variant_prompts[variant_name] = f"{base}, {description}{extra}"

    return variant_prompts
