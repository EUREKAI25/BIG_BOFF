#!/usr/bin/env python3
"""
Tests unitaires — visual_intent_engine

Zéro API. Zéro réseau. Zéro dépendance externe.
Référence image mockée pour les tests de mode reference/hybrid.
"""

import sys
from pathlib import Path

# Path setup
_MODULE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_MODULE_DIR))

from src.visual_intent_engine import (
    generate_visual_intent,
    intent_to_plan_overrides,
    STYLE_FAMILIES,
    ARCHETYPE_STYLE_MAP,
    EMOTIONAL_GOAL_ADJUSTMENTS,
    BRAND_POSITIONING_ADJUSTMENTS,
    _detect_mode,
    _detect_style_family,
    _build_strong_intent,
    _build_reference_intent,
    _blend_hybrid,
    _apply_brief_signals,
    _apply_user_constraints,
    _apply_context_adjustments,
    _extract_context,
    _validate_and_clean,
    _default_intent,
    _VALID_MODES, _VALID_INTENSITY, _VALID_DOMINANCE, _VALID_DENSITY,
    _VALID_ASYMMETRY, _VALID_RHYTHM, _VALID_CONTRAST, _VALID_PALETTE,
    _VALID_HIERARCHY, _VALID_WEIGHT, _VALID_TECHNIQUES,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de test
# ─────────────────────────────────────────────────────────────────────────────

_BRIEF_NEUTRAL   = "Agence conseil en communication"
_BRIEF_LUXURY    = "Maison de luxe parisienne, maroquinerie haut de gamme"
_BRIEF_TECH      = "Plateforme SaaS analytics pour équipes data"
_BRIEF_FESTIVAL  = "Festival de musique électronique, 3 jours, Marseille"


PASSED = []
FAILED = []


def _assert(condition: bool, msg: str) -> None:
    if condition:
        PASSED.append(msg)
        print(f"  ✅  {msg}")
    else:
        FAILED.append(msg)
        print(f"  ❌  FAIL — {msg}")


def _validate_schema(intent: dict) -> list[str]:
    """Valide la conformité complète du schéma de sortie. Retourne les violations."""
    errors = []

    if intent.get("mode") not in _VALID_MODES:
        errors.append(f"mode invalide: {intent.get('mode')!r}")

    ad = intent.get("art_direction", {})
    if not isinstance(ad, dict):
        errors.append("art_direction manquant")
    else:
        if ad.get("intensity") not in _VALID_INTENSITY:
            errors.append(f"intensity invalide: {ad.get('intensity')!r}")
        if not isinstance(ad.get("personality"), list):
            errors.append("personality n'est pas une liste")
        if not isinstance(ad.get("style_family"), str):
            errors.append("style_family n'est pas une string")
        if not isinstance(ad.get("tone"), str):
            errors.append("tone n'est pas une string")

    cb = intent.get("composition_bias", {})
    if not isinstance(cb, dict):
        errors.append("composition_bias manquant")
    else:
        if cb.get("dominance") not in _VALID_DOMINANCE:
            errors.append(f"dominance invalide: {cb.get('dominance')!r}")
        if cb.get("density") not in _VALID_DENSITY:
            errors.append(f"density invalide: {cb.get('density')!r}")
        if cb.get("asymmetry") not in _VALID_ASYMMETRY:
            errors.append(f"asymmetry invalide: {cb.get('asymmetry')!r}")
        if cb.get("rhythm") not in _VALID_RHYTHM:
            errors.append(f"rhythm invalide: {cb.get('rhythm')!r}")

    techniques = intent.get("visual_techniques", [])
    if not isinstance(techniques, list):
        errors.append("visual_techniques n'est pas une liste")
    else:
        invalid = [t for t in techniques if t not in _VALID_TECHNIQUES]
        if invalid:
            errors.append(f"techniques invalides: {invalid}")

    cs = intent.get("color_strategy", {})
    if not isinstance(cs, dict):
        errors.append("color_strategy manquant")
    else:
        if cs.get("contrast") not in _VALID_CONTRAST:
            errors.append(f"contrast invalide: {cs.get('contrast')!r}")
        if cs.get("palette_type") not in _VALID_PALETTE:
            errors.append(f"palette_type invalide: {cs.get('palette_type')!r}")

    ts = intent.get("typography_strategy", {})
    if not isinstance(ts, dict):
        errors.append("typography_strategy manquant")
    else:
        if ts.get("hierarchy_strength") not in _VALID_HIERARCHY:
            errors.append(f"hierarchy_strength invalide: {ts.get('hierarchy_strength')!r}")
        if ts.get("weight_contrast") not in _VALID_WEIGHT:
            errors.append(f"weight_contrast invalide: {ts.get('weight_contrast')!r}")

    ct = intent.get("constraints", {})
    if not isinstance(ct, dict):
        errors.append("constraints manquant")
    else:
        if not isinstance(ct.get("force"), list):
            errors.append("constraints.force n'est pas une liste")
        if not isinstance(ct.get("avoid"), list):
            errors.append("constraints.avoid n'est pas une liste")

    ctx = intent.get("context")
    if ctx is None:
        errors.append("context manquant")
    elif not isinstance(ctx, dict):
        errors.append("context n'est pas un dict")
    else:
        for field in ("product_type", "target_audience", "emotional_goal", "brand_positioning"):
            if not isinstance(ctx.get(field), str):
                errors.append(f"context.{field} manquant ou non-str")

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Imports et constantes
# ─────────────────────────────────────────────────────────────────────────────

def test_imports() -> None:
    print("\n  TEST 1 — Imports et constantes")
    _assert(len(STYLE_FAMILIES) == 6, "6 style families définies")
    _assert("editorial_luxury" in STYLE_FAMILIES, "editorial_luxury présent")
    _assert("brutalist"        in STYLE_FAMILIES, "brutalist présent")
    _assert("tech_minimal"     in STYLE_FAMILIES, "tech_minimal présent")
    _assert("experimental_grid" in STYLE_FAMILIES, "experimental_grid présent")
    _assert("premium_brand"    in STYLE_FAMILIES, "premium_brand présent")
    _assert("bold_marketing"   in STYLE_FAMILIES, "bold_marketing présent")
    _assert(len(ARCHETYPE_STYLE_MAP) > 5,          "ARCHETYPE_STYLE_MAP peuplé")
    _assert(callable(generate_visual_intent),      "generate_visual_intent callable")
    _assert(callable(intent_to_plan_overrides),    "intent_to_plan_overrides callable")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Mode detection
# ─────────────────────────────────────────────────────────────────────────────

def test_mode_detection() -> None:
    print("\n  TEST 2 — Détection de mode")

    # default : aucun input fort
    mode, sf = _detect_mode(None, None, None)
    _assert(mode == "default" and sf is None, "mode=default sans inputs")

    # default : style_dna sans archetype fort
    mode, sf = _detect_mode({"archetype": "unknown_archetype"}, None, None)
    _assert(mode == "default", "mode=default pour archetype inconnu")

    # strong via constraints.force
    mode, sf = _detect_mode(None, None, {"force": ["brutalist"], "avoid": []})
    _assert(mode == "strong" and sf == "brutalist", "mode=strong via constraints.force brutalist")

    # strong via constraints.force pour autre famille
    mode, sf = _detect_mode(None, None, {"force": ["editorial_luxury"]})
    _assert(mode == "strong" and sf == "editorial_luxury", "mode=strong via constraints.force editorial_luxury")

    # strong via style_dna.style_family
    mode, sf = _detect_mode({"style_family": "tech_minimal"}, None, None)
    _assert(mode == "strong" and sf == "tech_minimal", "mode=strong via style_dna.style_family")

    # strong via archetype fort
    mode, sf = _detect_mode({"archetype": "editorial_magazine"}, None, None)
    _assert(mode == "strong" and sf == "editorial_luxury",
            f"mode=strong via editorial_magazine archetype (sf={sf})")

    # reference : image fournie, pas de style
    mode, sf = _detect_mode(None, "ref.png", None)
    _assert(mode == "reference" and sf is None, "mode=reference avec image, sans style")

    # hybrid : image + style
    mode, sf = _detect_mode(None, "ref.png", {"force": ["brutalist"]})
    _assert(mode == "hybrid" and sf == "brutalist", "mode=hybrid avec image + brutalist")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Mode default
# ─────────────────────────────────────────────────────────────────────────────

def test_default_mode() -> None:
    print("\n  TEST 3 — Mode default")

    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL)
    _assert(intent["mode"] == "default", "mode=default")

    errors = _validate_schema(intent)
    _assert(len(errors) == 0, f"schéma valide (erreurs={errors})")

    _assert(intent["art_direction"]["intensity"] == "low",  "intensity=low en default")
    # asymmetry et density sont maintenant influencés par le contexte détecté dans le brief
    _assert(intent["composition_bias"]["asymmetry"] in _VALID_ASYMMETRY, "asymmetry valide en default")
    _assert(intent["composition_bias"]["density"]   in _VALID_DENSITY,   "density valide en default")
    _assert(isinstance(intent["visual_techniques"], list), "visual_techniques est une liste")
    _assert(len(intent["constraints"]["force"]) == 0, "constraints.force vide en default")
    _assert(len(intent["constraints"]["avoid"]) == 0, "constraints.avoid vide en default")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Mode strong (chaque style family)
