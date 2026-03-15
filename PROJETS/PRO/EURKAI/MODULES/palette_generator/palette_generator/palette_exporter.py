"""
palette_generator.palette_exporter
────────────────────────────────────
Exporte la PaletteSet vers :
  palette.json         → toutes les palettes sérialisées
  design_tokens.json   → tokens plats {color.primary.500: "#hex"}
  palette.svg          → swatches visuels SVG (pur stdlib)
  palette.png          → swatches PNG (nécessite Pillow, optionnel)
"""

from __future__ import annotations
import dataclasses
import json
import os
from typing import Dict, List, Optional

from .schemas import PaletteSet, Palette, ColorValue, TonalScale
from .color_scale_generator import scales_to_tokens


# ─── JSON ─────────────────────────────────────────────────────────────────────

def export_json(palette_set: PaletteSet, output_dir: str) -> str:
    path = os.path.join(output_dir, "palette.json")
    data = _palette_set_to_dict(palette_set)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


# ─── Design Tokens ────────────────────────────────────────────────────────────

def export_tokens(palette_set: PaletteSet, output_dir: str) -> str:
    """
    Génère design_tokens.json avec les tokens plats.
    Structure : {"color.primary.500": "#3B82F6", "color.background": "#FFF", ...}
    """
    tokens: Dict[str, str] = {}

    # Tokens depuis les scales tonales de la palette principale
    main = (
        palette_set.monochromatic
        or palette_set.complementary
        or palette_set.analogous
    )
    if main and main.tonal_scales:
        for scale in main.tonal_scales:
            tokens.update(scales_to_tokens(scale))

    # Tokens sémantiques depuis la palette la plus complète
    if main:
        _add_semantic_tokens(tokens, main)

    # Tokens dark mode si présent
    if palette_set.scenario.value == "dark_mode_palette" and palette_set.ui_safe:
        _add_semantic_tokens(tokens, palette_set.ui_safe, prefix="dark.")

    path = os.path.join(output_dir, "design_tokens.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    return path


def _add_semantic_tokens(tokens: dict, palette: Palette, prefix: str = "") -> None:
    if palette.primary:
        tokens[f"{prefix}color.primary"] = palette.primary[0].hex
        if len(palette.primary) > 1:
            tokens[f"{prefix}color.primary.light"] = palette.primary[1].hex
    if palette.secondary:
        tokens[f"{prefix}color.secondary"] = palette.secondary[0].hex
    if palette.accent:
        tokens[f"{prefix}color.accent"] = palette.accent[0].hex
    if palette.neutral:
        tokens[f"{prefix}color.background"] = palette.neutral[0].hex
        if len(palette.neutral) > 3:
            tokens[f"{prefix}color.text"] = palette.neutral[3].hex


# ─── SVG ──────────────────────────────────────────────────────────────────────

_SWATCH_W = 80
_SWATCH_H = 60
_LABEL_H  = 16
_PADDING  = 8


def _palette_to_svg_row(palette: Palette, y_offset: int) -> tuple[str, int]:
    """Génère une ligne de swatches SVG pour une palette. Retourne (svg_str, height_used)."""
    all_colors: List[ColorValue] = (
        palette.primary + palette.secondary + palette.accent + palette.neutral
    )[:12]  # max 12 couleurs

    row_w = len(all_colors) * (_SWATCH_W + _PADDING) + _PADDING
    row_h = _SWATCH_H + _LABEL_H + _PADDING * 2

    parts = [
        f'<text x="{_PADDING}" y="{y_offset + 14}" font-family="monospace" font-size="11" fill="#666">'
        f'{palette.harmony}</text>'
    ]
    for i, cv in enumerate(all_colors):
        x = _PADDING + i * (_SWATCH_W + _PADDING)
        y = y_offset + _LABEL_H + _PADDING
        label = cv.name or cv.hex
        parts.append(
            f'<rect x="{x}" y="{y}" width="{_SWATCH_W}" height="{_SWATCH_H}" '
            f'rx="4" fill="{cv.hex}" stroke="#E0E0E0" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x + 4}" y="{y + _SWATCH_H + 12}" font-family="monospace" '
            f'font-size="8" fill="#888">{cv.hex}</text>'
        )

    return "\n".join(parts), row_h + _LABEL_H


def export_svg(palette_set: PaletteSet, output_dir: str) -> str:
    """Génère un fichier SVG avec tous les swatches de palette."""
    rows = []
    y = _PADDING

    palettes_to_show = [
        p for p in [
            palette_set.monochromatic,
            palette_set.analogous,
            palette_set.complementary,
            palette_set.split_complementary,
            palette_set.triadic,
            palette_set.tetradic,
            palette_set.minimal,
            palette_set.ui_safe,
        ] if p is not None
    ]

    total_h = _PADDING
    svg_rows = []
    for palette in palettes_to_show:
        row_svg, row_h = _palette_to_svg_row(palette, y)
        svg_rows.append(row_svg)
        y += row_h + _PADDING
        total_h = y

    max_colors = max((
        len(p.primary) + len(p.secondary) + len(p.accent) + len(p.neutral)
        for p in palettes_to_show
    ), default=6)
    total_w = min(max_colors, 12) * (_SWATCH_W + _PADDING) + _PADDING * 2

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}" style="background:#FAFAFA">\n'
        + "\n".join(svg_rows)
        + "\n</svg>"
    )

    path = os.path.join(output_dir, "palette.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path


# ─── PNG (optionnel) ─────────────────────────────────────────────────────────

def export_png(palette_set: PaletteSet, output_dir: str) -> Optional[str]:
    """Génère palette.png via Pillow. Retourne None si Pillow non installé."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    palettes = [
        p for p in [
            palette_set.monochromatic, palette_set.analogous,
            palette_set.complementary, palette_set.triadic,
            palette_set.minimal, palette_set.ui_safe,
        ] if p is not None
    ]

    max_colors = max(
        (len(p.primary) + len(p.secondary) + len(p.accent) + len(p.neutral) for p in palettes),
        default=6
    )
    max_colors = min(max_colors, 12)

    W = max_colors * (_SWATCH_W + _PADDING) + _PADDING
    H = len(palettes) * (_SWATCH_H + _LABEL_H + _PADDING * 2) + _PADDING

    img = Image.new("RGB", (W, H), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    y = _PADDING
    for palette in palettes:
        all_colors = (palette.primary + palette.secondary + palette.accent + palette.neutral)[:max_colors]
        x = _PADDING
        for cv in all_colors:
            r, g, b = cv.rgb
            draw.rectangle([x, y + _LABEL_H, x + _SWATCH_W, y + _LABEL_H + _SWATCH_H], fill=(r, g, b))
            draw.rectangle([x, y + _LABEL_H, x + _SWATCH_W, y + _LABEL_H + _SWATCH_H], outline=(220, 220, 220))
            x += _SWATCH_W + _PADDING
        y += _SWATCH_H + _LABEL_H + _PADDING * 2

    path = os.path.join(output_dir, "palette.png")
    img.save(path)
    return path


# ─── Sérialisation ────────────────────────────────────────────────────────────

def _color_to_dict(cv: ColorValue) -> dict:
    return {"hex": cv.hex, "rgb": list(cv.rgb), "name": cv.name, "role": cv.role}


def _palette_to_dict(p: Palette) -> dict:
    return {
        "harmony": p.harmony,
        "primary":   [_color_to_dict(c) for c in p.primary],
        "secondary": [_color_to_dict(c) for c in p.secondary],
        "accent":    [_color_to_dict(c) for c in p.accent],
        "neutral":   [_color_to_dict(c) for c in p.neutral],
    }


def _palette_set_to_dict(ps: PaletteSet) -> dict:
    result: dict = {"base_hex": ps.base_hex, "scenario": ps.scenario.value}
    for key in [
        "monochromatic", "analogous", "complementary", "split_complementary",
        "triadic", "tetradic", "minimal", "ui_safe",
    ]:
        val = getattr(ps, key)
        if val is not None:
            result[key] = _palette_to_dict(val)

    if ps.black_and_white_variant:
        bw = ps.black_and_white_variant
        result["black_and_white_variant"] = {
            "false_blacks": [_color_to_dict(c) for c in bw.false_blacks],
            "false_whites": [_color_to_dict(c) for c in bw.false_whites],
        }
    if ps.metal_variant:
        mv = ps.metal_variant
        result["metal_variant"] = {
            "finish": mv.finish.value,
            "base_tones": [_color_to_dict(c) for c in mv.base_tones],
            "highlights": [_color_to_dict(c) for c in mv.highlights],
            "shadows":    [_color_to_dict(c) for c in mv.shadows],
            "accent":     [_color_to_dict(c) for c in mv.accent],
        }
    if ps.accessibility_report:
        ar = ps.accessibility_report
        result["accessibility_report"] = {
            "all_aa_pass": ar.all_aa_pass,
            "all_aaa_pass": ar.all_aaa_pass,
            "checks": [dataclasses.asdict(c) for c in ar.checks],
        }
    return result


# ─── Export tout en une fois ─────────────────────────────────────────────────

def export_all(palette_set: PaletteSet, output_dir: str) -> Dict[str, str]:
    """Exporte tous les formats disponibles. Retourne {format: path}."""
    os.makedirs(output_dir, exist_ok=True)
    paths = {}
    paths["json"]   = export_json(palette_set, output_dir)
    paths["tokens"] = export_tokens(palette_set, output_dir)
    paths["svg"]    = export_svg(palette_set, output_dir)
    png = export_png(palette_set, output_dir)
    if png:
        paths["png"] = png
    return paths
