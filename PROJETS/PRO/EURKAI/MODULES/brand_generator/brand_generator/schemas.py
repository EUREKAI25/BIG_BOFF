"""
brand_generator.schemas
────────────────────────
Types de données du module brand_generator.

BrandDirection est le type central : il encapsule une direction créative complète
et est consommable directement par logo_generator, font_generator,
icon_font_generator, palette_generator, webdesign_generator, image_generator.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# Import partagé depuis logo_generator pour éviter la duplication
try:
    from logo_generator.schemas import BrandDNA, LogoStructure
except ImportError:
    # Fallback si logo_generator n'est pas installé
    from dataclasses import dataclass as _dc

    @_dc
    class BrandDNA:  # type: ignore[no-redef]
        brand_name:  str
        slogan:      Optional[str]  = None
        sector:      Optional[str]  = None
        style_tags:  List[str]      = field(default_factory=list)
        palette:     List[str]      = field(default_factory=list)
        typography:  List[str]      = field(default_factory=list)
        tone:        Optional[str]  = None
        target:      Optional[str]  = None

    class LogoStructure(str, Enum):  # type: ignore[no-redef]
        WORDMARK        = "wordmark"
        MONOGRAM        = "monogram"
        ICON_WORDMARK   = "icon_wordmark"
        EMBLEM          = "emblem"
        BADGE           = "badge"
        MASCOT          = "mascot"
        ABSTRACT_SYMBOL = "abstract_symbol"
        STACKED         = "stacked"
        LETTERMARK      = "lettermark"


# ─── Sous-profils ─────────────────────────────────────────────────────────────

@dataclass
class PaletteProfile:
    """Description sémantique de la palette — pas de valeurs hex (rôle de palette_generator)."""
    palette_type:      str              # ex: "monochromatic", "complementary", "triadic", "neutral"
    dominant_hue:      Optional[str]   = None   # ex: "deep blue", "warm terracotta", "forest green"
    saturation_level:  str             = "medium"  # low / medium / high / vivid
    contrast_level:    str             = "medium"  # low / medium / high / extreme
    mood:              Optional[str]   = None   # ex: "cold & corporate", "warm & inviting"


@dataclass
class TypographyProfile:
    """Orientation typographique — pas de noms de fontes (rôle de font_generator)."""
    personality:          str              # ex: "geometric sans", "humanist serif", "display slab"
    primary_font_style:   str              # ex: "sans-serif geometric", "serif transitional"
    secondary_font_style: Optional[str]  = None  # ex: "monospace", "script"
    weight_range:         str             = "regular to bold"  # ex: "light to medium", "bold only"
    optical_size:         str             = "standard"  # compact / standard / display


# ─── BrandDirection ───────────────────────────────────────────────────────────

@dataclass
class BrandDirection:
    """
    Une direction créative complète.
    Consommable par tous les modules design en aval.
    """
    # Identité de la direction
    name:            str
    description:     str
    design_intent:   str
    style_tags:      List[str]         = field(default_factory=list)
    mood_keywords:   List[str]         = field(default_factory=list)

    # Profils visuels
    palette_profile:      Optional[PaletteProfile]    = None
    typography_profile:   Optional[TypographyProfile] = None
    icon_style:           str                         = "minimal"
    illustration_style:   Optional[str]               = None
    image_style:          Optional[str]               = None
    composition_style:    str                         = "balanced"
    motion_energy:        str                         = "subtle"   # none/subtle/moderate/dynamic

    # Guidance logo (→ logo_generator)
    logo_structure:    Optional[LogoStructure]  = None
    symbol_preference: Optional[str]            = None
    wordmark_weight:   Optional[str]            = None
    icon_complexity:   str                      = "minimal"

    # Guidance UI (→ webdesign_generator)
    layout_density:       str = "comfortable"  # compact / comfortable / spacious
    whitespace_level:     str = "medium"       # minimal / medium / generous
    grid_style:           str = "standard"     # strict / standard / fluid / asymmetric
    component_roundness:  str = "medium"       # sharp / medium / rounded / pill
    contrast_level:       str = "medium"       # low / medium / high / extreme


# ─── Input / Output ───────────────────────────────────────────────────────────

@dataclass
class BrandGeneratorInput:
    """Paramètres d'entrée du module."""
    project_brief:  str
    brand_dna:      BrandDNA
    sector:         Optional[str]  = None
    audience:       Optional[str]  = None
    positioning:    Optional[str]  = None


@dataclass
class BrandGeneratorOutput:
    """Résultat : 3 directions créatives distinctes."""
    direction_a:    BrandDirection
    direction_b:    BrandDirection
    direction_c:    BrandDirection
    trace:          dict           = field(default_factory=dict)

    def as_dict(self) -> dict:
        """Format de sortie compatible API et modules aval."""
        import dataclasses
        return {
            "direction_A": dataclasses.asdict(self.direction_a),
            "direction_B": dataclasses.asdict(self.direction_b),
            "direction_C": dataclasses.asdict(self.direction_c),
        }
