"""
models.py — Structures de données du EurkaiStyleAdapter.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColorSignal:
    """Une couleur détectée dans le CSS/DOM avec son contexte."""
    value: str                   # valeur hex normalisée (#rrggbb)
    raw: str                     # valeur originale CSS
    property: str                # ex: "background-color"
    selector: str                # ex: ".btn-primary"
    role: str = "unknown"        # primary | secondary | text | background | surface | border | accent
    frequency: int = 1
    confidence: float = 0.5      # 0–1 : certitude du rôle sémantique


@dataclass
class FontSignal:
    """Une police détectée."""
    family: str                  # ex: "Inter"
    raw: str                     # ex: "'Inter', sans-serif"
    property: str                # font-family
    selector: str                # ex: "body"
    role: str = "body"           # heading | body | mono
    is_google: bool = False


@dataclass
class RadiusSignal:
    """Une valeur de border-radius détectée."""
    value_px: float              # valeur en pixels
    raw: str                     # valeur CSS originale
    selector: str
    role: str = "md"             # sm | md | lg | xl


@dataclass
class SpacingSignal:
    """Une valeur d'espacement détectée."""
    value_px: float
    raw: str
    property: str               # padding | margin | gap
    selector: str


@dataclass
class CSSSignals:
    """Ensemble des signaux extraits du CSS."""
    colors:   list[ColorSignal]   = field(default_factory=list)
    fonts:    list[FontSignal]    = field(default_factory=list)
    radii:    list[RadiusSignal]  = field(default_factory=list)
    spacings: list[SpacingSignal] = field(default_factory=list)
    css_vars: dict[str, str]      = field(default_factory=dict)  # --xxx: value


@dataclass
class DOMSignals:
    """Signaux extraits de l'analyse du DOM."""
    detected_framework: str | None = None   # bootstrap | tailwind | bulma | ...
    existing_css_vars:  dict[str, str] = field(default_factory=dict)  # --xxx: value dans style
    color_hints:        dict[str, str] = field(default_factory=dict)  # role → hex
    font_hints:         dict[str, str] = field(default_factory=dict)  # role → family
    inline_signals:     list[ColorSignal] = field(default_factory=list)


@dataclass
class TokenMap:
    """Mapping final : token Eurkai → valeur extraite du site."""
    # Couleurs
    color_primary:        str = "#667eea"
    color_primary_light:  str = "#7c8ef5"
    color_primary_dark:   str = "#4f58c8"
    color_secondary:      str = "#764ba2"
    color_secondary_light:str = "#8d62b8"
    color_secondary_dark: str = "#5e3882"
    color_text:           str = "rgb(45, 55, 72)"
    color_text_light:     str = "rgb(113, 128, 150)"
    color_bg:             str = "rgb(255, 255, 255)"
    color_bg_gray:        str = "rgb(247, 250, 252)"
    color_border:         str = "rgb(226, 232, 240)"
    # Typographie
    font_family_headings: str = "Inter"
    font_family_body:     str = "Inter"
    font_google_url:      str = ""
    # Géométrie
    border_radius_sm:     str = "4px"
    border_radius_md:     str = "8px"
    border_radius_lg:     str = "12px"
    border_radius_xl:     str = "16px"
    # Ombres (dérivées de la couleur primaire)
    shadow_sm:            str = "0 1px 3px rgba(0,0,0,0.06)"
    shadow_md:            str = "0 4px 12px rgba(0,0,0,0.08)"
    shadow_lg:            str = "0 12px 28px rgba(0,0,0,0.12)"


@dataclass
class EurkaiPatch:
    """Output complet de l'EurkaiStyleAdapter."""
    # CSS patch prêt à injecter
    css_patch: str

    # Mapping documenté (pour debug / reporting)
    token_map: dict[str, str]

    # Sources d'où viennent les tokens (explainability)
    source_signals: dict[str, str]

    # Score de confiance global (0–1)
    confidence: float = 0.0

    # Avertissements (tokens non résolus, conflits, etc.)
    warnings: list[str] = field(default_factory=list)

    # Métadonnées
    framework_detected: str | None = None
    extraction_stats:   dict = field(default_factory=dict)
