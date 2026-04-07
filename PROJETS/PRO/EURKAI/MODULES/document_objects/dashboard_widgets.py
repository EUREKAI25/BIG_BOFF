"""
dashboard_widgets — Dashboard Intelligence Layer for EURKAI.

Visualization types:
    kpi_card    — single metric with trend indicator
    line_chart  — time series, multi-series SVG
    bar_chart   — comparison, grouped bars SVG
    pie_chart   — distribution, donut SVG
    table       — tabular records, data-driven
    list        — ranked list with progress bars
    funnel      — pipeline / conversion stages

Low-level data model:
    DataPoint(label, value, dimension, series, meta, previous_value, unit)
    DataSeries(name, points, color)

Business data model (first-class objects):
    Metric(name, value, unit, trend, trend_pct, trend_label)
    Dataset(name, dimension, labels, values, series)

Mapping engine:
    auto_detect_type(points) → VisualizationType

Objects:
    WidgetConfig        — configuration per widget
    DashboardWidget     — widget owning its render()
    WidgetSection       — section containing multiple widgets (used in DashboardPage)
"""
from __future__ import annotations

import colorsys
import math
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# ── Type alias ────────────────────────────────────────────────────────────────

VisualizationType = Literal[
    "kpi_card", "line_chart", "bar_chart", "pie_chart", "table", "list", "funnel"
]

# ── Data schema ───────────────────────────────────────────────────────────────

class DataPoint(BaseModel):
    """
    Atomic data unit for dashboard widgets.

    dimension   — semantic meaning of the point:
        time        → implies sequential ordering (use line_chart)
        stage       → implies funnel progression
        category    → comparison or distribution
        entity      → named entity (person, project, product…)
        geography   → geographic label

    series      — group multiple DataPoints into one series for multi-line/grouped-bar charts
    meta        — arbitrary extra fields (used by table widget as extra columns)
    """
    label: str
    value: float
    dimension: Literal["time", "category", "entity", "stage", "geography"] = "category"
    series: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    previous_value: Optional[float] = None    # for trend arrow in kpi_card
    unit: Optional[str] = None


class DataSeries(BaseModel):
    """Named series — convenience wrapper to build multiple DataPoints at once."""
    name: str
    points: List[DataPoint]
    color: Optional[str] = None


# ── Mapping engine ─────────────────────────────────────────────────────────────

def auto_detect_type(points: List[DataPoint]) -> VisualizationType:
    """
    Infer the best visualization type from data semantics.

    Rules:
        - single point                  → kpi_card
        - any dimension == "time"       → line_chart
        - any dimension == "stage"      → funnel
        - multiple named series         → bar_chart (grouped comparison)
        - ≤ 6 points, no named series   → pie_chart (distribution)
        - points have meta fields       → table
        - 7-15 points                   → bar_chart
        - > 15 points                   → list
    """
    if not points:
        return "kpi_card"
    if len(points) == 1:
        return "kpi_card"

    dimensions = {p.dimension for p in points}

    if "time" in dimensions:
        return "line_chart"
    if "stage" in dimensions:
        return "funnel"

    series_names = {p.series for p in points if p.series}
    if len(series_names) > 1:
        return "bar_chart"

    if any(p.meta for p in points):
        return "table"

    if len(points) <= 6 and not series_names:
        return "pie_chart"

    if len(points) <= 15:
        return "bar_chart"

    return "list"


# ── Widget config ──────────────────────────────────────────────────────────────

class WidgetConfig(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    height: int = 220
    show_legend: bool = True
    show_labels: bool = True
    show_grid: bool = True
    unit: Optional[str] = None
    format: Literal["number", "percent", "currency", "duration"] = "number"
    trend_label: Optional[str] = None          # e.g. "vs mois précédent"
    columns: Optional[List[str]] = None        # column headers for table widget
    max_items: Optional[int] = None            # cap visible rows/items
    color_scheme: Literal["primary", "accent", "gradient", "categorical"] = "gradient"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hex_to_hsv(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0.6, 0.7, 0.5)
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return colorsys.rgb_to_hsv(r, g, b)


def _hsv_to_hex(h, s, v) -> str:
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _chart_colors(accent: str, primary: str, n: int) -> List[str]:
    """Generate n visually distinct colors derived from the palette accent."""
    if n == 0:
        return []
    h, s, v = _hex_to_hsv(accent)
    s = max(0.50, min(s, 0.85))
    v = max(0.55, min(v, 0.90))
    colors = []
    for i in range(n):
        hue = (h + i * (1.0 / n)) % 1.0
        colors.append(_hsv_to_hex(hue, s, v))
    return colors


def _fmt_value(value: float, fmt: str = "number", unit: str = "") -> str:
    if fmt == "percent":
        return f"{value:.1f}%"
    if fmt == "currency":
        formatted = f"{value:,.0f}".replace(",", "\u202f")
        return f"{formatted}\u202f€"
    if fmt == "duration":
        return f"{value/60:.1f}h" if value >= 60 else f"{value:.0f}m"
    # number
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.1f}k"
    s = f"{value:,.0f}".replace(",", "\u202f")
    return f"{s}\u202f{unit}".rstrip() if unit else s


