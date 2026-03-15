"""
visual_consistency_validator.palette_checker
─────────────────────────────────────────────
Vérifie la cohérence de la palette générée avec les hints du DesignDNA.

Critères :
- preferred_colors / avoid_colors du palette_bias respectés
- saturation_level cohérente avec le DesignDNA
- color_temperature cohérente
- présence d'au moins une couleur dans la zone "preferred"
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from .schemas import CheckResult, PaletteAsset

# Mapping hue approximate ranges pour détecter la famille de couleur
# hex → teinte approximative → famille sémantique
_COLOR_FAMILIES: Dict[str, List[str]] = {
    "electric_blue":  ["0033ff", "0044ff", "003399", "1a53ff"],
    "navy":           ["001f5c", "002266", "003080", "001a4d"],
    "indigo":         ["4b0082", "3d007a", "6600cc", "5500aa"],
    "cyan":           ["00ffff", "00e5ff", "00cccc", "00bcd4"],
    "teal":           ["008080", "009688", "00897b", "00796b"],
    "violet":         ["8000ff", "7700ee", "6600cc", "9400d3"],
    "deep_red":       ["8b0000", "990000", "cc0000", "aa0000"],
    "crimson":        ["dc143c", "c0392b", "e74c3c", "b71c1c"],
    "gold":           ["ffd700", "ffcc00", "f4d03f", "f1c40f"],
    "amber":          ["ffbf00", "ff8f00", "ffa000", "ffb300"],
    "forest_green":   ["228b22", "2e7d32", "388e3c", "1b5e20"],
    "sage":           ["bccc9a", "a8c090", "9cba88", "8aab76"],
    "terracotta":     ["cc4e2a", "bf4520", "b5400e", "a03a00"],
    "warm_beige":     ["f5e6c8", "f0ddb5", "ece6d5", "e8dcc5"],
    "charcoal":       ["36454f", "2e3a42", "2c3e50", "263238"],
    "slate_gray":     ["708090", "607d8b", "546e7a", "455a64"],
    "off_white":      ["f8f8f8", "fafafa", "f5f5f5", "eeeeee"],
    "black":          ["000000", "111111", "1a1a1a", "0d0d0d"],
    "white":          ["ffffff", "fefefe", "fdfdfd", "fcfcfc"],
}

_SATURATION_LEVELS = ["very_low", "low", "medium", "high", "very_high"]
_TEMPERATURE_VALUES = ["very_cold", "cold", "neutral", "warm", "very_warm"]


def _hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
    """Convertit hex → (h, s, l) en 0-1."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h / 6, s, l


def _estimate_saturation_level(colors: List[str]) -> str:
    """Estime le niveau de saturation moyen d'une liste de couleurs hex."""
    if not colors:
        return "medium"
    saturations = []
    for c in colors:
        try:
            _, s, _ = _hex_to_hsl(c)
            saturations.append(s)
        except Exception:
            continue
    if not saturations:
        return "medium"
    avg = sum(saturations) / len(saturations)
    if avg < 0.15:
        return "very_low"
    if avg < 0.30:
        return "low"
    if avg < 0.55:
        return "medium"
    if avg < 0.75:
        return "high"
    return "very_high"


def _estimate_color_temperature(colors: List[str]) -> str:
    """Estime la température de couleur moyenne (froide/chaude)."""
    if not colors:
        return "neutral"
    warm_count, cold_count = 0, 0
    for c in colors:
        try:
            h, s, _ = _hex_to_hsl(c)
            if s < 0.1:
                continue
            # Hues 0-0.083 (rouge), 0.083-0.167 (orange), 0.167-0.25 (jaune) → chaud
            # Hues 0.5-0.667 (bleu) → froid
            # Hues 0.833-1.0 (magenta/rose) → chaud
            if h < 0.083 or (0.083 <= h < 0.25) or h > 0.833:
                warm_count += 1
            elif 0.5 <= h <= 0.70:
                cold_count += 1
        except Exception:
            continue
    total = warm_count + cold_count
    if total == 0:
        return "neutral"
    ratio = warm_count / total
    if ratio > 0.7:
        return "very_warm" if ratio > 0.85 else "warm"
    if ratio < 0.3:
        return "very_cold" if ratio < 0.15 else "cold"
    return "neutral"


