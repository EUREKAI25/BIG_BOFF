#!/usr/bin/env python3
"""
Tests unitaires — color_palette

Zéro API. Zéro réseau. Zéro dépendance externe.
Vérifie : schéma strict, WCAG AA garanti, 5 cas spec, style_family override.
"""

import sys
import re
from pathlib import Path

_MODULE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_MODULE_DIR))

from src.color_palette import (
    generate_palette,
    _contrast_ratio,
    _wcag_grade,
    _hsl_to_hex,
    _luminance,
    _is_valid_hex,
    _STYLE_FAMILY_PALETTES,
    _BASE_HUE,
    _POSITIONING_MOD,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PASSED = []
FAILED = []


def _assert(cond: bool, msg: str) -> None:
    if cond:
        PASSED.append(msg)
        print(f"  ✅  {msg}")
    else:
        FAILED.append(msg)
        print(f"  ❌  FAIL — {msg}")


_HEX_RE = re.compile(r"^#[0-9a-f]{6}$")
_COLOR_KEYS = ("primary", "secondary", "accent", "background", "surface",
               "text_primary", "text_secondary", "border")
_STATE_KEYS = ("success", "warning", "error")


def _validate_schema(p: dict) -> list[str]:
    errors = []
    for k in _COLOR_KEYS:
        val = p.get(k)
        if not isinstance(val, str) or not _HEX_RE.match(val):
            errors.append(f"{k} invalide: {val!r}")

    states = p.get("states")
    if not isinstance(states, dict):
        errors.append("states manquant")
    else:
        for k in _STATE_KEYS:
            val = states.get(k)
            if not isinstance(val, str) or not _HEX_RE.match(val):
                errors.append(f"states.{k} invalide: {val!r}")

    cs = p.get("contrast_score")
    if not isinstance(cs, dict):
        errors.append("contrast_score manquant")
    else:
        for k in ("body_text", "large_text"):
            if k not in cs:
                errors.append(f"contrast_score.{k} manquant")

    return errors


def _make_intent(emotional_goal="", brand_positioning="", style_family="neutral",
                 intensity="medium", product_type="generic") -> dict:
    return {
        "mode": "default",
        "art_direction": {"style_family": style_family, "tone": "", "intensity": intensity, "personality": []},
        "composition_bias": {"dominance": "balanced", "density": "medium", "asymmetry": "low", "rhythm": "regular"},
        "visual_techniques": [],
        "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
        "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
        "constraints": {"force": [], "avoid": []},
        "context": {
            "product_type":      product_type,
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
    _assert(callable(generate_palette),     "generate_palette callable")
    _assert(callable(_contrast_ratio),      "_contrast_ratio callable")
    _assert(callable(_hsl_to_hex),          "_hsl_to_hex callable")
    _assert(len(_STYLE_FAMILY_PALETTES) == 6, "6 style family palettes")
    _assert(len(_BASE_HUE) >= 7,            "_BASE_HUE peuplé")
    _assert(len(_POSITIONING_MOD) >= 5,     "_POSITIONING_MOD peuplé")

    # Vérifier math de base
    _assert(_hsl_to_hex(0, 0, 100)   == "#ffffff",  "hsl(0,0,100) = blanc")
    _assert(_hsl_to_hex(0, 0, 0)     == "#000000",  "hsl(0,0,0) = noir")
    _assert(_is_valid_hex("#1a73e8"),               "#1a73e8 valide")
    _assert(not _is_valid_hex("1a73e8"),            "sans # invalide")
    _assert(not _is_valid_hex("#gg0000"),            "hex invalide")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Math WCAG
# ─────────────────────────────────────────────────────────────────────────────

def test_wcag_math() -> None:
    print("\n  TEST 2 — Math WCAG")

    # Blanc sur noir = 21:1 (ratio théorique)
    ratio = _contrast_ratio("#ffffff", "#000000")
    _assert(abs(ratio - 21.0) < 0.1, f"blanc/noir ≈ 21:1 (got {ratio:.2f})")

    # Noir sur blanc = idem
    ratio2 = _contrast_ratio("#000000", "#ffffff")
    _assert(abs(ratio2 - 21.0) < 0.1, f"noir/blanc ≈ 21:1 (got {ratio2:.2f})")

    # Gris moyen sur blanc — vérifier AA
    ratio3 = _contrast_ratio("#767676", "#ffffff")
    _assert(abs(ratio3 - 4.54) < 0.15, f"#767676/blanc ≈ 4.54:1 (got {ratio3:.2f})")

    # Grades
    _assert(_wcag_grade(21.0) == "AAA",      "21:1 → AAA")
    _assert(_wcag_grade(7.0)  == "AAA",      "7:1 → AAA")
    _assert(_wcag_grade(4.5)  == "AA",       "4.5:1 → AA")
    _assert(_wcag_grade(3.0)  == "AA Large", "3:1 → AA Large")
    _assert(_wcag_grade(2.9)  == "FAIL",     "2.9:1 → FAIL")

    # Luminance
    _assert(abs(_luminance("#ffffff") - 1.0) < 0.001,  "luminance blanc = 1.0")
    _assert(abs(_luminance("#000000") - 0.0) < 0.001,  "luminance noir = 0.0")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Schéma strict (zéro champ manquant, toutes hex valides)
# ─────────────────────────────────────────────────────────────────────────────

def test_schema() -> None:
    print("\n  TEST 3 — Schéma strict")

    # Intent vide → fallback
    p = generate_palette({})
    errors = _validate_schema(p)
    _assert(len(errors) == 0, f"intent vide → schéma valide (err={errors})")
    _assert(set(p.keys()) == {"primary", "secondary", "accent", "background", "surface",
                               "text_primary", "text_secondary", "border",
                               "states", "contrast_score"},
            "10 clés exactes dans le résultat")

    # Tous les emotional_goals
    for goal in ("trust", "excitement", "desire", "calm", "curiosity", "authority", ""):
        p = generate_palette(_make_intent(emotional_goal=goal))
        errors = _validate_schema(p)
        _assert(len(errors) == 0, f"goal={goal!r} → schéma valide (err={errors})")

    # Tous les brand_positionings
    for pos in ("premium", "accessible", "disruptive", "playful", "serious", ""):
        p = generate_palette(_make_intent(brand_positioning=pos))
        errors = _validate_schema(p)
        _assert(len(errors) == 0, f"positioning={pos!r} → schéma valide (err={errors})")

    # Toutes les style families
    for sf in _STYLE_FAMILY_PALETTES:
        p = generate_palette(_make_intent(style_family=sf))
        errors = _validate_schema(p)
        _assert(len(errors) == 0, f"style_family={sf} → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Contraste WCAG AA garanti sur TOUS les outputs
# ─────────────────────────────────────────────────────────────────────────────

def test_contrast_guarantee() -> None:
    print("\n  TEST 4 — Contraste WCAG AA garanti")

    _FAIL = {"FAIL"}

    cases = (
        [_make_intent(emotional_goal=g) for g in ("trust", "excitement", "desire", "calm", "curiosity", "authority")] +
        [_make_intent(brand_positioning=p) for p in ("premium", "disruptive", "playful", "serious", "accessible")] +
        [_make_intent(style_family=sf) for sf in _STYLE_FAMILY_PALETTES] +
        [_make_intent(emotional_goal="trust",      product_type="finance"),
         _make_intent(emotional_goal="excitement", product_type="gaming"),
         _make_intent(emotional_goal="desire",     product_type="dating"),
         _make_intent(emotional_goal="desire",     brand_positioning="premium", product_type="luxury")]
    )

    for intent in cases:
        p = generate_palette(intent)
        sf   = intent.get("art_direction", {}).get("style_family", "")
        goal = intent.get("context", {}).get("emotional_goal", "")
        pos  = intent.get("context", {}).get("brand_positioning", "")
        label = sf or goal or pos or "default"

        # Contraste réel (recalculé, pas juste le grade en output)
        body_ratio  = _contrast_ratio(p["text_primary"],   p["background"])
        large_ratio = _contrast_ratio(p["text_secondary"], p["surface"])

        _assert(body_ratio >= 4.5,
                f"{label}: text_primary/bg ≥ 4.5:1 (got {body_ratio:.2f})")
        _assert(large_ratio >= 4.5,
                f"{label}: text_secondary/surface ≥ 4.5:1 (got {large_ratio:.2f})")

        # Grades dans l'output
        _assert(p["contrast_score"]["body_text"]  not in _FAIL,
                f"{label}: body_text grade pas FAIL")
        _assert(p["contrast_score"]["large_text"] not in _FAIL,
                f"{label}: large_text grade pas FAIL")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — 5 cas spec (gaming / dating / finance / luxury / saas)
# ─────────────────────────────────────────────────────────────────────────────

def test_spec_cases() -> None:
    print("\n  TEST 5 — 5 cas spec")

    # Gaming : excitement + disruptive → dark, haut contraste, neon
    gaming = generate_palette(_make_intent(
        emotional_goal="excitement", brand_positioning="disruptive", product_type="gaming"))
    _assert(_luminance(gaming["background"]) < 0.05,
            f"gaming → fond sombre (L={_luminance(gaming['background']):.3f})")
    _assert(_contrast_ratio(gaming["text_primary"], gaming["background"]) >= 7.0,
            f"gaming → texte/fond AAA (got {_contrast_ratio(gaming['text_primary'], gaming['background']):.2f})")
    errors = _validate_schema(gaming)
    _assert(len(errors) == 0, f"gaming → schéma valide (err={errors})")

    # Dating : desire + playful → fond clair ou sombre chaleureux, teinte rose/rouge
    dating = generate_palette(_make_intent(
        emotional_goal="desire", brand_positioning="playful", product_type="dating"))
    errors = _validate_schema(dating)
    _assert(len(errors) == 0, f"dating → schéma valide (err={errors})")
    _assert(_contrast_ratio(dating["text_primary"], dating["background"]) >= 4.5,
            f"dating → contraste body AA")

    # Finance : trust + serious → fond clair, palette sobre
    finance = generate_palette(_make_intent(
        emotional_goal="trust", brand_positioning="serious", product_type="finance"))
    _assert(_luminance(finance["background"]) > 0.8,
            f"finance → fond clair (L={_luminance(finance['background']):.3f})")
    _assert(_luminance(finance["text_primary"]) < 0.1,
            f"finance → texte sombre (L={_luminance(finance['text_primary']):.3f})")
    errors = _validate_schema(finance)
    _assert(len(errors) == 0, f"finance → schéma valide (err={errors})")

    # Luxury (via style family premium_brand) → fond sombre, gold
    luxury_sf = generate_palette(_make_intent(style_family="premium_brand"))
    _assert(_luminance(luxury_sf["background"]) < 0.05,
            f"luxury (premium_brand) → fond sombre")
    errors = _validate_schema(luxury_sf)
    _assert(len(errors) == 0, f"luxury (premium_brand) → schéma valide (err={errors})")

    # SaaS : trust + serious → fond blanc/clair, bleu sobre (via tech_minimal)
    saas_sf = generate_palette(_make_intent(style_family="tech_minimal"))
    _assert(_luminance(saas_sf["background"]) > 0.8,
            f"saas (tech_minimal) → fond clair (L={_luminance(saas_sf['background']):.3f})")
    errors = _validate_schema(saas_sf)
    _assert(len(errors) == 0, f"saas (tech_minimal) → schéma valide (err={errors})")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Style family palettes (override complet)
# ─────────────────────────────────────────────────────────────────────────────

def test_style_family_override() -> None:
    print("\n  TEST 6 — Style family override")

    for sf in _STYLE_FAMILY_PALETTES:
        p = generate_palette(_make_intent(style_family=sf))
        errors = _validate_schema(p)
        _assert(len(errors) == 0, f"{sf} → schéma valide (err={errors})")
        _assert(_contrast_ratio(p["text_primary"], p["background"]) >= 4.5,
                f"{sf} → text_primary/bg ≥ AA")

    # editorial_luxury → fond très sombre, palette warm
    p = generate_palette(_make_intent(style_family="editorial_luxury"))
    _assert(_luminance(p["background"]) < 0.01, "editorial_luxury → fond near-black")
    _assert(p["text_primary"] == "#f0ece0", f"editorial_luxury → cream text (got {p['text_primary']!r})")

    # brutalist → noir/blanc pur
    p = generate_palette(_make_intent(style_family="brutalist"))
    _assert(p["background"] == "#000000", f"brutalist → bg=black (got {p['background']!r})")
    _assert(p["text_primary"] == "#ffffff", f"brutalist → text=white (got {p['text_primary']!r})")

    # tech_minimal → fond blanc
    p = generate_palette(_make_intent(style_family="tech_minimal"))
    _assert(p["background"] == "#ffffff", f"tech_minimal → bg=white (got {p['background']!r})")
    _assert(_luminance(p["text_primary"]) < 0.05, "tech_minimal → texte sombre")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Pas de couleurs dupliquées (text ≠ background)
# ─────────────────────────────────────────────────────────────────────────────

def test_no_duplicate_roles() -> None:
    print("\n  TEST 7 — Pas de couleurs dupliquées")

    intents = [
        _make_intent("trust",      "serious",    product_type="finance"),
        _make_intent("excitement", "disruptive", product_type="gaming"),
        _make_intent("desire",     "playful",    product_type="dating"),
        _make_intent("calm",       "accessible", product_type="health"),
        _make_intent("authority",  "premium",    product_type="agency"),
    ] + [_make_intent(style_family=sf) for sf in _STYLE_FAMILY_PALETTES]

    for intent in intents:
        p = generate_palette(intent)
        sf   = intent.get("art_direction", {}).get("style_family", "")
        goal = intent.get("context", {}).get("emotional_goal", "")
        label = sf or goal

        # text_primary ≠ background (sinon illisible)
        _assert(p["text_primary"] != p["background"],
                f"{label}: text_primary ≠ background")

        # text_secondary ≠ surface
        _assert(p["text_secondary"] != p["surface"],
                f"{label}: text_secondary ≠ surface")

        # background ≠ surface (doivent être distincts)
        _assert(p["background"] != p["surface"],
                f"{label}: background ≠ surface")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — Paramètre context override
# ─────────────────────────────────────────────────────────────────────────────

def test_context_override() -> None:
    print("\n  TEST 8 — Paramètre context override")

    intent = _make_intent(emotional_goal="excitement", product_type="gaming")

    # Sans override → gaming dark
    p1 = generate_palette(intent)
    _assert(_luminance(p1["background"]) < 0.05, "gaming intent → fond sombre")

    # Avec context override → finance light
    ctx_override = {"emotional_goal": "trust", "brand_positioning": "serious",
                    "product_type": "finance"}
    p2 = generate_palette(intent, context=ctx_override)
    _assert(_luminance(p2["background"]) > 0.8,
            f"context override finance → fond clair (L={_luminance(p2['background']):.3f})")

    # Schémas valides dans les deux cas
    _assert(len(_validate_schema(p1)) == 0, "p1 schéma valide")
    _assert(len(_validate_schema(p2)) == 0, "p2 schéma valide")

    # Déterminisme : même input → même output
    p3 = generate_palette(intent)
    _assert(p1 == p3, "déterminisme : même intent → même palette")


# ─────────────────────────────────────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 64)
    print("  EURKAI — color_palette — Tests unitaires")
    print("=" * 64)

    test_imports()
    test_wcag_math()
    test_schema()
    test_contrast_guarantee()
    test_spec_cases()
    test_style_family_override()
    test_no_duplicate_roles()
    test_context_override()

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
