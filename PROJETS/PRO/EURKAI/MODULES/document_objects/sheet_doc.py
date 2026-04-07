"""
SheetDoc — Tabular business document object (invoice, quote, order, credit note).

The object owns its render logic. No adapter, no vendor.

Usage:
    from document_objects.sheet_doc import SheetDoc, SheetDocInput, IssuerSchema, ClientSchema, LineItem

    doc = SheetDoc(SheetDocInput(
        doc_type="invoice",
        doc_number="FAC-2026-001",
        doc_date="2026-03-26",
        issuer=IssuerSchema(name="EURKAI SAS", email="contact@eurkai.com"),
        client=ClientSchema(name="Acme Corp"),
        items=[LineItem(description="Design system", quantity=1, unit_price=2500.0)],
    ))
    html = doc.render()
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, model_validator

NAME     = "document.sheet_doc"
CATEGORY = "document"
VERSION  = "1.0.0"


# ── Schemas ──────────────────────────────────────────────────────────────────

class IssuerSchema(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    siret: Optional[str] = None
    logo_url: Optional[str] = None


class ClientSchema(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    ref: Optional[str] = None


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.20
    unit: Optional[str] = None

    @property
    def subtotal_ht(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.subtotal_ht * self.tax_rate, 2)

    @property
    def subtotal_ttc(self) -> float:
        return round(self.subtotal_ht + self.tax_amount, 2)


class SheetDocInput(BaseModel):
    doc_type: Literal["invoice", "quote", "order", "credit_note"] = "invoice"
    doc_number: str
    doc_date: str
    due_date: Optional[str] = None
    issuer: IssuerSchema
    client: ClientSchema
    items: List[LineItem]
    currency: str = "EUR"
    notes: Optional[str] = None
    footer: Optional[str] = None
    design: Optional[Dict[str, Any]] = None


# ── Object ───────────────────────────────────────────────────────────────────

class SheetDoc:
    NAME     = NAME
    CATEGORY = CATEGORY
    VERSION  = VERSION

    _DOC_TYPE_LABELS = {
        "invoice":     "FACTURE",
        "quote":       "DEVIS",
        "order":       "BON DE COMMANDE",
        "credit_note": "AVOIR",
    }
    _CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}

    def __init__(self, data: SheetDocInput) -> None:
        self.data = data

    # ── Computed totals ───────────────────────────────────────────────────────

    @property
    def total_ht(self) -> float:
        return round(sum(i.subtotal_ht for i in self.data.items), 2)

    @property
    def total_tax(self) -> float:
        return round(sum(i.tax_amount for i in self.data.items), 2)

    @property
    def total_ttc(self) -> float:
        return round(self.total_ht + self.total_tax, 2)

    # ── Validate ──────────────────────────────────────────────────────────────

    def validate(self) -> dict:
        errors = []
        if not self.data.doc_number:
            errors.append("doc_number is required")
        if not self.data.items:
            errors.append("at least one line item is required")
        for i, item in enumerate(self.data.items):
            if item.unit_price < 0:
                errors.append(f"item[{i}] unit_price must be >= 0")
            if item.quantity <= 0:
                errors.append(f"item[{i}] quantity must be > 0")
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        d = self.data
        pal  = (d.design or {}).get("palette", {})
        typo = (d.design or {}).get("typography", {})

        primary    = pal.get("primary",    "#0f172a")
        accent     = pal.get("accent",     "#6366f1")
        bg         = pal.get("background", "#ffffff")
        text_color = pal.get("text",       "#1e293b")
        muted      = pal.get("muted",      "#64748b")
        surface    = pal.get("surface",    "#f8fafc")
        border_c   = pal.get("border",     "#e2e8f0")
        font_body  = typo.get("body_font", "Inter, system-ui, sans-serif")
        font_mono  = typo.get("mono_font", "'JetBrains Mono', 'Courier New', monospace")

        cur       = self._CURRENCY_SYMBOLS.get(d.currency, d.currency)
        doc_label = self._DOC_TYPE_LABELS.get(d.doc_type, d.doc_type.upper())

        def fmt(n: float) -> str:
            return f"{n:,.2f}\u202f{cur}".replace(",", "\u202f")

        # ── Issuer block ──────────────────────────────────────────────────────
        issuer_lines = [f'<span style="font-size:15px; font-weight:700; color:{primary};">{d.issuer.name}</span>']
        for f_ in [d.issuer.address,
                   f"{d.issuer.postal_code or ''} {d.issuer.city or ''}".strip() or None,
                   d.issuer.country, d.issuer.email, d.issuer.phone,
                   f"SIRET&nbsp;: {d.issuer.siret}" if d.issuer.siret else None,
                   f"N° TVA&nbsp;: {d.issuer.vat_number}" if d.issuer.vat_number else None]:
            if f_:
                issuer_lines.append(f_)
        issuer_html = "<br>".join(issuer_lines)

        # ── Client block ──────────────────────────────────────────────────────
        client_lines = [f'<span style="font-size:14px; font-weight:700; color:{primary};">{d.client.name}</span>']
        for f_ in [d.client.address,
                   f"{d.client.postal_code or ''} {d.client.city or ''}".strip() or None,
                   d.client.country, d.client.email,
                   f"Réf.&nbsp;: {d.client.ref}" if d.client.ref else None]:
            if f_:
                client_lines.append(f_)
        client_html = "<br>".join(client_lines)

        # ── Logo or monogram ──────────────────────────────────────────────────
        if d.issuer.logo_url:
            logo_html = f'<img src="{d.issuer.logo_url}" style="max-height:52px; max-width:160px; object-fit:contain; display:block; margin-bottom:12px;" alt="{d.issuer.name}">'
        else:
            initial = d.issuer.name[0].upper()
            logo_html = (
                f'<div style="display:inline-flex; align-items:center; justify-content:center; '
                f'width:44px; height:44px; border-radius:8px; background:{primary}; '
                f'color:#fff; font-family:{font_body}; font-size:18px; font-weight:800; margin-bottom:12px;">'
                f'{initial}</div>'
            )

        # ── Doc type badge ────────────────────────────────────────────────────
        due_html = (
            f'<div style="margin-top:6px; font-size:12px; color:{muted};">'
            f'Échéance&nbsp;: <strong style="color:{primary};">{d.due_date}</strong></div>'
        ) if d.due_date else ""

        # ── Line items rows ───────────────────────────────────────────────────
        rows_html = ""
        for idx, item in enumerate(d.items):
            unit_label = f"&thinsp;/&thinsp;{item.unit}" if item.unit else ""
            row_bg = f'background:{surface};' if idx % 2 == 1 else ""
            rows_html += (
                f'<tr style="{row_bg}">'
                f'<td class="td-desc">{item.description}</td>'
                f'<td class="td-num">{item.quantity:g}{unit_label}</td>'
                f'<td class="td-num">{fmt(item.unit_price)}</td>'
                f'<td class="td-num">{int(item.tax_rate * 100)}&nbsp;%</td>'
                f'<td class="td-num td-amount">{fmt(item.subtotal_ht)}</td>'
                f'</tr>'
            )

        # ── Tax breakdown ─────────────────────────────────────────────────────
        tax_groups: Dict[float, float] = {}
        for item in d.items:
            tax_groups[item.tax_rate] = round(tax_groups.get(item.tax_rate, 0) + item.tax_amount, 2)
        tax_rows_html = "".join(
            f'<tr><td style="padding:3px 0; color:{muted}; font-size:12px;">TVA {int(r*100)}&nbsp;%</td>'
            f'<td style="padding:3px 0 3px 24px; text-align:right; font-family:{font_mono}; font-size:12px; color:{muted};">{fmt(a)}</td></tr>'
            for r, a in sorted(tax_groups.items())
        )

        notes_html = (
            f'<div style="margin-bottom:28px; padding:14px 18px; background:{surface}; '
            f'border-left:3px solid {accent}; border-radius:0 6px 6px 0;">'
            f'<p style="margin:0 0 4px; font-size:10px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.08em; color:{accent};">Note</p>'
            f'<p style="margin:0; font-size:12px; color:{muted}; line-height:1.6;">{d.notes}</p></div>'
        ) if d.notes else ""

        footer_html = (
            f'<footer style="margin-top:40px; padding-top:14px; border-top:1px solid {border_c}; '
            f'font-size:10px; color:{muted}; text-align:center; letter-spacing:.02em;">{d.footer}</footer>'
        ) if d.footer else ""

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{doc_label} {d.doc_number}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {font_body};
      font-size: 13px;
      color: {text_color};
      background: {bg};
      max-width: 860px;
      margin: 0 auto;
      line-height: 1.55;
    }}
    .accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, {primary} 0%, {accent} 100%);
    }}
    .doc-body {{ padding: 48px 52px; }}
    .doc-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 36px;
      padding-bottom: 28px;
      border-bottom: 1px solid {border_c};
    }}
    .issuer-info {{ font-size: 12px; color: {muted}; line-height: 1.7; }}
    .doc-badge {{
      text-align: right;
    }}
    .doc-type-label {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .1em;
      color: {accent};
      background: {accent}15;
      padding: 4px 10px;
      border-radius: 99px;
      margin-bottom: 10px;
    }}
    .doc-number-val {{
      font-size: 22px;
      font-weight: 800;
      color: {primary};
      letter-spacing: -.02em;
      line-height: 1;
    }}
    .doc-meta {{
      font-size: 12px;
      color: {muted};
      margin-top: 6px;
      line-height: 1.7;
    }}
    .parties {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 32px;
    }}
    .party-card {{
      padding: 16px 18px;
      border-radius: 8px;
      font-size: 12px;
      color: {muted};
      line-height: 1.75;
    }}
    .party-card.issuer {{
      background: {surface};
      border: 1px solid {border_c};
    }}
    .party-card.client {{
      background: {primary}08;
      border: 1px solid {primary}20;
    }}
    .party-label {{
      font-size: 9px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .12em;
      margin-bottom: 8px;
    }}
    .party-label.issuer-label {{ color: {muted}; }}
    .party-label.client-label {{ color: {accent}; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 0;
    }}
    .table-wrap {{
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid {border_c};
      margin-bottom: 28px;
    }}
    thead tr {{
      background: {primary};
    }}
    thead th {{
      padding: 11px 14px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: rgba(255,255,255,.75);
      text-align: left;
    }}
    thead th.th-num {{ text-align: right; }}
    .td-desc {{
      padding: 11px 14px;
      font-size: 13px;
      color: {text_color};
    }}
    .td-num {{
      padding: 11px 14px;
      text-align: right;
      font-family: {font_mono};
      font-size: 12px;
      color: {muted};
      white-space: nowrap;
    }}
    .td-amount {{
      font-weight: 600;
      color: {text_color};
    }}
    tbody tr:not(:last-child) td {{
      border-bottom: 1px solid {border_c};
    }}
    .totals-block {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 32px;
    }}
    .totals-inner {{
      min-width: 260px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid {border_c};
    }}
    .totals-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 9px 16px;
      font-size: 12px;
      color: {muted};
      border-bottom: 1px solid {border_c};
    }}
    .totals-row .amount {{
      font-family: {font_mono};
      font-size: 12px;
      color: {text_color};
    }}
    .totals-row.ttc {{
      background: {primary};
      padding: 13px 16px;
      border-bottom: none;
    }}
    .totals-row.ttc .label {{
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: rgba(255,255,255,.7);
    }}
    .totals-row.ttc .amount {{
      font-size: 18px;
      font-weight: 800;
      color: #fff;
      font-family: {font_mono};
    }}
  </style>
</head>
<body>
  <div class="accent-bar"></div>
  <div class="doc-body">

    <div class="doc-header">
      <div class="issuer-block">
        {logo_html}
        <div class="issuer-info">{issuer_html}</div>
      </div>
      <div class="doc-badge">
        <div class="doc-type-label">{doc_label}</div>
        <div class="doc-number-val">N°&thinsp;{d.doc_number}</div>
        <div class="doc-meta">
          Date&nbsp;: <strong style="color:{text_color};">{d.doc_date}</strong>
          {due_html}
        </div>
      </div>
    </div>

    <div class="parties">
      <div class="party-card issuer">
        <div class="party-label issuer-label">Émetteur</div>
        {issuer_html}
      </div>
      <div class="party-card client">
        <div class="party-label client-label">Facturé à</div>
        {client_html}
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Désignation</th>
            <th class="th-num">Qté</th>
            <th class="th-num">P.U. HT</th>
            <th class="th-num">TVA</th>
            <th class="th-num">Montant HT</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>

    <div class="totals-block">
      <div class="totals-inner">
        <div class="totals-row">
          <span class="label">Total HT</span>
          <span class="amount">{fmt(self.total_ht)}</span>
        </div>
        <div style="padding:6px 16px 6px; border-bottom:1px solid {border_c};">
          <table style="width:100%; font-size:12px; border-collapse:collapse;">
            <tbody>{tax_rows_html}</tbody>
          </table>
        </div>
        <div class="totals-row">
          <span class="label">Total TVA</span>
          <span class="amount">{fmt(self.total_tax)}</span>
        </div>
        <div class="totals-row ttc">
          <span class="label">Total TTC</span>
          <span class="amount">{fmt(self.total_ttc)}</span>
        </div>
      </div>
    </div>

    {notes_html}
    {footer_html}
  </div>
</body>
</html>"""

    # ── Test ──────────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        doc = cls(SheetDocInput(
            doc_type="invoice",
            doc_number="FAC-2026-TEST",
            doc_date="2026-03-26",
            due_date="2026-04-26",
            issuer=IssuerSchema(
                name="EURKAI SAS",
                address="12 rue de la République",
                city="Paris",
                postal_code="75001",
                country="France",
                email="contact@eurkai.com",
                siret="123 456 789 00010",
            ),
            client=ClientSchema(
                name="Acme Corporation",
                address="456 Business Ave",
                city="Lyon",
                postal_code="69001",
                country="France",
                email="billing@acme.com",
                ref="REF-ACME-2026",
            ),
            items=[
                LineItem(description="Design system complet", quantity=1, unit_price=3500.0),
                LineItem(description="Intégration pipeline IA", quantity=5, unit_price=480.0, unit="j"),
                LineItem(description="Support mensuel", quantity=3, unit_price=200.0, unit="mois"),
            ],
            notes="Paiement par virement bancaire à 30 jours. IBAN disponible sur demande.",
            footer="EURKAI SAS — SIRET 123 456 789 00010 — TVA FR 12 345678900",
        ))
        v = doc.validate()
        assert v["valid"], f"Validation failed: {v['errors']}"
        html = doc.render()
        assert "<table>" in html
        assert "FAC-2026-TEST" in html
        assert "EURKAI SAS" in html
        assert "Acme Corporation" in html
        assert doc.total_ht == 6500.0   # 3500 + 5*480 + 3*200 = 3500+2400+600 = 6500 HT
        assert doc.total_ttc == 7800.0  # 6500 * 1.20
        return True
