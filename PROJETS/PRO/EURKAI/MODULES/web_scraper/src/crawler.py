"""
web_scraper.crawler
────────────────────
Crawl récursif BFS d'un site web.
Reste dans le même domaine, déduplique les URLs, respecte max_pages / max_depth.
"""
from __future__ import annotations

from collections import deque
from typing import Callable
from urllib.parse import urlparse

from .asset_collector import extract_internal_links
from .fetcher import PageFetcher, FetchResult


def _normalize_url(url: str) -> str:
    """Supprime fragment et trailing slash pour la déduplication."""
    url = url.split("#")[0]
    parsed = urlparse(url)
    # Supprimer le trailing slash sauf pour la racine
    path = parsed.path.rstrip("/") or "/"
    return parsed._replace(path=path, fragment="").geturl()


def _same_domain(url1: str, url2: str) -> bool:
    d1 = urlparse(url1).netloc.lstrip("www.")
    d2 = urlparse(url2).netloc.lstrip("www.")
    return d1 == d2


def crawl_site(
    start_url:  str,
    fetcher:    PageFetcher,
    max_pages:  int = 100,
    max_depth:  int = 5,
    on_log:     Callable[[str], None] | None = None,
    on_page:    Callable[[str, int, int], None] | None = None,
) -> list[FetchResult]:
    """
    BFS du site depuis start_url.

    Args:
        start_url : URL de départ
        fetcher   : instance PageFetcher (déjà dans son context manager)
        max_pages : nombre maximum de pages à scraper
        max_depth : profondeur maximale de liens à suivre
        on_log    : callback(message) pour les logs
        on_page   : callback(url, depth, page_num) avant chaque fetch

    Returns:
        Liste de FetchResult dans l'ordre de visite.
    """
    log  = on_log  or (lambda msg: None)
    page_cb = on_page or (lambda url, depth, num: None)

    start_url = _normalize_url(start_url)
    visited:  set[str]             = set()
    queue:    deque[tuple[str, int]] = deque([(start_url, 0)])
    results:  list[FetchResult]    = []

    log(f"Crawl démarré : {start_url} (max {max_pages} pages, profondeur {max_depth})")

    while queue and len(results) < max_pages:
        url, depth = queue.popleft()
        url = _normalize_url(url)

        if url in visited:
            continue
        visited.add(url)

        page_num = len(results) + 1
        page_cb(url, depth, page_num)
        log(f"[{page_num}/{max_pages}] depth={depth} {url}")

        result = fetcher.fetch(url)
        results.append(result)

        if result.error:
            log(f"  ✗ Erreur : {result.error}")
            continue

        log(f"  ✓ HTTP {result.status_code} — {len(result.html)} chars HTML")

        # Suivre les liens internes si on n'a pas atteint la profondeur max
        if depth < max_depth and result.html:
            links = extract_internal_links(result.html, result.final_url)
            added = 0
            for link in links:
                norm = _normalize_url(link)
                if norm not in visited and _same_domain(start_url, norm):
                    queue.append((norm, depth + 1))
                    added += 1
            if added:
                log(f"  → {added} lien(s) ajouté(s) à la file")

    total_ok    = sum(1 for r in results if not r.error)
    total_error = sum(1 for r in results if r.error)
    log(f"Crawl terminé : {len(results)} pages ({total_ok} OK, {total_error} erreurs)")

    return results
