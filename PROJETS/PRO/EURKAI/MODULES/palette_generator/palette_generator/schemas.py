"""
palette_generator.schemas
──────────────────────────
Types de données du module palette_generator.
Entièrement standalone — aucune dépendance sur les autres modules EURKAI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ─── Enums ────────────────────────────────────────────────────────────────────

class PaletteScenario(str, Enum):
    BRAND              = "brand_palette"
    UI                 = "ui_palette"
    ILLUSTRATION       = "illustration_palette"
    PHOTO              = "photo_palette"
    MINIMAL            = "minimal_palette"
    DARK_MODE          = "dark_mode_palette"
    DATA_VISUALIZATION = "data_visualization_palette"


class HarmonyType(str, Enum):
    MONOCHROMATIC      = "monochromatic"
    ANALOGOUS          = "analogous"
    COMPLEMENTARY      = "complementary"
    SPLIT_COMPLEMENTARY = "split_complementary"
    TRIADIC            = "triadic"
    TETRADIC           = "tetradic"


class MetalFinish(str, Enum):
    SILVER    = "silver"
    CHROME    = "chrome"
    GOLD      = "gold"
    ROSE_GOLD = "rose_gold"
    COPPER    = "copper"
    BRASS     = "brass"
    GUNMETAL  = "gunmetal"
    TITANIUM  = "titanium"


class WCAGLevel(str, Enum):
    AA  = "AA"    # 4.5:1 normal text, 3:1 large text
    AAA = "AAA"   # 7:1 normal text


# ─── Couleur de base ──────────────────────────────────────────────────────────

@dataclass
class ColorValue:
    hex:   str                        # "#3B82F6"
    rgb:   Tuple[int, int, int]       = field(default_factory=lambda: (0, 0, 0))
    hsl:   Tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    name:  Optional[str]              = None   # label sémantique ex: "primary_blue"
    role:  Optional[str]              = None   # "primary", "accent", "neutral", "text", "background"


# ─── Scale tonale ─────────────────────────────────────────────────────────────

@dataclass
class TonalScale:
    """Scale 100→900 d'une couleur de base."""
    base_hex:   str
    base_name:  str                            # ex: "primary_blue"
    shades:     Dict[int, ColorValue]          = field(default_factory=dict)
    # shades keys : 100, 200, 300, 400, 500, 600, 700, 800, 900


# ─── Palette ──────────────────────────────────────────────────────────────────

@dataclass
class Palette:
    """Une palette = 4 groupes de couleurs + scales tonales optionnelles."""
    harmony:    str                       # type de palette (HarmonyType.value ou "bw" etc.)
    primary:    List[ColorValue]          = field(default_factory=list)
    secondary:  List[ColorValue]          = field(default_factory=list)
    accent:     List[ColorValue]          = field(default_factory=list)
    neutral:    List[ColorValue]          = field(default_factory=list)
    tonal_scales: List[TonalScale]        = field(default_factory=list)


# ─── BW Variant ───────────────────────────────────────────────────────────────

@dataclass
class BWVariant:
    false_blacks:  List[ColorValue]  = field(default_factory=list)
    false_whites:  List[ColorValue]  = field(default_factory=list)


# ─── Metal Variant ────────────────────────────────────────────────────────────

@dataclass
class MetalPalette:
    finish:       MetalFinish
    base_tones:   List[ColorValue]   = field(default_factory=list)
    highlights:   List[ColorValue]   = field(default_factory=list)
    shadows:      List[ColorValue]   = field(default_factory=list)
    accent:       List[ColorValue]   = field(default_factory=list)


# ─── Résultat de validation WCAG ──────────────────────────────────────────────

@dataclass
class ContrastCheck:
    pair:         str             # ex: "text_on_background"
    fg_hex:       str
    bg_hex:       str
    ratio:        float
    aa_pass:      bool
    aaa_pass:     bool


@dataclass
class AccessibilityReport:
    checks:       List[ContrastCheck]   = field(default_factory=list)
    all_aa_pass:  bool                  = False
    all_aaa_pass: bool                  = False


# ─── PaletteSet (output principal) ───────────────────────────────────────────

@dataclass
class PaletteSet:
    """Ensemble de toutes les variantes générées."""
    base_hex:             str
    scenario:             PaletteScenario
    monochromatic:        Optional[Palette]      = None
    analogous:            Optional[Palette]      = None
    complementary:        Optional[Palette]      = None
    split_complementary:  Optional[Palette]      = None
    triadic:              Optional[Palette]      = None
    tetradic:             Optional[Palette]      = None
    black_and_white_variant: Optional[BWVariant] = None
    metal_variant:        Optional[MetalPalette] = None
    minimal:              Optional[Palette]      = None
    ui_safe:              Optional[Palette]      = None
    accessibility_report: Optional[AccessibilityReport] = None


# ─── Inputs ───────────────────────────────────────────────────────────────────

@dataclass
class BrandDNAInput:
    """BrandDNA minimal — standalone, pas d'import depuis logo_generator."""
    brand_name:    Optional[str]    = None
    tone:          Optional[str]    = None
    style_tags:    List[str]        = field(default_factory=list)
    palette:       List[str]        = field(default_factory=list)   # hex existants
    brand_values:  List[str]        = field(default_factory=list)


@dataclass
class PaletteInput:
    """Entrée principale du générateur."""
    scenario:       PaletteScenario         = PaletteScenario.BRAND
    base_color:     Optional[str]           = None    # hex unique
    base_colors:    List[str]               = field(default_factory=list)  # plusieurs hex
    brand_dna:      Optional[BrandDNAInput] = None
    style_tags:     List[str]               = field(default_factory=list)
    palette_style:  Optional[str]           = None    # ex: "warm", "cool", "neutral"
    metal_finish:   Optional[MetalFinish]   = None    # si None → auto-détecté
    wcag_level:     WCAGLevel               = WCAGLevel.AA


# ─── Output final ─────────────────────────────────────────────────────────────

@dataclass
class PaletteOutput:
    """Résultat complet du module."""
    palette_set:    PaletteSet
    export_paths:   Dict[str, str]   = field(default_factory=dict)  # {format: path}
    trace:          dict             = field(default_factory=dict)
