"""
brand_identity.py — EURKAI Brand Identity Engine
v1.0.0

Génère un système d'identité visuelle complet depuis brief + visual_intent + palette.
Déterministe. Aucun appel externe. Aucune image générée ici.
Sortie : définition + prompts de génération.
"""
from __future__ import annotations

from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# VERSION
# ─────────────────────────────────────────────────────────────────────────────

VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────────────────────
# MAPPING TABLES — contexte → identité
# ─────────────────────────────────────────────────────────────────────────────

# Clé de contexte depuis product_type / brand_positioning / style_family
_CONTEXT_KEY_MAP: dict[str, str] = {
    # product_type
    "gaming":            "gaming",
    "luxury":            "luxury",
    "craft_artisan":     "luxury",
    "dating":            "dating",
    "social":            "dating",
    "finance":           "finance",
    "fintech":           "finance",
    "saas":              "startup",
    "b2b":               "finance",
    "editorial":         "editorial",
    "magazine":          "editorial",
    "ecommerce":         "ecommerce",
    "ecommerce_catalog": "ecommerce",
    "event":             "event",
    "event_campaign":    "event",
    # brand_positioning
    "playful":           "playful",
    "premium":           "premium",
    "accessible":        "default",
    "serious":           "finance",
    # style_family
    "brand_landing":     "premium",
    "studio_portfolio":  "premium",
    "product_saas":      "startup",
    "editorial_magazine":"editorial",
    "institution_manifesto": "editorial",
}

# ── Logo ───────────────────────────────────────────────────────────────────

_LOGO_MAP: dict[str, dict] = {
    "gaming": {
        "type":         "symbol",
        "style":        "bold geometric",
        "construction": "Sharp angular symbol with aggressive proportions and strong weight. Diagonal axis, high contrast form.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "diamond",
        "svg_rotation": "45deg",
        "svg_style":    "filled",
        "prompt_style": "dark background, neon accent, aggressive geometry, esports aesthetic, sharp angles",
    },
    "luxury": {
        "type":         "logotype",
        "style":        "refined serif logotype",
        "construction": "Letterform-based logotype. High tracking, delicate thin serifs, minimal weight. Name in uppercase spaced capitals.",
        "variations":   ["light", "dark", "monogram"],
        "svg_shape":    "horizontal_rule",
        "svg_rotation": "0deg",
        "svg_style":    "outline_1px",
        "prompt_style": "white background, black or gold, refined letterform, elegant tracking, Hermès / Celine aesthetic",
    },
    "dating": {
        "type":         "combination",
        "style":        "soft symbolic",
        "construction": "Organic rounded symbol (circle or soft form) paired with a friendly rounded sans wordmark. Warm, human proportions.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "circle",
        "svg_rotation": "0deg",
        "svg_style":    "filled_soft",
        "prompt_style": "warm pastel background, soft gradient, organic shapes, approachable, friendly",
    },
    "finance": {
        "type":         "combination",
        "style":        "structured monogram",
        "construction": "Clean geometric monogram initial mark (square or rounded square) with structured neutral-weight wordmark.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "rounded_square",
        "svg_rotation": "0deg",
        "svg_style":    "filled_geometric",
        "prompt_style": "white background, navy or slate blue, geometric precision, trustworthy, institutional",
    },
    "editorial": {
        "type":         "logotype",
        "style":        "editorial display",
        "construction": "High-contrast serif wordmark in editorial proportions. Ink-weight variation between thick and thin strokes.",
        "variations":   ["light", "dark", "abbreviated"],
        "svg_shape":    "rectangle",
        "svg_rotation": "0deg",
        "svg_style":    "letterform",
        "prompt_style": "white background, ink black, high contrast serif typography, New Yorker / Le Monde aesthetic",
    },
    "ecommerce": {
        "type":         "combination",
        "style":        "clean iconic",
        "construction": "Minimal icon mark (shopping-adjacent abstraction) with geometric sans wordmark. Instantly readable at small sizes.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "square",
        "svg_rotation": "0deg",
        "svg_style":    "filled_minimal",
        "prompt_style": "white background, brand primary color, geometric, clean, conversion-optimized, readable at 16px",
    },
    "event": {
        "type":         "combination",
        "style":        "dynamic symbolic",
        "construction": "Bold energetic symbol (star, burst, or motion shape) with strong wordmark. High visibility even at distance.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "starburst",
        "svg_rotation": "0deg",
        "svg_style":    "filled",
        "prompt_style": "dark background, vivid accent, bold motion shapes, festival energy, high contrast",
    },
    "playful": {
        "type":         "combination",
        "style":        "energetic symbol",
        "construction": "Bold playful symbol with personality, paired with a rounded variable-weight wordmark. Color as key differentiator.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "rounded_triangle",
        "svg_rotation": "0deg",
        "svg_style":    "filled",
        "prompt_style": "white background, vivid colors, rounded shapes, energetic, Duolingo / Notion aesthetic",
    },
    "premium": {
        "type":         "symbol",
        "style":        "clean abstract",
        "construction": "Minimal abstract symbol in balanced geometry. Confident weight, perfect optical balance. One primary shape.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "hexagon",
        "svg_rotation": "0deg",
        "svg_style":    "filled",
        "prompt_style": "white background, dark navy or charcoal, minimal abstract symbol, Apple / Stripe aesthetic",
    },
    "startup": {
        "type":         "combination",
        "style":        "minimal tech",
        "construction": "Geometric symbol mark (fragment, arrow, or abstract form) with technical neutral-weight sans wordmark.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "triangle",
        "svg_rotation": "0deg",
        "svg_style":    "filled_technical",
        "prompt_style": "white background, tech-minimal, geometric, Linear / Vercel aesthetic, confident simplicity",
    },
    "default": {
        "type":         "combination",
        "style":        "clean modern",
        "construction": "Simple geometric mark with balanced proportions, paired with a confident modern sans wordmark.",
        "variations":   ["light", "dark", "icon_only"],
        "svg_shape":    "circle",
        "svg_rotation": "0deg",
        "svg_style":    "filled",
        "prompt_style": "white background, brand primary color, clean modern geometry, professional",
    },
}

