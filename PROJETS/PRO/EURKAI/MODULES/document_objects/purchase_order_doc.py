"""
PurchaseOrderDoc — Specialized EURKAI object for purchase orders (bon de commande).

Uses render_business_doc() from document_base for shared rendering logic.
Adds: delivery_address, delivery_date, order_ref.
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

class DeliveryInfo(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_name: Optional[str] = None
    delivery_date: Optional[str] = None
    instructions: Optional[str] = None


class PurchaseOrderDocInput(BaseModel):
    # Document identity
    doc_number: str
    doc_date: str
    currency: str = "EUR"

    # Parties (buyer = issuer, seller = client for POs)
    issuer: DocumentIssuer     # the buying entity
    client: DocumentClient     # the supplier / seller

    # Line items
    items: List[DocumentLineItem]

    # PO-specific fields
    delivery: Optional[DeliveryInfo] = None
    order_ref: Optional[str] = None           # buyer's internal reference
    supplier_ref: Optional[str] = None        # supplier's reference
    show_confirmation_block: bool = True
    payment_terms: Optional[str] = None

    # Optional extras
    notes: Optional[str] = None
    page_header: Optional[DocumentPageHeader] = None
    page_footer: Optional[DocumentPageFooter] = None
    design: Optional[Dict[str, Any]] = None


# ── PurchaseOrderDoc object ───────────────────────────────────────────────────

class PurchaseOrderDoc:
    """
    Specialized EURKAI object for purchase orders (bons de commande).

    Usage:
        doc = PurchaseOrderDoc(PurchaseOrderDocInput(
            doc_number="BC-2026-007",
            doc_date="2026-03-26",
            issuer=DocumentIssuer(name="EURKAI SAS", ...),   # buyer
            client=DocumentClient(name="Supplier Inc", ...),  # seller
            items=[DocumentLineItem(description="Licences logiciels", quantity=5, unit_price=99.0)],
            delivery=DeliveryInfo(address="15 rue de la Paix", city="Paris", delivery_date="2026-04-10"),
        ))
        html = doc.render()
    """

    def __init__(self, inp: PurchaseOrderDocInput):
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

    # ── PO-specific extra blocks ──────────────────────────────────────────────

    def _extra_blocks_before_totals(self) -> str:
        inp = self.inp
        d = inp.delivery
        if not d and not inp.order_ref and not inp.supplier_ref:
            return ""

        pal = (inp.design or {}).get("palette", {})
        primary  = pal.get("primary",  "#0f172a")
        accent   = pal.get("accent",   "#6366f1")
        muted    = pal.get("muted",    "#64748b")
        surface  = pal.get("surface",  "#f8fafc")
        border_c = pal.get("border",   "#e2e8f0")

        parts = []

        # Order refs row
        if inp.order_ref or inp.supplier_ref:
            ref_cells = []
            if inp.order_ref:
                ref_cells.append(
                    f'<div>'
                    f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                    f'letter-spacing:.08em; color:{muted}; margin-bottom:4px;">Réf. interne</p>'
                    f'<p style="font-size:13px; font-weight:600; color:{primary};">{inp.order_ref}</p>'
                    f'</div>'
                )
            if inp.supplier_ref:
                ref_cells.append(
                    f'<div>'
                    f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                    f'letter-spacing:.08em; color:{muted}; margin-bottom:4px;">Réf. fournisseur</p>'
                    f'<p style="font-size:13px; font-weight:600; color:{primary};">{inp.supplier_ref}</p>'
                    f'</div>'
                )
            parts.append(
                f'<div style="margin:0 48px 12px; padding:12px 16px; '
                f'background:{surface}; border:1px solid {border_c}; border-radius:8px; '
                f'display:flex; gap:32px;">'
                + "".join(ref_cells) +
                f'</div>'
            )

        # Delivery block
        if d:
            lines = []
            if d.contact_name:
                lines.append(f'<strong>{d.contact_name}</strong>')
            if d.address:
                lines.append(d.address)
            city_line = f"{d.postal_code or ''} {d.city or ''}".strip()
            if city_line:
                lines.append(city_line)
            if d.country:
                lines.append(d.country)
            if d.instructions:
                lines.append(
                    f'<em style="color:{muted}80; font-size:11px;">{d.instructions}</em>'
                )

            delivery_date_html = ""
            if d.delivery_date:
                delivery_date_html = (
                    f'<div style="margin-top:8px; padding:6px 10px; '
                    f'background:{accent}12; border-radius:6px; '
                    f'font-size:11px; color:{accent}; font-weight:700;">'
                    f'Livraison prévue&nbsp;: {d.delivery_date}</div>'
                )

            parts.append(
                f'<div style="margin:0 48px 12px; padding:14px 18px; '
                f'background:{accent}08; border:1px solid {accent}20; border-radius:8px;">'
                f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                f'letter-spacing:.1em; color:{accent}; margin-bottom:8px;">Adresse de livraison</p>'
                f'<p style="font-size:12px; color:{muted}; line-height:1.75;">'
                + "<br>".join(lines) +
                f'</p>'
                + delivery_date_html +
                f'</div>'
            )

        return "".join(parts)

    def _extra_blocks_after_totals(self) -> str:
        inp = self.inp
        pal = (inp.design or {}).get("palette", {})
        primary  = pal.get("primary",  "#0f172a")
        accent   = pal.get("accent",   "#6366f1")
        muted    = pal.get("muted",    "#64748b")
        surface  = pal.get("surface",  "#f8fafc")
        border_c = pal.get("border",   "#e2e8f0")

        parts = []

        # Payment terms
        if inp.payment_terms:
            parts.append(
                f'<div style="margin:0 48px 16px; padding:12px 16px; '
                f'background:{surface}; border:1px solid {border_c}; border-radius:8px;">'
                f'<p style="font-size:10px; font-weight:800; text-transform:uppercase; '
                f'letter-spacing:.1em; color:{accent}; margin-bottom:4px;">Conditions de paiement</p>'
                f'<p style="font-size:12px; color:{muted}; line-height:1.6;">{inp.payment_terms}</p>'
                f'</div>'
            )

        # Confirmation block
        if inp.show_confirmation_block:
            parts.append(
                f'<div style="margin:0 48px 24px; padding:20px 24px; '
                f'border:2px dashed {border_c}; border-radius:10px;">'
                f'<p style="font-size:12px; font-weight:700; color:{primary}; margin-bottom:4px;">'
                f'Accusé de réception — Fournisseur</p>'
                f'<p style="font-size:11px; color:{muted}; margin-bottom:16px;">'
                f'Le fournisseur confirme la réception de la commande et s\'engage à honorer les délais indiqués.</p>'
                f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">'
                f'<div>'
                f'<p style="font-size:10px; font-weight:700; text-transform:uppercase; '
                f'letter-spacing:.08em; color:{muted}; margin-bottom:8px;">Date</p>'
                f'<div style="height:36px; border-bottom:1px solid {border_c};"></div>'
                f'</div>'
                f'<div>'
                f'<p style="font-size:10px; font-weight:700; text-transform:uppercase; '
                f'letter-spacing:.08em; color:{muted}; margin-bottom:8px;">Signature et cachet</p>'
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
            doc_label="Bon de commande",
            doc_number=inp.doc_number,
            doc_date=inp.doc_date,
            issuer=inp.issuer,
            client=inp.client,
            items=inp.items,
            total_ht=self.total_ht,
            total_tax=self.total_tax,
            total_ttc=self.total_ttc,
            currency=inp.currency,
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
        doc = cls(PurchaseOrderDocInput(
            doc_number="BC-2026-007",
            doc_date="2026-03-26",
            issuer=DocumentIssuer(
                name="EURKAI SAS",
                email="contact@eurkai.com",
                city="Paris",
            ),
            client=DocumentClient(
                name="TechSupply SAS",
                email="orders@techsupply.fr",
            ),
            items=[
                DocumentLineItem(
                    description="Licences logicielles annuelles",
                    quantity=5,
                    unit_price=299.0,
                    unit="licence",
                    tax_rate=0.20,
                ),
                DocumentLineItem(
                    description="Support premium",
                    quantity=1,
                    unit_price=500.0,
                    tax_rate=0.20,
                ),
            ],
            delivery=DeliveryInfo(
                address="15 rue de la Paix",
                city="Paris",
                postal_code="75001",
                delivery_date="2026-04-10",
            ),
            order_ref="BC-INT-2026-007",
            payment_terms="30 jours fin de mois.",
        ))
        assert doc.validate()["valid"] is True
        assert doc.total_ht == 1995.0
        assert doc.total_ttc == 2394.0
        html = doc.render()
        assert "BC-2026-007" in html
        assert "Bon de commande" in html
        assert "TechSupply SAS" in html
        assert "Livraison" in html
        return True
