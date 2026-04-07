"""
visual_intent_engine.py — EURKAI Visual Intent Engine

Définit la direction artistique AVANT la génération du design plan.
Produit un VisualIntent strict qui contraint le renderer et le design plan.

Ce module est sur l'INTENTION, pas sur le rendu.
Il définit : quelle audace visuelle, quelle déviation du générique.

Modes :
    default   — propre, lisible, risque minimal
    strong    — direction artistique forte (style family explicite)
    reference — extraction de principes depuis une image de référence
    hybrid    — blend style demandé + structure de référence

Usage :
    from visual_intent_engine import generate_visual_intent

    intent = generate_visual_intent(brief="...")
    intent = generate_visual_intent(brief="...", constraints={"force": ["brutalist"]})
    intent = generate_visual_intent(brief="...", reference_image="ref.png")
    intent = generate_visual_intent(brief="...",
                                    reference_image="ref.png",
                                    constraints={"force": ["editorial_luxury"]})
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent.parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute


# ─────────────────────────────────────────────────────────────────────────────
# STYLE FAMILIES — 6 directions fortes prédéfinies
# ─────────────────────────────────────────────────────────────────────────────

STYLE_FAMILIES: dict[str, dict] = {

    "editorial_luxury": {
        "tone":      "refined, contemplative, restrained",
        "intensity": "medium",
        "personality": ["elegant", "typographic", "spacious"],
        "composition_bias": {
            "dominance": "text",
            "density":   "low",
            "asymmetry": "medium",
            "rhythm":    "regular",
        },
        "visual_techniques": ["negative_space", "framing", "scale_contrast"],
        "color_strategy": {
            "contrast":     "medium",
            "palette_type": "neutral",
        },
        "typography_strategy": {
            "hierarchy_strength": "high",
            "weight_contrast":    "medium",
        },
        # Ce que ce style IMPOSE et REFUSE dans le design plan
        "_plan_profile":    "editorial",
        "_tension_level":   "medium",
        "_layout_boost":    ["editorial_flow", "magazine_spread", "vertical_narrative"],
        "_avoid_layouts":   ["brutalist_stack", "modular_grid"],
    },

    "brutalist": {
        "tone":      "raw, confrontational, direct",
        "intensity": "high",
        "personality": ["bold", "raw", "asymmetric"],
        "composition_bias": {
            "dominance": "text",
            "density":   "high",
            "asymmetry": "high",
            "rhythm":    "chaotic",
        },
        "visual_techniques": ["grid_breaking", "scale_contrast", "overlap", "cropping"],
        "color_strategy": {
            "contrast":     "high",
            "palette_type": "monochrome",
        },
        "typography_strategy": {
            "hierarchy_strength": "high",
            "weight_contrast":    "high",
        },
        "_plan_profile":  "bold",
        "_tension_level": "high",
        "_layout_boost":  ["brutalist_stack", "diagonal_tension", "layered_overlap"],
        "_avoid_layouts": ["editorial_flow", "modular_grid", "vertical_narrative"],
    },

    "tech_minimal": {
        "tone":      "clean, precise, functional",
        "intensity": "low",
        "personality": ["minimal", "structured", "confident"],
        "composition_bias": {
            "dominance": "balanced",
            "density":   "low",
            "asymmetry": "low",
            "rhythm":    "regular",
        },
        "visual_techniques": ["negative_space", "framing"],
        "color_strategy": {
            "contrast":     "medium",
            "palette_type": "neutral",
        },
        "typography_strategy": {
            "hierarchy_strength": "medium",
            "weight_contrast":    "high",
        },
        "_plan_profile":  "structural",
        "_tension_level": "medium",
        "_layout_boost":  ["modular_grid", "asymmetrical_split", "staggered_blocks"],
        "_avoid_layouts": ["brutalist_stack", "layered_overlap", "diagonal_tension"],
    },

    "experimental_grid": {
        "tone":      "unconventional, layered, surprising",
        "intensity": "high",
        "personality": ["experimental", "layered", "complex"],
        "composition_bias": {
            "dominance": "balanced",
            "density":   "high",
            "asymmetry": "high",
            "rhythm":    "alternating",
        },
        "visual_techniques": ["overlap", "layering", "grid_breaking", "scale_contrast", "cropping"],
        "color_strategy": {
            "contrast":     "high",
            "palette_type": "vibrant",
        },
        "typography_strategy": {
            "hierarchy_strength": "high",
            "weight_contrast":    "high",
        },
        "_plan_profile":  "bold",
        "_tension_level": "high",
        "_layout_boost":  ["layered_overlap", "diagonal_tension", "brutalist_stack"],
        "_avoid_layouts": ["vertical_narrative", "editorial_flow"],
    },

    "premium_brand": {
        "tone":      "aspirational, trustworthy, refined",
        "intensity": "medium",
        "personality": ["premium", "confident", "sophisticated"],
        "composition_bias": {
            "dominance": "image",
            "density":   "low",
            "asymmetry": "medium",
            "rhythm":    "regular",
        },
        "visual_techniques": ["framing", "scale_contrast", "negative_space", "cropping"],
        "color_strategy": {
            "contrast":     "low",
            "palette_type": "neutral",
        },
        "typography_strategy": {
            "hierarchy_strength": "medium",
            "weight_contrast":    "medium",
        },
        "_plan_profile":  "commercial",
        "_tension_level": "medium",
        "_layout_boost":  ["asymmetrical_split", "staggered_blocks", "magazine_spread"],
        "_avoid_layouts": ["brutalist_stack", "diagonal_tension"],
    },

    "bold_marketing": {
        "tone":      "energetic, direct, persuasive",
        "intensity": "high",
        "personality": ["bold", "energetic", "urgent"],
        "composition_bias": {
            "dominance": "balanced",
            "density":   "high",
            "asymmetry": "medium",
            "rhythm":    "alternating",
        },
        "visual_techniques": ["scale_contrast", "overlap", "framing"],
        "color_strategy": {
            "contrast":     "high",
            "palette_type": "vibrant",
        },
        "typography_strategy": {
            "hierarchy_strength": "high",
            "weight_contrast":    "high",
        },
        "_plan_profile":  "commercial",
        "_tension_level": "high",
        "_layout_boost":  ["staggered_blocks", "asymmetrical_split", "modular_grid"],
        "_avoid_layouts": ["vertical_narrative", "editorial_flow"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# ARCHETYPE → STYLE FAMILY MAPPING
# ─────────────────────────────────────────────────────────────────────────────

ARCHETYPE_STYLE_MAP: dict[str, str] = {
    # Editorial / culture
    "editorial_magazine":  "editorial_luxury",
    "editorial_rich":      "editorial_luxury",
    "editorial_asymmetric":"editorial_luxury",
    "editorial_grid":      "editorial_luxury",
    "editorial_sans":      "editorial_luxury",
    "editorial_serif":     "editorial_luxury",
    "institution_manifesto":"editorial_luxury",
    # Studio / craft / premium
    "studio_portfolio":    "premium_brand",
    "luxury_maison":       "premium_brand",
    "craft_artisan":       "premium_brand",
    # Tech / SaaS
    "startup_clean":       "tech_minimal",
    "product_saas":        "tech_minimal",
    "fintech":             "tech_minimal",
    "dark_tech":           "tech_minimal",
    # Bold / marketing
    "bold_disruptor":      "bold_marketing",
    "ecommerce_catalog":   "bold_marketing",
    "event_campaign":      "bold_marketing",
    "brand_landing":       "bold_marketing",
    # Experimental
    "experimental":        "experimental_grid",
}

# Archetypes qui constituent une direction FORTE (mode "strong")
_STRONG_ARCHETYPES: frozenset[str] = frozenset({
    "editorial_luxury", "brutalist", "tech_minimal",
    "experimental_grid", "premium_brand", "bold_marketing",
})

# ─────────────────────────────────────────────────────────────────────────────
# VALID ENUM VALUES — pour validation stricte
# ─────────────────────────────────────────────────────────────────────────────

_VALID_MODES          = {"default", "strong", "reference", "hybrid"}
_VALID_INTENSITY      = {"low", "medium", "high"}
_VALID_DOMINANCE      = {"text", "image", "balanced"}
_VALID_DENSITY        = {"low", "medium", "high"}
_VALID_ASYMMETRY      = {"low", "medium", "high"}
_VALID_RHYTHM         = {"regular", "alternating", "chaotic"}
_VALID_CONTRAST       = {"low", "medium", "high"}
_VALID_PALETTE        = {"neutral", "vibrant", "duotone", "monochrome"}
_VALID_HIERARCHY      = {"low", "medium", "high"}
_VALID_WEIGHT         = {"low", "medium", "high"}
_VALID_TECHNIQUES: frozenset[str] = frozenset({
    "overlap", "cropping", "scale_contrast", "layering",
    "negative_space", "framing", "grid_breaking",
})

# ─────────────────────────────────────────────────────────────────────────────
# CONTEXTUAL DESIGN ALIGNMENT — extraction et ajustements depuis le brief
# ─────────────────────────────────────────────────────────────────────────────

_PRODUCT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "ecommerce":  ["shop", "boutique", "store", "ecommerce", "e-commerce", "catalog", "buy", "cart", "product"],
    "saas":       ["saas", "dashboard", "analytics", "platform", "software", "tool", "subscription"],
    "event":      ["event", "festival", "concert", "conference", "meetup", "exhibition", "show", "gala"],
    "editorial":  ["magazine", "editorial", "journal", "revue", "blog", "media", "publication", "press"],
    "gaming":     ["game", "gaming", "esport", "esports", "play", "gamer", "rpg", "fps", "studio"],
    "dating":     ["dating", "rencontre", "love", "match", "couple", "romance", "relation"],
    "finance":    ["finance", "fintech", "bank", "banking", "invest", "trading", "crypto", "wealth", "insurance"],
    "luxury":     ["luxe", "luxury", "maison", "couture", "prestige", "exclusive", "haute"],
    "health":     ["health", "santé", "wellness", "clinic", "medical", "care", "therapy", "fitness"],
    "education":  ["education", "school", "academy", "cours", "learning", "formation", "study", "university"],
    "food":       ["food", "restaurant", "cuisine", "chef", "menu", "dining", "gastro", "recipe"],
    "travel":     ["travel", "voyage", "hotel", "booking", "destination", "trip", "tourism"],
    "agency":     ["agency", "agence", "studio", "creative", "design", "consulting", "brand"],
}

_AUDIENCE_KEYWORDS: dict[str, list[str]] = {
    "young_adult":   ["18-25", "jeune", "young", "youth", "millennials", "gen z", "genz", "étudiant"],
    "professional":  ["b2b", "entreprise", "business", "professional", "professionnel", "corporate", "executive"],
    "senior":        ["senior", "55+", "retraité", "mature", "older"],
    "mass_market":   ["tout public", "everyone", "grand public", "general", "famille", "family"],
    "niche":         ["passionné", "enthusiast", "expert", "connoisseur", "aficionado", "collector"],
}

# Objectif émotionnel par défaut selon le type de produit
_PRODUCT_EMOTIONAL_GOAL: dict[str, str] = {
    "ecommerce": "desire",
    "saas":      "trust",
    "event":     "excitement",
    "editorial": "curiosity",
    "gaming":    "excitement",
    "dating":    "desire",
    "finance":   "trust",
    "luxury":    "desire",
    "health":    "calm",
    "education": "curiosity",
    "food":      "desire",
    "travel":    "desire",
    "agency":    "authority",
}

# Positionnement de marque par défaut selon le type de produit
_PRODUCT_BRAND_POSITIONING: dict[str, str] = {
    "ecommerce": "accessible",
    "saas":      "serious",
    "event":     "playful",
    "editorial": "serious",
    "gaming":    "disruptive",
    "dating":    "playful",
    "finance":   "serious",
    "luxury":    "premium",
    "health":    "serious",
    "education": "accessible",
    "food":      "accessible",
    "travel":    "accessible",
    "agency":    "premium",
}

# Ajustements visuels par objectif émotionnel
# Appliqués en mode default/reference. En mode strong/hybrid : uniquement les constraints.
EMOTIONAL_GOAL_ADJUSTMENTS: dict[str, dict] = {
    "trust": {
        "composition_bias": {"dominance": "text", "density": "low", "asymmetry": "low", "rhythm": "regular"},
        "techniques_add":   ["framing", "negative_space"],
        "techniques_remove": ["grid_breaking", "overlap"],
        "color_strategy":   {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "high", "weight_contrast": "medium"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "excitement": {
        "composition_bias": {"dominance": "balanced", "density": "high", "asymmetry": "high", "rhythm": "alternating"},
        "techniques_add":   ["scale_contrast", "overlap"],
        "techniques_remove": ["negative_space"],
        "color_strategy":   {"contrast": "high", "palette_type": "vibrant"},
        "typography_strategy": {"hierarchy_strength": "high", "weight_contrast": "high"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "desire": {
        "composition_bias": {"dominance": "image", "density": "low", "asymmetry": "medium", "rhythm": "regular"},
        "techniques_add":   ["framing", "scale_contrast", "cropping"],
        "techniques_remove": ["grid_breaking"],
        "color_strategy":   {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "calm": {
        "composition_bias": {"dominance": "balanced", "density": "low", "asymmetry": "low", "rhythm": "regular"},
        "techniques_add":   ["negative_space", "framing"],
        "techniques_remove": ["grid_breaking", "overlap", "scale_contrast"],
        "color_strategy":   {"contrast": "low", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "low"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "curiosity": {
        "composition_bias": {"dominance": "balanced", "density": "medium", "asymmetry": "medium", "rhythm": "alternating"},
        "techniques_add":   ["layering", "overlap", "scale_contrast"],
        "techniques_remove": [],
        "color_strategy":   {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "authority": {
        "composition_bias": {"dominance": "text", "density": "medium", "asymmetry": "low", "rhythm": "regular"},
        "techniques_add":   ["framing", "negative_space"],
        "techniques_remove": ["grid_breaking", "overlap"],
        "color_strategy":   {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "high", "weight_contrast": "high"},
        "constraints_force": [],
        "constraints_avoid": [],
    },
}

# Fine-tune du positionnement de marque (appliqué après emotional_goal)
BRAND_POSITIONING_ADJUSTMENTS: dict[str, dict] = {
    "premium": {
        "composition_bias_override": {"density": "low", "asymmetry": "medium"},
        "color_strategy_override":   {"contrast": "low", "palette_type": "neutral"},
        "techniques_add":            ["negative_space", "framing"],
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "accessible": {
        "composition_bias_override": {"density": "medium"},
        "color_strategy_override":   {},
        "techniques_add":            [],
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "disruptive": {
        "composition_bias_override": {"asymmetry": "high"},
        "color_strategy_override":   {"contrast": "high"},
        "techniques_add":            ["grid_breaking", "overlap"],
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "playful": {
        "composition_bias_override": {"rhythm": "alternating"},
        "color_strategy_override":   {"palette_type": "vibrant"},
        "techniques_add":            [],
        "constraints_force": [],
        "constraints_avoid": [],
    },
    "serious": {
        "composition_bias_override": {"dominance": "text", "rhythm": "regular", "asymmetry": "low"},
        "color_strategy_override":   {"palette_type": "neutral"},
        "techniques_add":            [],
        "constraints_force": [],
        "constraints_avoid": [],
    },
}

# Signaux explicites dans le brief pour override l'objectif émotionnel inféré
_EMOTIONAL_OVERRIDE_SIGNALS: dict[str, list[str]] = {
    "trust":     ["confiance", "trust", "fiable", "reliable", "secure", "sécurisé", "safety", "sécurité"],
    "excitement":["excitant", "exciting", "adrénaline", "thrill", "energy", "énergie", "intense"],
    "desire":    ["désir", "desire", "séduisant", "seduction", "attractif", "sensuel", "sensual"],
    "calm":      ["calme", "calm", "sérénité", "serenity", "zen", "peaceful", "doux", "soft"],
    "curiosity": ["curiosité", "curiosity", "découverte", "discover", "explore", "apprendre", "learn"],
    "authority": ["autorité", "authority", "expert", "leader", "référence", "established"],
}

# Signaux explicites pour override le positionnement
_POSITIONING_OVERRIDE_SIGNALS: dict[str, list[str]] = {
    "premium":    ["premium", "luxe", "luxury", "prestige", "exclusive", "haut de gamme"],
    "accessible": ["accessible", "pour tous", "grand public", "abordable", "simple", "facile"],
    "disruptive": ["disruptif", "disruptive", "révolutionnaire", "innovant", "challenger", "disrupt"],
    "playful":    ["fun", "ludique", "playful", "amusant", "joyeux", "coloré"],
    "serious":    ["sérieux", "serious", "professionnel", "corporate", "institutionnel", "formel"],
}

# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT INTENT — safe baseline
# ─────────────────────────────────────────────────────────────────────────────

def _default_intent() -> dict:
    return {
        "mode": "default",
        "art_direction": {
            "style_family": "neutral",
            "tone":         "clean, balanced, readable",
            "intensity":    "low",
            "personality":  ["clear", "accessible", "neutral"],
        },
        "composition_bias": {
            "dominance": "balanced",
            "density":   "medium",
            "asymmetry": "low",
            "rhythm":    "regular",
        },
        "visual_techniques": ["framing", "negative_space"],
        "color_strategy": {
            "contrast":     "medium",
            "palette_type": "neutral",
        },
        "typography_strategy": {
            "hierarchy_strength": "medium",
            "weight_contrast":    "medium",
        },
        "constraints": {
            "force": [],
            "avoid": [],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def _detect_style_family(
    style_dna:   dict | None,
    constraints: dict | None,
) -> str | None:
    """
    Détecte si une direction de style forte est demandée.
    Retourne le nom de la style family, ou None si aucune demande forte.

    Priorité :
    1. constraints.force contient un nom de style family
    2. style_dna.style_family est un nom de style family
    3. style_dna.archetype est dans ARCHETYPE_STYLE_MAP ET est un archetype fort
    """
    # 1. constraints.force (priorité maximale — demande explicite)
    if constraints:
        for item in constraints.get("force", []):
            if item in STYLE_FAMILIES:
                return item

    if style_dna:
        # 2. style_dna.style_family explicite
        sf = style_dna.get("style_family", "")
        if sf in STYLE_FAMILIES:
            return sf

        # 3. archetype fort
        archetype = style_dna.get("archetype", "")
        if archetype in _STRONG_ARCHETYPES:
            return archetype
        mapped = ARCHETYPE_STYLE_MAP.get(archetype)
        if mapped and archetype in ARCHETYPE_STYLE_MAP:
            # Seulement si l'archetype est "articulé" (a une valeur propre forte)
            # On considère les archetypes de craft/studio/editorial comme forts
            _editorial_archetypes = {
                "editorial_magazine", "editorial_rich", "editorial_asymmetric",
                "editorial_grid", "editorial_serif", "editorial_sans",
                "studio_portfolio", "luxury_maison", "craft_artisan",
                "institution_manifesto", "bold_disruptor", "experimental",
            }
            if archetype in _editorial_archetypes:
                return mapped

    return None


def _detect_mode(
    style_dna:        dict | None,
    reference_image:  str  | None,
    constraints:      dict | None,
) -> tuple[str, str | None]:
    """
    Détecte le mode à partir des inputs.

    Returns:
        (mode, style_family_or_None)
    """
    has_reference = reference_image is not None
    style_family  = _detect_style_family(style_dna, constraints)
    has_style     = style_family is not None

    if has_reference and has_style:
        return "hybrid", style_family
    if has_reference:
        return "reference", None
    if has_style:
        return "strong", style_family
    return "default", None


# ─────────────────────────────────────────────────────────────────────────────
# STRONG MODE — intent depuis une style family
# ─────────────────────────────────────────────────────────────────────────────

def _build_strong_intent(style_family: str) -> dict:
    """Construit l'intent depuis une style family prédéfinie."""
    sf = STYLE_FAMILIES.get(style_family)
    if sf is None:
        return _default_intent()

    # Filtrer les clés internes (_*)
    techniques = sf["visual_techniques"]
    # Garantir que toutes les techniques sont dans la liste valide
    techniques = [t for t in techniques if t in _VALID_TECHNIQUES]

    return {
        "mode": "strong",
        "art_direction": {
            "style_family": style_family,
            "tone":         sf["tone"],
            "intensity":    sf["intensity"],
            "personality":  list(sf["personality"]),
        },
        "composition_bias": dict(sf["composition_bias"]),
        "visual_techniques": techniques,
        "color_strategy": dict(sf["color_strategy"]),
        "typography_strategy": dict(sf["typography_strategy"]),
        "constraints": {
            "force": list(sf.get("_avoid_layouts", []).__class__()),  # vide — géré via boost
            "avoid": list(sf.get("_avoid_layouts", [])),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE MODE — extraction depuis une image
# ─────────────────────────────────────────────────────────────────────────────

_REFERENCE_PROMPT = """Analyze this reference design image and extract its key visual principles.

DO NOT describe what you see literally.
Extract abstract design parameters only.

Return ONLY a valid JSON object with these exact fields:

{
  "dominance": "text | image | balanced",
  "density": "low | medium | high",
  "asymmetry": "low | medium | high",
  "rhythm": "regular | alternating | chaotic",
  "contrast": "low | medium | high",
  "palette_type": "neutral | vibrant | duotone | monochrome",
  "hierarchy_strength": "low | medium | high",
  "weight_contrast": "low | medium | high",
  "techniques": ["list", "of", "techniques"],
  "tone": "3 to 5 words describing the overall feel",
  "personality": ["adjective1", "adjective2", "adjective3"]
}

Valid techniques (only include those clearly visible): overlap, cropping, scale_contrast, layering, negative_space, framing, grid_breaking

Rules:
- techniques: max 4 items, only from valid list
- personality: 2 to 4 adjectives
- All enum fields MUST be one of the exact values listed
- Return ONLY the JSON. No explanation. No markdown.
"""


def _load_image_as_base64(reference_image: str) -> tuple[str, str]:
    """
    Charge l'image de référence et retourne (base64_data, media_type).
    Supporte : chemin fichier local, données base64 déjà encodées.
    """
    path = Path(reference_image)
    if path.exists():
        data = path.read_bytes()
        media_types = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp",
        }
        media_type = media_types.get(path.suffix.lower(), "image/png")
        return base64.b64encode(data).decode("utf-8"), media_type

    # Assume déjà en base64
    return reference_image, "image/png"


def _parse_reference_response(text: str) -> dict:
    """Parse la réponse JSON du modèle vision."""
    # Extraire le JSON (peut être entouré de markdown ou texte)
    text = text.strip()
    if "```" in text:
        for block in text.split("```"):
            stripped = block.strip().lstrip("json").strip()
            if stripped.startswith("{"):
                text = stripped
                break
    # Chercher le premier { et le dernier }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _extract_from_reference(
    reference_image: str,
    reference_type:  str | None,
) -> dict:
    """
    Extrait les principes visuels d'une image de référence via l'API vision.
    Retourne un dict partiel (pas un intent complet).
    Graceful fallback vers dict vide si API indisponible.
    """
    try:
        b64_data, media_type = _load_image_as_base64(reference_image)
    except Exception:
        return {}

    try:
        result = model_execute(
            "img2text",
            _REFERENCE_PROMPT,
            data={
                "image_base64":   b64_data,
                "media_type":     media_type,
                "max_tokens":     512,
                "model_override": "claude-haiku-4-5-20251001",
            },
            provider="anthropic",
        )
        raw = result["result"]
    except Exception:
        return {}

    parsed = _parse_reference_response(raw)
    if not parsed:
        return {}

    # Normaliser et valider les champs extraits
    def _clamp(val: Any, valid: set, fallback: str) -> str:
        return val if val in valid else fallback

    techniques_raw = parsed.get("techniques", [])
    if isinstance(techniques_raw, list):
        techniques = [t for t in techniques_raw if t in _VALID_TECHNIQUES][:4]
    else:
        techniques = []

    personality_raw = parsed.get("personality", [])
    if isinstance(personality_raw, list):
        personality = [str(p) for p in personality_raw[:4]]
    else:
        personality = []

    return {
        "composition_bias": {
            "dominance": _clamp(parsed.get("dominance"), _VALID_DOMINANCE, "balanced"),
            "density":   _clamp(parsed.get("density"),   _VALID_DENSITY,   "medium"),
            "asymmetry": _clamp(parsed.get("asymmetry"), _VALID_ASYMMETRY,  "low"),
            "rhythm":    _clamp(parsed.get("rhythm"),    _VALID_RHYTHM,     "regular"),
        },
        "visual_techniques": techniques,
        "color_strategy": {
            "contrast":     _clamp(parsed.get("contrast"),     _VALID_CONTRAST, "medium"),
            "palette_type": _clamp(parsed.get("palette_type"), _VALID_PALETTE,  "neutral"),
        },
        "typography_strategy": {
            "hierarchy_strength": _clamp(parsed.get("hierarchy_strength"), _VALID_HIERARCHY, "medium"),
            "weight_contrast":    _clamp(parsed.get("weight_contrast"),    _VALID_WEIGHT,    "medium"),
        },
        "tone":        str(parsed.get("tone", ""))[:80],
        "personality": personality,
    }