# ── Icons ──────────────────────────────────────────────────────────────────

_ICON_MAP: dict[str, dict] = {
    "gaming": {
        "style":         "filled geometric",
        "stroke":        "none (filled)",
        "corner_style":  "sharp (0px radius)",
        "consistency_rules": [
            "Filled icons only — never outline",
            "All corners at 0° — no rounding",
            "Bold proportions: icon occupies 80% of bounding box",
            "Strong optical weight — visible at small sizes",
            "Consistent visual mass across all icons in set",
        ],
    },
    "luxury": {
        "style":         "line only",
        "stroke":        "1px",
        "corner_style":  "sharp (0px radius)",
        "consistency_rules": [
            "Strict line-only icons — never filled",
            "Exactly 1px stroke, no exception",
            "No rounding — pure sharp corners",
            "Maximum negative space inside icon boundary",
            "Delicate: if it looks heavy, make it thinner",
        ],
    },
    "dating": {
        "style":         "filled soft",
        "stroke":        "none (filled)",
        "corner_style":  "fully rounded (100% radius)",
        "consistency_rules": [
            "Filled icons with maximum rounding",
            "No sharp edges anywhere",
            "Warm proportions: not too compact, not too thin",
            "Friendly scale — icons feel approachable",
            "Never hard, clinical, or technical",
        ],
    },
    "finance": {
        "style":         "line",
        "stroke":        "1.5px",
        "corner_style":  "slightly rounded (2px radius)",
        "consistency_rules": [
            "Line icons, consistent 1.5px stroke throughout",
            "Minimal: no decoration, no ornament",
            "Slight corner rounding for accessibility",
            "Every icon readable at 16px",
            "Neutral: no personality, pure function",
        ],
    },
    "editorial": {
        "style":         "line fine",
        "stroke":        "1px",
        "corner_style":  "sharp (0px radius)",
        "consistency_rules": [
            "Fine 1px lines — editorial restraint",
            "Sharp corners — no rounding",
            "Clear silhouette first — detail secondary",
            "Strict vertical/horizontal alignment",
            "Never playful — always considered",
        ],
    },
    "ecommerce": {
        "style":         "line",
        "stroke":        "2px",
        "corner_style":  "slightly rounded (3px radius)",
        "consistency_rules": [
            "2px stroke for clarity on product interfaces",
            "Slight rounding for approachability",
            "Action-oriented icons — never decorative",
            "Universal, unambiguous silhouettes",
            "Consistent across cart, wishlist, user, shipping icons",
        ],
    },
    "event": {
        "style":         "filled",
        "stroke":        "none (filled)",
        "corner_style":  "slightly rounded (4px radius)",
        "consistency_rules": [
            "Filled for maximum visibility at distance",
            "Bold weight — readable on dark backgrounds",
            "Slightly rounded: energetic but not childlike",
            "High contrast against both light and dark backgrounds",
        ],
    },
    "playful": {
        "style":         "filled rounded",
        "stroke":        "none (filled)",
        "corner_style":  "rounded (8px radius)",
        "consistency_rules": [
            "Filled with generous rounding",
            "Playful proportions — slight personality in each icon",
            "Consistent weight throughout",
            "Never boring — small detail or tilt allowed",
            "Color can vary per icon for playfulness",
        ],
    },
    "premium": {
        "style":         "line",
        "stroke":        "1.5px",
        "corner_style":  "sharp (0px radius)",
        "consistency_rules": [
            "Clean line style at consistent 1.5px",
            "No rounding — precision is the signal",
            "Minimal: only essential strokes",
            "Equal visual weight across entire icon set",
        ],
    },
    "startup": {
        "style":         "line",
        "stroke":        "1.5px",
        "corner_style":  "slightly rounded (2px radius)",
        "consistency_rules": [
            "Technical line icons",
            "Slight rounding for modern feel",
            "Pixel-perfect at 16px and 24px",
            "No decoration — function only",
            "Heroicons / Lucide aesthetic",
        ],
    },
    "default": {
        "style":         "line",
        "stroke":        "1.5px",
        "corner_style":  "slightly rounded (3px radius)",
        "consistency_rules": [
            "Line icons, 1.5px stroke",
            "Slightly rounded corners for approachability",
            "Unambiguous, clear silhouettes",
            "Consistent optical weight across set",
        ],
    },
}

