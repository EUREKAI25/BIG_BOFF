#!/usr/bin/env python3
"""
Génère demo_visual_decorators.html — démo visuelle du Visual Decorators Engine.

Appelle le module directement, traduit les valeurs en CSS, génère la page.
"""

import sys
import json
import subprocess
from pathlib import Path

# Path setup
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / "MODULES" / "visual_decorators"))

from src.visual_decorators import generate_visual_decorators

# ─────────────────────────────────────────────────────────────────────────────
# Cas à afficher
# ─────────────────────────────────────────────────────────────────────────────

EMOTIONAL_CASES = [
    ("trust",      "finance",   "Trust",      "#1a2e4a", "#4a90d9", "Finance / SaaS / Health"),
    ("excitement", "gaming",    "Excitement", "#1a0a2e", "#ff3d6b", "Gaming / Event"),
    ("desire",     "dating",    "Desire",     "#2e1a1a", "#ff7b7b", "Dating / Ecommerce / Food"),
    ("calm",       "health",    "Calm",       "#1a2e2a", "#6bc4a4", "Health / Wellness"),
    ("curiosity",  "editorial", "Curiosity",  "#1a1a2a", "#a08fff", "Editorial / Education"),
    ("authority",  "agency",    "Authority",  "#1e1e1e", "#e0c97f", "Agency / Institution"),
]

