"""
visual_coherence_engine.py  —  v1.1.0
======================================
Règle tripartite stricte image ↔ palette ↔ design reference.

CASE 1 — image_drives_palette            (reference_type = "image")
    Une image de référence est fournie.
    → Analyser l'image (hue dominante, luminosité, saturation, température, contraste)
    → Générer la palette DEPUIS l'image

CASE 2 — palette_drives_image            (reference_type = "none")
    Aucune image de référence (cas standard du pipeline).
    → Palette d'abord (fournie ou dérivée de visual_intent + context)
    → Calculer les ajustements d'image : duotone / overlay / filter / blend_mode
    → Garantir lisibilité WCAG AA

CASE 3 — design_reference_drives_plan    (reference_type = "screenshot" | "mockup")
    Une référence design (screenshot, maquette, landing page) est fournie.
    → Extraire les principes structurels (dominance, density, hierarchy, spacing, rhythm)
    → Ces principes alimentent visual_intent + design_plan comme inputs durs
    → La palette est calculée indépendamment (CASE 2 logic)
    → Ne pas copier pixel-perfect — extraire et réinterpréter

Entrée :
    visual_intent    : dict         (depuis visual_intent_engine)
    context          : dict         (seed complet)
    palette          : dict | None  (depuis color_palette, requis si pas d'image)
    reference_image  : str | None   (chemin local ou URL)
    reference_type   : str          ("none" | "image" | "screenshot" | "mockup")

Sortie :
    {
      "reference_mode"    : "image_drives_palette" | "palette_drives_image"
                          | "design_reference_drives_plan",
      "reference_type"    : str,
      "reference_analysis": {                    # empty dict pour CASE 1 et 2
          "dominance"       : "text | image | balanced",
          "density"         : "low | medium | high",
          "hierarchy"       : "calm | strong | aggressive",
          "spacing"         : "tight | balanced | airy",
          "composition_bias": { dominance, density, asymmetry, rhythm },
          "palette_hint"    : { dominant_hue, brightness, saturation, temperature },
          "_source"         : "vision_api | pixel_analysis | fallback",
      },
      "palette"           : { ... },
      "image_adjustments" : { duotone, overlay_color, overlay_opacity, filter, blend_mode },
      "readability_rules" : { text_on_image, min_overlay_for_wcag, gradient_scrim,
                              recommended_text_color },
      "conflicts"         : list[str],
    }
"""

from __future__ import annotations

