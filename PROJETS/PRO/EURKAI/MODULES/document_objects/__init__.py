"""
document_objects — EURKAI document/business surface objects.

Each object owns its own render method. No adapter architecture.

v1.0 Objects (visual surfaces):
    SheetDoc        — invoice, quote, order, credit note (generic)
    EmailSignature  — business email signature block
    TextDoc         — proposals, templates, client docs
    DashboardPage   — backoffice / admin / personal space

v1.1 Specialized business documents:
    InvoiceDoc          — commercial invoices with payment terms & bank details
    QuoteDoc            — quotes with validity date & acceptance block
    PurchaseOrderDoc    — purchase orders with delivery info & confirmation block

v1.1 Shared base types:
    DocumentIssuer, DocumentClient, DocumentLineItem
    DocumentPageHeader, DocumentPageFooter
    BankDetails, DeliveryInfo

v1.1 Template objects (brand-wired factories + install script generation):
    BrandDefinition
    InvoiceTemplate, QuoteTemplate, PurchaseOrderTemplate
    TextDocTemplate, SheetDocTemplate

v1.2 Dashboard Intelligence Layer:
    DataPoint, DataSeries
    VisualizationType
    WidgetConfig
    DashboardWidget     — autonomous chart/viz widget with render()
    WidgetSection       — multi-widget section for DashboardPage
    auto_detect_type()  — data → visualization type mapping engine

Usage:
    from document_objects import SheetDoc, EmailSignature, TextDoc, DashboardPage
    from document_objects import InvoiceDoc, QuoteDoc, PurchaseOrderDoc
    from document_objects import BrandDefinition, InvoiceTemplate
    from document_objects import DashboardWidget, WidgetSection, DataPoint, WidgetConfig
"""
# ── v1.0 objects ──────────────────────────────────────────────────────────────
from .sheet_doc        import SheetDoc, SheetDocInput, IssuerSchema, ClientSchema, LineItem
from .email_signature  import EmailSignature, EmailSignatureInput, SocialLink
from .text_doc         import TextDoc, TextDocInput, TextBlock
from .dashboard_page   import (
    DashboardPage, DashboardPageInput,
    NavItem, StatCard, TableSection, CardGridSection, FiltersBar,
)

# ── v1.1 base types ───────────────────────────────────────────────────────────
from .document_base import (
    DocumentIssuer, DocumentClient, DocumentLineItem,
    DocumentPageHeader, DocumentPageFooter,
    fmt_amount, render_business_doc,
)

# ── v1.1 specialized business documents ───────────────────────────────────────
from .invoice_doc        import InvoiceDoc, InvoiceDocInput, BankDetails
from .quote_doc          import QuoteDoc, QuoteDocInput
from .purchase_order_doc import PurchaseOrderDoc, PurchaseOrderDocInput, DeliveryInfo

# ── v1.1 template objects ─────────────────────────────────────────────────────
from .document_templates import (
    BrandDefinition,
    InvoiceTemplate, QuoteTemplate, PurchaseOrderTemplate,
    TextDocTemplate, SheetDocTemplate,
)

# ── v1.2 dashboard intelligence layer ────────────────────────────────────────
from .dashboard_widgets import (
    DataPoint, DataSeries,
    WidgetConfig, DashboardWidget, WidgetSection,
    auto_detect_type,
    Metric, Dataset,
)

__version__ = "1.2.0"

__all__ = [
    # v1.0 — SheetDoc
    "SheetDoc", "SheetDocInput", "IssuerSchema", "ClientSchema", "LineItem",
    # v1.0 — EmailSignature
    "EmailSignature", "EmailSignatureInput", "SocialLink",
    # v1.0 — TextDoc
    "TextDoc", "TextDocInput", "TextBlock",
    # v1.0 — DashboardPage
    "DashboardPage", "DashboardPageInput",
    "NavItem", "StatCard", "TableSection", "CardGridSection", "FiltersBar",
    # v1.1 — base types
    "DocumentIssuer", "DocumentClient", "DocumentLineItem",
    "DocumentPageHeader", "DocumentPageFooter",
    "fmt_amount", "render_business_doc",
    # v1.1 — specialized business documents
    "InvoiceDoc", "InvoiceDocInput", "BankDetails",
    "QuoteDoc", "QuoteDocInput",
    "PurchaseOrderDoc", "PurchaseOrderDocInput", "DeliveryInfo",
    # v1.1 — template objects
    "BrandDefinition",
    "InvoiceTemplate", "QuoteTemplate", "PurchaseOrderTemplate",
    "TextDocTemplate", "SheetDocTemplate",
    # v1.2 — dashboard intelligence layer
    "DataPoint", "DataSeries",
    "WidgetConfig", "DashboardWidget", "WidgetSection",
    "auto_detect_type",
    "Metric", "Dataset",
]