STYLE_FAMILY_CASES = [
    ("editorial_luxury", "editorial_luxury", "Editorial Luxury", "#0e0e0e", "#c8b078"),
    ("brutalist",        "brutalist",        "Brutalist",        "#111",    "#ffffff"),
    ("tech_minimal",     "tech_minimal",     "Tech Minimal",     "#0d1117", "#58a6ff"),
    ("experimental_grid","experimental_grid","Experimental Grid","#0a0a0f", "#ff6fff"),
    ("premium_brand",    "premium_brand",    "Premium Brand",    "#0e0c08", "#d4af6a"),
    ("bold_marketing",   "bold_marketing",   "Bold Marketing",   "#0f0f0f", "#ff5533"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Traduction valeurs → CSS
# ─────────────────────────────────────────────────────────────────────────────

def _border_css(dec: dict, accent_color: str) -> str:
    b = dec["borders"]
    style = b["style"]
    thickness_map = {"none": "0px", "thin": "1px", "medium": "2px", "thick": "4px"}
    radius_map    = {"none": "0", "small": "4px", "medium": "12px", "large": "24px", "full": "999px"}
    thick = thickness_map.get(b["thickness"], "1px")
    radius = radius_map.get(b["radius"], "4px")
    pattern = b["pattern"]

    if style == "none" or b["thickness"] == "none":
        border_str = "border: none;"
    elif style == "double":
        border_str = f"border: {thick} double {accent_color};"
    elif style == "dashed":
        border_str = f"border: {thick} dashed {accent_color};"
    elif style == "dotted":
        border_str = f"border: {thick} dotted {accent_color};"
    elif style == "glow":
        border_str = f"border: {thick} solid {accent_color}; box-shadow: 0 0 12px {accent_color}88, 0 0 24px {accent_color}44;"
    else:  # solid
        border_str = f"border: {thick} solid {accent_color};"

    # Pattern modifier
    if pattern == "top-only":
        border_str = border_str.replace("border:", "border-top:") + " border-right:none; border-bottom:none; border-left:none;" if style != "none" else border_str
    elif pattern == "accent":
        if style != "none":
            border_str = f"border-left: 3px solid {accent_color}; border-top:none; border-right:none; border-bottom:none;"

    return f"{border_str} border-radius: {radius};"


def _divider_html(dec: dict, accent_color: str, bg_color: str) -> str:
    d = dec["dividers"]
    dtype = d["type"]
    dstyle = d["style"]

    width_map   = {"bold": "2px", "decorative": "1px", "minimal": "1px", "subtle": "1px"}
    opacity_map = {"bold": "0.8", "decorative": "0.6", "minimal": "0.3", "subtle": "0.2"}
    w = width_map.get(dstyle, "1px")
    op = opacity_map.get(dstyle, "0.3")

    if dtype == "none" or dtype == "space":
        return f'<div style="height:24px;"></div>'
    elif dtype == "line":
        return f'<div style="height:{w}; background:{accent_color}; opacity:{op}; margin:16px 0;"></div>'
    elif dtype == "gradient":
        return f'<div style="height:{w}; background:linear-gradient(90deg,transparent,{accent_color},{accent_color},{accent_color},transparent); opacity:{op}; margin:16px 0;"></div>'
    elif dtype == "zigzag":
        return f'''<svg width="100%" height="12" style="margin:12px 0;display:block;" viewBox="0 0 200 12" preserveAspectRatio="none">
  <polyline points="0,6 10,0 20,6 30,0 40,6 50,0 60,6 70,0 80,6 90,0 100,6 110,0 120,6 130,0 140,6 150,0 160,6 170,0 180,6 190,0 200,6"
    fill="none" stroke="{accent_color}" stroke-width="1.5" opacity="{op}"/>
</svg>'''
    elif dtype == "ornament":
        return f'''<div style="text-align:center;margin:12px 0;opacity:{op};color:{accent_color};font-size:0.9rem;letter-spacing:0.3em;">
  ◆ ◇ ◆
</div>'''
    return f'<div style="height:1px;background:{accent_color};opacity:{op};margin:16px 0;"></div>'


def _icon_svg(dec: dict, accent_color: str) -> str:
    i = dec["icons"]
    istyle = i["style"]
    stroke_map = {"thin": "1", "medium": "1.5", "thick": "2.5"}
    sw = stroke_map.get(i["stroke"], "1.5")
    corner = i["corner_style"]
    rx = "0" if corner == "sharp" else ("6" if corner == "rounded" else "3")

    icons = []
    for shape, path in [
        ("circle",   f'<circle cx="12" cy="12" r="8" />'),
        ("square",   f'<rect x="4" y="4" width="16" height="16" rx="{rx}" />'),
        ("arrow",    f'<path d="M5 12h14M13 6l6 6-6 6" stroke-linecap="{"round" if corner=="rounded" else "square"}" stroke-linejoin="{"round" if corner=="rounded" else "miter"}" />'),
        ("star",     f'<polygon points="12,3 14.5,9 21,9 15.5,13.5 17.5,20 12,16 6.5,20 8.5,13.5 3,9 9.5,9" />'),
    ]:
        if istyle == "filled":
            icons.append(f'<svg width="28" height="28" viewBox="0 0 24 24" fill="{accent_color}" stroke="none">{path}</svg>')
        elif istyle == "duotone":
            icons.append(f'<svg width="28" height="28" viewBox="0 0 24 24" fill="{accent_color}44" stroke="{accent_color}" stroke-width="{sw}">{path}</svg>')
        elif istyle == "outline-filled":
            icons.append(f'<svg width="28" height="28" viewBox="0 0 24 24" fill="{accent_color}22" stroke="{accent_color}" stroke-width="{sw}">{path}</svg>')
        else:  # line
            icons.append(f'<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{accent_color}" stroke-width="{sw}">{path}</svg>')

    complexity = i["complexity"]
    n = {"simple": 2, "medium": 3, "detailed": 4}.get(complexity, 2)
    return f'<div style="display:flex;gap:10px;align-items:center;">{"".join(icons[:n])}</div>'


def _motif_css(dec: dict, accent_color: str) -> str:
    m = dec["motifs"]
    mtype = m["type"]
    usage = m["usage"]
    if mtype == "none":
        return ""
    opacity = "0.06" if usage in ("background", "full-bleed") else "0.12"
    col = accent_color

    patterns = {
        "dot-pattern":    f"radial-gradient({col} 1px, transparent 1px)",
        "geometric":      f"repeating-linear-gradient(45deg, {col}22 0, {col}22 1px, transparent 0, transparent 50%)",
        "grid-fragment":  f"linear-gradient({col}30 1px, transparent 1px), linear-gradient(90deg, {col}30 1px, transparent 1px)",
        "diagonal-cut":   f"repeating-linear-gradient(-45deg, transparent, transparent 10px, {col}22 10px, {col}22 11px)",
        "line-pattern":   f"repeating-linear-gradient(0deg, {col}22 0, {col}22 1px, transparent 0, transparent 8px)",
        "wave":           f"repeating-radial-gradient(ellipse at 0% 50%, transparent 0, transparent 8px, {col}22 8px, {col}22 9px)",
        "noise":          f"url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E\")",
        "blob":           f"radial-gradient(ellipse 60% 40% at 70% 30%, {col}20 0%, transparent 70%)",
    }
    bg_size = {
        "dot-pattern":    "12px 12px",
        "geometric":      "20px 20px",
        "grid-fragment":  "24px 24px",
        "diagonal-cut":   "",
        "line-pattern":   "",
        "wave":           "18px 18px",
        "noise":          "",
        "blob":           "",
    }
    pat = patterns.get(mtype, "")
    sz  = bg_size.get(mtype, "")
    if not pat:
        return ""
    size_css = f"background-size:{sz};" if sz else ""
    return f"background-image:{pat};{size_css}"


def _overlay_css(dec: dict, accent_color: str, bg_color: str) -> str:
    o = dec["overlays"]
    otype = o["type"]
    intensity_map = {"subtle": "0.08", "medium": "0.18", "strong": "0.35"}
    op = intensity_map.get(o["intensity"], "0")
    if otype == "none" or o["intensity"] == "none":
        return ""
    if otype == "gradient":
        return f"background: linear-gradient(135deg, {accent_color}{int(float(op)*255):02x} 0%, transparent 60%);"
    if otype == "scanlines":
        return f"background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,{op}) 2px, rgba(0,0,0,{op}) 4px);"
    if otype == "noise":
        return f"opacity:{float(op)*3:.2f}; background: url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='{op}'/%3E%3C/svg%3E\");"
    if otype == "vignette":
        return f"background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,{float(op)*2:.2f}) 100%);"
    if otype == "duotone":
        return f"background: linear-gradient(135deg, {bg_color}cc, {accent_color}{int(float(op)*255):02x});"
    return ""


def _decorator_card(title: str, subtitle: str, dec: dict, bg_color: str, accent_color: str) -> str:
    border_css  = _border_css(dec, accent_color)
    divider_html = _divider_html(dec, accent_color, bg_color)
    icons_html  = _icon_svg(dec, accent_color)
    motif_css   = _motif_css(dec, accent_color)
    overlay_css = _overlay_css(dec, accent_color, bg_color)

    motif_layer = f'<div style="position:absolute;inset:0;{motif_css}pointer-events:none;border-radius:inherit;"></div>' if motif_css else ""
    overlay_layer = f'<div style="position:absolute;inset:0;{overlay_css}pointer-events:none;border-radius:inherit;"></div>' if overlay_css else ""

    json_lines = json.dumps(dec, indent=2)

    b = dec["borders"]
    d = dec["dividers"]
    i = dec["icons"]
    m = dec["motifs"]
    o = dec["overlays"]

    tags = []
    tags.append(f'<span class="tag">{b["style"]}</span>')
    tags.append(f'<span class="tag">{b["thickness"]}</span>')
    if b["radius"] != "none": tags.append(f'<span class="tag">r:{b["radius"]}</span>')
    if b["pattern"] != "uniform": tags.append(f'<span class="tag">{b["pattern"]}</span>')
    if d["type"] != "none": tags.append(f'<span class="tag">{d["type"]}/{d["style"]}</span>')
    tags.append(f'<span class="tag">{i["style"]} {i["stroke"]}</span>')
    tags.append(f'<span class="tag">{i["corner_style"]} {i["complexity"]}</span>')
    if m["type"] != "none": tags.append(f'<span class="tag">motif:{m["type"]}</span>')
    if o["type"] != "none": tags.append(f'<span class="tag">overlay:{o["type"]}</span>')

    return f'''
<div class="card" style="background:{bg_color}; position:relative; overflow:hidden;">
  {motif_layer}
  {overlay_layer}
  <div style="position:relative;z-index:1;">
    <div class="card-inner" style="{border_css}">
      <div class="card-title" style="color:{accent_color};">{title}</div>
      <div class="card-subtitle">{subtitle}</div>

      {divider_html}

      <div class="demo-block" style="margin-bottom:16px;">
        <div class="label">ICONS · {i["style"].upper()} · {i["corner_style"].upper()}</div>
        {icons_html}
      </div>

      {divider_html}

      <div class="demo-block">
        <div class="label">BORDERS · {b["style"].upper()} {b["thickness"].upper()}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <div style="width:48px;height:32px;{border_css}"></div>
          <div style="width:80px;height:32px;{border_css}opacity:0.6;"></div>
          <div style="width:64px;height:32px;{border_css}opacity:0.3;"></div>
        </div>
      </div>

      <div class="tags" style="margin-top:16px;">{"".join(tags)}</div>
    </div>
  </div>
</div>'''


# ─────────────────────────────────────────────────────────────────────────────
# Génération HTML
# ─────────────────────────────────────────────────────────────────────────────

def generate_html() -> str:

    def make_intent(emotional_goal="", brand_positioning="", style_family="neutral",
                    intensity="medium", density="medium") -> dict:
        return {
            "mode": "default",
            "art_direction": {"style_family": style_family, "tone": "", "intensity": intensity, "personality": []},
            "composition_bias": {"dominance": "balanced", "density": density, "asymmetry": "low", "rhythm": "regular"},
            "visual_techniques": [],
            "color_strategy": {"contrast": "medium", "palette_type": "neutral"},
            "typography_strategy": {"hierarchy_strength": "medium", "weight_contrast": "medium"},
            "constraints": {"force": [], "avoid": []},
            "context": {"product_type": "generic", "target_audience": "general",
                        "emotional_goal": emotional_goal, "brand_positioning": brand_positioning},
        }

    # Générer toutes les cartes
    emotional_cards = ""
    for goal, product, label, bg, accent, desc in EMOTIONAL_CASES:
        intent = make_intent(emotional_goal=goal, brand_positioning="", intensity="medium")
        dec = generate_visual_decorators(intent)
        emotional_cards += _decorator_card(label, desc, dec, bg, accent)

    style_cards = ""
    for sf, product, label, bg, accent in STYLE_FAMILY_CASES:
        intent = make_intent(style_family=sf, intensity="medium")
        dec = generate_visual_decorators(intent)
        style_cards += _decorator_card(label, f"style_family={sf}", dec, bg, accent)

    # Cartes combinées (spec)
    combo_cases = [
        ("Gaming", "excitement", "disruptive", "gaming", "high", "#0a0814", "#ff3d6b"),
        ("Dating", "desire", "playful", "dating", "medium", "#1a0c14", "#ff8fad"),
        ("Finance", "trust", "serious", "finance", "low", "#080e18", "#4a8fcf"),
        ("Luxury", "desire", "premium", "luxury", "medium", "#0c0a06", "#c8a45a"),
    ]
    combo_cards = ""
    for label, goal, pos, product, intensity, bg, accent in combo_cases:
        intent = make_intent(emotional_goal=goal, brand_positioning=pos, intensity=intensity)
        dec = generate_visual_decorators(intent)
        combo_cards += _decorator_card(label, f"{goal} + {pos}", dec, bg, accent)

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EURKAI — Visual Decorators Demo</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #060608;
    color: #ccc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    padding: 40px 24px;
    min-height: 100vh;
  }}
  .page-title {{
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 4px;
  }}
  .page-heading {{
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 6px;
  }}
  .page-sub {{
    font-size: 0.85rem;
    color: #555;
    margin-bottom: 48px;
    max-width: 520px;
    line-height: 1.6;
  }}
  .section-label {{
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1a1a1a;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 60px;
  }}
  .card {{
    border-radius: 8px;
    padding: 24px;
  }}
  .card-inner {{
    padding: 20px;
    border-radius: inherit;
  }}
  .card-title {{
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 4px;
  }}
  .card-subtitle {{
    font-size: 0.7rem;
    color: #666;
    letter-spacing: 0.08em;
    margin-bottom: 20px;
  }}
  .demo-block {{
    margin-bottom: 12px;
  }}
  .label {{
    font-size: 0.55rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 8px;
  }}
  .tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }}
  .tag {{
    font-size: 0.6rem;
    padding: 2px 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 2px;
    color: #666;
    letter-spacing: 0.05em;
  }}
  .note {{
    font-size: 0.75rem;
    color: #444;
    margin-top: -40px;
    margin-bottom: 48px;
    font-style: italic;
  }}
</style>
</head>
<body>

<div class="page-title">EURKAI — Visual Decorators Engine</div>
<h1 class="page-heading">Couche de signature visuelle</h1>
<p class="page-sub">
  Chaque préset définit un système décoratif cohérent : borders, dividers, icons, motifs, overlays.
  Peu d'éléments, utilisés uniformément. La cohérence EST le design.
</p>

<div class="section-label">01 — Cas spec (emotional_goal + brand_positioning)</div>
<div class="grid">{combo_cards}</div>

<div class="section-label">02 — Presets par objectif émotionnel</div>
<div class="grid">{emotional_cards}</div>

<div class="section-label">03 — Style family overrides (priment sur tout)</div>
<div class="grid">{style_cards}</div>

</body>
</html>'''


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = Path(__file__).parent / "demo_visual_decorators.html"
    html = generate_html()
    out.write_text(html, encoding="utf-8")
    print(f"✅ Généré : {out}")
    subprocess.run(["open", str(out)])