import base64
import colorsys
import json
import math
import os
import struct
import sys
import urllib.request
import zlib
from pathlib import Path
from typing import Any, Optional

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent.parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def run(
    visual_intent: dict,
    context: dict,
    palette: Optional[dict] = None,
    reference_image: Optional[str] = None,
    reference_type: str = "none",
) -> dict:
    """
    Point d'entrée principal.

    Args:
        visual_intent   : dict depuis visual_intent_engine (emotion, mood, archetype…)
        context         : dict seed complet (name, family, seed_id, mode…)
        palette         : dict depuis color_palette (requis si reference_image=None)
        reference_image : chemin local (.jpg/.png) ou URL (optionnel)
        reference_type  : "none" | "image" | "screenshot" | "mockup"
                          "none"       → CASE 2 palette_drives_image
                          "image"      → CASE 1 image_drives_palette
                          "screenshot" → CASE 3 design_reference_drives_plan
                          "mockup"     → CASE 3 design_reference_drives_plan

    Returns:
        dict complet avec reference_mode, reference_type, reference_analysis,
        palette, image_adjustments, readability_rules, conflicts
    """
    conflicts: list[str] = []
    ref_analysis: dict = {}

    if reference_type in ("screenshot", "mockup") and reference_image:
        # CASE 3 — design reference drives plan
        ref_mode = "design_reference_drives_plan"
        ref_analysis = _analyze_design_reference(reference_image)
        if ref_analysis.get("_source") == "fallback":
            conflicts.append("Design reference analysis failed — using pixel fallback")
        # Palette still computed independently (CASE 2 logic)

    elif reference_type == "image" and reference_image:
        # CASE 1 — image drives palette
        img_data = _analyze_image(reference_image)
        if img_data.get("error"):
            conflicts.append(f"Image analysis failed: {img_data['error']} — fallback to palette_drives_image")
            ref_mode = "palette_drives_image"
        else:
            ref_mode = "image_drives_palette"
            derived_palette = _generate_palette_from_image(img_data, visual_intent, context)
            if palette:
                conf = _detect_palette_conflicts(derived_palette, palette)
                conflicts.extend(conf)
            palette = derived_palette

    elif reference_image and reference_type == "none":
        # Legacy: reference_image provided without reference_type → infer CASE 1
        img_data = _analyze_image(reference_image)
        if img_data.get("error"):
            conflicts.append(f"Image analysis failed: {img_data['error']} — fallback to palette_drives_image")
            ref_mode = "palette_drives_image"
        else:
            ref_mode = "image_drives_palette"
            derived_palette = _generate_palette_from_image(img_data, visual_intent, context)
            if palette:
                conflicts.extend(_detect_palette_conflicts(derived_palette, palette))
            palette = derived_palette

    else:
        # CASE 2 — palette drives image
        ref_mode = "palette_drives_image"

    if palette is None:
        conflicts.append("No palette provided and no reference image — using emergency fallback palette")
        palette = _emergency_palette(context)

    dark_mode = _is_dark(context, palette)
    image_adjustments = _compute_image_adjustments(palette, dark_mode)
    readability_rules = _compute_readability_rules(palette, image_adjustments, dark_mode)
    conflicts.extend(_check_wcag(palette, image_adjustments, readability_rules))

    return {
        "reference_mode":     ref_mode,
        "reference_type":     reference_type,
        "reference_analysis": ref_analysis,
        "palette":            palette,
        "image_adjustments":  image_adjustments,
        "readability_rules":  readability_rules,
        "conflicts":          conflicts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CASE 1 — Image analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_image(path_or_url: str) -> dict:
    """Public wrapper around _analyze_image."""
    return _analyze_image(path_or_url)


def _analyze_image(path_or_url: str) -> dict:
    """
    Analyse une image et retourne ses caractéristiques visuelles.
    Utilise PIL si disponible, sinon un parser PNG minimaliste.

    Returns:
        {
          dominant_hue   : float  (0–360)
          brightness     : float  (0–1)
          saturation     : float  (0–1)
          temperature    : "warm" | "neutral" | "cool"
          contrast_profile : "low" | "medium" | "high"
          dominant_hex   : "#RRGGBB"
          error          : str | None
        }
    """
    try:
        pixels = _load_pixels(path_or_url)
    except Exception as exc:
        return {"error": str(exc)}

    if not pixels:
        return {"error": "No pixels extracted"}

    # Travailler sur un échantillon max 5000 px pour la performance
    step = max(1, len(pixels) // 5000)
    sample = pixels[::step]

    # Convertir en HSL
    hsl_list = []
    for r, g, b in sample:
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        hsl_list.append((h * 360, l, s))

    # Hue dominante — moyenne circulaire pondérée par saturation
    dominant_hue = _circular_mean_hue(hsl_list)

    # Luminosité et saturation moyennes
    avg_brightness = sum(l for _, l, _ in hsl_list) / len(hsl_list)
    avg_saturation = sum(s for _, _, s in hsl_list) / len(hsl_list)

    # Température : basée sur hue dominante
    temperature = _hue_to_temperature(dominant_hue)

    # Profil de contraste : écart-type des luminosités
    mean_l = avg_brightness
    std_l = math.sqrt(sum((l - mean_l) ** 2 for _, l, _ in hsl_list) / len(hsl_list))
    if std_l < 0.12:
        contrast_profile = "low"
    elif std_l < 0.25:
        contrast_profile = "medium"
    else:
        contrast_profile = "high"

    # Couleur dominante en hex
    dominant_hex = _hsl_to_hex(dominant_hue, avg_saturation * 0.8, avg_brightness)

    return {
        "dominant_hue":      round(dominant_hue, 1),
        "brightness":        round(avg_brightness, 3),
        "saturation":        round(avg_saturation, 3),
        "temperature":       temperature,
        "contrast_profile":  contrast_profile,
        "dominant_hex":      dominant_hex,
        "error":             None,
    }


def _circular_mean_hue(hsl_list: list[tuple]) -> float:
    """Moyenne circulaire des hues, pondérée par saturation."""
    sin_sum = cos_sum = 0.0
    for h, _, s in hsl_list:
        rad = math.radians(h)
        sin_sum += math.sin(rad) * s
        cos_sum += math.cos(rad) * s
    if sin_sum == 0 and cos_sum == 0:
        return 0.0
    angle = math.degrees(math.atan2(sin_sum, cos_sum))
    return angle % 360


def _hue_to_temperature(hue: float) -> str:
    """Warm = rouge/orange/jaune (0-60° et 330-360°), cool = bleu/vert (120-270°)."""
    if hue <= 60 or hue >= 330:
        return "warm"
    elif 180 <= hue <= 270:
        return "cool"
    else:
        return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# CASE 1 — Générer palette depuis image
# ─────────────────────────────────────────────────────────────────────────────

def generate_palette_from_image(img_data: dict, visual_intent: dict, context: dict) -> dict:
    """Public wrapper."""
    return _generate_palette_from_image(img_data, visual_intent, context)


def _generate_palette_from_image(img_data: dict, visual_intent: dict, context: dict) -> dict:
    """
    Génère une palette cohérente à partir des données d'image analysée.
    La couleur primaire est dérivée de la hue dominante + saturation de l'image.
    """
    h = img_data["dominant_hue"]
    s = max(0.35, min(0.85, img_data["saturation"] * 1.2))  # boost légèrement
    l_base = 0.45  # primaire à luminosité médiane

    dark_mode = img_data["brightness"] < 0.45
    bg_l = 0.08 if dark_mode else 0.97
    fg_l = 0.92 if dark_mode else 0.10

    primary_hex = _hsl_to_hex(h, s, l_base)
    primary_light = _hsl_to_hex(h, s * 0.7, min(0.90, l_base + 0.28))
    primary_dark  = _hsl_to_hex(h, s,        max(0.10, l_base - 0.22))

    # Accent : hue complémentaire (+150° – +210°)
    acc_h = (h + 180) % 360
    accent_hex = _hsl_to_hex(acc_h, s * 0.75, 0.50)

    return {
        "mode":       "dark" if dark_mode else "light",
        "primary":    primary_hex,
        "primary_light": primary_light,
        "primary_dark":  primary_dark,
        "accent":     accent_hex,
        "background": _hsl_to_hex(h, 0.05 if not dark_mode else 0.08, bg_l),
        "foreground": _hsl_to_hex(h, 0.04, fg_l),
        "_source":    "image_driven",
        "_image_hue": h,
        "_image_brightness": img_data["brightness"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CASE 2 — Ajustements image depuis palette
# ─────────────────────────────────────────────────────────────────────────────

def compute_image_adjustments(palette: dict, dark_mode: bool) -> dict:
    """Public wrapper."""
    return _compute_image_adjustments(palette, dark_mode)


def _compute_image_adjustments(palette: dict, dark_mode: bool) -> dict:
    """
    Calcule les paramètres CSS d'overlay pour intégrer l'image dans la palette.

    Technique principale : grayscale(1) sur l'image + overlay mix-blend-mode:color
    → l'image prend la teinte brand sans détruire la structure lumineuse.

    overlay_opacity :
        dark mode  → 0.55-0.65  (overlay fort pour maintenir la lisibilité)
        light mode → 0.35-0.45  (overlay léger, laisser la photo respirer)
    """
    primary = palette.get("primary", "#4A7CFF")
    p_h, p_l, p_s = _hex_to_hsl(primary)

    # Adapter l'opacité selon la luminosité de la primaire et le mode
    if dark_mode:
        # Mode sombre : overlay plus fort
        base_op = 0.60
        if p_l > 0.6:
            base_op = 0.55  # primaire claire en dark → moins d'overlay
    else:
        base_op = 0.42
        if p_l < 0.3:
            base_op = 0.48  # primaire très foncée en light → un peu plus d'overlay

    # Saturation de la primaire : si très désaturée, augmenter l'opacité
    if p_s < 0.25:
        base_op = min(0.75, base_op + 0.12)

    # Filtre CSS sur l'image
    grayscale = 1.0
    contrast  = 1.05 if dark_mode else 1.10
    css_filter = f"grayscale({grayscale}) contrast({contrast})"

    return {
        "duotone":          True,
        "overlay_color":    primary,
        "overlay_opacity":  round(base_op, 2),
        "filter":           css_filter,
        "blend_mode":       "color",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Règles de lisibilité WCAG
# ─────────────────────────────────────────────────────────────────────────────

def compute_readability_rules(palette: dict, image_adjustments: dict, dark_mode: bool) -> dict:
    """Public wrapper."""
    return _compute_readability_rules(palette, image_adjustments, dark_mode)


def _compute_readability_rules(palette: dict, image_adjustments: dict, dark_mode: bool) -> dict:
    """
    Calcule les règles de lisibilité pour le texte posé sur image.

    Stratégie :
    - Calculer le contraste effectif après overlay
    - Si insuffisant → recommander un scrim dégradé supplémentaire
    - Déterminer la couleur de texte recommandée (blanc ou noir)
    """
    primary = palette.get("primary", "#4A7CFF")
    overlay_op = image_adjustments["overlay_opacity"]
    bg = palette.get("background", "#FFFFFF")

    # Couleur résultante approximative après overlay sur image "grisée"
    # Image grisée ≈ luminosité moyenne (on simule avec gris 50%)
    img_avg_hex = "#808080"
    blended = _blend_color(img_avg_hex, primary, overlay_op, "color")

    # Contraste blanc sur blended et noir sur blended
    contrast_white = _wcag_contrast(blended, "#FFFFFF")
    contrast_black = _wcag_contrast(blended, "#000000")

    recommended_text = "#FFFFFF" if contrast_white >= contrast_black else "#000000"
    best_contrast    = max(contrast_white, contrast_black)

    # WCAG AA : 4.5 pour texte normal, 3.0 pour large
    text_on_image = best_contrast >= 3.0  # seuil large pour hero

    # Opacité minimale pour atteindre 3.0 de contraste
    min_op = _min_overlay_for_wcag(primary, img_avg_hex, target_ratio=3.0)

    # Recommander un scrim si contraste insuffisant même avec overlay max raisonnable
    gradient_scrim = not text_on_image or best_contrast < 4.5

    return {
        "text_on_image":          text_on_image,
        "min_overlay_for_wcag":   round(min_op, 2),
        "gradient_scrim":         gradient_scrim,
        "recommended_text_color": recommended_text,
        "_contrast_white":        round(contrast_white, 2),
        "_contrast_black":        round(contrast_black, 2),
    }


def _min_overlay_for_wcag(overlay_color: str, bg_color: str, target_ratio: float = 3.0) -> float:
    """Trouve l'opacité minimale de l'overlay pour atteindre target_ratio en WCAG."""
    for op_int in range(0, 101):
        op = op_int / 100
        blended = _blend_color(bg_color, overlay_color, op, "normal")
        if _wcag_contrast(blended, "#FFFFFF") >= target_ratio:
            return op
        if _wcag_contrast(blended, "#000000") >= target_ratio:
            return op
    return 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Détection de conflits
# ─────────────────────────────────────────────────────────────────────────────

def _detect_palette_conflicts(derived: dict, provided: dict) -> list[str]:
    """Compare la palette dérivée de l'image avec la palette fournie."""
    conflicts = []
    d_h, d_l, d_s = _hex_to_hsl(derived.get("primary", "#888888"))
    p_h, p_l, p_s = _hex_to_hsl(provided.get("primary", "#888888"))
    hue_diff = abs(d_h - p_h)
    hue_diff = min(hue_diff, 360 - hue_diff)
    if hue_diff > 60:
        conflicts.append(
            f"Image hue ({d_h:.0f}°) conflicts with provided palette hue ({p_h:.0f}°) — diff {hue_diff:.0f}°"
        )
    return conflicts


def _check_wcag(palette: dict, image_adjustments: dict, readability_rules: dict) -> list[str]:
    """Vérifie les violations WCAG et retourne la liste des avertissements."""
    conflicts = []
    if not readability_rules["text_on_image"]:
        conflicts.append(
            "WCAG WARNING: text-on-image contrast insufficient — gradient_scrim required"
        )
    min_op = readability_rules["min_overlay_for_wcag"]
    actual_op = image_adjustments["overlay_opacity"]
    if actual_op < min_op:
        conflicts.append(
            f"WCAG WARNING: overlay_opacity {actual_op} < min required {min_op} — increase or add scrim"
        )
    return conflicts


# ─────────────────────────────────────────────────────────────────────────────
# CASE 3 — Design reference drives plan
# ─────────────────────────────────────────────────────────────────────────────

_DESIGN_REFERENCE_PROMPT = """Analyze this design reference (UI mockup, website screenshot, landing page).
Extract structural and compositional principles only. Do NOT describe content or text.

Return ONLY a valid JSON object:
{
  "dominance": "text" | "image" | "balanced",
  "density": "low" | "medium" | "high",
  "hierarchy": "calm" | "strong" | "aggressive",
  "spacing": "tight" | "balanced" | "airy",
  "asymmetry": "low" | "medium" | "high",
  "rhythm": "regular" | "alternating" | "chaotic"
}

Definitions:
- dominance: is text or imagery visually dominant in the layout?
- density: how much content is packed per viewport area?
- hierarchy: how clearly are visual elements ranked? calm=subtle, strong=clear, aggressive=extreme contrast
- spacing: how much white/negative space is used overall?
- asymmetry: how off-balance/asymmetric is the layout?
- rhythm: are section heights/content amounts regular or varied?

Return ONLY the JSON. No explanation. No markdown.
"""

_DR_DOMINANCE  = {"text", "image", "balanced"}
_DR_DENSITY    = {"low", "medium", "high"}
_DR_HIERARCHY  = {"calm", "strong", "aggressive"}
_DR_SPACING    = {"tight", "balanced", "airy"}
_DR_ASYMMETRY  = {"low", "medium", "high"}
_DR_RHYTHM     = {"regular", "alternating", "chaotic"}


def analyze_design_reference(
    path_or_url: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Public wrapper — analyse une référence design (screenshot, mockup, UI).
    Retourne reference_analysis prêt à alimenter visual_intent + design_plan.
    """
    return _analyze_design_reference(path_or_url, api_key=api_key)


def _analyze_design_reference(path_or_url: str, api_key: Optional[str] = None) -> dict:
    """
    CASE 3 — analyse une référence design (screenshot, mockup, landing page).

    Deux niveaux d'analyse :
    1. PIL/stdlib → palette_hint + heuristiques pixel
    2. Anthropic vision API (optionnel, graceful fallback) → analyse structurelle précise

    Returns reference_analysis dict :
    {
      dominance, density, hierarchy, spacing,
      composition_bias: { dominance, density, asymmetry, rhythm },
      palette_hint: { dominant_hue, brightness, saturation, temperature },
      _source: "vision_api" | "pixel_analysis" | "fallback"
    }
    """
    # Pixel-level analysis (toujours disponible)
    img_data = _analyze_image(path_or_url)
    if img_data.get("error"):
        return _fallback_reference_analysis()

    palette_hint = {
        "dominant_hue": img_data.get("dominant_hue", 0.0),
        "brightness":   img_data.get("brightness", 0.5),
        "saturation":   img_data.get("saturation", 0.3),
        "temperature":  img_data.get("temperature", "neutral"),
    }

    # Heuristiques pixel
    pixel_struct = _pixel_structural_inference(img_data)

    # Vision API (meilleure précision, graceful fallback)
    _api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    vision_struct: dict = {}
    if _api_key:
        vision_struct = _vision_structural_analysis(path_or_url, _api_key)

    # Merge : vision prime si disponible
    def _v(vision_val: Any, pixel_val: str, valid: set) -> str:
        return vision_val if vision_val in valid else pixel_val

    dominance = _v(vision_struct.get("dominance"), pixel_struct["dominance"], _DR_DOMINANCE)
    density   = _v(vision_struct.get("density"),   pixel_struct["density"],   _DR_DENSITY)
    hierarchy = _v(vision_struct.get("hierarchy"), pixel_struct["hierarchy"], _DR_HIERARCHY)
    spacing   = _v(vision_struct.get("spacing"),   pixel_struct["spacing"],   _DR_SPACING)
    asymmetry = _v(vision_struct.get("asymmetry"), pixel_struct["asymmetry"], _DR_ASYMMETRY)
    rhythm    = _v(vision_struct.get("rhythm"),    pixel_struct["rhythm"],    _DR_RHYTHM)

    # Mapping spacing → density (plus sémantique pour le design plan)
    _spacing_density = {"airy": "low", "balanced": "medium", "tight": "high"}
    cb_density = _spacing_density.get(spacing, density)

    return {
        "dominance":  dominance,
        "density":    density,
        "hierarchy":  hierarchy,
        "spacing":    spacing,
        "composition_bias": {
            "dominance":  dominance,
            "density":    cb_density,
            "asymmetry":  asymmetry,
            "rhythm":     rhythm,
        },
        "palette_hint": palette_hint,
        "_source": "vision_api" if vision_struct else "pixel_analysis",
    }


def _pixel_structural_inference(img_data: dict) -> dict:
    """
    Infère les principes structurels depuis les données pixel uniquement.
    Heuristiques raisonnables — moins précises que la vision API.
    """
    brightness = img_data.get("brightness", 0.5)
    saturation = img_data.get("saturation", 0.3)
    contrast   = img_data.get("contrast_profile", "medium")

    # Dominance : image saturée + sombre → image-driven ; claire + peu saturée → text-driven
    if saturation > 0.45 and brightness < 0.60:
        dominance = "image"
    elif saturation < 0.18 or brightness > 0.78:
        dominance = "text"
    else:
        dominance = "balanced"

    # Density : du profil de contraste
    density = contrast  # "low" | "medium" | "high" (same values)

    # Hierarchy : de la saturation
    if saturation > 0.50:
        hierarchy = "aggressive"
    elif saturation > 0.25:
        hierarchy = "strong"
    else:
        hierarchy = "calm"

    # Spacing : de la luminosité (clair ≈ plus d'espace blanc)
    if brightness > 0.72:
        spacing = "airy"
    elif brightness < 0.35:
        spacing = "tight"
    else:
        spacing = "balanced"

    # Asymmetry : difficile à déduire des pixels seuls → "medium" par défaut
    asymmetry = "medium"

    # Rhythm : du profil de contraste
    rhythm = "regular" if contrast == "low" else "alternating"

    return {
        "dominance": dominance,
        "density":   density,
        "hierarchy": hierarchy,
        "spacing":   spacing,
        "asymmetry": asymmetry,
        "rhythm":    rhythm,
    }


def _vision_structural_analysis(path_or_url: str, api_key: str) -> dict:
    """
    Appelle l'API vision via MODEL_EXECUTOR pour l'analyse structurelle d'une référence design.
    Retourne dict partiel ou {} si indisponible.
    api_key conservé pour compatibilité de signature.
    """
    raw_data = _load_raw_image_data(path_or_url)
    if not raw_data:
        return {}
    b64_data, media_type = raw_data

    try:
        result = model_execute(
            "img2text",
            _DESIGN_REFERENCE_PROMPT,
            data={
                "image_base64":   b64_data,
                "media_type":     media_type,
                "max_tokens":     256,
                "model_override": "claude-haiku-4-5-20251001",
            },
            provider="anthropic",
        )
        raw = result["result"]
    except Exception:
        return {}

    try:
        raw = raw.strip()
        if "```" in raw:
            for block in raw.split("```"):
                s = block.strip().lstrip("json").strip()
                if s.startswith("{"):
                    raw = s
                    break
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end > start:
            return json.loads(raw[start:end + 1])
    except Exception:
        pass
    return {}


def _load_raw_image_data(path_or_url: str) -> Optional[tuple]:
    """Charge une image et retourne (base64_data, media_type) ou None."""
    try:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            with urllib.request.urlopen(path_or_url, timeout=10) as resp:
                data = resp.read()
                ct = resp.headers.get("Content-Type", "image/jpeg")
                media_type = ct.split(";")[0].strip()
        else:
            p = Path(path_or_url)
            if not p.exists():
                return None
            data = p.read_bytes()
            _ext = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".webp": "image/webp", ".gif": "image/gif"}
            media_type = _ext.get(p.suffix.lower(), "image/jpeg")
        return base64.b64encode(data).decode("utf-8"), media_type
    except Exception:
        return None


def _fallback_reference_analysis() -> dict:
    """Fallback générique quand l'analyse d'image échoue."""
    return {
        "dominance":  "balanced",
        "density":    "medium",
        "hierarchy":  "strong",
        "spacing":    "balanced",
        "composition_bias": {
            "dominance": "balanced",
            "density":   "medium",
            "asymmetry": "medium",
            "rhythm":    "alternating",
        },
        "palette_hint": {
            "dominant_hue": 180.0,
            "brightness":   0.5,
            "saturation":   0.3,
            "temperature":  "neutral",
        },
        "_source": "fallback",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utilitaires couleur
# ─────────────────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return h * 360, l, s


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    # colorsys uses HLS order: hls_to_rgb(h, l, s)
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return _rgb_to_hex(round(r * 255), round(g * 255), round(b * 255))


def _relative_luminance(hex_color: str) -> float:
    """WCAG 2.1 relative luminance (0=black, 1=white)."""
    r, g, b = _hex_to_rgb(hex_color)
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _wcag_contrast(c1: str, c2: str) -> float:
    """Ratio de contraste WCAG entre deux couleurs hex."""
    l1 = _relative_luminance(c1)
    l2 = _relative_luminance(c2)
    lighter = max(l1, l2)
    darker  = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _blend_color(base_hex: str, overlay_hex: str, opacity: float, blend_mode: str) -> str:
    """
    Simule un blend CSS simplifié (mode 'normal' alpha compositing ou 'color').
    Pour 'color' : conserve luminosité base + hue/saturation overlay.
    """
    br, bg_, bb = _hex_to_rgb(base_hex)
    or_, og, ob = _hex_to_rgb(overlay_hex)

    if blend_mode == "normal":
        nr = round(or_ * opacity + br * (1 - opacity))
        ng = round(og * opacity + bg_ * (1 - opacity))
        nb = round(ob * opacity + bb * (1 - opacity))
        return _rgb_to_hex(
            max(0, min(255, nr)),
            max(0, min(255, ng)),
            max(0, min(255, nb)),
        )
    elif blend_mode == "color":
        # Prendre luminosité de la base, hue+saturation de l'overlay
        bh, bl, bs = colorsys.rgb_to_hls(br / 255.0, bg_ / 255.0, bb / 255.0)
        oh, ol, os_ = colorsys.rgb_to_hls(or_ / 255.0, og / 255.0, ob / 255.0)
        # Interpoler selon opacity
        rh = oh * opacity + bh * (1 - opacity)
        rs = os_ * opacity + bs * (1 - opacity)
        rr, rg, rb = colorsys.hls_to_rgb(rh, bl, rs)  # garder luminosité base
        return _rgb_to_hex(round(rr * 255), round(rg * 255), round(rb * 255))
    else:
        # Fallback : normal alpha
        return _blend_color(base_hex, overlay_hex, opacity, "normal")


def _is_dark(context: dict, palette: dict) -> bool:
    if context.get("mode") == "dark":
        return True
    if context.get("mode") == "light":
        return False
    return palette.get("mode", "light") == "dark"


def _emergency_palette(context: dict) -> dict:
    mode = context.get("mode", "light")
    return {
        "mode": mode,
        "primary": "#4A7CFF",
        "primary_light": "#7FA0FF",
        "primary_dark": "#2A5CDF",
        "accent": "#FF6B4A",
        "background": "#0E1117" if mode == "dark" else "#F8F9FA",
        "foreground": "#F0F0F0" if mode == "dark" else "#1A1A1A",
        "_source": "emergency_fallback",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chargement pixels (PIL ou parser PNG minimal)
# ─────────────────────────────────────────────────────────────────────────────

def _load_pixels(path_or_url: str) -> list[tuple[int, int, int]]:
    """
    Charge une image et retourne la liste de pixels RGB.
    Essaie PIL/Pillow en premier, puis un parser PNG minimaliste.
    """
    try:
        from PIL import Image
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            import io
            with urllib.request.urlopen(path_or_url, timeout=10) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
        else:
            img = Image.open(path_or_url).convert("RGB")
        # Redimensionner pour performance
        img.thumbnail((200, 200))
        return list(img.getdata())
    except ImportError:
        pass  # PIL non disponible → parser minimal

    # Parser PNG minimaliste (stdlib uniquement)
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        with urllib.request.urlopen(path_or_url, timeout=10) as resp:
            raw = resp.read()
    else:
        raw = Path(path_or_url).read_bytes()

    return _parse_png_pixels(raw)


def _parse_png_pixels(data: bytes) -> list[tuple[int, int, int]]:
    """
    Parser PNG minimal utilisant uniquement stdlib (zlib + struct).
    Supporte PNG RGB et RGBA, bit depth 8.
    """
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Not a valid PNG file")

    # Lire chunks
    ihdr = None
    idat_data = b""
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos+4])[0]
        ctype  = data[pos+4:pos+8]
        chunk  = data[pos+8:pos+8+length]
        pos   += 12 + length
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat_data += chunk
        elif ctype == b"IEND":
            break

    if not ihdr:
        raise ValueError("PNG: no IHDR chunk")

    width, height, bit_depth, color_type = ihdr[0], ihdr[1], ihdr[2], ihdr[3]
    if bit_depth != 8:
        raise ValueError(f"PNG: unsupported bit depth {bit_depth}")
    if color_type not in (2, 6):  # 2=RGB, 6=RGBA
        raise ValueError(f"PNG: unsupported color_type {color_type}")

    channels = 4 if color_type == 6 else 3
    raw = zlib.decompress(idat_data)

    pixels = []
    stride = width * channels + 1  # +1 for filter byte
    for y in range(height):
        row_start = y * stride
        filt = raw[row_start]
        row  = bytearray(raw[row_start+1:row_start+1+width*channels])

        # Appliquer filtre PNG (Sub/Up/Average/Paeth simplifié)
        if filt == 1:  # Sub
            for x in range(channels, len(row)):
                row[x] = (row[x] + row[x - channels]) & 0xFF
        elif filt == 2 and y > 0:  # Up
            prev = bytearray(raw[(y-1)*stride+1:(y-1)*stride+1+width*channels])
            for x in range(len(row)):
                row[x] = (row[x] + prev[x]) & 0xFF
        # Filtres 3/4 ignorés pour simplifier (rare en pratique dans photos JPEG-to-PNG)

        for x in range(0, width * channels, channels):
            pixels.append((row[x], row[x+1], row[x+2]))

    return pixels
