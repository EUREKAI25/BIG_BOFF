"""
Tests for v1.1 business document objects:
    InvoiceDoc, QuoteDoc, PurchaseOrderDoc, BrandDefinition, Template objects.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from document_objects import (
    # base types
    DocumentIssuer, DocumentClient, DocumentLineItem,
    DocumentPageHeader, DocumentPageFooter,
    BankDetails, DeliveryInfo,
    # business docs
    InvoiceDoc, InvoiceDocInput,
    QuoteDoc, QuoteDocInput,
    PurchaseOrderDoc, PurchaseOrderDocInput,
    # templates
    BrandDefinition, InvoiceTemplate, QuoteTemplate,
    PurchaseOrderTemplate, TextDocTemplate, SheetDocTemplate,
    # for SheetDocTemplate
    IssuerSchema, ClientSchema, LineItem, TextBlock,
)


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _issuer():
    return DocumentIssuer(
        name="EURKAI SAS",
        address="15 rue de la Paix",
        city="Paris",
        postal_code="75001",
        siret="123 456 789 00012",
        vat_number="FR12 123456789",
        email="contact@eurkai.com",
    )


def _client():
    return DocumentClient(
        name="Acme Corp",
        city="Lyon",
        email="acme@example.com",
    )


def _items():
    return [
        DocumentLineItem(description="Conseil", quantity=1, unit_price=2000.0, tax_rate=0.20),
        DocumentLineItem(description="Développement", quantity=5, unit_price=600.0, unit="j", tax_rate=0.20),
    ]


def _design():
    return {"palette": {"primary": "#0f172a", "accent": "#6366f1"}}


def _brand():
    return BrandDefinition(
        name="EURKAI SAS",
        design=_design(),
        issuer=_issuer(),
        bank_details=BankDetails(
            bank_name="BNP Paribas",
            iban="FR76 3000 4000 0100 0000 0012 345",
            bic="BNPAFRPPXXX",
        ),
    )


# ── InvoiceDoc ────────────────────────────────────────────────────────────────

class TestInvoiceDoc:
    def _make(self, **kwargs):
        defaults = dict(
            doc_number="FAC-2026-001",
            doc_date="2026-03-26",
            issuer=_issuer(),
            client=_client(),
            items=_items(),
        )
        defaults.update(kwargs)
        return InvoiceDoc(InvoiceDocInput(**defaults))

    def test_validate_ok(self):
        assert self._make().validate()["valid"] is True

    def test_validate_missing_items(self):
        result = self._make(items=[]).validate()
        assert result["valid"] is False
        assert any("item" in e for e in result["errors"])

    def test_validate_missing_issuer_name(self):
        result = self._make(issuer=DocumentIssuer(name="")).validate()
        assert result["valid"] is False

    def test_totals(self):
        doc = self._make()
        # 2000 + 5×600 = 5000 HT, tax 20% = 1000, TTC = 6000
        assert doc.total_ht == 5000.0
        assert doc.total_tax == 1000.0
        assert doc.total_ttc == 6000.0

    def test_render_contains_doc_number(self):
        assert "FAC-2026-001" in self._make().render()

    def test_render_contains_parties(self):
        html = self._make().render()
        assert "EURKAI SAS" in html
        assert "Acme Corp" in html

    def test_render_label(self):
        assert "Facture" in self._make().render()

    def test_render_with_design(self):
        html = self._make(design=_design()).render()
        assert "#0f172a" in html

    def test_render_with_due_date(self):
        html = self._make(due_date="2026-04-25").render()
        assert "2026-04-25" in html

    def test_render_with_bank_details(self):
        html = self._make(
            bank_details=BankDetails(iban="FR76 1234", bic="BNPAFRPP", bank_name="BNP")
        ).render()
        assert "BNP" in html
        assert "FR76 1234" in html

    def test_render_with_payment_terms(self):
        html = self._make(payment_terms="Paiement immédiat.").render()
        assert "Paiement immédiat" in html

    def test_render_with_purchase_order_ref(self):
        html = self._make(purchase_order_ref="PO-ABC-2026").render()
        assert "PO-ABC-2026" in html

    def test_render_with_page_footer(self):
        html = self._make(
            page_footer=DocumentPageFooter(company_line="EURKAI SAS — SIRET 123")
        ).render()
        assert "SIRET 123" in html

    def test_render_notes(self):
        html = self._make(notes="Note de test.").render()
        assert "Note de test" in html

    def test_item_with_note(self):
        items = [DocumentLineItem(description="Prestation", quantity=1, unit_price=100.0, note="Sous-note")]
        html = self._make(items=items).render()
        assert "Sous-note" in html

    def test_built_in_test(self):
        assert InvoiceDoc.test() is True


# ── QuoteDoc ──────────────────────────────────────────────────────────────────

class TestQuoteDoc:
    def _make(self, **kwargs):
        defaults = dict(
            doc_number="DEV-2026-042",
            doc_date="2026-03-26",
            issuer=_issuer(),
            client=_client(),
            items=_items(),
        )
        defaults.update(kwargs)
        return QuoteDoc(QuoteDocInput(**defaults))

    def test_validate_ok(self):
        assert self._make().validate()["valid"] is True

    def test_validate_missing_items(self):
        result = self._make(items=[]).validate()
        assert result["valid"] is False

    def test_totals(self):
        doc = self._make()
        assert doc.total_ht == 5000.0
        assert doc.total_ttc == 6000.0

    def test_render_label(self):
        assert "Devis" in self._make().render()

    def test_render_doc_number(self):
        assert "DEV-2026-042" in self._make().render()

    def test_render_validity_date(self):
        html = self._make(validity_date="2026-04-30").render()
        assert "2026-04-30" in html

    def test_render_acceptance_block(self):
        html = self._make(show_acceptance_block=True).render()
        assert "Bon pour accord" in html

    def test_no_acceptance_block(self):
        html = self._make(show_acceptance_block=False).render()
        assert "Bon pour accord" not in html

    def test_render_conditions(self):
        html = self._make(conditions="Conditions spéciales.").render()
        assert "Conditions spéciales" in html

    def test_render_with_design(self):
        html = self._make(design=_design()).render()
        assert "#6366f1" in html

    def test_built_in_test(self):
        assert QuoteDoc.test() is True


# ── PurchaseOrderDoc ──────────────────────────────────────────────────────────

class TestPurchaseOrderDoc:
    def _make(self, **kwargs):
        defaults = dict(
            doc_number="BC-2026-007",
            doc_date="2026-03-26",
            issuer=_issuer(),
            client=_client(),
            items=_items(),
        )
        defaults.update(kwargs)
        return PurchaseOrderDoc(PurchaseOrderDocInput(**defaults))

    def test_validate_ok(self):
        assert self._make().validate()["valid"] is True

    def test_validate_missing_items(self):
        result = self._make(items=[]).validate()
        assert result["valid"] is False

    def test_totals(self):
        doc = self._make()
        assert doc.total_ht == 5000.0
        assert doc.total_ttc == 6000.0

    def test_render_label(self):
        assert "Bon de commande" in self._make().render()

    def test_render_doc_number(self):
        assert "BC-2026-007" in self._make().render()

    def test_render_with_delivery(self):
        html = self._make(
            delivery=DeliveryInfo(
                address="42 av. des Champs",
                city="Paris",
                delivery_date="2026-04-15",
            )
        ).render()
        assert "Livraison" in html
        assert "2026-04-15" in html
        assert "Paris" in html

    def test_render_order_ref(self):
        html = self._make(order_ref="INT-REF-999").render()
        assert "INT-REF-999" in html

    def test_render_supplier_ref(self):
        html = self._make(supplier_ref="SUP-REF-001").render()
        assert "SUP-REF-001" in html

    def test_render_confirmation_block(self):
        html = self._make(show_confirmation_block=True).render()
        assert "Accusé de réception" in html

    def test_no_confirmation_block(self):
        html = self._make(show_confirmation_block=False).render()
        assert "Accusé de réception" not in html

    def test_render_payment_terms(self):
        html = self._make(payment_terms="60 jours fin de mois.").render()
        assert "60 jours" in html

    def test_render_with_design(self):
        html = self._make(design=_design()).render()
        assert "#0f172a" in html

    def test_built_in_test(self):
        assert PurchaseOrderDoc.test() is True


# ── BrandDefinition ───────────────────────────────────────────────────────────

class TestBrandDefinition:
    def test_create_minimal(self):
        brand = BrandDefinition(name="TestBrand")
        assert brand.name == "TestBrand"
        assert brand.design == {}

    def test_design_repr(self):
        brand = BrandDefinition(
            name="X",
            design={"palette": {"primary": "#000"}},
        )
        repr_str = brand.design_repr()
        assert '"primary"' in repr_str
        assert '"#000"' in repr_str


# ── InvoiceTemplate ───────────────────────────────────────────────────────────

class TestInvoiceTemplate:
    def test_create_doc(self):
        tmpl = InvoiceTemplate(brand=_brand())
        doc = tmpl.create(
            "FAC-T-001", "2026-03-26",
            client=_client(),
            items=_items(),
        )
        html = doc.render()
        assert "FAC-T-001" in html
        assert "EURKAI SAS" in html

    def test_create_inherits_bank(self):
        tmpl = InvoiceTemplate(brand=_brand())
        doc = tmpl.create("FAC-T-002", "2026-03-26", client=_client(), items=_items())
        html = doc.render()
        assert "BNP Paribas" in html

    def test_generate_install_script_structure(self):
        script = InvoiceTemplate(brand=_brand()).generate_install_script()
        assert "make_invoice" in script
        assert "BRAND_DESIGN" in script
        assert "ISSUER" in script
        assert "from document_objects import" in script

    def test_generate_install_script_runnable(self):
        """Install script must be valid Python syntax."""
        script = InvoiceTemplate(brand=_brand()).generate_install_script()
        compile(script, "<install_script>", "exec")


# ── QuoteTemplate ─────────────────────────────────────────────────────────────

class TestQuoteTemplate:
    def test_create_doc(self):
        tmpl = QuoteTemplate(brand=_brand())
        doc = tmpl.create("DEV-T-001", "2026-03-26", client=_client(), items=_items())
        html = doc.render()
        assert "DEV-T-001" in html
        assert "Devis" in html

    def test_generate_install_script_runnable(self):
        script = QuoteTemplate(brand=_brand()).generate_install_script()
        compile(script, "<install_script>", "exec")


# ── PurchaseOrderTemplate ─────────────────────────────────────────────────────

class TestPurchaseOrderTemplate:
    def test_create_doc(self):
        tmpl = PurchaseOrderTemplate(brand=_brand())
        doc = tmpl.create("BC-T-001", "2026-03-26", client=_client(), items=_items())
        html = doc.render()
        assert "BC-T-001" in html
        assert "Bon de commande" in html

    def test_generate_install_script_runnable(self):
        script = PurchaseOrderTemplate(brand=_brand()).generate_install_script()
        compile(script, "<install_script>", "exec")


# ── TextDocTemplate ───────────────────────────────────────────────────────────

class TestTextDocTemplate:
    def test_create_doc(self):
        tmpl = TextDocTemplate(brand=_brand())
        doc = tmpl.create("Mon doc", [TextBlock(type="paragraph", content="Hello.")])
        html = doc.render()
        assert "Mon doc" in html
        assert "Hello." in html

    def test_generate_install_script_runnable(self):
        script = TextDocTemplate(brand=_brand()).generate_install_script()
        compile(script, "<install_script>", "exec")


# ── SheetDocTemplate ──────────────────────────────────────────────────────────

class TestSheetDocTemplate:
    def test_create_doc(self):
        tmpl = SheetDocTemplate(brand=_brand())
        doc = tmpl.create(
            doc_type="invoice",
            doc_number="FAC-SHT-001",
            doc_date="2026-03-26",
            issuer=IssuerSchema(name="EURKAI SAS"),
            client=ClientSchema(name="Legacy Client"),
            items=[LineItem(description="Service", quantity=1, unit_price=1000.0)],
        )
        html = doc.render()
        assert "FAC-SHT-001" in html
        assert "Legacy Client" in html

    def test_generate_install_script_runnable(self):
        script = SheetDocTemplate(brand=_brand()).generate_install_script()
        compile(script, "<install_script>", "exec")
