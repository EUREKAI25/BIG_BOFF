"""CLI seed-build — ligne de commande."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="seed-build",
        description="Génère des seeds de pages depuis des maquettes",
    )
    sub = parser.add_subparsers(dest="command")

    # seed-build analyze <image> [--id template_id] [--out seeds/]
    p_analyze = sub.add_parser("analyze", help="Analyser une image unique")
    p_analyze.add_argument("image", help="Chemin de l'image")
    p_analyze.add_argument("--id", dest="template_id", default=None)
    p_analyze.add_argument("--out", default="seeds/", help="Répertoire de sortie")

    # seed-build watch [--mockups mockups/] [--seeds seeds/]
    p_watch = sub.add_parser("watch", help="Traiter toutes les maquettes en attente")
    p_watch.add_argument("--mockups", default="mockups/")
    p_watch.add_argument("--seeds",   default="seeds/")

    # seed-build show <seed.json>
    p_show = sub.add_parser("show", help="Afficher le résumé d'une seed")
    p_show.add_argument("seed", help="Chemin du fichier seed JSON")

    args = parser.parse_args()

    if args.command == "analyze":
        from .analyzer import MockupAnalyzer
        from .watcher import _save_seed
        analyzer = MockupAnalyzer()
        seed = analyzer.analyze(args.image, template_id=args.template_id)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{seed.template_id}.json"
        _save_seed(seed, out_path)
        print(f"✓ Seed générée : {out_path}")
        _print_summary(seed)

    elif args.command == "watch":
        from .watcher import process_pending_mockups
        process_pending_mockups(
            mockups_dir=args.mockups,
            seeds_dir=args.seeds,
            verbose=True,
        )

    elif args.command == "show":
        from .watcher import load_seed
        seed = load_seed(args.seed)
        _print_summary(seed)

    else:
        parser.print_help()
        sys.exit(1)


def _print_summary(seed) -> None:
    print(f"\n{'─'*50}")
    print(f"  Template  : {seed.template_id}")
    print(f"  Type      : {seed.page_type}")
    print(f"  Desc      : {seed.description}")
    print(f"  Sections  : {len(seed.sections)}")
    print(f"{'─'*50}")
    for s in seed.sections:
        fw = "⬛ full-width" if s.full_width else "  container"
        print(f"  {s.order}. [{s.block_type:<20}] {s.key:<20} ({fw})")
        if s.content_role:
            print(f"       → {s.content_role}")
        for f in s.fields:
            req = "* " if f.required else "  "
            print(f"       {req}{f.key:<30} {f.type:<10} {f.label}")
    print(f"{'─'*50}\n")
