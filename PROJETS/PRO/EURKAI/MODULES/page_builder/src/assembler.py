"""
assembler.py
Convertit les outputs du pipeline design EURKAI en Page (page_builder).

Règles Eurkai DOM Library :
  - Structure : uniquement blocs v0.2 (NavBarBlock … FooterBlock)
  - Tokens    : var(--color-*) var(--spacing-*) var(--font-*) var(--border-*) var(--transition-*)
  - Zéro HTML arbitraire — tout passe par les renderers officiels page_builder
"""
from __future__ import annotations

import colorsys
import datetime
import re
from typing import Any

from .core.schemas import Page, Section, Column
from .blocks.navbar      import NavBarBlock, NavBarStructure, NavBarSeed, NavLink
from .blocks.hero        import HeroBlock, HeroStructure, HeroSeed
from .blocks.stat        import StatBlock, StatStructure, StatSeed, StatItem
from .blocks.steps       import StepsBlock, StepsStructure, StepsSeed, StepItem
from .blocks.faq         import FAQBlock, FAQStructure, FAQSeed, FAQItem
from .blocks.pricing     import PricingBlock, PricingStructure, PricingSeed, PricingCardSeed
from .blocks.cta         import CTABlock, CTAStructure, CTASeed
from .blocks.testimonial import (
    TestimonialBlock, TestimonialStructure, TestimonialSeed, TestimonialItemSeed,
)
from .blocks.content     import ContentBlock, ContentStructure, ContentSeed, ContentItem
from .blocks.footer      import FooterBlock, FooterStructure, FooterSeed, FooterColumn


# ── Tokens de typo par style_family ──────────────────────────────────────────

_FONTS: dict[str, tuple[str, str, str]] = {
    "editorial_luxury": (
        "Playfair Display", "Lora",
        "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700"
        "&family=Lora:wght@400;500&display=swap",
    ),
    "brutalist": (
        "Space Grotesk", "Inter",
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700"
        "&family=Inter:wght@400;500&display=swap",
    ),
    "tech_minimal": (
        "Inter", "Inter",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ),
    "experimental_grid": (
        "Space Mono", "Inter",
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700"
        "&family=Inter:wght@400;500&display=swap",
    ),
    "premium_brand": (
        "Cormorant Garamond", "Raleway",
        "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600"
        "&family=Raleway:wght@400;500;600&display=swap",
    ),
    "bold_marketing": (
        "Montserrat", "Open Sans",
        "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800"
        "&family=Open+Sans:wght@400;500&display=swap",
    ),
}
_FONTS_DEFAULT = (
    "Inter", "Inter",
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
)


# ── Plan de sections par site_family ─────────────────────────────────────────

_FAMILY_SECTIONS: dict[str, list[str]] = {
    "product_saas":       ["navbar", "hero", "stats", "steps", "pricing", "testimonials", "cta", "footer"],
    "brand_landing":      ["navbar", "hero", "steps", "testimonials", "cta", "footer"],
    "editorial_magazine": ["navbar", "hero", "content", "cta", "footer"],
    "studio_portfolio":   ["navbar", "hero", "content", "testimonials", "footer"],
    "ecommerce_catalog":  ["navbar", "hero", "stats", "steps", "cta", "footer"],
    "event_campaign":     ["navbar", "hero", "stats", "steps", "cta", "footer"],
}
_SECTIONS_DEFAULT = ["navbar", "hero", "steps", "cta", "footer"]


# ── Hero : mapping plan.hero_type + emotional_goal ────────────────────────────

_HERO_TYPE_MAP: dict[str, dict] = {
    "full_bleed": {"min_height": "95vh", "text_position": "center"},
    "split":      {"min_height": "80vh", "text_position": "left"},
    "minimal":    {"min_height": "55vh", "text_position": "left"},
    "magazine":   {"min_height": "70vh", "text_position": "center"},
    "bold":       {"min_height": "90vh", "text_position": "center"},
    "centered":   {"min_height": "75vh", "text_position": "center"},
}
_EMOTIONAL_HERO: dict[str, dict] = {
    "trust":      {"text_position": "left",   "min_height": "78vh"},
    "excitement": {"text_position": "center", "min_height": "95vh"},
    "desire":     {"text_position": "left",   "min_height": "85vh"},
    "calm":       {"text_position": "left",   "min_height": "68vh"},
    "curiosity":  {"text_position": "center", "min_height": "75vh"},
    "authority":  {"text_position": "left",   "min_height": "80vh"},
}
_BADGE_BY_EMOTION: dict[str, str] = {
    "trust":      "✓ Fiable &amp; Sécurisé",
    "excitement": "🚀 Nouveau",
    "desire":     "⭐ Premium",
    "calm":       "✦ Bien-être",
    "curiosity":  "→ Découvrir",
    "authority":  "◈ Référence",
}


