#!/usr/bin/env python3
"""
AUTOSITES — Générateur de site depuis un ou plusieurs manifests JSON.

Usage — page unique :
    python generate.py manifests/home.json
    python generate.py manifests/home.json -o ./output/mon_site --open

Usage — toutes les pages d'un site :
    python generate.py manifests/          # traite tous les .json du dossier
    python generate.py manifests/ -o ./output/mon_site --open

Convention de sortie :
    output/<slug>/          ← chaque manifest → son propre sous-dossier
    output/<slug>/index.html
"""
import json
import sys
import argparse
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent.resolve()
MODULES_DIR = HERE.parent  # EURKAI/MODULES/

sys.path.insert(0, str(MODULES_DIR / "page_builder"))
sys.path.insert(0, str(MODULES_DIR / "theme_generator"))

# ── Imports ───────────────────────────────────────────────────────────────────
try:
    from src.manifest.schema import ManifestPage
    from src.manifest.parser import parse_manifest
    from src.renderer.html   import render_page
except ImportError as e:
    print(f"[ERREUR] Import page_builder échoué : {e}")
    print(f"         Vérifier que {MODULES_DIR / 'page_builder'} est accessible.")
    sys.exit(1)


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_manifests(source: Path) -> list[Path]:
    """
    Retourne la liste des manifests à traiter.
    - source est un fichier .json → [source]
    - source est un dossier      → tous les .json du dossier (non récursif)
    """
    if source.is_file():
        return [source]
    if source.is_dir():
        manifests = sorted(source.glob("*.json"))
        if not manifests:
            print(f"[ATTENTION] Aucun fichier .json trouvé dans : {source}")
        return manifests
    print(f"[ERREUR] Source invalide : {source}")
    sys.exit(1)


def check_fill(raw: dict) -> int:
    return json.dumps(raw).count("FILL:")


def generate_one(manifest_path: Path, output_dir: Path) -> tuple[Path, float]:
    """
    Génère index.html depuis un manifest JSON.
    Retourne (chemin_fichier, taille_ko).
    """
    raw      = json.loads(manifest_path.read_text(encoding="utf-8"))
    fills    = check_fill(raw)
    manifest = ManifestPage(**raw)
    page     = parse_manifest(manifest)
    html     = render_page(page)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")

    return out_file, out_file.stat().st_size / 1024, fills


def generate_all(sources: list[Path], base_output: Path) -> list[Path]:
    """
    Génère toutes les pages. Chaque manifest → base_output/<stem>/index.html.
    Retourne la liste des fichiers générés.
    """
    generated = []
    errors    = []

    for i, manifest_path in enumerate(sources, 1):
        slug       = manifest_path.stem
        output_dir = base_output / slug
        prefix     = f"  [{i}/{len(sources)}] {slug}"

        try:
            out_file, size_kb, fills = generate_one(manifest_path, output_dir)
            warn = f"  ⚠  {fills} FILL: non résolus" if fills else ""
            print(f"{prefix} → {size_kb:.1f} Ko{warn}")
            generated.append(out_file)
        except Exception as e:
            print(f"{prefix} → ERREUR : {e}")
            errors.append((manifest_path, e))

    if errors:
        print(f"\n{len(errors)} erreur(s) sur {len(sources)} page(s).")

    return generated


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AUTOSITES — Génération de site(s) depuis manifest(s) JSON"
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Manifest .json unique OU dossier contenant plusieurs manifests",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Répertoire de sortie (défaut : ./output/)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Ouvrir la première page générée dans le navigateur",
    )
    args = parser.parse_args()

    source     = args.source.resolve()
    base_out   = (args.output or HERE / "output").resolve()
    manifests  = find_manifests(source)

    print(f"Source   : {source}")
    print(f"Pages    : {len(manifests)}")
    print(f"Sortie   : {base_out}")
    print()

    generated = generate_all(manifests, base_out)

    print(f"\n{len(generated)}/{len(manifests)} page(s) générée(s).")

    if args.open and generated:
        import subprocess
        subprocess.run(["open", str(generated[0])])


if __name__ == "__main__":
    main()