# ── Typography ─────────────────────────────────────────────────────────────

_TYPO_MAP: dict[str, dict] = {
    "gaming": {
        "primary_font":         "Rajdhani",
        "secondary_font":       "Barlow Condensed",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "condensed, technical, high-energy, aggressive tracking",
        "pairing_logic":        "Condensed display for headers at high weight, clean condensed sans for UI body text. Both feel fast.",
        "custom_font_possible": True,
    },
    "luxury": {
        "primary_font":         "Cormorant Garamond",
        "secondary_font":       "EB Garamond",
        "fallbacks":            ["Georgia", "serif"],
        "style":                "refined high-contrast serif, generous tracking, elegant spacing",
        "pairing_logic":        "High-contrast serif display with wide letter-spacing. Fine weight body in same serif family. Never sans-serif.",
        "custom_font_possible": True,
    },
    "dating": {
        "primary_font":         "Nunito",
        "secondary_font":       "DM Sans",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "rounded, warm, approachable, friendly weight",
        "pairing_logic":        "Friendly rounded sans for headlines, clean neutral for body. Both feel human and never cold.",
        "custom_font_possible": False,
    },
    "finance": {
        "primary_font":         "IBM Plex Sans",
        "secondary_font":       "Source Sans 3",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "structured, neutral, trustworthy, consistent",
        "pairing_logic":        "Technical precision sans throughout. Consistency over personality. Hierarchy through size and weight only.",
        "custom_font_possible": False,
    },
    "editorial": {
        "primary_font":         "Playfair Display",
        "secondary_font":       "Libre Baskerville",
        "fallbacks":            ["Georgia", "serif"],
        "style":                "classical editorial serif, ink-weight contrast, authoritative",
        "pairing_logic":        "High-contrast display serif for headlines. Readable serif body with good leading. Type-led design.",
        "custom_font_possible": True,
    },
    "ecommerce": {
        "primary_font":         "Jost",
        "secondary_font":       "Mulish",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "clean geometric, conversion-optimized, clear hierarchy",
        "pairing_logic":        "Geometric sans for impact headers, neutral legible sans for product descriptions and UI.",
        "custom_font_possible": False,
    },
    "event": {
        "primary_font":         "Barlow",
        "secondary_font":       "Barlow Semi Condensed",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "bold, energetic, variable-weight, high-legibility at scale",
        "pairing_logic":        "Same family at different widths and weights. Big headlines demand compressed, body needs breathing room.",
        "custom_font_possible": True,
    },
    "playful": {
        "primary_font":         "Outfit",
        "secondary_font":       "Plus Jakarta Sans",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "modern, energetic, friendly, variable weight",
        "pairing_logic":        "Geometric variable display with personality, readable contemporary body. Both feel fresh.",
        "custom_font_possible": False,
    },
    "premium": {
        "primary_font":         "Sora",
        "secondary_font":       "Nunito Sans",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "clean, confident, modern premium, slight character",
        "pairing_logic":        "Contemporary geometric for authority and clarity, neutral humanist body for warmth.",
        "custom_font_possible": True,
    },
    "startup": {
        "primary_font":         "Geist",
        "secondary_font":       "DM Sans",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "minimal, technical, forward-looking, precise",
        "pairing_logic":        "Tech-minimal monospace-adjacent sans for brand presence, readable DM Sans for content.",
        "custom_font_possible": False,
    },
    "default": {
        "primary_font":         "Sora",
        "secondary_font":       "Source Sans 3",
        "fallbacks":            ["system-ui", "sans-serif"],
        "style":                "neutral, balanced, versatile, contemporary",
        "pairing_logic":        "Contemporary rounded sans for headlines, highly legible neutral for body. Broadly compatible.",
        "custom_font_possible": False,
    },
}

