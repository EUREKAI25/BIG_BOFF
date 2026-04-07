"""
web_scraper
────────────
Module EURKAI — scraping complet de pages et de sites web.

API publique :
    scrape_page(url, output_dir, download_assets, timeout_ms) → ScrapeResult
    scrape_site(url, output_dir, max_pages, max_depth, download_assets, timeout_ms, on_progress) → ScrapeResult

Usage minimal :
    from MODULES.web_scraper.src import scrape_page, scrape_site
    from pathlib import Path

    # Page unique
    result = scrape_page("https://example.com", output_dir=Path("~/scrapes"))
    print(result.output_dir, result.assets_count)

    # Site complet
    result = scrape_site(
        "https://example.com",
        max_pages  = 50,
        max_depth  = 3,
        on_progress = lambda msg: print(msg),
    )
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from .models          import ScrapeResult, PageResult, AssetManifest
from .fetcher         import PageFetcher
from .dom_parser      import html_to_dom, extract_meta
from .asset_collector import collect_assets
from .asset_downloader import download_assets as _download_assets
from .crawler         import crawl_site as _crawl
from .output_writer   import write_scrape_result, _output_root

__version__ = "1.0.0"
__all__ = ["scrape_page", "scrape_site", "ScrapeResult"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_page_result(
    fetch_result,
    depth:      int = 0,
    output_dir: Path | None = None,
) -> PageResult:
    """Convertit un FetchResult en PageResult (DOM + assets collectés)."""
    if fetch_result.error or not fetch_result.html:
        return PageResult(
            url         = fetch_result.url,
            final_url   = fetch_result.final_url,
            status_code = fetch_result.status_code,
            html        = "",
            dom         = {},
            assets      = AssetManifest(),
            depth       = depth,
            error       = fetch_result.error or "HTML vide",
        )

    dom    = html_to_dom(fetch_result.html)
    assets = collect_assets(fetch_result.html, fetch_result.final_url)

    return PageResult(
        url         = fetch_result.url,
        final_url   = fetch_result.final_url,
        status_code = fetch_result.status_code,
        html        = fetch_result.html,
        dom         = dom,
        assets      = assets,
        depth       = depth,
        output_dir  = output_dir,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def scrape_page(
    url:              str,
    output_dir:       str | Path | None = None,
    download_assets:  bool = True,
    timeout_ms:       int  = 30_000,
    on_progress:      Callable[[str], None] | None = None,
) -> ScrapeResult:
    """
    Scrape une seule page.

    Args:
        url             : URL à scraper
        output_dir      : répertoire racine (défaut: ~/eurkai_scrapes/<domain>_<ts>/)
        download_assets : télécharger les médias et scripts (défaut: True)
        timeout_ms      : timeout Playwright (défaut: 30s)
        on_progress     : callback(message) pour les logs en temps réel

    Returns:
        ScrapeResult avec pages[0] = la page scrapée
    """
    log   = on_progress or (lambda msg: None)
    root  = _output_root(url, Path(output_dir) if output_dir else None)
    t0    = time.perf_counter()

    result = ScrapeResult(mode="page", start_url=url, output_dir=root)

    log(f"Scraping page : {url}")

    try:
        with PageFetcher(timeout_ms=timeout_ms, on_log=log) as fetcher:
            fetch = fetcher.fetch(url)

        page = _build_page_result(fetch)
        result.pages.append(page)

        if download_assets and page.ok:
            log(f"Téléchargement des assets ({page.assets.total} trouvés)…")
            page.assets = _download_assets(page.assets, root, on_log=log)

        log("Écriture des fichiers…")
        write_scrape_result(result)

    except Exception as exc:
        result.error = str(exc)
        log(f"✗ Erreur : {exc}")

    result.duration_s = time.perf_counter() - t0
    log(f"✓ Terminé en {result.duration_s:.1f}s — {root}")
    return result


def scrape_site(
    url:              str,
    output_dir:       str | Path | None = None,
    max_pages:        int  = 100,
    max_depth:        int  = 5,
    download_assets:  bool = True,
    timeout_ms:       int  = 30_000,
    on_progress:      Callable[[str], None] | None = None,
) -> ScrapeResult:
    """
    Crawl récursif d'un site web entier depuis url.

    Args:
        url             : URL de départ
        output_dir      : répertoire racine de sortie
        max_pages       : nombre max de pages à scraper (défaut: 100)
        max_depth       : profondeur max de liens à suivre (défaut: 5)
        download_assets : télécharger les médias et scripts (défaut: True)
        timeout_ms      : timeout Playwright par page (défaut: 30s)
        on_progress     : callback(message) pour les logs en temps réel

    Returns:
        ScrapeResult avec une PageResult par page visitée
    """
    log  = on_progress or (lambda msg: None)
    root = _output_root(url, Path(output_dir) if output_dir else None)
    t0   = time.perf_counter()

    result = ScrapeResult(mode="site", start_url=url, output_dir=root)

    log(f"Crawl site : {url} (max {max_pages} pages, depth {max_depth})")

    try:
        with PageFetcher(timeout_ms=timeout_ms, on_log=log) as fetcher:
            fetch_results = _crawl(
                start_url = url,
                fetcher   = fetcher,
                max_pages = max_pages,
                max_depth = max_depth,
                on_log    = log,
            )

        log(f"Construction des PageResults ({len(fetch_results)} pages)…")
        for fr in fetch_results:
            page = _build_page_result(fr)
            result.pages.append(page)

        if download_assets:
            # Collecter tous les assets uniques (dédupliqués par URL)
            seen_urls: set[str] = set()
            from .models import AssetManifest as _AM
            global_assets = _AM()

            for page in result.pages:
                if not page.ok:
                    continue
                for field in ("images", "videos", "audio", "scripts", "stylesheets"):
                    for asset in getattr(page.assets, field):
                        if asset["url"] not in seen_urls:
                            seen_urls.add(asset["url"])
                            getattr(global_assets, field).append(asset)

            total = global_assets.total
            log(f"Téléchargement de {total} assets uniques…")

            _download_assets(global_assets, root, on_log=log)

            # Mettre à jour les références dans les pages
            url_to_local: dict[str, str | None] = {}
            for field in ("images", "videos", "audio", "scripts", "stylesheets"):
                for asset in getattr(global_assets, field):
                    url_to_local[asset["url"]] = asset.get("local")

            for page in result.pages:
                for field in ("images", "videos", "audio", "scripts", "stylesheets"):
                    for asset in getattr(page.assets, field):
                        asset["local"] = url_to_local.get(asset["url"])

        log("Écriture des fichiers…")
        write_scrape_result(result)

    except Exception as exc:
        import traceback
        result.error = str(exc)
        log(f"✗ Erreur : {exc}\n{traceback.format_exc()}")

    result.duration_s = time.perf_counter() - t0
    log(f"✓ Crawl terminé en {result.duration_s:.1f}s — {result.pages_count} pages — {root}")
    return result
