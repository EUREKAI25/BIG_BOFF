"""
design_dna_resolver.style_mapper
──────────────────────────────────
Mappe un StyleArchetype vers tous les hints stylistiques
consommés par les modules aval.

Chaque archétype définit :
  typography_style   → font_generator
  icon_style         → logo_generator, icon_font_generator
  layout_style       → webdesign_generator
  visual_style       → webdesign_generator, media_generator
  image_style        → image_generator, media_generator
  composition_style  → logo_generator
  motion_energy      → media_generator
  logo_structure     → logo_generator (LogoStructure value)
  wordmark_weight    → logo_generator
  palette_bias       → color_psychology_engine → palette_generator
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .schemas import PaletteBias


@dataclass
class ArchetypeStyleProfile:
    typography_style:    str
    icon_style:          str
    layout_style:        str
    visual_style:        str
    image_style:         str
    composition_style:   str
    motion_energy:       str
    logo_structure:      str          # LogoStructure value
    wordmark_weight:     str
    palette_bias:        PaletteBias


_PROFILES: dict[str, ArchetypeStyleProfile] = {

    "luxury_minimal": ArchetypeStyleProfile(
        typography_style="display_serif",
        icon_style="line_thin",
        layout_style="spacious_minimal",
        visual_style="minimal_luxury",
        image_style="high_fashion_photography",
        composition_style="centered_balanced",
        motion_energy="subtle",
        logo_structure="wordmark",
        wordmark_weight="light",
        palette_bias=PaletteBias(
            preferred_colors=["black", "ivory", "deep_charcoal"],
            accent_candidates=["gold", "rose_gold", "platinum"],
            neutral_candidates=["warm_ivory", "cream", "taupe"],
            avoid_colors=["neon", "bright_yellow", "lime"],
            saturation_level="low",
            color_temperature="neutral",
        ),
    ),

    "startup_clean": ArchetypeStyleProfile(
        typography_style="geometric_sans",
        icon_style="line",
        layout_style="clean_grid",
        visual_style="minimal_tech",
        image_style="soft_light_photography",
        composition_style="balanced_asymmetric",
        motion_energy="moderate",
        logo_structure="icon_wordmark",
        wordmark_weight="medium",
        palette_bias=PaletteBias(
            preferred_colors=["electric_blue", "navy", "indigo"],
            accent_candidates=["cyan", "teal", "violet"],
            neutral_candidates=["cool_gray", "off_white", "slate"],
            avoid_colors=["warm_brown", "mustard", "terracotta"],
            saturation_level="medium",
            color_temperature="cool",
        ),
    ),

    "editorial_magazine": ArchetypeStyleProfile(
        typography_style="display_serif_editorial",
        icon_style="minimal_filled",
        layout_style="editorial_asymmetric",
        visual_style="editorial_bold",
        image_style="editorial_fashion_photography",
        composition_style="dynamic_asymmetric",
        motion_energy="moderate",
        logo_structure="wordmark",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["black", "deep_red", "ivory"],
            accent_candidates=["gold", "burgundy", "blush"],
            neutral_candidates=["off_white", "warm_gray", "cream"],
            avoid_colors=["neon", "lime", "electric_blue"],
            saturation_level="medium",
            color_temperature="warm",
        ),
    ),

    "tech_futurist": ArchetypeStyleProfile(
        typography_style="condensed_tech_sans",
        icon_style="duotone_neon",
        layout_style="dark_grid",
        visual_style="dark_futurist",
        image_style="3d_render_photography",
        composition_style="dynamic_diagonal",
        motion_energy="dynamic",
        logo_structure="abstract_symbol",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["near_black", "electric_purple", "electric_blue"],
            accent_candidates=["neon_cyan", "magenta", "electric_green"],
            neutral_candidates=["dark_gray", "charcoal"],
            avoid_colors=["warm_beige", "terracotta", "ivory"],
            saturation_level="vivid",
            color_temperature="cool",
        ),
    ),

    "creative_studio": ArchetypeStyleProfile(
        typography_style="expressive_display",
        icon_style="illustrated_expressive",
        layout_style="fluid_creative",
        visual_style="vibrant_expressive",
        image_style="colorful_lifestyle_photography",
        composition_style="fluid_asymmetric",
        motion_energy="dynamic",
        logo_structure="icon_wordmark",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["coral", "electric_blue", "lime"],
            accent_candidates=["magenta", "violet", "yellow"],
            neutral_candidates=["off_white", "near_black"],
            avoid_colors=["corporate_navy", "muted_gray"],
            saturation_level="vivid",
            color_temperature="warm",
        ),
    ),

    "brutalist": ArchetypeStyleProfile(
        typography_style="grotesque_bold",
        icon_style="solid_minimal",
        layout_style="raw_asymmetric",
        visual_style="brutalist_raw",
        image_style="raw_photography",
        composition_style="tense_asymmetric",
        motion_energy="subtle",
        logo_structure="wordmark",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["near_black", "white", "concrete_gray"],
            accent_candidates=["bright_red", "electric_yellow"],
            neutral_candidates=["concrete_gray", "off_white"],
            avoid_colors=["pastel", "blush", "soft_teal"],
            saturation_level="low",
            color_temperature="neutral",
        ),
    ),

    "organic_natural": ArchetypeStyleProfile(
        typography_style="humanist_sans_organic",
        icon_style="organic_line",
        layout_style="breathing_organic",
        visual_style="organic_warm",
        image_style="natural_light_photography",
        composition_style="organic_balanced",
        motion_energy="subtle",
        logo_structure="emblem",
        wordmark_weight="light",
        palette_bias=PaletteBias(
            preferred_colors=["forest_green", "sage", "earth_brown"],
            accent_candidates=["terracotta", "warm_yellow", "sky_blue"],
            neutral_candidates=["cream", "linen", "off_white"],
            avoid_colors=["neon", "electric", "cold_blue"],
            saturation_level="medium",
            color_temperature="warm",
        ),
    ),

    "playful_brand": ArchetypeStyleProfile(
        typography_style="rounded_sans",
        icon_style="filled_rounded",
        layout_style="card_playful",
        visual_style="colorful_friendly",
        image_style="bright_lifestyle_photography",
        composition_style="dynamic_centered",
        motion_energy="dynamic",
        logo_structure="mascot",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["bright_red", "sky_blue", "sunny_yellow"],
            accent_candidates=["lime", "coral", "purple"],
            neutral_candidates=["white", "cream"],
            avoid_colors=["dark", "black", "corporate_gray"],
            saturation_level="vivid",
            color_temperature="warm",
        ),
    ),

    "corporate_pro": ArchetypeStyleProfile(
        typography_style="transitional_sans",
        icon_style="outlined",
        layout_style="structured_grid",
        visual_style="corporate_clean",
        image_style="professional_photography",
        composition_style="structured_balanced",
        motion_energy="none",
        logo_structure="icon_wordmark",
        wordmark_weight="medium",
        palette_bias=PaletteBias(
            preferred_colors=["navy", "deep_blue", "charcoal"],
            accent_candidates=["gold", "teal", "cool_gray"],
            neutral_candidates=["off_white", "light_gray", "warm_white"],
            avoid_colors=["neon", "lime", "hot_pink"],
            saturation_level="low",
            color_temperature="cool",
        ),
    ),

    "premium_craft": ArchetypeStyleProfile(
        typography_style="serif_artisan",
        icon_style="etched_line",
        layout_style="editorial_rich",
        visual_style="craft_premium",
        image_style="product_texture_photography",
        composition_style="centered_balanced",
        motion_energy="subtle",
        logo_structure="emblem",
        wordmark_weight="medium",
        palette_bias=PaletteBias(
            preferred_colors=["deep_green", "burgundy", "warm_black"],
            accent_candidates=["gold", "copper", "sage"],
            neutral_candidates=["cream", "linen", "warm_gray"],
            avoid_colors=["neon", "electric_blue", "cold_gray"],
            saturation_level="medium",
            color_temperature="warm",
        ),
    ),

    "bold_challenger": ArchetypeStyleProfile(
        typography_style="condensed_bold_sans",
        icon_style="solid_bold",
        layout_style="high_contrast_grid",
        visual_style="bold_high_contrast",
        image_style="action_photography",
        composition_style="diagonal_dynamic",
        motion_energy="dynamic",
        logo_structure="abstract_symbol",
        wordmark_weight="bold",
        palette_bias=PaletteBias(
            preferred_colors=["black", "electric_blue", "deep_red"],
            accent_candidates=["neon_yellow", "orange", "cyan"],
            neutral_candidates=["dark_gray", "charcoal"],
            avoid_colors=["pastel", "ivory", "blush"],
            saturation_level="high",
            color_temperature="neutral",
        ),
    ),

    "warm_human": ArchetypeStyleProfile(
        typography_style="humanist_rounded_sans",
        icon_style="friendly_filled",
        layout_style="open_breathing",
        visual_style="warm_accessible",
        image_style="people_candid_photography",
        composition_style="organic_balanced",
        motion_energy="subtle",
        logo_structure="icon_wordmark",
        wordmark_weight="medium",
        palette_bias=PaletteBias(
            preferred_colors=["warm_orange", "teal", "sage_green"],
            accent_candidates=["terracotta", "blush", "warm_yellow"],
            neutral_candidates=["cream", "warm_white", "light_beige"],
            avoid_colors=["cold_gray", "black_dominant", "neon"],
            saturation_level="medium",
            color_temperature="warm",
        ),
    ),
}

_FALLBACK = _PROFILES["startup_clean"]


def get_style_profile(archetype: str) -> ArchetypeStyleProfile:
    return _PROFILES.get(archetype, _FALLBACK)


def list_archetypes() -> list[str]:
    return sorted(_PROFILES.keys())
