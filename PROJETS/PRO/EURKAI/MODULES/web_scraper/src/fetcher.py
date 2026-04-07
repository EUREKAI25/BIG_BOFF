"""
web_scraper.fetcher
────────────────────
Récupération de pages web avec Playwright (rendu JS complet).
Gère le cycle de vie du browser pour une utilisation en crawl (une instance, N pages).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

try:
    from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PWTimeout
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

import requests as _requests


_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36 EurkaiScraper/1.0"
)


@dataclass
class FetchResult:
    url:         str
    final_url:   str
    html:        str
    status_code: int
    error:       str | None = None


class PageFetcher:
    """
    Gère un browser Playwright partagé pour scraper plusieurs pages.

    Usage :
        with PageFetcher(headless=True, timeout_ms=30_000) as fetcher:
            result = fetcher.fetch("https://example.com")

    Si Playwright n'est pas installé, bascule automatiquement sur requests
    (pas de rendu JS).
    """

    def __init__(
        self,
        headless:   bool = True,
        timeout_ms: int  = 30_000,
        on_log:     Callable[[str], None] | None = None,
    ) -> None:
        self.headless   = headless
        self.timeout_ms = timeout_ms
        self.on_log     = on_log or (lambda msg: None)
        self._pw        = None
        self._browser: Browser | None = None

    # ── Context manager ──────────────────────────────────────────────────────

    def __enter__(self) -> "PageFetcher":
        if _HAS_PLAYWRIGHT:
            self._pw      = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=self.headless)
            self.on_log("Browser Playwright démarré (Chromium headless)")
        else:
            self.on_log("Playwright absent — mode requests (pas de rendu JS)")
        return self

    def __exit__(self, *_) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def fetch(self, url: str) -> FetchResult:
        """Récupère l'HTML final d'une URL (après exécution JS si Playwright dispo)."""
        if self._browser:
            return self._fetch_playwright(url)
        return self._fetch_requests(url)

    def _fetch_playwright(self, url: str) -> FetchResult:
        page: Page | None = None
        try:
            page = self._browser.new_page()
            page.set_extra_http_headers({"User-Agent": _USER_AGENT})
            response = page.goto(
                url,
                timeout    = self.timeout_ms,
                wait_until = "networkidle",
            )
            status    = response.status if response else 0
            html      = page.content()
            final_url = page.url
            return FetchResult(url=url, final_url=final_url, html=html, status_code=status)
        except PWTimeout:
            # Retry with domcontentloaded (less strict)
            try:
                if page:
                    response = page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                    return FetchResult(
                        url=url, final_url=page.url,
                        html=page.content(),
                        status_code=response.status if response else 0,
                    )
            except Exception:
                pass
            return FetchResult(url=url, final_url=url, html="", status_code=0, error="Timeout")
        except Exception as exc:
            return FetchResult(url=url, final_url=url, html="", status_code=0, error=str(exc))
        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass

    def _fetch_requests(self, url: str) -> FetchResult:
        """Fallback sans Playwright — HTML statique uniquement."""
        try:
            r = _requests.get(
                url,
                timeout  = self.timeout_ms / 1000,
                headers  = {"User-Agent": _USER_AGENT},
                allow_redirects = True,
            )
            return FetchResult(
                url         = url,
                final_url   = r.url,
                html        = r.text,
                status_code = r.status_code,
            )
        except Exception as exc:
            return FetchResult(url=url, final_url=url, html="", status_code=0, error=str(exc))


# ── Convenience function (single page, no browser reuse) ─────────────────────

def fetch_page(url: str, timeout_ms: int = 30_000) -> FetchResult:
    """Scrape une seule page (ouvre et ferme le browser à chaque appel)."""
    with PageFetcher(timeout_ms=timeout_ms) as fetcher:
        return fetcher.fetch(url)
