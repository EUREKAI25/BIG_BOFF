"""
design_dna_resolver.schemas
─────────────────────────────
Types de données du module.

BriefInput : brief normalisé (intermédiaire interne)
DesignDNA  : objet structuré consommé par tous les modules design aval
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Input ────────────────────────────────────────────────────────────────────

@dataclass
class BriefInput:
    """Brief normalisé issu du brief_parser."""
    project_name:    Optional[str]   = None
    industry:        Optional[str]   = None
    brand_values:    List[str]       = field(default_factory=list)
    tone:            Optional[str]   = None
    target_audience: Optional[str]   = None
    keywords:        List[str]       = field(default_factory=list)
    style_tags:      List[str]       = field(default_factory=list)
    region:          Optional[str]   = None
    raw_text:        Optional[str]   = None     # brief texte libre (si fourni)


# ─── Palette Bias ─────────────────────────────────────────────────────────────

@dataclass
class PaletteBias:
    """
    Suggestions colorées sémantiques pour palette_generator.
    Cohérentes avec color_psychology_engine.ColorRecommendation.
    """
    preferred_colors:   List[str]  = field(default_factory=list)
    accent_candidates:  List[str]  = field(default_factory=list)
    neutral_candidates: List[str]  = field(default_factory=list)
    avoid_colors:       List[str]  = field(default_factory=list)
    saturation_level:   str        = "medium"
    color_temperature:  str        = "neutral"


# ─── DesignDNA ────────────────────────────────────────────────────────────────

@dataclass
class DesignDNA:
    """
    Objet structuré produit par design_dna_resolver.
    Consommé par tous les modules design EURKAI en aval.
    """
    # Identité de marque
    project_name:    Optional[str]  = None
    industry:        Optional[str]  = None
    brand_values:    List[str]      = field(default_factory=list)
    tone:            Optional[str]  = None
    target_audience: Optional[str]  = None
    keywords:        List[str]      = field(default_factory=list)

    # Archétype stylistique (inféré)
    style_archetype: Optional[str]  = None   # luxury_minimal, startup_clean, etc.

    # Hints pour chaque module aval
    palette_bias:      Optional[PaletteBias] = None   # → color_psychology_engine + palette_generator
    typography_style:  Optional[str]         = None   # → font_generator
    icon_style:        Optional[str]         = None   # → icon_font_generator, logo_generator
    layout_style:      Optional[str]         = None   # → webdesign_generator
    visual_style:      Optional[str]         = None   # → webdesign_generator, media_generator
    image_style:       Optional[str]         = None   # → media_generator, image_generator
    composition_style: Optional[str]         = None   # → logo_generator, webdesign_generator
    motion_energy:     Optional[str]         = None   # → media_generator (none/subtle/moderate/dynamic)

    # Logo guidance
    logo_structure_hint:  Optional[str] = None   # → logo_generator (LogoStructure value)
    wordmark_weight_hint: Optional[str] = None   # → logo_generator

    # Méta
    confidence:      float  = 0.0
    trace:           dict   = field(default_factory=dict)
