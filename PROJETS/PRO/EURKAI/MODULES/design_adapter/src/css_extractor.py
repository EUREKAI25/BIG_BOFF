"""
css_extractor.py
Extrait les signaux de style (couleurs, polices, rayons, espacements) depuis un CSS brut.
Zero dépendance externe — uniquement re, colorsys.
"""
from __future__ import annotations

import colorsys
import re
from typing import Optional

from .models import CSSSignals, ColorSignal, FontSignal, RadiusSignal, SpacingSignal


# ── Couleurs nommées CSS ──────────────────────────────────────────────────────

_NAMED: dict[str, str | None] = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000",
    "blue": "#0000ff",  "green": "#008000", "gray": "#808080",
    "grey": "#808080",  "silver": "#c0c0c0","navy": "#000080",
    "teal": "#008080",  "purple": "#800080","orange": "#ffa500",
    "yellow": "#ffff00","pink": "#ffc0cb",  "brown": "#a52a2a",
    "indigo": "#4b0082","violet": "#ee82ee","lime": "#00ff00",
    "transparent": None, "inherit": None, "currentcolor": None,
    "initial": None,    "unset": None,
}

# ── Regex ─────────────────────────────────────────────────────────────────────

_RE_HEX    = re.compile(r'#([0-9a-fA-F]{3,8})\b')
_RE_RGB    = re.compile(r'rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)')
_RE_HSL    = re.compile(r'hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%')
_RE_CSS_VAR= re.compile(r'--[\w-]+\s*:\s*([^;}\n]+)')
_RE_RULE   = re.compile(r'([^{]+)\{([^}]*)\}', re.DOTALL)
_RE_PROP   = re.compile(r'([\w-]+)\s*:\s*([^;]+);?')
_RE_FONT   = re.compile(r"['\"]?([\w\s-]+)['\"]?\s*(?:,|$)")
_RE_PX     = re.compile(r'([\d.]+)px')
_RE_VAR_DEF= re.compile(r'--([\w-]+)\s*:\s*([^;}\n]+)', re.MULTILINE)


# ── Normalisation couleur ─────────────────────────────────────────────────────

