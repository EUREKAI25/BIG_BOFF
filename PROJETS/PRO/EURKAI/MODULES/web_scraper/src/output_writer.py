"""
web_scraper.output_writer
──────────────────────────
Écrit les résultats de scraping dans l'arborescence de sortie.

Structure page unique :
    <output_dir>/
    ├── index.html
    ├── dom.json
    ├── meta.json
    ├── assets_manifest.json
    ├── media/img/
    ├── media/video/
    ├── media/audio/
    ├── scripts/js/
    └── scripts/css/

Structure crawl :
    <output_dir>/
    ├── scrape_manifest.json     ← inventaire global
    ├── pages/
    │   ├── 001_home/
    │   │   ├── index.html
    │   │   ├── dom.json
    │   │   ├── meta.json
    │   │   └── assets_manifest.json
    │   └── 002_about/
    │       └── …
    ├── media/img/               ← assets partagés (dédupliqués)
    ├── media/video/
    ├── media/audio/
    ├── scripts/js/
    └── scripts/css/
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from .models import PageResult, ScrapeResult


def _safe_dir_name(url: str) -> str:
    """Convertit une URL en nom de dossier safe."""
    parsed = urlparse(url)
    path   = (parsed.path.strip("/") or "home").replace("/", "_")
    # Supprimer caractères non-alphanumériques (sauf _ et -)
    path = re.sub(r"[^\w\-]", "_", path)[:60]
    return path or "home"


def _output_root(url: str, base_dir: Path | None) -> Path:
    """Calcule le répertoire racine de sortie."""
    if base_dir is None:
        base_dir = Path.home() / "eurkai_scrapes"
    domain    = urlparse(url).netloc.replace("www.", "").replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_dir / f"{domain}_{timestamp}"


def write_page_result(
    result:     PageResult,
    output_dir: Path,
    index:      int | None = None,
) -> Path:
    """
    Écrit index.html, dom.json, meta.json, assets_manifest.json dans output_dir.
    Retourne le chemin du dossier écrit.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # HTML brut
    (output_dir / "index.html").write_text(result.html, encoding="utf-8", errors="replace")

    # DOM JSON (compact — pas d'indentation pour les gros sites)
    dom_path = output_dir / "dom.json"
    dom_path.write_text(
        json.dumps(result.dom, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # Assets manifest
    (output_dir / "assets_manifest.json").write_text(
        json.dumps(result.assets.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result.output_dir = output_dir
    return output_dir


def write_scrape_result(result: ScrapeResult) -> Path:
    """
    Écrit le résultat complet (page unique ou crawl) dans result.output_dir.
    Retourne le chemin racine.
    """
    root = result.output_dir
    root.mkdir(parents=True, exist_ok=True)

    if result.mode == "page" and result.pages:
        # Page unique → écrire à la racine directement
        write_page_result(result.pages[0], root)

    else:
        # Crawl → dossier pages/NNN_slug/
        pages_dir = root / "pages"
        for i, page in enumerate(result.pages, 1):
            slug     = _safe_dir_name(page.final_url or page.url)
            page_dir = pages_dir / f"{i:03d}_{slug}"
            write_page_result(page, page_dir, index=i)

    # Manifeste global
    manifest = {
        "scraper":    "EURKAI web_scraper v1.0.0",
        "mode":       result.mode,
        "start_url":  result.start_url,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "success":    result.success,
        "pages":      [
            {
                "index":       i + 1,
                "url":         p.url,
                "final_url":   p.final_url,
                "status_code": p.status_code,
                "depth":       p.depth,
                "assets":      p.assets.to_dict() if p.assets else {},
                "output_dir":  str(p.output_dir) if p.output_dir else None,
                "error":       p.error,
            }
            for i, p in enumerate(result.pages)
        ],
        "totals": {
            "pages":         result.pages_count,
            "assets":        result.assets_count,
            "duration_s":    round(result.duration_s, 2),
        },
        "error": result.error,
    }
    (root / "scrape_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return root
