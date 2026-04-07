"""
QuoteDoc — Specialized EURKAI object for commercial quotes/proposals.

Uses render_business_doc() from document_base for shared rendering logic.
Adds: validity_date, acceptance_block (signature zone).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .document_base import (
    DocumentIssuer, DocumentClient, DocumentLineItem,
    DocumentPageHeader, DocumentPageFooter,
    render_business_doc,
)


# ── Input schema ──────────────────────────────────────────────────────────────

class QuoteDocInput(BaseModel):
    # Document identity
    doc_number: str
    doc_date: str
    validity_date: Optional[str] = None    # devis valable jusqu'au
    currency: str = "EUR"

    # Parties
    issuer: DocumentIssuer
    client: DocumentClient

    # Line items
    items: List[DocumentLineItem]

    # Quote-specific fields
    show_acceptance_block: bool = True
    acceptance_text: str = (
        "Bon pour accord — Signature et cachet du client :"
    )
    conditions: Optional[str] = (
        "Ce devis est établi sans engagement. Il est valable jusqu'à la date de validité indiquée. "
        "Toute commande entraîne l'acceptation des présentes conditions."
    )

    # Optional extras
    notes: Optional[str] = None
    page_header: Optional[DocumentPageHeader] = None
    page_footer: Optional[DocumentPageFooter] = None
    design: Optional[Dict[str, Any]] = None


# ── QuoteDoc object ───────────────────────────────────────────────────────────

class QuoteDoc:
    """
    Specialized EURKAI object for commercial quotes.

    Usage:
        doc = QuoteDoc(QuoteDocInput(
            doc_number="DEV-2026-042",
            doc_date="2026-03-26",
            validity_date="2026-04-26",
            issuer=DocumentIssuer(name="EURKAI SAS", ...),
            client=DocumentClient(name="Acme Corp", ...),
            items=[DocumentLineItem(description="Conseil", quantity=10, unit_price=150.0)],
        ))
        html = doc.render()
    """

    def __init__(self, inp: QuoteDocInput):
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

    # ── Quote-specific extra blocks ───────────────────────────────────────────

    def _extra_blocks_before_totals(self) -> str:
        inp = self.inp
        if not inp.validity_date:
            return ""
        pal = (inp.design or {}).get("palette", {})
        accent  = pal.get("accent",  "#6366f1")
        muted   = pal.get("muted",   "#64748b")
        primary = pal.get("primary", "#0f172a")

        return (
            f'<div style="margin:0 48px 8px; padding:10px 16px; '
            f'background:{accent}12; border-left:3px solid {accent}; '
            f'border-radius:0 6px 6px 0; font-size:12px; color:{muted};">'
            f'Ce devis est valable jusqu\'au&nbsp;: '
            f'<strong style="color:{primary};">{inp.validity_date}</strong>'
            f'</div>'
        )

    def _extra_blocks_after_totals(self) -> str:
        inp = self.inp
        pal = (inp.design or {}).get("palette", {})
        primary  = pal.get("primary",  "#0f172a")
        accent   = pal.get("accent",   "#6366f1")
        muted    = pal.get("muted",    "#64748b")
        surface  = pal.get("surface",  "#f8fafc")
        border_c = pal.get("border",   "#e2e8f0")

        parts = []

        # General conditions
        if inp.conditions:
            parts.append(
                f'<div style="margin:0 48px 16px; padding:12px 16px; '
                f'background:{surface}; border:1px solid {border_c}; border-radius:8px; '
                f'font-size:11px; color:{muted}80; line-height:1.65; font-style:italic;">'
                f'{inp.conditions}</div>'
            )

        # Acceptance block
        if inp.show_acceptance_block:
            parts.append(
                f'<div style="margin:0 48px 24px; padding:20px 24px; '
                f'border:2px dashed {border_c}; border-radius:10px;">'
                f'<p style="font-size:12px; font-weight:700; color:{primary}; margin-bottom:16px;">'
                f'{inp.acceptance_text}</p>'
                f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">'
                # Left: date + place
                f'<div>'
                f'<p style="font-size:10px; font-weight:700; text-transform:uppercase; '
                f'letter-spacing:.08em; color:{muted}; margin-bottom:8px;">Date et lieu</p>'
                f'<div style="height:36px; border-bottom:1px solid {border_c};"></div>'
                f'</div>'
                # Right: signature
                f'<div>'
                f'<p style="font-size:10px; font-weight:700; text-transform:uppercase; '
                f'letter-spacing:.08em; color:{muted}; margin-bottom:8px;">Signature</p>'
                f'<div style="height:36px; border-bottom:1px solid {border_c};"></div>'
                f'</div>'
                f'</div>'
                f'</div>'
            )

        return "".join(parts)

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        inp = self.inp
        return render_business_doc(
            doc_label="Devis",
            doc_number=inp.doc_number,
            doc_date=inp.doc_date,
            issuer=inp.issuer,
            client=inp.client,
            items=inp.items,
            total_ht=self.total_ht,
            total_tax=self.total_tax,
            total_ttc=self.total_ttc,
            currency=inp.currency,
            due_date=inp.validity_date,
            notes=inp.notes,
            extra_blocks_before_totals=self._extra_blocks_before_totals(),
            extra_blocks_after_totals=self._extra_blocks_after_totals(),
            page_header=inp.page_header,
            page_footer=inp.page_footer,
            design=inp.design,
        )

    # ── Built-in test ─────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        doc = cls(QuoteDocInput(
            doc_number="DEV-2026-042",
            doc_date="2026-03-26",
            validity_date="2026-04-26",
            issuer=DocumentIssuer(
                name="EURKAI SAS",
                email="contact@eurkai.com",
                siret="123 456 789 00012",
            ),
            client=DocumentClient(
                name="Beta Client SARL",
                city="Bordeaux",
            ),
            items=[
                DocumentLineItem(description="Conception UI", quantity=5, unit_price=800.0, unit="j"),
                DocumentLineItem(description="Développement", quantity=10, unit_price=600.0, unit="j"),
            ],
            notes="Prix nets. Frais de déplacement non inclus.",
        ))
        assert doc.validate()["valid"] is True
        assert doc.total_ht == 10000.0
        assert doc.total_ttc == 12000.0
        html = doc.render()
        assert "DEV-2026-042" in html
        assert "Devis" in html
        assert "Beta Client SARL" in html
        assert "2026-04-26" in html
        assert "Bon pour accord" in html
        return True
