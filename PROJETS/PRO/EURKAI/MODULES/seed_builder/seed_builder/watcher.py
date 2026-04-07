"""
Watcher de répertoire — traite les nouvelles maquettes à chaque session.

Usage :
    from seed_builder.watcher import process_pending_mockups
    process_pending_mockups()          # à appeler en début de session

Ou en ligne de commande :
    seed-build watch
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Optional

from .analyzer import MockupAnalyzer
from .schemas import PageSeed

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def process_pending_mockups(
    mockups_dir: str | Path = "mockups",
    seeds_dir: str | Path = "seeds",
    done_dir: Optional[str | Path] = None,
    api_key: Optional[str] = None,
    verbose: bool = True,
) -> list[PageSeed]:
    """
    Traite toutes les images dans `mockups_dir` qui n'ont pas encore
    de seed correspondante dans `seeds_dir`.

    Après traitement, l'image est déplacée dans `done_dir` (mockups/_done/ par défaut).

    Returns:
        Liste des PageSeed générées.
    """
    mockups_path = Path(mockups_dir)
    seeds_path   = Path(seeds_dir)
    done_path    = Path(done_dir) if done_dir else mockups_path / "_done"

    seeds_path.mkdir(parents=True, exist_ok=True)
    done_path.mkdir(parents=True, exist_ok=True)

    # Trouver les images non traitées
    images = [
        f for f in mockups_path.iterdir()
        if f.is_file() and f.suffix.lower() in _IMAGE_EXTENSIONS
    ]

    if not images:
        if verbose:
            print("✓ Aucune maquette à traiter.")
        return []

    analyzer = MockupAnalyzer(api_key=api_key)
    results: list[PageSeed] = []

    for image in sorted(images):
        seed_file = seeds_path / f"{image.stem}.json"

        if verbose:
            print(f"  ⟳ Analyse de {image.name}...")

        try:
            seed = analyzer.analyze(image)

            # Nommage numéroté : {page_type}_{n}.json
            seed_file = _numbered_path(seeds_path, seed.page_type)
            seed.template_id = seed_file.stem  # ex: landing_3

            _save_seed(seed, seed_file)
            shutil.move(str(image), done_path / image.name)
            results.append(seed)

            if verbose:
                print(f"  ✓ {image.name} → {seed_file.name} ({len(seed.sections)} sections)")

        except Exception as e:
            if verbose:
                print(f"  ✗ {image.name} → Erreur : {e}")

    if verbose and results:
        print(f"\n{len(results)} seed(s) générée(s) dans {seeds_path}/")

    return results


def _numbered_path(seeds_dir: Path, page_type: str) -> Path:
    """Retourne le prochain chemin numéroté : landing_1.json, landing_2.json..."""
    n = 1
    while True:
        path = seeds_dir / f"{page_type}_{n}.json"
        if not path.exists():
            return path
        n += 1


def _save_seed(seed: PageSeed, path: Path) -> None:
    """Sauvegarde la seed en JSON formaté."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seed.model_dump(exclude_none=True), f, ensure_ascii=False, indent=2)


def load_seed(path: str | Path) -> PageSeed:
    """Charge une seed depuis un fichier JSON."""
    with open(path, encoding="utf-8") as f:
        return PageSeed(**json.load(f))


def list_seeds(seeds_dir: str | Path = "seeds") -> list[Path]:
    """Retourne la liste des fichiers seed disponibles."""
    return sorted(Path(seeds_dir).glob("*.json"))