# ─────────────────────────────────────────────────────────────────────────────

def test_strong_mode() -> None:
    print("\n  TEST 4 — Mode strong")

    for sf_name in STYLE_FAMILIES:
        intent = generate_visual_intent(
            brief=_BRIEF_NEUTRAL,
            constraints={"force": [sf_name], "avoid": []},
        )
        _assert(intent["mode"] == "strong", f"mode=strong pour {sf_name}")
        errors = _validate_schema(intent)
        _assert(len(errors) == 0, f"schéma valide pour {sf_name} (err={errors})")
        _assert(intent["art_direction"]["style_family"] == sf_name,
                f"style_family={sf_name} dans art_direction")

    # brutalist doit avoir asymmetry=high + intensity=high
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["brutalist"]})
    _assert(intent["composition_bias"]["asymmetry"] == "high", "brutalist → asymmetry=high")
    _assert(intent["art_direction"]["intensity"]    == "high", "brutalist → intensity=high")
    _assert("grid_breaking" in intent["visual_techniques"],    "brutalist → grid_breaking technique")
    _assert(intent["color_strategy"]["contrast"]   == "high",  "brutalist → contrast=high")

    # tech_minimal doit avoir asymmetry=low + intensity=low
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["tech_minimal"]})
    _assert(intent["composition_bias"]["asymmetry"] == "low", "tech_minimal → asymmetry=low")
    _assert(intent["art_direction"]["intensity"]    == "low", "tech_minimal → intensity=low")

    # editorial_luxury doit avoir density=low + dominance=text
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["editorial_luxury"]})
    _assert(intent["composition_bias"]["density"]   == "low",  "editorial_luxury → density=low")
    _assert(intent["composition_bias"]["dominance"] == "text", "editorial_luxury → dominance=text")

    # premium_brand doit avoir dominance=image
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["premium_brand"]})
    _assert(intent["composition_bias"]["dominance"] == "image", "premium_brand → dominance=image")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Mode strong via archetype style_dna
