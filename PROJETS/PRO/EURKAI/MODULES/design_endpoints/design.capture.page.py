"""
design.capture.page
Endpoint : capture les zones audit d'une page via Playwright.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parents[2]
for _p in [str(_ROOT), str(_ROOT / "MODULES")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from screenshot_capture.src.screenshot_capture import ScreenshotCapture

NAME     = "design.capture.page"
CATEGORY = "design"
OBJECT   = "capture"
ACTION   = "page"
VERSION  = "1.0.0"

INPUTS = {
    "url":         {"type": "str",       "required": True,  "description": "URL de la page (locale ou distante)"},
    "site":        {"type": "str",       "required": True,  "description": "Identifiant site (dossier output)"},
    "page":        {"type": "str",       "required": True,  "description": "Identifiant page (dossier output)"},
    "output_root": {"type": "str",       "required": False, "description": "Répertoire output (default: output/captures)"},
    "viewport":    {"type": "str",       "required": False, "description": "desktop | tablet | mobile (default: desktop)"},
    "zones":       {"type": "list|None", "required": False, "description": "Zones audit à capturer (None = toutes)"},
}

OUTPUTS = {
    "captures":   {"type": "list[dict]", "description": "Liste des captures: ok, path, site, page, viewport, zone, error, duration_ms"},
    "ok_count":   {"type": "int",        "description": "Nombre de captures réussies"},
    "fail_count": {"type": "int",        "description": "Nombre de captures échouées"},
}


def run(
    url: str,
    site: str,
    page: str,
    output_root: str = "output/captures",
    viewport: str = "desktop",
    zones: list[str] | None = None,
) -> dict:
    """
    Inputs  → voir INPUTS
    Outputs → voir OUTPUTS

    Nécessite Playwright installé (playwright install chromium).
    """
    capture = ScreenshotCapture(output_root=output_root, default_viewport=viewport)
    results = capture.capture_all_zones(
        url=url, site=site, page=page, viewport=viewport, zones=zones,
    )
    captures = [r.to_dict() for r in results]
    return {
        "captures":   captures,
        "ok_count":   sum(1 for c in captures if c.get("ok")),
        "fail_count": sum(1 for c in captures if not c.get("ok")),
    }
