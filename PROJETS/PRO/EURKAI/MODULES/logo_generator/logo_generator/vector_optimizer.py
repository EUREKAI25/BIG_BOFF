"""
logo_generator.vector_optimizer
─────────────────────────────────
Normalise et optimise les SVG retournés par Recraft.

RÈGLE ABSOLUE : ne jamais supprimer de shapes.
L'optimizer FLAG uniquement — la décision de suppression
appartient à l'humain ou à un agent de revue.

Opérations autorisées :
  - Normaliser viewBox (si absent ou incohérent)
  - Simplifier les groupes vides (<g> sans enfants)
  - Supprimer les métadonnées Recraft (commentaires, xmlns inutiles)
  - Optimiser les attributs redondants (fill="none" sur g parent)
  - Réduire la taille textuelle (espaces, sauts de ligne)

Opérations de FLAG uniquement :
  - Rectangle couvrant tout le viewBox (fond suspect)
  - Formes à opacité 0 ou fill="none" stroke="none"
  - Shapes très grands (> 95% viewBox) avec fill opaque
"""

from __future__ import annotations
import re
from typing import Tuple, List


# ─── Regex helpers ────────────────────────────────────────────────────────────

_VIEWBOX_RE  = re.compile(r'viewBox=["\']([^"\']+)["\']', re.IGNORECASE)
_WIDTH_RE    = re.compile(r'\bwidth=["\']([^"\']+)["\']', re.IGNORECASE)
_HEIGHT_RE   = re.compile(r'\bheight=["\']([^"\']+)["\']', re.IGNORECASE)
_EMPTY_G_RE  = re.compile(r'<g[^>]*>\s*</g>', re.IGNORECASE)
_COMMENT_RE  = re.compile(r'<!--.*?-->', re.DOTALL)

# Détection fond suspect : rect couvrant tout le viewBox
_BG_RECT_RE = re.compile(
    r'<rect[^>]+'
    r'(?:x=["\']0["\'][^>]+y=["\']0["\']|y=["\']0["\'][^>]+x=["\']0["\'])'
    r'[^>]*/?>',
    re.IGNORECASE
)


# ─── Normalisation viewBox ────────────────────────────────────────────────────

def _normalize_viewbox(svg: str) -> str:
    """Ajoute viewBox="0 0 100 100" si absent ; conserve l'existant sinon."""
    if not _VIEWBOX_RE.search(svg):
        svg = svg.replace("<svg", '<svg viewBox="0 0 100 100"', 1)
    return svg


# ─── Nettoyage structurel ─────────────────────────────────────────────────────

def _remove_comments(svg: str) -> str:
    return _COMMENT_RE.sub("", svg)


def _remove_empty_groups(svg: str) -> str:
    prev = None
    while prev != svg:
        prev = svg
        svg = _EMPTY_G_RE.sub("", svg)
    return svg


def _compact_whitespace(svg: str) -> str:
    svg = re.sub(r"\n\s*\n", "\n", svg)
    svg = re.sub(r"  +", " ", svg)
    return svg.strip()


# ─── Détection de flags ───────────────────────────────────────────────────────

def _detect_flags(svg: str) -> List[str]:
    """Détecte des anomalies sans rien supprimer. Retourne une liste de warnings."""
    flags = []

    # Fond rectangulaire couvrant x=0 y=0
    if _BG_RECT_RE.search(svg):
        flags.append(
            "FLAG_BG_RECT: rectangle at (0,0) detected — possible background fill. "
            "Review manually before export."
        )

    # Shapes invisibles (opacity:0 ou fill="none" stroke="none")
    if re.search(r'opacity\s*:\s*0', svg) or re.search(r"opacity=['\"]0['\"]", svg):
        flags.append(
            "FLAG_INVISIBLE_SHAPE: element with opacity=0 detected. "
            "Likely Recraft artifact — review manually."
        )

    # Rect très large sans x/y (peut être un fond implicite)
    large_rect = re.search(
        r'<rect[^>]+(?:width=["\'](?:100%|100)["\']|height=["\'](?:100%|100)["\'])',
        svg, re.IGNORECASE
    )
    if large_rect:
        flags.append(
            "FLAG_FULL_SIZE_RECT: full-width/height rect detected — may be a background. "
            "Review before production use."
        )

    return flags


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def optimize_svg(raw_svg: str) -> Tuple[str, List[str]]:
    """
    Normalise et optimise un SVG Recraft.

    Returns:
        (optimized_svg, flags)
        flags : liste de warnings (jamais de suppression implicite)
    """
    svg = raw_svg

    # Étapes de nettoyage (non destructif)
    svg = _remove_comments(svg)
    svg = _normalize_viewbox(svg)
    svg = _remove_empty_groups(svg)
    svg = _compact_whitespace(svg)

    # Détection flags
    flags = _detect_flags(svg)

    return svg, flags