# ─────────────────────────────────────────────────────────────────────────────

def test_strong_via_archetype() -> None:
    print("\n  TEST 5 — Mode strong via style_dna.archetype")

    editorial_archetypes = [
        "editorial_magazine", "editorial_rich", "studio_portfolio",
        "luxury_maison", "craft_artisan",
    ]
    for archetype in editorial_archetypes:
        intent = generate_visual_intent(
            brief=_BRIEF_NEUTRAL,
            style_dna={"archetype": archetype},
        )
        _assert(intent["mode"] == "strong",
                f"mode=strong via archetype={archetype}")

    # Archetype SaaS → tech_minimal
    intent = generate_visual_intent(
        brief=_BRIEF_TECH,
        style_dna={"archetype": "startup_clean"},
    )
    # N'est pas dans editorial_archetypes → mode default OU autre
    # (startup_clean n'est pas dans _editorial_archetypes → default)
    errors = _validate_schema(intent)
    _assert(len(errors) == 0, "startup_clean → schéma valide")

    # style_dna.style_family explicite → strong
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        style_dna={"style_family": "experimental_grid"},
    )
    _assert(intent["mode"] == "strong",        "mode=strong via style_dna.style_family")
    _assert(intent["art_direction"]["style_family"] == "experimental_grid",
            "style_family=experimental_grid")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Mode reference (mocked)
# ─────────────────────────────────────────────────────────────────────────────

