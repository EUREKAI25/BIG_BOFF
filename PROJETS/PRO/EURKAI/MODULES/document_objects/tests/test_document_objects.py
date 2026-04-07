"""
Tests for document_objects module — SheetDoc, EmailSignature, TextDoc, DashboardPage.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from document_objects import (
    SheetDoc, SheetDocInput, IssuerSchema, ClientSchema, LineItem,
    EmailSignature, EmailSignatureInput, SocialLink,
    TextDoc, TextDocInput, TextBlock,
    DashboardPage, DashboardPageInput,
    NavItem, StatCard, TableSection, CardGridSection, FiltersBar,
)


# ── SheetDoc ─────────────────────────────────────────────────────────────────

class TestSheetDoc:
    def _make(self, **kwargs):
        defaults = dict(
            doc_type="invoice",
            doc_number="FAC-001",
            doc_date="2026-03-26",
            issuer=IssuerSchema(name="EURKAI SAS", email="contact@eurkai.com"),
            client=ClientSchema(name="Acme Corp"),
            items=[LineItem(description="Service", quantity=1, unit_price=1000.0)],
        )
        defaults.update(kwargs)
        return SheetDoc(SheetDocInput(**defaults))

    def test_validate_ok(self):
        doc = self._make()
        result = doc.validate()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_missing_items(self):
        doc = self._make(items=[])
        result = doc.validate()
        assert result["valid"] is False
        assert any("item" in e for e in result["errors"])

    def test_totals(self):
        doc = self._make(items=[
            LineItem(description="A", quantity=2, unit_price=100.0, tax_rate=0.20),
            LineItem(description="B", quantity=1, unit_price=500.0, tax_rate=0.20),
        ])
        assert doc.total_ht  == 700.0
        assert doc.total_tax == 140.0
        assert doc.total_ttc == 840.0

    def test_render_contains_key_data(self):
        doc = self._make()
        html = doc.render()
        assert "FAC-001" in html
        assert "EURKAI SAS" in html
        assert "Acme Corp" in html
        assert "<table>" in html
        assert "FACTURE" in html

    def test_render_with_design(self):
        doc = self._make(design={"palette": {"primary": "#ff0000", "accent": "#00ff00"}})
        html = doc.render()
        assert "#ff0000" in html

    def test_render_quote_type(self):
        doc = self._make(doc_type="quote", doc_number="DEV-001")
        html = doc.render()
        assert "DEVIS" in html

    def test_line_item_computations(self):
        item = LineItem(description="X", quantity=3, unit_price=100.0, tax_rate=0.10)
        assert item.subtotal_ht  == 300.0
        assert item.tax_amount   == 30.0
        assert item.subtotal_ttc == 330.0

    def test_built_in_test(self):
        assert SheetDoc.test() is True


# ── EmailSignature ────────────────────────────────────────────────────────────

class TestEmailSignature:
    def _make(self, **kwargs):
        defaults = dict(name="Test User", email="test@eurkai.com")
        defaults.update(kwargs)
        return EmailSignature(EmailSignatureInput(**defaults))

    def test_validate_ok(self):
        sig = self._make()
        assert sig.validate()["valid"] is True

    def test_validate_cta_missing_url(self):
        sig = self._make(cta_label="Voir", cta_url=None)
        result = sig.validate()
        assert result["valid"] is False

    def test_render_contains_name(self):
        sig = self._make()
        assert "Test User" in sig.render()

    def test_render_contains_email(self):
        sig = self._make()
        assert "test@eurkai.com" in sig.render()

    def test_render_with_all_fields(self):
        sig = self._make(
            role="Director",
            company="EURKAI",
            phone="+33 6 00 00 00 00",
            website="https://eurkai.com",
            cta_label="CTA",
            cta_url="https://eurkai.com",
            tagline="Tagline test",
            social_links=[SocialLink(platform="linkedin", url="https://linkedin.com/in/test")],
        )
        html = sig.render()
        assert "Director" in html
        assert "EURKAI" in html
        assert "CTA" in html
        assert "LinkedIn" in html
        assert "Tagline test" in html

    def test_render_table_structure(self):
        sig = self._make()
        html = sig.render()
        assert "<table" in html
        assert "</table>" in html

    def test_render_full_is_valid_html(self):
        sig = self._make()
        html = sig.render_full()
        assert "<!DOCTYPE html>" in html
        assert "Test User" in html

    def test_logo_vs_monogram(self):
        sig_logo = self._make(logo_url="https://eurkai.com/logo.png")
        assert 'img src=' in sig_logo.render()

        sig_mono = self._make()
        assert '<div' in sig_mono.render()

    def test_built_in_test(self):
        assert EmailSignature.test() is True


# ── TextDoc ───────────────────────────────────────────────────────────────────

class TestTextDoc:
    def _make_blocks(self):
        return [
            TextBlock(type="heading", content="Section 1"),
            TextBlock(type="paragraph", content="Lorem ipsum dolor sit amet."),
            TextBlock(type="bullet_list", items=["A", "B", "C"]),
        ]

    def _make(self, **kwargs):
        defaults = dict(title="Test Doc", blocks=self._make_blocks())
        defaults.update(kwargs)
        return TextDoc(TextDocInput(**defaults))

    def test_validate_ok(self):
        doc = self._make()
        assert doc.validate()["valid"] is True

    def test_validate_missing_title(self):
        doc = TextDoc(TextDocInput(title="", blocks=self._make_blocks()))
        assert doc.validate()["valid"] is False

    def test_validate_list_without_items(self):
        doc = self._make(blocks=[TextBlock(type="bullet_list")])
        result = doc.validate()
        assert result["valid"] is False

    def test_render_title(self):
        doc = self._make()
        html = doc.render()
        assert "Test Doc" in html

    def test_render_all_block_types(self):
        blocks = [
            TextBlock(type="title", content="T"),
            TextBlock(type="subtitle", content="S"),
            TextBlock(type="heading", content="H2", level=2),
            TextBlock(type="heading", content="H3", level=3),
            TextBlock(type="paragraph", content="P"),
            TextBlock(type="bullet_list", items=["X", "Y"]),
            TextBlock(type="numbered_list", items=["1", "2"]),
            TextBlock(type="callout", content="C", callout_variant="info"),
            TextBlock(type="separator"),
            TextBlock(type="quote", content="Q"),
            TextBlock(type="code", content="print('hello')"),
            TextBlock(type="footer", content="F"),
        ]
        doc = TextDoc(TextDocInput(title="Full", blocks=blocks))
        html = doc.render()
        for tag in ["<h1", "<h2", "<h3", "<p", "<ul", "<ol", "<blockquote", "<pre"]:
            assert tag in html, f"Missing tag: {tag}"
        assert "border-radius" in html  # separator is a styled div now

    def test_callout_variants(self):
        for variant in ["info", "warning", "success", "neutral"]:
            block = TextBlock(type="callout", content="Test", callout_variant=variant)
            doc = TextDoc(TextDocInput(title="T", blocks=[block]))
            html = doc.render()
            assert "Test" in html

    def test_render_with_design(self):
        doc = self._make(design={"palette": {"primary": "#abcdef"}})
        html = doc.render()
        assert "#abcdef" in html

    def test_built_in_test(self):
        assert TextDoc.test() is True


# ── DashboardPage ─────────────────────────────────────────────────────────────

class TestDashboardPage:
    def _make(self, **kwargs):
        defaults = dict(
            title="Test Dashboard",
            user_name="Alice",
            stat_cards=[StatCard(title="KPI", value="42")],
            sections=[
                TableSection(
                    columns=["Col A", "Col B"],
                    rows=[["a1", "b1"], ["a2", "b2"]],
                )
            ],
        )
        defaults.update(kwargs)
        return DashboardPage(DashboardPageInput(**defaults))

    def test_validate_ok(self):
        page = self._make()
        assert page.validate()["valid"] is True

    def test_validate_table_column_mismatch(self):
        page = DashboardPage(DashboardPageInput(
            title="T",
            sections=[TableSection(columns=["A", "B"], rows=[["x"]])],
        ))
        result = page.validate()
        assert result["valid"] is False

    def test_render_title(self):
        page = self._make()
        assert "Test Dashboard" in page.render()

    def test_render_user_name(self):
        page = self._make()
        assert "Alice" in page.render()

    def test_render_with_nav(self):
        page = self._make(nav_items=[
            NavItem(label="Home", href="#", active=True),
            NavItem(label="Reports", href="#reports"),
        ])
        html = page.render()
        assert "Home" in html
        assert "Reports" in html
        assert "<nav" in html

    def test_render_stat_cards(self):
        page = self._make(stat_cards=[
            StatCard(title="Revenue", value="10 000 €", subtitle="↑ 12%"),
            StatCard(title="Users", value="234"),
        ])
        html = page.render()
        assert "Revenue" in html
        assert "10 000" in html
        assert "Users" in html

    def test_render_table_section(self):
        page = self._make(sections=[
            TableSection(
                title="Clients",
                columns=["Nom", "Email"],
                rows=[["Acme", "acme@test.com"]],
                actions=[{"label": "Voir", "href": "#"}],
            )
        ])
        html = page.render()
        assert "Clients" in html
        assert "Acme" in html
        assert "acme@test.com" in html

    def test_render_card_grid(self):
        page = self._make(sections=[
            CardGridSection(
                title="Quick Access",
                cards=[{"title": "Card 1", "body": "Body text", "badge": "NEW"}],
            )
        ])
        html = page.render()
        assert "Card 1" in html
        assert "NEW" in html

    def test_render_filters_bar(self):
        page = self._make(sections=[
            FiltersBar(
                filters=[{"label": "Status", "options": ["Active", "Archived"]}],
                search_placeholder="Search…",
            )
        ])
        html = page.render()
        assert "Search" in html
        assert "Status" in html

    def test_render_with_design(self):
        page = self._make(design={"palette": {"primary": "#123456", "accent": "#654321"}})
        html = page.render()
        assert "#123456" in html

    def test_built_in_test(self):
        assert DashboardPage.test() is True