# ── Visual Signature ────────────────────────────────────────────────────────

_SIGNATURE_MAP: dict[str, dict] = {
    "gaming": {
        "motifs":            ["diagonal slash overlays", "angular corner marks", "glitch fragment shapes"],
        "borders":           ["thick diagonal cut edges", "angled clip-path frames", "sharp inset borders no radius"],
        "patterns":          ["hex grid texture", "circuit line overlay", "scanline pattern"],
        "composition_rules": [
            "Content bleeds to edges — no comfortable margins",
            "Diagonal composition lines as structural element",
            "High-contrast section transitions — never soft gradients",
            "Dark base with vivid accent explosions",
        ],
    },
    "luxury": {
        "motifs":            ["thin horizontal rules", "minimal dot accents", "oversized letter marks"],
        "borders":           ["hairline 0.5px borders", "wide inner padding as border substitute", "no decorative ornaments"],
        "patterns":          ["subtle grain overlay only", "linen texture at low opacity", "no repeating pattern"],
        "composition_rules": [
            "Maximum negative space — content is sculpture",
            "Center-aligned or extreme asymmetry, never middle-ground",
            "White space is intentional, never incidental",
            "One focal point per section, nothing competes",
        ],
    },
    "dating": {
        "motifs":            ["soft organic blobs", "gradient halos", "abstract heart-adjacent shapes"],
        "borders":           ["rounded soft borders 12px+", "gradient border effects", "no sharp lines"],
        "patterns":          ["soft dot confetti", "gentle pastel gradient backgrounds", "organic blob overlays"],
        "composition_rules": [
            "Warm, inviting sections — nothing feels clinical",
            "Asymmetric but balanced — feels natural",
            "Gradients over flat colors",
            "Images of people whenever possible",
        ],
    },
    "finance": {
        "motifs":            ["thin grid lines", "data visualization abstracts", "minimal geometric dividers"],
        "borders":           ["1px grid borders", "full-width thin separators", "hairline section dividers"],
        "patterns":          ["subtle dot matrix", "grid background at 2% opacity"],
        "composition_rules": [
            "Strict grid alignment — no exceptions",
            "Data before decoration — charts over photography",
            "Consistent spacing system (8pt grid)",
            "Never surprise the user — predictable hierarchy",
        ],
    },
    "editorial": {
        "motifs":            ["column rules", "ink marks", "pull-quote delimiters", "headline underlines"],
        "borders":           ["thick editorial rules 4-6px", "column dividers", "text-width decorative rules"],
        "patterns":          ["newsprint grain", "paper texture at low opacity"],
        "composition_rules": [
            "Type leads every layout decision",
            "Column-based structure always",
            "White space is editorial choice, not padding",
            "Photography serves text — never dominates",
        ],
    },
    "ecommerce": {
        "motifs":            ["product shadow shapes", "badge elements", "price tag forms"],
        "borders":           ["clean 1px product card borders", "subtle hover states", "rounded cards 8px"],
        "patterns":          ["no pattern — products are the visual"],
        "composition_rules": [
            "Product photography is hero",
            "Consistent card grid — no layout surprises",
            "CTA always visible — never below fold",
            "Speed over beauty — clarity over concept",
        ],
    },
    "event": {
        "motifs":            ["burst shapes", "motion lines", "date/countdown abstract elements"],
        "borders":           ["bold strokes", "colored accent borders", "cutout masked sections"],
        "patterns":          ["halftone dots", "diagonal stripe accents", "geometric fill patterns"],
        "composition_rules": [
            "Bold, immediate visual impact",
            "Large type — readable at poster scale",
            "High energy section transitions",
            "Dark or vivid base, never neutral",
        ],
    },
    "playful": {
        "motifs":            ["rounded geometric shapes", "color block accents", "wobbly organic outlines"],
        "borders":           ["thick rounded borders 6px+", "color-filled borders as accent"],
        "patterns":          ["polka dots", "small geometric repeat", "hand-drawn aesthetic at low opacity"],
        "composition_rules": [
            "Color is personality — use it boldly",
            "Asymmetry as feature, not bug",
            "Typography can be expressive",
            "Joy is the brief — if it feels boring, add color",
        ],
    },
    "premium": {
        "motifs":            ["minimal geometric accents", "brand color thin lines", "oversized letter watermarks"],
        "borders":           ["thin precise borders 1px", "subtle inner glow effects", "no decorative borders"],
        "patterns":          ["subtle halftone at 3% opacity", "no strong patterns"],
        "composition_rules": [
            "Restraint is sophistication",
            "One statement element per section",
            "Brand color as accent, never base",
            "Precision in every margin and spacing decision",
        ],
    },
    "startup": {
        "motifs":            ["gradient mesh shapes", "code-inspired fragments", "geometric data abstracts"],
        "borders":           ["border-radius cards 8px", "colored gradient borders", "glassmorphism effects"],
        "patterns":          ["dot grid", "mesh gradient backgrounds", "subtle glow halos"],
        "composition_rules": [
            "Product screenshot is hero — never bury it",
            "Social proof immediately after hero",
            "Gradient as energy signal",
            "Dark or light — pick one, commit fully",
        ],
    },
    "default": {
        "motifs":            ["geometric shapes", "brand color accent marks", "subtle dividers"],
        "borders":           ["clean 1px borders", "colored accent borders on key elements"],
        "patterns":          ["no pattern by default"],
        "composition_rules": [
            "Balanced layout with clear visual hierarchy",
            "Consistent spacing system",
            "Brand color as accent, not background",
            "Content clarity over visual complexity",
        ],
    },
}

