"""Parse les exports ChatGPT JSON et produit un brief structuré via API Anthropic."""
import json
import os
import re
import requests

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, TEMPLATES_DIR


def call_claude(prompt, system=""):
    """Appelle l'API Anthropic Messages."""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def extraire_messages(json_path):
    """Extrait les messages d'un export ChatGPT JSON."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("conversation", {}).get("messages", [])
    titre = data.get("conversationMetadata", {}).get("title", "Sans titre")

    texte = f"# {titre}\n\n"
    for msg in messages:
        role = "NATHALIE" if msg["role"] == "user" else "CHATGPT"
        texte += f"**{role}** :\n{msg['content']}\n\n---\n\n"

    return titre, texte


def generer_brief(json_path):
    """Parse un export ChatGPT et génère un brief structuré."""
    titre, conversation = extraire_messages(json_path)

    template_path = os.path.join(TEMPLATES_DIR, "brief.md")
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    system = (
        "Tu es un chef de projet senior. Tu analyses des conversations "
        "exploratoires et tu en extrais un brief structuré, factuel, opérationnel. "
        "Pas de pitch, pas de flatterie, pas d'emojis. Juste les faits, le périmètre, "
        "les décisions. Tout en français."
    )

    prompt = f"""Voici une conversation exploratoire entre Nathalie et ChatGPT.

Analyse-la et produis un brief structuré en suivant exactement ce template :

{template}

---

CONVERSATION :

{conversation[:30000]}"""

    brief = call_claude(prompt, system)

    # Suggérer un nom de projet
    nom_prompt = (
        "À partir de ce brief, suggère un nom de projet court (1-3 mots, "
        "MAJUSCULES, underscores, pas d'accents, pas d'espaces). "
        "Réponds UNIQUEMENT avec le nom, rien d'autre.\n\n"
        f"{brief[:2000]}"
    )
    nom = call_claude(nom_prompt).strip().upper().replace(" ", "_")
    nom = re.sub(r'[^A-Z0-9_]', '', nom)

    return nom, brief, titre
