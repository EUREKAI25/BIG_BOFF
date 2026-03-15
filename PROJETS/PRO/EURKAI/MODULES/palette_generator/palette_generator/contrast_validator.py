"""
palette_generator.contrast_validator
──────────────────────────────────────
Validation WCAG + génération de palette ui_safe.

Paires de contraste vérifiées :
  - text_on_background
  - accent_on_background
  - button_text_on_button

Niveaux :
  AA  : texte normal ≥ 4.5:1, texte large ≥ 3:1
  AAA : texte normal ≥ 7:1

Correction auto : si une paire échoue, on ajuste la lightness
de la couleur de premier plan par pas de 5% jusqu'à satisfaction.
"""

from __future__ import annotations
from typing import Optional

from .schemas import (
    Palette, AccessibilityReport, ContrastCheck, WCAGLevel, ColorValue
)
from .color_utils import (
    contrast_ratio, make_color, hex_to_hsl, hsl_to_hex,
    darken, lighten, best_text_color
)


# ─── Seuils WCAG ─────────────────────────────────────────────────────────────

_THRESHOLDS = {
    WCAGLevel.AA:  {"normal": 4.5, "large": 3.0},
    WCAGLevel.AAA: {"normal": 7.0, "large": 4.5},
}


# ─── Validation d'une paire ──────────────────────────────────────────────────

def check_pair(label: str, fg_hex: str, bg_hex: str) -> ContrastCheck:
    ratio = contrast_ratio(fg_hex, bg_hex)
    return ContrastCheck(
        pair=label,
        fg_hex=fg_hex,
        bg_hex=bg_hex,
        ratio=round(ratio, 2),
        aa_pass=ratio >= 4.5,
        aaa_pass=ratio >= 7.0,
    )


# ─── Correction auto ─────────────────────────────────────────────────────────

def _adjust_to_meet_ratio(fg_hex: str, bg_hex: str, target_ratio: float) -> str:
    """
    Ajuste la lightness de fg_hex par pas de 5% pour atteindre target_ratio.
    Essaie d'abord d'assombrir, puis d'éclaircir.
    Retourne le fg_hex corrigé ou l'original si impossible.
    """
    from .color_utils import relative_luminance, hex_to_rgb
    bg_lum = relative_luminance(*hex_to_rgb(bg_hex))

    # Assombrir
    candidate = fg_hex
    for _ in range(20):
        r = contrast_ratio(candidate, bg_hex)
        if r >= target_ratio:
            return candidate
        candidate = darken(candidate, 0.05)

    # Éclaircir
    candidate = fg_hex
    for _ in range(20):
        r = contrast_ratio(candidate, bg_hex)
        if r >= target_ratio:
            return candidate
        candidate = lighten(candidate, 0.05)

    return fg_hex  # fallback : original


# ─── Validation d'une palette ────────────────────────────────────────────────

def validate_palette(
    palette: Palette,
    level: WCAGLevel = WCAGLevel.AA,
) -> AccessibilityReport:
    """
    Vérifie les paires de contraste clés d'une palette.
    Retourne un AccessibilityReport.
    """
    bg = palette.neutral[0].hex if palette.neutral else "#FFFFFF"
    text_color = best_text_color(bg)
    checks = []

    # text vs background
    if palette.primary:
        checks.append(check_pair("text_on_background", text_color, bg))

    # accent vs background
    if palette.accent:
        checks.append(check_pair("accent_on_background", palette.accent[0].hex, bg))

    # primary (bouton) vs text du bouton
    if palette.primary:
        btn_bg = palette.primary[0].hex
        btn_text = best_text_color(btn_bg)
        checks.append(check_pair("button_text_on_button", btn_text, btn_bg))

    threshold = _THRESHOLDS[level]["normal"]
    all_aa  = all(c.ratio >= 4.5 for c in checks)
    all_aaa = all(c.ratio >= 7.0 for c in checks)

    return AccessibilityReport(
        checks=checks,
        all_aa_pass=all_aa,
        all_aaa_pass=all_aaa,
    )


# ─── Génération palette ui_safe ───────────────────────────────────────────────

def generate_ui_safe(
    palette: Palette,
    level: WCAGLevel = WCAGLevel.AA,
) -> Palette:
    """
    Produit une variante ui_safe de la palette où toutes les paires
    de contraste clés respectent le niveau WCAG demandé.
    Les couleurs originales sont ajustées minimalement.
    """
    target = _THRESHOLDS[level]["normal"]
    bg = palette.neutral[0].hex if palette.neutral else "#FFFFFF"

    # Corriger les primaires si nécessaire
    safe_primary = []
    for cv in palette.primary:
        if contrast_ratio(cv.hex, bg) < target:
            corrected = _adjust_to_meet_ratio(cv.hex, bg, target)
            safe_primary.append(make_color(corrected, name=cv.name, role=cv.role))
        else:
            safe_primary.append(cv)

    # Corriger les accents
    safe_accent = []
    for cv in palette.accent:
        if contrast_ratio(cv.hex, bg) < target:
            corrected = _adjust_to_meet_ratio(cv.hex, bg, target)
            safe_accent.append(make_color(corrected, name=cv.name, role=cv.role))
        else:
            safe_accent.append(cv)

    return Palette(
        harmony="ui_safe",
        primary=safe_primary,
        secondary=palette.secondary,
        accent=safe_accent,
        neutral=palette.neutral,
        tonal_scales=palette.tonal_scales,
    )
