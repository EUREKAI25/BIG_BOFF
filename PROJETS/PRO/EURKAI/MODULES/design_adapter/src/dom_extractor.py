"""
dom_extractor.py
Analyse le DOM HTML pour extraire des signaux de style complémentaires au CSS.
Détecte les frameworks, les CSS variables inline, et les couleurs d'éléments clés.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional

from .models import DOMSignals, ColorSignal
from .css_extractor import normalize_color


# ── Détection de frameworks ───────────────────────────────────────────────────

_FRAMEWORK_PATTERNS: list[tuple[str, str]] = [
    (r'bootstrap', "bootstrap"),
    (r'tailwind|tw-', "tailwind"),
    (r'bulma', "bulma"),
    (r'foundation', "foundation"),
    (r'materialize', "materialize"),
    (r'chakra|mui|antd|shadcn', "ui-library"),
    (r'uikit', "uikit"),
]


def _detect_framework(html: str) -> str | None:
    lower = html[:50_000].lower()  # Chercher dans les premiers 50k chars
    for pattern, name in _FRAMEWORK_PATTERNS:
        if re.search(pattern, lower):
            return name
    return None


# ── Extraction des CSS variables dans <style> inline ─────────────────────────

_RE_VAR_DEF = re.compile(r'--([\w-]+)\s*:\s*([^;}\n]+)', re.MULTILINE)
_RE_CSS_VAR_USE = re.compile(r'var\(--([\w-]+)\)')


def _extract_style_vars(html: str) -> dict[str, str]:
    """Extrait les CSS custom properties dans les blocs <style> du HTML."""
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    vars_found: dict[str, str] = {}
    for block in style_blocks:
        for m in _RE_VAR_DEF.finditer(block):
            vars_found[m.group(1)] = m.group(2).strip()
    return vars_found


# ── Parser HTML léger ─────────────────────────────────────────────────────────

class _StyleParser(HTMLParser):
    """Parser HTML minimal pour extraire les attributs style des éléments."""

    _ROLE_TAGS = {"button", "a", "h1", "h2", "h3", "h4", "nav", "header", "footer", "p", "body"}
    _COLOR_PROPS = {"background", "background-color", "color", "border-color"}

    def __init__(self):
        super().__init__()
        self.elements: dict[str, list[dict]] = {}  # tag → [{class, style, color_hints}]
        self._meta_colors: list[tuple[str, str]] = []  # (context, hex)

    def handle_starttag(self, tag: str, attrs: list):
        tag = tag.lower()
        if tag not in self._ROLE_TAGS:
            return

        attr_dict = dict(attrs)
        style = attr_dict.get("style", "")
        classes = attr_dict.get("class", "")

        hints: dict[str, str] = {}
        if style:
            for m in re.finditer(r'([\w-]+)\s*:\s*([^;]+)', style):
                prop  = m.group(1).strip().lower()
                value = m.group(2).strip()
                if prop in self._COLOR_PROPS:
                    hex_c = normalize_color(value)
                    if hex_c:
                        hints[prop] = hex_c

        entry = {"class": classes, "style": style, "color_hints": hints}
        self.elements.setdefault(tag, []).append(entry)

    def error(self, message):
        pass  # Ignorer les erreurs de parsing HTML


def _parse_elements(html: str) -> dict[str, list[dict]]:
    parser = _StyleParser()
    try:
        parser.feed(html[:200_000])  # Limiter pour les très grandes pages
    except Exception:
        pass
    return parser.elements


# ── Heuristiques d'extraction de couleurs depuis le DOM ──────────────────────

def _guess_primary_from_elements(elements: dict) -> Optional[str]:
    """Cherche la couleur primaire dans les boutons et liens."""
    for tag in ("button", "a"):
        for el in elements.get(tag, []):
            hints = el.get("color_hints", {})
            bg = hints.get("background-color") or hints.get("background")
            if bg and not _is_neutral(bg):
                return bg
    return None


def _guess_text_from_elements(elements: dict) -> Optional[str]:
    """Cherche la couleur de texte principale dans p, body."""
    for tag in ("p", "body"):
        for el in elements.get(tag, []):
            hints = el.get("color_hints", {})
            color = hints.get("color")
            if color:
                return color
    return None


def _guess_bg_from_elements(elements: dict) -> Optional[str]:
    """Cherche le background principal."""
    for tag in ("body",):
        for el in elements.get(tag, []):
            hints = el.get("color_hints", {})
            bg = hints.get("background-color") or hints.get("background")
            if bg:
                return bg
    return None


def _is_neutral(hex_color: str) -> bool:
    """Retourne True si la couleur est proche du blanc/noir/gris."""
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        avg = (r + g + b) / 3
        diff = max(abs(r - g), abs(g - b), abs(r - b))
        return avg > 235 or avg < 20 or diff < 15
    except Exception:
        return True


# ── Détection de polices Google Fonts depuis les links ───────────────────────

_RE_GF_FAMILY = re.compile(r'family=([A-Za-z+]+)', re.IGNORECASE)


def _detect_google_fonts(html: str) -> list[str]:
    """Détecte les polices Google Fonts depuis les <link> tags."""
    links = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    families: list[str] = []
    for link in links:
        if "fonts.googleapis.com" in link or "fonts.gstatic.com" in link:
            for m in _RE_GF_FAMILY.finditer(link):
                family = m.group(1).replace("+", " ").title()
                if family not in families:
                    families.append(family)
    return families


# ── Point d'entrée public ─────────────────────────────────────────────────────

def extract(html: str) -> DOMSignals:
    """
    Analyse le DOM HTML et retourne des signaux de style.

    Args:
        html: Contenu HTML complet de la page

    Returns:
        DOMSignals avec framework, variables CSS, hints couleurs/polices
    """
    signals = DOMSignals()

    # Framework
    signals.detected_framework = _detect_framework(html)

    # CSS variables inline
    signals.existing_css_vars = _extract_style_vars(html)

    # Éléments DOM
    elements = _parse_elements(html)

    # Hints couleurs depuis inline styles
    primary = _guess_primary_from_elements(elements)
    if primary:
        signals.color_hints["primary"] = primary

    text = _guess_text_from_elements(elements)
    if text:
        signals.color_hints["text"] = text

    bg = _guess_bg_from_elements(elements)
    if bg:
        signals.color_hints["background"] = bg

    # Polices Google Fonts
    gf = _detect_google_fonts(html)
    if gf:
        signals.font_hints["google_fonts"] = gf[0]
        if len(gf) > 1:
            signals.font_hints["google_fonts_secondary"] = gf[1]

    # Variables CSS existantes qui mappent vers des couleurs
    for name, value in signals.existing_css_vars.items():
        hex_c = normalize_color(value.split(" ")[0])
        if hex_c:
            # Essayer d'inférer le rôle depuis le nom de la variable
            lower = name.lower()
            if any(k in lower for k in ("primary", "brand", "main", "accent")):
                signals.color_hints.setdefault("primary", hex_c)
            elif any(k in lower for k in ("secondary", "sub")):
                signals.color_hints.setdefault("secondary", hex_c)
            elif any(k in lower for k in ("text", "body", "foreground", "fg")):
                signals.color_hints.setdefault("text", hex_c)
            elif any(k in lower for k in ("bg", "background", "surface")):
                signals.color_hints.setdefault("background", hex_c)
            elif any(k in lower for k in ("border", "divider", "separator")):
                signals.color_hints.setdefault("border", hex_c)

    return signals
