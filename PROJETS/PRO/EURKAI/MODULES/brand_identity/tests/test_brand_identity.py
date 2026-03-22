"""
Tests pour brand_identity.
Run : python -m pytest MODULES/brand_identity/tests/ -v

Aucune dépendance externe. Module purement déterministe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import importlib.util as _ilu

_ROOT   = Path(__file__).parents[4]
_BI_PY  = Path(__file__).parents[1] / "src" / "brand_identity.py"

_spec = _ilu.spec_from_file_location("_brand_identity_core", _BI_PY)
_mod  = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
generate_brand_identity = _mod.generate_brand_identity


# ── Fixtures ─────────────────────────────────────────────────────────────────

BRIEF_GAMING    = "FPS esports tournament platform, competitive, dark, global"
BRIEF_LUXURY    = "Maison de parfum parisienne 1905, ultra-luxury, minimalist"
BRIEF_STARTUP   = "Developer tools SaaS, API-first, modern stack, B2B"
BRIEF_EDITORIAL = "Magazine d'architecture et de design contemporain"
BRIEF_DEFAULT   = "Conseil en management, Paris, sérieux"

VI_BASIC = {
    "emotion": "trust",
    "mood": "professional",
    "archetype": "startup_clean",
    "context": {"product_type": "saas", "brand_positioning": "premium"},
    "composition_bias": {"dominance": "text", "density": "low"},
    "typography_strategy": {"hierarchy_strength": "high"},
    "color_strategy": {"contrast": "medium"},
    "mode": "palette",
}

VI_GAMING = {
    "emotion": "power",
    "mood": "aggressive",
    "archetype": "esports",
    "context": {"product_type": "gaming", "brand_positioning": "competitive"},
    "composition_bias": {"dominance": "image", "density": "high"},
    "typography_strategy": {"hierarchy_strength": "high"},
    "color_strategy": {"contrast": "high"},
    "mode": "palette",
}

VI_LUXURY = {
    "emotion": "elegance",
    "mood": "refined",
    "archetype": "luxury_house",
    "context": {"product_type": "luxury", "brand_positioning": "exclusive"},
    "composition_bias": {"dominance": "image", "density": "low"},
    "typography_strategy": {"hierarchy_strength": "medium"},
    "color_strategy": {"contrast": "low"},
    "mode": "palette",
}

PALETTE_BASIC = {
    "mode": "light",
    "primary": "#2563EB",
    "primary_light": "#60A5FA",
    "primary_dark": "#1D4ED8",
    "accent": "#F59E0B",
    "background": "#FFFFFF",
    "foreground": "#111827",
    "text_primary": "#111827",
    "body_text_grade": "AAA",
}

PALETTE_DARK = {
    "mode": "dark",
    "primary": "#7C3AED",
    "primary_light": "#A78BFA",
    "primary_dark": "#5B21B6",
    "accent": "#00FF88",
    "background": "#0F0F0F",
    "foreground": "#F8FAFC",
    "text_primary": "#F8FAFC",
    "body_text_grade": "AAA",
}

CTX_BASIC    = {"name": "Synaptic",   "mode": "light", "family": "saas"}
CTX_GAMING   = {"name": "FrostByte",  "mode": "dark",  "family": "gaming"}
CTX_LUXURY   = {"name": "Maison Éva", "mode": "light", "family": "luxury"}
CTX_EDITORIAL= {"name": "Arcform",    "mode": "light", "family": "editorial"}


# ── Structure output ──────────────────────────────────────────────────────────

def test_brand_identity_structure_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    for key in ("brand_core", "logo", "icons", "typography", "visual_signature", "_meta"):
        assert key in result, f"Missing top-level key: {key}"


def test_brand_core_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    bc = result["brand_core"]
    for key in ("name", "tone", "personality", "positioning"):
        assert key in bc, f"Missing brand_core key: {key}"
    assert isinstance(bc["personality"], list)
    assert len(bc["personality"]) > 0


def test_logo_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    logo = result["logo"]
    for key in ("type", "style", "construction", "variations", "generation_prompt", "svg_spec"):
        assert key in logo, f"Missing logo key: {key}"
    assert isinstance(logo["variations"], list)
    assert len(logo["generation_prompt"]) > 20


def test_logo_svg_spec_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    svg = result["logo"]["svg_spec"]
    for key in ("shape", "rotation", "style", "primary_color", "background", "viewport"):
        assert key in svg, f"Missing svg_spec key: {key}"


def test_icons_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    icons = result["icons"]
    for key in ("style", "stroke", "corner_style", "consistency_rules", "generation_prompt", "examples"):
        assert key in icons, f"Missing icons key: {key}"
    assert isinstance(icons["consistency_rules"], list)
    assert len(icons["consistency_rules"]) >= 3
    assert isinstance(icons["examples"], list)
    assert len(icons["examples"]) >= 4


def test_typography_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    typo = result["typography"]
    for key in ("primary_font", "secondary_font", "fallbacks", "style", "pairing_logic", "custom_font_possible"):
        assert key in typo, f"Missing typography key: {key}"
    assert isinstance(typo["fallbacks"], list)
    assert isinstance(typo["custom_font_possible"], bool)


def test_visual_signature_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    sig = result["visual_signature"]
    for key in ("motifs", "borders", "patterns", "composition_rules"):
        assert key in sig, f"Missing visual_signature key: {key}"
    for field in ("motifs", "borders", "patterns", "composition_rules"):
        assert isinstance(sig[field], list)


def test_meta_keys():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    meta = result["_meta"]
    assert "context_key" in meta
    assert "version" in meta
    assert "generated_at" in meta


# ── Context resolution ────────────────────────────────────────────────────────

def test_context_gaming():
    result = generate_brand_identity(BRIEF_GAMING, VI_GAMING, PALETTE_DARK, CTX_GAMING)
    assert result["_meta"]["context_key"] == "gaming"
    assert "gaming" in result["typography"]["primary_font"].lower() or \
           result["typography"]["primary_font"] in ("Rajdhani", "Barlow Condensed")


def test_context_luxury():
    result = generate_brand_identity(BRIEF_LUXURY, VI_LUXURY, PALETTE_BASIC, CTX_LUXURY)
    assert result["_meta"]["context_key"] == "luxury"
    typo = result["typography"]["primary_font"]
    assert typo in ("Cormorant Garamond", "EB Garamond", "Playfair Display")


def test_context_startup():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    ck = result["_meta"]["context_key"]
    assert ck in ("startup", "premium")  # saas → startup, b2b → finance, positioning premium → premium


def test_context_editorial():
    vi_ed = {**VI_BASIC, "context": {"product_type": "editorial"}}
    result = generate_brand_identity(BRIEF_EDITORIAL, vi_ed, PALETTE_BASIC, CTX_EDITORIAL)
    assert result["_meta"]["context_key"] == "editorial"
    assert result["typography"]["primary_font"] in ("Playfair Display", "Libre Baskerville")


def test_context_default_fallback():
    vi_unknown = {**VI_BASIC, "context": {"product_type": "unknown_xyz"}}
    ctx_unknown = {"name": "TestCo", "mode": "light"}
    result = generate_brand_identity(BRIEF_DEFAULT, vi_unknown, PALETTE_BASIC, ctx_unknown)
    assert result["_meta"]["context_key"] == "default"


# ── Typography variation ──────────────────────────────────────────────────────

def test_typography_not_always_inter():
    """Vérifie que la typo varie selon le contexte — pas toujours Inter."""
    contexts = [
        (VI_GAMING,  PALETTE_DARK,  CTX_GAMING,   "gaming"),
        (VI_LUXURY,  PALETTE_BASIC, CTX_LUXURY,   "luxury"),
        (VI_BASIC,   PALETTE_BASIC, CTX_BASIC,    "startup"),
    ]
    fonts = set()
    for vi, pal, ctx, _ in contexts:
        result = generate_brand_identity("test brief", vi, pal, ctx)
        fonts.add(result["typography"]["primary_font"])

    assert len(fonts) >= 2, f"Typography should vary by context, got: {fonts}"
    assert "Inter" not in fonts, "Inter should not appear — use contextual fonts"


# ── Logo type variation ───────────────────────────────────────────────────────

def test_logo_type_varies_by_context():
    result_luxury  = generate_brand_identity(BRIEF_LUXURY,  VI_LUXURY,  PALETTE_BASIC, CTX_LUXURY)
    result_gaming  = generate_brand_identity(BRIEF_GAMING,  VI_GAMING,  PALETTE_DARK,  CTX_GAMING)

    assert result_luxury["logo"]["type"] == "logotype"
    assert result_gaming["logo"]["type"] == "symbol"


def test_logo_generation_prompt_contains_name():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    assert "Synaptic" in result["logo"]["generation_prompt"]


def test_logo_generation_prompt_contains_color():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    assert "#" in result["logo"]["generation_prompt"]  # contient une couleur hex


# ── Reference mode overrides ─────────────────────────────────────────────────

MOCK_REFERENCE = {
    "dominance":       "text",
    "density":         "low",
    "hierarchy":       "calm",
    "spacing":         "airy",
    "composition_bias": {"dominance": "text", "density": "low", "asymmetry": "low", "rhythm": "regular"},
    "palette_hint":    {},
    "_source":         "fallback",
}

MOCK_REFERENCE_AGGRESSIVE = {
    "dominance":       "image",
    "density":         "high",
    "hierarchy":       "aggressive",
    "spacing":         "tight",
    "composition_bias": {"dominance": "image", "density": "high", "asymmetry": "high", "rhythm": "chaotic"},
    "palette_hint":    {},
    "_source":         "test",
}


def test_reference_override_logo_type_text():
    """dominance=text → logo type forced to logotype."""
    result = generate_brand_identity(BRIEF_GAMING, VI_GAMING, PALETTE_DARK, CTX_GAMING,
                                     reference=MOCK_REFERENCE)
    assert result["logo"]["type"] == "logotype"


def test_reference_override_logo_style_calm():
    """hierarchy=calm → logo style prefixed with 'minimal'."""
    result = generate_brand_identity(BRIEF_GAMING, VI_GAMING, PALETTE_DARK, CTX_GAMING,
                                     reference=MOCK_REFERENCE)
    assert "minimal" in result["logo"]["style"].lower()


def test_reference_override_logo_style_aggressive():
    """hierarchy=aggressive → logo style prefixed with 'bold'."""
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC,
                                     reference=MOCK_REFERENCE_AGGRESSIVE)
    assert "bold" in result["logo"]["style"].lower()


def test_reference_override_typography_airy():
    """spacing=airy → typography style contains 'generous tracking'."""
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC,
                                     reference=MOCK_REFERENCE)
    assert "tracking" in result["typography"]["style"].lower()


def test_reference_override_signature_airy():
    """density=low + spacing=airy → composition_rules contains 'negative space'."""
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC,
                                     reference=MOCK_REFERENCE)
    rules_text = " ".join(result["visual_signature"]["composition_rules"]).lower()
    assert "negative space" in rules_text


def test_reference_override_signature_high_density():
    """density=high → composition_rules contains 'dense'."""
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC,
                                     reference=MOCK_REFERENCE_AGGRESSIVE)
    rules_text = " ".join(result["visual_signature"]["composition_rules"]).lower()
    assert "dense" in rules_text


def test_reference_none_no_change():
    """reference=None → résultat identique à sans référence."""
    r1 = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC, reference=None)
    r2 = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    assert r1["typography"]["primary_font"] == r2["typography"]["primary_font"]
    assert r1["logo"]["type"] == r2["logo"]["type"]


# ── Brand name extraction ─────────────────────────────────────────────────────

def test_brand_name_from_context():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    assert result["brand_core"]["name"] == "Synaptic"


def test_brand_name_from_brief_fallback():
    ctx_no_name = {"mode": "light", "family": "saas"}
    result = generate_brand_identity("MonProjet startup B2B", VI_BASIC, PALETTE_BASIC, ctx_no_name)
    assert len(result["brand_core"]["name"]) > 0


# ── Palette integration ───────────────────────────────────────────────────────

def test_logo_svg_uses_palette_primary():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    assert result["logo"]["svg_spec"]["primary_color"] == PALETTE_BASIC["primary"]
    assert result["logo"]["svg_spec"]["background"] == PALETTE_BASIC["background"]


def test_logo_prompt_uses_palette_colors():
    result = generate_brand_identity(BRIEF_STARTUP, VI_BASIC, PALETTE_BASIC, CTX_BASIC)
    prompt = result["logo"]["generation_prompt"]
    assert PALETTE_BASIC["primary"] in prompt or PALETTE_BASIC["background"] in prompt
