"""
token_mapper.py
Convertit les signaux CSS/DOM en TokenMap Eurkai.

Stratégie de résolution (priorité décroissante) :
  1. CSS variables existantes qui mappent sémantiquement vers un token Eurkai
  2. Hints DOM (inline styles, framework classes)
  3. Signaux CSS classifiés (selector + property)
  4. Analyse fréquentielle des couleurs chromiques
  5. Dérivations (primary → secondary, primary → primary-light/dark)
"""
from __future__ import annotations

import colorsys
import re
from typing import Optional

from .models import CSSSignals, DOMSignals, TokenMap, ColorSignal


# ── Utilitaires couleur ───────────────────────────────────────────────────────

def _parse_hex(c: str) -> tuple[int, int, int]:
    h = c.lstrip("#")
    if len(h) == 3:
        h = "".join(x * 2 for x in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex_to_rgb_str(c: str) -> str:
    r, g, b = _parse_hex(c)
    return f"rgb({r}, {g}, {b})"


def _lighten(c: str, amt: float = 0.12) -> str:
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        nr, ng, nb = colorsys.hls_to_rgb(h, min(1.0, ll + amt), s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


def _darken(c: str, amt: float = 0.12) -> str:
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        nr, ng, nb = colorsys.hls_to_rgb(h, max(0.0, ll - amt), s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


def _complementary(c: str) -> str:
    """Couleur complémentaire (hue + 180°)."""
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        h2 = (h + 0.5) % 1.0
        nr, ng, nb = colorsys.hls_to_rgb(h2, ll, s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


def _split_complement(c: str) -> str:
    """Split-complémentaire (hue + 150°)."""
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        h2 = (h + 0.417) % 1.0
        nr, ng, nb = colorsys.hls_to_rgb(h2, ll, s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


def _is_chromic(c: str) -> bool:
    """Retourne True si la couleur est chromique (pas neutre gris/blanc/noir)."""
    try:
        r, g, b = _parse_hex(c)
        _, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        return s > 0.15 and 0.1 < ll < 0.9
    except Exception:
        return False


def _brightness(c: str) -> float:
    try:
        r, g, b = _parse_hex(c)
        return (r + g + b) / 3 / 255
    except Exception:
        return 0.5


# ── Mapping noms de variables → token Eurkai ──────────────────────────────────

_VAR_NAME_TO_TOKEN: list[tuple[str, str]] = [
    # (pattern in var name, token)
    (r"primary|brand|main|cta|key",       "color_primary"),
    (r"secondary|sub|complement",          "color_secondary"),
    (r"accent|highlight",                  "color_primary"),
    (r"text-?primary|body-?text|foreground","color_text"),
    (r"text-?secondary|muted|subtle-?text","color_text_light"),
    (r"bg|background(?!-color)",           "color_bg"),
    (r"surface|card|panel",               "color_bg_gray"),
    (r"border|divider|separator|stroke",   "color_border"),
    (r"font-?heading|heading-?font",       "font_family_headings"),
    (r"font-?body|body-?font",             "font_family_body"),
]


def _var_name_to_token(var_name: str) -> Optional[str]:
    lower = var_name.lower()
    for pattern, token in _VAR_NAME_TO_TOKEN:
        if re.search(pattern, lower):
            return token
    return None


# ── Extraction du meilleur signal par rôle ────────────────────────────────────

def _best_color_for_role(signals: CSSSignals, role: str) -> Optional[str]:
    """Retourne la couleur la plus confiante pour un rôle donné."""
    candidates = [
        c for c in signals.colors
        if c.role == role and _is_chromic(c.value)
    ]
    if not candidates:
        return None
    # Trier par confidence × log(frequency)
    import math
    best = max(candidates, key=lambda c: c.confidence * math.log(c.frequency + 1))
    return best.value


def _most_frequent_chromic(signals: CSSSignals) -> Optional[str]:
    """Couleur chromique la plus fréquente (fallback pour primary)."""
    chromic = [c for c in signals.colors if _is_chromic(c.value)]
    if not chromic:
        return None
    return max(chromic, key=lambda c: c.frequency).value


def _dominant_radius(signals: CSSSignals) -> dict[str, str]:
    """Retourne les valeurs de border-radius pour chaque rôle."""
    result: dict[str, str] = {}
    for role in ("sm", "md", "lg", "xl"):
        items = [r for r in signals.radii if r.role == role]
        if items:
            # Médiane
            vals = sorted(r.value_px for r in items)
            median = vals[len(vals) // 2]
            result[role] = f"{int(median)}px"
    return result


def _dominant_spacing(signals: CSSSignals) -> Optional[int]:
    """Tente de déduire l'unité de base d'espacement (spacing-unit)."""
    if not signals.spacings:
        return None
    vals = [s.value_px for s in signals.spacings if s.value_px > 0]
    if not vals:
        return None
    # Cherche le GCD approximatif des valeurs (unité de base)
    from math import gcd
    from functools import reduce
    ints = [round(v) for v in vals if 2 <= v <= 64]
    if not ints:
        return 8
    g = reduce(gcd, ints)
    return max(4, min(16, g)) if g > 0 else 8


# ── Google Fonts URL builder ──────────────────────────────────────────────────

_KNOWN_GF_WEIGHTS: dict[str, str] = {
    "inter":              "wght@400;500;600;700",
    "roboto":             "wght@300;400;500;700",
    "open sans":          "wght@400;600;700",
    "montserrat":         "wght@400;600;700;800",
    "poppins":            "wght@400;500;600;700",
    "lato":               "wght@400;700",
    "raleway":            "wght@400;500;600",
    "playfair display":   "wght@400;600;700",
    "lora":               "wght@400;500",
    "merriweather":       "wght@400;700",
    "space grotesk":      "wght@400;600;700",
    "cormorant garamond": "wght@300;400;600",
    "space mono":         "wght@400;700",
    "dm sans":            "wght@400;500;600",
    "plus jakarta sans":  "wght@400;500;600;700",
}


def _build_gf_url(families: list[str]) -> str:
    if not families:
        return ""
    params = []
    for f in families:
        key = f.lower()
        weights = _KNOWN_GF_WEIGHTS.get(key, "wght@400;600;700")
        params.append(f"family={f.replace(' ', '+')}:{weights}")
    return "https://fonts.googleapis.com/css2?" + "&".join(params) + "&display=swap"


# ── Point d'entrée public ─────────────────────────────────────────────────────

def map_to_tokens(
    css_signals: CSSSignals,
    dom_signals: DOMSignals,
) -> tuple[TokenMap, dict[str, str], list[str]]:
    """
    Résout les TokenMap Eurkai depuis les signaux CSS + DOM.

    Returns:
        (TokenMap, source_signals, warnings)
        - TokenMap : valeurs finales pour chaque token
        - source_signals : dict {token: "d'où vient cette valeur"}
        - warnings : liste de messages d'avertissement
    """
    tm = TokenMap()
    sources: dict[str, str] = {}
    warnings: list[str] = []

    # ── 1. CSS variables sémantiques (priorité maximale) ─────────────────────
    for var_name, raw_value in {**css_signals.css_vars, **dom_signals.existing_css_vars}.items():
        token = _var_name_to_token(var_name)
        if not token:
            continue
        # Couleur ?
        from .css_extractor import normalize_color
        hex_c = normalize_color(raw_value.split(" ")[0].strip())
        if hex_c and token.startswith("color_"):
            rgb_v = _hex_to_rgb_str(hex_c) if not hex_c.startswith("rgb") else hex_c
            setattr(tm, token, rgb_v)
            sources[token] = f"var(--{var_name})"
            # Conserver hex pour dérivations
            if token == "color_primary":
                tm.color_primary = hex_c
                sources["color_primary"] = f"var(--{var_name})"
            elif token == "color_secondary":
                tm.color_secondary = hex_c
                sources["color_secondary"] = f"var(--{var_name})"
        elif token.startswith("font_"):
            family = raw_value.strip().strip("'\"").split(",")[0].strip()
            setattr(tm, token, family)
            sources[token] = f"var(--{var_name})"

    # ── 2. Hints DOM (inline styles, framework) ───────────────────────────────
    if "primary" in dom_signals.color_hints and "color_primary" not in sources:
        tm.color_primary = dom_signals.color_hints["primary"]
        sources["color_primary"] = "inline style (button/a)"

    if "text" in dom_signals.color_hints and "color_text" not in sources:
        tm.color_text = _hex_to_rgb_str(dom_signals.color_hints["text"])
        sources["color_text"] = "inline style (body/p)"

    if "background" in dom_signals.color_hints and "color_bg" not in sources:
        tm.color_bg = _hex_to_rgb_str(dom_signals.color_hints["background"])
        sources["color_bg"] = "inline style (body bg)"

    if "border" in dom_signals.color_hints and "color_border" not in sources:
        tm.color_border = _hex_to_rgb_str(dom_signals.color_hints["border"])
        sources["color_border"] = "inline style (border-color)"

    # ── 3. Signaux CSS classifiés ─────────────────────────────────────────────
    role_to_token = {
        "primary":    ("color_primary",    True),
        "secondary":  ("color_secondary",  True),
        "text":       ("color_text",       False),
        "background": ("color_bg",         False),
        "surface":    ("color_bg_gray",    False),
        "border":     ("color_border",     False),
    }
    for role, (token, hex_mode) in role_to_token.items():
        if token in sources:
            continue
        best = _best_color_for_role(css_signals, role)
        if best:
            val = best if hex_mode else _hex_to_rgb_str(best)
            setattr(tm, token, val)
            sources[token] = f"CSS ({role} signal)"

    # ── 4. Fallback fréquentiel pour primary ──────────────────────────────────
    if "color_primary" not in sources:
        best = _most_frequent_chromic(css_signals)
        if best:
            tm.color_primary = best
            sources["color_primary"] = "most frequent chromic color"
        else:
            warnings.append("color_primary: aucune couleur chromique détectée — valeur par défaut Eurkai")

    # ── 5. Dérivations primary → secondary, light, dark ──────────────────────
    primary_hex = tm.color_primary if tm.color_primary.startswith("#") else "#667eea"

    if "color_primary_light" not in sources:
        tm.color_primary_light = _hex_to_rgb_str(_lighten(primary_hex, 0.12))
        sources["color_primary_light"] = f"derivé de primary (+12% lightness)"

    if "color_primary_dark" not in sources:
        tm.color_primary_dark = _hex_to_rgb_str(_darken(primary_hex, 0.12))
        sources["color_primary_dark"] = f"derivé de primary (-12% lightness)"

    if "color_secondary" not in sources:
        tm.color_secondary = _split_complement(primary_hex)
        sources["color_secondary"] = "split-complémentaire de primary"
        warnings.append("color_secondary: pas de couleur secondaire détectée — split-complémentaire utilisée")

    secondary_hex = tm.color_secondary if tm.color_secondary.startswith("#") else _split_complement(primary_hex)
    if "color_secondary_light" not in sources:
        tm.color_secondary_light = _hex_to_rgb_str(_lighten(secondary_hex, 0.12))
        sources["color_secondary_light"] = "derivé de secondary"
    if "color_secondary_dark" not in sources:
        tm.color_secondary_dark = _hex_to_rgb_str(_darken(secondary_hex, 0.12))
        sources["color_secondary_dark"] = "derivé de secondary"

    # Convertir primary/secondary en rgb() pour le CSS final
    if tm.color_primary.startswith("#"):
        tm.color_primary = _hex_to_rgb_str(tm.color_primary)
    if tm.color_secondary.startswith("#"):
        tm.color_secondary = _hex_to_rgb_str(tm.color_secondary)

    # ── 6. Texte et fond : fallbacks ─────────────────────────────────────────
    if "color_text_light" not in sources:
        # Dériver depuis color_text si disponible
        tm.color_text_light = "rgb(113, 128, 150)"  # défaut Eurkai
        sources["color_text_light"] = "valeur par défaut Eurkai"

    if "color_bg_gray" not in sources:
        tm.color_bg_gray = "rgb(247, 250, 252)"
        sources["color_bg_gray"] = "valeur par défaut Eurkai"

    if "color_border" not in sources:
        tm.color_border = "rgb(226, 232, 240)"
        sources["color_border"] = "valeur par défaut Eurkai"

    # ── 7. Typographie ────────────────────────────────────────────────────────
    google_fonts = []
    heading_font = dom_signals.font_hints.get("google_fonts")
    body_font    = dom_signals.font_hints.get("google_fonts_secondary")

    # CSS signals
    heading_from_css = next(
        (f.family for f in css_signals.fonts if f.role == "heading"), None
    )
    body_from_css = next(
        (f.family for f in css_signals.fonts if f.role == "body"), None
    )

    if heading_font or heading_from_css:
        tm.font_family_headings = heading_font or heading_from_css
        sources["font_family_headings"] = "Google Fonts link" if heading_font else "CSS font-family"
        google_fonts.append(tm.font_family_headings)
    else:
        warnings.append("font_family_headings: non détectée — Inter utilisée")

    if body_font or body_from_css:
        tm.font_family_body = body_font or body_from_css
        sources["font_family_body"] = "Google Fonts link" if body_font else "CSS font-family"
        if tm.font_family_body != tm.font_family_headings:
            google_fonts.append(tm.font_family_body)
    else:
        tm.font_family_body = tm.font_family_headings  # même police
        sources["font_family_body"] = "même que headings (fallback)"

    if google_fonts:
        tm.font_google_url = _build_gf_url(google_fonts)
        sources["font_google_url"] = f"généré depuis {google_fonts}"

    # ── 8. Border-radius ─────────────────────────────────────────────────────
    radii = _dominant_radius(css_signals)
    if radii.get("sm"):
        tm.border_radius_sm = radii["sm"]
        sources["border_radius_sm"] = "CSS border-radius (sm)"
    if radii.get("md"):
        tm.border_radius_md = radii["md"]
        sources["border_radius_md"] = "CSS border-radius (md)"
    if radii.get("lg"):
        tm.border_radius_lg = radii["lg"]
        sources["border_radius_lg"] = "CSS border-radius (lg)"
    if radii.get("xl"):
        tm.border_radius_xl = radii["xl"]
        sources["border_radius_xl"] = "CSS border-radius (xl)"

    return tm, sources, warnings
