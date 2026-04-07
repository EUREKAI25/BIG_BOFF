"""
TextDoc — Core textual document object (proposals, templates, client docs, internal docs).

The object owns its render logic. Not a Google Docs / Word adapter.

Usage:
    from document_objects.text_doc import TextDoc, TextDocInput, TextBlock

    doc = TextDoc(TextDocInput(
        title="Proposition commerciale",
        subtitle="EURKAI × Acme Corp — Mars 2026",
        blocks=[
            TextBlock(type="heading", content="Contexte", level=2),
            TextBlock(type="paragraph", content="Votre entreprise cherche à automatiser..."),
            TextBlock(type="bullet_list", items=["Point A", "Point B", "Point C"]),
            TextBlock(type="callout", content="Notre approche réduit les coûts de 40%."),
            TextBlock(type="separator"),
            TextBlock(type="footer", content="EURKAI SAS — contact@eurkai.com"),
        ],
    ))
    html = doc.render()
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

NAME     = "document.text_doc"
CATEGORY = "document"
VERSION  = "1.0.0"


# ── Schemas ──────────────────────────────────────────────────────────────────

BlockType = Literal[
    "title",
    "subtitle",
    "heading",
    "paragraph",
    "bullet_list",
    "numbered_list",
    "callout",
    "separator",
    "footer",
    "quote",
    "code",
]


class TextBlock(BaseModel):
    type: BlockType
    content: Optional[str] = None
    items: Optional[List[str]] = None   # for bullet_list / numbered_list
    level: int = 2                       # for heading (h2-h4)
    callout_variant: Literal["info", "warning", "success", "neutral"] = "neutral"


class TextDocInput(BaseModel):
    title: str
    subtitle: Optional[str] = None
    doc_number: Optional[str] = None
    doc_date: Optional[str] = None
    author: Optional[str] = None
    blocks: List[TextBlock]
    design: Optional[Dict[str, Any]] = None


# ── Object ───────────────────────────────────────────────────────────────────

_CALLOUT_COLORS = {
    "info":    ("#eff6ff", "#3b82f6", "#1e40af"),
    "warning": ("#fffbeb", "#f59e0b", "#92400e"),
    "success": ("#f0fdf4", "#22c55e", "#166534"),
    "neutral": ("#f9fafb", "#9ca3af", "#374151"),
}


class TextDoc:
    NAME     = NAME
    CATEGORY = CATEGORY
    VERSION  = VERSION

    def __init__(self, data: TextDocInput) -> None:
        self.data = data

    # ── Validate ──────────────────────────────────────────────────────────────

    def validate(self) -> dict:
        errors = []
        if not self.data.title:
            errors.append("title is required")
        if not self.data.blocks:
            errors.append("at least one block is required")
        for i, block in enumerate(self.data.blocks):
            if block.type in ("bullet_list", "numbered_list") and not block.items:
                errors.append(f"block[{i}] ({block.type}) requires items")
            if block.type not in ("separator",) and block.type not in ("bullet_list", "numbered_list"):
                if not block.content:
                    errors.append(f"block[{i}] ({block.type}) requires content")
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Block renderers ───────────────────────────────────────────────────────

    def _render_block(self, block: TextBlock, pal: dict, typo: dict) -> str:
        primary   = pal.get("primary", "#0f172a")
        accent    = pal.get("accent",  "#6366f1")
        muted     = pal.get("muted",   "#64748b")
        border_c  = pal.get("border",  "#e2e8f0")
        font_body = typo.get("body_font", "Inter, system-ui, sans-serif")
        font_mono = typo.get("mono_font", "'JetBrains Mono', 'Courier New', monospace")

        t = block.type

        if t == "title":
            return (
                f'<h1 class="block-title" style="font-size:30px; font-weight:900; '
                f'color:{primary}; margin:0 0 6px; line-height:1.15; letter-spacing:-.03em;">'
                f'{block.content}</h1>'
            )

        elif t == "subtitle":
            return (
                f'<p class="block-subtitle" style="font-size:17px; color:{muted}; '
                f'margin:0 0 28px; font-style:italic; font-weight:400; line-height:1.5;">'
                f'{block.content}</p>'
            )

        elif t == "heading":
            level = max(2, min(4, block.level))
            cfg = {
                2: (f"font-size:19px; font-weight:800; color:{primary}; margin:40px 0 14px; "
                    f"padding-bottom:8px; border-bottom:2px solid {accent}20; letter-spacing:-.01em;"),
                3: (f"font-size:15px; font-weight:700; color:{accent}; margin:32px 0 10px; "
                    f"text-transform:uppercase; letter-spacing:.06em;"),
                4: (f"font-size:13px; font-weight:700; color:{primary}; margin:24px 0 8px; "
                    f"text-transform:uppercase; letter-spacing:.08em;"),
            }
            return f'<h{level} style="{cfg[level]}">{block.content}</h{level}>'

        elif t == "paragraph":
            return (
                f'<p style="margin:0 0 18px; line-height:1.8; color:inherit; font-size:14px;">'
                f'{block.content}</p>'
            )

        elif t == "bullet_list":
            items_html = "".join(
                f'<li style="margin-bottom:7px; padding-left:4px;">{item}</li>'
                for item in (block.items or [])
            )
            return (
                f'<ul style="margin:0 0 20px; padding-left:0; list-style:none;">'
                f'<style>.custom-li::before{{content:"▸"; color:{accent}; '
                f'font-weight:700; margin-right:8px;}}</style>'
                + "".join(
                    f'<li style="margin-bottom:8px; padding-left:20px; position:relative; '
                    f'line-height:1.65; font-size:14px;">'
                    f'<span style="position:absolute; left:0; color:{accent}; font-weight:700;">▸</span>'
                    f'{item}</li>'
                    for item in (block.items or [])
                )
                + '</ul>'
            )

        elif t == "numbered_list":
            items_html = "".join(
                f'<li style="margin-bottom:8px; padding-left:4px; line-height:1.65; '
                f'font-size:14px; counter-increment:ol-counter;">'
                f'<span style="color:{accent}; font-weight:700; margin-right:10px; '
                f'font-variant-numeric:tabular-nums; min-width:18px; display:inline-block;">'
                f'{i+1}.</span>{item}</li>'
                for i, item in enumerate(block.items or [])
            )
            return f'<ol style="margin:0 0 20px; padding-left:0; list-style:none;">{items_html}</ol>'

        elif t == "callout":
            _ICONS = {"info": "ℹ", "warning": "⚠", "success": "✓", "neutral": "·"}
            bg, border, text = _CALLOUT_COLORS.get(block.callout_variant, _CALLOUT_COLORS["neutral"])
            icon = _ICONS.get(block.callout_variant, "·")
            return (
                f'<div style="display:flex; gap:12px; background:{bg}; border-left:4px solid {border}; '
                f'padding:14px 18px; border-radius:0 8px 8px 0; margin:0 0 20px; align-items:flex-start;">'
                f'<span style="color:{border}; font-size:15px; font-weight:900; flex-shrink:0; '
                f'margin-top:1px;">{icon}</span>'
                f'<p style="margin:0; color:{text}; font-size:13px; line-height:1.65;">'
                f'{block.content}</p></div>'
            )

        elif t == "separator":
            return (
                f'<div style="margin:36px 0; display:flex; align-items:center; gap:12px;">'
                f'<div style="flex:1; height:1px; background:{border_c};"></div>'
                f'<div style="width:6px; height:6px; border-radius:50%; background:{accent}40;"></div>'
                f'<div style="flex:1; height:1px; background:{border_c};"></div>'
                f'</div>'
            )

        elif t == "footer":
            return (
                f'<div style="margin-top:56px; padding-top:16px; border-top:1px solid {border_c}; '
                f'font-size:11px; color:{muted}; line-height:1.6; letter-spacing:.01em;">'
                f'{block.content}</div>'
            )

        elif t == "quote":
            return (
                f'<blockquote style="margin:0 0 24px; padding:20px 24px 20px 28px; '
                f'border-left:4px solid {accent}; background:{accent}06; border-radius:0 8px 8px 0;">'
                f'<p style="margin:0; font-size:16px; font-style:italic; color:{primary}; '
                f'line-height:1.6; font-weight:500;">{block.content}</p>'
                f'</blockquote>'
            )

        elif t == "code":
            return (
                f'<div style="margin:0 0 20px; border-radius:8px; overflow:hidden; '
                f'border:1px solid #1e293b30;">'
                f'<div style="background:#0f172a; padding:8px 14px; display:flex; '
                f'align-items:center; gap:6px;">'
                f'<span style="width:10px; height:10px; border-radius:50%; background:#ef4444; display:inline-block;"></span>'
                f'<span style="width:10px; height:10px; border-radius:50%; background:#f59e0b; display:inline-block;"></span>'
                f'<span style="width:10px; height:10px; border-radius:50%; background:#22c55e; display:inline-block;"></span>'
                f'</div>'
                f'<pre style="background:#1e293b; color:#e2e8f0; font-family:{font_mono}; '
                f'font-size:12.5px; padding:16px 18px; margin:0; overflow-x:auto; line-height:1.6;">'
                f'<code>{block.content}</code></pre></div>'
            )

        return f'<div style="margin:0 0 18px;">{block.content or ""}</div>'

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        d = self.data
        pal  = (d.design or {}).get("palette", {})
        typo = (d.design or {}).get("typography", {})

        primary    = pal.get("primary",    "#0f172a")
        accent     = pal.get("accent",     "#6366f1")
        bg         = pal.get("background", "#ffffff")
        text_color = pal.get("text",       "#334155")
        muted      = pal.get("muted",      "#64748b")
        surface    = pal.get("surface",    "#f8fafc")
        border_c   = pal.get("border",     "#e2e8f0")
        font_body  = typo.get("body_font", "Inter, system-ui, sans-serif")

        # ── Meta pills ────────────────────────────────────────────────────────
        meta_pills = []
        if d.doc_number:
            meta_pills.append(f'<span class="meta-pill">N°&thinsp;{d.doc_number}</span>')
        if d.doc_date:
            meta_pills.append(f'<span class="meta-pill">{d.doc_date}</span>')
        if d.author:
            meta_pills.append(f'<span class="meta-pill">Par&nbsp;{d.author}</span>')
        meta_html = (
            f'<div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:36px;">'
            + "".join(meta_pills) +
            f'</div>'
        ) if meta_pills else ""

        subtitle_html = ""
        if d.subtitle:
            subtitle_html = (
                f'<p style="font-size:17px; color:{muted}; margin:8px 0 0; '
                f'font-style:italic; font-family:{font_body}; line-height:1.5;">{d.subtitle}</p>'
            )

        blocks_html = "\n".join(self._render_block(b, pal, typo) for b in d.blocks)

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{d.title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {font_body};
      font-size: 14px;
      color: {text_color};
      background: {bg};
      line-height: 1.7;
    }}
    .page-chrome {{
      display: flex;
      min-height: 100vh;
    }}
    .accent-spine {{
      width: 4px;
      background: linear-gradient(180deg, {primary} 0%, {accent} 100%);
      flex-shrink: 0;
    }}
    .doc-content {{
      flex: 1;
      padding: 56px 64px;
      max-width: 800px;
    }}
    .doc-cover {{
      margin-bottom: 40px;
      padding-bottom: 28px;
      border-bottom: 1px solid {border_c};
    }}
    .meta-pill {{
      display: inline-block;
      padding: 3px 10px;
      background: {surface};
      border: 1px solid {border_c};
      border-radius: 99px;
      font-size: 11px;
      color: {muted};
      font-weight: 500;
      letter-spacing: .02em;
    }}
    .doc-body p:last-child {{
      margin-bottom: 0;
    }}
  </style>
</head>
<body>
  <div class="page-chrome">
    <div class="accent-spine"></div>
    <div class="doc-content">
      <div class="doc-cover">
        <h1 style="font-size:30px; font-weight:900; color:{primary}; line-height:1.15; letter-spacing:-.03em;">{d.title}</h1>
        {subtitle_html}
      </div>
      {meta_html}
      <div class="doc-body">
        {blocks_html}
      </div>
    </div>
  </div>
</body>
</html>"""

    # ── Test ──────────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        doc = cls(TextDocInput(
            title="Proposition commerciale",
            subtitle="EURKAI × Acme Corp — Mars 2026",
            doc_number="PROP-2026-007",
            doc_date="2026-03-26",
            author="Nathalie Dupont",
            blocks=[
                TextBlock(type="heading", content="Contexte", level=2),
                TextBlock(type="paragraph", content="Votre entreprise cherche à automatiser son pipeline de design."),
                TextBlock(type="bullet_list", items=["Réduction des coûts", "Scalabilité internationale", "IA intégrée"]),
                TextBlock(type="callout", content="Notre approche réduit les délais de 40%.", callout_variant="success"),
                TextBlock(type="heading", content="Livrables", level=3),
                TextBlock(type="numbered_list", items=["Design system complet", "Pipeline automatisé", "Formation équipe"]),
                TextBlock(type="separator"),
                TextBlock(type="quote", content="EURKAI est l'IA qui construit, pas seulement qui suggère."),
                TextBlock(type="footer", content="EURKAI SAS — contact@eurkai.com — eurkai.com"),
            ],
            design={
                "palette": {"primary": "#0f172a", "accent": "#6366f1"},
            },
        ))
        v = doc.validate()
        assert v["valid"], f"Validation failed: {v['errors']}"
        html = doc.render()
        assert "Proposition commerciale" in html
        assert "Acme Corp" in html
        assert "Réduction des coûts" in html
        assert "success" in html or "success" in str(doc.data)
        return True