def test_reference_mode_mocked() -> None:
    """Teste le mode reference en mockant _extract_from_reference."""
    print("\n  TEST 6 — Mode reference (mocké)")

    import src.visual_intent_engine as _module

    _original = _module._extract_from_reference

    def _mock_extract(ref_image, ref_type):
        return {
            "composition_bias": {
                "dominance": "image",
                "density":   "low",
                "asymmetry": "medium",
                "rhythm":    "regular",
            },
            "visual_techniques": ["framing", "scale_contrast"],
            "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
            "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "low"},
            "tone":        "editorial, clean, spacious",
            "personality": ["minimal", "refined"],
        }

    _module._extract_from_reference = _mock_extract

    try:
        intent = generate_visual_intent(
            brief=_BRIEF_NEUTRAL,
            reference_image="fake_ref.png",
        )

        _assert(intent["mode"] == "reference",                           "mode=reference")
        _assert(intent["composition_bias"]["dominance"] == "image",      "dominance=image depuis référence")
        _assert(intent["composition_bias"]["density"]   == "low",        "density=low depuis référence")
        _assert(intent["composition_bias"]["asymmetry"] == "medium",     "asymmetry=medium depuis référence")
        _assert("framing" in intent["visual_techniques"],                "framing technique présente")
        _assert("scale_contrast" in intent["visual_techniques"],         "scale_contrast technique présente")
        _assert(intent["art_direction"]["tone"] == "editorial, clean, spacious", "tone extrait")
        errors = _validate_schema(intent)
        _assert(len(errors) == 0, f"schéma valide en mode reference (err={errors})")

    finally:
        _module._extract_from_reference = _original


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Mode reference avec extraction échouée (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def test_reference_mode_fallback() -> None:
    """Si l'extraction échoue, le mode reference retourne un intent default valide."""
    print("\n  TEST 7 — Mode reference avec extraction échouée")

    import src.visual_intent_engine as _module

    _original = _module._extract_from_reference

    def _mock_fail(*a, **kw):
        return {}   # extraction vide — simule API unavailable

    _module._extract_from_reference = _mock_fail

    try:
        intent = generate_visual_intent(
            brief=_BRIEF_NEUTRAL,
            reference_image="nonexistent.png",
        )
        _assert(intent["mode"] == "reference", "mode=reference même si extraction vide")
        errors = _validate_schema(intent)
        _assert(len(errors) == 0, f"schéma valide avec extraction vide (err={errors})")

    finally:
        _module._extract_from_reference = _original


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — Mode hybrid
# ─────────────────────────────────────────────────────────────────────────────

def test_hybrid_mode() -> None:
    """Teste le blend style + reference."""
    print("\n  TEST 8 — Mode hybrid")

    import src.visual_intent_engine as _module

    _original = _module._extract_from_reference

    def _mock_extract_image_dominant(ref_image, ref_type):
        return {
            "composition_bias": {
                "dominance": "image",
                "density":   "low",
                "asymmetry": "low",
                "rhythm":    "regular",
            },
            "visual_techniques": ["framing", "cropping"],
            "color_strategy": {"contrast": "low", "palette_type": "neutral"},
            "typography_strategy": {"hierarchy_strength": "low", "weight_contrast": "low"},
            "tone":        "image dominant, spacious",
            "personality": ["clean", "spacious"],
        }

    _module._extract_from_reference = _mock_extract_image_dominant

    try:
        # Hybrid : brutalist style + image-dominant reference
        intent = generate_visual_intent(
            brief=_BRIEF_NEUTRAL,
            reference_image="ref.png",
            constraints={"force": ["brutalist"]},
        )

        _assert(intent["mode"] == "hybrid",                         "mode=hybrid")
        errors = _validate_schema(intent)
        _assert(len(errors) == 0,                                   f"schéma valide en hybrid (err={errors})")

        # Style (brutalist) → intensity=high doit primer sur la référence
        _assert(intent["art_direction"]["intensity"] == "high",     "hybrid: intensity=high depuis brutalist")

        # Référence → dominance=image doit primer sur le style
        _assert(intent["composition_bias"]["dominance"] == "image", "hybrid: dominance=image depuis référence")

        # Asymmetry = max(brutalist=high, ref=low) = high
        _assert(intent["composition_bias"]["asymmetry"] == "high",  "hybrid: asymmetry=high (max)")

        # Techniques = union style + ref (style en priorité)
        _assert("grid_breaking" in intent["visual_techniques"],     "hybrid: grid_breaking de brutalist")
        _assert("framing"       in intent["visual_techniques"],     "hybrid: framing de la référence")

        # Contrast = max(brutalist=high, ref=low) = high
        _assert(intent["color_strategy"]["contrast"] == "high",     "hybrid: contrast=high (max)")

    finally:
        _module._extract_from_reference = _original


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9 — Brief signal enrichment
# ─────────────────────────────────────────────────────────────────────────────

def test_brief_signals() -> None:
    print("\n  TEST 9 — Enrichissement par signaux du brief")

    # Brief luxury → intensity upgrade en mode default
    intent = generate_visual_intent(brief=_BRIEF_LUXURY)
    _assert(intent["mode"] == "default",                             "mode=default pour brief luxury sans style")
    _assert(intent["art_direction"]["intensity"] in ("medium", "high"),
            f"luxury → intensity upgradé (actuel: {intent['art_direction']['intensity']})")

    # Brief festival → palette vibrant
    intent = generate_visual_intent(brief=_BRIEF_FESTIVAL)
    _assert(intent["color_strategy"]["palette_type"] == "vibrant",  "festival → palette vibrant")
    _assert(intent["art_direction"]["intensity"] in ("medium", "high"),
            "festival → intensity upgradé")

    # Brief SaaS/dashboard → density medium (pas de modification car déjà medium en default)
    intent = generate_visual_intent(brief=_BRIEF_TECH)
    _assert(intent["composition_bias"]["density"] in ("low", "medium"),
            "saas → density low ou medium")

    # Brief mode strong : signal brief ne surcharge PAS
    intent = generate_visual_intent(
        brief=_BRIEF_FESTIVAL,   # festival → palette vibrant
        constraints={"force": ["tech_minimal"]},   # tech_minimal → palette neutral
    )
    # tech_minimal garde palette neutral malgré "festival" dans le brief
    _assert(intent["color_strategy"]["palette_type"] == "neutral",
            "strong mode: brief signal n'écrase pas style (palette reste neutral)")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10 — User constraints
# ─────────────────────────────────────────────────────────────────────────────

def test_user_constraints() -> None:
    print("\n  TEST 10 — Contraintes utilisateur")

    # avoid items ajoutés à constraints.avoid
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        constraints={"force": [], "avoid": ["centered_hero", "uniform_grid"]},
    )
    _assert("centered_hero" in intent["constraints"]["avoid"],   "centered_hero dans avoid")
    _assert("uniform_grid"  in intent["constraints"]["avoid"],   "uniform_grid dans avoid")
    _assert(intent["mode"] == "default",                         "mode=default sans style fort")

    # force items (non style-family) ajoutés à constraints.force
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        constraints={"force": ["typographic_emphasis"], "avoid": []},
    )
    _assert("typographic_emphasis" in intent["constraints"]["force"],
            "typographic_emphasis dans force")
    # Mode default (typographic_emphasis n'est pas une style family)
    _assert(intent["mode"] == "default", "mode=default même avec force non-style")

    # strong + avoid : les avoid s'accumulent
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        constraints={"force": ["brutalist"], "avoid": ["centered_hero"]},
    )
    _assert("centered_hero" in intent["constraints"]["avoid"],   "brutalist + centered_hero dans avoid")
    _assert(intent["mode"] == "strong",                          "mode=strong avec brutalist")

    # Style family name dans force ne doit PAS atterrir dans constraints.force du résultat
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        constraints={"force": ["brutalist", "typographic_emphasis"]},
    )
    _assert("brutalist" not in intent["constraints"]["force"],
            "style family name filtré de constraints.force")
    _assert("typographic_emphasis" in intent["constraints"]["force"],
            "non-style force item conservé")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 11 — intent_to_plan_overrides
