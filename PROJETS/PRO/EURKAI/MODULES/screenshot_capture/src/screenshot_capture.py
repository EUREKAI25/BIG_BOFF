"""
screenshot_capture.py — Module autonome de capture déterministe de screenshots.

Usage programmatique :
    from screenshot_capture import ScreenshotCapture
    cap = ScreenshotCapture(output_root="output/captures")
    result = cap.capture_full_page("http://localhost:8765?brief=brut", site="brut", page="landing")
    result = cap.capture_audit_zone("http://...", audit_name="hero", site="brut", page="landing")

Usage CLI :
    python screenshot_capture.py --url "http://localhost:8765?brief=brut" \\
        --site brut --page landing --zone hero --viewport desktop

Zones audit reconnues via : [data-audit="<zone>"]
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

VIEWPORT_PRESETS: dict[str, dict] = {
    "desktop": {"width": 1440, "height": 900},
    "tablet":  {"width": 834,  "height": 1112},
    "mobile":  {"width": 390,  "height": 844},
}

# Zones audit standard — mappées vers leurs sélecteurs data-audit
AUDIT_ZONES = {
    "hero":          "[data-audit='hero']",
    "nav":           "[data-audit='nav']",
    "primary_cta":   "[data-audit='primary_cta']",
    "final_cta":     "[data-audit='final_cta']",
    "first_section": "[data-audit='first_section']",
    "section-1":     "[data-audit='section-1']",
    "section-2":     "[data-audit='section-2']",
    "section-3":     "[data-audit='section-3']",
}

# Délais de rendu stables (ms)
RENDER_WAIT_MS        = 1500   # après networkidle
FONT_WAIT_TIMEOUT_MS  = 8000
IMAGE_WAIT_TIMEOUT_MS = 10000
ANIMATION_FREEZE_JS   = """
// Fige toutes les animations CSS et transitions pour des captures stables
document.querySelectorAll('*').forEach(el => {
    el.style.animationPlayState = 'paused';
    el.style.transition = 'none';
});
// Remplace requestAnimationFrame pour bloquer les animations JS
window._raf = window.requestAnimationFrame;
window.requestAnimationFrame = (cb) => setTimeout(cb, 100000);
"""

WAIT_FOR_STABLE_JS = """
// Attendre que les images soient chargées
() => {
    const imgs = Array.from(document.images);
    return imgs.every(img => img.complete && img.naturalWidth > 0);
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# RESULT OBJECT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CaptureResult:
    ok: bool
    path: str | None
    site: str
    page: str
    viewport: str
    zone: str                        # "full_page" | "viewport" | "hero" | "nav" | ...
    selector: str | None = None
    error: str | None    = None
    duration_ms: float   = 0.0

    def to_dict(self) -> dict:
        return {
            "ok":          self.ok,
            "path":        self.path,
            "site":        self.site,
            "page":        self.page,
            "viewport":    self.viewport,
            "zone":        self.zone,
            "selector":    self.selector,
            "error":       self.error,
            "duration_ms": round(self.duration_ms, 1),
        }

    def __repr__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"[{status}] {self.zone}@{self.viewport} → {self.path or self.error}"


# ─────────────────────────────────────────────────────────────────────────────
# CAPTURE SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class ScreenshotCapture:
    """
    Service de capture déterministe. Instancier une fois, appeler plusieurs fois.
    Thread-safe via asyncio. Chaque capture ouvre une page dédiée.
    """

    def __init__(
        self,
        output_root: str | Path = "output/captures",
        default_viewport: str   = "desktop",
    ):
        self.output_root     = Path(output_root)
        self.default_viewport = default_viewport

    # ── Public API ────────────────────────────────────────────────────────────

    def capture_full_page(
        self, url: str, site: str, page: str,
        viewport: str | None = None,
    ) -> CaptureResult:
        """Screenshot de la page entière (scrollée)."""
        return asyncio.run(self._run(
            url=url, site=site, page=page,
            viewport=viewport or self.default_viewport,
            zone="full_page", selector=None, full_page=True,
        ))

    def capture_viewport(
        self, url: str, site: str, page: str,
        viewport: str | None = None,
    ) -> CaptureResult:
        """Screenshot de ce qui est visible dans le viewport uniquement."""
        return asyncio.run(self._run(
            url=url, site=site, page=page,
            viewport=viewport or self.default_viewport,
            zone="viewport", selector=None, full_page=False,
        ))

    def capture_selector(
        self, url: str, selector: str, site: str, page: str,
        viewport: str | None = None,
        zone: str | None     = None,
    ) -> CaptureResult:
        """Screenshot d'un élément par sélecteur CSS arbitraire."""
        zone_name = zone or _selector_to_zone_name(selector)
        return asyncio.run(self._run(
            url=url, site=site, page=page,
            viewport=viewport or self.default_viewport,
            zone=zone_name, selector=selector, full_page=False,
        ))

    def capture_audit_zone(
        self, url: str, audit_name: str, site: str, page: str,
        viewport: str | None = None,
    ) -> CaptureResult:
        """
        Screenshot d'une zone balisée [data-audit="<audit_name>"].
        Lève une erreur structurée si la zone n'est pas trouvée dans le DOM.
        """
        selector = AUDIT_ZONES.get(audit_name, f"[data-audit='{audit_name}']")
        return asyncio.run(self._run(
            url=url, site=site, page=page,
            viewport=viewport or self.default_viewport,
            zone=audit_name, selector=selector, full_page=False,
        ))

    def capture_all_zones(
        self, url: str, site: str, page: str,
        viewport: str | None = None,
        zones: list[str] | None = None,
    ) -> list[CaptureResult]:
        """
        Capture full_page + toutes les zones audit présentes dans le DOM.
        Si zones=None, tente toutes les zones AUDIT_ZONES connues.
        """
        return asyncio.run(self._run_all_zones(
            url=url, site=site, page=page,
            viewport=viewport or self.default_viewport,
            zones=zones or (["full_page"] + list(AUDIT_ZONES.keys())),
        ))

    # ── Async core ────────────────────────────────────────────────────────────

    async def _run(
        self, url: str, site: str, page: str,
        viewport: str, zone: str,
        selector: str | None, full_page: bool,
    ) -> CaptureResult:
        t0 = time.monotonic()
        vp = _resolve_viewport(viewport)
        out_path = self._output_path(site, page, viewport, zone)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx     = await browser.new_context(viewport=vp)
            pg      = await ctx.new_page()
            try:
                await _navigate_and_stabilize(pg, url)
                result = await _do_capture(
                    pg, out_path, zone, selector, full_page
                )
                duration = (time.monotonic() - t0) * 1000
                if result["ok"]:
                    return CaptureResult(
                        ok=True, path=str(out_path),
                        site=site, page=page, viewport=viewport,
                        zone=zone, selector=selector, duration_ms=duration,
                    )
                else:
                    return CaptureResult(
                        ok=False, path=None,
                        site=site, page=page, viewport=viewport,
                        zone=zone, selector=selector,
                        error=result["error"], duration_ms=duration,
                    )
            except Exception as exc:
                duration = (time.monotonic() - t0) * 1000
                return CaptureResult(
                    ok=False, path=None,
                    site=site, page=page, viewport=viewport,
                    zone=zone, selector=selector,
                    error=f"{type(exc).__name__}: {exc}", duration_ms=duration,
                )
            finally:
                await browser.close()

    async def _run_all_zones(
        self, url: str, site: str, page: str,
        viewport: str, zones: list[str],
    ) -> list[CaptureResult]:
        """Ouvre la page une seule fois, capture toutes les zones en séquence."""
        t0 = time.monotonic()
        vp = _resolve_viewport(viewport)
        results: list[CaptureResult] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx     = await browser.new_context(viewport=vp)
            pg      = await ctx.new_page()
            try:
                await _navigate_and_stabilize(pg, url)
                for zone in zones:
                    zt0 = time.monotonic()
                    if zone == "full_page":
                        out_path = self._output_path(site, page, viewport, "full_page")
                        r = await _do_capture(pg, out_path, "full_page", None, True)
                        sel = None
                    elif zone == "viewport":
                        out_path = self._output_path(site, page, viewport, "viewport")
                        r = await _do_capture(pg, out_path, "viewport", None, False)
                        sel = None
                    else:
                        sel = AUDIT_ZONES.get(zone, f"[data-audit='{zone}']")
                        out_path = self._output_path(site, page, viewport, zone)
                        r = await _do_capture(pg, out_path, zone, sel, False)
                    duration = (time.monotonic() - zt0) * 1000
                    if r["ok"]:
                        results.append(CaptureResult(
                            ok=True, path=str(out_path),
                            site=site, page=page, viewport=viewport,
                            zone=zone, selector=sel, duration_ms=duration,
                        ))
                    else:
                        results.append(CaptureResult(
                            ok=False, path=None,
                            site=site, page=page, viewport=viewport,
                            zone=zone, selector=sel,
                            error=r["error"], duration_ms=duration,
                        ))
            except Exception as exc:
                results.append(CaptureResult(
                    ok=False, path=None,
                    site=site, page=page, viewport=viewport,
                    zone="*", error=f"Navigation failed: {exc}", duration_ms=0,
                ))
            finally:
                await browser.close()

        return results

    # ── Path builder ──────────────────────────────────────────────────────────

    def _output_path(self, site: str, page: str, viewport: str, zone: str) -> Path:
        """output/captures/<site>/<page>/<viewport>/<zone>.png"""
        path = self.output_root / site / page / viewport / f"{zone}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_viewport(name: str) -> dict:
    if name not in VIEWPORT_PRESETS:
        raise ValueError(f"Viewport inconnu : '{name}'. Valides : {list(VIEWPORT_PRESETS)}")
    return VIEWPORT_PRESETS[name]


def _selector_to_zone_name(selector: str) -> str:
    """Crée un nom de zone depuis un sélecteur CSS pour le nom de fichier."""
    return selector.replace("[", "").replace("]", "").replace("'", "") \
                   .replace("=", "_").replace(" ", "_").replace("#", "") \
                   .replace(".", "")[:40]


async def _navigate_and_stabilize(pg: Page, url: str) -> None:
    """
    Navigation + attente de stabilisation complète :
    1. Charge la page
    2. Attend networkidle
    3. Attend que les fonts soient prêtes (document.fonts.ready)
    4. Attend que les images soient chargées
    5. Fige les animations pour des captures stables
    6. Pause supplémentaire pour le layout final
    """
    await pg.goto(url, wait_until="networkidle", timeout=30_000)

    # Fonts prêtes
    await pg.evaluate("() => document.fonts.ready")

    # Images chargées
    try:
        await pg.wait_for_function(WAIT_FOR_STABLE_JS, timeout=IMAGE_WAIT_TIMEOUT_MS)
    except Exception:
        pass  # Des images Picsum peuvent échouer en réseau lent, on continue

    # Figer animations
    await pg.evaluate(ANIMATION_FREEZE_JS)

    # Pause layout
    await pg.wait_for_timeout(RENDER_WAIT_MS)


async def _do_capture(
    pg: Page, out_path: Path,
    zone: str, selector: str | None, full_page: bool,
) -> dict:
    """
    Effectue la capture réelle. Retourne {"ok": bool, "error": str | None}.
    Ne lève pas d'exception — erreurs structurées uniquement.
    """
    try:
        if selector is not None:
            # Element screenshot
            element = await pg.query_selector(selector)
            if element is None:
                return {
                    "ok": False,
                    "error": (
                        f"Zone '{zone}' introuvable. "
                        f"Sélecteur '{selector}' absent du DOM. "
                        f"Vérifiez que data-audit='{zone}' est présent dans le HTML."
                    ),
                }
            # Scroller l'élément dans le viewport pour un rendu correct
            await element.scroll_into_view_if_needed()
            await pg.wait_for_timeout(200)
            await element.screenshot(path=str(out_path))
        else:
            # Full-page ou viewport
            await pg.screenshot(path=str(out_path), full_page=full_page)

        return {"ok": True, "error": None}

    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="screenshot_capture — Capture déterministe de zones de page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python screenshot_capture.py --url "http://localhost:8765?brief=brut" \\
      --site brut --page landing --zone full_page

  python screenshot_capture.py --url "http://localhost:8765?brief=brut" \\
      --site brut --page landing --zone hero

  python screenshot_capture.py --url "http://localhost:8765?brief=brut" \\
      --site brut --page landing --zone all --viewport mobile

Zones disponibles : full_page, viewport, """ + ", ".join(AUDIT_ZONES.keys()),
    )
    parser.add_argument("--url",      required=True,  help="URL à capturer")
    parser.add_argument("--site",     required=True,  help="Identifiant du site (ex: brut)")
    parser.add_argument("--page",     default="landing", help="Type de page (ex: landing, about)")
    parser.add_argument("--zone",     default="full_page",
                        help="Zone à capturer : full_page | viewport | hero | nav | all | ...")
    parser.add_argument("--viewport", default="desktop",
                        choices=list(VIEWPORT_PRESETS), help="Preset viewport")
    parser.add_argument("--output",   default="output/captures", help="Dossier de sortie racine")
    parser.add_argument("--json",     action="store_true", help="Output JSON structuré")
    args = parser.parse_args()

    cap = ScreenshotCapture(output_root=args.output, default_viewport=args.viewport)

    if args.zone == "all":
        results = cap.capture_all_zones(
            url=args.url, site=args.site, page=args.page, viewport=args.viewport,
        )
        if args.json:
            print(json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
        else:
            for r in results:
                print(r)
    elif args.zone == "full_page":
        r = cap.capture_full_page(args.url, site=args.site, page=args.page, viewport=args.viewport)
        print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False) if args.json else r)
    elif args.zone == "viewport":
        r = cap.capture_viewport(args.url, site=args.site, page=args.page, viewport=args.viewport)
        print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False) if args.json else r)
    else:
        r = cap.capture_audit_zone(
            args.url, audit_name=args.zone,
            site=args.site, page=args.page, viewport=args.viewport,
        )
        print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False) if args.json else r)


if __name__ == "__main__":
    _cli()