# ── Contenu générique par famille ─────────────────────────────────────────────

_STATS: dict[str, list[dict]] = {
    "product_saas": [
        {"value": "10K+",  "label": "Utilisateurs actifs"},
        {"value": "99,9%", "label": "Uptime garanti"},
        {"value": "2×",    "label": "Gain de productivité"},
        {"value": "< 24h", "label": "Mise en place"},
    ],
    "ecommerce_catalog": [
        {"value": "50K+",   "label": "Références produit"},
        {"value": "4,8 / 5","label": "Note moyenne"},
        {"value": "98%",    "label": "Clients satisfaits"},
        {"value": "J+1",    "label": "Livraison express"},
    ],
    "event_campaign": [
        {"value": "500+",  "label": "Événements organisés"},
        {"value": "95%",   "label": "Taux de satisfaction"},
        {"value": "12",    "label": "Pays couverts"},
    ],
    "default": [
        {"value": "500+",  "label": "Clients accompagnés"},
        {"value": "98%",   "label": "Satisfaction client"},
        {"value": "5 ans", "label": "D'expertise"},
    ],
}

_STEPS: dict[str, list[dict]] = {
    "product_saas": [
        {"title": "Inscrivez-vous", "description": "Créez votre compte en 30 secondes, sans carte bancaire requise."},
        {"title": "Configurez",     "description": "Personnalisez l'espace de travail selon vos besoins en quelques clics."},
        {"title": "Mesurez",        "description": "Suivez vos résultats en temps réel depuis votre dashboard."},
    ],
    "ecommerce_catalog": [
        {"title": "Parcourez",  "description": "Explorez notre catalogue de milliers de produits sélectionnés."},
        {"title": "Commandez",  "description": "Ajoutez au panier et réglez en toute sécurité."},
        {"title": "Recevez",    "description": "Livraison rapide à domicile ou en point relais."},
    ],
    "event_campaign": [
        {"title": "Choisissez", "description": "Sélectionnez la formule adaptée à votre projet."},
        {"title": "Planifiez",  "description": "Notre équipe vous accompagne étape par étape."},
        {"title": "Profitez",   "description": "Vivez votre événement en toute sérénité."},
    ],
    "default": [
        {"title": "Découvrez",  "description": "Explorez nos solutions et trouvez ce qui correspond à vos besoins."},
        {"title": "Démarrez",   "description": "Notre équipe vous accompagne pour une mise en place rapide."},
        {"title": "Évoluez",    "description": "Suivez vos résultats et progressez grâce à notre expertise."},
    ],
}

_PRICING_SAAS = [
    {
        "name": "Starter",    "price": "Gratuit",   "period": "Pour toujours",    "is_featured": False,
        "cta_label": "Commencer gratuitement", "cta_href": "#",
        "features": ["Jusqu'à 5 projets", "1 utilisateur", "Support communautaire", "2 Go"],
    },
    {
        "name": "Pro",        "price": "29 €",      "period": "/ mois",           "is_featured": True,
        "cta_label": "Essai gratuit 14 jours",   "cta_href": "#",
        "features": ["Projets illimités", "10 utilisateurs", "Support prioritaire", "50 Go", "Intégrations"],
    },
    {
        "name": "Enterprise", "price": "Sur devis", "period": "engagement annuel", "is_featured": False,
        "cta_label": "Contacter l'équipe",       "cta_href": "#",
        "features": ["Tout en Pro", "Utilisateurs illimités", "SLA dédié", "Stockage illimité", "SSO + API"],
    },
]

