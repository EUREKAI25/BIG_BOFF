"""
palette_generator.bw_palette_generator
────────────────────────────────────────
Génère la variante "black & white design" : false blacks et false whites.

Ces palettes ne sont pas du noir/blanc pur — elles sont les noirs et blancs
utilisés dans le design premium (deep plum, dark navy, ivory, warm cream...).

La sélection des teintes est influencée par la teinte de la couleur de base :
  - Teintes chaudes (H 0..60 ou 300..360) → noirs chauds + blancs crémeux
  - Teintes froides (H 180..270) → noirs froids + blancs neutres/froids
  - Teintes vertes (H 60..180) → noirs forestiers + blancs naturels
"""

from __future__ import annotations

from .schemas import ColorValue, BWVariant
from .color_utils import make_color, hex_to_hsl


# ─── Tables de référence ─────────────────────────────────────────────────────

_FALSE_BLACKS_WARM = [
    ("#1A0F1A", "deep_plum"),
    ("#1C1108", "espresso"),
    ("#1A1A10", "forest_black"),
    ("#1C1917", "warm_graphite"),
]

_FALSE_BLACKS_COOL = [
    ("#0D1B2A", "dark_navy"),
    ("#111827", "slate_black"),
    ("#0F1923", "deep_teal_black"),
    ("#18181B", "cool_graphite"),
]

_FALSE_BLACKS_GREEN = [
    ("#0D1F12", "forest_black"),
    ("#1A1F1A", "dark_moss"),
    ("#121A12", "deep_fern"),
    ("#1C1E18", "military_dark"),
]

_FALSE_WHITES_WARM = [
    ("#FFFFF0", "ivory"),
    ("#FDF8F2", "warm_cream"),
    ("#FAF0E6", "linen"),
    ("#F5F0E8", "parchment"),
]

_FALSE_WHITES_COOL = [
    ("#F0F4F8", "cool_off_white"),
    ("#F8FAFC", "ice_white"),
    ("#EFF6FF", "sky_white"),
    ("#F9FAFB", "neutral_off_white"),
]

_FALSE_WHITES_NEUTRAL = [
    ("#FAFAF9", "near_white"),
    ("#F5F5F4", "warm_gray"),
    ("#F4F4F5", "cool_gray"),
    ("#F9F9F7", "soft_white"),
]


def _hue_category(h: float) -> str:
    if h < 60 or h >= 300:
        return "warm"
    elif 60 <= h < 180:
        return "green"
    else:
        return "cool"


def generate_bw_variant(base_hex: str) -> BWVariant:
    """
    Génère la variante black & white en cohérence avec la teinte de base.
    """
    h, s, l = hex_to_hsl(base_hex)
    category = _hue_category(h)

    if category == "warm":
        blacks_data = _FALSE_BLACKS_WARM
        whites_data = _FALSE_WHITES_WARM
    elif category == "green":
        blacks_data = _FALSE_BLACKS_GREEN
        whites_data = _FALSE_WHITES_NEUTRAL
    else:
        blacks_data = _FALSE_BLACKS_COOL
        whites_data = _FALSE_WHITES_COOL

    false_blacks = [make_color(h, name=name, role="false_black") for h, name in blacks_data]
    false_whites = [make_color(h, name=name, role="false_white") for h, name in whites_data]

    return BWVariant(false_blacks=false_blacks, false_whites=false_whites)
