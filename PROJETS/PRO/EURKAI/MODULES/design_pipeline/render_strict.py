"""
render_strict — Rendu HTML strict depuis un DesignPlan.

Règles absolues :
- Utilise layout_strategy EXACTEMENT (data-layout-strategy sur <body>)
- Utilise hero_type EXACTEMENT (data-hero-type sur section hero)
- Utilise section_types EXACTEMENT dans l'ordre défini
- PAS de fallback, PAS de normalisation, PAS d'override silencieux
- Si un section_type n'a pas de builder → RenderError (pas de fallback)
- Chaque section injecte data-section-type="<type>"
- Chaque section injecte data-section-index="<n>"
"""

from __future__ import annotations

from typing import Any


# ─── Exception ────────────────────────────────────────────────────────────────

class RenderError(Exception):
    """Échec de rendu — pas de fallback, erreur remontée."""
    def __init__(self, reason: str):
        super().__init__(f"[render_strict] {reason}")


# ─── Palette helpers ──────────────────────────────────────────────────────────

_PALETTE_DEFAULTS: dict[str, dict[str, str]] = {
    # startup
    "startup_blue":     {"primary": "#2563EB", "secondary": "#1E40AF", "accent": "#3B82F6",
                         "bg": "#FFFFFF", "surface": "#F8FAFC", "text": "#0F172A", "muted": "#64748B"},
    "startup_green":    {"primary": "#059669", "secondary": "#047857", "accent": "#10B981",
                         "bg": "#FFFFFF", "surface": "#F0FDF4", "text": "#064E3B", "muted": "#6B7280"},
    "startup_purple":   {"primary": "#7C3AED", "secondary": "#6D28D9", "accent": "#8B5CF6",
                         "bg": "#FFFFFF", "surface": "#FAF5FF", "text": "#1E1B4B", "muted": "#6B7280"},
    # luxury
    "luxury_black":     {"primary": "#0A0A0A", "secondary": "#1A1A1A", "accent": "#C9A84C",
                         "bg": "#FAFAF8", "surface": "#F5F5F0", "text": "#0A0A0A", "muted": "#6B6B6B"},
    "luxury_cream":     {"primary": "#C9A87C", "secondary": "#A07850", "accent": "#E8D5B7",
                         "bg": "#FDFAF5", "surface": "#F8F3EC", "text": "#1A0F00", "muted": "#8B7355"},
    "luxury_gold":      {"primary": "#B8860B", "secondary": "#8B6914", "accent": "#FFD700",
                         "bg": "#0A0A0A", "surface": "#111111", "text": "#F5F5F0", "muted": "#8B7355"},
    # editorial
    "editorial_cool":   {"primary": "#1A1A2E", "secondary": "#16213E", "accent": "#0F3460",
                         "bg": "#FFFFFF", "surface": "#F7F7F9", "text": "#1A1A2E", "muted": "#6B6B80"},
    "editorial_warm":   {"primary": "#2C1810", "secondary": "#4A2C1A", "accent": "#C4602A",
                         "bg": "#FFFEF8", "surface": "#FEF9F0", "text": "#2C1810", "muted": "#7A5A4A"},
    "editorial_mono":   {"primary": "#111111", "secondary": "#333333", "accent": "#111111",
                         "bg": "#FFFFFF", "surface": "#F5F5F5", "text": "#111111", "muted": "#888888"},
    # corporate
    "corporate_navy":   {"primary": "#1E3A5F", "secondary": "#152D4A", "accent": "#2E86AB",
                         "bg": "#FFFFFF", "surface": "#F0F4F8", "text": "#1A2A3A", "muted": "#64748B"},
    "corporate_slate":  {"primary": "#334155", "secondary": "#1E293B", "accent": "#475569",
                         "bg": "#FFFFFF", "surface": "#F8FAFC", "text": "#0F172A", "muted": "#64748B"},
    "corporate_charcoal":{"primary": "#374151", "secondary": "#1F2937", "accent": "#4B5563",
                         "bg": "#FFFFFF", "surface": "#F9FAFB", "text": "#111827", "muted": "#6B7280"},
    # warm human
    "warm_terracotta":  {"primary": "#C4602A", "secondary": "#9C4220", "accent": "#E8845A",
                         "bg": "#FFFEF8", "surface": "#FEF5EC", "text": "#2C1205", "muted": "#9A7060"},
    "warm_sage":        {"primary": "#5A7A5C", "secondary": "#3D5C3F", "accent": "#7CA07E",
                         "bg": "#FAFDF8", "surface": "#F2F7F2", "text": "#1A2E1C", "muted": "#6B7A6C"},
    "warm_peach":       {"primary": "#E8845A", "secondary": "#C4602A", "accent": "#F4A880",
                         "bg": "#FFFCF8", "surface": "#FEF7F0", "text": "#3A1A08", "muted": "#A07060"},
    # tech
    "tech_dark_blue":   {"primary": "#0066CC", "secondary": "#004A99", "accent": "#00A8FF",
                         "bg": "#080E1A", "surface": "#0D1526", "text": "#E8F4FF", "muted": "#5B7FA6"},
    "tech_cyan":        {"primary": "#00BCD4", "secondary": "#0097A7", "accent": "#00E5FF",
                         "bg": "#0A0E12", "surface": "#0F1419", "text": "#E0F7FA", "muted": "#4A7A82"},
    "tech_violet":      {"primary": "#7B2FBE", "secondary": "#5C1FA0", "accent": "#AB47BC",
                         "bg": "#0D0A14", "surface": "#13101E", "text": "#EDE7F6", "muted": "#7B6A8A"},
    # brutalist
    "brutalist_bw":     {"primary": "#000000", "secondary": "#111111", "accent": "#000000",
                         "bg": "#FFFFFF", "surface": "#EEEEEE", "text": "#000000", "muted": "#555555"},
    "brutalist_accent": {"primary": "#000000", "secondary": "#111111", "accent": "#FF0000",
                         "bg": "#FFFFFF", "surface": "#F0F0F0", "text": "#000000", "muted": "#444444"},
    "brutalist_raw":    {"primary": "#1A1A1A", "secondary": "#0A0A0A", "accent": "#FFD600",
                         "bg": "#F0EFE8", "surface": "#E8E7E0", "text": "#0A0A0A", "muted": "#5A5A5A"},
    # organic
    "organic_earth":    {"primary": "#6B4226", "secondary": "#4A2C18", "accent": "#A05C3A",
                         "bg": "#FDFAF5", "surface": "#F5EEE4", "text": "#2C1A0A", "muted": "#8A6A50"},
    "organic_forest":   {"primary": "#2D5016", "secondary": "#1E3A0F", "accent": "#4A7C2A",
                         "bg": "#F8FCF5", "surface": "#EEF7E8", "text": "#0F2005", "muted": "#5A7045"},
    "organic_sand":     {"primary": "#C4A882", "secondary": "#A08060", "accent": "#DFC4A0",
                         "bg": "#FDFBF5", "surface": "#F8F4EC", "text": "#3A2A18", "muted": "#8A7A60"},
    # premium craft
    "craft_linen":      {"primary": "#3A2A18", "secondary": "#2A1C10", "accent": "#6A4A2A",
                         "bg": "#F8F4EC", "surface": "#F2EDE0", "text": "#1A0E06", "muted": "#7A6A55"},
    "craft_copper":     {"primary": "#B87333", "secondary": "#8C5A28", "accent": "#D4944A",
                         "bg": "#FAFAF5", "surface": "#F5F0E8", "text": "#2A1A08", "muted": "#8A7A60"},
    "craft_ink":        {"primary": "#1C2B4A", "secondary": "#12213A", "accent": "#2E4A7A",
                         "bg": "#F8F9FA", "surface": "#EEF0F5", "text": "#0A1220", "muted": "#5A6A80"},
    # bold
    "bold_red":         {"primary": "#DC2626", "secondary": "#B91C1C", "accent": "#EF4444",
                         "bg": "#FFFFFF", "surface": "#FEF2F2", "text": "#1A0505", "muted": "#7F7F7F"},
    "bold_orange":      {"primary": "#EA580C", "secondary": "#C2410C", "accent": "#F97316",
                         "bg": "#FFFFFF", "surface": "#FFF7ED", "text": "#1A0800", "muted": "#7F7F7F"},
    "bold_electric":    {"primary": "#0EA5E9", "secondary": "#0284C7", "accent": "#38BDF8",
                         "bg": "#030712", "surface": "#0D1117", "text": "#F0F9FF", "muted": "#4A6A80"},
    # playful
    "playful_vivid":    {"primary": "#7C3AED", "secondary": "#EC4899", "accent": "#F59E0B",
                         "bg": "#FFFFFF", "surface": "#FAF5FF", "text": "#1A0A2E", "muted": "#7F7F7F"},
    "playful_pastel":   {"primary": "#A78BFA", "secondary": "#F9A8D4", "accent": "#FCD34D",
                         "bg": "#FEFCFF", "surface": "#F5F0FF", "text": "#2A1A40", "muted": "#9A8AB0"},
    "playful_neon":     {"primary": "#00FF88", "secondary": "#FF0080", "accent": "#00E0FF",
                         "bg": "#0A0A0A", "surface": "#111111", "text": "#F0FFF0", "muted": "#4A7A5A"},
    # creative studio
    "studio_gradient":  {"primary": "#6366F1", "secondary": "#8B5CF6", "accent": "#EC4899",
                         "bg": "#030712", "surface": "#0D0D1A", "text": "#F8F8FF", "muted": "#6A6A90"},
    "studio_minimal":   {"primary": "#18181B", "secondary": "#27272A", "accent": "#52525B",
                         "bg": "#FAFAFA", "surface": "#F4F4F5", "text": "#09090B", "muted": "#71717A"},
    "studio_eclectic":  {"primary": "#DC2626", "secondary": "#1D4ED8", "accent": "#D97706",
                         "bg": "#FAFAF8", "surface": "#F5F0E8", "text": "#0A0A0A", "muted": "#6A6A6A"},
}