def _saturation_distance(a: str, b: str) -> int:
    """Distance ordinale entre deux niveaux de saturation."""
    try:
        return abs(_SATURATION_LEVELS.index(a) - _SATURATION_LEVELS.index(b))
    except ValueError:
        return 1


def _temperature_distance(a: str, b: str) -> int:
    """Distance ordinale entre deux températures de couleur."""
    try:
        return abs(_TEMPERATURE_VALUES.index(a) - _TEMPERATURE_VALUES.index(b))
    except ValueError:
        return 1


def check_palette(
    asset: PaletteAsset,
    design_dna: Dict[str, Any],
) -> CheckResult:
    """
    Vérifie la cohérence de la palette avec le DesignDNA.

    Returns CheckResult avec score 0..1.
    """
    warnings: List[str] = []
    suggestions: List[str] = []
    details: Dict[str, Any] = {}
    score = 1.0

    palette_bias = design_dna.get("palette_bias") or {}
    preferred    = palette_bias.get("preferred_colors", [])
    avoid        = palette_bias.get("avoid_colors", [])
    dna_sat      = palette_bias.get("saturation_level", "medium")
    dna_temp     = palette_bias.get("color_temperature", "neutral")

    all_colors = (asset.primary_colors or []) + (asset.accent_colors or [])

    # ── Avoid colors ───────────────────────────────────────────────────────────
    # Heuristique simple : couleur "red" → chercher des hues ~0 dans les couleurs
    # On travaille en noms sémantiques car les assets passent souvent des noms
    avoid_hit = [c for c in all_colors if any(av.lower() in c.lower() for av in avoid)]
    if avoid_hit:
        penalty = 0.15 * len(avoid_hit)
        score -= min(penalty, 0.30)
        warnings.append(
            f"Couleur(s) à éviter détectées : {', '.join(avoid_hit)}"
        )
        suggestions.append(
            f"Remplacer {', '.join(avoid_hit)} par des couleurs issues de : {', '.join(preferred[:3])}"
        )

    # ── Preferred colors coverage ──────────────────────────────────────────────
    if preferred:
        # Cherche si au moins une preferred_color famille est représentée
        covered = any(
            any(pref.lower() in c.lower() for c in all_colors)
            for pref in preferred
        )
        details["preferred_coverage"] = covered
        if not covered:
            score -= 0.20
            warnings.append(
                f"Aucune couleur préférée ({', '.join(preferred[:3])}) n'est représentée dans la palette."
            )
            suggestions.append(
                f"Intégrer au moins une couleur parmi : {', '.join(preferred[:3])}"
            )

    # ── Saturation level ──────────────────────────────────────────────────────
    actual_sat = asset.saturation_level or _estimate_saturation_level(all_colors)
    details["saturation_actual"] = actual_sat
    details["saturation_expected"] = dna_sat
    sat_dist = _saturation_distance(actual_sat, dna_sat)
    if sat_dist >= 2:
        penalty = 0.10 * sat_dist
        score -= min(penalty, 0.20)
        warnings.append(
            f"Saturation '{actual_sat}' éloignée du niveau attendu '{dna_sat}'."
        )
        suggestions.append(
            f"Ajuster la saturation vers '{dna_sat}' pour correspondre au DesignDNA."
        )
    elif sat_dist == 1:
        score -= 0.05

    # ── Color temperature ─────────────────────────────────────────────────────
    actual_temp = asset.color_temperature or _estimate_color_temperature(all_colors)
    details["temperature_actual"] = actual_temp
    details["temperature_expected"] = dna_temp
    temp_dist = _temperature_distance(actual_temp, dna_temp)
    if temp_dist >= 2:
        penalty = 0.10 * temp_dist
        score -= min(penalty, 0.20)
        warnings.append(
            f"Température '{actual_temp}' éloignée de '{dna_temp}'."
        )
        suggestions.append(
            f"Orienter la palette vers des tons '{dna_temp}'."
        )
    elif temp_dist == 1:
        score -= 0.05

    score = max(0.0, min(1.0, score))
    return CheckResult(
        checker="palette",
        score=round(score, 3),
        passed=score >= 0.80,
        warnings=warnings,
        suggestions=suggestions,
        details=details,
    )
