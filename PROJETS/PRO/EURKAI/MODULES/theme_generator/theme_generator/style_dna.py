"""
theme_generator.style_dna
──────────────────────────
Structures de données représentant le DNA visuel extrait d'une source.

Produit par visual_analysis, consommé par theme_translation.
Générique : web, app, print, branding.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PaletteProfile:
    """Profil colorimétrique extrait de la source visuelle."""
    dominant:    List[str] = field(default_factory=list)   # hex — 2-3 couleurs dominantes
    accent:      List[str] = field(default_factory=list)   # hex — 1-2 couleurs d'accent
    neutral:     List[str] = field(default_factory=list)   # hex — fond + texte
    temperature: str = "neutral"   # cold | neutral | warm
    saturation:  str = "medium"    # very_low | low | medium | high | very_high
    contrast:    str = "medium"    # low | medium | high


@dataclass
class TypographyProfile:
    """Profils typographiques (pas de polices identifiées — profils sémantiques)."""
    display: str = "neutral_sans"              # voir font_map.DISPLAY_FONT_MAP
    body:    str = "neutral_humanist_sans"     # voir font_map.BODY_FONT_MAP
    accent:  Optional[str] = None              # optionnel


@dataclass
class GeometryProfile:
    """Profil géométrique de la source."""
    border_radius: str = "medium"   # none | sharp | small | medium | large | circular
    shape_family:  str = "geometric" # geometric | organic | irregular | strict
    stroke_weight: str = "regular"  # thin | regular | bold | heavy
    symmetry:      str = "balanced" # strict | balanced | free


@dataclass
class OrnamentProfile:
    """Profil des éléments décoratifs."""
    has_ornaments: bool = False
    family:        Optional[str] = None          # "candles" | "botanical" | "geometric_frame" | ...
    density:       str = "none"                  # none | light | medium | heavy
    placement:     List[str] = field(default_factory=list)  # ["top", "corners", "scattered"]
    rendering:     str = "none"                  # svg_parametric | pattern | asset_pack | none


@dataclass
class LayoutProfile:
    """Profil de mise en page."""
    rhythm:    str = "balanced"    # tight | balanced | spacious | editorial
    grid_type: str = "modular"     # strict | modular | asymmetric | freeform
    density:   str = "moderate"    # minimal | moderate | dense


@dataclass
class StyleDNA:
    """
    Représentation structurée du langage visuel extrait d'une source.

    Produit par visual_analysis (ou injecté manuellement pour MVP/tests).
    Consommé par theme_translation pour produire un ThemePreset.
    """
    palette_profile:    PaletteProfile    = field(default_factory=PaletteProfile)
    typography_profile: TypographyProfile = field(default_factory=TypographyProfile)
    geometry_profile:   GeometryProfile   = field(default_factory=GeometryProfile)
    ornament_profile:   OrnamentProfile   = field(default_factory=OrnamentProfile)
    layout_profile:     LayoutProfile     = field(default_factory=LayoutProfile)

    emotional_tone:   str       = "calm"     # calm | bold | playful | premium | raw | tech
    complexity_level: str       = "moderate" # minimal | moderate | rich
    aesthetic_tags:   List[str] = field(default_factory=list)

    # Méta (source, non utilisé par la traduction)
    source_type: Optional[str] = None   # image | screenshot | logo | mockup | manual
    source_ref:  Optional[str] = None   # path ou URL de la source


def style_dna_from_dict(d: dict) -> StyleDNA:
    """Reconstruit un StyleDNA depuis un dict (ex: chargé depuis JSON)."""
    pp = d.get("palette_profile", {})
    tp = d.get("typography_profile", {})
    gp = d.get("geometry_profile", {})
    op = d.get("ornament_profile", {})
    lp = d.get("layout_profile", {})

    return StyleDNA(
        palette_profile=PaletteProfile(
            dominant=pp.get("dominant", []),
            accent=pp.get("accent", []),
            neutral=pp.get("neutral", []),
            temperature=pp.get("temperature", "neutral"),
            saturation=pp.get("saturation", "medium"),
            contrast=pp.get("contrast", "medium"),
        ),
        typography_profile=TypographyProfile(
            display=tp.get("display", "neutral_sans"),
            body=tp.get("body", "neutral_humanist_sans"),
            accent=tp.get("accent"),
        ),
        geometry_profile=GeometryProfile(
            border_radius=gp.get("border_radius", "medium"),
            shape_family=gp.get("shape_family", "geometric"),
            stroke_weight=gp.get("stroke_weight", "regular"),
            symmetry=gp.get("symmetry", "balanced"),
        ),
        ornament_profile=OrnamentProfile(
            has_ornaments=op.get("has_ornaments", False),
            family=op.get("family"),
            density=op.get("density", "none"),
            placement=op.get("placement", []),
            rendering=op.get("rendering", "none"),
        ),
        layout_profile=LayoutProfile(
            rhythm=lp.get("rhythm", "balanced"),
            grid_type=lp.get("grid_type", "modular"),
            density=lp.get("density", "moderate"),
        ),
        emotional_tone=d.get("emotional_tone", "calm"),
        complexity_level=d.get("complexity_level", "moderate"),
        aesthetic_tags=d.get("aesthetic_tags", []),
        source_type=d.get("source_type"),
        source_ref=d.get("source_ref"),
    )
