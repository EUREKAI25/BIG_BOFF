"""
EmailSignature — Business email signature block object.

The object owns its render logic. Renders as self-contained HTML table
compatible with email clients (inline styles, no flexbox/grid).

Usage:
    from document_objects.email_signature import EmailSignature, EmailSignatureInput, SocialLink

    sig = EmailSignature(EmailSignatureInput(
        name="Nathalie Dupont",
        role="Creative Director",
        company="EURKAI",
        email="nathalie@eurkai.com",
        website="https://eurkai.com",
        cta_label="Voir mon portfolio",
        cta_url="https://eurkai.com/portfolio",
    ))
    html = sig.render()
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel

NAME     = "document.email_signature"
CATEGORY = "document"
VERSION  = "1.0.0"


# ── Schemas ──────────────────────────────────────────────────────────────────

class SocialLink(BaseModel):
    platform: Literal["linkedin", "twitter", "instagram", "github", "youtube", "tiktok", "other"]
    url: str
    label: Optional[str] = None


class EmailSignatureInput(BaseModel):
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None
    social_links: List[SocialLink] = []
    tagline: Optional[str] = None
    design: Optional[Dict[str, Any]] = None


# ── Social icons (inline SVG data URIs — email-safe fallback to text) ────────

_SOCIAL_LABELS = {
    "linkedin": "LinkedIn",
    "twitter": "Twitter / X",
    "instagram": "Instagram",
    "github": "GitHub",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "other": "Lien",
}


# ── Object ───────────────────────────────────────────────────────────────────

class EmailSignature:
    NAME     = NAME
    CATEGORY = CATEGORY
    VERSION  = VERSION

    def __init__(self, data: EmailSignatureInput) -> None:
        self.data = data

    # ── Validate ──────────────────────────────────────────────────────────────

    def validate(self) -> dict:
        errors = []
        if not self.data.name:
            errors.append("name is required")
        if self.data.cta_label and not self.data.cta_url:
            errors.append("cta_url is required when cta_label is set")
        return {"valid": len(errors) == 0, "errors": errors}

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self) -> str:
        """
        Returns a self-contained HTML email signature.
        Uses table layout + inline styles for maximum email client compatibility.
        Left column: identity. Right column: contact + CTA.
        """
        d = self.data
        pal  = (d.design or {}).get("palette", {})
        typo = (d.design or {}).get("typography", {})

        primary    = pal.get("primary", "#0f172a")
        accent     = pal.get("accent",  "#6366f1")
        text_color = pal.get("text",    "#1e293b")
        muted      = pal.get("muted",   "#64748b")
        surface    = pal.get("surface", "#f8fafc")
        font_body  = typo.get("body_font", "Inter, Arial, sans-serif")

        # ── Avatar / logo ─────────────────────────────────────────────────────
        if d.logo_url:
            avatar_html = (
                f'<img src="{d.logo_url}" width="52" height="52" '
                f'style="border-radius:8px; display:block; object-fit:contain; border:2px solid {accent}30;" '
                f'alt="{d.company or d.name}">'
            )
        else:
            initials = "".join(p[0].upper() for p in d.name.split()[:2])
            avatar_html = (
                f'<div style="width:52px; height:52px; border-radius:10px; background:{primary}; '
                f'color:#fff; font-family:{font_body}; font-size:18px; font-weight:800; '
                f'text-align:center; line-height:52px; letter-spacing:-.02em;">{initials}</div>'
            )

        # ── Identity column (left) ────────────────────────────────────────────
        role_line = ""
        if d.role or d.company:
            parts = []
            if d.role:
                parts.append(f'<span style="color:{accent}; font-weight:600;">{d.role}</span>')
            if d.company:
                parts.append(f'<span style="color:{muted};">{d.company}</span>')
            role_line = (
                f'<p style="margin:3px 0 0; font-size:12px; font-family:{font_body};">'
                f'{"&ensp;·&ensp;".join(parts)}</p>'
            )

        tagline_line = ""
        if d.tagline:
            tagline_line = (
                f'<p style="margin:5px 0 0; font-size:11px; color:{muted}; '
                f'font-style:italic; font-family:{font_body}; letter-spacing:.01em;">{d.tagline}</p>'
            )

        identity_td = (
            f'<td style="vertical-align:top; padding-right:20px; border-right:1px solid {accent}30; '
            f'padding-bottom:4px;">'
            f'<table cellpadding="0" cellspacing="0" border="0">'
            f'<tr>'
            f'<td style="padding-right:12px; vertical-align:middle;">{avatar_html}</td>'
            f'<td style="vertical-align:middle;">'
            f'<p style="margin:0; font-size:16px; font-weight:800; color:{primary}; '
            f'font-family:{font_body}; letter-spacing:-.02em; white-space:nowrap;">{d.name}</p>'
            f'{role_line}'
            f'{tagline_line}'
            f'</td>'
            f'</tr>'
            f'</table>'
            f'</td>'
        )

        # ── Contact column (right) ────────────────────────────────────────────
        contact_rows = []

        if d.email:
            contact_rows.append(
                f'<tr><td style="padding:2px 0; font-size:12px; font-family:{font_body}; '
                f'white-space:nowrap; color:{muted};">'
                f'<span style="display:inline-block; width:16px; text-align:center; '
                f'color:{accent}; margin-right:6px; font-size:11px;">✉</span>'
                f'<a href="mailto:{d.email}" style="color:{text_color}; text-decoration:none; '
                f'font-family:{font_body};">{d.email}</a></td></tr>'
            )
        if d.phone:
            contact_rows.append(
                f'<tr><td style="padding:2px 0; font-size:12px; font-family:{font_body}; '
                f'white-space:nowrap; color:{muted};">'
                f'<span style="display:inline-block; width:16px; text-align:center; '
                f'color:{accent}; margin-right:6px; font-size:11px;">☎</span>'
                f'<a href="tel:{d.phone}" style="color:{text_color}; text-decoration:none; '
                f'font-family:{font_body};">{d.phone}</a></td></tr>'
            )
        if d.website:
            display_url = d.website.replace("https://", "").replace("http://", "").rstrip("/")
            contact_rows.append(
                f'<tr><td style="padding:2px 0; font-size:12px; font-family:{font_body}; '
                f'white-space:nowrap; color:{muted};">'
                f'<span style="display:inline-block; width:16px; text-align:center; '
                f'color:{accent}; margin-right:6px; font-size:11px;">🌐</span>'
                f'<a href="{d.website}" style="color:{muted}; text-decoration:none; '
                f'font-family:{font_body};">{display_url}</a></td></tr>'
            )

        contact_table = (
            f'<table cellpadding="0" cellspacing="0" border="0">'
            f'<tbody>{"".join(contact_rows)}</tbody>'
            f'</table>'
            if contact_rows else ""
        )

        # Social links as compact pills
        social_html = ""
        if d.social_links:
            pills = "".join(
                f'<a href="{s.url}" style="display:inline-block; margin:0 4px 4px 0; '
                f'padding:2px 8px; background:{accent}12; color:{accent}; font-size:10px; '
                f'font-weight:600; text-decoration:none; border-radius:99px; '
                f'font-family:{font_body}; letter-spacing:.02em; border:1px solid {accent}30;">'
                f'{s.label or _SOCIAL_LABELS.get(s.platform, s.platform)}</a>'
                for s in d.social_links
            )
            social_html = f'<p style="margin:8px 0 0;">{pills}</p>'

        # CTA pill button
        cta_html = ""
        if d.cta_label and d.cta_url:
            cta_html = (
                f'<p style="margin:10px 0 0;">'
                f'<a href="{d.cta_url}" style="display:inline-block; padding:7px 16px; '
                f'background:{accent}; color:#fff; font-family:{font_body}; font-size:11px; '
                f'font-weight:700; text-decoration:none; border-radius:99px; '
                f'letter-spacing:.04em;">{d.cta_label}&nbsp;→</a></p>'
            )

        contact_td = (
            f'<td style="vertical-align:top; padding-left:20px;">'
            f'{contact_table}'
            f'{social_html}'
            f'{cta_html}'
            f'</td>'
        )

        # ── Top accent bar (4px gradient) ─────────────────────────────────────
        bar = (
            f'<tr><td colspan="2" style="padding-bottom:14px;">'
            f'<div style="height:3px; background:linear-gradient(90deg, {primary} 0%, {accent} 100%); '
            f'border-radius:99px;"></div>'
            f'</td></tr>'
        )

        return (
            f'<table cellpadding="0" cellspacing="0" border="0" '
            f'style="font-family:{font_body}; color:{text_color}; max-width:560px;">'
            f'<tbody>'
            f'{bar}'
            f'<tr>{identity_td}{contact_td}</tr>'
            f'</tbody>'
            f'</table>'
        )

    def render_full(self) -> str:
        """Renders as full HTML document (for preview/export)."""
        d = self.data
        pal = (d.design or {}).get("palette", {})
        bg  = pal.get("background", "#f1f5f9")
        inner = self.render()
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Signature — {d.name}</title>
  <style>
    body {{ padding: 48px; background: {bg}; font-family: Inter, system-ui, sans-serif; }}
    .preview-label {{
      font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em;
      color: #94a3b8; margin-bottom: 20px;
    }}
    .preview-wrap {{
      display: inline-block; background: #fff; padding: 28px 32px;
      border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.08);
    }}
  </style>
</head>
<body>
  <p class="preview-label">Aperçu signature email</p>
  <div class="preview-wrap">{inner}</div>
</body>
</html>"""

    # ── Test ──────────────────────────────────────────────────────────────────

    @classmethod
    def test(cls) -> bool:
        sig = cls(EmailSignatureInput(
            name="Nathalie Dupont",
            role="Creative Director",
            company="EURKAI",
            email="nathalie@eurkai.com",
            phone="+33 6 12 34 56 78",
            website="https://eurkai.com",
            cta_label="Découvrir EURKAI",
            cta_url="https://eurkai.com",
            tagline="Design × IA × Scalabilité",
            social_links=[
                SocialLink(platform="linkedin", url="https://linkedin.com/in/nathalie"),
                SocialLink(platform="instagram", url="https://instagram.com/eurkai"),
            ],
            design={
                "palette": {"primary": "#0f172a", "accent": "#6366f1", "muted": "#64748b"},
                "typography": {"body_font": "Inter, Arial, sans-serif"},
            },
        ))
        v = sig.validate()
        assert v["valid"], f"Validation failed: {v['errors']}"
        html = sig.render()
        assert "Nathalie Dupont" in html
        assert "nathalie@eurkai.com" in html
        assert "EURKAI" in html
        assert "Découvrir EURKAI" in html
        assert "LinkedIn" in html
        return True