_PALETTE_FALLBACK = {
    "primary": "#1A1A2E", "secondary": "#16213E", "accent": "#0F3460",
    "bg": "#FFFFFF", "surface": "#F7F7F9", "text": "#1A1A2E", "muted": "#6B7280",
}


def _resolve_palette(palette_family: str, palette_override: dict | None) -> dict:
    """Résout la palette CSS depuis palette_family. palette_override prioritaire."""
    if palette_override and all(k in palette_override for k in ("primary", "bg", "text")):
        return palette_override
    return _PALETTE_DEFAULTS.get(palette_family, _PALETTE_FALLBACK)


# ─── Typography helpers ───────────────────────────────────────────────────────

_TYPOGRAPHY_STACKS: dict[str, dict[str, str]] = {
    "serif_editorial":     {"heading": "'Playfair Display', Georgia, serif",
                            "body":    "'Source Serif Pro', Georgia, serif",
                            "mono":    "monospace"},
    "sans_editorial":      {"heading": "'DM Sans', system-ui, sans-serif",
                            "body":    "'DM Sans', system-ui, sans-serif",
                            "mono":    "monospace"},
    "serif_luxury":        {"heading": "'Cormorant Garamond', 'Times New Roman', serif",
                            "body":    "'Libre Baskerville', Georgia, serif",
                            "mono":    "monospace"},
    "sans_luxury":         {"heading": "'Montserrat', system-ui, sans-serif",
                            "body":    "'Lato', system-ui, sans-serif",
                            "mono":    "monospace"},
    "display_playful":     {"heading": "'Fredoka One', 'Comic Sans MS', cursive",
                            "body":    "'Nunito', system-ui, sans-serif",
                            "mono":    "monospace"},
    "rounded_playful":     {"heading": "'Nunito', system-ui, sans-serif",
                            "body":    "'Nunito', system-ui, sans-serif",
                            "mono":    "monospace"},
    "humanist_sans":       {"heading": "'Inter', system-ui, sans-serif",
                            "body":    "'Inter', system-ui, sans-serif",
                            "mono":    "monospace"},
    "serif_warm":          {"heading": "'Lora', Georgia, serif",
                            "body":    "'Lora', Georgia, serif",
                            "mono":    "monospace"},
    "geometric_sans":      {"heading": "'Inter', 'Helvetica Neue', sans-serif",
                            "body":    "'Inter', 'Helvetica Neue', sans-serif",
                            "mono":    "monospace"},
    "system_sans":         {"heading": "system-ui, -apple-system, sans-serif",
                            "body":    "system-ui, -apple-system, sans-serif",
                            "mono":    "monospace"},
    "corporate_sans":      {"heading": "'IBM Plex Sans', system-ui, sans-serif",
                            "body":    "'IBM Plex Sans', system-ui, sans-serif",
                            "mono":    "monospace"},
    "corporate_serif":     {"heading": "'Merriweather', Georgia, serif",
                            "body":    "'Merriweather', Georgia, serif",
                            "mono":    "monospace"},
    "mono_tech":           {"heading": "'JetBrains Mono', 'Fira Code', monospace",
                            "body":    "'JetBrains Mono', 'Fira Code', monospace",
                            "mono":    "'JetBrains Mono', monospace"},
    "geometric_tech":      {"heading": "'Space Grotesk', system-ui, sans-serif",
                            "body":    "'Space Grotesk', system-ui, sans-serif",
                            "mono":    "monospace"},
    "slab_brutal":         {"heading": "'Roboto Slab', 'Georgia', serif",
                            "body":    "'Roboto Slab', 'Georgia', serif",
                            "mono":    "monospace"},
    "grotesque_brutal":    {"heading": "'Haas Grotesk', 'Arial', sans-serif",
                            "body":    "'Haas Grotesk', 'Arial', sans-serif",
                            "mono":    "monospace"},
    "organic_serif":       {"heading": "'Crimson Text', 'Georgia', serif",
                            "body":    "'Crimson Text', 'Georgia', serif",
                            "mono":    "monospace"},
    "handwritten_natural": {"heading": "'Caveat', 'Brush Script MT', cursive",
                            "body":    "'Lato', system-ui, sans-serif",
                            "mono":    "monospace"},
    "refined_serif":       {"heading": "'EB Garamond', 'Times New Roman', serif",
                            "body":    "'EB Garamond', 'Times New Roman', serif",
                            "mono":    "monospace"},
    "craft_sans":          {"heading": "'Josefin Sans', system-ui, sans-serif",
                            "body":    "'Josefin Sans', system-ui, sans-serif",
                            "mono":    "monospace"},
    "bold_display":        {"heading": "'Oswald', 'Arial Black', sans-serif",
                            "body":    "'Open Sans', system-ui, sans-serif",
                            "mono":    "monospace"},
    "condensed_impact":    {"heading": "'Barlow Condensed', 'Arial Narrow', sans-serif",
                            "body":    "'Barlow', system-ui, sans-serif",
                            "mono":    "monospace"},
    "experimental_type":   {"heading": "'Space Mono', monospace",
                            "body":    "'Space Mono', monospace",
                            "mono":    "'Space Mono', monospace"},
    "mixed_editorial":     {"heading": "'Playfair Display', Georgia, serif",
                            "body":    "'DM Sans', system-ui, sans-serif",
                            "mono":    "monospace"},
}

_TYPO_FALLBACK = {
    "heading": "system-ui, sans-serif",
    "body":    "system-ui, sans-serif",
    "mono":    "monospace",
}


def _resolve_fonts(typography_family: str) -> dict:
    return _TYPOGRAPHY_STACKS.get(typography_family, _TYPO_FALLBACK)


# ─── CSS global ───────────────────────────────────────────────────────────────

def _build_css(palette: dict, fonts: dict, composition: dict) -> str:
    density = composition.get("density", "medium")
    spacing_base = {"low": "1.6rem", "medium": "1.2rem", "high": "0.9rem"}.get(density, "1.2rem")
    section_padding = {"low": "7rem 0", "medium": "5rem 0", "high": "3.5rem 0"}.get(density, "5rem 0")

    return f"""
:root {{
  --color-primary:   {palette['primary']};
  --color-secondary: {palette['secondary']};
  --color-accent:    {palette['accent']};
  --color-bg:        {palette['bg']};
  --color-surface:   {palette['surface']};
  --color-text:      {palette['text']};
  --color-muted:     {palette['muted']};
  --font-heading:    {fonts['heading']};
  --font-body:       {fonts['body']};
  --font-mono:       {fonts['mono']};
  --spacing-base:    {spacing_base};
  --section-padding: {section_padding};
  --radius-sm: 4px; --radius-md: 8px; --radius-lg: 16px;
  --transition: 0.25s ease;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html {{ scroll-behavior: smooth; -webkit-font-smoothing: antialiased; }}

body {{
  background-color: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: var(--spacing-base);
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-heading);
  color: var(--color-text);
  line-height: 1.1;
  letter-spacing: -0.02em;
}}

a {{ color: var(--color-primary); text-decoration: none; transition: color var(--transition); }}
a:hover {{ color: var(--color-accent); }}

img {{ max-width: 100%; height: auto; display: block; }}

.container {{ max-width: 1200px; margin: 0 auto; padding: 0 2rem; }}
.container--narrow {{ max-width: 760px; margin: 0 auto; padding: 0 2rem; }}
.container--wide {{ max-width: 1440px; margin: 0 auto; padding: 0 2rem; }}

/* ── Buttons ── */
.btn {{
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1.75rem; border-radius: var(--radius-md);
  font-family: var(--font-heading); font-weight: 600; font-size: 0.95rem;
  cursor: pointer; border: 2px solid transparent; transition: all var(--transition);
  text-decoration: none;
}}
.btn--primary {{
  background: var(--color-primary); color: var(--color-bg);
  border-color: var(--color-primary);
}}
.btn--primary:hover {{ background: var(--color-secondary); border-color: var(--color-secondary); color: var(--color-bg); }}
.btn--outline {{
  background: transparent; color: var(--color-primary);
  border-color: var(--color-primary);
}}
.btn--outline:hover {{ background: var(--color-primary); color: var(--color-bg); }}

/* ── Layout helpers ── */
.grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; }}
.grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; }}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }}
@media (max-width: 900px) {{
  .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
}}

/* ── Tag / badge ── */
.tag {{
  display: inline-block; padding: 0.25rem 0.75rem;
  background: var(--color-surface); color: var(--color-muted);
  border-radius: 100px; font-size: 0.8rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
}}
.tag--accent {{
  background: var(--color-accent); color: var(--color-bg);
}}

/* ── Section base ── */
[data-section-type] {{
  padding: var(--section-padding);
  position: relative;
}}
[data-section-type].surface {{
  background: var(--color-surface);
}}

/* ── Navbar ── */
.navbar {{
  position: sticky; top: 0; z-index: 100;
  background: var(--color-bg); border-bottom: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent);
  padding: 1rem 0;
}}
.navbar__inner {{
  display: flex; align-items: center; justify-content: space-between;
}}
.navbar__logo {{
  font-family: var(--font-heading); font-weight: 800; font-size: 1.4rem;
  color: var(--color-primary);
}}
.navbar__links {{
  display: flex; gap: 2rem; list-style: none;
  font-size: 0.9rem; font-weight: 500;
}}
.navbar__links a {{ color: var(--color-text); }}
.navbar__links a:hover {{ color: var(--color-primary); }}

/* ── Footer ── */
.footer {{
  background: var(--color-text); color: var(--color-bg);
  padding: 3rem 0 2rem;
}}
.footer a {{ color: var(--color-muted); }}
.footer__bottom {{
  margin-top: 2rem; padding-top: 1.5rem;
  border-top: 1px solid rgba(255,255,255,0.1);
  font-size: 0.85rem; color: var(--color-muted);
  display: flex; justify-content: space-between;
}}
""".strip()


# ─── Section builders ─────────────────────────────────────────────────────────
# Chaque builder : fn(idx, context, plan) → str (HTML fragment)

