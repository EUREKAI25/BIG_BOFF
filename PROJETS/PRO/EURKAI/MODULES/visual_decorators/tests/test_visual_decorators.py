#!/usr/bin/env python3
"""
Tests unitaires — visual_decorators

Zéro API. Zéro réseau. Zéro dépendance externe.
Vérifie : schéma strict, cohérence des 4 cas spec, priorité style_family.
"""

import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_MODULE_DIR))

from src.visual_decorators import (
    generate_visual_decorators,
    _PRESETS,
    _STYLE_FAMILY_OVERRIDES,
    _POSITIONING_ADJUSTMENTS,
    _VALID_BORDER_STYLE, _VALID_BORDER_THICKNESS, _VALID_BORDER_RADIUS, _VALID_BORDER_PATTERN,
    _VALID_DIVIDER_TYPE, _VALID_DIVIDER_STYLE,
    _VALID_ICON_STYLE, _VALID_ICON_STROKE, _VALID_ICON_CORNER, _VALID_ICON_COMPLEXITY,
    _VALID_MOTIF_TYPE, _VALID_MOTIF_USAGE,
    _VALID_OVERLAY_TYPE, _VALID_OVERLAY_INTENSITY,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PASSED = []
FAILED = []


def _assert(condition: bool, msg: str) -> None:
    if condition:
        PASSED.append(msg)
        print(f"  ✅  {msg}")
    else:
        FAILED.append(msg)
        print(f"  ❌  FAIL — {msg}")


def _validate_schema(dec: dict) -> list[str]:
    errors = []

    b = dec.get("borders")
    if not isinstance(b, dict):
        errors.append("borders manquant")
    else:
        if b.get("style")     not in _VALID_BORDER_STYLE:     errors.append(f"borders.style invalide: {b.get('style')!r}")
        if b.get("thickness") not in _VALID_BORDER_THICKNESS: errors.append(f"borders.thickness invalide: {b.get('thickness')!r}")
        if b.get("radius")    not in _VALID_BORDER_RADIUS:    errors.append(f"borders.radius invalide: {b.get('radius')!r}")
        if b.get("pattern")   not in _VALID_BORDER_PATTERN:   errors.append(f"borders.pattern invalide: {b.get('pattern')!r}")

    d = dec.get("dividers")
    if not isinstance(d, dict):
        errors.append("dividers manquant")
    else:
        if d.get("type")  not in _VALID_DIVIDER_TYPE:  errors.append(f"dividers.type invalide: {d.get('type')!r}")
        if d.get("style") not in _VALID_DIVIDER_STYLE: errors.append(f"dividers.style invalide: {d.get('style')!r}")

    i = dec.get("icons")
    if not isinstance(i, dict):
        errors.append("icons manquant")
    else:
        if i.get("style")        not in _VALID_ICON_STYLE:       errors.append(f"icons.style invalide: {i.get('style')!r}")
        if i.get("stroke")       not in _VALID_ICON_STROKE:      errors.append(f"icons.stroke invalide: {i.get('stroke')!r}")
        if i.get("corner_style") not in _VALID_ICON_CORNER:      errors.append(f"icons.corner_style invalide: {i.get('corner_style')!r}")
        if i.get("complexity")   not in _VALID_ICON_COMPLEXITY:  errors.append(f"icons.complexity invalide: {i.get('complexity')!r}")

    m = dec.get("motifs")
    if not isinstance(m, dict):
        errors.append("motifs manquant")
    else:
        if m.get("type")  not in _VALID_MOTIF_TYPE:  errors.append(f"motifs.type invalide: {m.get('type')!r}")
        if m.get("usage") not in _VALID_MOTIF_USAGE: errors.append(f"motifs.usage invalide: {m.get('usage')!r}")

    o = dec.get("overlays")
    if not isinstance(o, dict):
        errors.append("overlays manquant")
    else:
        if o.get("type")      not in _VALID_OVERLAY_TYPE:      errors.append(f"overlays.type invalide: {o.get('type')!r}")
        if o.get("intensity") not in _VALID_OVERLAY_INTENSITY: errors.append(f"overlays.intensity invalide: {o.get('intensity')!r}")

    return errors


def _make_intent(emotional_goal="", brand_positioning="", style_family="neutral",
                 intensity="medium", density="medium", mode="default") -> dict:
    """Construit un visual_intent minimal pour les tests."""
    return {
        "mode": mode,
        "art_direction": {
            "style_family": style_family,
            "tone":         "test",
            "intensity":    intensity,
            "personality":  [],
        },
        "composition_bias": {
            "dominance": "balanced",
            "density":   density,
            "asymmetry": "low",
            "rhythm":    "regular",
        },
        "visual_techniques": [],
        "color_strategy":   {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints": {"force": [], "avoid": []},
        "context": {
            "product_type":      "generic",
            "target_audience":   "general",
            "emotional_goal":    emotional_goal,
            "brand_positioning": brand_positioning,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Imports et constantes
# ─────────────────────────────────────────────────────────────────────────────

def test_imports() -> None:
    print("\n  TEST 1 — Imports et constantes")
    _assert(callable(generate_visual_decorators), "generate_visual_decorators callable")
    _assert(len(_PRESETS) >= 7,               f"_PRESETS peuplé ({len(_PRESETS)} presets)")
    _assert(len(_STYLE_FAMILY_OVERRIDES) == 6, "6 style family overrides")
    _assert(len(_POSITIONING_ADJUSTMENTS) >= 5, "5 positioning adjustments")
    _assert("trust"     in _PRESETS,           "preset trust présent")
    _assert("excitement" in _PRESETS,          "preset excitement présent")
    _assert("desire"    in _PRESETS,           "preset desire présent")
    _assert("calm"      in _PRESETS,           "preset calm présent")
    _assert("curiosity" in _PRESETS,           "preset curiosity présent")
    _assert("authority" in _PRESETS,           "preset authority présent")
    _assert("default"   in _PRESETS,           "preset default présent")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Schéma strict (zéro champ manquant, toutes valeurs valides)
# ─────────────────────────────────────────────────────────────────────────────

def test_schema() -> None:
    print("\n  TEST 2 — Schéma strict")

    # Intent vide → default
    dec = generate_visual_decorators({})
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"intent vide → schéma valide (err={errors})")
    _assert(set(dec.keys()) == {"borders", "dividers", "icons", "motifs", "overlays"},
            "5 clés exactement présentes")

    # Tous les emotional_goals
    for goal in ("trust", "excitement", "desire", "calm", "curiosity", "authority", ""):
        intent = _make_intent(emotional_goal=goal)
        dec = generate_visual_decorators(intent)
        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"goal={goal!r} → schéma valide (err={errors})")

    # Tous les brand_positionings
    for pos in ("premium", "accessible", "disruptive", "playful", "serious", ""):
        intent = _make_intent(brand_positioning=pos)
        dec = generate_visual_decorators(intent)
        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"positioning={pos!r} → schéma valide (err={errors})")

    # Toutes les style families
    style_families = ["editorial_luxury", "brutalist", "tech_minimal",
                      "experimental_grid", "premium_brand", "bold_marketing"]
    for sf in style_families:
        intent = _make_intent(style_family=sf)
        dec = generate_visual_decorators(intent)
        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"style_family={sf} → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — 4 cas spec : gaming / dating / finance / luxury
# ─────────────────────────────────────────────────────────────────────────────

def test_spec_cases() -> None:
    print("\n  TEST 3 — 4 cas spec")

    # Gaming : excitement + disruptive → glow borders, sharp angles
    intent = _make_intent(emotional_goal="excitement", brand_positioning="disruptive",
                          intensity="high")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["radius"]        == "none",  f"gaming → radius=none (got {dec['borders']['radius']!r})")
    _assert(dec["icons"]["corner_style"]    == "sharp", f"gaming → icons.corner_style=sharp (got {dec['icons']['corner_style']!r})")
    _assert(dec["borders"]["thickness"] in ("medium", "thick"),
            f"gaming → borders épaisseur significative (got {dec['borders']['thickness']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"gaming → schéma valide (err={errors})")

    # Dating : desire + playful → rounded, soft curves, warm shapes
    intent = _make_intent(emotional_goal="desire", brand_positioning="playful",
                          intensity="medium")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["radius"] in ("medium", "large", "full"),
            f"dating → radius arrondi (got {dec['borders']['radius']!r})")
    _assert(dec["icons"]["corner_style"] == "rounded",
            f"dating → icons arrondis (got {dec['icons']['corner_style']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"dating → schéma valide (err={errors})")

    # Finance : trust + serious → minimal borders, precise lines, no noise
    intent = _make_intent(emotional_goal="trust", brand_positioning="serious",
                          intensity="low")
    dec = generate_visual_decorators(intent)
    _assert(dec["motifs"]["type"]        == "none",     f"finance → motifs=none (got {dec['motifs']['type']!r})")
    _assert(dec["overlays"]["type"]      == "none",     f"finance → overlays=none (got {dec['overlays']['type']!r})")
    _assert(dec["icons"]["corner_style"] == "sharp",    f"finance → icons sharp (got {dec['icons']['corner_style']!r})")
    _assert(dec["borders"]["thickness"]  == "thin",     f"finance → borders thin (got {dec['borders']['thickness']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"finance → schéma valide (err={errors})")

    # Luxury : desire + premium → thin lines, high spacing (low density), elegant separators
    intent = _make_intent(emotional_goal="desire", brand_positioning="premium",
                          intensity="medium", density="low")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["style"] in ("double", "solid"),
            f"luxury → border style élégant (got {dec['borders']['style']!r})")
    _assert(dec["borders"]["thickness"] == "thin",
            f"luxury → borders thin (got {dec['borders']['thickness']!r})")
    _assert(dec["motifs"]["type"]  == "none",
            f"luxury → motifs=none (got {dec['motifs']['type']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"luxury → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Priorité style_family (prime sur emotional_goal)
# ─────────────────────────────────────────────────────────────────────────────

def test_style_family_priority() -> None:
    print("\n  TEST 4 — Priorité style_family")

    # editorial_luxury → double border thin, no motifs, no overlays
    intent = _make_intent(style_family="editorial_luxury", emotional_goal="excitement",
                          intensity="high")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["style"]     == "double",  f"editorial_luxury → border=double (got {dec['borders']['style']!r})")
    _assert(dec["borders"]["thickness"] == "thin",    f"editorial_luxury → thin (got {dec['borders']['thickness']!r})")
    _assert(dec["motifs"]["type"]       == "none",    f"editorial_luxury → motifs=none (got {dec['motifs']['type']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"editorial_luxury → schéma valide (err={errors})")

    # brutalist → thick solid, sharp, grid-fragment full-bleed
    intent = _make_intent(style_family="brutalist", emotional_goal="calm", intensity="high")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["thickness"] == "thick",          f"brutalist → thick (got {dec['borders']['thickness']!r})")
    _assert(dec["borders"]["radius"]    == "none",           f"brutalist → radius=none (got {dec['borders']['radius']!r})")
    _assert(dec["icons"]["corner_style"] == "sharp",         f"brutalist → icons sharp (got {dec['icons']['corner_style']!r})")
    _assert(dec["motifs"]["type"]       == "grid-fragment",  f"brutalist → motif=grid-fragment (got {dec['motifs']['type']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"brutalist → schéma valide (err={errors})")

    # tech_minimal → thin line, sharp, dot-pattern
    intent = _make_intent(style_family="tech_minimal", emotional_goal="desire")
    dec = generate_visual_decorators(intent)
    _assert(dec["icons"]["stroke"]      == "thin",           f"tech_minimal → stroke=thin (got {dec['icons']['stroke']!r})")
    _assert(dec["motifs"]["type"]       == "dot-pattern",    f"tech_minimal → dot-pattern (got {dec['motifs']['type']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"tech_minimal → schéma valide (err={errors})")

    # experimental_grid → dashed, mixed corners, noise
    intent = _make_intent(style_family="experimental_grid", intensity="high")
    dec = generate_visual_decorators(intent)
    _assert(dec["borders"]["style"]     == "dashed",         f"experimental_grid → dashed (got {dec['borders']['style']!r})")
    _assert(dec["icons"]["corner_style"] == "mixed",         f"experimental_grid → mixed corners (got {dec['icons']['corner_style']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"experimental_grid → schéma valide (err={errors})")

    # bold_marketing → thick, filled, diagonal-cut
    intent = _make_intent(style_family="bold_marketing", intensity="high")
    dec = generate_visual_decorators(intent)
    _assert(dec["icons"]["style"]       == "filled",         f"bold_marketing → icons filled (got {dec['icons']['style']!r})")
    _assert(dec["motifs"]["type"]       == "diagonal-cut",   f"bold_marketing → diagonal-cut (got {dec['motifs']['type']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"bold_marketing → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Ajustements intensity
# ─────────────────────────────────────────────────────────────────────────────

def test_intensity_adjustments() -> None:
    print("\n  TEST 5 — Ajustements selon intensity")

    # intensity=low → motifs=none, overlays=none, borders max thin
    for goal in ("excitement", "curiosity", "authority"):
        intent = _make_intent(emotional_goal=goal, intensity="low")
        dec = generate_visual_decorators(intent)
        _assert(dec["motifs"]["type"]       == "none", f"intensity=low + {goal} → motifs=none")
        _assert(dec["overlays"]["type"]     == "none", f"intensity=low + {goal} → overlays=none")
        _assert(dec["borders"]["thickness"] == "thin", f"intensity=low + {goal} → borders thin")
        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"intensity=low + {goal} → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Ajustements density
# ─────────────────────────────────────────────────────────────────────────────

def test_density_adjustments() -> None:
    print("\n  TEST 6 — Ajustements selon density")

    # density=low → motif usage réduit (pas de full-bleed)
    intent = _make_intent(emotional_goal="excitement", brand_positioning="disruptive",
                          intensity="high", density="low")
    dec = generate_visual_decorators(intent)
    _assert(dec["motifs"]["usage"] != "full-bleed",
            f"density=low → motif.usage pas full-bleed (got {dec['motifs']['usage']!r})")
    errors = _validate_schema(dec)
    _assert(len(errors) == 0, f"density=low → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Cohérence du langage visuel (tous éléments compatibles)
# ─────────────────────────────────────────────────────────────────────────────

def test_visual_language_coherence() -> None:
    print("\n  TEST 7 — Cohérence du langage visuel")

    # Un intent avec style_family connue → tous éléments partagent le même langage
    for sf in ("editorial_luxury", "brutalist", "tech_minimal",
               "premium_brand", "bold_marketing", "experimental_grid"):
        intent = _make_intent(style_family=sf, intensity="medium")
        dec = generate_visual_decorators(intent)

        # Vérification de cohérence : si radius=none → pas de full rounded ailleurs
        if dec["borders"]["radius"] == "none":
            _assert(dec["icons"]["corner_style"] != "full",
                    f"{sf}: radius=none → icons pas full-round")

        # Vérification : si borders=double → elegant (pas thick)
        if dec["borders"]["style"] == "double":
            _assert(dec["borders"]["thickness"] in ("thin", "medium"),
                    f"{sf}: border=double → épaisseur modérée")

        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"{sf} → cohérence + schéma valide (err={errors})")

    # Cohérence globale : un intent random ne produit jamais de champs inconnus
    intents = [
        _make_intent("trust", "serious", "neutral", "low", "low"),
        _make_intent("excitement", "disruptive", "neutral", "high", "high"),
        _make_intent("desire", "playful", "neutral", "medium", "medium"),
        _make_intent("calm", "accessible", "neutral", "low", "low"),
        _make_intent("authority", "premium", "neutral", "medium", "medium"),
    ]
    for intent in intents:
        dec = generate_visual_decorators(intent)
        _assert(set(dec.keys()) == {"borders", "dividers", "icons", "motifs", "overlays"},
                "exactement 5 clés dans le résultat")
        errors = _validate_schema(dec)
        _assert(len(errors) == 0, f"intent mixte → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 64)
    print("  EURKAI — visual_decorators — Tests unitaires")
    print("=" * 64)

    test_imports()
    test_schema()
    test_spec_cases()
    test_style_family_priority()
    test_intensity_adjustments()
    test_density_adjustments()
    test_visual_language_coherence()

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
