"""
patch_generator.py
Génère le CSS patch (couche :root override) depuis un TokenMap résolu.

Le patch est une feuille de style autonome qui surcharge les variables Eurkai
pour les aligner sur le style visuel du site analysé.
Aucune modification du site d'origine n'est requise.
"""
from __future__ import annotations

import colorsys
import re
from typing import Optional

from .models import TokenMap


# ── Utilitaires couleur ────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> Optional[tuple[int, int, int]]:
    """Accepte #rrggbb ou rgb(r, g, b)."""
    v = hex_color.strip()
    # Format rgb(r, g, b)
    m = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', v)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    # Format #rrggbb
    h = v.lstrip("#")
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except Exception:
        return None


def _rgb_str(r: int, g: int, b: int) -> str:
    return f"rgb({r}, {g}, {b})"


def _rgba_str(r: int, g: int, b: int, a: float) -> str:
    return f"rgba({r}, {g}, {b}, {a})"


def _shadow_from_primary(hex_primary: str) -> tuple[str, str, str]:
    """Dérive les 3 niveaux d'ombre depuis la couleur primaire."""
    rgb = _hex_to_rgb(hex_primary)
    if rgb is None:
        return (
            "0 1px 3px rgba(0,0,0,0.06)",
            "0 4px 12px rgba(0,0,0,0.08)",
            "0 12px 28px rgba(0,0,0,0.12)",
        )
    r, g, b = rgb
    # Teinter l'ombre avec la couleur primaire (très léger)
    return (
        f"0 1px 3px {_rgba_str(r, g, b, 0.08)}",
        f"0 4px 12px {_rgba_str(r, g, b, 0.12)}",
        f"0 12px 28px {_rgba_str(r, g, b, 0.18)}",
    )


def _focus_ring_from_primary(hex_primary: str) -> str:
    """Génère un focus-ring cohérent depuis la couleur primaire."""
    rgb = _hex_to_rgb(hex_primary)
    if rgb is None:
        return "0 0 0 3px rgba(102,126,234,0.35)"
    r, g, b = rgb
    return f"0 0 0 3px {_rgba_str(r, g, b, 0.35)}"


def _is_dark(hex_color: str) -> bool:
    """Retourne True si la couleur est sombre (pour choisir text-on-primary)."""
    rgb = _hex_to_rgb(hex_color)
    if rgb is None:
        return False
    r, g, b = rgb
    # Luminance relative perçue
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.5


def _text_on(hex_bg: str) -> str:
    """Retourne #ffffff ou #1a1a1a selon la luminosité du fond."""
    return "#ffffff" if _is_dark(hex_bg) else "#1a1a1a"


def _transition_speed_from_mood(mood: Optional[str]) -> tuple[str, str]:
    """Fast/normal transition selon le mood."""
    if mood in ("bold", "energetic", "playful"):
        return "120ms", "220ms"
    if mood in ("luxury", "editorial", "elegant"):
        return "300ms", "500ms"
    return "150ms", "300ms"  # default


# ── Génération du patch CSS ────────────────────────────────────────────────────

_PATCH_HEADER = """\
/*
 * ╔══════════════════════════════════════════════════════╗
 * ║       EURKAI STYLE ADAPTER — CSS Patch Layer         ║
 * ║  Auto-generated — do not edit manually               ║
 * ╚══════════════════════════════════════════════════════╝
 *
 * Ce patch surcharge les variables Eurkai avec les tokens
 * extraits du style visuel du site analysé.
 * Injectez ce fichier APRÈS les styles Eurkai de base.
 */
"""

_SECTION = lambda title: f"\n  /* ── {title} {'─' * (44 - len(title))} */\n"


