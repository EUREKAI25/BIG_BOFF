"""
web_scraper.asset_collector
────────────────────────────
Collecte toutes les URLs d'assets référencées dans un HTML
(images, vidéos, audio, JS, CSS).
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from .models import AssetManifest


def collect_assets(html: str, base_url: str) -> AssetManifest:
    """
    Analyse le HTML et retourne un AssetManifest avec toutes les URLs trouvées.
    Gère : img src/srcset, video, audio, <script src>, <link stylesheet>,
           CSS url(), preload, data-src (lazy loading).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return AssetManifest()

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    manifest = AssetManifest()
    seen: set[str] = set()  # dédupliquer

    def _abs(url: str) -> str | None:
        if not url or url.startswith("data:"):
            return None
        abs_url = urljoin(base_url, url.strip())
        parsed = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            return None
        return abs_url

    def _add(collection: list, url: str, **extra) -> None:
        abs_url = _abs(url)
        if abs_url and abs_url not in seen:
            seen.add(abs_url)
            collection.append({"url": abs_url, **extra})

    def _parse_srcset(srcset: str) -> list[str]:
        """Parse srcset="url1 1x, url2 2x" → [url1, url2]"""
        urls = []
        for part in srcset.split(","):
            tokens = part.strip().split()
            if tokens:
                urls.append(tokens[0])
        return urls

    # ── Images ────────────────────────────────────────────────────────────────
    for tag in soup.find_all(["img", "source"]):
        # src normal
        if tag.get("src"):
            _add(manifest.images, tag["src"], tag=tag.name, attr="src")
        # srcset
        if tag.get("srcset"):
            for u in _parse_srcset(tag["srcset"]):
                _add(manifest.images, u, tag=tag.name, attr="srcset")
        # lazy loading (data-src, data-lazy-src, etc.)
        for attr in tag.attrs:
            if "src" in attr.lower() and attr != "src" and attr != "srcset":
                _add(manifest.images, tag[attr], tag=tag.name, attr=attr)

    # picture > source[srcset]
    for tag in soup.find_all("source"):
        if tag.parent and tag.parent.name == "picture":
            if tag.get("srcset"):
                for u in _parse_srcset(tag["srcset"]):
                    _add(manifest.images, u, tag="picture>source", attr="srcset")

    # CSS background-image dans les style attributes inline
    for tag in soup.find_all(style=True):
        for url in re.findall(r'url\(["\']?([^"\'()]+)["\']?\)', tag["style"]):
            _add(manifest.images, url, tag=tag.name, attr="style[background]")

    # ── Vidéos ────────────────────────────────────────────────────────────────
    for tag in soup.find_all("video"):
        if tag.get("src"):
            _add(manifest.videos, tag["src"], tag="video")
        if tag.get("poster"):
            _add(manifest.images, tag["poster"], tag="video[poster]", attr="poster")
    for tag in soup.find_all("source"):
        if tag.parent and tag.parent.name in ("video",):
            if tag.get("src"):
                _add(manifest.videos, tag["src"], tag="source[video]")

    # iframes YouTube/Vimeo → noter l'URL sans télécharger
    for tag in soup.find_all("iframe", src=True):
        src = tag["src"]
        if any(domain in src for domain in ("youtube.com", "youtu.be", "vimeo.com", "dailymotion.com")):
            abs_url = _abs(src)
            if abs_url and abs_url not in seen:
                seen.add(abs_url)
                manifest.videos.append({"url": abs_url, "tag": "iframe", "embed": True})

    # ── Audio ─────────────────────────────────────────────────────────────────
    for tag in soup.find_all("audio"):
        if tag.get("src"):
            _add(manifest.audio, tag["src"], tag="audio")
    for tag in soup.find_all("source"):
        if tag.parent and tag.parent.name == "audio":
            if tag.get("src"):
                _add(manifest.audio, tag["src"], tag="source[audio]")

    # ── Scripts JS ────────────────────────────────────────────────────────────
    for tag in soup.find_all("script", src=True):
        _add(manifest.scripts, tag["src"], tag="script", type=tag.get("type", ""))
    # preload scripts
    for tag in soup.find_all("link", rel=lambda r: r and "preload" in r, as_="script"):
        if tag.get("href"):
            _add(manifest.scripts, tag["href"], tag="link[preload]", attr="href")

    # ── CSS ───────────────────────────────────────────────────────────────────
    for tag in soup.find_all("link"):
        rel = tag.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]
        if "stylesheet" in rel and tag.get("href"):
            _add(manifest.stylesheets, tag["href"], tag="link[stylesheet]", media=tag.get("media", "all"))
    # preload stylesheets
    for tag in soup.find_all("link", rel=lambda r: r and "preload" in r, as_="style"):
        if tag.get("href"):
            _add(manifest.stylesheets, tag["href"], tag="link[preload]", attr="href")

    return manifest


def extract_internal_links(html: str, base_url: str) -> list[str]:
    """
    Extrait tous les liens internes (<a href>) du même domaine.
    Retourne une liste d'URLs absolues dédupliquées, sans fragments.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    base_domain = urlparse(base_url).netloc
    seen: set[str] = set()
    links: list[str] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        abs_url = urljoin(base_url, href).split("#")[0].rstrip("/") or "/"
        parsed  = urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc != base_domain:
            continue
        if abs_url not in seen:
            seen.add(abs_url)
            links.append(abs_url)

    return links