# ─────────────────────────────────────────────────────────────────────────────

def test_intent_to_plan_overrides() -> None:
    print("\n  TEST 11 — intent_to_plan_overrides")

    # Default → overrides minimaux
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL)
    ov = intent_to_plan_overrides(intent)
    _assert(isinstance(ov, dict),                "retourne un dict")
    _assert("profile_override"  in ov,           "profile_override présent")
    _assert("density_override"  in ov,           "density_override présent")
    _assert("tension_override"  in ov,           "tension_override présent")
    _assert("layout_boost"      in ov,           "layout_boost présent")
    _assert("layout_avoid"      in ov,           "layout_avoid présent")
    _assert("extra_required"    in ov,           "extra_required présent")
    _assert("extra_forbidden"   in ov,           "extra_forbidden présent")

    # Brutalist → profil=bold, tension=high, layout boost asymétrique
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["brutalist"]})
    ov = intent_to_plan_overrides(intent)
    _assert(ov["profile_override"] == "bold",    "brutalist → profile_override=bold")
    _assert(ov["tension_override"] == "high",    "brutalist → tension_override=high")
    _assert("brutalist_stack" in ov["layout_boost"], "brutalist_stack dans layout_boost")
    _assert("grid_break" in ov["tension_methods"],   "grid_break dans tension_methods")

    # Editorial_luxury → profil=editorial, density=low, layout editorial
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["editorial_luxury"]})
    ov = intent_to_plan_overrides(intent)
    _assert(ov["profile_override"] == "editorial", "editorial_luxury → profile=editorial")
    _assert(ov["density_override"] == "low",       "editorial_luxury → density=low")
    _assert("editorial_flow" in ov["layout_boost"], "editorial_flow dans layout_boost")

    # Tech_minimal → tension medium, layout modular_grid
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL, constraints={"force": ["tech_minimal"]})
    ov = intent_to_plan_overrides(intent)
    _assert(ov["profile_override"] == "structural", "tech_minimal → profile=structural")
    _assert("modular_grid" in ov["layout_boost"],   "modular_grid dans layout_boost")

    # Constraints avoid → extra_forbidden
    intent = generate_visual_intent(
        brief=_BRIEF_NEUTRAL,
        constraints={"avoid": ["centered_hero", "uniform_grid"]},
    )
    ov = intent_to_plan_overrides(intent)
    _assert("centered_hero" in ov["extra_forbidden"], "centered_hero dans extra_forbidden")

    # Default mode → tension=medium
    intent = generate_visual_intent(brief=_BRIEF_NEUTRAL)
    ov = intent_to_plan_overrides(intent)
    _assert(ov["tension_override"] == "medium",    "default → tension=medium")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 12 — Schema validation (validate_and_clean)
# ─────────────────────────────────────────────────────────────────────────────

