"""
palette_generator.metal_palette_generator
───────────────────────────────────────────
Génère des palettes métal inspirées de finitions matériaux.
La palette reste cohérente avec la teinte d'entrée.

Approche :
  Chaque métal a une base de teinte neutre (ex: silver ≈ H:220, S:0.05).
  On blende légèrement cette base avec la teinte d'entrée (~20%).
  On dérive ensuite base_tones, highlights, shadows, accents.
"""

from __future__ import annotations

from .schemas import ColorValue, MetalFinish, MetalPalette
from .color_utils import (
    make_color, hex_to_hsl, hsl_to_hex, tint, shade,
    darken, lighten, set_saturation
)


# ─── Profils de base des métaux ───────────────────────────────────────────────
# (H, S, L) — teinte de référence du métal

_METAL_PROFILES: dict[MetalFinish, dict] = {
    MetalFinish.SILVER: {
        "hue": 220, "sat": 0.05, "light": 0.75,
        "highlight_l": 0.94, "shadow_l": 0.45,
        "accent": "#E8EAF0",
    },
    MetalFinish.CHROME: {
        "hue": 210, "sat": 0.04, "light": 0.80,
        "highlight_l": 0.97, "shadow_l": 0.35,
        "accent": "#F0F2F5",
    },
    MetalFinish.GOLD: {
        "hue": 43, "sat": 0.65, "light": 0.52,
        "highlight_l": 0.82, "shadow_l": 0.28,
        "accent": "#FFF8DC",
    },
    MetalFinish.ROSE_GOLD: {
        "hue": 12, "sat": 0.35, "light": 0.68,
        "highlight_l": 0.88, "shadow_l": 0.38,
        "accent": "#FFE4E1",
    },
    MetalFinish.COPPER: {
        "hue": 20, "sat": 0.60, "light": 0.50,
        "highlight_l": 0.78, "shadow_l": 0.25,
        "accent": "#FFE0CC",
    },
    MetalFinish.BRASS: {
        "hue": 38, "sat": 0.50, "light": 0.45,
        "highlight_l": 0.72, "shadow_l": 0.22,
        "accent": "#FFF3CC",
    },
    MetalFinish.GUNMETAL: {
        "hue": 210, "sat": 0.12, "light": 0.28,
        "highlight_l": 0.55, "shadow_l": 0.12,
        "accent": "#C8D0D8",
    },
    MetalFinish.TITANIUM: {
        "hue": 200, "sat": 0.08, "light": 0.55,
        "highlight_l": 0.80, "shadow_l": 0.25,
        "accent": "#D8DCE0",
    },
}

# Correspondance teinte d'entrée → métal recommandé
_HUE_TO_METAL: list[tuple[float, float, MetalFinish]] = [
    (0,   60,  MetalFinish.ROSE_GOLD),
    (20,  50,  MetalFinish.COPPER),
    (35,  65,  MetalFinish.GOLD),
    (60,  180, MetalFinish.TITANIUM),
    (180, 270, MetalFinish.SILVER),
    (270, 330, MetalFinish.TITANIUM),
    (330, 360, MetalFinish.ROSE_GOLD),
]


def auto_detect_finish(base_hex: str) -> MetalFinish:
    """Détecte automatiquement le métal le plus cohérent avec la teinte d'entrée."""
    h, s, l = hex_to_hsl(base_hex)
    for h_min, h_max, finish in _HUE_TO_METAL:
        if h_min <= h < h_max:
            return finish
    return MetalFinish.SILVER


def generate_metal_palette(base_hex: str, finish: MetalFinish = None) -> MetalPalette:
    """
    Génère une palette métal cohérente avec la couleur d'entrée.

    Args:
        base_hex:   Couleur de la marque
        finish:     Finition métal souhaitée (auto-détectée si None)

    Returns:
        MetalPalette avec base_tones, highlights, shadows, accents
    """
    if finish is None:
        finish = auto_detect_finish(base_hex)

    profile = _METAL_PROFILES[finish]
    h_input, s_input, l_input = hex_to_hsl(base_hex)
    h_metal = profile["hue"]
    s_metal = profile["sat"]
    l_metal = profile["light"]

    # Blend 20% teinte d'entrée dans la teinte métal
    blended_hue = h_metal * 0.80 + h_input * 0.20
    blended_sat = s_metal * 0.90 + s_input * 0.10

    base = hsl_to_hex(blended_hue, blended_sat, l_metal)
    highlight = hsl_to_hex(blended_hue, blended_sat * 0.5, profile["highlight_l"])
    shadow = hsl_to_hex(blended_hue, blended_sat * 1.1, profile["shadow_l"])

    base_tones = [
        make_color(base, name=f"{finish.value}_base", role="primary"),
        make_color(hsl_to_hex(blended_hue, blended_sat, l_metal * 0.85), name=f"{finish.value}_mid", role="primary"),
    ]
    highlights = [
        make_color(highlight, name=f"{finish.value}_highlight", role="accent"),
        make_color(tint(highlight, 0.4), name=f"{finish.value}_shine", role="accent"),
    ]
    shadows = [
        make_color(shadow, name=f"{finish.value}_shadow", role="neutral"),
        make_color(shade(shadow, 0.3), name=f"{finish.value}_deep_shadow", role="neutral"),
    ]
    accents = [
        make_color(profile["accent"], name=f"{finish.value}_accent", role="accent"),
    ]

    return MetalPalette(
        finish=finish,
        base_tones=base_tones,
        highlights=highlights,
        shadows=shadows,
        accent=accents,
    )
