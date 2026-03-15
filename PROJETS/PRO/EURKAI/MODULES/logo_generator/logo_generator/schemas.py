"""
logo_generator.schemas
──────────────────────
Types de données du module logo_generator.
LogoDNA étend BrandDNA avec les champs spécifiques logo.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ─── Types de base ────────────────────────────────────────────────────────────

class LogoType(str, Enum):
    """Conservé pour rétrocompatibilité. Préférer LogoStructure."""
    WORDMARK      = "wordmark"
    LETTERMARK    = "lettermark"
    SYMBOL        = "symbol"
    COMBINATION   = "combination"
    EMBLEM        = "emblem"


class LogoStructure(str, Enum):
    """
    Structure de composition du logo.
    Pilote les règles de prompt et la génération de variantes.
    """
    WORDMARK         = "wordmark"         # typographie distinctive, texte seul
    MONOGRAM         = "monogram"         # initiales/combinaison de lettres
    ICON_WORDMARK    = "icon_wordmark"    # symbole + nom de marque
    EMBLEM           = "emblem"           # texte intégré dans forme/symbole
    BADGE            = "badge"            # logo dans forme décorative
    MASCOT           = "mascot"           # personnage/illustration + marque
    ABSTRACT_SYMBOL  = "abstract_symbol"  # symbole géométrique abstrait
    STACKED          = "stacked"          # éléments texte empilés verticalement
    LETTERMARK       = "lettermark"       # lettre unique stylisée


class ArbitrationMode(str, Enum):
    NONE  = "none"    # premier concept retenu automatiquement
    AI    = "ai"      # scoring automatique (ThemeResolver / VIE)
    HUMAN = "human"   # sélection manuelle (retourne tous les concepts)


class BackgroundMode(str, Enum):
    TRANSPARENT = "transparent"
    WHITE       = "white"
    BRAND       = "brand"   # couleur primaire BrandDNA


# ─── BrandDNA (racine) ────────────────────────────────────────────────────────

@dataclass
class BrandDNA:
    """Identité de marque partagée par tous les modules visuels."""
    brand_name:   str
    slogan:       Optional[str]       = None
    sector:       Optional[str]       = None      # ex: "fintech", "restauration"
    style_tags:   List[str]           = field(default_factory=list)
    palette:      List[str]           = field(default_factory=list)   # hex
    typography:   List[str]           = field(default_factory=list)   # noms de fontes
    tone:         Optional[str]       = None      # ex: "premium", "playful"
    target:       Optional[str]       = None      # ex: "B2B", "18-35 ans"


# ─── LogoDNA (extension de BrandDNA) ─────────────────────────────────────────

@dataclass
class LogoDNA(BrandDNA):
    """
    DNA spécifique à la génération de logos.
    Étend BrandDNA sans en dupliquer les champs.
    """
    logo_structure:     Optional[LogoStructure] = None  # structure de composition principale
    symbol_preference:  Optional[str]           = None  # ex: "geometric", "organic", "abstract"
    composition_style:  Optional[str]           = None  # ex: "balanced", "stacked", "inline"
    wordmark_weight:    Optional[str]           = None  # ex: "light", "bold", "italic"
    icon_complexity:    Optional[str]           = None  # ex: "minimal", "moderate", "detailed"
    background_mode:    BackgroundMode          = BackgroundMode.TRANSPARENT


# ─── Configuration d'arbitrage ────────────────────────────────────────────────

@dataclass
class ArbitrationConfig:
    mode:               ArbitrationMode     = ArbitrationMode.AI
    n_concepts:         int                 = 5     # concepts à générer
    n_variants:         int                 = 5     # variantes par concept retenu
    ai_score_threshold: float               = 0.6   # seuil minimum (mode AI)


# ─── Concepts et variantes ────────────────────────────────────────────────────

@dataclass
class LogoConcept:
    """Un concept logo généré (avant sélection)."""
    concept_id:         str
    logo_structure:     LogoStructure
    prompt_used:        str
    svg_content:    str                     # SVG brut retourné par Recraft
    score:          Optional[float]  = None  # renseigné en mode AI
    flags:          List[str]        = field(default_factory=list)  # warnings vector_optimizer


@dataclass
class LogoVariant:
    """Une variante SVG d'un concept sélectionné."""
    variant_name:   str          # logo, logo_horizontal, logo_icon, logo_monochrome, favicon
    prompt_used:    str
    svg_content:    str
    file_path:      Optional[str] = None    # chemin après export


@dataclass
class LogoVariantSet:
    """Ensemble des 5 variantes d'un concept retenu."""
    concept_id:     str
    variants:       List[LogoVariant]       = field(default_factory=list)


# ─── Output final ─────────────────────────────────────────────────────────────

@dataclass
class LogoOutput:
    """Résultat complet du module logo_generator."""
    brand_name:         str
    logo_structure:     LogoStructure
    arbitration_mode:   ArbitrationMode
    selected_concept:   Optional[LogoConcept]       = None
    all_concepts:       List[LogoConcept]            = field(default_factory=list)
    variant_set:        Optional[LogoVariantSet]     = None
    output_dir:         Optional[str]                = None
    trace:              dict                         = field(default_factory=dict)