def generate_patch(
    token_map: TokenMap,
    sources: dict[str, str],
    warnings: list[str],
    *,
    mood: Optional[str] = None,
) -> str:
    """
    Génère la feuille CSS :root{} qui adapte les tokens Eurkai au site analysé.

    Args:
        token_map:  TokenMap résolu (issu de token_mapper.map_to_tokens)
        sources:    Dict token_name → source description (pour commentaires)
        warnings:   Avertissements du token mapper (tokens non résolus, etc.)
        mood:       Mood optionnel pour ajuster transitions

    Returns:
        String CSS complet et documenté
    """
    tm = token_map
    shadow_sm, shadow_md, shadow_lg = _shadow_from_primary(tm.color_primary)
    focus_ring = _focus_ring_from_primary(tm.color_primary)
    text_on_primary = _text_on(tm.color_primary)
    text_on_secondary = _text_on(tm.color_secondary)
    transition_fast, transition_normal = _transition_speed_from_mood(mood)

    lines: list[str] = [_PATCH_HEADER]

    # ── Avertissements en commentaire ─────────────────────────────────────────
    if warnings:
        lines.append("/*\n * AVERTISSEMENTS :\n")
        for w in warnings:
            lines.append(f" *   ⚠  {w}\n")
        lines.append(" */\n")

    lines.append(":root {\n")

    # ── Couleurs primaires ────────────────────────────────────────────────────
    lines.append(_SECTION("Couleurs primaires"))
    lines.append(_token_line("--color-primary",         tm.color_primary,        sources))
    lines.append(_token_line("--color-primary-light",   tm.color_primary_light,  sources))
    lines.append(_token_line("--color-primary-dark",    tm.color_primary_dark,   sources))
    lines.append(_token_line("--color-primary-subtle",  _subtle(tm.color_primary), sources))
    lines.append(_token_line("--color-on-primary",      text_on_primary,         sources))

    # ── Couleurs secondaires ──────────────────────────────────────────────────
    lines.append(_SECTION("Couleurs secondaires"))
    lines.append(_token_line("--color-secondary",       tm.color_secondary,      sources))
    lines.append(_token_line("--color-secondary-light", tm.color_secondary_light,sources))
    lines.append(_token_line("--color-secondary-dark",  tm.color_secondary_dark, sources))
    lines.append(_token_line("--color-on-secondary",    text_on_secondary,       sources))

    # ── Couleurs neutres ──────────────────────────────────────────────────────
    lines.append(_SECTION("Couleurs neutres"))
    lines.append(_token_line("--color-text",            tm.color_text,           sources))
    lines.append(_token_line("--color-text-light",      tm.color_text_light,     sources))
    lines.append(_token_line("--color-text-muted",      _muted(tm.color_text),   sources))
    lines.append(_token_line("--color-bg",              tm.color_bg,             sources))
    lines.append(_token_line("--color-bg-subtle",       tm.color_bg_gray,        sources))
    lines.append(_token_line("--color-border",          tm.color_border,         sources))
    lines.append(_token_line("--color-border-light",    _lighter_border(tm.color_border), sources))

    # ── Typographie ───────────────────────────────────────────────────────────
    lines.append(_SECTION("Typographie"))
    lines.append(_token_line("--font-family-heading",   f'"{tm.font_family_headings}", sans-serif', sources))
    lines.append(_token_line("--font-family-body",      f'"{tm.font_family_body}", sans-serif',     sources))
    if tm.font_family_headings == tm.font_family_body:
        lines.append(_token_line("--font-family-mono",  '"JetBrains Mono", "Fira Code", monospace', sources))

    # ── Rayons ────────────────────────────────────────────────────────────────
    lines.append(_SECTION("Border radius"))
    lines.append(_token_line("--border-radius-sm",  tm.border_radius_sm,  sources))
    lines.append(_token_line("--border-radius-md",  tm.border_radius_md,  sources))
    lines.append(_token_line("--border-radius-lg",  tm.border_radius_lg,  sources))
    lines.append(_token_line("--border-radius-xl",  tm.border_radius_xl,  sources))
    lines.append(_token_line("--border-radius-full","9999px",              sources))

    # ── Ombres ────────────────────────────────────────────────────────────────
    lines.append(_SECTION("Ombres"))
    lines.append(_token_line("--shadow-sm",  shadow_sm,  sources))
    lines.append(_token_line("--shadow-md",  shadow_md,  sources))
    lines.append(_token_line("--shadow-lg",  shadow_lg,  sources))
    lines.append(_token_line("--focus-ring", focus_ring, sources))

    # ── Transitions ───────────────────────────────────────────────────────────
    lines.append(_SECTION("Transitions"))
    lines.append(_token_line("--transition-fast",   f"{transition_fast} ease",   sources))
    lines.append(_token_line("--transition-normal", f"{transition_normal} ease",  sources))
    lines.append(_token_line("--transition-slow",   "600ms ease",                sources))

    lines.append("}\n")

    # ── Google Fonts import ───────────────────────────────────────────────────
    if tm.font_google_url:
        gf_block = (
            "\n/* Google Fonts — adapter injection */\n"
            f'@import url("{tm.font_google_url}");\n'
        )
        lines.insert(1, gf_block)  # juste après le header

    return "".join(lines)


# ── Helpers internes ──────────────────────────────────────────────────────────

def _token_line(name: str, value: str, sources: dict[str, str]) -> str:
    """Génère une ligne `  --token: value; /* source */`."""
    # Nettoyer le nom pour le lookup dans sources (enlever --)
    key = name.lstrip("-").replace("-", "_")
    # Chercher source dans plusieurs variantes de clé
    src = (
        sources.get(name)
        or sources.get(key)
        or sources.get(name.lstrip("-"))
        or ""
    )
    comment = f"  /* ← {src} */" if src else ""
    return f"  {name}: {value};{comment}\n"


def _subtle(hex_color: str) -> str:
    """Génère une version très légère de la couleur (pour backgrounds)."""
    rgb = _hex_to_rgb(hex_color)
    if rgb is None:
        return "rgba(102,126,234,0.08)"
    r, g, b = rgb
    return f"rgba({r},{g},{b},0.08)"


def _muted(hex_color: str) -> str:
    """Génère une version atténuée de la couleur texte."""
    rgb = _hex_to_rgb(hex_color)
    if rgb is None:
        return "rgb(113, 128, 150)"
    r, g, b = rgb
    # Mélange avec gris 50%
    mr = (r + 150) // 2
    mg = (g + 150) // 2
    mb = (b + 150) // 2
    return f"rgb({mr}, {mg}, {mb})"


def _lighter_border(hex_color: str) -> str:
    """Génère une variante plus légère pour les bordures subtiles."""
    rgb = _hex_to_rgb(hex_color)
    if rgb is None:
        return "rgb(237, 242, 247)"
    r, g, b = rgb
    # Pousser vers le blanc
    lr = min(255, r + (255 - r) // 2)
    lg = min(255, g + (255 - g) // 2)
    lb = min(255, b + (255 - b) // 2)
    return f"rgb({lr}, {lg}, {lb})"
