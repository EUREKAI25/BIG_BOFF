"""
document_base — Canonical shared types and page-level structures for EURKAI document objects.

Provides:
  - DocumentPageHeader  : document-level page header (brand mark, doc metadata, page numbering)
  - DocumentPageFooter  : document-level page footer (legal info, company line, payment terms)
  - DocumentIssuer      : canonical issuer identity (used by InvoiceDoc, QuoteDoc, PurchaseOrderDoc)
  - DocumentClient      : canonical client identity
  - DocumentLineItem    : canonical line item with computed HT/TVA/TTC properties
  - render_business_doc(): shared HTML renderer for tabular business documents

These are NOT website header/footer components.
They are document page structures, equivalent to headers/footers in Word or Google Docs.

SheetDoc continues to use its own inline schemas for backward compatibility.
InvoiceDoc, QuoteDoc, PurchaseOrderDoc use the canonical types from this module.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# ── Canonical document identity schemas ──────────────────────────────────────

class DocumentIssuer(BaseModel):
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
    website: Optional[str] = None


class DocumentClient(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ref: Optional[str] = None


class DocumentLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.20
    unit: Optional[str] = None
    note: Optional[str] = None   # optional sub-line note

    @property
    def subtotal_ht(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.subtotal_ht * self.tax_rate, 2)

    @property
    def subtotal_ttc(self) -> float:
        return round(self.subtotal_ht + self.tax_amount, 2)


# ── Document page structures ──────────────────────────────────────────────────

class DocumentPageHeader(BaseModel):
    """
    Document-level page header.
    Appears at the top of each printed/rendered page.
    NOT a website navigation header.
    """
    brand_name: Optional[str] = None
    brand_tagline: Optional[str] = None
    logo_url: Optional[str] = None
    show_doc_number: bool = True
    show_doc_date: bool = True
    show_due_date: bool = True
    show_page_number: bool = False   # for multi-page PDFs
    custom_right_block: Optional[str] = None  # raw HTML escape hatch


class DocumentPageFooter(BaseModel):
    """
    Document-level page footer.
    Appears at the bottom of each printed/rendered page.
    NOT a website footer.
    """
    company_line: Optional[str] = None      # "EURKAI SAS — SIRET 123... — TVA FR..."
    legal_text: Optional[str] = None        # legal mentions obligatoires
    payment_terms: Optional[str] = None     # "Paiement à 30 jours net. Pénalités: 3× taux légal."
    show_page_number: bool = True
    custom_html: Optional[str] = None       # raw HTML escape hatch


# ── Currency helpers ──────────────────────────────────────────────────────────

_CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}


def fmt_amount(n: float, currency: str = "EUR") -> str:
    sym = _CURRENCY_SYMBOLS.get(currency, currency)
    return f"{n:,.2f}\u202f{sym}".replace(",", "\u202f")


# ── Shared HTML renderer ──────────────────────────────────────────────────────

def render_business_doc(
    *,
    doc_label: str,
    doc_number: str,
    doc_date: str,
    issuer: DocumentIssuer,
    client: DocumentClient,
    items: List[DocumentLineItem],
    total_ht: float,
    total_tax: float,
    total_ttc: float,
    currency: str = "EUR",
    due_date: Optional[str] = None,
    notes: Optional[str] = None,
    extra_blocks_before_totals: str = "",   # e.g. delivery info, acceptance block
    extra_blocks_after_totals: str = "",    # e.g. payment terms, bank details, acceptance signature
    page_header: Optional[DocumentPageHeader] = None,
    page_footer: Optional[DocumentPageFooter] = None,
    design: Optional[Dict[str, Any]] = None,
    title_override: Optional[str] = None,
) -> str:
    """
    Shared HTML renderer for tabular business documents.
    Used by InvoiceDoc, QuoteDoc, PurchaseOrderDoc.
    """
    pal  = (design or {}).get("palette", {})
    typo = (design or {}).get("typography", {})

    primary   = pal.get("primary",    "#0f172a")
    accent    = pal.get("accent",     "#6366f1")
    bg        = pal.get("background", "#ffffff")
    text_c    = pal.get("text",       "#1e293b")
    muted     = pal.get("muted",      "#64748b")
    surface   = pal.get("surface",    "#f8fafc")
    border_c  = pal.get("border",     "#e2e8f0")
    font_body = typo.get("body_font",    "Inter, system-ui, sans-serif")
    font_mono = typo.get("mono_font",    "'JetBrains Mono', 'Courier New', monospace")
    font_disp = typo.get("display_font", font_body)

    fmt = lambda n: fmt_amount(n, currency)

    # ── Page header rendering ─────────────────────────────────────────────────
    ph = page_header or DocumentPageHeader()

    if ph.logo_url:
        brand_left = (
            f'<img src="{ph.logo_url}" style="max-height:48px; max-width:160px; '
            f'object-fit:contain; display:block; margin-bottom:8px;" alt="{issuer.name}">'
        )
    elif ph.brand_name or issuer.name:
        bname = ph.brand_name or issuer.name
        initial = bname[0].upper()
        brand_left = (
            f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">'
            f'<div style="width:36px; height:36px; border-radius:8px; background:{primary}; '
            f'color:#fff; font-family:{font_body}; font-size:15px; font-weight:800; '
            f'text-align:center; line-height:36px; flex-shrink:0;">{initial}</div>'
            f'<span style="font-family:{font_disp}; font-size:17px; font-weight:600; '
            f'color:{primary}; letter-spacing:-.01em;">{bname}</span>'
            f'</div>'
        )
    else:
        brand_left = ""

    tagline_html = (
        f'<p style="font-size:11px; color:{muted}; margin:0 0 4px; font-style:italic;">'
        f'{ph.brand_tagline}</p>'
    ) if ph.brand_tagline else ""

    issuer_lines = []
    for f_ in [issuer.address,
               f"{issuer.postal_code or ''} {issuer.city or ''}".strip() or None,
               issuer.country, issuer.email, issuer.phone]:
        if f_:
            issuer_lines.append(f_)
    issuer_contact_html = "<br>".join(issuer_lines)

    # Right block: doc badge
    if ph.custom_right_block:
        right_block = ph.custom_right_block
    else:
        due_line = (
            f'<div style="margin-top:5px; font-size:12px; color:{muted};">'
            f'Échéance&nbsp;: <strong style="color:{primary};">{due_date}</strong></div>'
        ) if (due_date and ph.show_due_date) else ""

        date_line = (
            f'<div style="font-size:12px; color:{muted}; margin-top:4px;">'
            f'Date&nbsp;: <strong style="color:{text_c};">{doc_date}</strong>{due_line}</div>'
        ) if ph.show_doc_date else ""

        num_line = (
            f'<div style="font-size:24px; font-weight:900; color:{primary}; '
            f'font-family:{font_disp}; letter-spacing:-.03em; line-height:1;">N°&thinsp;{doc_number}</div>'
        ) if ph.show_doc_number else ""

        right_block = (
            f'<div style="text-align:right;">'
            f'<div style="display:inline-block; padding:4px 12px; background:{accent}15; '
            f'border-radius:99px; font-size:10px; font-weight:800; text-transform:uppercase; '
            f'letter-spacing:.1em; color:{accent}; margin-bottom:10px;">{doc_label}</div>'
            f'{num_line}'
            f'{date_line}'
            f'</div>'
        )

    page_header_html = (
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; '
        f'padding:36px 48px 28px; border-bottom:1px solid {border_c};">'
        f'<div>'
        f'{brand_left}'
        f'{tagline_html}'
        f'<div style="font-size:11px; color:{muted}; line-height:1.7; margin-top:4px;">'
        f'{issuer_contact_html}</div>'
        f'</div>'
        f'{right_block}'
        f'</div>'
    )

    # ── Parties block ─────────────────────────────────────────────────────────
    issuer_party = [f'<span style="font-size:14px; font-weight:700; color:{primary};">{issuer.name}</span>']
    for f_ in [issuer.address, f"{issuer.postal_code or ''} {issuer.city or ''}".strip() or None,
               issuer.country, issuer.email, issuer.phone,
               f"SIRET&nbsp;: {issuer.siret}" if issuer.siret else None,
               f"N° TVA&nbsp;: {issuer.vat_number}" if issuer.vat_number else None]:
        if f_:
            issuer_party.append(f_)

    client_party = [f'<span style="font-size:14px; font-weight:700; color:{primary};">{client.name}</span>']
    for f_ in [client.address, f"{client.postal_code or ''} {client.city or ''}".strip() or None,
               client.country, client.email, client.phone,
               f"Réf.&nbsp;: {client.ref}" if client.ref else None]:
        if f_:
            client_party.append(f_)

    parties_html = (
        f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; '
        f'padding:24px 48px; border-bottom:1px solid {border_c};">'
        f'<div style="padding:16px 18px; background:{surface}; border:1px solid {border_c}; '
        f'border-radius:8px; font-size:12px; color:{muted}; line-height:1.75;">'
        f'<div style="font-size:9px; font-weight:800; text-transform:uppercase; '
        f'letter-spacing:.12em; color:{muted}; margin-bottom:8px;">Émetteur</div>'
        f'{"<br>".join(issuer_party)}'
        f'</div>'
        f'<div style="padding:16px 18px; background:{primary}08; '
        f'border:1px solid {primary}20; border-radius:8px; '
        f'font-size:12px; color:{muted}; line-height:1.75;">'
        f'<div style="font-size:9px; font-weight:800; text-transform:uppercase; '
        f'letter-spacing:.12em; color:{accent}; margin-bottom:8px;">Facturé à</div>'
        f'{"<br>".join(client_party)}'
        f'</div>'
        f'</div>'
    )

    # ── Line items table ──────────────────────────────────────────────────────
    rows_html = ""
    for idx, item in enumerate(items):
        unit_label = f"&thinsp;/&thinsp;{item.unit}" if item.unit else ""
        row_bg = f"background:{surface};" if idx % 2 == 1 else ""
        note_cell = (
            f'<br><span style="font-size:11px; color:{muted}; font-style:italic;">{item.note}</span>'
            if item.note else ""
        )
        rows_html += (
            f'<tr style="{row_bg}">'
            f'<td style="padding:11px 16px; font-size:13px; color:{text_c};">'
            f'{item.description}{note_cell}</td>'
            f'<td style="padding:11px 16px; text-align:right; font-family:{font_mono}; '
            f'font-size:12px; color:{muted}; white-space:nowrap;">'
            f'{item.quantity:g}{unit_label}</td>'
            f'<td style="padding:11px 16px; text-align:right; font-family:{font_mono}; '
            f'font-size:12px; color:{muted}; white-space:nowrap;">{fmt(item.unit_price)}</td>'
            f'<td style="padding:11px 16px; text-align:right; font-family:{font_mono}; '
            f'font-size:12px; color:{muted}; white-space:nowrap;">{int(item.tax_rate*100)}&nbsp;%</td>'
            f'<td style="padding:11px 16px; text-align:right; font-family:{font_mono}; '
            f'font-size:12px; font-weight:600; color:{text_c}; white-space:nowrap;">'
            f'{fmt(item.subtotal_ht)}</td>'
            f'</tr>'
        )
        if idx < len(items) - 1:
            rows_html += (
                f'<tr><td colspan="5" style="border-bottom:1px solid {border_c}; padding:0;"></td></tr>'
            )

    table_html = (
        f'<div style="padding:24px 48px;">'
        f'<div style="border-radius:10px; overflow:hidden; border:1px solid {border_c};">'
        f'<table style="width:100%; border-collapse:collapse; font-family:{font_body};">'
        f'<thead><tr style="background:{primary};">'
        f'<th style="padding:11px 16px; text-align:left; font-size:10px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7);">Désignation</th>'
        f'<th style="padding:11px 16px; text-align:right; font-size:10px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7);">Qté</th>'
        f'<th style="padding:11px 16px; text-align:right; font-size:10px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7);">P.U. HT</th>'
        f'<th style="padding:11px 16px; text-align:right; font-size:10px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7);">TVA</th>'
        f'<th style="padding:11px 16px; text-align:right; font-size:10px; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:.08em; color:rgba(255,255,255,.7);">Montant HT</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
        f'</div>'
        f'</div>'
    )

    # ── Tax breakdown + totals ────────────────────────────────────────────────
    tax_groups: Dict[float, float] = {}
    for item in items:
        tax_groups[item.tax_rate] = round(tax_groups.get(item.tax_rate, 0) + item.tax_amount, 2)

    tax_rows = "".join(
        f'<div style="display:flex; justify-content:space-between; padding:4px 0; '
        f'font-size:12px; color:{muted};">'
        f'<span>TVA {int(r*100)}&nbsp;%</span>'
        f'<span style="font-family:{font_mono};">{fmt(a)}</span>'
        f'</div>'
        for r, a in sorted(tax_groups.items())
    )

    totals_html = (
        f'<div style="display:flex; justify-content:flex-end; padding:0 48px 28px;">'
        f'<div style="min-width:280px; border-radius:10px; overflow:hidden; border:1px solid {border_c};">'
        f'<div style="padding:12px 18px; border-bottom:1px solid {border_c}; '
        f'display:flex; justify-content:space-between; font-size:13px; color:{muted};">'
        f'<span>Total HT</span>'
        f'<span style="font-family:{font_mono}; color:{text_c};">{fmt(total_ht)}</span>'
        f'</div>'
        f'<div style="padding:8px 18px; border-bottom:1px solid {border_c}; background:{surface};">'
        f'{tax_rows}'
        f'</div>'
        f'<div style="padding:12px 18px; border-bottom:1px solid {border_c}; '
        f'display:flex; justify-content:space-between; font-size:13px; color:{muted};">'
        f'<span>Total TVA</span>'
        f'<span style="font-family:{font_mono}; color:{text_c};">{fmt(total_tax)}</span>'
        f'</div>'
        f'<div style="padding:15px 18px; background:{primary}; '
        f'display:flex; justify-content:space-between; align-items:center;">'
        f'<span style="font-size:12px; font-weight:700; text-transform:uppercase; '
        f'letter-spacing:.06em; color:rgba(255,255,255,.7);">Total TTC</span>'
        f'<span style="font-size:20px; font-weight:900; color:#fff; '
        f'font-family:{font_mono}; letter-spacing:-.02em;">{fmt(total_ttc)}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes_html = ""
    if notes:
        notes_html = (
            f'<div style="margin:0 48px 24px; padding:14px 18px; background:{surface}; '
            f'border-left:3px solid {accent}; border-radius:0 6px 6px 0;">'
            f'<p style="margin:0 0 4px; font-size:10px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:.08em; color:{accent};">Note</p>'
            f'<p style="margin:0; font-size:12px; color:{muted}; line-height:1.65;">{notes}</p>'
            f'</div>'
        )

    # ── Page footer ───────────────────────────────────────────────────────────
    pf = page_footer or DocumentPageFooter()
    footer_parts = []
    if pf.company_line:
        footer_parts.append(f'<span>{pf.company_line}</span>')
    if pf.legal_text:
        footer_parts.append(f'<span style="color:{muted}60;">{pf.legal_text}</span>')
    if pf.payment_terms:
        footer_parts.append(f'<em style="color:{muted}80;">{pf.payment_terms}</em>')
    if pf.show_page_number:
        footer_parts.append('<span style="margin-left:auto;">Page 1 / 1</span>')

    if pf.custom_html:
        page_footer_html = (
            f'<div style="margin:24px 48px 0; padding-top:16px; '
            f'border-top:1px solid {border_c};">{pf.custom_html}</div>'
        )
    elif footer_parts:
        page_footer_html = (
            f'<div style="margin:24px 48px 0; padding:12px 0 32px; '
            f'border-top:1px solid {border_c}; display:flex; flex-wrap:wrap; gap:8px 24px; '
            f'font-size:10px; color:{muted}; line-height:1.6;">'
            + "".join(footer_parts) +
            f'</div>'
        )
    else:
        page_footer_html = f'<div style="height:32px;"></div>'

    # ── Assemble ──────────────────────────────────────────────────────────────
    title = title_override or f"{doc_label} {doc_number}"

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {font_body};
      font-size: 13px;
      color: {text_c};
      background: {bg};
      -webkit-font-smoothing: antialiased;
    }}
    .accent-bar {{
      height: 4px;
      background: linear-gradient(90deg, {primary} 0%, {accent} 100%);
    }}
  </style>
</head>
<body>
  <div class="accent-bar"></div>
  {page_header_html}
  {parties_html}
  {extra_blocks_before_totals}
  {table_html}
  {totals_html}
  {extra_blocks_after_totals}
  {notes_html}
  {page_footer_html}
</body>
</html>"""
