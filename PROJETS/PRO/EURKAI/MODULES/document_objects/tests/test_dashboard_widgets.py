"""
Tests for dashboard_widgets — Dashboard Intelligence Layer.
Covers: DataPoint, auto_detect_type, all 7 widget types, WidgetSection,
DashboardPage integration.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from document_objects import (
    DataPoint, DataSeries, WidgetConfig, DashboardWidget, WidgetSection,
    auto_detect_type,
    Metric, Dataset,
    DashboardPage, DashboardPageInput,
    NavItem, StatCard,
)

DESIGN = {
    "palette": {
        "primary": "#0f172a",
        "accent": "#6366f1",
        "muted": "#64748b",
        "border": "#e2e8f0",
        "surface": "#f8fafc",
        "background": "#f1f5f9",
    },
    "typography": {"body_font": "Inter, sans-serif"},
}


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _time_series(n=8, base=100, step=15):
    return [DataPoint(label=f"M{i}", value=base + i * step, dimension="time") for i in range(n)]


def _categories(items=None):
    items = items or [("Dev", 45), ("Design", 30), ("Conseil", 25)]
    return [DataPoint(label=l, value=v) for l, v in items]


def _stages():
    return [
        DataPoint(label="Leads",       value=500, dimension="stage"),
        DataPoint(label="Qualifiés",   value=200, dimension="stage"),
        DataPoint(label="Propositions",value=90,  dimension="stage"),
        DataPoint(label="Signés",      value=40,  dimension="stage"),
    ]


def _kpi(val=8400, prev=7200):
    return [DataPoint(label="MRR", value=val, previous_value=prev)]


def _ranked(n=10):
    return [DataPoint(label=f"Item {i}", value=(n - i) * 100) for i in range(n)]


def _table_data():
    return [
        DataPoint(label="EURKAI", value=12000, meta={"statut": "Actif", "client": "SAS"}),
        DataPoint(label="Présence IA", value=8500, meta={"statut": "En cours", "client": "Auto"}),
    ]


def _multi_series():
    data = []
    for month in ["Jan", "Fév", "Mar", "Avr"]:
        data.append(DataPoint(label=month, value=80 + hash(month) % 40, series="Produit A"))
        data.append(DataPoint(label=month, value=60 + hash(month) % 30, series="Produit B"))
    return data


# ── DataPoint ──────────────────────────────────────────────────────────────────

class TestDataPoint:
    def test_defaults(self):
        p = DataPoint(label="X", value=42)
        assert p.dimension == "category"
        assert p.series is None
        assert p.meta == {}
        assert p.previous_value is None

    def test_all_dimensions(self):
        for dim in ["time", "category", "entity", "stage", "geography"]:
            p = DataPoint(label="X", value=1, dimension=dim)
            assert p.dimension == dim

    def test_with_meta(self):
        p = DataPoint(label="X", value=10, meta={"status": "active", "count": 3})
        assert p.meta["status"] == "active"

    def test_with_series(self):
        p = DataPoint(label="Jan", value=100, series="Série A")
        assert p.series == "Série A"


# ── auto_detect_type ───────────────────────────────────────────────────────────

class TestAutoDetectType:
    def test_empty_returns_kpi(self):
        assert auto_detect_type([]) == "kpi_card"

    def test_single_returns_kpi(self):
        assert auto_detect_type([DataPoint(label="X", value=1)]) == "kpi_card"

    def test_time_dimension_returns_line(self):
        assert auto_detect_type(_time_series()) == "line_chart"

    def test_stage_dimension_returns_funnel(self):
        assert auto_detect_type(_stages()) == "funnel"

    def test_few_categories_returns_pie(self):
        result = auto_detect_type(_categories())
        assert result == "pie_chart"

    def test_multi_series_returns_bar(self):
        assert auto_detect_type(_multi_series()) == "bar_chart"

    def test_many_points_returns_list(self):
        pts = [DataPoint(label=f"X{i}", value=i) for i in range(20)]
        assert auto_detect_type(pts) == "list"

    def test_meta_data_returns_table(self):
        assert auto_detect_type(_table_data()) == "table"

    def test_mid_range_returns_bar(self):
        pts = [DataPoint(label=f"C{i}", value=i * 10) for i in range(8)]
        assert auto_detect_type(pts) == "bar_chart"


# ── DashboardWidget — KPI Card ─────────────────────────────────────────────────

class TestKpiCard:
    def _w(self, **kwargs):
        return DashboardWidget(type="kpi_card", data=_kpi(), design=DESIGN, **kwargs)

    def test_renders_value(self):
        html = self._w().render()
        assert "8" in html  # 8400 → "8.4k" or similar

    def test_renders_trend_up(self):
        html = self._w().render()
        assert "↑" in html

    def test_renders_trend_down(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="Users", value=100, previous_value=120)],
            design=DESIGN,
        )
        assert "↓" in w.render()

    def test_renders_label(self):
        assert "MRR" in self._w().render()

    def test_renders_title_override(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=42)],
            config=WidgetConfig(title="Mon KPI"),
            design=DESIGN,
        )
        assert "Mon KPI" in w.render()

    def test_renders_unit(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=42, unit="j")],
            design=DESIGN,
        )
        assert "j" in w.render()

    def test_no_trend_without_previous(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=100)],
            design=DESIGN,
        )
        html = w.render()
        assert "↑" not in html and "↓" not in html

    def test_empty_data_renders(self):
        w = DashboardWidget(type="kpi_card", data=[], design=DESIGN)
        assert w.render() != ""

    def test_format_percent(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="Taux", value=87.5)],
            config=WidgetConfig(format="percent"),
            design=DESIGN,
        )
        assert "87.5%" in w.render()

    def test_format_currency(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="CA", value=12000)],
            config=WidgetConfig(format="currency"),
            design=DESIGN,
        )
        assert "€" in w.render()


# ── DashboardWidget — Line Chart ───────────────────────────────────────────────

class TestLineChart:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="line_chart", data=_time_series(), design=DESIGN, **kwargs
        )

    def test_renders_polyline(self):
        assert "<polyline" in self._w().render()

    def test_renders_area(self):
        assert "<polygon" in self._w().render()

    def test_renders_dots(self):
        assert "<circle" in self._w().render()

    def test_renders_title(self):
        w = self._w(config=WidgetConfig(title="Visites"))
        assert "Visites" in w.render()

    def test_renders_grid(self):
        assert "<line" in self._w().render()

    def test_no_grid_when_disabled(self):
        w = self._w(config=WidgetConfig(show_grid=False))
        html = w.render()
        assert "stroke-dasharray" not in html

    def test_multi_series(self):
        w = DashboardWidget(
            type="line_chart", data=_multi_series(), design=DESIGN,
            config=WidgetConfig(title="Multi"),
        )
        html = w.render()
        assert html.count("<polyline") >= 2

    def test_single_point_renders(self):
        w = DashboardWidget(
            type="line_chart",
            data=[DataPoint(label="Jan", value=100, dimension="time")],
            design=DESIGN,
        )
        assert w.render() != ""

    def test_svg_viewbox(self):
        assert 'viewBox="0 0 500' in self._w().render()


# ── DashboardWidget — Bar Chart ────────────────────────────────────────────────

class TestBarChart:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="bar_chart", data=_categories(), design=DESIGN, **kwargs
        )

    def test_renders_rects(self):
        assert "<rect" in self._w().render()

    def test_renders_title(self):
        w = self._w(config=WidgetConfig(title="Budget"))
        assert "Budget" in w.render()

    def test_renders_labels(self):
        html = self._w().render()
        assert "Dev" in html

    def test_grouped_bars(self):
        w = DashboardWidget(
            type="bar_chart", data=_multi_series(), design=DESIGN,
            config=WidgetConfig(show_legend=True),
        )
        html = w.render()
        assert html.count("<rect") >= 4  # at least 4 bars (2 series × 2+ groups)

    def test_legend_shown_for_multi_series(self):
        w = DashboardWidget(type="bar_chart", data=_multi_series(), design=DESIGN)
        html = w.render()
        assert "Produit A" in html or "Produit B" in html

    def test_value_labels(self):
        w = DashboardWidget(
            type="bar_chart",
            data=[DataPoint(label="X", value=1000)],
            config=WidgetConfig(show_labels=True),
            design=DESIGN,
        )
        assert "1" in w.render()

    def test_baseline_line(self):
        assert "<line" in self._w().render()


# ── DashboardWidget — Pie Chart ────────────────────────────────────────────────

class TestPieChart:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="pie_chart", data=_categories(), design=DESIGN, **kwargs
        )

    def test_renders_paths(self):
        assert "<path" in self._w().render()

    def test_renders_donut_hole(self):
        assert "<circle" in self._w().render()

    def test_renders_legend(self):
        html = self._w().render()
        assert "Dev" in html

    def test_pct_labels_on_large_slices(self):
        w = DashboardWidget(
            type="pie_chart",
            data=[DataPoint(label="A", value=70), DataPoint(label="B", value=30)],
            design=DESIGN,
        )
        assert "%" in w.render()

    def test_center_total(self):
        w = DashboardWidget(
            type="pie_chart",
            data=_categories(),
            config=WidgetConfig(title="Total"),
            design=DESIGN,
        )
        assert "Total" in w.render()

    def test_single_slice(self):
        w = DashboardWidget(
            type="pie_chart",
            data=[DataPoint(label="Only", value=100)],
            design=DESIGN,
        )
        assert w.render() != ""


# ── DashboardWidget — Table ────────────────────────────────────────────────────

class TestTableWidget:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="table", data=_table_data(), design=DESIGN,
            config=WidgetConfig(title="Projets", columns=["Projet", "CA", "Statut", "Client"]),
            **kwargs,
        )

    def test_renders_rows(self):
        html = self._w().render()
        assert "EURKAI" in html
        assert "Présence IA" in html

    def test_renders_meta_columns(self):
        html = self._w().render()
        assert "Actif" in html

    def test_renders_header(self):
        html = self._w().render()
        assert "Projet" in html

    def test_renders_title(self):
        assert "Projets" in self._w().render()

    def test_max_items(self):
        data = [DataPoint(label=f"Row {i}", value=i) for i in range(10)]
        w = DashboardWidget(
            type="table", data=data,
            config=WidgetConfig(max_items=3),
            design=DESIGN,
        )
        html = w.render()
        assert "Row 0" in html
        assert "Row 9" not in html

    def test_table_html_structure(self):
        html = self._w().render()
        assert "<table" in html
        assert "<thead" in html
        assert "<tbody" in html


# ── DashboardWidget — List ─────────────────────────────────────────────────────

class TestListWidget:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="list", data=_ranked(), design=DESIGN,
            config=WidgetConfig(title="Top items"),
            **kwargs,
        )

    def test_renders_items(self):
        html = self._w().render()
        assert "Item 0" in html

    def test_renders_rank_numbers(self):
        html = self._w().render()
        assert ">1<" in html

    def test_renders_progress_bars(self):
        html = self._w().render()
        assert "width:" in html and "%" in html

    def test_renders_title(self):
        assert "Top items" in self._w().render()

    def test_max_items(self):
        w = DashboardWidget(
            type="list", data=_ranked(10),
            config=WidgetConfig(max_items=5),
            design=DESIGN,
        )
        html = w.render()
        assert "Item 0" in html
        assert "Item 9" not in html


# ── DashboardWidget — Funnel ───────────────────────────────────────────────────

class TestFunnelWidget:
    def _w(self, **kwargs):
        return DashboardWidget(
            type="funnel", data=_stages(), design=DESIGN,
            config=WidgetConfig(title="Pipeline"),
            **kwargs,
        )

    def test_renders_polygons(self):
        assert "<polygon" in self._w().render()

    def test_renders_stage_labels(self):
        html = self._w().render()
        assert "Leads" in html
        assert "Signés" in html

    def test_renders_values(self):
        html = self._w().render()
        assert "500" in html or "0.5k" in html

    def test_renders_conversion(self):
        html = self._w().render()
        assert "%" in html

    def test_renders_title(self):
        assert "Pipeline" in self._w().render()

    def test_n_stages_equals_n_polygons(self):
        stages = _stages()
        html = self._w().render()
        assert html.count("<polygon") == len(stages)


# ── WidgetSection ──────────────────────────────────────────────────────────────

class TestWidgetSection:
    def _section(self, layout="grid", **kwargs):
        return WidgetSection(
            title="Performances",
            widgets=[
                DashboardWidget(type="kpi_card", data=_kpi()),
                DashboardWidget(type="bar_chart", data=_categories()),
            ],
            layout=layout,
            **kwargs,
        )

    def test_grid_layout(self):
        html = self._section("grid")._render(DESIGN)
        assert "grid-template-columns" in html

    def test_row_layout(self):
        html = self._section("row")._render(DESIGN)
        assert "display:flex" in html

    def test_single_layout(self):
        sec = WidgetSection(
            widgets=[DashboardWidget(type="kpi_card", data=_kpi())],
            layout="single",
        )
        assert sec._render(DESIGN) != ""

    def test_title_rendered(self):
        html = self._section()._render(DESIGN)
        assert "Performances" in html

    def test_subtitle_rendered(self):
        sec = WidgetSection(
            title="T", subtitle="Sous-titre",
            widgets=[DashboardWidget(type="kpi_card", data=_kpi())],
        )
        assert "Sous-titre" in sec._render(DESIGN)

    def test_design_propagated_to_widgets(self):
        """Widgets without own design should inherit page design."""
        sec = WidgetSection(
            widgets=[DashboardWidget(type="kpi_card", data=_kpi())],
        )
        html = sec._render(DESIGN)
        assert "#6366f1" in html  # accent from DESIGN

    def test_own_widget_design_not_overridden(self):
        custom = {"palette": {"accent": "#ff0000"}}
        sec = WidgetSection(
            widgets=[DashboardWidget(type="kpi_card", data=_kpi(), design=custom)],
        )
        html = sec._render(DESIGN)
        assert "#ff0000" in html

    def test_columns_config(self):
        sec = WidgetSection(
            widgets=[DashboardWidget(type="kpi_card", data=_kpi())] * 3,
            columns=3,
        )
        assert "repeat(3, 1fr)" in sec._render(DESIGN)

    def test_empty_widgets_renders(self):
        sec = WidgetSection(widgets=[])
        assert sec._render(DESIGN) != ""


# ── DashboardPage integration ──────────────────────────────────────────────────

class TestDashboardPageWithWidgets:
    def _page(self):
        return DashboardPage(DashboardPageInput(
            title="Analytics",
            user_name="Nathalie",
            design=DESIGN,
            nav_items=[NavItem(label="Dashboard", href="#", active=True)],
            stat_cards=[StatCard(title="MRR", value="8 400 €", subtitle="↑ 17%")],
            sections=[
                WidgetSection(
                    title="Métriques",
                    widgets=[
                        DashboardWidget(type="kpi_card", data=_kpi()),
                        DashboardWidget(type="line_chart", data=_time_series()),
                        DashboardWidget(type="pie_chart", data=_categories()),
                    ],
                    columns=3,
                ),
                WidgetSection(
                    title="Pipeline",
                    layout="single",
                    widgets=[DashboardWidget(type="funnel", data=_stages())],
                ),
            ],
        ))

    def test_validate(self):
        assert self._page().validate()["valid"] is True

    def test_render_contains_title(self):
        assert "Analytics" in self._page().render()

    def test_render_contains_user(self):
        assert "Nathalie" in self._page().render()

    def test_render_contains_widget_section_title(self):
        assert "Métriques" in self._page().render()

    def test_render_contains_charts(self):
        html = self._page().render()
        assert "<polyline" in html
        assert "<path" in html
        assert "<polygon" in html

    def test_render_valid_html(self):
        html = self._page().render()
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_no_design_still_renders(self):
        page = DashboardPage(DashboardPageInput(
            title="Test",
            sections=[
                WidgetSection(
                    widgets=[DashboardWidget(type="bar_chart", data=_categories())],
                )
            ],
        ))
        html = page.render()
        assert "<rect" in html

    def test_mixed_section_types(self):
        """WidgetSection and legacy sections coexist."""
        from document_objects import TableSection
        page = DashboardPage(DashboardPageInput(
            title="Mixed",
            design=DESIGN,
            sections=[
                TableSection(
                    columns=["A", "B"],
                    rows=[["x", "y"]],
                ),
                WidgetSection(
                    widgets=[DashboardWidget(type="kpi_card", data=_kpi())],
                ),
            ],
        ))
        html = page.render()
        assert "<table" in html
        assert "8" in html  # kpi value


# ── Format helpers ─────────────────────────────────────────────────────────────

class TestFormatHelpers:
    def _w(self, fmt):
        return DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=12345.67)],
            config=WidgetConfig(format=fmt),
            design=DESIGN,
        )

    def test_number_format_k(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=12000)],
            config=WidgetConfig(format="number"),
            design=DESIGN,
        )
        assert "12" in w.render()

    def test_percent_format(self):
        assert "%" in self._w("percent").render()

    def test_currency_format(self):
        assert "€" in self._w("currency").render()

    def test_duration_hours(self):
        w = DashboardWidget(
            type="kpi_card",
            data=[DataPoint(label="X", value=120)],
            config=WidgetConfig(format="duration"),
            design=DESIGN,
        )
        assert "h" in w.render()


# ── TestMetric ─────────────────────────────────────────────────────────────────

class TestMetric:

    def test_validate_valid(self):
        m = Metric(name="MRR", value=8400, unit="€", trend="up", trend_pct=17.0)
        result = m.validate()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_missing_name(self):
        m = Metric(name="", value=100)
        result = m.validate()
        assert result["valid"] is False
        assert any("name" in e for e in result["errors"])

    def test_validate_invalid_trend_pct(self):
        m = Metric(name="X", value=100, trend_pct=-5.0)
        result = m.validate()
        assert result["valid"] is False

    def test_to_widget_returns_kpi_card(self):
        m = Metric(name="CAC", value=120, unit="€", trend="down", trend_pct=10.0)
        w = m.to_widget(design=DESIGN)
        assert w.type == "kpi_card"
        assert len(w.data) == 1

    def test_to_widget_up_trend_sets_previous_value(self):
        m = Metric(name="Revenue", value=10000, trend="up", trend_pct=25.0)
        w = m.to_widget()
        pt = w.data[0]
        assert pt.previous_value is not None
        assert pt.previous_value < pt.value

    def test_to_widget_down_trend_sets_previous_value(self):
        m = Metric(name="Churn", value=5.0, trend="down", trend_pct=20.0)
        w = m.to_widget()
        pt = w.data[0]
        assert pt.previous_value is not None
        assert pt.previous_value > pt.value

    def test_to_widget_neutral_no_previous_value(self):
        m = Metric(name="Score", value=77, trend="neutral")
        w = m.to_widget()
        assert w.data[0].previous_value is None

    def test_render_contains_name(self):
        m = Metric(name="NPS", value=68, trend="up", trend_pct=5.0)
        html = m.render(design=DESIGN)
        assert "NPS" in html

    def test_render_up_shows_arrow(self):
        m = Metric(name="MRR", value=9000, trend="up", trend_pct=12.0)
        html = m.render(design=DESIGN)
        assert "↑" in html

    def test_render_down_shows_arrow(self):
        m = Metric(name="Churn", value=8.0, trend="down", trend_pct=15.0)
        html = m.render(design=DESIGN)
        assert "↓" in html

    def test_render_unit_present(self):
        m = Metric(name="ARR", value=120000, unit="€", trend="up", trend_pct=30.0)
        html = m.render(design=DESIGN)
        assert "€" in html

    def test_render_no_trend_no_arrow(self):
        m = Metric(name="Uptime", value=99.9, unit="%", trend="neutral")
        html = m.render(design=DESIGN)
        assert "↑" not in html
        assert "↓" not in html

    def test_subtitle_in_config(self):
        m = Metric(name="Leads", value=240, subtitle="Ce mois-ci")
        w = m.to_widget()
        assert w.config.subtitle == "Ce mois-ci"

    def test_trend_label_in_config(self):
        m = Metric(name="LTV", value=3400, trend="up", trend_pct=8.0, trend_label="vs jan")
        w = m.to_widget()
        assert w.config.trend_label == "vs jan"

    def test_classmethod_test_passes(self):
        assert Metric.test() is True


# ── TestDataset ────────────────────────────────────────────────────────────────

class TestDataset:

    def test_validate_valid(self):
        ds = Dataset(name="Visites", dimension="time",
                     labels=["Jan", "Fév", "Mar"], values=[100, 120, 110])
        result = ds.validate()
        assert result["valid"] is True

    def test_validate_empty_labels(self):
        ds = Dataset(name="X", dimension="category", labels=[], values=[])
        result = ds.validate()
        assert result["valid"] is False

    def test_validate_length_mismatch(self):
        ds = Dataset(name="X", dimension="time", labels=["A", "B"], values=[1.0])
        result = ds.validate()
        assert result["valid"] is False
        assert any("length" in e for e in result["errors"])

    def test_to_data_points_count(self):
        ds = Dataset(name="CA", dimension="time",
                     labels=["Jan", "Fév", "Mar"], values=[7000, 7400, 6800])
        pts = ds.to_data_points()
        assert len(pts) == 3

    def test_to_data_points_dimension(self):
        ds = Dataset(name="X", dimension="stage", labels=["A", "B"], values=[200, 80])
        pts = ds.to_data_points()
        assert all(p.dimension == "stage" for p in pts)

    def test_to_data_points_series(self):
        ds = Dataset(name="Serie1", dimension="category",
                     labels=["A", "B"], values=[10, 20], series="Prod A")
        pts = ds.to_data_points()
        assert all(p.series == "Prod A" for p in pts)

    def test_to_data_points_meta_columns(self):
        ds = Dataset(name="X", dimension="category",
                     labels=["A"], values=[5.0],
                     meta_columns=[{"note": "important"}])
        pts = ds.to_data_points()
        assert pts[0].meta == {"note": "important"}

    def test_to_widget_time_returns_line_chart(self):
        ds = Dataset(name="MRR", dimension="time",
                     labels=["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul"],
                     values=[1, 2, 3, 4, 5, 6, 7])
        w = ds.to_widget()
        assert w._resolved_type() == "line_chart"

    def test_to_widget_stage_returns_funnel(self):
        ds = Dataset(name="Pipe", dimension="stage",
                     labels=["Leads", "Qualif", "Signés"], values=[300, 120, 45])
        w = ds.to_widget()
        assert w._resolved_type() == "funnel"

    def test_to_widget_explicit_viz_type(self):
        ds = Dataset(name="X", dimension="category",
                     labels=["A", "B", "C"], values=[10, 20, 15])
        w = ds.to_widget(viz_type="bar_chart")
        assert w.type == "bar_chart"

    def test_to_widget_uses_name_as_title(self):
        ds = Dataset(name="Chiffre d'affaires", dimension="time",
                     labels=["Jan", "Fév"], values=[5000, 6000])
        w = ds.to_widget()
        assert w.config.title == "Chiffre d'affaires"

    def test_render_line_chart_has_polyline(self):
        ds = Dataset(name="Visites", dimension="time",
                     labels=["Jan", "Fév", "Mar", "Avr", "Mai", "Jun"],
                     values=[1200, 1450, 1380, 1600, 1700, 1900])
        html = ds.render(design=DESIGN)
        assert "<polyline" in html

    def test_render_funnel_has_polygon(self):
        ds = Dataset(name="Entonnoir", dimension="stage",
                     labels=["Leads", "Qualif", "Signés"], values=[300, 120, 45])
        html = ds.render(design=DESIGN)
        assert "<polygon" in html

    def test_combine_merges_points(self):
        ds_a = Dataset(name="A", dimension="category",
                       labels=["X", "Y"], values=[10, 20], series="S-A")
        ds_b = Dataset(name="B", dimension="category",
                       labels=["X", "Y"], values=[15, 25], series="S-B")
        pts = Dataset.combine(ds_a, ds_b)
        assert len(pts) == 4
        assert pts[0].series == "S-A"
        assert pts[2].series == "S-B"

    def test_combine_single(self):
        ds = Dataset(name="Solo", dimension="time",
                     labels=["A", "B"], values=[1.0, 2.0])
        pts = Dataset.combine(ds)
        assert len(pts) == 2

    def test_classmethod_test_passes(self):
        assert Dataset.test() is True
