"""
visual_consistency_validator.schemas
────────────────────────────────────
Types de données du module.

ValidationInput  : assets à valider (logo, palette, typo, icônes, UI, visuals)
CheckResult      : résultat d'un checker individuel
ValidationReport : rapport complet avec score global + warnings + suggestions
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Asset descriptors ────────────────────────────────────────────────────────

@dataclass
class LogoAsset:
    """Descripteur d'un logo généré."""
    style_archetype:    Optional[str] = None   # archetype utilisé lors de la génération
    logo_structure:     Optional[str] = None   # wordmark, icon_wordmark, etc.
    palette_colors:     List[str]     = field(default_factory=list)  # hex
    typography_style:   Optional[str] = None
    icon_style:         Optional[str] = None
    composition_style:  Optional[str] = None


@dataclass
class PaletteAsset:
    """Descripteur d'une palette générée."""
    primary_colors:    List[str] = field(default_factory=list)   # hex
    accent_colors:     List[str] = field(default_factory=list)
    neutral_colors:    List[str] = field(default_factory=list)
    saturation_level:  Optional[str] = None
    color_temperature: Optional[str] = None
    harmony_type:      Optional[str] = None


@dataclass
class TypographyAsset:
    """Descripteur d'une typographie choisie/générée."""
    style:          Optional[str] = None   # geometric_sans, serif_editorial, etc.
    font_family:    Optional[str] = None
    weight_hint:    Optional[str] = None   # light, medium, bold
    pairing_style:  Optional[str] = None   # mono_family, sans_serif_pair, etc.


@dataclass
class IconAsset:
    """Descripteur d'un set d'icônes."""
    style:          Optional[str] = None   # line, filled, duotone, etc.
    corner_radius:  Optional[str] = None   # sharp, rounded, circular
    weight:         Optional[str] = None   # thin, regular, bold


@dataclass
class UIThemeAsset:
    """Descripteur d'un thème UI généré."""
    layout_style:   Optional[str] = None   # clean_grid, editorial_flow, etc.
    visual_style:   Optional[str] = None   # minimal_tech, warm_organic, etc.
    spacing_type:   Optional[str] = None   # tight, balanced, spacious
    border_radius:  Optional[str] = None   # none, small, medium, large


@dataclass
class VisualAsset:
    """Descripteur d'un asset visuel (photo, illustration, motion)."""
    image_style:        Optional[str] = None   # soft_light_photography, geometric_illustration, etc.
    composition_style:  Optional[str] = None
    motion_energy:      Optional[str] = None   # none, subtle, moderate, dynamic
    color_palette:      List[str]     = field(default_factory=list)


# ─── Input ────────────────────────────────────────────────────────────────────

@dataclass
class ValidationInput:
    """Ensemble des assets à valider + le DesignDNA de référence."""
    # DesignDNA peut être passé tel quel (dict) ou reconstruit
    design_dna: Dict[str, Any] = field(default_factory=dict)

    # Assets (tous optionnels — seuls ceux fournis sont validés)
    logo:       Optional[LogoAsset]       = None
    palette:    Optional[PaletteAsset]    = None
    typography: Optional[TypographyAsset] = None
    icons:      Optional[IconAsset]       = None
    ui_theme:   Optional[UIThemeAsset]    = None
    visuals:    Optional[VisualAsset]     = None


# ─── Checker results ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Résultat d'un checker individuel."""
    checker:     str              # palette, typography, icon_style, visual_style, layout
    score:       float            # 0.0 → 1.0
    passed:      bool
    warnings:    List[str]        = field(default_factory=list)
    suggestions: List[str]        = field(default_factory=list)
    details:     Dict[str, Any]   = field(default_factory=dict)


# ─── Validation Report ────────────────────────────────────────────────────────

@dataclass
class ValidationReport:
    """Rapport complet de validation de cohérence visuelle."""
    # Statut global
    status:          str    = "valid"   # "valid" | "needs_revision" | "rejected"
    overall_score:   float  = 1.0       # 0.0 → 1.0

    # Scores par dimension
    palette_score:      Optional[float] = None
    typography_score:   Optional[float] = None
    icon_style_score:   Optional[float] = None
    visual_style_score: Optional[float] = None
    layout_score:       Optional[float] = None

    # Détails
    warnings:    List[str]         = field(default_factory=list)
    suggestions: List[str]         = field(default_factory=list)
    checks:      List[CheckResult] = field(default_factory=list)

    # Méta
    threshold:   float = 0.80
    trace:       Dict[str, Any] = field(default_factory=dict)