_TESTIMONIALS_DEFAULT = [
    {"name": "Marie Dupont",  "role": "CEO, TechVentures",    "content": "Une transformation réelle de notre façon de travailler. Les résultats ont dépassé nos attentes."},
    {"name": "Lucas Bernard", "role": "Product Manager",      "content": "Intuitif, puissant et parfaitement adapté à nos besoins. L'équipe est très réactive."},
    {"name": "Sophie Moreau", "role": "Directrice Marketing", "content": "Nous avons gagné un temps précieux. Je le recommande sans hésitation à toute équipe sérieuse."},
]

_NAV_LABELS: dict[str, str] = {
    "steps":        "Fonctionnement",
    "pricing":      "Tarifs",
    "testimonials": "Avis",
    "stats":        "Résultats",
    "content":      "À propos",
}


# ── Utilitaires couleur ───────────────────────────────────────────────────────

def _parse_hex(c: str) -> tuple[int, int, int]:
    h = c.lstrip("#")
    if len(h) == 3:
        h = "".join(x * 2 for x in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _to_rgb(c: str) -> str:
    """Hex → rgb(r, g, b). Passe-traver si déjà rgb/hsl."""
    if not c:
        return "rgb(102, 126, 234)"
    if c.startswith(("rgb", "hsl")):
        return c
    try:
        r, g, b = _parse_hex(c)
        return f"rgb({r}, {g}, {b})"
    except Exception:
        return c


def _lighten(c: str, amt: float = 0.12) -> str:
    if not c.startswith("#"):
        return c
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        nr, ng, nb = colorsys.hls_to_rgb(h, min(1.0, ll + amt), s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


def _darken(c: str, amt: float = 0.12) -> str:
    if not c.startswith("#"):
        return c
    try:
        r, g, b = _parse_hex(c)
        h, ll, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        nr, ng, nb = colorsys.hls_to_rgb(h, max(0.0, ll - amt), s)
        return f"#{int(nr*255):02x}{int(ng*255):02x}{int(nb*255):02x}"
    except Exception:
        return c


# ── Construction du theme dict ────────────────────────────────────────────────

def _build_theme(cp_palette: dict | None, visual_intent: dict | None) -> dict:
    """Construit le dict theme (pour generate_page_css) depuis la palette pipeline."""
    vi = visual_intent or {}
    sf = vi.get("style_family", "tech_minimal")
    fh, fb, gf_url = _FONTS.get(sf, _FONTS_DEFAULT)

    p         = cp_palette or {}
    primary   = p.get("primary",        "#667eea")
    secondary = p.get("secondary",      "#764ba2")
    bg        = p.get("background",     "#ffffff")
    surface   = p.get("surface",        "#f7fafc")
    text_p    = p.get("text_primary",   "#2d3748")
    text_s    = p.get("text_secondary", "#718096")
    border    = p.get("border",         "#e2e8f0")

    mood = "neutral"
    if sf in ("editorial_luxury", "premium_brand"):
        mood = "elegant"
    elif sf in ("bold_marketing", "brutalist"):
        mood = "bold"
    try:
        if bg.startswith("#") and sum(_parse_hex(bg)) / 3 < 80:
            mood = "dark"
    except Exception:
        pass

    return {
        "font_family_headings": fh,
        "font_family_body":     fb,
        "font_google_url":      gf_url,
        "mood":                 mood,
        "color_system": {
            "primary": {
                "base":  _to_rgb(primary),
                "light": _to_rgb(_lighten(primary)),
                "dark":  _to_rgb(_darken(primary)),
            },
            "secondary": {
                "base":  _to_rgb(secondary),
                "light": _to_rgb(_lighten(secondary)),
                "dark":  _to_rgb(_darken(secondary)),
            },
        },
        # Surcharges directes pour _fallback_variables()
        "_palette": {
            "text":       _to_rgb(text_p),
            "text_light": _to_rgb(text_s),
            "bg":         _to_rgb(bg),
            "bg_gray":    _to_rgb(surface),
            "border":     _to_rgb(border),
        },
    }


# ── Helpers contenu ───────────────────────────────────────────────────────────

def _tagline(brief: str, max_chars: int = 110) -> str:
    m = re.match(r"^([^.!?]+[.!?]?)", brief.strip())
    t = m.group(1).strip() if m else brief.strip()
    return t[:max_chars].rsplit(" ", 1)[0] if len(t) > max_chars else t


def _section(
    block: Any, section_id: str, order: int, bg_color: str | None = None,
) -> Section:
    return Section(
        id=section_id,
        order=order,
        bg_color=bg_color,
        columns=[Column(span=12, module=block)],
    )


# ── Builders de blocs ────────────────────────────────────────────────────────

def _make_navbar(project_name: str, nav_labels: list[str]) -> NavBarBlock:
    links = [
        NavLink(label=lbl, href=f"#{lbl.lower().replace(' ', '-').replace('é', 'e').replace('à', 'a')}")
        for lbl in nav_labels
    ]
    return NavBarBlock(
        id="navbar",
        structure=NavBarStructure(position="sticky", style="white"),
        seed=NavBarSeed(logo_text=project_name, logo_href="/", links=links),
    )


def _make_hero(
    project_name: str, brief: str,
    primary: str, secondary: str,
    visual_intent: dict | None, plan: dict | None,
) -> HeroBlock:
    vi  = visual_intent or {}
    pl  = plan or {}
    emo = vi.get("emotional_goal", "trust")
    sf  = vi.get("style_family",   "tech_minimal")

    cfg = {"text_position": "center", "min_height": "85vh"}
    cfg.update(_EMOTIONAL_HERO.get(emo, {}))
    cfg.update(_HERO_TYPE_MAP.get(pl.get("hero_type") or pl.get("layout", ""), {}))

    if sf in ("bold_marketing", "experimental_grid"):
        bg_type  = "gradient"
        bg_color = None
    else:
        bg_type  = "color"
        bg_color = primary

    return HeroBlock(
        id="hero",
        structure=HeroStructure(
            bg_type=bg_type,
            text_position=cfg["text_position"],
            overlay=False,
            min_height=cfg["min_height"],
        ),
        seed=HeroSeed(
            title=project_name,
            subtitle=_tagline(brief),
            badge=_BADGE_BY_EMOTION.get(emo),
            cta_primary_label="Commencer",
            cta_primary_href="#",
            cta_secondary_label="En savoir plus",
            cta_secondary_href="#",
            bg_color=bg_color,
        ),
    )


def _make_stats(sf: str) -> StatBlock:
    data = _STATS.get(sf, _STATS["default"])
    return StatBlock(
        id="stats",
        structure=StatStructure(layout="horizontal"),
        seed=StatSeed(stats=[StatItem(value=d["value"], label=d["label"]) for d in data]),
    )


def _make_steps(sf: str) -> StepsBlock:
    data = _STEPS.get(sf, _STEPS["default"])
    return StepsBlock(
        id="how-it-works",
        structure=StepsStructure(variant="cards", direction="horizontal", numbering="numeric"),
        seed=StepsSeed(
            title="Comment ça marche",
            steps=[StepItem(title=d["title"], description=d["description"]) for d in data],
        ),
    )


def _make_pricing() -> PricingBlock:
    cards = [
        PricingCardSeed(
            name=d["name"], price=d["price"], period=d.get("period"),
            features=d["features"], cta_label=d["cta_label"],
            cta_href=d["cta_href"], is_featured=d["is_featured"],
        )
        for d in _PRICING_SAAS
    ]
    return PricingBlock(
        id="pricing",
        structure=PricingStructure(layout="auto", card_style="elevated"),
        seed=PricingSeed(
            title="Tarifs simples et transparents",
            subtitle="Commencez gratuitement, évoluez selon vos besoins.",
            cards=cards,
        ),
    )


def _make_testimonials() -> TestimonialBlock:
    items = [
        TestimonialItemSeed(name=t["name"], role=t["role"], content=t["content"])
        for t in _TESTIMONIALS_DEFAULT
    ]
    return TestimonialBlock(
        id="testimonials",
        structure=TestimonialStructure(layout="grid", columns=3),
        seed=TestimonialSeed(title="Ce qu'ils en disent", items=items),
    )


def _make_content(project_name: str, brief: str) -> ContentBlock:
    return ContentBlock(
        id="about",
        structure=ContentStructure(variant="highlight"),
        seed=ContentSeed(items={
            "headline": ContentItem(type="html",  value=f"<h2>À propos de {project_name}</h2>"),
            "body":     ContentItem(type="text",  value=brief),
        }),
    )


def _make_cta(project_name: str, primary: str, secondary: str) -> CTABlock:
    return CTABlock(
        id="cta",
        structure=CTAStructure(bg_type="gradient", text_align="center"),
        seed=CTASeed(
            title=f"Prêt à démarrer avec {project_name} ?",
            subtitle="Rejoignez des milliers d'utilisateurs satisfaits.",
            btn_label="Démarrer maintenant",
            btn_href="#",
            bg_gradient=f"linear-gradient(135deg, {primary}, {secondary})",
        ),
    )


def _make_footer(project_name: str, sections_present: list[str]) -> FooterBlock:
    links_nav = [NavLink(label="Accueil", href="/")]
    if "pricing"      in sections_present: links_nav.append(NavLink(label="Tarifs",       href="#pricing"))
    if "testimonials" in sections_present: links_nav.append(NavLink(label="Témoignages",  href="#testimonials"))
    if "content"      in sections_present: links_nav.append(NavLink(label="À propos",     href="#about"))

    return FooterBlock(
        id="footer",
        structure=FooterStructure(columns=2, show_social=False),
        seed=FooterSeed(
            copyright=f"© {datetime.date.today().year} {project_name}. Tous droits réservés.",
            columns=[
                FooterColumn(title="Navigation",  links=links_nav),
                FooterColumn(title="Contact",     links=[NavLink(label="Nous contacter", href="#")]),
            ],
        ),
    )


# ── Point d'entrée public ─────────────────────────────────────────────────────

def assemble_page(
    project_name:  str,
    brief_text:    str,
    cp_palette:    dict | None = None,
    site_family:   str = "",
    seed:          int = 42,
    visual_intent: dict | None = None,
    plan:          dict | None = None,
) -> Page:
    """
    Assemble une Page page_builder depuis les outputs du pipeline design EURKAI.

    Toute la structure DOM utilise exclusivement les blocs v0.2 (Eurkai DOM Library).
    Les tokens CSS sont injectés via le theme dict → generate_page_css().

    Args:
        project_name  : Nom du projet / marque (ex: "MyHealth")
        brief_text    : Description libre du projet
        cp_palette    : Palette du pipeline (design.palette.generate)
        site_family   : Famille de template (product_saas, brand_landing, …)
        seed          : Seed de reproductibilité
        visual_intent : (optionnel) output de design.visual_intent.generate
        plan          : (optionnel) output de design.plan.generate

    Returns:
        Page prête pour render_page()
    """
    p         = cp_palette or {}
    primary   = p.get("primary",   "#667eea")
    secondary = p.get("secondary", "#764ba2")

    sf = (site_family or "").lower().replace("-", "_")
    section_types = _FAMILY_SECTIONS.get(sf, _SECTIONS_DEFAULT)

    nav_labels = [_NAV_LABELS[t] for t in section_types if t in _NAV_LABELS]

    sections: list[Section] = []
    for order, stype in enumerate(section_types):
        if stype == "navbar":
            sections.append(_section(_make_navbar(project_name, nav_labels), "navbar", order))
        elif stype == "hero":
            sections.append(_section(
                _make_hero(project_name, brief_text, primary, secondary, visual_intent, plan),
                "hero", order,
            ))
        elif stype == "stats":
            sections.append(_section(_make_stats(sf), "stats", order, bg_color="var(--color-bg-gray)"))
        elif stype == "steps":
            sections.append(_section(_make_steps(sf), "steps", order))
        elif stype == "pricing":
            sections.append(_section(_make_pricing(), "pricing", order, bg_color="var(--color-bg-gray)"))
        elif stype == "testimonials":
            sections.append(_section(_make_testimonials(), "testimonials", order))
        elif stype == "content":
            sections.append(_section(_make_content(project_name, brief_text), "content", order))
        elif stype == "cta":
            sections.append(_section(_make_cta(project_name, primary, secondary), "cta", order))
        elif stype == "footer":
            sections.append(_section(_make_footer(project_name, section_types), "footer", order))

    return Page(
        title=project_name,
        description=_tagline(brief_text, max_chars=160),
        lang="fr",
        theme=_build_theme(cp_palette, visual_intent),
        sections=sections,
    )
