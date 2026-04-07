"""
InvoiceDoc — Specialized EURKAI object for commercial invoices.

Uses render_business_doc() from document_base for shared rendering logic.
Adds: payment_terms, bank_details, late_payment_clause.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .document_base import (
    DocumentIssuer, DocumentClient, DocumentLineItem,
    DocumentPageHeader, DocumentPageFooter,
    render_business_doc, fmt_amount,
)


# ── Input schema ──────────────────────────────────────────────────────────────

class BankDetails(BaseModel):
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    account_holder: Optional[str] = None


class InvoiceDocInput(BaseModel):
    # Document identity
    doc_number: str
    doc_date: str
    due_date: Optional[str] = None
    currency: str = "EUR"

    # Parties
    issuer: DocumentIssuer
    client: DocumentClient

    # Line items
    items: List[DocumentLineItem]

    # Invoice-specific fields
    payment_terms: Optional[str] = "Paiement à 30 jours nets à compter de la date d'émission."
    late_payment_clause: Optional[str] = (
        "En cas de retard de paiement, des pénalités de 3× le taux d'intérêt légal "
        "seront appliquées, ainsi qu'une indemnité forfaitaire de 40 € pour frais de recouvrement."
    )
    bank_details: Optional[BankDetails] = None

    # Optional extras
    notes: Optional[str] = None
    page_header: Optional[DocumentPageHeader] = None
    page_footer: Optional[DocumentPageFooter] = None
    design: Optional[Dict[str, Any]] = None
    purchase_order_ref: Optional[str] = None   # client's PO reference


# ── InvoiceDoc object ─────────────────────────────────────────────────────────

class InvoiceDoc:
    """
    Specialized EURKAI object for commercial invoices.

    Usage:
        doc = InvoiceDoc(InvoiceDocInput(
            doc_number="FAC-2026-001",
            doc_date="2026-03-26",
            due_date="2026-04-25",
            issuer=DocumentIssuer(name="EURKAI SAS", ...),
            client=DocumentClient(name="Acme Corp", ...),
            items=[DocumentLineItem(description="Conseil", quantity=10, unit_price=150.0)],
        ))
        html = doc.render()
    """

    def __init__(self, inp: InvoiceDocInput):
        self.inp = inp

    # ── Computed totals ────────────────────────────────────────────────────────

    @property
    def total_ht(self) -> float:
        return round(sum(i.subtotal_ht for i in self.inp.items), 2)

    @property
    def total_tax(self) -> float:
        return round(sum(i.tax_amount for i in self.inp.items), 2)

    @property
    def total_ttc(self) -> float:
        return round(self.total_ht + self.total_tax, 2)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self) -> Dict[str, Any]:
        errors: List[str] = []
        if not self.inp.doc_number:
            errors.append("doc_number is required")
        if not self.inp.doc_date:
            errors.append("doc_date is required")
        if not self.inp.items:
            errors.append("At least one line item is required")
        if not self.inp.issuer.name:
            errors.append("issuer.name is required")
        if not self.inp.client.name:
            errors.append("client.name is required")
        for i, item in enumerate(self.inp.items):
            if not item.description:
                errors.append(f"items[{i}].description is required")
            if item.unit_price < 0:
                errors.append(f"items[{i}].unit_price must be >= 0")
            if item.quantity <= 0:
                errors.append(f"items[{i}].quantity must be > 0")
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Invoice-specific extra blocks ─────────────────────────────────────────

    def _extra_blocks_after_totals(self) -> str:
        inp = self.inp
        pal = (inp.design or {}).get("palette", {})
        primary  = pal.get("primary",  "#0f172a")
        accent   = pal.get("accent",   "#6366f1")
        muted    = pal.get("muted",    "#64748b")
        surface  = pal.get("surface",  "#f8fafc")
        border_c = pal.get("border",   "#e2e8f0")

        parts = []

        # PO reference (if any)
        if inp.purchase_order_ref:
            parts.append(
                f'<div style="margin:0 48px 16px; padding:10px 16px; '
                f'background:{surface}; border:1px solid {border_c}; border-radius:8px; '
                f'font-size:12px; color:{muted};">'
                f'<span style="font-weight:700; color:{primary};">Bon de commande réf.&nbsp;:</span> '
                f'{inp.purchase_order_ref}</div>'
            )

        # Payment terms block
        if inp.payment_terms or inp.bank_details or inp.late_payment_clause:
            sections = []

            if inp.payment_terms:
                sections.append(
                    f'<div style="margin-bottom:10px;">'
                    f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                    f'letter-spacing:.1em; color:{accent}; margin-bottom:4px;">Conditions de paiement</p>'
                    f'<p style="font-size:12px; color:{muted}; line-height:1.6;">{inp.payment_terms}</p>'
                    f'</div>'
                )

            if inp.bank_details:
                bd = inp.bank_details
                bank_lines = []
                if bd.account_holder:
                    bank_lines.append(f'<strong>{bd.account_holder}</strong>')
                if bd.bank_name:
                    bank_lines.append(bd.bank_name)
                if bd.iban:
                    bank_lines.append(f'IBAN&nbsp;: <code style="font-size:11px;">{bd.iban}</code>')
                if bd.bic:
                    bank_lines.append(f'BIC&nbsp;: <code style="font-size:11px;">{bd.bic}</code>')
                sections.append(
                    f'<div style="margin-bottom:10px;">'
                    f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                    f'letter-spacing:.1em; color:{accent}; margin-bottom:4px;">Coordonnées bancaires</p>'
                    f'<p style="font-size:12px; color:{muted}; line-height:1.8;">'
                    + "<br>".join(bank_lines) +
                    f'</p></div>'
                )

            if inp.late_payment_clause:
                sections.append(
                    f'<div>'
                    f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                    f'letter-spacing:.1em; color:{muted}; margin-bottom:4px;">Pénalités de retard</p>'
                    f'<p style="font-size:11px; color:{muted}80; line-height:1.6; font-style:italic;">'
                    f'{inp.late_payment_clause}</p></div>'
                )

            parts.append(
                f'<div style="margin:0 48px 24px; padding:18px 20px; '
                f'background:{surface}; border:1px solid {border_c}; border-radius:10px;">'
                + "".join(sections) +
                f'</div>'
            )

        return "".join(parts)

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        inp = self.inp
        return render_business_doc(
            doc_label="Facture",
            doc_number=inp.doc_number,
            doc_date=inp.doc_date,
            issuer=inp.issuer,
            client=inp.client,
            items=inp.items,
            total_ht=self.total_ht,
            total_tax=self.total_tax,
            total_ttc=self.total_ttc,
            currency=inp.currency,
            due_date=inp.due_date,
            notes=inp.notes,
            extra_blocks_after_totals=self._extra_blocks_after_totals(),
            page_header=inp.page_header,
            page_footer=inp.page_footer,
            design=inp.design,
        )

    # ── Built-in test ─────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        doc = cls(InvoiceDocInput(
            doc_number="FAC-2026-001",
            doc_date="2026-03-26",
            due_date="2026-04-25",
            issuer=DocumentIssuer(
                name="EURKAI SAS",
                address="15 rue de la Paix",
                city="Paris",
                postal_code="75001",
                siret="123 456 789 00012",
                vat_number="FR12 123456789",
                email="contact@eurkai.com",
            ),
            client=DocumentClient(
                name="Acme Corp",
                address="42 avenue des Champs",
                city="Lyon",
                postal_code="69001",
                email="acme@example.com",
            ),
            items=[
                DocumentLineItem(
                    description="Audit stratégique",
                    quantity=1,
                    unit_price=2500.0,
                    tax_rate=0.20,
                ),
                DocumentLineItem(
                    description="Développement — sprint 1",
                    quantity=10,
                    unit_price=150.0,
                    unit="j",
                    tax_rate=0.20,
                ),
                DocumentLineItem(
                    description="Formation équipe",
                    quantity=2,
                    unit_price=800.0,
                    unit="j",
                    tax_rate=0.20,
                    note="2 sessions de 4h",
                ),
            ],
            payment_terms="Paiement à 30 jours nets.",
            bank_details=BankDetails(
                bank_name="BNP Paribas",
                iban="FR76 3000 4000 0100 0000 0012 345",
                bic="BNPAFRPPXXX",
            ),
            notes="TVA acquittée sur les débits. Merci pour votre confiance.",
        ))
        # 2500 + (10×150) + (2×800) = 2500 + 1500 + 1600 = 5600 HT
        assert doc.validate()["valid"] is True
        assert doc.total_ht == 5600.0
        assert doc.total_ttc == 6720.0
        html = doc.render()
        assert "FAC-2026-001" in html
        assert "EURKAI SAS" in html
        assert "Acme Corp" in html
        assert "Facture" in html
        assert "BNP Paribas" in html
        assert "Paiement" in html
        return True
