"""
DashboardPage — Personal space / backoffice / admin-like page object.

The object owns its render logic. Not a framework adapter.

Usage:
    from document_objects.dashboard_page import DashboardPage, DashboardPageInput
    from document_objects.dashboard_page import NavItem, StatCard, TableSection, CardSection

    page = DashboardPage(DashboardPageInput(
        title="EURKAI — Tableau de bord",
        user_name="Nathalie",
        nav_items=[
            NavItem(label="Projets", href="#projects", active=True),
            NavItem(label="Clients", href="#clients"),
            NavItem(label="Facturation", href="#invoices"),
        ],
        sections=[
            StatCard(title="Projets actifs", value="12", subtitle="↑ 3 ce mois"),
            StatCard(title="Revenus MRR", value="8 400 €", subtitle="vs 7 200 € M-1"),
        ],
        ...
    ))
    html = page.render()
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

NAME     = "document.dashboard_page"
CATEGORY = "document"
VERSION  = "1.0.0"


# ── Nav ───────────────────────────────────────────────────────────────────────

class NavItem(BaseModel):
    label: str
    href: str = "#"
    active: bool = False
    icon: Optional[str] = None  # emoji or SVG string


# ── Sections ──────────────────────────────────────────────────────────────────

class StatCard(BaseModel):
    section_type: Literal["stat_card"] = "stat_card"
    title: str
    value: str
    subtitle: Optional[str] = None
    color: Optional[str] = None       # override accent color for this card
    icon: Optional[str] = None


class TableSection(BaseModel):
    section_type: Literal["table"] = "table"
    title: Optional[str] = None
    columns: List[str]
    rows: List[List[str]]
    actions: Optional[List[Dict[str, str]]] = None  # [{"label": "Voir", "href": "#"}]


class CardGridSection(BaseModel):
    section_type: Literal["card_grid"] = "card_grid"
    title: Optional[str] = None
    cards: List[Dict[str, Any]]   # {"title", "body", "href", "badge", "badge_color"}
    columns: int = 3


class FiltersBar(BaseModel):
    section_type: Literal["filters_bar"] = "filters_bar"
    filters: List[Dict[str, Any]]  # {"label": "Statut", "options": ["Actif", "Archivé"]}
    search_placeholder: Optional[str] = None


from .dashboard_widgets import WidgetSection  # noqa: E402 — imported after local classes

SectionUnion = Union[StatCard, TableSection, CardGridSection, FiltersBar, WidgetSection]


class DashboardPageInput(BaseModel):
    title: str
    user_name: Optional[str] = None
    nav_items: List[NavItem] = []
    stat_cards: List[StatCard] = []
    sections: List[SectionUnion] = Field(default_factory=list)
    design: Optional[Dict[str, Any]] = None


# ── Object ───────────────────────────────────────────────────────────────────

class DashboardPage:
    NAME     = NAME
    CATEGORY = CATEGORY
    VERSION  = VERSION

    def __init__(self, data: DashboardPageInput) -> None:
        self.data = data

    # ── Validate ──────────────────────────────────────────────────────────────

    def validate(self) -> dict:
        errors = []
        if not self.data.title:
            errors.append("title is required")
        for i, section in enumerate(self.data.sections):
            if isinstance(section, TableSection):
                for j, row in enumerate(section.rows):
                    if len(row) != len(section.columns):
                        errors.append(
                            f"section[{i}] row[{j}]: expected {len(section.columns)} cols, got {len(row)}"
                        )
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Section renderers ─────────────────────────────────────────────────────

    def _render_stat_card(self, card: StatCard, pal: dict, font_body: str = "Inter, system-ui, sans-serif") -> str:
        accent  = card.color or pal.get("accent", "#6366f1")
        primary = pal.get("primary", "#0f172a")
        muted   = pal.get("muted",   "#64748b")
        surface = pal.get("surface", "#f8fafc")

        icon_html = (
            f'<div style="width:36px; height:36px; border-radius:8px; background:{accent}15; '
            f'display:flex; align-items:center; justify-content:center; font-size:18px; '
            f'margin-bottom:14px;">{card.icon}</div>'
            if card.icon else ""
        )

        # Trend detection: subtitle starting with ↑ → green, ↓ → red
        subtitle_color = muted
        if card.subtitle:
            if card.subtitle.startswith("↑"):
                subtitle_color = "#16a34a"
            elif card.subtitle.startswith("↓"):
                subtitle_color = "#dc2626"

        subtitle_html = (
            f'<p style="margin:6px 0 0; font-size:12px; color:{subtitle_color}; '
            f'font-family:{font_body}; font-weight:500;">{card.subtitle}</p>'
            if card.subtitle else ""
        )

        return (
            f'<div style="background:#fff; border-radius:12px; padding:22px 24px; '
            f'box-shadow:0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04); '
            f'border-bottom:3px solid {accent}; position:relative; overflow:hidden;">'
            f'<div style="position:absolute; top:0; right:0; width:80px; height:80px; '
            f'border-radius:50%; background:{accent}06; transform:translate(20px,-20px);"></div>'
            f'{icon_html}'
            f'<p style="margin:0; font-size:11px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.08em; color:{muted}; font-family:{font_body};">{card.title}</p>'
            f'<p style="margin:8px 0 0; font-size:28px; font-weight:900; color:{primary}; '
            f'line-height:1; letter-spacing:-.03em; font-family:{font_body};">{card.value}</p>'
            f'{subtitle_html}'
            f'</div>'
        )

    def _render_table(self, section: TableSection, pal: dict, font_body: str) -> str:
        primary  = pal.get("primary", "#0f172a")
        muted    = pal.get("muted",   "#64748b")
        accent   = pal.get("accent",  "#6366f1")
        surface  = pal.get("surface", "#f8fafc")
        border_c = pal.get("border",  "#e2e8f0")

        section_title_html = (
            f'<div style="padding:18px 20px 16px; border-bottom:1px solid {border_c}; '
            f'display:flex; justify-content:space-between; align-items:center;">'
            f'<h3 style="margin:0; font-size:14px; font-weight:700; color:{primary}; '
            f'font-family:{font_body}; letter-spacing:-.01em;">{section.title}</h3>'
            f'</div>'
        ) if section.title else ""

        header_cells = "".join(
            f'<th style="padding:11px 16px; text-align:left; font-size:10px; font-weight:700; '
            f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7); '
            f'white-space:nowrap;">{col}</th>'
            for col in section.columns
        )

        rows_html = ""
        for idx, row in enumerate(section.rows):
            row_bg = f"background:{surface};" if idx % 2 == 1 else ""
            cells = "".join(
                f'<td style="padding:11px 16px; border-bottom:1px solid {border_c}; '
                f'font-size:13px; color:{primary if i == 0 else muted}; '
                f'font-family:{font_body};">{cell}</td>'
                for i, cell in enumerate(row)
            )
            rows_html += f'<tr style="{row_bg}">{cells}</tr>'

        actions_html = ""
        if section.actions:
            links = " ".join(
                f'<a href="{a.get("href","#")}" style="color:{accent}; font-size:12px; '
                f'font-weight:600; text-decoration:none; font-family:{font_body}; '
                f'margin-right:16px;">{a.get("label","")}&nbsp;→</a>'
                for a in section.actions
            )
            actions_html = (
                f'<div style="padding:12px 20px; border-top:1px solid {border_c}; '
                f'background:{surface};">{links}</div>'
            )

        return (
            f'<div style="background:#fff; border-radius:12px; '
            f'box-shadow:0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04); '
            f'overflow:hidden; margin-bottom:24px; border:1px solid {border_c};">'
            f'{section_title_html}'
            f'<table style="width:100%; border-collapse:collapse; font-family:{font_body};">'
            f'<thead><tr style="background:{primary};">{header_cells}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>'
            f'{actions_html}'
            f'</div>'
        )

    def _render_card_grid(self, section: CardGridSection, pal: dict, font_body: str = "Inter, system-ui, sans-serif") -> str:
        primary  = pal.get("primary", "#0f172a")
        accent   = pal.get("accent",  "#6366f1")
        muted    = pal.get("muted",   "#64748b")
        border_c = pal.get("border",  "#e2e8f0")

        title_html = (
            f'<h3 style="margin:0 0 14px; font-size:14px; font-weight:700; color:{primary}; '
            f'font-family:{font_body}; letter-spacing:-.01em;">{section.title}</h3>'
        ) if section.title else ""

        cards_html = ""
        for card in section.cards:
            badge_color = card.get("badge_color", accent)
            badge_html = (
                f'<span style="display:inline-block; padding:2px 9px; background:{badge_color}15; '
                f'color:{badge_color}; font-size:9px; font-weight:800; border-radius:99px; '
                f'text-transform:uppercase; letter-spacing:.08em; margin-bottom:10px; '
                f'border:1px solid {badge_color}30;">{card["badge"]}</span>'
            ) if card.get("badge") else ""

            href = card.get("href", "")
            arrow_html = (
                f'<span style="position:absolute; bottom:16px; right:18px; color:{accent}; '
                f'font-size:16px; opacity:.5;">→</span>'
                if href else ""
            )
            card_wrap_s = f'<a href="{href}" style="text-decoration:none; color:inherit; display:block;">' if href else ""
            card_wrap_e = "</a>" if href else ""

            cards_html += (
                f'<div style="background:#fff; border-radius:12px; padding:20px 18px 36px; '
                f'box-shadow:0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04); '
                f'flex:1; min-width:180px; position:relative; border:1px solid {border_c}; '
                f'border-top:3px solid {accent};">'
                f'{card_wrap_s}'
                f'{badge_html}'
                f'<p style="margin:0; font-size:14px; font-weight:700; color:{primary}; '
                f'font-family:{font_body}; letter-spacing:-.01em;">{card.get("title","")}</p>'
                f'<p style="margin:6px 0 0; font-size:12px; color:{muted}; font-family:{font_body}; '
                f'line-height:1.55;">{card.get("body","")}</p>'
                f'{card_wrap_e}'
                f'{arrow_html}'
                f'</div>'
            )

        return (
            f'<div style="margin-bottom:28px;">'
            f'{title_html}'
            f'<div style="display:flex; flex-wrap:wrap; gap:16px;">{cards_html}</div>'
            f'</div>'
        )

    def _render_filters_bar(self, section: FiltersBar, pal: dict, font_body: str) -> str:
        accent   = pal.get("accent",  "#6366f1")
        muted    = pal.get("muted",   "#64748b")
        border_c = pal.get("border",  "#e2e8f0")
        surface  = pal.get("surface", "#f8fafc")

        search_html = ""
        if section.search_placeholder:
            search_html = (
                f'<div style="position:relative; flex:1; max-width:260px;">'
                f'<span style="position:absolute; left:10px; top:50%; transform:translateY(-50%); '
                f'color:{muted}; font-size:13px; pointer-events:none;">🔍</span>'
                f'<input type="text" placeholder="{section.search_placeholder}" '
                f'style="width:100%; padding:8px 12px 8px 32px; border:1px solid {border_c}; '
                f'border-radius:8px; font-size:13px; font-family:{font_body}; '
                f'outline:none; background:#fff; color:inherit;">'
                f'</div>'
            )

        filters_html = "".join(
            f'<select style="padding:8px 32px 8px 12px; border:1px solid {border_c}; '
            f'border-radius:8px; font-size:12px; font-family:{font_body}; '
            f'color:{muted}; background:#fff; appearance:none; cursor:pointer; '
            f'background-image:url(\'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="12" height="8" viewBox="0 0 12 8"><path d="M1 1l5 5 5-5" stroke="%2364748b" '
            f'stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>\'); '
            f'background-repeat:no-repeat; background-position:right 10px center;">'
            f'<option value="" disabled selected>{f["label"]}</option>'
            + "".join(f'<option>{opt}</option>' for opt in f.get("options", []))
            + "</select>"
            for f in section.filters
        )

        return (
            f'<div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; '
            f'margin-bottom:20px; padding:14px 18px; background:#fff; border-radius:10px; '
            f'box-shadow:0 1px 4px rgba(0,0,0,.06); border:1px solid {border_c};">'
            f'{search_html}'
            f'{filters_html}'
            f'</div>'
        )

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        d = self.data
        pal  = (d.design or {}).get("palette", {})
        typo = (d.design or {}).get("typography", {})

        primary    = pal.get("primary",    "#0f172a")
        accent     = pal.get("accent",     "#6366f1")
        bg         = pal.get("background", "#f1f5f9")
        text_color = pal.get("text",       "#1e293b")
        muted      = pal.get("muted",      "#64748b")
        sidebar_bg = pal.get("sidebar",    "#0f172a")
        surface    = pal.get("surface",    "#f8fafc")
        border_c   = pal.get("border",     "#e2e8f0")
        font_body  = typo.get("body_font", "Inter, system-ui, sans-serif")

        # ── Sidebar ───────────────────────────────────────────────────────────
        nav_items_html = ""
        for item in d.nav_items:
            icon_span = (
                f'<span style="width:18px; text-align:center; margin-right:10px; '
                f'font-size:14px; flex-shrink:0;">{item.icon}</span>'
                if item.icon else
                f'<span style="width:18px; margin-right:10px; flex-shrink:0;"></span>'
            )
            if item.active:
                item_style = (
                    f"display:flex; align-items:center; padding:9px 12px; border-radius:8px; "
                    f"text-decoration:none; font-size:13px; font-weight:600; margin-bottom:2px; "
                    f"background:{accent}; color:#fff; box-shadow:0 2px 8px {accent}40;"
                )
            else:
                item_style = (
                    f"display:flex; align-items:center; padding:9px 12px; border-radius:8px; "
                    f"text-decoration:none; font-size:13px; font-weight:400; margin-bottom:2px; "
                    f"color:rgba(255,255,255,.55);"
                )
            nav_items_html += (
                f'<a href="{item.href}" style="{item_style}">'
                f'{icon_span}{item.label}</a>'
            )

        # Brand mark in sidebar
        brand_initial = d.title[0].upper()
        brand_html = (
            f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:32px; padding-bottom:24px; '
            f'border-bottom:1px solid rgba(255,255,255,.08);">'
            f'<div style="width:32px; height:32px; border-radius:8px; background:{accent}; '
            f'display:flex; align-items:center; justify-content:center; '
            f'font-size:14px; font-weight:900; color:#fff; flex-shrink:0;">{brand_initial}</div>'
            f'<span style="font-size:14px; font-weight:800; color:#fff; letter-spacing:-.02em; '
            f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{d.title}</span>'
            f'</div>'
        )

        nav_html = (
            f'<nav style="width:230px; min-height:100vh; background:{sidebar_bg}; '
            f'padding:24px 14px; flex-shrink:0; font-family:{font_body}; '
            f'display:flex; flex-direction:column;">'
            f'{brand_html}'
            f'{nav_items_html}'
            f'</nav>'
            if d.nav_items else ""
        )

        # ── Header bar ────────────────────────────────────────────────────────
        user_initial = (d.user_name or d.title)[0].upper()
        greeting_text = f"Bonjour,&nbsp;<strong style='color:{primary};'>{d.user_name}</strong>" if d.user_name else d.title
        header_html = (
            f'<header style="background:#fff; border-bottom:1px solid {border_c}; '
            f'padding:0 28px; height:56px; display:flex; justify-content:space-between; '
            f'align-items:center; font-family:{font_body}; flex-shrink:0; '
            f'box-shadow:0 1px 4px rgba(0,0,0,.04);">'
            f'<p style="margin:0; font-size:14px; color:{muted};">{greeting_text}</p>'
            f'<div style="display:flex; align-items:center; gap:12px;">'
            f'<div style="width:34px; height:34px; border-radius:50%; background:{primary}; '
            f'color:#fff; font-size:13px; font-weight:700; display:flex; '
            f'align-items:center; justify-content:center; '
            f'box-shadow:0 2px 6px {primary}40; font-family:{font_body};">{user_initial}</div>'
            f'</div>'
            f'</header>'
        )

        # ── Stat cards ────────────────────────────────────────────────────────
        stat_cards_html = ""
        if d.stat_cards:
            cards_rendered = "".join(
                self._render_stat_card(c, pal, font_body) for c in d.stat_cards
            )
            stat_cards_html = (
                f'<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); '
                f'gap:16px; margin-bottom:28px;">{cards_rendered}</div>'
            )

        # ── Dynamic sections ──────────────────────────────────────────────────
        sections_html = ""
        for section in d.sections:
            st = section.section_type
            if st == "stat_card":
                sections_html += self._render_stat_card(section, pal, font_body)
            elif st == "table":
                sections_html += self._render_table(section, pal, font_body)
            elif st == "card_grid":
                sections_html += self._render_card_grid(section, pal, font_body)
            elif st == "filters_bar":
                sections_html += self._render_filters_bar(section, pal, font_body)
            elif st == "widget_section":
                sections_html += section._render(design=d.design)

        main_content = (
            f'<main style="flex:1; padding:28px 32px; overflow-y:auto; '
            f'font-family:{font_body}; color:{text_color};">'
            f'{stat_cards_html}'
            f'{sections_html}'
            f'</main>'
        )

        layout_style = "display:flex;" if d.nav_items else ""

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{d.title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {font_body};
      background: {bg};
      color: {text_color};
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}
    .layout {{ {layout_style} min-height: 100vh; }}
    .main-area {{ flex: 1; display: flex; flex-direction: column; min-width: 0; }}
    a {{ color: {accent}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="layout">
    {nav_html}
    <div class="main-area">
      {header_html}
      {main_content}
    </div>
  </div>
</body>
</html>"""

    # ── Test ──────────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        from document_objects.dashboard_page import (
            DashboardPage, DashboardPageInput,
            NavItem, StatCard, TableSection, CardGridSection, FiltersBar,
        )
        page = cls(DashboardPageInput(
            title="EURKAI — Dashboard",
            user_name="Nathalie",
            nav_items=[
                NavItem(label="Projets", href="#projects", active=True, icon="📁"),
                NavItem(label="Clients", href="#clients", icon="👥"),
                NavItem(label="Facturation", href="#invoices", icon="💰"),
                NavItem(label="Réglages", href="#settings", icon="⚙️"),
            ],
            stat_cards=[
                StatCard(title="Projets actifs", value="12", subtitle="↑ 3 ce mois"),
                StatCard(title="Clients", value="47"),
                StatCard(title="MRR", value="8 400 €", subtitle="vs 7 200 € M-1"),
                StatCard(title="Tâches ouvertes", value="23", subtitle="5 urgentes"),
            ],
            sections=[
                FiltersBar(
                    filters=[
                        {"label": "Statut", "options": ["Actif", "Archivé", "En pause"]},
                        {"label": "Priorité", "options": ["Haute", "Normale", "Basse"]},
                    ],
                    search_placeholder="Rechercher un projet…",
                ),
                TableSection(
                    title="Projets récents",
                    columns=["Projet", "Client", "Statut", "Date"],
                    rows=[
                        ["EURKAI Design System", "EURKAI SAS", "Actif", "2026-03-26"],
                        ["Refonte site Acme", "Acme Corp", "En cours", "2026-03-20"],
                        ["App mobile Lyra", "Lyra SAS", "Livré", "2026-02-15"],
                    ],
                    actions=[{"label": "Voir tous", "href": "#projects"}],
                ),
                CardGridSection(
                    title="Accès rapide",
                    cards=[
                        {"title": "Nouveau projet", "body": "Créer un projet depuis un brief IA", "href": "#new", "badge": "IA", "badge_color": "#6366f1"},
                        {"title": "Générer devis", "body": "SheetDoc depuis un template", "href": "#quote"},
                        {"title": "Design System", "body": "Accéder à la bibliothèque EURKAI", "href": "#design"},
                    ],
                ),
            ],
            design={
                "palette": {
                    "primary": "#0f172a",
                    "accent":  "#6366f1",
                    "sidebar": "#1e293b",
                    "muted":   "#64748b",
                },
            },
        ))
        v = page.validate()
        assert v["valid"], f"Validation failed: {v['errors']}"
        html = page.render()
        assert "EURKAI" in html
        assert "Nathalie" in html
        assert "Projets récents" in html
        assert "Nouveau projet" in html
        return True