# ── Personality + Tone ──────────────────────────────────────────────────────

_PERSONALITY_MAP: dict[str, list] = {
    "gaming":    ["competitive", "bold", "dynamic", "immersive"],
    "luxury":    ["refined", "exclusive", "timeless", "effortless"],
    "dating":    ["warm", "genuine", "playful", "connecting"],
    "finance":   ["trustworthy", "precise", "stable", "transparent"],
    "editorial": ["authoritative", "thoughtful", "curated", "intelligent"],
    "ecommerce": ["clear", "convenient", "confident", "direct"],
    "event":     ["energetic", "experiential", "memorable", "live"],
    "playful":   ["energetic", "friendly", "creative", "surprising"],
    "premium":   ["confident", "modern", "aspirational", "focused"],
    "startup":   ["innovative", "lean", "ambitious", "direct"],
    "default":   ["professional", "reliable", "clear", "modern"],
}

_TONE_MAP: dict[str, str] = {
    "gaming":    "aggressive, energetic, immersive",
    "luxury":    "understated, refined, exclusive",
    "dating":    "warm, genuine, encouraging",
    "finance":   "reassuring, precise, structured",
    "editorial": "intelligent, considered, authoritative",
    "ecommerce": "direct, helpful, confident",
    "event":     "exciting, urgent, experiential",
    "playful":   "enthusiastic, friendly, fun",
    "premium":   "confident, modern, aspirational",
    "startup":   "ambitious, direct, clear",
    "default":   "professional, balanced, clear",
}