def _b_hero(idx: int, ctx: dict, plan: dict) -> str:
    hero_cfg   = plan.get("hero_config", {})
    hero_type  = plan.get("hero_type", "centered_statement")
    layout_cls = hero_cfg.get("layout_class", "hero--centered")
    min_h      = hero_cfg.get("min_height", "72vh")
    text_pos   = hero_cfg.get("text_position", "center")
    has_image  = hero_cfg.get("has_image", False)
    brand      = ctx.get("brand_name", ctx.get("project_name", "Brand"))
    tagline    = ctx.get("tagline", "Une nouvelle vision du possible.")

    align_cls  = "text-center" if text_pos == "center" else "text-left"

    image_block = ""
    if has_image:
        image_block = f"""
  <div class="hero__media">
    <div class="hero__image-placeholder" style="background:var(--color-surface);aspect-ratio:4/3;border-radius:var(--radius-lg);display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;">
      Image principale
    </div>
  </div>"""

    layout_inner = "display:flex;align-items:center;gap:4rem;" if has_image else "display:flex;flex-direction:column;align-items:center;justify-content:center;"

    return f"""<section
  data-section-type="hero"
  data-section-index="{idx}"
  data-hero-type="{hero_type}"
  class="hero {layout_cls}"
  style="min-height:{min_h};background:var(--color-bg);"
>
  <div class="container">
    <div class="hero__inner {align_cls}" style="{layout_inner}">
      <div class="hero__content" style="flex:1;">
        <span class="tag tag--accent" style="margin-bottom:1.5rem;">Nouveau</span>
        <h1 style="font-size:clamp(2.5rem,5vw,4.5rem);font-weight:900;margin-bottom:1.5rem;line-height:1.05;">{brand}</h1>
        <p style="font-size:1.25rem;color:var(--color-muted);max-width:560px;margin-bottom:2.5rem;line-height:1.6;">{tagline}</p>
        <div style="display:flex;gap:1rem;flex-wrap:wrap;{('justify-content:center;' if text_pos=='center' else '')}">
          <a href="#contact" class="btn btn--primary">Commencer</a>
          <a href="#features" class="btn btn--outline">En savoir plus</a>
        </div>
      </div>{image_block}
    </div>
  </div>
</section>"""


