"""
design_exploration_engine.schemas
──────────────────────────────────
Types de données du module.

DesignDirection  : une direction créative (archétype + paramètres de style)
ExplorationInput : DesignDNA + config (n_directions)
ExplorationOutput: liste de directions générées
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── Direction ────────────────────────────────────────────────────────────────

@dataclass
class DesignDirection:
    """
    Une direction créative distincte, déclinée depuis un DesignDNA.
    Chaque direction est passable directement aux modules de génération aval.
    """
    id:               str              # "direction_1", "direction_2", ...
    name:             str              # Nom court (ex: "Clean Tech")
    tagline:          str              # Description 1 phrase
    style_archetype:  str              # Un des 12 archetypes

    # Paramètres de style (compatible avec DesignDNA downstream)
    palette_bias:        List[str]      = field(default_factory=list)   # couleurs sémantiques préférées
    typography_style:    Optional[str]  = None
    icon_style:          Optional[str]  = None
    visual_style:        Optional[str]  = None
    layout_style:        Optional[str]  = None
    image_style:         Optional[str]  = None
    composition_style:   Optional[str]  = None
    motion_energy:       Optional[str]  = None

    # Logo hints
    logo_structure_hint:  Optional[str] = None
    wordmark_weight_hint: Optional[str] = None

    # Méta
    direction_family:  Optional[str]    = None   # clean_modern, premium_luxury, etc.
    differentiation:   List[str]        = field(default_factory=list)  # axes de différenciation vs dna source
    confidence:        float            = 1.0


# ─── Input ────────────────────────────────────────────────────────────────────

@dataclass
class ExplorationInput:
    """
    Entrée du module.
    Le DesignDNA peut être passé en dict brut (issu de design_dna_resolver).
    """
    design_dna:   Dict[str, Any] = field(default_factory=dict)
    n_directions: int            = 3    # 2 à 5


# ─── Output ───────────────────────────────────────────────────────────────────

@dataclass
class ExplorationOutput:
    """Sortie : N directions créatives."""
    directions: List[DesignDirection] = field(default_factory=list)
    source_archetype: Optional[str]   = None   # archétype du DesignDNA d'origine
    trace: Dict[str, Any]             = field(default_factory=dict)
