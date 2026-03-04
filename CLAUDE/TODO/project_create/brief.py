#!/usr/bin/env python3
"""
Brief Agent — conversation guidée pour produire un project.json
Usage:
  python3 brief.py "marketplace de recettes cosmétiques maison"
  python3 brief.py                         # démarre sans brief initial
  python3 brief.py --outdir /chemin/custom # répertoire de sortie custom
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"
DEFAULT_OUTDIR = ROOT / "outputs"
DEFAULT_LOGDIR = ROOT / "logs"
REGISTRY_PATH = ROOT / "product_registry.json"

# Points à établir dans l'ordre — injectés dans chaque message user
CHECKLIST = ["REFORMULATION", "UTILISATEURS", "PRODUIT", "FEATURES_MVP", "STACK", "CONTRAINTES", "VALIDATION"]


def load_env():
    from dotenv import load_dotenv
    for p in [ROOT / ".env", Path.home() / ".bigboff" / "secrets.env"]:
        if p.exists():
            load_dotenv(p, override=False)
            return


def load_registry() -> dict:
    """Charge le registre des types de produits connus."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {"types": {}}


def format_registry_context(registry: dict) -> str:
    """Formate le registre pour injection dans le prompt agent_brief."""
    types = registry.get("types", {})
    if not types:
        return (
            "Aucun type enregistré pour l'instant.\n"
            "Si tu identifies un type de produit, ajoute `\"taxonomy\": \"Categorie:SousType\"` "
            "dans chaque produit du JSON (ex: \"Website:LandingPage\", \"WebApp\", \"Service:WebmarketingService\")."
        )
    lines = ["Types de produits connus (utilise-les en priorité) :"]
    for key, val in types.items():
        seen = ", ".join(val.get("seen_in", [])[:2])
        lines.append(f"- `{key}` : {val.get('pattern', '')} — depth {val.get('depth', 2)} (ex: {seen})")
    lines.append(
        "\nSi aucun type ne correspond, crée un nom selon la convention `Categorie:SousType` "
        "et ajoute-le dans `taxonomy`."
    )
    return "\n".join(lines)


def update_registry(registry: dict, spec: dict) -> bool:
    """Enregistre les types inconnus issus de la spec. Retourne True si modifié."""
    changed = False
    project = spec.get("project", "unknown")
    for product in spec.get("products", []):
        taxonomy = product.get("taxonomy")
        if not taxonomy:
            continue
        if taxonomy not in registry["types"]:
            registry["types"][taxonomy] = {
                "depth": 2,
                "seeds": [],
                "pattern": product.get("type", "unknown"),
                "seen_in": [project],
            }
            changed = True
            print(f"  📋 Nouveau type enregistré : {taxonomy}")
        else:
            seen = registry["types"][taxonomy].setdefault("seen_in", [])
            if project not in seen:
                seen.append(project)
                changed = True
    if changed:
        REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    return changed


def load_prompt(registry_context: str) -> str:
    path = PROMPTS / "agent_brief.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text().replace("{registry_context}", registry_context)


def extract_spec(text: str) -> dict | None:
    """Détecte un JSON de projet valide dans le message de l'agent."""
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict) and "project" in data:
                return data
        except json.JSONDecodeError as e:
            print(f"\n⚠️  JSON malformé : {e}")
    return None


def extract_ok_tags(text: str) -> list[str]:
    """Extrait les points marqués [OK: X] par l'agent."""
    return re.findall(r'\[OK:\s*([A-Z_]+)\]', text)


def strip_tags(text: str) -> str:
    """Supprime les lignes de tracking [OK: ...] et [Points restants: ...] de l'affichage."""
    lines = text.splitlines()
    clean = [l for l in lines if not re.match(r'^\s*\[OK:', l)
             and not re.match(r'^\s*\[Points restants:', l)]
    return '\n'.join(clean).strip()


def state_prefix(established: set) -> str:
    """Préfixe injecté dans chaque message user (invisible à l'affichage)."""
    pending = [p for p in CHECKLIST if p not in established]
    if not pending:
        return "[Points restants: aucun — passer à la validation finale]\n"
    return f"[Points restants: {', '.join(pending)}]\n"


def resolve_paths(spec: dict, outdir: Path) -> tuple[Path, Path]:
    """Calcule les chemins de sortie depuis le nom du projet dans la spec."""
    project_name = spec.get("project", "projet")
    dest = outdir / project_name / "project.json"
    log = DEFAULT_LOGDIR / f"{project_name}.history.json"
    return dest, log


def print_separator():
    print("\n" + "─" * 60)


def run_brief(initial_brief: str = "", outdir: Path | None = None):
    load_env()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY manquante")
        sys.exit(1)

    import anthropic
    model = os.getenv("PROJECT_CREATE_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=api_key)
    registry = load_registry()
    system_prompt = load_prompt(format_registry_context(registry))

    out_base = outdir or DEFAULT_OUTDIR
    history: list[dict] = []
    established: set[str] = set()

    print("\n" + "=" * 60)
    print("  PROJECT CREATE — Agent Brief")
    print("  Décrivez votre projet. 'quit' pour abandonner.")
    print("=" * 60)

    # Premier message
    if initial_brief:
        user_msg = initial_brief
        print(f"\nVous : {user_msg}")
    else:
        print()
        user_msg = input("Vous : ").strip()
        if not user_msg or user_msg.lower() in ("quit", "exit", "q"):
            print("(Annulé)")
            return None

    while True:
        # Injecter l'état courant dans le message user (invisible à l'affichage)
        history.append({"role": "user", "content": state_prefix(established) + user_msg})

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=history,
        )
        agent_msg = response.content[0].text
        history.append({"role": "assistant", "content": agent_msg})

        # Mettre à jour l'état établi
        established.update(extract_ok_tags(agent_msg))

        # Afficher sans les tags de tracking
        print_separator()
        print(f"\nAgent : {strip_tags(agent_msg)}\n")

        # Spec détectée ? On sauvegarde et on sort
        spec = extract_spec(agent_msg)
        if spec:
            dest, log_dest = resolve_paths(spec, out_base)
            dest.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_LOGDIR.mkdir(parents=True, exist_ok=True)

            update_registry(registry, spec)
            dest.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
            log_dest.write_text(json.dumps(
                {"brief": initial_brief, "history": history},
                indent=2, ensure_ascii=False
            ))
            print_separator()
            print(f"\n✅ Spec     : {dest}")
            print(f"   Log      : {log_dest}")
            print(f"\nLancez la génération :")
            print(f'  python3 runner.py "votre brief" --config {dest}\n')
            return spec

        # Prochaine réponse utilisateur
        print()
        user_msg = ""
        while not user_msg:
            user_msg = input("Vous : ").strip()
        if user_msg.lower() in ("quit", "exit", "q"):
            print("\n(Conversation abandonnée — spec non sauvegardée)")
            return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Brief Agent — produit un project.json")
    parser.add_argument("brief", nargs="*", help="Brief initial (optionnel)")
    parser.add_argument("--outdir", type=Path, default=None,
                        help=f"Répertoire de sortie (défaut : {DEFAULT_OUTDIR})")
    args = parser.parse_args()

    brief = " ".join(args.brief) if args.brief else ""
    run_brief(initial_brief=brief, outdir=args.outdir)
