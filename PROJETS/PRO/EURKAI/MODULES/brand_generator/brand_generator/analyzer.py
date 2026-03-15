"""
brand_generator.analyzer
──────────────────────────
Extrait le contexte créatif à partir du brief + BrandDNA.
Produit un CreativeContext qui guide la génération des 3 directions.

Ce module ne fait pas d'appel LLM — il construit le contexte
structuré qui sera injecté dans le prompt de direction_builder.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .schemas import BrandDNA, BrandGeneratorInput


@dataclass
class CreativeContext:
    """Contexte créatif enrichi, prêt pour injection dans le prompt LLM."""
    brand_name:        str
    brief_summary:     str
    sector:            Optional[str]
    audience:          Optional[str]
    positioning:       Optional[str]
    existing_tags:     List[str]       = field(default_factory=list)
    existing_palette:  List[str]       = field(default_factory=list)
    existing_tone:     Optional[str]   = None
    constraints:       List[str]       = field(default_factory=list)
    contrast_axes:     List[str]       = field(default_factory=list)


# ─── Axes de contraste par secteur ────────────────────────────────────────────
# Guide la génération de directions différenciées selon le secteur.

_SECTOR_CONTRAST_AXES: dict[str, List[str]] = {
    "fintech":       ["minimal/tech", "premium/editorial", "bold/disruptive"],
    "health":        ["clean/clinical", "warm/human", "modern/dynamic"],
    "food":          ["artisan/natural", "bold/graphic", "playful/colorful"],
    "fashion":       ["minimal/luxury", "editorial/bold", "avant-garde/expressive"],
    "saas":          ["minimal/geometric", "modern/friendly", "bold/high-contrast"],
    "education":     ["playful/accessible", "clean/structured", "inspirational/warm"],
    "real_estate":   ["premium/minimal", "trustworthy/classic", "modern/bold"],
    "wellness":      ["organic/natural", "clean/airy", "bold/empowering"],
    "sport":         ["dynamic/energetic", "minimal/athletic", "bold/urban"],
    "luxury":        ["minimal/refined", "editorial/dramatic", "heritage/classic"],
    "gaming":        ["neon/tech", "dark/aggressive", "playful/colorful"],
    "nonprofit":     ["warm/human", "bold/activist", "clean/hopeful"],
}

_DEFAULT_CONTRAST_AXES = ["minimal/geometric", "expressive/rounded", "bold/editorial"]


def analyze(input_data: BrandGeneratorInput) -> CreativeContext:
    """
    Construit le CreativeContext à partir des inputs.
    Infère les axes de contraste selon le secteur.
    """
    dna = input_data.brand_dna
    sector = (input_data.sector or dna.sector or "").lower().strip()

    # Axes de contraste selon secteur
    contrast_axes = _SECTOR_CONTRAST_AXES.get(sector, _DEFAULT_CONTRAST_AXES)

    # Contraintes issues du DNA existant
    constraints: List[str] = []
    if dna.style_tags:
        constraints.append(f"existing style: {', '.join(dna.style_tags)}")
    if dna.palette:
        constraints.append(f"existing palette: {', '.join(dna.palette[:3])}")
    if dna.typography:
        constraints.append(f"existing typography: {', '.join(dna.typography[:2])}")
    if dna.tone:
        constraints.append(f"brand tone: {dna.tone}")

    return CreativeContext(
        brand_name=dna.brand_name,
        brief_summary=input_data.project_brief.strip(),
        sector=sector or None,
        audience=input_data.audience or dna.target,
        positioning=input_data.positioning,
        existing_tags=dna.style_tags,
        existing_palette=dna.palette,
        existing_tone=dna.tone,
        constraints=constraints,
        contrast_axes=contrast_axes,
    )
