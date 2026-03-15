"""
color_psychology_engine.industry_color_map
────────────────────────────────────────────
Mapping secteur → profil coloré conventionnel.

Structure de chaque entrée :
  preferred   : couleurs principales associées au secteur
  accents     : couleurs d'accent courantes
  neutrals    : neutres typiques du secteur
  avoid       : couleurs évitées dans ce secteur (risque)
  saturation  : niveau de saturation habituel
  temperature : warm / neutral / cool
  emotion     : émotion dominante véhiculée
  notes       : rationale

Extensible : ajouter une entrée dans _MAP pour couvrir un nouveau secteur.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IndustryProfile:
    preferred:    List[str]
    accents:      List[str]
    neutrals:     List[str]
    avoid:        List[str]
    saturation:   str             # low / medium / high / vivid
    temperature:  str             # warm / neutral / cool
    emotion:      str
    notes:        str = ""


_MAP: dict[str, IndustryProfile] = {
    "finance": IndustryProfile(
        preferred=["navy", "deep_blue", "midnight_blue", "slate_blue"],
        accents=["gold", "silver", "cyan"],
        neutrals=["cool_gray", "off_white", "charcoal"],
        avoid=["neon_orange", "hot_pink", "acid_green", "lime"],
        saturation="medium",
        temperature="cool",
        emotion="trust",
        notes="Stabilité, confiance, autorité. Bleus profonds dominants.",
    ),
    "fintech": IndustryProfile(
        preferred=["electric_blue", "navy", "indigo", "deep_purple"],
        accents=["cyan", "teal", "neon_blue"],
        neutrals=["dark_slate", "cool_white", "light_gray"],
        avoid=["warm_brown", "olive", "mustard"],
        saturation="high",
        temperature="cool",
        emotion="innovation",
        notes="Tech + finance : bleus vifs, violet, nuances électriques.",
    ),
    "healthcare": IndustryProfile(
        preferred=["teal", "sky_blue", "soft_blue", "aqua"],
        accents=["green", "mint", "white"],
        neutrals=["light_gray", "off_white", "pale_blue"],
        avoid=["deep_red", "black", "neon", "dark_purple"],
        saturation="low",
        temperature="cool",
        emotion="calm",
        notes="Propreté, calme, soin. Éviter les couleurs anxiogènes.",
    ),
    "technology": IndustryProfile(
        preferred=["blue", "purple", "cyan", "electric_blue"],
        accents=["neon_cyan", "violet", "teal"],
        neutrals=["dark_gray", "near_black", "light_gray"],
        avoid=["warm_brown", "terracotta", "mustard"],
        saturation="high",
        temperature="cool",
        emotion="innovation",
        notes="Innovation, vitesse, disruption. Palette souvent dark + accent vif.",
    ),
    "saas": IndustryProfile(
        preferred=["blue", "indigo", "violet", "teal"],
        accents=["cyan", "green", "purple"],
        neutrals=["off_white", "light_gray", "slate"],
        avoid=["dark_brown", "maroon"],
        saturation="medium",
        temperature="cool",
        emotion="efficiency",
        notes="Interface-first : lisibilité, clarté, palette professionnelle.",
    ),
    "luxury": IndustryProfile(
        preferred=["black", "deep_charcoal", "midnight", "ivory"],
        accents=["gold", "rose_gold", "platinum", "champagne"],
        neutrals=["warm_ivory", "cream", "taupe"],
        avoid=["bright_yellow", "neon", "lime", "hot_pink"],
        saturation="low",
        temperature="neutral",
        emotion="premium",
        notes="Contraste fort, palette restreinte, accent métal précieux.",
    ),
    "fashion": IndustryProfile(
        preferred=["black", "ivory", "camel", "burgundy"],
        accents=["gold", "terracotta", "blush"],
        neutrals=["beige", "cream", "warm_gray"],
        avoid=["lime", "neon_orange", "electric_blue"],
        saturation="medium",
        temperature="warm",
        emotion="elegance",
        notes="Dépend fortement du positionnement (luxe vs streetwear vs sportswear).",
    ),
    "food": IndustryProfile(
        preferred=["red", "orange", "warm_yellow", "terracotta"],
        accents=["green", "lime", "golden_yellow"],
        neutrals=["cream", "warm_white", "light_brown"],
        avoid=["blue", "purple", "gray"],
        saturation="high",
        temperature="warm",
        emotion="appetite",
        notes="Rouge/orange stimulent l'appétit. Bleu est un suppresseur d'appétit connu.",
    ),
    "food_premium": IndustryProfile(
        preferred=["deep_green", "burgundy", "terracotta", "warm_black"],
        accents=["gold", "copper", "sage"],
        neutrals=["cream", "linen", "warm_gray"],
        avoid=["neon", "cold_blue", "electric"],
        saturation="medium",
        temperature="warm",
        emotion="craft",
        notes="Artisan / gastronomie : palettes terres, or, vert profond.",
    ),
    "wellness": IndustryProfile(
        preferred=["sage_green", "soft_teal", "lavender", "warm_ivory"],
        accents=["terracotta", "blush", "peach"],
        neutrals=["off_white", "cream", "warm_beige"],
        avoid=["neon", "electric", "cold_gray", "black"],
        saturation="low",
        temperature="warm",
        emotion="calm",
        notes="Douceur, nature, équilibre. Saturation basse, tons terreux.",
    ),
    "sport": IndustryProfile(
        preferred=["electric_blue", "red", "black", "orange"],
        accents=["neon_yellow", "cyan", "lime"],
        neutrals=["dark_gray", "charcoal", "white"],
        avoid=["pastel", "ivory", "blush"],
        saturation="vivid",
        temperature="neutral",
        emotion="energy",
        notes="Énergie, dynamisme, performance. Contraste élevé.",
    ),
    "education": IndustryProfile(
        preferred=["blue", "sky_blue", "warm_yellow", "green"],
        accents=["orange", "teal", "purple"],
        neutrals=["off_white", "light_gray", "warm_white"],
        avoid=["black_dominant", "neon", "dark_red"],
        saturation="medium",
        temperature="neutral",
        emotion="curiosity",
        notes="Accessible, positif, stimulant. Couleurs primaires revisitées.",
    ),
    "real_estate": IndustryProfile(
        preferred=["navy", "forest_green", "warm_gray", "charcoal"],
        accents=["gold", "copper", "white"],
        neutrals=["warm_white", "cream", "light_gray"],
        avoid=["neon", "bright_red", "lime"],
        saturation="low",
        temperature="neutral",
        emotion="trust",
        notes="Fiabilité, solidité, aspiration. Tons neutres + accent premium.",
    ),
    "eco": IndustryProfile(
        preferred=["forest_green", "sage", "olive", "earth_brown"],
        accents=["terracotta", "warm_yellow", "sky_blue"],
        neutrals=["cream", "linen", "off_white"],
        avoid=["neon", "electric", "fluorescent", "plastic_colors"],
        saturation="medium",
        temperature="warm",
        emotion="nature",
        notes="Authenticité, durabilité, nature. Tons organiques.",
    ),
    "gaming": IndustryProfile(
        preferred=["deep_black", "electric_purple", "neon_blue"],
        accents=["neon_green", "magenta", "electric_cyan"],
        neutrals=["dark_gray", "near_black"],
        avoid=["pastel", "ivory", "warm_beige"],
        saturation="vivid",
        temperature="cool",
        emotion="excitement",
        notes="Dark dominant + accents néon haute saturation.",
    ),
    "nonprofit": IndustryProfile(
        preferred=["warm_blue", "green", "orange", "warm_red"],
        accents=["yellow", "teal", "purple"],
        neutrals=["off_white", "light_gray", "warm_white"],
        avoid=["black_dominant", "cold_gray", "neon"],
        saturation="medium",
        temperature="warm",
        emotion="hope",
        notes="Accessibilité, chaleur humaine, énergie positive.",
    ),
    "beauty": IndustryProfile(
        preferred=["blush", "rose", "mauve", "ivory"],
        accents=["gold", "rose_gold", "burgundy"],
        neutrals=["cream", "warm_white", "champagne"],
        avoid=["neon", "lime", "electric_blue"],
        saturation="medium",
        temperature="warm",
        emotion="elegance",
        notes="Beauté féminine premium : tons doux + accents métalliques.",
    ),
    "kids": IndustryProfile(
        preferred=["bright_red", "sky_blue", "sunny_yellow", "grass_green"],
        accents=["orange", "purple", "pink"],
        neutrals=["white", "light_gray", "cream"],
        avoid=["dark", "black", "dark_brown", "maroon"],
        saturation="vivid",
        temperature="warm",
        emotion="playful",
        notes="Couleurs primaires vives, joyeuses, accessibles.",
    ),
    "travel": IndustryProfile(
        preferred=["sky_blue", "turquoise", "coral", "warm_orange"],
        accents=["golden_yellow", "terracotta", "teal"],
        neutrals=["sand", "warm_white", "beige"],
        avoid=["cold_gray", "corporate_navy", "black"],
        saturation="high",
        temperature="warm",
        emotion="adventure",
        notes="Évasion, horizon, chaleur. Bleus ciel + coraux.",
    ),
}

# Aliases et variantes orthographiques
_ALIASES: dict[str, str] = {
    "tech": "technology",
    "health": "healthcare",
    "food_artisan": "food_premium",
    "sustainability": "eco",
    "environment": "eco",
    "sport": "sport",
    "sports": "sport",
    "game": "gaming",
    "games": "gaming",
    "finance_tech": "fintech",
    "e-commerce": "saas",
    "ecommerce": "saas",
    "cosmetics": "beauty",
    "cosmetic": "beauty",
    "children": "kids",
    "kids_brands": "kids",
}


def get_industry_profile(industry: str) -> IndustryProfile | None:
    key = industry.lower().strip().replace(" ", "_").replace("-", "_")
    key = _ALIASES.get(key, key)
    return _MAP.get(key)


def list_industries() -> list[str]:
    return sorted(_MAP.keys())