def _build_reference_intent(extracted: dict) -> dict:
    """Construit l'intent complet depuis les données extraites de la référence."""
    base = _default_intent()
    base["mode"] = "reference"

    if not extracted:
        return base

    if "composition_bias" in extracted:
        base["composition_bias"].update(extracted["composition_bias"])
    if "visual_techniques" in extracted and extracted["visual_techniques"]:
        base["visual_techniques"] = extracted["visual_techniques"]
    if "color_strategy" in extracted:
        base["color_strategy"].update(extracted["color_strategy"])
    if "typography_strategy" in extracted:
        base["typography_strategy"].update(extracted["typography_strategy"])
    if "tone" in extracted and extracted["tone"]:
        base["art_direction"]["tone"] = extracted["tone"]
    if "personality" in extracted and extracted["personality"]:
        base["art_direction"]["personality"] = extracted["personality"]

    return base


# ─────────────────────────────────────────────────────────────────────────────
# HYBRID MODE — blend style + reference
# ─────────────────────────────────────────────────────────────────────────────

def _blend_hybrid(
    style_intent: dict,
    ref_extracted: dict,
) -> dict:
    """
    Blend : style + reference.

    Règles :
    - Le style définit : tone, intensity, personality, color_strategy, typography_strategy
    - La référence guide : composition_bias (structure/layout feeling)
    - Les visual_techniques sont merged (union, max 5)
    - Le style override les valeurs faibles de la référence

    Logique de merge par champ :
    - dominance   : référence (structure observée)
    - density     : référence si "low", sinon style
    - asymmetry   : max(style, reference)
    - rhythm      : style (intention narrative)
    - contrast    : max(style, reference)
    - palette     : style
    - hierarchy   : style
    - weight      : style
    """
    result = dict(style_intent)
    result["mode"] = "hybrid"

    if not ref_extracted:
        return result

    # Niveaux ordonnés pour "max"
    _level_order = {"low": 0, "medium": 1, "high": 2, "chaotic": 2, "alternating": 1, "regular": 0}

    def _max_level(a: str, b: str, valid: set) -> str:
        oa = _level_order.get(a, 1)
        ob = _level_order.get(b, 1)
        winner = a if oa >= ob else b
        return winner if winner in valid else a

    ref_cb = ref_extracted.get("composition_bias", {})
    sty_cb = style_intent["composition_bias"]

    result["composition_bias"] = {
        "dominance": ref_cb.get("dominance", sty_cb["dominance"]),
        "density":   ref_cb.get("density", "low") if ref_cb.get("density") == "low" else sty_cb["density"],
        "asymmetry": _max_level(sty_cb["asymmetry"], ref_cb.get("asymmetry", "low"), _VALID_ASYMMETRY),
        "rhythm":    sty_cb["rhythm"],  # le style garde le rythme
    }

    # Techniques : union des deux, limitée à 5
    ref_tech = ref_extracted.get("visual_techniques", [])
    sty_tech = style_intent.get("visual_techniques", [])
    merged_tech = list(dict.fromkeys(sty_tech + ref_tech))  # style en priorité
    result["visual_techniques"] = merged_tech[:5]

    # contrast : max(style, ref)
    ref_cs = ref_extracted.get("color_strategy", {})
    result["color_strategy"]["contrast"] = _max_level(
        style_intent["color_strategy"]["contrast"],
        ref_cs.get("contrast", "low"),
        _VALID_CONTRAST,
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# BRIEF SIGNAL ENRICHMENT
# ─────────────────────────────────────────────────────────────────────────────

# Mots-clés dans le brief → ajustements légers de l'intent
_BRIEF_SIGNALS: dict[str, dict] = {
    # Signaux vers plus de personnalité
    "luxe":       {"intensity_boost": True, "palette_type": "neutral"},
    "luxury":     {"intensity_boost": True, "palette_type": "neutral"},
    "premium":    {"intensity_boost": True, "palette_type": "neutral"},
    "artisan":    {"palette_type": "neutral", "density_prefer": "low"},
    "artisanal":  {"palette_type": "neutral", "density_prefer": "low"},
    # Signaux vers plus de lisibilité
    "saas":       {"density_prefer": "medium", "palette_type": "neutral"},
    "dashboard":  {"density_prefer": "medium", "rhythm": "regular"},
    "analytics":  {"density_prefer": "medium", "rhythm": "regular"},
    # Signaux événementiels
    "festival":   {"intensity_boost": True, "palette_type": "vibrant"},
    "événement":  {"intensity_boost": True, "palette_type": "vibrant"},
    "event":      {"intensity_boost": True},
    # Signaux éditoriaux
    "magazine":   {"density_prefer": "low", "rhythm": "regular"},
    "editorial":  {"density_prefer": "low", "rhythm": "regular"},
    "revue":      {"density_prefer": "low", "rhythm": "regular"},
}

_INTENSITY_UPGRADE = {"low": "medium", "medium": "high", "high": "high"}


def _apply_brief_signals(intent: dict, brief: str) -> dict:
    """
    Enrichit l'intent avec des ajustements dérivés du brief.
    Ne surcharge PAS les valeurs déjà fortes (mode strong/hybrid).
    S'applique uniquement en mode default/reference.
    """
    if intent.get("mode") in ("strong", "hybrid"):
        return intent  # Le style prime

    lower = brief.lower()
    result = _deep_copy(intent)

    for keyword, adjustments in _BRIEF_SIGNALS.items():
        if keyword not in lower:
            continue

        if adjustments.get("intensity_boost"):
            current = result["art_direction"]["intensity"]
            result["art_direction"]["intensity"] = _INTENSITY_UPGRADE.get(current, current)

        if "palette_type" in adjustments:
            # Seulement si la palette est encore neutre (pas de surcharge forte)
            if result["color_strategy"]["palette_type"] == "neutral":
                result["color_strategy"]["palette_type"] = adjustments["palette_type"]

        if "density_prefer" in adjustments:
            # Suggestion douce — n'écrase que "medium" vers une valeur plus adaptée
            if result["composition_bias"]["density"] == "medium":
                result["composition_bias"]["density"] = adjustments["density_prefer"]

        if "rhythm" in adjustments:
            if result["composition_bias"]["rhythm"] == "regular":
                result["composition_bias"]["rhythm"] = adjustments["rhythm"]

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT EXTRACTION — détection automatique depuis le brief
# ─────────────────────────────────────────────────────────────────────────────

def _extract_context(brief: str) -> dict:
    """
    Extrait le contexte produit depuis le brief.
    Retourne toujours un dict complet (zéro champ manquant).

    Fields :
        product_type      — type de produit détecté (ou "generic")
        target_audience   — audience cible (ou "general")
        emotional_goal    — objectif émotionnel principal
        brand_positioning — positionnement de marque
    """
    lower = brief.lower()

    # Détection du type de produit (premier match dans l'ordre de déclaration)
    product_type = "generic"
    for ptype, keywords in _PRODUCT_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            product_type = ptype
            break

    # Détection de l'audience cible
    target_audience = "general"
    for audience, keywords in _AUDIENCE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            target_audience = audience
            break

    # Objectif émotionnel : par défaut depuis product_type, override si signal explicite
    emotional_goal = _PRODUCT_EMOTIONAL_GOAL.get(product_type, "curiosity")
    for goal, signals in _EMOTIONAL_OVERRIDE_SIGNALS.items():
        if any(s in lower for s in signals):
            emotional_goal = goal
            break

    # Positionnement de marque : par défaut depuis product_type, override si signal explicite
    brand_positioning = _PRODUCT_BRAND_POSITIONING.get(product_type, "accessible")
    for pos, signals in _POSITIONING_OVERRIDE_SIGNALS.items():
        if any(s in lower for s in signals):
            brand_positioning = pos
            break

    return {
        "product_type":      product_type,
        "target_audience":   target_audience,
        "emotional_goal":    emotional_goal,
        "brand_positioning": brand_positioning,
    }


def _apply_context_adjustments(intent: dict, context: dict, mode: str) -> dict:
    """
    Adapte l'intent selon le contexte détecté.

    Règle centrale :
        default / reference → le contexte DRIVE composition_bias, color_strategy,
                              typography_strategy, visual_techniques
        strong / hybrid     → le contexte ajoute UNIQUEMENT aux constraints
                              (le style family prime sur tout)

    Le champ "context" est systématiquement injecté dans l'intent.
    """
    result = _deep_copy(intent)
    result["context"] = context

    emotional_goal    = context.get("emotional_goal", "")
    brand_positioning = context.get("brand_positioning", "")

    eg_adj = EMOTIONAL_GOAL_ADJUSTMENTS.get(emotional_goal, {})
    bp_adj = BRAND_POSITIONING_ADJUSTMENTS.get(brand_positioning, {})

    if mode in ("strong", "hybrid"):
        # Style prime — le contexte ne peut qu'ajouter des contraintes
        all_force = eg_adj.get("constraints_force", []) + bp_adj.get("constraints_force", [])
        all_avoid = eg_adj.get("constraints_avoid", []) + bp_adj.get("constraints_avoid", [])
        if all_force:
            result["constraints"]["force"] = list(dict.fromkeys(
                result["constraints"]["force"] + all_force
            ))
        if all_avoid:
            result["constraints"]["avoid"] = list(dict.fromkeys(
                result["constraints"]["avoid"] + all_avoid
            ))
        return result

    if mode == "reference":
        # La référence guide la structure (composition_bias) — le contexte ajuste
        # uniquement color_strategy, typography_strategy et techniques (pas composition_bias).
        # La reference extraction est la source de vérité pour la structure visuelle.
        if eg_adj:
            result["color_strategy"].update(eg_adj.get("color_strategy", {}))
            result["typography_strategy"].update(eg_adj.get("typography_strategy", {}))
            current_tech = list(result.get("visual_techniques", []))
            for t in eg_adj.get("techniques_add", []):
                if t in _VALID_TECHNIQUES and t not in current_tech:
                    current_tech.append(t)
            result["visual_techniques"] = current_tech[:5]
        if bp_adj:
            result["color_strategy"].update(bp_adj.get("color_strategy_override", {}))
            current_tech = list(result.get("visual_techniques", []))
            for t in bp_adj.get("techniques_add", []):
                if t in _VALID_TECHNIQUES and t not in current_tech:
                    current_tech.append(t)
            result["visual_techniques"] = current_tech[:5]
        return result

    # ── Mode default — le contexte drive tous les paramètres visuels ──────────

    # 1. Emotional goal → composition_bias + color_strategy + typography + techniques
    if eg_adj:
        result["composition_bias"].update(eg_adj.get("composition_bias", {}))
        result["color_strategy"].update(eg_adj.get("color_strategy", {}))
        result["typography_strategy"].update(eg_adj.get("typography_strategy", {}))

        current_tech = list(result.get("visual_techniques", []))
        # Retirer les techniques incompatibles
        current_tech = [t for t in current_tech if t not in eg_adj.get("techniques_remove", [])]
        # Ajouter les techniques recommandées (sans doublon, max 5)
        for t in eg_adj.get("techniques_add", []):
            if t in _VALID_TECHNIQUES and t not in current_tech:
                current_tech.append(t)
        result["visual_techniques"] = current_tech[:5]

    # 2. Brand positioning → fine-tune par-dessus emotional_goal
    if bp_adj:
        result["composition_bias"].update(bp_adj.get("composition_bias_override", {}))
        result["color_strategy"].update(bp_adj.get("color_strategy_override", {}))

        current_tech = list(result.get("visual_techniques", []))
        for t in bp_adj.get("techniques_add", []):
            if t in _VALID_TECHNIQUES and t not in current_tech:
                current_tech.append(t)
        result["visual_techniques"] = current_tech[:5]

    return result


# ─────────────────────────────────────────────────────────────────────────────
# USER CONSTRAINTS APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def _apply_user_constraints(intent: dict, constraints: dict | None) -> dict:
    """
    Fusionne les contraintes utilisateur dans l'intent.
    constraints.force → intent.constraints.force (sauf les style family names déjà gérés)
    constraints.avoid → intent.constraints.avoid
    """
    if not constraints:
        return intent

    result = _deep_copy(intent)

    user_force = constraints.get("force", [])
    user_avoid = constraints.get("avoid", [])

    # Filtrer les style family names (déjà utilisés pour la détection de mode)
    non_style_force = [f for f in user_force if f not in STYLE_FAMILIES]
    non_style_avoid = [a for a in user_avoid if a not in STYLE_FAMILIES]

    existing_force = result["constraints"]["force"]
    existing_avoid = result["constraints"]["avoid"]

    result["constraints"]["force"] = list(dict.fromkeys(existing_force + non_style_force))
    result["constraints"]["avoid"] = list(dict.fromkeys(existing_avoid + non_style_avoid))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION — garantit la conformité du schema de sortie
# ─────────────────────────────────────────────────────────────────────────────

def _validate_and_clean(intent: dict) -> dict:
    """
    Valide et nettoie l'intent pour garantir la conformité stricte du schéma.
    Corrige silencieusement les valeurs invalides vers les défauts.
    """
    def _v(val: Any, valid: set, fallback: str) -> str:
        return val if (isinstance(val, str) and val in valid) else fallback

    def _vlist(val: Any, valid: frozenset) -> list:
        if isinstance(val, list):
            return [x for x in val if isinstance(x, str) and x in valid]
        return []

    ad = intent.get("art_direction", {})
    cb = intent.get("composition_bias", {})
    cs = intent.get("color_strategy", {})
    ts = intent.get("typography_strategy", {})
    ct = intent.get("constraints", {})

    personality = ad.get("personality", [])
    if not isinstance(personality, list):
        personality = []
    personality = [str(p)[:30] for p in personality[:6]]

    techniques = intent.get("visual_techniques", [])
    techniques = _vlist(techniques, _VALID_TECHNIQUES)

    # ── Contexte produit — préservé tel quel (champs str uniquement) ──────────
    raw_ctx = intent.get("context", {})
    if not isinstance(raw_ctx, dict):
        raw_ctx = {}
    context_out = {
        "product_type":      str(raw_ctx.get("product_type",      "generic"))[:40],
        "target_audience":   str(raw_ctx.get("target_audience",   "general"))[:40],
        "emotional_goal":    str(raw_ctx.get("emotional_goal",    ""))[:40],
        "brand_positioning": str(raw_ctx.get("brand_positioning",  ""))[:40],
    }

    return {
        "mode": _v(intent.get("mode"), _VALID_MODES, "default"),
        "art_direction": {
            "style_family": str(ad.get("style_family", "neutral"))[:40],
            "tone":         str(ad.get("tone", "clean, balanced"))[:120],
            "intensity":    _v(ad.get("intensity"), _VALID_INTENSITY, "low"),
            "personality":  personality,
        },
        "composition_bias": {
            "dominance": _v(cb.get("dominance"), _VALID_DOMINANCE, "balanced"),
            "density":   _v(cb.get("density"),   _VALID_DENSITY,   "medium"),
            "asymmetry": _v(cb.get("asymmetry"), _VALID_ASYMMETRY,  "low"),
            "rhythm":    _v(cb.get("rhythm"),    _VALID_RHYTHM,     "regular"),
        },
        "visual_techniques": techniques,
        "color_strategy": {
            "contrast":     _v(cs.get("contrast"),     _VALID_CONTRAST, "medium"),
            "palette_type": _v(cs.get("palette_type"), _VALID_PALETTE,  "neutral"),
        },
        "typography_strategy": {
            "hierarchy_strength": _v(ts.get("hierarchy_strength"), _VALID_HIERARCHY, "medium"),
            "weight_contrast":    _v(ts.get("weight_contrast"),    _VALID_WEIGHT,    "medium"),
        },
        "constraints": {
            "force": [str(x) for x in ct.get("force", []) if isinstance(x, str)],
            "avoid": [str(x) for x in ct.get("avoid", []) if isinstance(x, str)],
        },
        "context": context_out,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _deep_copy(d: dict) -> dict:
    """Deep copy d'un dict via JSON (suffisant pour nos structures de données)."""
    return json.loads(json.dumps(d))


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_visual_intent(
    brief:              str,
    style_dna:          dict | None = None,
    reference_image:    str  | None = None,
    reference_type:     str  | None = None,
    constraints:        dict | None = None,
    reference_analysis: dict | None = None,
) -> dict:
    """
    Génère un VisualIntent strict qui définit la direction artistique de la page.

    Args:
        brief           : texte libre du projet (obligatoire)
        style_dna           : dict optionnel depuis le pipeline — peut contenir "archetype",
                              "style_family", "intensity"
        reference_image     : chemin fichier image ou données base64 — déclenche le mode référence
        reference_type      : type de référence ("screenshot", "moodboard", "design", "brand")
                              information contexte pour l'extraction
        constraints         : dict {"force": [...], "avoid": [...]} — overrides utilisateur
                              Noms de style family dans "force" déclenchent le mode strong/hybrid
        reference_analysis  : dict depuis visual_coherence_engine CASE 3 (design_reference_drives_plan)
                              Quand fourni, surcharge composition_bias, hierarchy, spacing
                              comme inputs durs (analyse déjà faite, pas de re-extraction)

    Returns:
        dict strict conforme au schéma VisualIntent (zéro champ manquant)

    Mode auto-détecté :
        "default"   — aucun input fort → clean, lisible, risque minimal
        "strong"    — style family détecté (via constraints.force ou style_dna.archetype)
        "reference" — reference_image fournie, pas de style fort
        "hybrid"    — reference_image + style fort
    """
    # ── 1. Détection du mode ──────────────────────────────────────────────────
    mode, style_family = _detect_mode(style_dna, reference_image, constraints)

    # ── 2. Construction de l'intent de base ───────────────────────────────────
    if mode == "default":
        intent = _default_intent()

    elif mode == "strong":
        intent = _build_strong_intent(style_family)  # type: ignore[arg-type]

    elif mode == "reference":
        extracted = _extract_from_reference(reference_image, reference_type)  # type: ignore[arg-type]
        intent    = _build_reference_intent(extracted)

    else:  # hybrid
        style_intent  = _build_strong_intent(style_family)       # type: ignore[arg-type]
        ref_extracted = _extract_from_reference(reference_image, reference_type)  # type: ignore[arg-type]
        intent        = _blend_hybrid(style_intent, ref_extracted)

    # ── 2.5 Application de la référence design pré-calculée (hard override) ──────
    if reference_analysis:
        intent = _apply_reference_analysis(intent, reference_analysis)
        mode   = intent.get("mode", "reference")  # sync local mode

    # ── 3. Extraction et application du contexte produit ─────────────────────
    context = _extract_context(brief)
    intent  = _apply_context_adjustments(intent, context, mode)

    # ── 4. Enrichissement léger depuis le brief (mots-clés) ───────────────────
    intent = _apply_brief_signals(intent, brief)

    # ── 5. Application des contraintes utilisateur ────────────────────────────
    intent = _apply_user_constraints(intent, constraints)

    # ── 6. Validation et nettoyage du schéma ─────────────────────────────────
    return _validate_and_clean(intent)


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN REFERENCE INTEGRATION — applique reference_analysis comme hard override
# ─────────────────────────────────────────────────────────────────────────────

def _apply_reference_analysis(intent: dict, ref: dict) -> dict:
    """
    Applique une reference_analysis (depuis visual_coherence_engine CASE 3) comme
    overrides durs sur l'intent.

    Règles :
    - composition_bias vient entièrement de ref.composition_bias (structure observée)
    - typography_strategy est dérivée de ref.hierarchy
    - color_strategy.contrast est dérivé de ref.palette_hint.saturation
    - Le mode passe à "reference" (structure guidée par la référence)

    Ne surcharge PAS le style family (si mode strong/hybrid : composition uniquement).
    """
    result = _deep_copy(intent)
    result["mode"] = "reference"

    cb = ref.get("composition_bias", {})
    if cb.get("dominance") in _VALID_DOMINANCE:
        result["composition_bias"]["dominance"] = cb["dominance"]
    if cb.get("density") in _VALID_DENSITY:
        result["composition_bias"]["density"] = cb["density"]
    if cb.get("asymmetry") in _VALID_ASYMMETRY:
        result["composition_bias"]["asymmetry"] = cb["asymmetry"]
    if cb.get("rhythm") in _VALID_RHYTHM:
        result["composition_bias"]["rhythm"] = cb["rhythm"]

    # Hierarchy → typography_strategy
    _hierarchy_typo: dict[str, dict] = {
        "calm":       {"hierarchy_strength": "medium", "weight_contrast": "low"},
        "strong":     {"hierarchy_strength": "high",   "weight_contrast": "medium"},
        "aggressive": {"hierarchy_strength": "high",   "weight_contrast": "high"},
    }
    hierarchy = ref.get("hierarchy", "")
    if hierarchy in _hierarchy_typo:
        result["typography_strategy"].update(_hierarchy_typo[hierarchy])

    # palette_hint.saturation → color_strategy.contrast
    ph  = ref.get("palette_hint", {})
    sat = ph.get("saturation", 0.3)
    if sat > 0.50:
        result["color_strategy"]["contrast"] = "high"
    elif sat < 0.20:
        result["color_strategy"]["contrast"] = "low"

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PLAN INTEGRATION HELPERS — utilisés par design_plan.py
# ─────────────────────────────────────────────────────────────────────────────

def intent_to_plan_overrides(visual_intent: dict) -> dict:
    """
    Traduit un VisualIntent en overrides pour generate_design_plan.

    Retourne un dict avec les clés attendues par generate_design_plan :
        profile_override  : str | None         — remplace _extract_profile()
        density_override  : str | None         — remplace le choix de density
        tension_override  : str | None         — remplace le choix de tension level
        tension_methods   : list[str]          — méthodes à utiliser
        layout_boost      : list[str]          — layouts à favoriser
        layout_avoid      : list[str]          — layouts à éviter
        extra_required    : list[str]          — ajouts à constraints.required
        extra_forbidden   : list[str]          — ajouts à constraints.forbidden
    """
    sf_name = visual_intent.get("art_direction", {}).get("style_family", "")
    sf_data = STYLE_FAMILIES.get(sf_name, {})

    cb        = visual_intent.get("composition_bias", {})
    ad        = visual_intent.get("art_direction", {})
    ct        = visual_intent.get("constraints", {})
    techniques = visual_intent.get("visual_techniques", [])

    # Profil
    profile_override: str | None = sf_data.get("_plan_profile")

    # Density
    density_override: str | None = cb.get("density") or None

    # Tension depuis intensity
    _intensity_to_tension = {"low": "medium", "medium": "high", "high": "high"}
    intensity     = ad.get("intensity", "low")
    tension_level = sf_data.get("_tension_level") or _intensity_to_tension.get(intensity, "medium")
    # En mode default, garder medium
    if visual_intent.get("mode") == "default":
        tension_level = "medium"

    # Layout boost/avoid depuis asymmetry + style family
    asymmetry = cb.get("asymmetry", "low")
    _asymmetry_layout_boost: dict[str, list[str]] = {
        "high":   ["asymmetrical_split", "staggered_blocks", "diagonal_tension",
                   "brutalist_stack", "layered_overlap"],
        "medium": ["asymmetrical_split", "staggered_blocks", "magazine_spread"],
        "low":    ["modular_grid", "editorial_flow", "vertical_narrative"],
    }
    layout_boost = sf_data.get("_layout_boost") or _asymmetry_layout_boost.get(asymmetry, [])
    layout_avoid = sf_data.get("_avoid_layouts") or ct.get("avoid", [])

    # Méthodes de tension depuis visual_techniques
    _technique_to_method = {
        "overlap":        "overlap",
        "cropping":       "bleeding_elements",
        "scale_contrast": "scale_contrast",
        "layering":       "layering",
        "negative_space": "negative_space_imbalance",
        "framing":        "whitespace_tension",
        "grid_breaking":  "grid_break",
    }
    tension_methods = [
        _technique_to_method[t]
        for t in techniques
        if t in _technique_to_method
    ]

    # Extra constraints
    extra_required  = [x for x in ct.get("force", []) if x not in STYLE_FAMILIES]
    extra_forbidden = [x for x in ct.get("avoid", []) if x not in STYLE_FAMILIES]

    return {
        "profile_override":  profile_override,
        "density_override":  density_override,
        "tension_override":  tension_level,
        "tension_methods":   tension_methods,
        "layout_boost":      layout_boost,
        "layout_avoid":      layout_avoid,
        "extra_required":    extra_required,
        "extra_forbidden":   extra_forbidden,
    }