def normalize_color(raw: str) -> Optional[str]:
    """Normalise n'importe quelle valeur CSS couleur vers #rrggbb."""
    v = raw.strip().lower()

    if v in _NAMED:
        return _NAMED[v]

    m = _RE_HEX.match(v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        elif len(h) == 8:
            h = h[:6]
        return f"#{h.lower()}"

    m = _RE_RGB.search(v)
    if m:
        r, g, b = int(float(m.group(1))), int(float(m.group(2))), int(float(m.group(3)))
        if r > 255 or g > 255 or b > 255:
            return None
        return f"#{r:02x}{g:02x}{b:02x}"

    m = _RE_HSL.search(v)
    if m:
        h = float(m.group(1)) / 360
        s = float(m.group(2)) / 100
        ll = float(m.group(3)) / 100
        r, g, b = colorsys.hls_to_rgb(h, ll, s)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    return None


def _is_near_white(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r + g + b) / 3 > 235
    except Exception:
        return False


def _is_near_black(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r + g + b) / 3 < 30
    except Exception:
        return False


def _is_near_gray(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        diff = max(abs(r - g), abs(g - b), abs(r - b))
        return diff < 20
    except Exception:
        return False


# ── Classification sémantique des sélecteurs ─────────────────────────────────

_SELECTOR_ROLES: list[tuple[str, str, float]] = [
    # (pattern, role, confidence)
    (r'button|\.btn|input\[type.*submit\]|\.submit', "primary",    0.9),
    (r'\.primary|\.brand|\.accent',                  "primary",    0.85),
    (r'a\b|:link|:visited|\.link',                   "primary",    0.7),
    (r'\.secondary|\.muted',                         "secondary",  0.8),
    (r'body\b|html\b',                               "background", 0.85),
    (r'\.card|\.box|\.panel|section\b|\.container',  "surface",    0.75),
    (r'\.text|p\b|\.body',                           "text",       0.8),
    (r'h[1-6]\b|\.heading|\.title',                  "heading",    0.85),
    (r'\.border|hr\b|\.divider|\.separator',         "border",     0.8),
    (r'nav\b|\.nav|header\b',                        "surface",    0.6),
    (r'footer\b',                                    "background", 0.5),
]

_PROPERTY_ROLES: dict[str, list[str]] = {
    "background":       ["background", "surface"],
    "background-color": ["background", "surface"],
    "color":            ["text"],
    "border-color":     ["border"],
    "border":           ["border"],
    "outline-color":    ["border"],
    "box-shadow":       [],  # ignore
    "text-decoration-color": ["accent"],
}

_GENERIC_FAMILIES = {
    "sans-serif", "serif", "monospace", "cursive", "fantasy",
    "system-ui", "-apple-system", "blinkmacsystemfont",
    "helvetica", "arial", "times", "georgia",
    "ui-sans-serif", "ui-serif", "ui-monospace",
}

_GOOGLE_FONTS = {
    "inter", "roboto", "open sans", "lato", "montserrat", "oswald",
    "poppins", "raleway", "nunito", "playfair display", "merriweather",
    "ubuntu", "source sans pro", "pt sans", "noto sans", "work sans",
    "fira sans", "barlow", "mulish", "josefin sans", "space grotesk",
    "space mono", "dm sans", "karla", "cormorant garamond", "lora",
    "bitter", "crimson text", "EB garamond", "libre baskerville",
    "libre franklin", "source serif pro", "exo 2", "cabin",
    "rubik", "manrope", "outfit", "plus jakarta sans",
}


def _classify_selector(selector: str, prop: str) -> tuple[str, float]:
    """Retourne (role, confidence) pour un sélecteur + propriété."""
    sel_lower = selector.lower()
    prop_lower = prop.lower()

    for pattern, role, conf in _SELECTOR_ROLES:
        if re.search(pattern, sel_lower):
            # Affiner avec la propriété
            allowed = _PROPERTY_ROLES.get(prop_lower, [])
            if allowed and role not in allowed:
                # La propriété ne correspond pas au rôle attendu
                # ex: color on button → c'est la couleur du texte du bouton, pas primary
                if role == "primary" and prop_lower == "color":
                    return "unknown", 0.2
            return role, conf

    return "unknown", 0.2


# ── Extraction des variables CSS ──────────────────────────────────────────────

def _extract_css_vars(css: str) -> dict[str, str]:
    """Extrait les custom properties (--xxx: value)."""
    return {
        m.group(1): m.group(2).strip()
        for m in _RE_VAR_DEF.finditer(css)
    }


# ── Extraction principale ─────────────────────────────────────────────────────

def extract(css: str) -> CSSSignals:
    """
    Parse le CSS et retourne les signaux de style.

    Args:
        css: Contenu CSS brut (concaténation de toutes les feuilles de style)

    Returns:
        CSSSignals avec couleurs, polices, rayons, espacements détectés
    """
    signals = CSSSignals()
    signals.css_vars = _extract_css_vars(css)

    # Compteur de fréquence par valeur normalisée
    color_freq: dict[str, int] = {}
    color_best_role: dict[str, tuple[str, float, str, str]] = {}  # hex → (role, conf, selector, prop)

    for m in _RE_RULE.finditer(css):
        raw_selector = m.group(1).strip()
        body = m.group(2)

        # Nettoyer le sélecteur (première partie avant virgule ou :)
        selector = re.split(r'[,\n]', raw_selector)[0].strip()

        for pm in _RE_PROP.finditer(body):
            prop  = pm.group(1).strip()
            value = pm.group(2).strip()

            # ── Couleurs ─────────────────────────────────────────────────────
            if prop in _PROPERTY_ROLES or prop in (
                "background", "background-color", "color",
                "border-color", "fill", "stroke",
            ):
                raw_colors = re.findall(
                    r'#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|'
                    + r'\b(?:' + '|'.join(_NAMED.keys()) + r')\b',
                    value,
                )
                for rc in raw_colors:
                    hex_c = normalize_color(rc)
                    if hex_c is None:
                        continue
                    # Ignorer blanc/noir quasi-purs sauf s'ils sont pertinents
                    if _is_near_white(hex_c) and "background" not in prop:
                        continue
                    if _is_near_black(hex_c) and "border" not in prop and "color" not in prop:
                        continue

                    color_freq[hex_c] = color_freq.get(hex_c, 0) + 1
                    role, conf = _classify_selector(selector, prop)

                    existing = color_best_role.get(hex_c)
                    if existing is None or conf > existing[1]:
                        color_best_role[hex_c] = (role, conf, selector, prop)

            # ── Polices ───────────────────────────────────────────────────────
            if prop == "font-family":
                families = _RE_FONT.findall(value)
                for fam in families:
                    fam = fam.strip().lower()
                    if fam in _GENERIC_FAMILIES or not fam:
                        continue
                    role = "heading" if re.search(r'h[1-6]\b|\.heading|\.title', selector.lower()) else "body"
                    is_google = fam in _GOOGLE_FONTS

                    # Vérifier doublon
                    existing_families = [f.family.lower() for f in signals.fonts]
                    if fam not in existing_families:
                        signals.fonts.append(FontSignal(
                            family=fam.title(),
                            raw=value,
                            property=prop,
                            selector=selector,
                            role=role,
                            is_google=is_google,
                        ))

            # ── Rayons ────────────────────────────────────────────────────────
            if prop == "border-radius":
                m_px = _RE_PX.search(value)
                if m_px:
                    px = float(m_px.group(1))
                    if 1 <= px <= 100:
                        role = "sm" if px <= 5 else "md" if px <= 12 else "lg" if px <= 24 else "xl"
                        signals.radii.append(RadiusSignal(
                            value_px=px, raw=value, selector=selector, role=role,
                        ))

            # ── Espacements ───────────────────────────────────────────────────
            if prop in ("padding", "margin", "gap", "padding-top", "padding-left", "margin-top"):
                m_px = _RE_PX.search(value)
                if m_px:
                    px = float(m_px.group(1))
                    if 2 <= px <= 128:
                        signals.spacings.append(SpacingSignal(
                            value_px=px, raw=value, property=prop, selector=selector,
                        ))

    # Construire les ColorSignals depuis freq + best_role
    for hex_c, freq in sorted(color_freq.items(), key=lambda x: -x[1]):
        role_info = color_best_role.get(hex_c, ("unknown", 0.2, "", ""))
        signals.colors.append(ColorSignal(
            value=hex_c,
            raw=hex_c,
            property=role_info[3],
            selector=role_info[2],
            role=role_info[0],
            frequency=freq,
            confidence=role_info[1],
        ))

    return signals
