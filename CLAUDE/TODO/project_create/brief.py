#!/usr/bin/env python3
"""
Brief Agent — project_create
Wrapper autour du module EURKAI conversational_brief.

Usage:
  python3 brief.py "marketplace de recettes cosmétiques maison"
  python3 brief.py                         # démarre sans brief initial
  python3 brief.py --outdir /chemin/custom # répertoire de sortie custom
"""

import sys
from pathlib import Path

# Injection du module EURKAI (chemin relatif depuis project_create)
EURKAI_MODULES = Path(__file__).parent.parent.parent / "PROJETS" / "PRO" / "EURKAI" / "MODULES"
sys.path.insert(0, str(EURKAI_MODULES / "conversational_brief"))

from conversational_brief import run_brief

ROOT     = Path(__file__).parent
PROMPTS  = ROOT / "prompts"
OUTDIR   = ROOT / "outputs"
LOGDIR   = ROOT / "logs"
REGISTRY = ROOT / "product_registry.json"

CHECKLIST = [
    "REFORMULATION", "UTILISATEURS", "PRODUIT",
    "FEATURES_MVP", "STACK", "CONTRAINTES", "VALIDATION",
]


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    for p in [ROOT / ".env", Path.home() / ".bigboff" / "secrets.env"]:
        if p.exists():
            load_dotenv(p, override=False)
            break

    parser = argparse.ArgumentParser(description="Brief Agent — produit un project.json")
    parser.add_argument("brief", nargs="*", help="Brief initial (optionnel)")
    parser.add_argument("--outdir", type=Path, default=OUTDIR)
    args = parser.parse_args()

    run_brief(
        system_prompt  = PROMPTS / "agent_brief.md",
        checklist      = CHECKLIST,
        initial_brief  = " ".join(args.brief) if args.brief else "",
        outdir         = args.outdir,
        logdir         = LOGDIR,
        registry_path  = REGISTRY,
    )