# ── DashboardWidget ───────────────────────────────────────────────────────────

class DashboardWidget(BaseModel):
    """
    Autonomous dashboard visualization object.

    Each widget owns its render() method — no adapter layer.
    The type is auto-detected from data if not specified.

    Usage:
        w = DashboardWidget(
            data=[
                DataPoint(label="Jan", value=120, dimension="time"),
                DataPoint(label="Fév", value=145, dimension="time"),
                DataPoint(label="Mar", value=132, dimension="time"),
            ],
            config=WidgetConfig(title="Visites", format="number"),
            design={"palette": {"accent": "#6366f1"}},
        )
        html = w.render()
    """
    type: Optional[VisualizationType] = None
    data: List[DataPoint] = Field(default_factory=list)
    config: WidgetConfig = Field(default_factory=WidgetConfig)
    design: Optional[Dict[str, Any]] = None

    model_config = {"arbitrary_types_allowed": True}

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _resolved_type(self) -> VisualizationType:
        return self.type or auto_detect_type(self.data)

    def _pal(self) -> Dict[str, str]:
        raw = (self.design or {}).get("palette", {})
        return {
            "primary":  raw.get("primary",    "#0f172a"),
            "accent":   raw.get("accent",     "#6366f1"),
            "bg":       raw.get("background", "#ffffff"),
            "text":     raw.get("text",       "#1e293b"),
            "muted":    raw.get("muted",      "#64748b"),
            "surface":  raw.get("surface",    "#f8fafc"),
            "border":   raw.get("border",     "#e2e8f0"),
        }

    def _font(self) -> str:
        return (self.design or {}).get("typography", {}).get(
            "body_font", "Inter, system-ui, sans-serif"
        )

    def _mono(self) -> str:
        return (self.design or {}).get("typography", {}).get(
            "mono_font", "'JetBrains Mono', 'Courier New', monospace"
        )

    def _colors(self, n: int) -> List[str]:
        p = self._pal()
        return _chart_colors(p["accent"], p["primary"], n)

    def _fmt(self, v: float) -> str:
        return _fmt_value(v, self.config.format, self.config.unit or "")

    def _card_shell(self, content: str, accent_override: Optional[str] = None) -> str:
        p = self._pal()
        font = self._font()
        accent = accent_override or p["accent"]
        return (
            f'<div style="padding:16px 18px; background:{p["bg"]}; '
            f'border:1px solid {p["border"]}; border-radius:10px; '
            f'border-top:3px solid {accent}; font-family:{font};">'
            f'{content}'
            f'</div>'
        )

    def _section_title(self, text: str, p: dict, font: str) -> str:
        return (
            f'<p style="font-size:11px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.1em; color:{p["muted"]}; margin:0 0 10px; font-family:{font};">'
            f'{text}</p>'
        )

    # ── Render dispatcher ──────────────────────────────────────────────────────

    def render(self) -> str:
        t = self._resolved_type()
        dispatch = {
            "kpi_card":   self._render_kpi_card,
            "line_chart": self._render_line_chart,
            "bar_chart":  self._render_bar_chart,
            "pie_chart":  self._render_pie_chart,
            "table":      self._render_table,
            "list":       self._render_list,
            "funnel":     self._render_funnel,
        }
        return dispatch[t]()

    # ── KPI Card ───────────────────────────────────────────────────────────────

    def _render_kpi_card(self) -> str:
        p = self._pal()
        font = self._font()
        mono = self._mono()
        cfg = self.config

        if not self.data:
            return self._card_shell(
                f'<p style="color:{p["muted"]}; font-size:12px; margin:0;">—</p>'
            )

        pt = self.data[0]
        val = self._fmt(pt.value)
        unit_str = cfg.unit or pt.unit or ""

        title_text = cfg.title or pt.label
        title_html = (
            f'<p style="font-size:11px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.1em; color:{p["muted"]}; margin:0 0 12px; font-family:{font};">'
            f'{title_text}</p>'
        ) if title_text else ""

        subtitle_html = ""
        if cfg.subtitle:
            subtitle_html = (
                f'<p style="font-size:12px; color:{p["muted"]}; margin:0 0 6px; font-family:{font};">'
                f'{cfg.subtitle}</p>'
            )

        unit_html = (
            f'<span style="font-size:14px; font-weight:400; color:{p["muted"]}; '
            f'margin-left:3px;">{unit_str}</span>'
        ) if unit_str else ""

        value_html = (
            f'<div style="font-family:{mono}; font-size:30px; font-weight:900; '
            f'color:{p["primary"]}; letter-spacing:-.03em; line-height:1;">'
            f'{val}{unit_html}</div>'
        )

        trend_html = ""
        if pt.previous_value is not None and pt.previous_value != 0:
            delta = pt.value - pt.previous_value
            pct = delta / pt.previous_value * 100
            is_up = delta >= 0
            color = "#22c55e" if is_up else "#ef4444"
            arrow = "↑" if is_up else "↓"
            label = cfg.trend_label or "vs période préc."
            trend_html = (
                f'<div style="display:flex; align-items:center; gap:6px; margin-top:10px;">'
                f'<span style="font-size:13px; font-weight:700; color:{color}; font-family:{font};">'
                f'{arrow} {abs(pct):.1f}%</span>'
                f'<span style="font-size:11px; color:{p["muted"]}; font-family:{font};">{label}</span>'
                f'</div>'
            )

        return self._card_shell(
            title_html + subtitle_html + value_html + trend_html
        )

    # ── Line Chart ─────────────────────────────────────────────────────────────

    def _render_line_chart(self) -> str:
        p = self._pal()
        font = self._font()
        cfg = self.config

        if not self.data:
            return self._card_shell(
                f'<p style="color:{p["muted"]}; font-size:12px; margin:0;">No data</p>'
            )

        # Group by series
        series_map: Dict[str, List[DataPoint]] = {}
        for pt in self.data:
            key = pt.series or "_default"
            series_map.setdefault(key, []).append(pt)

        n_series = len(series_map)
        colors = self._colors(n_series)

        W, H = 500, 190
        PL, PR, PT, PB = 54, 18, 18, 38

        all_values = [pt.value for pt in self.data]
        min_v, max_v = min(all_values), max(all_values)
        v_range = max_v - min_v or 1
        chart_w = W - PL - PR
        chart_h = H - PT - PB

        def sx(i, n): return PL + (i / max(n - 1, 1)) * chart_w
        def sy(v): return PT + chart_h - ((v - min_v) / v_range) * chart_h

        # Grid + Y labels
        grid_svg = ""
        if cfg.show_grid:
            for gi in range(5):
                gy = PT + (gi / 4) * chart_h
                gv = max_v - (gi / 4) * v_range
                grid_svg += (
                    f'<line x1="{PL}" y1="{gy:.1f}" x2="{W - PR}" y2="{gy:.1f}" '
                    f'stroke="{p["border"]}" stroke-width="1" stroke-dasharray="3,3"/>'
                    f'<text x="{PL - 6}" y="{gy + 3.5:.1f}" text-anchor="end" '
                    f'font-size="9" fill="{p["muted"]}" font-family="{font}">'
                    f'{self._fmt(gv)}</text>'
                )

        # X labels
        x_labels_svg = ""
        first_pts = list(series_map.values())[0]
        n_pts = len(first_pts)
        x_step = max(1, n_pts // 7)
        for i, pt in enumerate(first_pts):
            if i == 0 or i == n_pts - 1 or i % x_step == 0:
                lbl = pt.label[:9] + "…" if len(pt.label) > 10 else pt.label
                x_labels_svg += (
                    f'<text x="{sx(i, n_pts):.1f}" y="{H - 6}" text-anchor="middle" '
                    f'font-size="9" fill="{p["muted"]}" font-family="{font}">{lbl}</text>'
                )

        # Series paths + dots
        series_svg = ""
        for ci, (sname, pts) in enumerate(series_map.items()):
            color = colors[ci]
            n = len(pts)
            coords = [(sx(i, n), sy(pt.value)) for i, pt in enumerate(pts)]
            pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)

            # Area fill
            area_pts = (
                f"{PL:.1f},{PT + chart_h:.1f} "
                + pts_str
                + f" {coords[-1][0]:.1f},{PT + chart_h:.1f}"
            )
            series_svg += (
                f'<polygon points="{area_pts}" fill="{color}" fill-opacity="0.07"/>'
                f'<polyline points="{pts_str}" fill="none" stroke="{color}" '
                f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
            )

            # Dots
            show_all_dots = n <= 14
            for i, (dx, dy) in enumerate(coords):
                if show_all_dots or i == 0 or i == n - 1:
                    series_svg += (
                        f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="3.5" '
                        f'fill="{p["bg"]}" stroke="{color}" stroke-width="2"/>'
                    )

        # Legend
        legend_svg = ""
        if cfg.show_legend and n_series > 1:
            lx = PL
            for ci, sname in enumerate(series_map):
                if sname != "_default":
                    color = colors[ci]
                    legend_svg += (
                        f'<rect x="{lx:.0f}" y="{H - 3}" width="12" height="3" '
                        f'rx="1.5" fill="{color}"/>'
                        f'<text x="{lx + 16:.0f}" y="{H:.0f}" font-size="9" '
                        f'fill="{p["muted"]}" font-family="{font}">{sname}</text>'
                    )
                    lx += max(len(sname) * 6.5 + 22, 60)

        title_html = self._section_title(cfg.title, p, font) if cfg.title else ""
        svg = (
            f'<svg viewBox="0 0 {W} {H}" style="width:100%; height:{cfg.height}px; display:block;" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'{grid_svg}{x_labels_svg}{series_svg}{legend_svg}'
            f'</svg>'
        )
        return self._card_shell(title_html + svg)

    # ── Bar Chart ──────────────────────────────────────────────────────────────

    def _render_bar_chart(self) -> str:
        p = self._pal()
        font = self._font()
        cfg = self.config

        if not self.data:
            return self._card_shell(
                f'<p style="color:{p["muted"]}; font-size:12px; margin:0;">No data</p>'
            )

        series_map: Dict[str, List[DataPoint]] = {}
        for pt in self.data:
            key = pt.series or "_default"
            series_map.setdefault(key, []).append(pt)

        n_series = len(series_map)
        colors = self._colors(n_series)
        group_labels = [pt.label for pt in list(series_map.values())[0]]
        n_groups = len(group_labels)

        W, H = 500, 190
        PL, PR, PT, PB = 54, 18, 18, 38

        all_values = [pt.value for pt in self.data]
        max_v = max(all_values) if all_values else 1
        min_v = min(0.0, min(all_values))
        v_range = max_v - min_v or 1
        chart_w = W - PL - PR
        chart_h = H - PT - PB

        def sy(v): return PT + chart_h - ((v - min_v) / v_range) * chart_h
        baseline_y = sy(0)

        # Grid
        grid_svg = ""
        if cfg.show_grid:
            for gi in range(5):
                gy = PT + (gi / 4) * chart_h
                gv = max_v - (gi / 4) * v_range
                grid_svg += (
                    f'<line x1="{PL}" y1="{gy:.1f}" x2="{W - PR}" y2="{gy:.1f}" '
                    f'stroke="{p["border"]}" stroke-width="1" stroke-dasharray="3,3"/>'
                    f'<text x="{PL - 6}" y="{gy + 3.5:.1f}" text-anchor="end" '
                    f'font-size="9" fill="{p["muted"]}" font-family="{font}">'
                    f'{self._fmt(gv)}</text>'
                )

        # Bars
        group_w = chart_w / max(n_groups, 1)
        gap_ratio = 0.20
        total_bar_w = group_w * (1 - gap_ratio)
        single_bar_w = total_bar_w / n_series

        bars_svg = ""
        label_svg = ""

        for gi, label in enumerate(group_labels):
            group_x = PL + gi * group_w + (group_w * gap_ratio / 2)
            for si, (sname, pts) in enumerate(series_map.items()):
                if gi >= len(pts):
                    continue
                pt = pts[gi]
                bx = group_x + si * single_bar_w
                top_y = min(sy(pt.value), baseline_y)
                bh = abs(sy(pt.value) - baseline_y)
                color = colors[si]
                rx = min(3.0, single_bar_w * 0.25)
                bars_svg += (
                    f'<rect x="{bx:.1f}" y="{top_y:.1f}" '
                    f'width="{max(single_bar_w - 1, 1):.1f}" '
                    f'height="{max(bh, 1.5):.1f}" rx="{rx:.1f}" '
                    f'fill="{color}" fill-opacity="0.88"/>'
                )
                if cfg.show_labels and bh > 16:
                    bars_svg += (
                        f'<text x="{bx + (single_bar_w - 1) / 2:.1f}" y="{top_y - 3:.1f}" '
                        f'text-anchor="middle" font-size="8" fill="{p["muted"]}" '
                        f'font-family="{font}">{self._fmt(pt.value)}</text>'
                    )

            lbl = label[:8] + "…" if len(label) > 9 else label
            label_svg += (
                f'<text x="{PL + gi * group_w + group_w / 2:.1f}" y="{H - 6}" '
                f'text-anchor="middle" font-size="9" fill="{p["muted"]}" '
                f'font-family="{font}">{lbl}</text>'
            )

        baseline_svg = (
            f'<line x1="{PL}" y1="{baseline_y:.1f}" x2="{W - PR}" y2="{baseline_y:.1f}" '
            f'stroke="{p["border"]}" stroke-width="1.5"/>'
        )

        # Legend
        legend_svg = ""
        if cfg.show_legend and n_series > 1:
            lx = PL
            for ci, sname in enumerate(series_map):
                if sname != "_default":
                    color = colors[ci]
                    legend_svg += (
                        f'<rect x="{lx:.0f}" y="4" width="10" height="7" rx="2" fill="{color}"/>'
                        f'<text x="{lx + 14:.0f}" y="10" font-size="9" fill="{p["muted"]}" '
                        f'font-family="{font}">{sname}</text>'
                    )
                    lx += max(len(sname) * 6.5 + 20, 55)

        title_html = self._section_title(cfg.title, p, font) if cfg.title else ""
        svg = (
            f'<svg viewBox="0 0 {W} {H}" style="width:100%; height:{cfg.height}px; display:block;" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'{grid_svg}{baseline_svg}{bars_svg}{label_svg}{legend_svg}'
            f'</svg>'
        )
        return self._card_shell(title_html + svg)

    # ── Pie / Donut Chart ──────────────────────────────────────────────────────

    def _render_pie_chart(self) -> str:
        p = self._pal()
        font = self._font()
        cfg = self.config

        if not self.data:
            return self._card_shell(
                f'<p style="color:{p["muted"]}; font-size:12px; margin:0;">No data</p>'
            )

        colors = self._colors(len(self.data))
        total = sum(pt.value for pt in self.data) or 1

        W, H = 320, 200
        cx, cy, r = 95, 100, 78

        slices_svg = ""
        start = -math.pi / 2

        for i, pt in enumerate(self.data):
            angle = 2 * math.pi * pt.value / total
            end = start + angle
            x1 = cx + r * math.cos(start)
            y1 = cy + r * math.sin(start)
            x2 = cx + r * math.cos(end)
            y2 = cy + r * math.sin(end)
            large = 1 if angle > math.pi else 0
            color = colors[i]

            slices_svg += (
                f'<path d="M {cx:.2f} {cy:.2f} L {x1:.2f} {y1:.2f} '
                f'A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f} Z" '
                f'fill="{color}" stroke="{p["bg"]}" stroke-width="2.5"/>'
            )

            # Slice label if large enough
            if angle > 0.28:
                mid = start + angle / 2
                lx = cx + r * 0.64 * math.cos(mid)
                ly = cy + r * 0.64 * math.sin(mid)
                pct = pt.value / total * 100
                slices_svg += (
                    f'<text x="{lx:.1f}" y="{ly + 3.5:.1f}" text-anchor="middle" '
                    f'font-size="9" font-weight="700" fill="white" font-family="{font}">'
                    f'{pct:.0f}%</text>'
                )
            start = end

        # Donut hole
        inner_r = int(r * 0.44)
        slices_svg += f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="{p["bg"]}"/>'

        # Center: title + total
        center_title = cfg.title or "Total"
        center_val = (
            "100%" if cfg.format == "percent" else self._fmt(sum(pt.value for pt in self.data))
        )
        slices_svg += (
            f'<text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="8" '
            f'fill="{p["muted"]}" font-family="{font}">{center_title}</text>'
            f'<text x="{cx}" y="{cy + 9}" text-anchor="middle" font-size="14" '
            f'font-weight="900" fill="{p["primary"]}" font-family="{font}">'
            f'{center_val}</text>'
        )

        # Legend
        legend_svg = ""
        if cfg.show_legend:
            n = len(self.data)
            ly_start = max(10, (H - n * 22) // 2)
            for i, pt in enumerate(self.data):
                color = colors[i]
                ly = ly_start + i * 22
                pct = pt.value / total * 100
                lbl = pt.label[:16] + "…" if len(pt.label) > 17 else pt.label
                val_str = self._fmt(pt.value)
                legend_svg += (
                    f'<rect x="198" y="{ly}" width="9" height="9" rx="2" fill="{color}"/>'
                    f'<text x="211" y="{ly + 8}" font-size="10" fill="{p["text"]}" '
                    f'font-family="{font}">{lbl}</text>'
                    f'<text x="{W - 4}" y="{ly + 8}" text-anchor="end" font-size="9" '
                    f'fill="{p["muted"]}" font-family="{font}">{val_str}</text>'
                )

        svg = (
            f'<svg viewBox="0 0 {W} {H}" style="width:100%; height:{cfg.height}px; display:block;" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'{slices_svg}{legend_svg}'
            f'</svg>'
        )
        return self._card_shell(svg)

    # ── Table ──────────────────────────────────────────────────────────────────

    def _render_table(self) -> str:
        p = self._pal()
        font = self._font()
        mono = self._mono()
        cfg = self.config

        rows = self.data[:cfg.max_items] if cfg.max_items else self.data
        columns = cfg.columns or ["Label", "Valeur"]

        title_html = ""
        if cfg.title:
            title_html = (
                f'<div style="padding:12px 16px; border-bottom:1px solid {p["border"]}; '
                f'font-family:{font};">'
                f'<p style="font-size:11px; font-weight:700; text-transform:uppercase; '
                f'letter-spacing:.1em; color:{p["muted"]}; margin:0;">{cfg.title}</p>'
                f'</div>'
            )

        header_cells = "".join(
            f'<th style="padding:9px 14px; text-align:{"right" if i > 0 else "left"}; '
            f'font-size:10px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.08em; color:rgba(255,255,255,.7); white-space:nowrap;">{col}</th>'
            for i, col in enumerate(columns)
        )

        rows_html = ""
        for ri, pt in enumerate(rows):
            bg = f"background:{p['surface']};" if ri % 2 == 1 else ""
            # Extra columns from meta
            extra = ""
            for col in columns[2:]:
                meta_val = pt.meta.get(col.lower(), pt.meta.get(col, "—"))
                extra += (
                    f'<td style="padding:9px 14px; font-size:12px; color:{p["muted"]}; '
                    f'font-family:{font};">{meta_val}</td>'
                )
            rows_html += (
                f'<tr style="{bg}">'
                f'<td style="padding:9px 14px; font-size:12px; color:{p["text"]}; '
                f'font-weight:500; font-family:{font};">{pt.label}</td>'
                f'<td style="padding:9px 14px; text-align:right; font-family:{mono}; '
                f'font-size:12px; font-weight:600; color:{p["primary"]};">{self._fmt(pt.value)}</td>'
                f'{extra}'
                f'</tr>'
            )

        return (
            f'<div style="background:{p["bg"]}; border:1px solid {p["border"]}; '
            f'border-radius:10px; overflow:hidden; border-top:3px solid {p["accent"]};">'
            f'{title_html}'
            f'<table style="width:100%; border-collapse:collapse;">'
            f'<thead><tr style="background:{p["primary"]};">{header_cells}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>'
            f'</div>'
        )

    # ── List ───────────────────────────────────────────────────────────────────

    def _render_list(self) -> str:
        p = self._pal()
        font = self._font()
        mono = self._mono()
        cfg = self.config

        items = self.data[:cfg.max_items] if cfg.max_items else self.data
        colors = self._colors(min(len(items), 6))
        max_v = max((pt.value for pt in items), default=1) or 1

        title_html = self._section_title(cfg.title, p, font) if cfg.title else ""

        rows_html = ""
        for i, pt in enumerate(items):
            color = colors[min(i, len(colors) - 1)]
            pct = pt.value / max_v * 100
            is_last = i == len(items) - 1
            border = "" if is_last else f"border-bottom:1px solid {p['border']};"
            rows_html += (
                f'<div style="display:flex; align-items:center; gap:10px; '
                f'padding:9px 0; {border}">'
                f'<span style="width:22px; font-size:11px; font-weight:700; '
                f'color:{p["muted"]}; flex-shrink:0; text-align:right;">{i + 1}</span>'
                f'<div style="flex:1; min-width:0;">'
                f'<div style="font-size:12px; color:{p["text"]}; font-weight:500; '
                f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis; '
                f'margin-bottom:4px;">{pt.label}</div>'
                f'<div style="height:3px; background:{p["border"]}; border-radius:99px; overflow:hidden;">'
                f'<div style="height:100%; width:{pct:.1f}%; background:{color}; '
                f'border-radius:99px; transition:width .3s;"></div>'
                f'</div>'
                f'</div>'
                f'<span style="font-family:{mono}; font-size:12px; font-weight:700; '
                f'color:{p["primary"]}; flex-shrink:0;">{self._fmt(pt.value)}</span>'
                f'</div>'
            )

        return self._card_shell(title_html + f'<div>{rows_html}</div>')

    # ── Funnel ─────────────────────────────────────────────────────────────────

    def _render_funnel(self) -> str:
        p = self._pal()
        font = self._font()
        mono = self._mono()
        cfg = self.config

        if not self.data:
            return self._card_shell(
                f'<p style="color:{p["muted"]}; font-size:12px; margin:0;">No data</p>'
            )

        stages = self.data
        n = len(stages)
        colors = self._colors(n)
        top_v = stages[0].value if stages[0].value else 1

        W, H = 480, max(n * 42, 160)
        FUNNEL_W = 280          # max trapezoid width
        MIN_W_RATIO = 0.20      # minimum trapezoid width ratio
        CX = 150                # center x of funnel
        PAD_T = 8
        stage_h = (H - PAD_T) / n
        bar_h = stage_h - 3     # gap between stages

        svg_parts = []

        for i, pt in enumerate(stages):
            ratio_top = pt.value / top_v if top_v else 0
            if i < n - 1:
                ratio_bot = stages[i + 1].value / top_v if top_v else 0
            else:
                ratio_bot = ratio_top * MIN_W_RATIO

            ratio_top = max(ratio_top, MIN_W_RATIO)
            ratio_bot = max(ratio_bot, MIN_W_RATIO)

            w_top = FUNNEL_W * ratio_top
            w_bot = FUNNEL_W * ratio_bot
            y_top = PAD_T + i * stage_h
            y_bot = y_top + bar_h

            x1 = CX - w_top / 2
            x2 = CX + w_top / 2
            x3 = CX + w_bot / 2
            x4 = CX - w_bot / 2

            color = colors[i]
            svg_parts.append(
                f'<polygon points="{x1:.1f},{y_top:.1f} {x2:.1f},{y_top:.1f} '
                f'{x3:.1f},{y_bot:.1f} {x4:.1f},{y_bot:.1f}" '
                f'fill="{color}" fill-opacity="0.85"/>'
            )

            # Stage name (centered)
            my = (y_top + y_bot) / 2 + 4
            lbl = pt.label[:18] + "…" if len(pt.label) > 19 else pt.label
            svg_parts.append(
                f'<text x="{CX:.1f}" y="{my:.1f}" text-anchor="middle" '
                f'font-size="10" font-weight="600" fill="white" font-family="{font}">'
                f'{lbl}</text>'
            )

            # Right side stats
            rx = CX + FUNNEL_W / 2 + 20
            svg_parts.append(
                f'<text x="{rx}" y="{my - 5:.1f}" font-size="11" font-weight="700" '
                f'fill="{p["primary"]}" font-family="{font}">'
                f'{self._fmt(pt.value)}</text>'
            )
            pct_total = pt.value / stages[0].value * 100 if stages[0].value else 0
            if i > 0:
                drop = (1 - pt.value / stages[i - 1].value) * 100 if stages[i - 1].value else 0
                sub = f"{pct_total:.0f}% total · −{drop:.0f}%"
            else:
                sub = "100%"
            svg_parts.append(
                f'<text x="{rx}" y="{my + 8:.1f}" font-size="8.5" '
                f'fill="{p["muted"]}" font-family="{font}">{sub}</text>'
            )

        svg = (
            f'<svg viewBox="0 0 {W} {H}" style="width:100%; height:{cfg.height}px; display:block;" '
            f'xmlns="http://www.w3.org/2000/svg">'
            + "".join(svg_parts) +
            f'</svg>'
        )
        title_html = self._section_title(cfg.title, p, font) if cfg.title else ""
        return self._card_shell(title_html + svg)


# ── WidgetSection ──────────────────────────────────────────────────────────────

class WidgetSection(BaseModel):
    """
    Dashboard section containing one or more DashboardWidgets.

    Plugs directly into DashboardPage.sections.
    Design tokens are inherited from DashboardPage if not set on individual widgets.

    layout:
        "grid"    → CSS grid with `columns` columns (default 2)
        "row"     → flex row, equal width
        "single"  → single widget, full width
    """
    section_type: Literal["widget_section"] = "widget_section"
    title: Optional[str] = None
    subtitle: Optional[str] = None
    widgets: List[DashboardWidget] = Field(default_factory=list)
    layout: Literal["grid", "row", "single"] = "grid"
    columns: int = 2

    def _render(self, design: Optional[Dict[str, Any]] = None) -> str:
        pal = (design or {}).get("palette", {})
        font = (design or {}).get("typography", {}).get("body_font", "Inter, system-ui, sans-serif")
        primary  = pal.get("primary", "#0f172a")
        muted    = pal.get("muted",   "#64748b")
        border_c = pal.get("border",  "#e2e8f0")

        # Inject page-level design into widgets that don't have their own
        resolved_widgets = [
            DashboardWidget(
                type=w.type,
                data=w.data,
                config=w.config,
                design=w.design if w.design is not None else design,
            )
            for w in self.widgets
        ]

        title_html = ""
        if self.title:
            subtitle_html = (
                f'<p style="font-size:12px; color:{muted}; margin:4px 0 0; font-family:{font};">'
                f'{self.subtitle}</p>'
            ) if self.subtitle else ""
            title_html = (
                f'<div style="margin-bottom:16px;">'
                f'<p style="font-size:14px; font-weight:700; color:{primary}; margin:0; '
                f'font-family:{font}; letter-spacing:-.01em;">{self.title}</p>'
                f'{subtitle_html}</div>'
            )

        if not resolved_widgets:
            content = ""
        elif self.layout == "single" or len(resolved_widgets) == 1:
            content = resolved_widgets[0].render()
        elif self.layout == "row":
            cells = "".join(
                f'<div style="flex:1; min-width:0;">{w.render()}</div>'
                for w in resolved_widgets
            )
            content = f'<div style="display:flex; gap:16px; align-items:flex-start;">{cells}</div>'
        else:  # grid
            cols = min(self.columns, len(resolved_widgets))
            cells = "".join(f'<div>{w.render()}</div>' for w in resolved_widgets)
            content = (
                f'<div style="display:grid; grid-template-columns:repeat({cols}, 1fr); gap:16px;">'
                f'{cells}</div>'
            )

        return (
            f'<div style="padding:24px 32px; border-bottom:1px solid {border_c}; '
            f'font-family:{font};">'
            f'{title_html}{content}'
            f'</div>'
        )


# ── Metric ─────────────────────────────────────────────────────────────────────

class Metric(BaseModel):
    """
    First-class business metric object.

    Produces a kpi_card DashboardWidget directly.
    trend is explicit ('up'/'down'/'neutral') — no need to supply previous_value.

    Usage:
        m = Metric(name="MRR", value=8400, unit="€", trend="up", trend_pct=17.0)
        html = m.render(design={"palette": {"accent": "#6366f1"}})
    """
    name: str
    value: float
    unit: Optional[str] = None
    trend: Literal["up", "down", "neutral"] = "neutral"
    trend_pct: Optional[float] = None          # e.g. 17.0 → "↑ 17.0%"
    trend_label: Optional[str] = None          # e.g. "vs mois précédent"
    subtitle: Optional[str] = None

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if not self.name:
            errors.append("name is required")
        if self.trend_pct is not None and self.trend_pct < 0:
            errors.append("trend_pct must be positive (use trend='down' for decrease direction)")
        return {"valid": len(errors) == 0, "errors": errors}

    def to_widget(self, design: Optional[Dict[str, Any]] = None) -> "DashboardWidget":
        # Build a synthetic DataPoint that carries trend info
        # trend_pct is encoded as previous_value so DashboardWidget can compute ↑↓
        previous_value: Optional[float] = None
        if self.trend_pct is not None and self.trend_pct != 0:
            if self.trend == "up":
                previous_value = self.value / (1 + self.trend_pct / 100)
            elif self.trend == "down":
                previous_value = self.value / (1 - abs(self.trend_pct) / 100)
            # neutral → no previous_value

        pt = DataPoint(
            label=self.name,
            value=self.value,
            unit=self.unit,
            previous_value=previous_value,
        )
        cfg = WidgetConfig(
            title=self.name,
            subtitle=self.subtitle,
            unit=self.unit,
            trend_label=self.trend_label or "vs période préc.",
        )
        return DashboardWidget(type="kpi_card", data=[pt], config=cfg, design=design)

    def render(self, design: Optional[Dict[str, Any]] = None) -> str:
        return self.to_widget(design).render()

    @classmethod
    def test(cls) -> bool:
        m = cls(name="MRR", value=8400, unit="€", trend="up", trend_pct=17.0)
        assert m.validate()["valid"] is True
        html = m.render()
        assert "MRR" in html
        assert "↑" in html
        m_down = cls(name="Churn", value=5.2, unit="%", trend="down", trend_pct=20.0)
        html2 = m_down.render()
        assert "↓" in html2
        return True


# ── Dataset ────────────────────────────────────────────────────────────────────

class Dataset(BaseModel):
    """
    First-class named dataset object.

    Separates labels from values — cleaner API than building DataPoints manually.
    Supports multi-series by combining multiple Datasets with the same labels.

    Usage:
        ds = Dataset(
            name="Visites mensuelles",
            dimension="time",
            labels=["Jan", "Fév", "Mar", "Avr"],
            values=[1200, 1450, 1380, 1600],
        )
        widget = ds.to_widget(config=WidgetConfig(title="Visites"))
        html = ds.render(design={"palette": {"accent": "#6366f1"}})
    """
    name: str
    dimension: Literal["time", "category", "entity", "stage"] = "category"
    labels: List[str]
    values: List[float]
    series: Optional[str] = None              # series name for grouped charts
    meta_columns: Optional[List[Dict[str, Any]]] = None  # extra per-row metadata for table

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if not self.name:
            errors.append("name is required")
        if not self.labels:
            errors.append("labels must not be empty")
        if not self.values:
            errors.append("values must not be empty")
        if len(self.labels) != len(self.values):
            errors.append(
                f"labels ({len(self.labels)}) and values ({len(self.values)}) must have the same length"
            )
        return {"valid": len(errors) == 0, "errors": errors}

    def to_data_points(self) -> List[DataPoint]:
        """Convert to DataPoint list consumable by DashboardWidget."""
        points = []
        for i, (label, value) in enumerate(zip(self.labels, self.values)):
            meta: Dict[str, Any] = {}
            if self.meta_columns and i < len(self.meta_columns):
                meta = self.meta_columns[i]
            points.append(DataPoint(
                label=label,
                value=value,
                dimension=self.dimension,
                series=self.series,
                meta=meta,
            ))
        return points

    def to_widget(
        self,
        viz_type: Optional[VisualizationType] = None,
        config: Optional[WidgetConfig] = None,
        design: Optional[Dict[str, Any]] = None,
    ) -> "DashboardWidget":
        pts = self.to_data_points()
        cfg = config or WidgetConfig(title=self.name)
        return DashboardWidget(type=viz_type, data=pts, config=cfg, design=design)

    def render(
        self,
        viz_type: Optional[VisualizationType] = None,
        config: Optional[WidgetConfig] = None,
        design: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self.to_widget(viz_type, config, design).render()

    @classmethod
    def combine(cls, *datasets: "Dataset") -> List[DataPoint]:
        """Merge multiple Datasets into a flat DataPoint list (for grouped charts)."""
        pts: List[DataPoint] = []
        for ds in datasets:
            pts.extend(ds.to_data_points())
        return pts

    @classmethod
    def test(cls) -> bool:
        ds = cls(
            name="Chiffre d'affaires",
            dimension="time",
            labels=["Jan", "Fév", "Mar", "Avr", "Mai", "Jun"],
            values=[7000, 7400, 6800, 8100, 8500, 9200],
        )
        assert ds.validate()["valid"] is True
        pts = ds.to_data_points()
        assert len(pts) == 6
        assert pts[0].dimension == "time"
        assert pts[2].label == "Mar"
        assert pts[2].value == 6800

        w = ds.to_widget()
        assert w._resolved_type() == "line_chart"
        html = ds.render()
        assert "<polyline" in html

        # Stage dataset → funnel
        funnel_ds = cls(
            name="Pipeline",
            dimension="stage",
            labels=["Leads", "Qualifiés", "Signés"],
            values=[300, 120, 45],
        )
        assert funnel_ds.to_widget()._resolved_type() == "funnel"

        # Combine multi-series
        ds_a = cls(name="A", dimension="category", labels=["X", "Y"], values=[10, 20], series="Série A")
        ds_b = cls(name="B", dimension="category", labels=["X", "Y"], values=[15, 25], series="Série B")
        combined = cls.combine(ds_a, ds_b)
        assert len(combined) == 4
        assert combined[0].series == "Série A"
        assert combined[2].series == "Série B"

        return True
