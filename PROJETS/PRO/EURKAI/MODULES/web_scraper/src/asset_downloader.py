"""
web_scraper.asset_downloader
─────────────────────────────
Télécharge les assets collectés vers l'arborescence de sortie.
Structure :
    <output_dir>/
    ├── media/img/
    ├── media/video/
    ├── media/audio/
    └── scripts/js/
    └── scripts/css/
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests

from .models import AssetManifest


_DEST_MAP = {
    "images":      ("media", "img"),
    "videos":      ("media", "video"),
    "audio":       ("media", "audio"),
    "scripts":     ("scripts", "js"),
    "stylesheets": ("scripts", "css"),
}

_TIMEOUT = 20  # secondes


def _url_to_filename(url: str) -> str:
    """Dérive un nom de fichier unique depuis une URL."""
    parsed   = urlparse(url)
    path_part = Path(parsed.path)
    name      = path_part.name

    # Supprimer les query strings du nom
    if "?" in name:
        name = name.split("?")[0]

    # Ajouter l'extension si manquante
    if name and "." not in name[-6:]:
        # Essayer de deviner via le Content-Type plus tard
        pass

    # Si pas de nom ou trop court, utiliser un hash court
    if not name or len(name) < 2:
        name = hashlib.md5(url.encode()).hexdigest()[:12]

    # Éviter les noms trop longs
    if len(name) > 80:
        ext  = Path(name).suffix
        name = hashlib.md5(url.encode()).hexdigest()[:16] + ext

    return name


def _safe_dest(dest_dir: Path, url: str, content_type: str | None = None) -> Path:
    """Retourne un chemin de destination garanti unique."""
    name = _url_to_filename(url)

    # Ajouter extension depuis Content-Type si manquante
    if content_type and "." not in name[-6:]:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ""
        if ext and not name.endswith(ext):
            name += ext

    dest = dest_dir / name

    # Éviter les collisions (même nom, URL différente)
    if dest.exists():
        stem = Path(name).stem
        suf  = Path(name).suffix
        h    = hashlib.md5(url.encode()).hexdigest()[:6]
        dest = dest_dir / f"{stem}_{h}{suf}"

    return dest


def _download_one(url: str, dest_dir: Path, session: requests.Session) -> dict:
    """Télécharge un fichier. Retourne un dict de résultat."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Embeds (YouTube etc.) → noter sans télécharger
    result_base = {"url": url}

    try:
        r = session.get(
            url,
            timeout        = _TIMEOUT,
            stream         = True,
            allow_redirects= True,
            headers        = {"User-Agent": "EurkaiScraper/1.0"},
        )
        r.raise_for_status()

        content_type = r.headers.get("Content-Type", "")
        dest         = _safe_dest(dest_dir, url, content_type)

        # Écrire par chunks (gros fichiers)
        size = 0
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(chunk_size=65_536):
                if chunk:
                    fh.write(chunk)
                    size += len(chunk)

        return {**result_base, "local": str(dest), "size_bytes": size, "status": r.status_code}

    except requests.exceptions.HTTPError as exc:
        return {**result_base, "error": f"HTTP {exc.response.status_code}"}
    except requests.exceptions.Timeout:
        return {**result_base, "error": "Timeout"}
    except Exception as exc:
        return {**result_base, "error": str(exc)}


def download_assets(
    manifest:   AssetManifest,
    output_dir: Path,
    on_log:     Callable[[str], None] | None = None,
) -> AssetManifest:
    """
    Télécharge tous les assets du manifest dans <output_dir>/.
    Retourne le manifest mis à jour avec les chemins locaux.
    Skips les embeds (YouTube, etc.).
    """
    log = on_log or (lambda msg: None)

    with requests.Session() as session:
        for field_name, sub_path in _DEST_MAP.items():
            assets = getattr(manifest, field_name)
            if not assets:
                continue

            dest_dir = output_dir / sub_path[0] / sub_path[1]
            total    = len(assets)

            for i, asset in enumerate(assets, 1):
                url = asset.get("url", "")
                if not url:
                    continue
                if asset.get("embed"):
                    log(f"  [embed] {url}")
                    asset["local"] = None
                    continue

                log(f"  [{field_name}] {i}/{total} {url[:80]}")
                result = _download_one(url, dest_dir, session)
                asset.update(result)

    return manifest