# Icon examples by context
_ICON_EXAMPLES: dict[str, list] = {
    "gaming":    ["sword", "shield", "controller", "trophy", "lightning bolt", "skull"],
    "luxury":    ["diamond", "leaf", "crown", "key", "ribbon", "clock"],
    "dating":    ["heart", "message bubble", "star", "person", "location pin", "sparkle"],
    "finance":   ["chart bar", "lock", "document", "checkmark", "building", "card"],
    "editorial": ["pen", "book", "quote mark", "eye", "bookmark", "share"],
    "ecommerce": ["cart", "bag", "heart", "search", "filter", "star rating"],
    "event":     ["calendar", "ticket", "location", "music note", "camera", "map pin"],
    "playful":   ["smile", "lightning", "star", "rocket", "fire", "rainbow"],
    "premium":   ["hexagon", "arrow", "diamond", "grid", "circle", "dot"],
    "startup":   ["code", "terminal", "bolt", "layers", "arrow-right", "users"],
    "default":   ["home", "user", "search", "settings", "arrow", "check"],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_context_key(visual_intent: dict, context: dict) -> str:
    """Résout la clé de contexte depuis visual_intent + context dict."""
    vi_ctx       = visual_intent.get("context", {})
    product_type = (
        vi_ctx.get("product_type")
        or context.get("family", "")
        or context.get("product_type", "")
    )
    positioning  = vi_ctx.get("brand_positioning", "")
    style_family = context.get("style_family", "")

    for key in (product_type, positioning, style_family):
        if key in _CONTEXT_KEY_MAP:
            return _CONTEXT_KEY_MAP[key]

    return "default"


def _extract_name(brief: str, context: dict) -> str:
    """Extrait le nom de la marque depuis context ou brief."""
    return context.get("name") or context.get("project_name") or brief[:30].split(",")[0].strip()


def _apply_reference_overrides(data: dict, reference: dict, section: str) -> dict:
    """
    Adapte une section de l'identité depuis une reference_analysis.
    reference = output de design.coherence.apply → reference_analysis
    Traduit, ne copie pas.
    """
    if not reference:
        return data

    result    = dict(data)
    dominance = reference.get("dominance", "balanced")
    hierarchy = reference.get("hierarchy", "strong")
    spacing   = reference.get("spacing", "balanced")
    density   = reference.get("density", "medium")
    cb        = reference.get("composition_bias", {})

    if section == "logo":
        if dominance == "text":
            result["type"] = "logotype"
        elif dominance == "image":
            result["type"] = "symbol"
        if hierarchy == "aggressive":
            result["style"] = "bold " + result.get("style", "")
        elif hierarchy == "calm":
            result["style"] = "minimal " + result.get("style", "")

    elif section == "icons":
        if hierarchy == "aggressive":
            result["stroke"] = "2px" if "line" in result.get("style", "") else result["stroke"]
            result["corner_style"] = "sharp (0px radius)"
        elif hierarchy == "calm":
            result["corner_style"] = "fully rounded (8px radius)"
        if dominance == "text":
            result["style"] = "line fine"

    elif section == "typography":
        if spacing == "airy":
            result["style"] = result.get("style", "") + ", generous tracking and leading"
        elif spacing == "tight":
            result["style"] = result.get("style", "") + ", compact condensed style"
        if hierarchy == "aggressive":
            result["style"] = "bold heavy " + result.get("style", "")

    elif section == "signature":
        if density == "low" and spacing == "airy":
            result["composition_rules"] = [
                "Maximum negative space — reference confirms airy composition",
            ] + result.get("composition_rules", [])
        elif density == "high":
            result["composition_rules"] = [
                "Dense, content-rich layout — reference confirms high density",
            ] + result.get("composition_rules", [])
        if cb.get("asymmetry") == "high":
            result["composition_rules"].append("Strong asymmetric composition — per reference analysis")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# SUB-GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_brand_core(brief: str, visual_intent: dict, context: dict, ck: str) -> dict:
    vi_ctx      = visual_intent.get("context", {})
    name        = _extract_name(brief, context)
    tone        = _TONE_MAP.get(ck, _TONE_MAP["default"])
    personality = _PERSONALITY_MAP.get(ck, _PERSONALITY_MAP["default"])
    positioning = vi_ctx.get("brand_positioning") or context.get("positioning", "professional")
    return {
        "name":        name,
        "tone":        tone,
        "personality": personality,
        "positioning": positioning,
    }


def _generate_logo(
    brief: str,
    visual_intent: dict,
    palette: dict,
    context: dict,
    brand_core: dict,
    ck: str,
    reference: dict | None,
) -> dict:
    spec    = dict(_LOGO_MAP.get(ck, _LOGO_MAP["default"]))
    primary = palette.get("primary", "#2563EB")
    bg      = palette.get("background", "#FFFFFF")
    name    = brand_core["name"]

    spec = _apply_reference_overrides(spec, reference or {}, "logo")

    prompt = (
        f"Professional logo design for '{name}'. "
        f"{spec['construction']}. "
        f"Style: {spec['style']}. "
        f"Primary color: {primary}. Background: {bg}. "
        f"{spec.pop('prompt_style', '')}. "
        f"Vector illustration. Clean, scalable, isolated on white background. "
        f"No lorem ipsum. No decorative text unless logotype."
    )

    svg_spec = {
        "shape":         spec.pop("svg_shape",    "circle"),
        "rotation":      spec.pop("svg_rotation", "0deg"),
        "style":         spec.pop("svg_style",    "filled"),
        "primary_color": primary,
        "background":    bg,
        "viewport":      "0 0 512 512",
        "proportions":   "1:1",
        "format":        "SVG vector, scalable, 512×512px base",
        "notes":         f"Symbol extracted from {spec.get('type','combination')} logo system",
    }

    return {
        "type":              spec["type"],
        "style":             spec["style"],
        "construction":      spec["construction"],
        "variations":        spec["variations"],
        "generation_prompt": prompt,
        "svg_spec":          svg_spec,
    }


def _generate_icons(
    visual_intent: dict,
    context: dict,
    ck: str,
    reference: dict | None,
) -> dict:
    spec     = dict(_ICON_MAP.get(ck, _ICON_MAP["default"]))
    examples = _ICON_EXAMPLES.get(ck, _ICON_EXAMPLES["default"])

    spec = _apply_reference_overrides(spec, reference or {}, "icons")

    prompt = (
        f"Icon set in {spec['style']} style. "
        f"Stroke: {spec['stroke']}. "
        f"Corner style: {spec['corner_style']}. "
        f"Pixel-perfect at 24×24px and 16×16px. "
        f"SVG format, monochrome first then brand color version. "
        f"Consistency rule: same visual weight across all icons in the set. "
        f"Reference icons: {', '.join(examples[:4])} — same system for all."
    )

    return {
        "style":              spec["style"],
        "stroke":             spec["stroke"],
        "corner_style":       spec["corner_style"],
        "consistency_rules":  spec["consistency_rules"],
        "generation_prompt":  prompt,
        "examples":           examples,
    }


def _generate_typography(
    visual_intent: dict,
    context: dict,
    ck: str,
    reference: dict | None,
) -> dict:
    spec = dict(_TYPO_MAP.get(ck, _TYPO_MAP["default"]))
    spec = _apply_reference_overrides(spec, reference or {}, "typography")
    return {
        "primary_font":         spec["primary_font"],
        "secondary_font":       spec["secondary_font"],
        "fallbacks":            spec["fallbacks"],
        "style":                spec["style"],
        "pairing_logic":        spec["pairing_logic"],
        "custom_font_possible": spec["custom_font_possible"],
    }


def _generate_visual_signature(
    visual_intent: dict,
    palette: dict,
    context: dict,
    ck: str,
    reference: dict | None,
) -> dict:
    spec = dict(_SIGNATURE_MAP.get(ck, _SIGNATURE_MAP["default"]))
    spec = _apply_reference_overrides(spec, reference or {}, "signature")
    return {
        "motifs":            spec["motifs"],
        "borders":           spec["borders"],
        "patterns":          spec["patterns"],
        "composition_rules": spec["composition_rules"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def generate_brand_identity(
    brief: str,
    visual_intent: dict,
    palette: dict,
    context: dict,
    reference: dict | None = None,
) -> dict:
    """
    Génère un système d'identité visuelle complet.

    Args:
        brief          : str  — description de la marque/projet
        visual_intent  : dict — from generate_visual_intent()
        palette        : dict — from generate_palette()
        context        : dict — {name, mode, family, product_type, ...}
        reference      : dict | None — reference_analysis from visual_coherence_engine CASE 3
                         → adapte style sans copier

    Returns:
        dict — brand_identity avec brand_core, logo, icons, typography, visual_signature
    """
    ck = _resolve_context_key(visual_intent, context)

    brand_core = _generate_brand_core(brief, visual_intent, context, ck)
    logo       = _generate_logo(brief, visual_intent, palette, context, brand_core, ck, reference)
    icons      = _generate_icons(visual_intent, context, ck, reference)
    typography = _generate_typography(visual_intent, context, ck, reference)
    signature  = _generate_visual_signature(visual_intent, palette, context, ck, reference)

    return {
        "brand_core":       brand_core,
        "logo":             logo,
        "icons":            icons,
        "typography":       typography,
        "visual_signature": signature,
        "_meta": {
            "context_key": ck,
            "version":     VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