def test_schema_validation() -> None:
    print("\n  TEST 12 — Validation et nettoyage du schéma")

    # Intent invalide → corrigé silencieusement
    broken = {
        "mode": "INVALID_MODE",
        "art_direction": {
            "style_family": "neutral",
            "tone": "ok",
            "intensity": "ULTRA",   # invalide
            "personality": "not_a_list",  # invalide
        },
        "composition_bias": {
            "dominance": "invalid_dom",   # invalide
            "density":   "medium",
            "asymmetry": "low",
            "rhythm":    "regular",
        },
        "visual_techniques": ["overlap", "invalid_tech"],   # invalide
        "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints": {"force": [], "avoid": []},
    }

    cleaned = _validate_and_clean(broken)
    errors = _validate_schema(cleaned)
    _assert(len(errors) == 0,                                   f"invalid → corrigé (err={errors})")
    _assert(cleaned["mode"] == "default",                       "mode invalide → default")
    _assert(cleaned["art_direction"]["intensity"] == "low",     "intensity invalide → low")
    _assert(isinstance(cleaned["art_direction"]["personality"], list), "personality → liste")
    _assert(cleaned["composition_bias"]["dominance"] == "balanced", "dominance invalide → balanced")
    _assert("invalid_tech" not in cleaned["visual_techniques"], "technique invalide filtrée")
    _assert("overlap"       in cleaned["visual_techniques"],    "technique valide conservée")

    # Tous les outputs de generate_visual_intent passent la validation
    for sf in list(STYLE_FAMILIES.keys()) + [None]:
        brief  = _BRIEF_LUXURY if sf is None else _BRIEF_NEUTRAL
        kw     = {} if sf is None else {"constraints": {"force": [sf]}}
        intent = generate_visual_intent(brief=brief, **kw)
        errors = _validate_schema(intent)
        _assert(len(errors) == 0,
                f"schema valide pour style_family={sf} (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 13 — Extraction de contexte
# ─────────────────────────────────────────────────────────────────────────────

def test_context_extraction() -> None:
    print("\n  TEST 13 — Extraction de contexte produit")

    # Structures de données présentes
    _assert(len(EMOTIONAL_GOAL_ADJUSTMENTS) >= 6, "EMOTIONAL_GOAL_ADJUSTMENTS peuplé")
    _assert(len(BRAND_POSITIONING_ADJUSTMENTS) >= 5, "BRAND_POSITIONING_ADJUSTMENTS peuplé")
    _assert(callable(_extract_context), "_extract_context callable")

    # Dating app
    ctx = _extract_context("Application de rencontre pour jeunes adultes, matching par affinités")
    _assert(ctx["product_type"]      == "dating",     f"dating → product_type=dating (got {ctx['product_type']!r})")
    _assert(ctx["emotional_goal"]    == "desire",     f"dating → emotional_goal=desire (got {ctx['emotional_goal']!r})")
    _assert(ctx["brand_positioning"] == "playful",    f"dating → brand_positioning=playful (got {ctx['brand_positioning']!r})")
    _assert(ctx["target_audience"]   == "young_adult", f"dating → target_audience=young_adult (got {ctx['target_audience']!r})")

    # Gaming / esports
    ctx = _extract_context("Jeu de combat en ligne, esports, gaming compétitif")
    _assert(ctx["product_type"]      == "gaming",     f"gaming → product_type=gaming (got {ctx['product_type']!r})")
    _assert(ctx["emotional_goal"]    == "excitement", f"gaming → emotional_goal=excitement (got {ctx['emotional_goal']!r})")
    _assert(ctx["brand_positioning"] == "disruptive", f"gaming → brand_positioning=disruptive (got {ctx['brand_positioning']!r})")

    # Finance / trading
    ctx = _extract_context("Plateforme d'investissement et de trading en ligne")
    _assert(ctx["product_type"]      == "finance",    f"finance → product_type=finance (got {ctx['product_type']!r})")
    _assert(ctx["emotional_goal"]    == "trust",      f"finance → emotional_goal=trust (got {ctx['emotional_goal']!r})")
    _assert(ctx["brand_positioning"] == "serious",    f"finance → brand_positioning=serious (got {ctx['brand_positioning']!r})")

    # Luxury / couture
    ctx = _extract_context("Maison de haute couture, collection exclusive")
    _assert(ctx["product_type"]      == "luxury",     f"luxury → product_type=luxury (got {ctx['product_type']!r})")
    _assert(ctx["emotional_goal"]    == "desire",     f"luxury → emotional_goal=desire (got {ctx['emotional_goal']!r})")
    _assert(ctx["brand_positioning"] == "premium",    f"luxury → brand_positioning=premium (got {ctx['brand_positioning']!r})")

    # SaaS analytics
    ctx = _extract_context("Plateforme SaaS analytics pour équipes data")
    _assert(ctx["product_type"]   == "saas",   f"saas → product_type=saas (got {ctx['product_type']!r})")
    _assert(ctx["emotional_goal"] == "trust",  f"saas → emotional_goal=trust (got {ctx['emotional_goal']!r})")

    # Override émotionnel explicite : brief générique + mot "sécurisé" → trust
    ctx = _extract_context("Application mobile — fiable et sécurisé")
    _assert(ctx["emotional_goal"] == "trust",  f"secure signal → emotional_goal=trust (got {ctx['emotional_goal']!r})")

    # Override positionnement : mention "premium" → premium
    ctx = _extract_context("Agence web, positionnement premium")
    _assert(ctx["brand_positioning"] == "premium",
            f"'premium' signal → brand_positioning=premium (got {ctx['brand_positioning']!r})")

    # Brief vide / générique → defaults
    ctx = _extract_context("Site web")
    _assert(isinstance(ctx["product_type"],      str), "product_type est une str")
    _assert(isinstance(ctx["target_audience"],   str), "target_audience est une str")
    _assert(isinstance(ctx["emotional_goal"],    str), "emotional_goal est une str")
    _assert(isinstance(ctx["brand_positioning"], str), "brand_positioning est une str")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 14 — Contextual Design Alignment (4 exemples spec)
# ─────────────────────────────────────────────────────────────────────────────

def test_contextual_alignment() -> None:
    print("\n  TEST 14 — Contextual Design Alignment")

    # ── Dating app (desire + playful) ─────────────────────────────────────────
    intent = generate_visual_intent(brief="Application de rencontre pour jeunes adultes, matching par affinités")
    _assert(intent["mode"] == "default",                                "dating → mode=default")
    _assert(intent["context"]["product_type"]      == "dating",         "dating → context.product_type=dating")
    _assert(intent["context"]["emotional_goal"]    == "desire",         "dating → context.emotional_goal=desire")
    _assert(intent["context"]["brand_positioning"] == "playful",        "dating → context.brand_positioning=playful")
    _assert(intent["composition_bias"]["dominance"] == "image",
            f"dating → dominance=image (got {intent['composition_bias']['dominance']!r})")
    # playful → vibrant palette (brand_positioning fine-tune over desire=neutral)
    _assert(intent["color_strategy"]["palette_type"] == "vibrant",
            f"dating → palette=vibrant (got {intent['color_strategy']['palette_type']!r})")
    errors = _validate_schema(intent)
    _assert(len(errors) == 0,                                           f"dating → schéma valide (err={errors})")

    # ── Gaming / esports (excitement + disruptive) ────────────────────────────
    intent = generate_visual_intent(brief="Jeu de combat en ligne, esports, gaming compétitif")
    _assert(intent["context"]["product_type"]   == "gaming",           "gaming → context.product_type=gaming")
    _assert(intent["context"]["emotional_goal"] == "excitement",        "gaming → context.emotional_goal=excitement")
    _assert(intent["composition_bias"]["density"] == "high",
            f"gaming → density=high (got {intent['composition_bias']['density']!r})")
    _assert(intent["color_strategy"]["palette_type"] == "vibrant",
            f"gaming → palette=vibrant (got {intent['color_strategy']['palette_type']!r})")
    _assert(intent["color_strategy"]["contrast"] == "high",
            f"gaming → contrast=high (got {intent['color_strategy']['contrast']!r})")
    errors = _validate_schema(intent)
    _assert(len(errors) == 0,                                           f"gaming → schéma valide (err={errors})")

    # ── Finance / trading (trust + serious) ───────────────────────────────────
    intent = generate_visual_intent(brief="Plateforme d'investissement et de trading en ligne")
    _assert(intent["context"]["product_type"]   == "finance",          "finance → context.product_type=finance")
    _assert(intent["context"]["emotional_goal"] == "trust",             "finance → context.emotional_goal=trust")
    _assert(intent["composition_bias"]["dominance"] == "text",
            f"finance → dominance=text (got {intent['composition_bias']['dominance']!r})")
    _assert(intent["color_strategy"]["palette_type"] == "neutral",
            f"finance → palette=neutral (got {intent['color_strategy']['palette_type']!r})")
    _assert(intent["composition_bias"]["rhythm"] == "regular",
            f"finance → rhythm=regular (got {intent['composition_bias']['rhythm']!r})")
    _assert(intent["composition_bias"]["asymmetry"] == "low",
            f"finance → asymmetry=low (got {intent['composition_bias']['asymmetry']!r})")
    errors = _validate_schema(intent)
    _assert(len(errors) == 0,                                           f"finance → schéma valide (err={errors})")

    # ── Luxury / couture (desire + premium) ───────────────────────────────────
    intent = generate_visual_intent(brief="Maison de haute couture, collection exclusive")
    _assert(intent["context"]["product_type"]      == "luxury",        "luxury → context.product_type=luxury")
    _assert(intent["context"]["brand_positioning"] == "premium",        "luxury → context.brand_positioning=premium")
    _assert(intent["composition_bias"]["density"] == "low",
            f"luxury → density=low (got {intent['composition_bias']['density']!r})")
    # Désir + premium → palette neutral, contrast low
    _assert(intent["color_strategy"]["palette_type"] == "neutral",
            f"luxury → palette=neutral (got {intent['color_strategy']['palette_type']!r})")
    errors = _validate_schema(intent)
    _assert(len(errors) == 0,                                           f"luxury → schéma valide (err={errors})")

    # ── En mode strong : contexte n'écrase PAS la style family ───────────────
    # Gaming brief + brutalist style → composition_bias vient de brutalist, pas de gaming context
    intent_gaming_brutalist = generate_visual_intent(
        brief="Jeu de combat en ligne, esports, gaming compétitif",
        constraints={"force": ["brutalist"]},
    )
    _assert(intent_gaming_brutalist["mode"] == "strong",                "gaming+brutalist → mode=strong")
    # Brutalist garde ses valeurs — context ne les écrase pas
    _assert(intent_gaming_brutalist["composition_bias"]["asymmetry"] == "high",
            "strong mode: asymmetry=high depuis brutalist (non écrasé par context)")
    _assert(intent_gaming_brutalist["art_direction"]["style_family"] == "brutalist",
            "strong mode: style_family=brutalist conservé")
    _assert(intent_gaming_brutalist["context"]["product_type"] == "gaming",
            "strong mode: context.product_type=gaming présent dans le résultat")
    errors = _validate_schema(intent_gaming_brutalist)
    _assert(len(errors) == 0,                                           f"gaming+brutalist → schéma valide (err={errors})")

    # ── Finance brief + editorial_luxury style ────────────────────────────────
    intent_fin_editorial = generate_visual_intent(
        brief="Plateforme d'investissement et de trading en ligne",
        constraints={"force": ["editorial_luxury"]},
    )
    _assert(intent_fin_editorial["mode"] == "strong",                   "finance+editorial → mode=strong")
    # editorial_luxury garde density=low même si finance/trust voudrait medium
    _assert(intent_fin_editorial["composition_bias"]["density"] == "low",
            "strong mode: density=low depuis editorial_luxury (non écrasé par trust context)")
    errors = _validate_schema(intent_fin_editorial)
    _assert(len(errors) == 0,                                           f"finance+editorial → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 15 — Context field toujours présent dans le schéma de sortie
# ─────────────────────────────────────────────────────────────────────────────

def test_context_always_in_schema() -> None:
    print("\n  TEST 15 — Context field systématiquement présent")

    # Tous les modes + toutes les style families
    test_cases = [
        # (brief, kwargs)
        (_BRIEF_NEUTRAL,  {}),
        (_BRIEF_LUXURY,   {}),
        (_BRIEF_TECH,     {}),
        (_BRIEF_FESTIVAL, {}),
    ] + [
        (_BRIEF_NEUTRAL, {"constraints": {"force": [sf]}})
        for sf in STYLE_FAMILIES
    ]

    for brief, kw in test_cases:
        intent = generate_visual_intent(brief=brief, **kw)
        ctx = intent.get("context")
        _assert(ctx is not None, f"context présent pour brief={brief[:30]!r} kw={list(kw)}")
        if ctx:
            _assert(isinstance(ctx, dict),                    "context est un dict")
            _assert(isinstance(ctx.get("product_type"),      str), "context.product_type est str")
            _assert(isinstance(ctx.get("target_audience"),   str), "context.target_audience est str")
            _assert(isinstance(ctx.get("emotional_goal"),    str), "context.emotional_goal est str")
            _assert(isinstance(ctx.get("brand_positioning"), str), "context.brand_positioning est str")

        errors = _validate_schema(intent)
        _assert(len(errors) == 0, f"schéma complet valide (err={errors})")

    # validate_and_clean préserve context
    intent_with_ctx = {
        "mode": "default",
        "art_direction": {"style_family": "neutral", "tone": "ok", "intensity": "low", "personality": []},
        "composition_bias": {"dominance": "balanced", "density": "medium", "asymmetry": "low", "rhythm": "regular"},
        "visual_techniques": [],
        "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints": {"force": [], "avoid": []},
        "context": {
            "product_type": "saas", "target_audience": "professional",
            "emotional_goal": "trust", "brand_positioning": "serious",
        },
    }
    cleaned = _validate_and_clean(intent_with_ctx)
    _assert(cleaned.get("context", {}).get("product_type") == "saas",
            "validate_and_clean préserve context.product_type")
    _assert(cleaned.get("context", {}).get("emotional_goal") == "trust",
            "validate_and_clean préserve context.emotional_goal")

    # Sans context dans l'input → context avec defaults dans l'output
    intent_no_ctx = {
        "mode": "default",
        "art_direction": {"style_family": "neutral", "tone": "ok", "intensity": "low", "personality": []},
        "composition_bias": {"dominance": "balanced", "density": "medium", "asymmetry": "low", "rhythm": "regular"},
        "visual_techniques": [],
        "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints": {"force": [], "avoid": []},
    }
    cleaned2 = _validate_and_clean(intent_no_ctx)
    _assert("context" in cleaned2,           "validate_and_clean ajoute context si manquant")
    _assert(isinstance(cleaned2["context"], dict), "context ajouté est un dict")


# ─────────────────────────────────────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 64)
    print("  EURKAI — visual_intent_engine — Tests unitaires")
    print("=" * 64)

    test_imports()
    test_mode_detection()
    test_default_mode()
    test_strong_mode()
    test_strong_via_archetype()
    test_reference_mode_mocked()
    test_reference_mode_fallback()
    test_hybrid_mode()
    test_brief_signals()
    test_user_constraints()
    test_intent_to_plan_overrides()
    test_schema_validation()
    test_context_extraction()
    test_contextual_alignment()
    test_context_always_in_schema()

    total  = len(PASSED) + len(FAILED)
    passed = len(PASSED)

    print()
    print("=" * 64)
    print(f"  {passed}/{total} tests passés")
    if FAILED:
        print()
        print("  ÉCHECS :")
        for f in FAILED:
            print(f"    ✗  {f}")
    else:
        print("  ✅  Tous les tests passent")
    print("=" * 64)

    if FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
