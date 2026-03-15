"""
palette_generator.color_scale_generator
─────────────────────────────────────────
Génère les scales tonales 100→900 pour chaque couleur de base.

La progression suit une courbe non-linéaire :
  100 = très clair (L≈0.97)
  200 = clair (L≈0.90)
  300 = clair-moyen (L≈0.75)
  400 = moyen-clair (L≈0.60)
  500 = couleur de base (L inchangée)
  600 = moyen-foncé (L≈0.42)
  700 = foncé (L≈0.30)
  800 = très foncé (L≈0.20)
  900 = presque noir (L≈0.10)

La saturation est légèrement réduite aux extrêmes (comportement Adobe/Tailwind).
"""

from __future__ import annotations
from typing import Dict

from .schemas import ColorValue, TonalScale
from .color_utils import hex_to_hsl, hsl_to_hex, make_color, normalize_hex


# Lightness cible par step (100..900)
_LIGHTNESS_MAP: Dict[int, float] = {
    100: 0.970,
    200: 0.900,
    300: 0.750,
    400: 0.600,
    500: None,    # valeur de base conservée
    600: 0.420,
    700: 0.300,
    800: 0.200,
    900: 0.100,
}

# Facteur de saturation par step (légère réduction aux extrêmes)
_SAT_FACTOR: Dict[int, float] = {
    100: 0.40,
    200: 0.55,
    300: 0.70,
    400: 0.85,
    500: 1.00,
    600: 0.95,
    700: 0.90,
    800: 0.85,
    900: 0.75,
}


def generate_scale(base_hex: str, name: str = "color") -> TonalScale:
    """
    Génère la scale 100→900 depuis une couleur hex.

    Args:
        base_hex:   Couleur de base
        name:       Nom sémantique (ex: "primary_blue", "accent_coral")

    Returns:
        TonalScale avec 9 shades
    """
    base_hex = normalize_hex(base_hex)
    h, s, l_base = hex_to_hsl(base_hex)

    shades: Dict[int, ColorValue] = {}
    for step in range(100, 1000, 100):
        target_l = _LIGHTNESS_MAP[step]
        l = l_base if target_l is None else target_l
        sat = s * _SAT_FACTOR[step]

        shade_hex = hsl_to_hex(h, max(0.0, min(1.0, sat)), max(0.0, min(1.0, l)))
        shades[step] = make_color(
            shade_hex,
            name=f"{name}_{step}",
            role="scale",
        )

    return TonalScale(base_hex=base_hex, base_name=name, shades=shades)


def scales_to_tokens(scale: TonalScale) -> Dict[str, str]:
    """
    Convertit une TonalScale en design tokens plats.
    Ex : {"color.primary_blue.500": "#3B82F6"}
    """
    return {
        f"color.{scale.base_name}.{step}": cv.hex
        for step, cv in scale.shades.items()
    }
