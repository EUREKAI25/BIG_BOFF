"""
conversational_brief.agent
───────────────────────────
Logique principale de la conversation guidée.

Paramètres injectables :
  system_prompt  — prompt système (string ou Path vers .md)
  checklist      — liste ordonnée des points à établir
  registry_path  — fichier JSON du registre produits (optionnel)
  outdir         — répertoire de sortie pour le JSON final
  logdir         — répertoire des logs de conversation
  model          — modèle LLM (défaut : variable d'env PROJECT_CREATE_MODEL)
  api_key        — clé Anthropic (défaut : variable d'env ANTHROPIC_API_KEY)
"""

from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Optional


# ─── Registry helpers ─────────────────────────────────────────────────────────

def load_registry(registry_path: Optional[Path]) -> dict:
    if registry_path and registry_path.exists():
        return json.loads(registry_path.read_text())
    return {"types": {}}


def format_registry_context(registry: dict) -> str:
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


def update_registry(registry: dict, spec: dict, registry_path: Optional[Path]) -> bool:
    if not registry_path:
        return False
    changed = False
    project = spec.get("project", "unknown")
    for product in spec.get("products", []):
        taxonomy = product.get("taxonomy")
        if not taxonomy:
            continue
        if taxonomy not in registry["types"]:
            registry["types"][taxonomy] = {
                "depth": 2, "seeds": [],
                "pattern": product.get("type", "unknown"),
                "seen_in": [project],
            }
            changed = True
        else:
            seen = registry["types"][taxonomy].setdefault("seen_in", [])
            if project not in seen:
                seen.append(project)
                changed = True
    if changed:
        registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    return changed


# ─── Prompt & state helpers ───────────────────────────────────────────────────

def load_system_prompt(system_prompt: str | Path, registry_context: str) -> str:
    if isinstance(system_prompt, Path):
        text = system_prompt.read_text()
    else:
        text = system_prompt
    return text.replace("{registry_context}", registry_context)


def extract_spec(text: str) -> dict | None:
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict) and "project" in data:
                return data
        except json.JSONDecodeError:
            pass
    return None


def extract_ok_tags(text: str) -> list[str]:
    return re.findall(r'\[OK:\s*([A-Z_]+)\]', text)


def strip_tags(text: str) -> str:
    lines = text.splitlines()
    clean = [l for l in lines
             if not re.match(r'^\s*\[OK:', l)
             and not re.match(r'^\s*\[Points restants:', l)]
    return '\n'.join(clean).strip()


def state_prefix(established: set, checklist: list[str]) -> str:
    pending = [p for p in checklist if p not in established]
    if not pending:
        return "[Points restants: aucun — passer à la validation finale]\n"
    return f"[Points restants: {', '.join(pending)}]\n"


def resolve_paths(spec: dict, outdir: Path, logdir: Path) -> tuple[Path, Path]:
    project_name = spec.get("project", "projet")
    dest = outdir / project_name / "project.json"
    log  = logdir / f"{project_name}.history.json"
    return dest, log


# ─── Main runner ─────────────────────────────────────────────────────────────

def run_brief(
    system_prompt: str | Path,
    checklist: list[str],
    initial_brief: str = "",
    outdir: Path = Path("outputs"),
    logdir: Path = Path("logs"),
    registry_path: Optional[Path] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict | None:
    """
    Lance la conversation guidée.

    Returns le dict JSON final (project.json) ou None si abandonné.
    """
    import anthropic

    _api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not _api_key:
        raise RuntimeError("ANTHROPIC_API_KEY manquante")

    _model = model or os.getenv("PROJECT_CREATE_MODEL", "claude-haiku-4-5-20251001")
    client = anthropic.Anthropic(api_key=_api_key)

    registry = load_registry(registry_path)
    registry_context = format_registry_context(registry)
    prompt = load_system_prompt(system_prompt, registry_context)

    history: list[dict] = []
    established: set[str] = set()

    print("\n" + "=" * 60)
    print("  Agent Brief — conversation guidée")
    print("  Décrivez votre projet. 'quit' pour abandonner.")
    print("=" * 60)

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
        history.append({"role": "user", "content": state_prefix(established, checklist) + user_msg})

        response = client.messages.create(
            model=_model,
            max_tokens=1024,
            system=prompt,
            messages=history,
        )
        agent_msg = response.content[0].text
        history.append({"role": "assistant", "content": agent_msg})
        established.update(extract_ok_tags(agent_msg))

        print("\n" + "─" * 60)
        print(f"\nAgent : {strip_tags(agent_msg)}\n")

        spec = extract_spec(agent_msg)
        if spec:
            dest, log_dest = resolve_paths(spec, outdir, logdir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            logdir.mkdir(parents=True, exist_ok=True)

            update_registry(registry, spec, registry_path)
            dest.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
            log_dest.write_text(json.dumps(
                {"brief": initial_brief, "history": history},
                indent=2, ensure_ascii=False
            ))
            print("─" * 60)
            print(f"\n✅ Spec  : {dest}")
            print(f"   Log   : {log_dest}\n")
            return spec

        print()
        user_msg = ""
        while not user_msg:
            user_msg = input("Vous : ").strip()
        if user_msg.lower() in ("quit", "exit", "q"):
            print("\n(Conversation abandonnée — spec non sauvegardée)")
            return None