def _b_editorial_narrative(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="editorial_narrative" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container--narrow">
    <p style="font-size:1.15rem;line-height:1.9;color:var(--color-muted);font-style:italic;border-left:3px solid var(--color-accent);padding-left:1.5rem;">
      Nous croyons que chaque détail compte. Notre approche repose sur une conviction simple : l'excellence n'est pas un accident. Elle est le résultat d'un travail minutieux, d'une attention constante et d'une passion qui ne s'éteint jamais.
    </p>
    <p style="font-size:1.05rem;line-height:1.8;margin-top:1.5rem;color:var(--color-text);">
      Depuis notre fondation, nous avons accompagné des centaines de projets avec la même exigence. Chaque collaboration est unique, chaque résultat est pensé pour durer.
    </p>
  </div>
</section>"""


def _b_visual_break(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="visual_break" data-section-index="{idx}" style="padding:3rem 0;background:var(--color-primary);">
  <div class="container">
    <div style="height:2px;background:linear-gradient(90deg,transparent,var(--color-accent),transparent);"></div>
    <p style="text-align:center;color:var(--color-bg);font-family:var(--font-heading);font-size:1.1rem;font-weight:600;margin-top:2rem;letter-spacing:0.1em;text-transform:uppercase;opacity:0.9;">
      Excellence · Précision · Impact
    </p>
  </div>
</section>"""


def _b_feature_split(idx: int, ctx: dict, plan: dict) -> str:
    is_even = idx % 2 == 0
    order_a = "order:1;" if is_even else "order:2;"
    order_b = "order:2;" if is_even else "order:1;"
    return f"""<section data-section-type="feature_split" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-{'surface' if is_even else 'bg'});">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;">
      <div style="{order_a}">
        <span class="tag" style="margin-bottom:1rem;">Fonctionnalité clé</span>
        <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:800;margin-bottom:1.5rem;">
          Une approche différente, des résultats prouvés
        </h2>
        <p style="font-size:1.05rem;line-height:1.7;color:var(--color-muted);margin-bottom:2rem;">
          Nous avons repensé chaque étape du processus pour vous offrir une expérience fluide et des résultats mesurables. Notre méthode éprouvée s'adapte à votre contexte.
        </p>
        <a href="#" class="btn btn--primary">Découvrir →</a>
      </div>
      <div style="{order_b}">
        <div style="background:var(--color-surface);border-radius:var(--radius-lg);aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">
          Visuel illustratif
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_quote_pull(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="quote_pull" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-primary);">
  <div class="container--narrow" style="text-align:center;">
    <p style="font-size:clamp(1.4rem,2.5vw,2rem);font-family:var(--font-heading);font-weight:700;color:var(--color-bg);line-height:1.4;margin-bottom:1.5rem;">
      « Le design n'est pas seulement ce à quoi une chose ressemble. Le design, c'est comment ça fonctionne. »
    </p>
    <p style="color:color-mix(in srgb,var(--color-bg) 70%,transparent);font-size:0.9rem;letter-spacing:0.05em;text-transform:uppercase;font-weight:600;">
      — Principe fondateur
    </p>
  </div>
</section>"""


def _b_spread_feature(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="spread_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container--wide">
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:3rem;align-items:start;">
      <div>
        <h2 style="font-size:clamp(2rem,4vw,3.5rem);font-weight:900;margin-bottom:1.5rem;line-height:1.1;">
          L'excellence comme standard, pas comme exception
        </h2>
        <p style="font-size:1.1rem;line-height:1.8;color:var(--color-muted);">
          Notre engagement dépasse la simple livraison. Nous construisons des solutions qui s'inscrivent dans la durée, qui évoluent avec vos besoins et qui portent votre vision au-delà de vos attentes initiales.
        </p>
      </div>
      <div style="padding-top:1rem;">
        <div style="background:var(--color-accent);color:var(--color-bg);padding:2rem;border-radius:var(--radius-lg);">
          <div style="font-size:3rem;font-weight:900;line-height:1;">98%</div>
          <div style="font-size:0.9rem;margin-top:0.5rem;opacity:0.9;">de clients satisfaits sur 5 ans</div>
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_column_narrative(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="column_narrative" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div class="grid-3">
      <div>
        <h3 style="font-size:1.3rem;font-weight:700;margin-bottom:1rem;">Vision</h3>
        <p style="color:var(--color-muted);line-height:1.7;">Nous croyons en un futur où la technologie amplifie le potentiel humain sans jamais le remplacer. Chaque outil que nous créons porte cette conviction.</p>
      </div>
      <div>
        <h3 style="font-size:1.3rem;font-weight:700;margin-bottom:1rem;">Mission</h3>
        <p style="color:var(--color-muted);line-height:1.7;">Rendre accessible ce qui était réservé aux grandes organisations. Démocratiser l'excellence, un projet à la fois, une équipe à la fois.</p>
      </div>
      <div>
        <h3 style="font-size:1.3rem;font-weight:700;margin-bottom:1rem;">Valeurs</h3>
        <p style="color:var(--color-muted);line-height:1.7;">Transparence radicale, exigence bienveillante, impact mesurable. Nous ne promettons que ce que nous pouvons tenir, et nous tenons tout ce que nous promettons.</p>
      </div>
    </div>
  </div>
</section>"""


def _b_visual_interrupt(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="visual_interrupt" data-section-index="{idx}" style="padding:0;background:var(--color-primary);overflow:hidden;">
  <div style="height:320px;background:linear-gradient(135deg,var(--color-primary),var(--color-secondary));display:flex;align-items:center;justify-content:center;">
    <div style="text-align:center;color:var(--color-bg);">
      <div style="font-size:0.8rem;letter-spacing:0.2em;text-transform:uppercase;font-weight:600;margin-bottom:1rem;opacity:0.7;">Notre approche</div>
      <div style="font-size:clamp(1.8rem,4vw,3rem);font-family:var(--font-heading);font-weight:900;line-height:1.2;">
        Simple. Puissant. Durable.
      </div>
    </div>
  </div>
</section>"""


def _b_byline_block(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="byline_block" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container--narrow">
    <div style="display:flex;gap:2rem;align-items:center;padding:2rem;background:var(--color-surface);border-radius:var(--radius-lg);border-left:4px solid var(--color-accent);">
      <div style="width:60px;height:60px;border-radius:50%;background:var(--color-primary);flex-shrink:0;display:flex;align-items:center;justify-content:center;color:var(--color-bg);font-weight:800;font-size:1.4rem;">E</div>
      <div>
        <div style="font-weight:700;margin-bottom:0.25rem;">Équipe éditoriale</div>
        <div style="color:var(--color-muted);font-size:0.9rem;line-height:1.6;">
          Notre équipe de spécialistes combine expertise technique et sens créatif pour vous livrer des résultats au-delà de vos attentes.
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_chapter_opener(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="chapter_opener" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);border-top:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">
  <div class="container--narrow">
    <div style="display:flex;align-items:baseline;gap:1.5rem;margin-bottom:1.5rem;">
      <span style="font-size:4rem;font-weight:900;color:var(--color-accent);line-height:1;font-family:var(--font-heading);">01</span>
      <div>
        <div style="font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--color-muted);font-weight:600;margin-bottom:0.4rem;">Chapitre premier</div>
        <h2 style="font-size:2rem;font-weight:800;">Le commencement de tout</h2>
      </div>
    </div>
    <p style="font-size:1.1rem;line-height:1.8;color:var(--color-muted);">
      Chaque grande histoire commence par une décision. Celle de ne pas se contenter du possible, mais de s'emparer de l'impossible. C'est ici que tout commence.
    </p>
  </div>
</section>"""


def _b_narrative_text(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="narrative_text" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container--narrow">
    <p style="font-size:1.15rem;line-height:1.9;color:var(--color-text);">
      Nous avons construit notre réputation sur une promesse simple : livrer ce que nous annonçons, quand nous l'annonçons, à la qualité attendue. Dans un secteur où les promesses sont nombreuses et les résultats rares, nous avons choisi la voie de l'exigence.
    </p>
    <p style="font-size:1.05rem;line-height:1.8;color:var(--color-muted);margin-top:1.5rem;">
      Notre méthode s'est affinée au fil de dizaines de projets, de centaines d'heures de collaboration, et d'une obsession constante pour ce qui fonctionne vraiment — pas ce qui semble impressionnant sur le papier.
    </p>
  </div>
</section>"""


def _b_visual_pause(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="visual_pause" data-section-index="{idx}" style="padding:4rem 0;background:var(--color-bg);">
  <div class="container">
    <div style="height:1px;background:color-mix(in srgb,var(--color-text) 12%,transparent);"></div>
    <div style="display:flex;justify-content:center;margin-top:-1rem;">
      <div style="background:var(--color-bg);padding:0 1.5rem;">
        <div style="width:8px;height:8px;border-radius:50%;background:var(--color-accent);display:inline-block;"></div>
        <div style="width:8px;height:8px;border-radius:50%;background:var(--color-accent);display:inline-block;margin:0 0.5rem;opacity:0.5;"></div>
        <div style="width:8px;height:8px;border-radius:50%;background:var(--color-accent);display:inline-block;opacity:0.25;"></div>
      </div>
    </div>
  </div>
</section>"""


def _b_feature_list(idx: int, ctx: dict, plan: dict) -> str:
    items = [
        ("Performance", "Résultats mesurables dès les premières semaines."),
        ("Fiabilité", "Architecture éprouvée, zéro compromis sur la stabilité."),
        ("Support", "Équipe dédiée, réponse en moins de 4h ouvrées."),
        ("Évolutivité", "Conçu pour grandir avec vous, sans refonte."),
    ]
    items_html = "".join(
        f'<div style="display:flex;gap:1.5rem;align-items:start;padding:1.5rem 0;border-bottom:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">'
        f'<div style="width:36px;height:36px;border-radius:50%;background:var(--color-accent);display:flex;align-items:center;justify-content:center;flex-shrink:0;">✓</div>'
        f'<div><strong style="display:block;margin-bottom:0.25rem;">{t}</strong><span style="color:var(--color-muted);font-size:0.95rem;">{d}</span></div></div>'
        for t, d in items
    )
    return f"""<section data-section-type="feature_list" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <h2 style="font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;margin-bottom:2.5rem;text-align:center;">Ce qui nous distingue</h2>
    <div class="container--narrow" style="padding:0;">{items_html}</div>
  </div>
</section>"""


def _b_feature_offset(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="feature_offset" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center;">
      <div style="transform:translateY(2rem);">
        <div style="background:var(--color-bg);padding:3rem;border-radius:var(--radius-lg);box-shadow:0 20px 60px -10px rgba(0,0,0,0.12);">
          <h2 style="font-size:2rem;font-weight:800;margin-bottom:1.5rem;line-height:1.2;">Décalé par design, précis par nature</h2>
          <p style="color:var(--color-muted);line-height:1.7;margin-bottom:2rem;">Notre approche asymétrique n'est pas un accident esthétique. C'est une conviction : les meilleures solutions émergent quand on ose sortir des schémas attendus.</p>
          <a href="#" class="btn btn--primary">Explorer →</a>
        </div>
      </div>
      <div>
        <div style="background:var(--color-primary);border-radius:var(--radius-lg);aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;color:var(--color-bg);font-size:0.85rem;opacity:0.8;">
          Visuel de feature
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_narrative_block(idx: int, ctx: dict, plan: dict) -> str:
    return _b_narrative_text(idx, ctx, plan)


def _b_visual_contrast(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="visual_contrast" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-text);color:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;">
      <div>
        <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:900;color:var(--color-bg);margin-bottom:1.5rem;line-height:1.1;">Contraste voulu. Impact immédiat.</h2>
        <p style="color:color-mix(in srgb,var(--color-bg) 70%,transparent);line-height:1.7;">
          Quand tout le monde parle, seuls ceux qui osent le contraste sont entendus. Notre positionnement est clair, assumé, et conçu pour marquer les esprits.
        </p>
      </div>
      <div>
        <div style="background:var(--color-accent);padding:2.5rem;border-radius:var(--radius-lg);">
          <div style="font-size:3.5rem;font-weight:900;color:var(--color-bg);line-height:1;">+240%</div>
          <div style="color:var(--color-bg);margin-top:0.5rem;font-size:1rem;opacity:0.9;">d'impact moyen sur les campagnes accompagnées</div>
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_staggered_feature(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="staggered_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;">
      <div style="padding:2rem;background:var(--color-surface);border-radius:var(--radius-lg);margin-top:0;">
        <div style="font-size:2rem;margin-bottom:1rem;">⚡</div>
        <h3 style="font-size:1.2rem;font-weight:700;margin-bottom:0.75rem;">Rapidité</h3>
        <p style="color:var(--color-muted);font-size:0.95rem;line-height:1.6;">Déploiement en heures, pas en semaines. Notre infrastructure cloud-native garantit une mise en production ultra-rapide.</p>
      </div>
      <div style="padding:2rem;background:var(--color-primary);border-radius:var(--radius-lg);margin-top:2rem;">
        <div style="font-size:2rem;margin-bottom:1rem;">🎯</div>
        <h3 style="font-size:1.2rem;font-weight:700;margin-bottom:0.75rem;color:var(--color-bg);">Précision</h3>
        <p style="color:color-mix(in srgb,var(--color-bg) 80%,transparent);font-size:0.95rem;line-height:1.6;">Chaque feature répond à un besoin réel, validé par données. Pas de fonctionnalités superflues, que de l'essentiel.</p>
      </div>
      <div style="padding:2rem;background:var(--color-surface);border-radius:var(--radius-lg);margin-top:4rem;">
        <div style="font-size:2rem;margin-bottom:1rem;">🔒</div>
        <h3 style="font-size:1.2rem;font-weight:700;margin-bottom:0.75rem;">Sécurité</h3>
        <p style="color:var(--color-muted);font-size:0.95rem;line-height:1.6;">Conformité RGPD, chiffrement de bout en bout, audits réguliers. Votre confiance est notre première priorité.</p>
      </div>
    </div>
  </div>
</section>"""


def _b_data_strip(idx: int, ctx: dict, plan: dict) -> str:
    stats = [("500+", "Projets livrés"), ("98%", "Taux de satisfaction"), ("4h", "Temps de réponse"), ("12", "Pays couverts")]
    items = "".join(
        f'<div style="text-align:center;padding:1.5rem;">'
        f'<div style="font-size:2.5rem;font-weight:900;color:var(--color-accent);font-family:var(--font-heading);">{v}</div>'
        f'<div style="color:var(--color-muted);font-size:0.85rem;margin-top:0.4rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">{l}</div>'
        f'</div>'
        for v, l in stats
    )
    return f"""<section data-section-type="data_strip" data-section-index="{idx}" style="padding:3rem 0;background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">{items}</div>
  </div>
</section>"""


def _b_offset_visual(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="offset_visual" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);overflow:hidden;">
  <div class="container">
    <div style="display:grid;grid-template-columns:5fr 7fr;gap:3rem;align-items:center;">
      <div>
        <span class="tag" style="margin-bottom:1rem;">Produit</span>
        <h2 style="font-size:2rem;font-weight:800;margin-bottom:1.5rem;line-height:1.2;">Visualisez. Créez. Dominez.</h2>
        <p style="color:var(--color-muted);line-height:1.7;">Un outil conçu pour les équipes qui refusent de se limiter. Interface intuitive, puissance professionnelle.</p>
      </div>
      <div style="position:relative;">
        <div style="background:var(--color-surface);border-radius:var(--radius-lg);aspect-ratio:16/10;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;">
          Capture d'écran produit
        </div>
        <div style="position:absolute;bottom:-1.5rem;right:-1.5rem;background:var(--color-accent);color:var(--color-bg);padding:1rem 1.5rem;border-radius:var(--radius-md);font-weight:700;font-size:0.9rem;">
          v3.0 disponible
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_asymmetric_grid(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="asymmetric_grid" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <h2 style="font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;margin-bottom:2.5rem;">Notre portfolio</h2>
    <div style="display:grid;grid-template-columns:2fr 1fr;grid-template-rows:auto auto;gap:1.5rem;">
      <div style="grid-row:1/3;background:var(--color-primary);border-radius:var(--radius-lg);min-height:300px;display:flex;align-items:end;padding:2rem;">
        <div style="color:var(--color-bg);"><div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;opacity:0.7;margin-bottom:0.5rem;">Projet phare</div><strong style="font-size:1.2rem;">Transformation numérique — Secteur santé</strong></div>
      </div>
      <div style="background:var(--color-accent);border-radius:var(--radius-lg);min-height:140px;display:flex;align-items:end;padding:1.5rem;">
        <div style="color:var(--color-bg);font-size:0.9rem;font-weight:600;">Stratégie de marque</div>
      </div>
      <div style="background:var(--color-bg);border:1px solid color-mix(in srgb,var(--color-text) 10%,transparent);border-radius:var(--radius-lg);min-height:140px;display:flex;align-items:end;padding:1.5rem;">
        <div style="font-size:0.9rem;font-weight:600;">Système design</div>
      </div>
    </div>
  </div>
</section>"""


def _b_module_cluster(idx: int, ctx: dict, plan: dict) -> str:
    modules = [
        ("Analytics", "Tableaux de bord en temps réel"),
        ("Automatisation", "Workflows sans code"),
        ("Intégrations", "200+ connecteurs natifs"),
        ("Rapports", "Export multi-format"),
        ("API", "REST & GraphQL"),
        ("Support", "Chat 24/7"),
    ]
    items = "".join(
        f'<div style="background:var(--color-surface);padding:1.5rem;border-radius:var(--radius-md);border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">'
        f'<strong style="display:block;margin-bottom:0.5rem;font-size:1rem;">{n}</strong>'
        f'<span style="color:var(--color-muted);font-size:0.875rem;">{d}</span></div>'
        for n, d in modules
    )
    return f"""<section data-section-type="module_cluster" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <h2 style="font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;text-align:center;margin-bottom:2.5rem;">Tout ce qu'il vous faut, intégré</h2>
    <div class="grid-3">{items}</div>
  </div>
</section>"""


def _b_stat_row(idx: int, ctx: dict, plan: dict) -> str:
    return _b_data_strip(idx, ctx, plan)


def _b_visual_module(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="visual_module" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container--wide">
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
      {"".join(f'<div style="background:var(--color-surface);border-radius:var(--radius-md);aspect-ratio:1;display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">Image {i+1}</div>' for i in range(4))}
    </div>
  </div>
</section>"""


def _b_feature_tiles(idx: int, ctx: dict, plan: dict) -> str:
    return _b_module_cluster(idx, ctx, plan)


def _b_data_wall(idx: int, ctx: dict, plan: dict) -> str:
    _data = [
        ("3.2M",    "Données traitées/jour"),
        ("99.9%",   "Uptime garanti"),
        ("0.8s",    "Temps de réponse moyen"),
        ("ISO 27001", "Certification sécurité"),
        ("RGPD",    "Conformité totale"),
        ("SOC 2",   "Audit Type II"),
    ]
    cs = "padding:2.5rem;border-right:1px solid rgba(255,255,255,0.1);border-bottom:1px solid rgba(255,255,255,0.1);"
    cells_parts = []
    for i, (v, l) in enumerate(_data):
        if i < 3:
            inner = f'<div style="font-size:3rem;font-weight:900;color:var(--color-accent);">{v}</div><div style="margin-top:0.5rem;color:rgba(255,255,255,0.6);font-size:0.85rem;text-transform:uppercase;">{l}</div>'
        else:
            inner = f'<div style="font-size:1.1rem;font-weight:700;">{l}</div>'
        cells_parts.append(f'<div style="{cs}">{inner}</div>')
    cells = "".join(cells_parts)
    sec = f'data-section-type="data_wall" data-section-index="{idx}"'
    style = "padding:var(--section-padding);background:var(--color-text);color:var(--color-bg);"
    return f'<section {sec} style="{style}"><div class="container"><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid rgba(255,255,255,0.1);">{cells}</div></div></section>'


def _b_brutal_text_block(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="brutal_text_block" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);border-top:3px solid var(--color-text);border-bottom:3px solid var(--color-text);">
  <div class="container">
    <p style="font-size:clamp(2rem,5vw,4rem);font-weight:900;font-family:var(--font-heading);line-height:1;text-transform:uppercase;letter-spacing:-0.03em;">
      NOUS NE FAISONS PAS DANS LA DEMI-MESURE.
    </p>
    <p style="font-size:clamp(1rem,2vw,1.5rem);margin-top:1.5rem;color:var(--color-muted);max-width:600px;">
      Notre approche est directe, nos résultats sont documentés, nos clients restent. C'est aussi simple que ça.
    </p>
  </div>
</section>"""


def _b_raw_visual(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="raw_visual" data-section-index="{idx}" style="padding:0;background:var(--color-text);">
  <div style="height:280px;display:flex;align-items:stretch;">
    <div style="flex:1;background:var(--color-accent);"></div>
    <div style="flex:2;display:flex;align-items:center;justify-content:center;padding:3rem;">
      <p style="color:var(--color-bg);font-size:1.5rem;font-weight:700;line-height:1.4;font-family:var(--font-heading);">
        « Des chiffres qui parlent. Des résultats qui convainquent. »
      </p>
    </div>
  </div>
</section>"""


def _b_layer_reveal(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="layer_reveal" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);position:relative;overflow:hidden;">
  <div style="position:absolute;top:-40px;right:-40px;width:400px;height:400px;background:var(--color-surface);border-radius:50%;opacity:0.5;"></div>
  <div class="container" style="position:relative;z-index:1;">
    <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:800;margin-bottom:1.5rem;">Couche après couche, la vérité se révèle</h2>
    <p style="font-size:1.1rem;color:var(--color-muted);line-height:1.7;max-width:600px;margin-bottom:2.5rem;">
      Notre méthode de travail procède par strates successives. Chaque couche affine la précédente, jusqu'à atteindre une clarté absolue sur votre projet.
    </p>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;">
      <div style="background:var(--color-surface);padding:1rem 1.5rem;border-radius:var(--radius-md);border:1px solid color-mix(in srgb,var(--color-text) 10%,transparent);">Analyse</div>
      <div style="background:var(--color-surface);padding:1rem 1.5rem;border-radius:var(--radius-md);border:1px solid color-mix(in srgb,var(--color-text) 10%,transparent);">Conception</div>
      <div style="background:var(--color-accent);color:var(--color-bg);padding:1rem 1.5rem;border-radius:var(--radius-md);">Livraison</div>
    </div>
  </div>
</section>"""


def _b_depth_feature(idx: int, ctx: dict, plan: dict) -> str:
    return _b_feature_split(idx, ctx, plan)


def _b_overlap_narrative(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="overlap_narrative" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container--narrow">
    <div style="background:var(--color-bg);padding:3rem;border-radius:var(--radius-lg);box-shadow:0 25px 50px -12px rgba(0,0,0,0.1);margin-top:-3rem;">
      <h2 style="font-size:1.8rem;font-weight:800;margin-bottom:1.5rem;">Le détail qui change tout</h2>
      <p style="color:var(--color-muted);line-height:1.8;font-size:1.05rem;">
        Dans chaque projet que nous livrons, il y a un moment où tout s'assemble. Un détail qui transforme le bon en excellent, le fonctionnel en mémorable. C'est ce moment que nous cherchons systématiquement à créer pour vous.
      </p>
    </div>
  </div>
</section>"""


def _b_floating_cta(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="floating_cta" data-section-index="{idx}" style="padding:2rem var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="background:var(--color-primary);border-radius:var(--radius-lg);padding:2.5rem 3rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:2rem;">
      <div style="color:var(--color-bg);">
        <h3 style="font-size:1.4rem;font-weight:800;margin-bottom:0.5rem;">Prêt à démarrer ?</h3>
        <p style="opacity:0.85;font-size:0.95rem;">Rejoignez les équipes qui ont déjà fait le choix de l'excellence.</p>
      </div>
      <a href="#contact" class="btn" style="background:var(--color-bg);color:var(--color-primary);">Commencer maintenant</a>
    </div>
  </div>
</section>"""


def _b_diagonal_feature(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="diagonal_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;right:0;width:50%;height:100%;background:var(--color-primary);clip-path:polygon(20% 0%,100% 0%,100% 100%,0% 100%);"></div>
  <div class="container" style="position:relative;z-index:1;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center;">
      <div>
        <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:900;margin-bottom:1.5rem;line-height:1.1;">La diagonale comme signature</h2>
        <p style="color:var(--color-muted);line-height:1.7;margin-bottom:2rem;">
          Notre positionnement est intentionnellement oblique. Là où les autres vont droit, nous choisissons l'angle qui crée la surprise et retient l'attention.
        </p>
        <a href="#" class="btn btn--primary">Voir notre méthode</a>
      </div>
      <div style="color:var(--color-bg);padding:2rem;">
        <h3 style="font-size:1.5rem;font-weight:700;margin-bottom:1rem;">Approche unique</h3>
        <p style="opacity:0.85;line-height:1.7;">Nous combinons créativité radicale et rigueur analytique pour créer des solutions qui ne ressemblent à rien d'autre sur le marché.</p>
      </div>
    </div>
  </div>
</section>"""


def _b_tension_visual(idx: int, ctx: dict, plan: dict) -> str:
    return _b_visual_contrast(idx, ctx, plan)


def _b_oblique_narrative(idx: int, ctx: dict, plan: dict) -> str:
    return _b_narrative_text(idx, ctx, plan)


def _b_contrast_block(idx: int, ctx: dict, plan: dict) -> str:
    return _b_visual_contrast(idx, ctx, plan)


def _b_manifesto_strip(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="manifesto_strip" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-text);color:var(--color-bg);">
  <div class="container--narrow" style="text-align:center;">
    <p style="font-size:clamp(1.2rem,2.5vw,1.8rem);font-family:var(--font-heading);font-weight:700;line-height:1.5;max-width:700px;margin:0 auto;">
      Nous sommes convaincus que les meilleures idées naissent à la frontière du possible et de l'impossible. C'est là que nous travaillons. C'est là que vous trouverez votre prochain avantage compétitif.
    </p>
  </div>
</section>"""


def _b_stat_centered(idx: int, ctx: dict, plan: dict) -> str:
    stats = [("500+", "Projets"), ("98%", "Satisfaction"), ("4h", "Réponse")]
    items = "".join(
        f'<div style="text-align:center;"><div style="font-size:3rem;font-weight:900;font-family:var(--font-heading);color:var(--color-primary);">{v}</div><div style="color:var(--color-muted);font-size:0.85rem;margin-top:0.25rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">{l}</div></div>'
        for v, l in stats
    )
    return f"""<section data-section-type="stat_centered" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container--narrow">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:3rem;">{items}</div>
  </div>
</section>"""


def _b_feature_centered(idx: int, ctx: dict, plan: dict) -> str:
    features = [("Vision", "Anticiper les tendances, pas les suivre."), ("Méthode", "Processus éprouvés, résultats documentés."), ("Impact", "Mesurable, immédiat, durable.")]
    items = "".join(
        f'<div style="text-align:center;padding:2rem;"><h3 style="font-size:1.2rem;font-weight:700;margin-bottom:0.75rem;">{n}</h3><p style="color:var(--color-muted);font-size:0.95rem;line-height:1.6;">{d}</p></div>'
        for n, d in features
    )
    return f"""<section data-section-type="feature_centered" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <h2 style="font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;text-align:center;margin-bottom:3rem;">Trois piliers. Un seul but.</h2>
    <div class="grid-3">{items}</div>
  </div>
</section>"""


def _b_quote_centered(idx: int, ctx: dict, plan: dict) -> str:
    return _b_quote_pull(idx, ctx, plan)


def _b_anchor_statement(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="anchor_statement" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container--narrow" style="text-align:center;">
    <h2 style="font-size:clamp(2rem,4vw,3rem);font-weight:900;margin-bottom:1.5rem;line-height:1.1;">
      La question n'est pas si vous devez changer.<br>C'est quand vous commencez.
    </h2>
    <a href="#contact" class="btn btn--primary" style="font-size:1.1rem;padding:1rem 2.5rem;">Démarrer maintenant</a>
  </div>
</section>"""


def _b_feature_compact(idx: int, ctx: dict, plan: dict) -> str:
    features = [("✓ Setup en 1 jour", "Configuration guidée, onboarding inclus"), ("✓ ROI en 30 jours", "Garantie résultats ou remboursement"), ("✓ Support dédié", "Équipe disponible 7j/7")]
    items = "".join(
        f'<div style="display:flex;gap:1rem;align-items:start;padding:1rem 0;"><div><strong style="display:block;font-size:0.95rem;margin-bottom:0.25rem;">{t}</strong><span style="color:var(--color-muted);font-size:0.875rem;">{d}</span></div></div>'
        for t, d in features
    )
    return f"""<section data-section-type="feature_compact" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container--narrow">{items}</div>
</section>"""


def _b_social_proof(idx: int, ctx: dict, plan: dict) -> str:
    reviews = [
        ("Sarah M.", "Directrice Innovation", "Une transformation complète de notre process en 3 semaines. Résultats au-delà de nos espérances."),
        ("Thomas B.", "CEO, Startup Series A", "La meilleure décision de l'année. ROI atteint dès le premier mois."),
        ("Elena K.", "CTO", "L'équipe la plus compétente avec qui j'ai eu la chance de travailler."),
    ]
    items = "".join(
        f'<div style="background:var(--color-bg);padding:2rem;border-radius:var(--radius-lg);border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">'
        f'<p style="color:var(--color-muted);font-style:italic;line-height:1.7;margin-bottom:1.5rem;">« {t} »</p>'
        f'<div style="display:flex;align-items:center;gap:1rem;">'
        f'<div style="width:40px;height:40px;border-radius:50%;background:var(--color-primary);display:flex;align-items:center;justify-content:center;color:var(--color-bg);font-weight:700;">{n[0]}</div>'
        f'<div><strong style="display:block;font-size:0.9rem;">{n}</strong><span style="color:var(--color-muted);font-size:0.8rem;">{r}</span></div>'
        f'</div></div>'
        for n, r, t in reviews
    )
    return f"""<section data-section-type="social_proof" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <h2 style="font-size:clamp(1.6rem,3vw,2.4rem);font-weight:800;text-align:center;margin-bottom:2.5rem;">Ce qu'ils en disent</h2>
    <div class="grid-3">{items}</div>
  </div>
</section>"""


def _b_zigzag_left(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="zigzag_left" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;">
      <div>
        <span class="tag" style="margin-bottom:1rem;">Étape {(idx)//2 + 1}</span>
        <h2 style="font-size:2rem;font-weight:800;margin-bottom:1.5rem;line-height:1.2;">Analyse et compréhension de votre contexte</h2>
        <p style="color:var(--color-muted);line-height:1.7;margin-bottom:2rem;">Nous commençons par une écoute active. Votre secteur, vos contraintes, vos ambitions — tout est pris en compte avant d'écrire la première ligne de solution.</p>
        <a href="#" style="color:var(--color-primary);font-weight:600;">En savoir plus →</a>
      </div>
      <div style="background:var(--color-surface);border-radius:var(--radius-lg);aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">
        Illustration
      </div>
    </div>
  </div>
</section>"""


def _b_zigzag_right(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="zigzag_right" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;">
      <div style="order:2;">
        <span class="tag" style="margin-bottom:1rem;">Étape {(idx)//2 + 1}</span>
        <h2 style="font-size:2rem;font-weight:800;margin-bottom:1.5rem;line-height:1.2;">Conception et prototypage rapide</h2>
        <p style="color:var(--color-muted);line-height:1.7;margin-bottom:2rem;">En 48h, vous avez un prototype fonctionnel. En 1 semaine, une version testée et validée. Notre cycle court élimine les surprises et accélère votre mise sur le marché.</p>
        <a href="#" style="color:var(--color-primary);font-weight:600;">Voir le process →</a>
      </div>
      <div style="order:1;background:var(--color-bg);border-radius:var(--radius-lg);aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;color:var(--color-muted);font-size:0.85rem;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">
        Illustration
      </div>
    </div>
  </div>
</section>"""


def _b_whitespace_text(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="whitespace_text" data-section-index="{idx}" style="padding:8rem 0;background:var(--color-bg);">
  <div class="container--narrow" style="text-align:center;">
    <h2 style="font-size:clamp(1.8rem,3.5vw,3rem);font-weight:800;line-height:1.2;margin-bottom:2rem;letter-spacing:-0.02em;">
      Moins de bruit. Plus d'impact.
    </h2>
    <p style="font-size:1.15rem;color:var(--color-muted);line-height:1.8;max-width:520px;margin:0 auto;">
      Dans un monde saturé de messages, la clarté est le nouvel avantage compétitif. Nous aidons nos clients à distiller l'essentiel et à le communiquer avec précision.
    </p>
  </div>
</section>"""


def _b_single_feature(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="single_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:5rem;align-items:center;">
      <div style="text-align:center;">
        <div style="font-size:5rem;font-weight:900;color:var(--color-primary);font-family:var(--font-heading);line-height:1;">01</div>
        <div style="width:60px;height:2px;background:var(--color-accent);margin:1rem auto 0;"></div>
      </div>
      <div>
        <h2 style="font-size:2rem;font-weight:800;margin-bottom:1.5rem;">La fonctionnalité qui change tout</h2>
        <p style="color:var(--color-muted);line-height:1.7;font-size:1.05rem;">
          Une seule fonctionnalité, pensée jusqu'au moindre détail, peut transformer radicalement votre productivité. C'est notre philosophie : plutôt un outil parfait que dix outils médiocres.
        </p>
      </div>
    </div>
  </div>
</section>"""


def _b_filmstrip_band(idx: int, ctx: dict, plan: dict) -> str:
    band_bg = ["var(--color-primary)", "var(--color-text)", "var(--color-surface)"][idx % 3]
    band_color = "var(--color-bg)" if idx % 3 < 2 else "var(--color-text)"
    titles = ["Analyser", "Concevoir", "Livrer", "Évoluer"]
    title = titles[idx % len(titles)]
    return f"""<section data-section-type="filmstrip_band" data-section-index="{idx}" style="padding:5rem 0;background:{band_bg};color:{band_color};">
  <div class="container--wide">
    <div style="display:flex;align-items:center;gap:3rem;">
      <div style="flex-shrink:0;font-size:5rem;font-weight:900;font-family:var(--font-heading);opacity:0.3;line-height:1;">{str(idx).zfill(2)}</div>
      <div style="flex:1;">
        <h2 style="font-size:clamp(2rem,4vw,3rem);font-weight:900;line-height:1;text-transform:uppercase;letter-spacing:-0.02em;">{title}</h2>
        <p style="opacity:0.7;margin-top:1rem;font-size:1.05rem;max-width:560px;line-height:1.6;">
          {'Chaque étape de notre processus est calibrée pour maximiser la valeur délivrée et minimiser le temps perdu. Nous avançons ensemble, vite et bien.'}
        </p>
      </div>
      <div style="flex-shrink:0;width:200px;height:120px;background:rgba(255,255,255,0.1);border-radius:var(--radius-md);display:flex;align-items:center;justify-content:center;font-size:0.8rem;opacity:0.5;">
        Image {idx}
      </div>
    </div>
  </div>
</section>"""


def _b_mosaic_header(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="mosaic_header" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:800;margin-bottom:0.75rem;">Explorez notre univers</h2>
    <p style="color:var(--color-muted);font-size:1.05rem;max-width:560px;margin-bottom:2.5rem;line-height:1.6;">Une collection de travaux qui témoignent de notre engagement pour l'excellence et la créativité.</p>
  </div>
</section>"""


def _b_mosaic_grid(idx: int, ctx: dict, plan: dict) -> str:
    colors = ["var(--color-primary)", "var(--color-accent)", "var(--color-surface)", "var(--color-text)", "var(--color-secondary)"]
    heights = ["200px", "280px", "180px", "250px", "220px", "300px"]
    cards = "".join(
        f'<div style="background:{colors[i%len(colors)]};border-radius:var(--radius-lg);height:{heights[i%len(heights)]};display:flex;align-items:end;padding:1.5rem;overflow:hidden;">'
        f'<div style="color:var(--color-bg) if {i%len(colors)} in [0,1,3,4] else var(--color-text);font-weight:600;font-size:0.9rem;">Projet {i+1}</div>'
        f'</div>'
        for i in range(6)
    )
    return f"""<section data-section-type="mosaic_grid" data-section-index="{idx}" style="padding:2rem 0 var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;">{cards}</div>
  </div>
</section>"""


def _b_poster_statement(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="poster_statement" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <p style="font-size:clamp(3rem,8vw,7rem);font-weight:900;font-family:var(--font-heading);line-height:0.95;letter-spacing:-0.04em;text-transform:uppercase;color:var(--color-text);">
      L'AVENIR<br>APPARTIENT<br><span style="color:var(--color-accent);">À CEUX</span><br>QUI OSENT.
    </p>
  </div>
</section>"""


def _b_type_hierarchy(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="type_hierarchy" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:3rem;align-items:start;">
      <div>
        <p style="font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--color-muted);font-weight:600;margin-bottom:0.5rem;">Notre promesse</p>
        <p style="font-size:2rem;font-weight:900;font-family:var(--font-heading);line-height:1.1;letter-spacing:-0.03em;">Excellence par défaut</p>
      </div>
      <div>
        <p style="font-size:1.1rem;line-height:1.8;color:var(--color-muted);">
          Ce que nous livrons n'est pas seulement fonctionnel — c'est exemplaire. Chaque pixel, chaque ligne de code, chaque interaction est pensée pour créer une expérience mémorable et efficace.
        </p>
        <p style="font-size:0.9rem;line-height:1.7;color:var(--color-muted);margin-top:1rem;">
          Notre processus de validation interne est plus exigeant que n'importe quel brief client. Parce que nous savons que la vraie valeur se cache dans les détails.
        </p>
      </div>
    </div>
  </div>
</section>"""


def _b_type_feature(idx: int, ctx: dict, plan: dict) -> str:
    items = [("01. ANALYSER", "Comprendre avant d'agir."), ("02. CONCEVOIR", "Élaborer avec soin."), ("03. LIVRER", "Livrer avec précision.")]
    items_html = "".join(
        f'<div style="padding:2rem 0;border-bottom:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);display:flex;justify-content:space-between;align-items:baseline;gap:2rem;">'
        f'<span style="font-size:1rem;font-weight:800;font-family:var(--font-heading);letter-spacing:0.05em;">{t}</span>'
        f'<span style="color:var(--color-muted);font-size:0.9rem;max-width:320px;text-align:right;">{d}</span></div>'
        for t, d in items
    )
    return f"""<section data-section-type="type_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">{items_html}</div>
</section>"""


def _b_sidebar_content(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="sidebar_content" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:240px 1fr;gap:4rem;align-items:start;">
      <div style="position:sticky;top:5rem;">
        <nav>
          <ul style="list-style:none;display:flex;flex-direction:column;gap:0.5rem;">
            {"".join(f'<li><a href="#section-{i}" style="display:block;padding:0.6rem 1rem;border-radius:var(--radius-sm);font-size:0.9rem;font-weight:500;color:var(--color-muted);border-left:2px solid {"var(--color-accent)" if i==0 else "transparent"};">{"→ " if i==0 else ""}{s}</a></li>' for i, s in enumerate(["Vue d'ensemble", "Fonctionnalités", "Cas d'usage", "Tarifs", "FAQ"]))}
          </ul>
        </nav>
      </div>
      <div>
        <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:800;margin-bottom:1.5rem;">Documentation complète</h2>
        <p style="color:var(--color-muted);line-height:1.7;font-size:1.05rem;">
          Notre plateforme est documentée dans les moindres détails. Chaque fonctionnalité est expliquée, chaque cas d'usage est illustré, chaque intégration est guidée.
        </p>
      </div>
    </div>
  </div>
</section>"""


def _b_sidebar_feature(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="sidebar_feature" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:240px 1fr;gap:4rem;">
      <div></div>
      <div>
        <h3 style="font-size:1.5rem;font-weight:700;margin-bottom:1.5rem;">Fonctionnalités avancées</h3>
        <div class="grid-2">
          {"".join(f'<div style="background:var(--color-bg);padding:1.5rem;border-radius:var(--radius-md);border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);"><strong style="display:block;margin-bottom:0.5rem;font-size:0.95rem;">{f}</strong><span style="color:var(--color-muted);font-size:0.85rem;">{d}</span></div>' for f, d in [("API First", "Intégration native REST/GraphQL"), ("Webhooks", "Notifications temps réel"), ("SSO", "Authentification centralisée"), ("Audit Log", "Traçabilité complète")])}
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_sidebar_stats(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="sidebar_stats" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-bg);">
  <div class="container">
    <div style="display:grid;grid-template-columns:240px 1fr;gap:4rem;">
      <div></div>
      <div>
        <h3 style="font-size:1.5rem;font-weight:700;margin-bottom:2rem;">Nos chiffres parlent</h3>
        <div class="grid-3">
          {"".join(f'<div style="text-align:center;padding:1.5rem;background:var(--color-surface);border-radius:var(--radius-md);"><div style="font-size:2.5rem;font-weight:900;color:var(--color-primary);font-family:var(--font-heading);">{v}</div><div style="color:var(--color-muted);font-size:0.8rem;margin-top:0.25rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">{l}</div></div>' for v, l in [("500+", "Projets"), ("98%", "Satisfaction"), ("4h", "Support")])}
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_sidebar_cta(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="sidebar_cta" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:240px 1fr;gap:4rem;">
      <div></div>
      <div style="background:var(--color-primary);padding:2.5rem;border-radius:var(--radius-lg);">
        <h3 style="font-size:1.4rem;font-weight:800;color:var(--color-bg);margin-bottom:1rem;">Commencer dès aujourd'hui</h3>
        <p style="color:color-mix(in srgb,var(--color-bg) 80%,transparent);margin-bottom:2rem;line-height:1.6;">14 jours d'essai gratuit, sans carte bancaire. Annulez quand vous voulez.</p>
        <a href="#contact" class="btn" style="background:var(--color-bg);color:var(--color-primary);">Essai gratuit →</a>
      </div>
    </div>
  </div>
</section>"""


def _b_data_showcase(idx: int, ctx: dict, plan: dict) -> str:
    return f"""<section data-section-type="data_showcase" data-section-index="{idx}" style="padding:var(--section-padding);background:var(--color-text);color:var(--color-bg);">
  <div class="container">
    <div style="text-align:center;margin-bottom:3rem;">
      <div style="font-size:clamp(4rem,10vw,8rem);font-weight:900;font-family:var(--font-heading);color:var(--color-accent);line-height:1;">3.2M</div>
      <div style="font-size:1.1rem;opacity:0.7;margin-top:0.5rem;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">Transactions traitées cette année</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2rem;border-top:1px solid rgba(255,255,255,0.1);padding-top:2.5rem;">
      {"".join(f'<div style="text-align:center;"><div style="font-size:1.8rem;font-weight:800;color:var(--color-accent);">{v}</div><div style="opacity:0.6;font-size:0.8rem;margin-top:0.25rem;text-transform:uppercase;letter-spacing:0.08em;">{l}</div></div>' for v, l in [("99.9%", "Uptime"), ("< 1s", "Latence"), ("ISO 27001", "Certifié"), ("RGPD", "Conforme")])}
    </div>
  </div>
</section>"""


def _b_stat_grid(idx: int, ctx: dict, plan: dict) -> str:
    return _b_data_strip(idx, ctx, plan)


def _b_data_narrative(idx: int, ctx: dict, plan: dict) -> str:
    _metrics = [
        ("Taux de conversion", "+34%"),
        ("Rétention 30j", "87%"),
        ("NPS Score", "72"),
        ("Churn mensuel", "< 2%"),
    ]
    rows = []
    for i, (m, v) in enumerate(_metrics):
        sep = "border-bottom:1px solid color-mix(in srgb,var(--color-text) 6%,transparent);" if i < 3 else ""
        rows.append(
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 0;{sep}">'  # noqa
            f'<span style="font-size:0.9rem;color:var(--color-muted);">{m}</span>'
            f'<span style="font-weight:700;color:var(--color-primary);">{v}</span></div>'
        )
    table = "".join(rows)
    sec = f'data-section-type="data_narrative" data-section-index="{idx}"'
    return f"""<section {sec} style="padding:var(--section-padding);background:var(--color-surface);" class="surface">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center;">
      <div>
        <h2 style="font-size:clamp(1.8rem,3vw,2.8rem);font-weight:800;margin-bottom:1.5rem;">Les données au service de la décision</h2>
        <p style="color:var(--color-muted);line-height:1.7;margin-bottom:1.5rem;">Chaque décision que nous prenons est étayée par des données réelles.</p>
        <p style="color:var(--color-muted);line-height:1.7;">Nos tableaux de bord en temps réel vous donnent une visibilité totale sur vos indicateurs clés.</p>
      </div>
      <div>
        <div style="background:var(--color-bg);border-radius:var(--radius-lg);padding:2rem;border:1px solid color-mix(in srgb,var(--color-text) 8%,transparent);">
          {table}
        </div>
      </div>
    </div>
  </div>
</section>"""


def _b_proof_strip(idx: int, ctx: dict, plan: dict) -> str:
    logos = ["Entreprise A", "Groupe B", "Corp C", "Société D", "Firm E", "Inc. F"]
    items = "".join(
        f'<div style="display:flex;align-items:center;justify-content:center;padding:1.5rem;background:var(--color-surface);border-radius:var(--radius-md);font-weight:700;font-size:0.85rem;color:var(--color-muted);letter-spacing:0.05em;text-transform:uppercase;">{l}</div>'
        for l in logos
    )
    return f"""<section data-section-type="proof_strip" data-section-index="{idx}" style="padding:3rem 0;background:var(--color-bg);">
  <div class="container">
    <p style="text-align:center;font-size:0.8rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--color-muted);font-weight:600;margin-bottom:2rem;">Ils nous font confiance</p>
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:1rem;">{items}</div>
  </div>
</section>"""


def _b_cta_block(idx: int, ctx: dict, plan: dict) -> str:
    brand = ctx.get("brand_name", ctx.get("project_name", "Brand"))
    return f"""<section data-section-type="cta_block" data-section-index="{idx}" style="padding:6rem 0;background:var(--color-primary);">
  <div class="container--narrow" style="text-align:center;">
    <h2 style="font-size:clamp(2rem,4vw,3rem);font-weight:900;color:var(--color-bg);margin-bottom:1.5rem;line-height:1.1;">
      Prêt à transformer votre vision en réalité ?
    </h2>
    <p style="font-size:1.1rem;color:color-mix(in srgb,var(--color-bg) 80%,transparent);margin-bottom:3rem;line-height:1.6;max-width:480px;margin-left:auto;margin-right:auto;">
      Rejoignez les équipes qui ont choisi {brand} pour accélérer leur croissance. Premier échange offert, sans engagement.
    </p>
    <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
      <a href="#contact" class="btn" style="background:var(--color-bg);color:var(--color-primary);font-size:1rem;padding:1rem 2.5rem;">Démarrer maintenant</a>
      <a href="#about" class="btn" style="background:transparent;color:var(--color-bg);border-color:rgba(255,255,255,0.4);font-size:1rem;padding:1rem 2.5rem;">En savoir plus</a>
    </div>
  </div>
</section>"""


# ─── Registry des section builders ───────────────────────────────────────────

_SECTION_BUILDERS: dict[str, Any] = {
    "hero":                  _b_hero,
    "editorial_narrative":   _b_editorial_narrative,
    "visual_break":          _b_visual_break,
    "feature_split":         _b_feature_split,
    "quote_pull":            _b_quote_pull,
    "spread_feature":        _b_spread_feature,
    "column_narrative":      _b_column_narrative,
    "visual_interrupt":      _b_visual_interrupt,
    "byline_block":          _b_byline_block,
    "chapter_opener":        _b_chapter_opener,
    "narrative_text":        _b_narrative_text,
    "visual_pause":          _b_visual_pause,
    "feature_list":          _b_feature_list,
    "feature_offset":        _b_feature_offset,
    "narrative_block":       _b_narrative_block,
    "visual_contrast":       _b_visual_contrast,
    "staggered_feature":     _b_staggered_feature,
    "data_strip":            _b_data_strip,
    "offset_visual":         _b_offset_visual,
    "asymmetric_grid":       _b_asymmetric_grid,
    "module_cluster":        _b_module_cluster,
    "stat_row":              _b_stat_row,
    "visual_module":         _b_visual_module,
    "feature_tiles":         _b_feature_tiles,
    "data_wall":             _b_data_wall,
    "brutal_text_block":     _b_brutal_text_block,
    "raw_visual":            _b_raw_visual,
    "layer_reveal":          _b_layer_reveal,
    "depth_feature":         _b_depth_feature,
    "overlap_narrative":     _b_overlap_narrative,
    "floating_cta":          _b_floating_cta,
    "diagonal_feature":      _b_diagonal_feature,
    "tension_visual":        _b_tension_visual,
    "oblique_narrative":     _b_oblique_narrative,
    "contrast_block":        _b_contrast_block,
    "manifesto_strip":       _b_manifesto_strip,
    "stat_centered":         _b_stat_centered,
    "feature_centered":      _b_feature_centered,
    "quote_centered":        _b_quote_centered,
    "anchor_statement":      _b_anchor_statement,
    "feature_compact":       _b_feature_compact,
    "social_proof":          _b_social_proof,
    "zigzag_left":           _b_zigzag_left,
    "zigzag_right":          _b_zigzag_right,
    "whitespace_text":       _b_whitespace_text,
    "single_feature":        _b_single_feature,
    "filmstrip_band":        _b_filmstrip_band,
    "mosaic_header":         _b_mosaic_header,
    "mosaic_grid":           _b_mosaic_grid,
    "poster_statement":      _b_poster_statement,
    "type_hierarchy":        _b_type_hierarchy,
    "type_feature":          _b_type_feature,
    "sidebar_content":       _b_sidebar_content,
    "sidebar_feature":       _b_sidebar_feature,
    "sidebar_stats":         _b_sidebar_stats,
    "sidebar_cta":           _b_sidebar_cta,
    "data_showcase":         _b_data_showcase,
    "stat_grid":             _b_stat_grid,
    "data_narrative":        _b_data_narrative,
    "proof_strip":           _b_proof_strip,
    "cta_block":             _b_cta_block,
}


# ─── Navbar + Footer ──────────────────────────────────────────────────────────

def _build_navbar(brand: str) -> str:
    return f"""<nav class="navbar" aria-label="Navigation principale">
  <div class="container">
    <div class="navbar__inner">
      <a href="#" class="navbar__logo">{brand}</a>
      <ul class="navbar__links">
        <li><a href="#features">Produit</a></li>
        <li><a href="#about">À propos</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
      <a href="#contact" class="btn btn--primary" style="padding:0.5rem 1.25rem;font-size:0.875rem;">Démarrer</a>
    </div>
  </div>
</nav>"""


def _build_footer(brand: str, visual_family: str) -> str:
    return f"""<footer class="footer" aria-label="Pied de page">
  <div class="container">
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:3rem;">
      <div>
        <div style="font-family:var(--font-heading);font-weight:800;font-size:1.3rem;color:var(--color-bg);margin-bottom:1rem;">{brand}</div>
        <p style="color:var(--color-muted);font-size:0.9rem;line-height:1.6;max-width:260px;">
          Excellence, précision et impact. Votre partenaire de confiance pour accélérer votre croissance.
        </p>
      </div>
      <div>
        <div style="font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--color-bg);margin-bottom:1rem;opacity:0.6;">Produit</div>
        <ul style="list-style:none;display:flex;flex-direction:column;gap:0.5rem;">
          {"".join(f'<li><a href="#" style="color:var(--color-muted);font-size:0.875rem;">{l}</a></li>' for l in ["Fonctionnalités", "Tarifs", "Roadmap", "Changelog"])}
        </ul>
      </div>
      <div>
        <div style="font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--color-bg);margin-bottom:1rem;opacity:0.6;">Ressources</div>
        <ul style="list-style:none;display:flex;flex-direction:column;gap:0.5rem;">
          {"".join(f'<li><a href="#" style="color:var(--color-muted);font-size:0.875rem;">{l}</a></li>' for l in ["Documentation", "Blog", "API", "Support"])}
        </ul>
      </div>
      <div>
        <div style="font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--color-bg);margin-bottom:1rem;opacity:0.6;">Légal</div>
        <ul style="list-style:none;display:flex;flex-direction:column;gap:0.5rem;">
          {"".join(f'<li><a href="#" style="color:var(--color-muted);font-size:0.875rem;">{l}</a></li>' for l in ["CGU", "Confidentialité", "Cookies", "Mentions légales"])}
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© 2026 {brand}. Tous droits réservés.</span>
      <span style="color:var(--color-muted);font-size:0.8rem;">{visual_family} · v2</span>
    </div>
  </div>
</footer>"""


# ─── Entry point ──────────────────────────────────────────────────────────────

def render_from_plan(plan: dict, context: dict, palette_override: dict | None = None) -> str:
    """
    Rend une page HTML complète depuis un DesignPlan.

    Args:
        plan           : dict issu de validate_design_plan (ou compose_design_plan)
        context        : contexte pipeline (brand_name, seed, etc.)
        palette_override: palette déjà résolue (dict avec primary/bg/text) — optionnel

    Returns:
        str : HTML complet

    Raises:
        RenderError : si un section_type n'a pas de builder enregistré
    """
    layout_strategy   = plan["layout_strategy"]
    hero_type         = plan["hero_type"]
    visual_family     = plan["visual_family"]
    palette_family    = plan["palette_family"]
    typography_family = plan["typography_family"]
    section_types     = plan["section_types"]
    composition       = plan.get("composition", {"density": "medium", "grid": "12col"})

    # ── Résolution palette + fonts ────────────────────────────────────────────
    palette = _resolve_palette(palette_family, palette_override)
    fonts   = _resolve_fonts(typography_family)
    css     = _build_css(palette, fonts, composition)

    brand = context.get("brand_name", context.get("project_name", "Brand"))

    # ── Vérification builders avant rendu ────────────────────────────────────
    missing = [s for s in section_types if s not in _SECTION_BUILDERS]
    if missing:
        raise RenderError(
            f"section_type(s) sans builder: {missing}. "
            f"layout_strategy={layout_strategy!r}, hero_type={hero_type!r}. "
            f"Ajouter un builder dans render_strict._SECTION_BUILDERS."
        )

    # ── Rendu sections ────────────────────────────────────────────────────────
    sections_html = []
    for idx, section_type in enumerate(section_types):
        builder = _SECTION_BUILDERS[section_type]
        sections_html.append(builder(idx, context, plan))

    # ── Assemblage HTML ───────────────────────────────────────────────────────
    google_fonts_url = _build_google_fonts_url(typography_family)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{brand}</title>
  {f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="{google_fonts_url}" rel="stylesheet">' if google_fonts_url else ''}
  <style>
{css}
  </style>
</head>
<body
  data-layout-strategy="{layout_strategy}"
  data-visual-family="{visual_family}"
  data-palette-family="{palette_family}"
  data-typography-family="{typography_family}"
  data-hero-type="{hero_type}"
  data-seed="{context.get('seed', 42)}"
>
{_build_navbar(brand)}
<main>
{"".join(sections_html)}
</main>
{_build_footer(brand, visual_family)}
</body>
</html>"""


def _build_google_fonts_url(typography_family: str) -> str:
    """Retourne une URL Google Fonts pour les polices identifiées, ou '' si system fonts."""
    _FAMILY_TO_FONTS: dict[str, list[str]] = {
        "serif_editorial":     ["Playfair+Display:wght@400;700;900", "Source+Serif+Pro:wght@400;600"],
        "sans_editorial":      ["DM+Sans:wght@400;500;700"],
        "serif_luxury":        ["Cormorant+Garamond:wght@400;600;700"],
        "sans_luxury":         ["Montserrat:wght@400;600;700;800", "Lato:wght@400;700"],
        "display_playful":     ["Fredoka+One", "Nunito:wght@400;700;900"],
        "rounded_playful":     ["Nunito:wght@400;600;700;900"],
        "humanist_sans":       ["Inter:wght@400;500;600;700;900"],
        "serif_warm":          ["Lora:wght@400;600;700"],
        "geometric_sans":      ["Inter:wght@400;500;600;700;900"],
        "corporate_sans":      ["IBM+Plex+Sans:wght@400;500;600;700"],
        "corporate_serif":     ["Merriweather:wght@400;700;900"],
        "mono_tech":           ["JetBrains+Mono:wght@400;700"],
        "geometric_tech":      ["Space+Grotesk:wght@400;500;600;700"],
        "slab_brutal":         ["Roboto+Slab:wght@400;700;900"],
        "organic_serif":       ["Crimson+Text:wght@400;600;700"],
        "handwritten_natural": ["Caveat:wght@400;700", "Lato:wght@400;700"],
        "refined_serif":       ["EB+Garamond:wght@400;600;700"],
        "craft_sans":          ["Josefin+Sans:wght@400;600;700"],
        "bold_display":        ["Oswald:wght@400;600;700", "Open+Sans:wght@400;600"],
        "condensed_impact":    ["Barlow+Condensed:wght@400;600;700;900", "Barlow:wght@400;600"],
        "experimental_type":   ["Space+Mono:wght@400;700"],
        "mixed_editorial":     ["Playfair+Display:wght@400;700;900", "DM+Sans:wght@400;500;700"],
    }
    fonts = _FAMILY_TO_FONTS.get(typography_family)
    if not fonts:
        return ""
    families = "&family=".join(fonts)
    return f"https://fonts.googleapis.com/css2?family={families}&display=swap"
