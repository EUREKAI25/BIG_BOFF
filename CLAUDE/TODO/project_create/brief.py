#!/usr/bin/env python3
"""
Brief Agent — conversation guidée pour produire un project.json
Usage:
  python3 brief.py "marketplace de recettes cosmétiques maison"
  python3 brief.py                    # démarre sans brief initial
  python3 brief.py --output my.json   # chemin de sortie custom
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"


def load_env():
    from dotenv import load_dotenv
    for p in [ROOT / ".env", Path.home() / ".bigboff" / "secrets.env"]:
        if p.exists():
            load_dotenv(p, override=False)
            return


def load_prompt() -> str:
    path = PROMPTS / "agent_brief.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt introuvable : {path}")
    return path.read_text()


def extract_spec(text: str) -> dict | None:
    """Détecte un JSON de projet valide dans le message de l'agent.
    Pas de marqueur requis — on reconnaît la spec à sa structure."""
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict) and "project" in data:
                return data
        except json.JSONDecodeError as e:
            print(f"\n⚠️  JSON malformé : {e}")
    return None


def print_separator():
    print("\n" + "─" * 60)


def run_brief(initial_brief: str = "", output_path: Path | None = None):
    load_env()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY manquante")
        sys.exit(1)

    import anthropic
    model = os.getenv("PROJECT_CREATE_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = load_prompt()

    history: list[dict] = []

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
        history.append({"role": "user", "content": user_msg})

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=history,
        )
        agent_msg = response.content[0].text
        history.append({"role": "assistant", "content": agent_msg})

        print_separator()
        print(f"\nAgent : {agent_msg}\n")

        # Spec détectée ? On sauvegarde tout et on sort
        spec = extract_spec(agent_msg)
        if spec:
            dest = output_path or (Path.cwd() / "project.json")
            dest.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
            hist_dest = dest.with_name(dest.stem + ".history.json")
            hist_dest.write_text(json.dumps(
                {"brief": initial_brief, "history": history},
                indent=2, ensure_ascii=False
            ))
            print_separator()
            print(f"\n✅ Spec sauvegardée : {dest}")
            print(f"   Historique : {hist_dest}")
            print(f"\nLancez la génération :")
            print(f'  python3 runner.py "votre brief" --config {dest}\n')
            return spec

        # Prochaine réponse utilisateur — boucle jusqu'à une réponse non vide
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
    parser.add_argument("--output", type=Path, default=None, help="Fichier de sortie (défaut : project.json)")
    args = parser.parse_args()

    brief = " ".join(args.brief) if args.brief else ""
    run_brief(initial_brief=brief, output_path=args.output)
