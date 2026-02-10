"""Orchestrateur principal du pipeline agence.

Scan TODO/ pour les nouveaux dépôts, gère les transitions d'étapes,
appelle l'API Anthropic pour générer les livrables, déclenche les notifications.
"""
import json
import os
import re
import shutil
from datetime import datetime

from config import (
    TODO_DIR, PROJETS_DIR, STATE_FILE, LOG_FILE,
    PIPELINE_DIR, TEMPLATES_DIR, PROJETS_FILE, HUB_FILE
)
from parser import generer_brief, call_claude
from notifier import notifier

# Étapes du pipeline dans l'ordre
ETAPES = ["BRIEF", "CDC", "SPECS", "BUILD", "DEPLOY"]

# Correspondance étape → (fichier gate, fichier livrable)
GATE_MAP = {
    "BRIEF":  ("GATE_1_BRIEF.md",  "01_BRIEF.md"),
    "CDC":    ("GATE_2_CDC.md",    "02_CDC.md"),
    "SPECS":  ("GATE_3_SPECS.md",  "03_SPECS.md"),
    "BUILD":  ("GATE_4_BUILD.md",  "04_BUILD_REPORT.md"),
    "DEPLOY": ("GATE_5_LAUNCH.md", "05_DEPLOY.md"),
}

# Templates par étape (pour la génération)
TEMPLATE_MAP = {
    "CDC":    "cdc.md",
    "SPECS":  "specs.md",
}


def log(message):
    """Log horodaté dans pipeline.log et stdout."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def charger_state():
    """Charge l'état du pipeline depuis state.json."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"projects": {}, "processed_files": []}


def sauver_state(state):
    """Sauvegarde l'état du pipeline."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def charger_template(nom):
    """Charge un template markdown."""
    path = os.path.join(TEMPLATES_DIR, nom)
    with open(path, encoding="utf-8") as f:
        return f.read()


# --- GATE ---

def creer_gate(projet_path, gate_num, etape, resume, questions=""):
    """Crée un fichier GATE pour validation Nathalie."""
    template = charger_template("gate.md")
    nom = os.path.basename(projet_path)

    contenu = template.replace("{N}", str(gate_num))
    contenu = contenu.replace("{ETAPE}", etape)
    contenu = contenu.replace("{NOM_PROJET}", nom)
    contenu = contenu.replace("{DATE}", datetime.now().strftime("%Y-%m-%d"))
    contenu = contenu.replace("{RESUME}", resume)
    contenu = contenu.replace("{LIVRABLES}", f"→ `PIPELINE/{GATE_MAP[etape][1]}`")
    contenu = contenu.replace("{QUESTIONS}", questions or "Aucune question particulière.")

    gate_dir = os.path.join(projet_path, "VALIDATION")
    os.makedirs(gate_dir, exist_ok=True)
    gate_path = os.path.join(gate_dir, GATE_MAP[etape][0])

    with open(gate_path, "w", encoding="utf-8") as f:
        f.write(contenu)

    return gate_path


def lire_gate(projet_path, etape):
    """Lit le statut d'une GATE. Retourne (statut, commentaires) ou (None, '')."""
    gate_name = GATE_MAP[etape][0]
    gate_path = os.path.join(projet_path, "VALIDATION", gate_name)

    if not os.path.exists(gate_path):
        return None, ""

    with open(gate_path, encoding="utf-8") as f:
        contenu = f.read()

    # Chercher STATUT: GO / AJUSTER / KILL (après la section DÉCISION)
    match = re.search(r'STATUT:\s*(GO|AJUSTER|KILL)', contenu, re.IGNORECASE)
    if not match:
        return None, ""

    statut = match.group(1).upper()

    # Extraire les commentaires après "Commentaires :"
    comm_match = re.search(r'Commentaires\s*:\s*(.*)', contenu, re.DOTALL)
    commentaires = comm_match.group(1).strip() if comm_match else ""

    return statut, commentaires


# --- CRÉATION PROJET ---

def creer_projet(nom, brief, titre, source_path):
    """Crée la structure complète d'un nouveau projet."""
    projet_path = os.path.join(PROJETS_DIR, nom)

    # Arborescence
    for sub in ["PIPELINE", "VALIDATION", "src", "tests", "dist"]:
        os.makedirs(os.path.join(projet_path, sub), exist_ok=True)

    # Copier la source originale
    shutil.copy2(source_path, os.path.join(projet_path, "PIPELINE", "00_SOURCE.json"))

    # Écrire le brief
    with open(os.path.join(projet_path, "PIPELINE", "01_BRIEF.md"), "w", encoding="utf-8") as f:
        f.write(brief)

    # _SUIVI.md
    date = datetime.now().strftime("%Y-%m-%d")
    suivi = (
        f"# {nom} — Suivi\n\n"
        f"> {titre}\n\n"
        f"**Statut** : 💡 idée — brief généré, en attente validation\n"
        f"**Créé** : {date}\n"
        f"**Dernière MAJ** : {date}\n"
        f"**Pipeline** : BRIEF ⏳\n\n"
        "---\n\n"
        "## Historique\n\n"
        f"- {date} : Création automatique via Pipeline Agence\n"
    )
    with open(os.path.join(projet_path, "_SUIVI.md"), "w", encoding="utf-8") as f:
        f.write(suivi)

    # README.md
    readme = (
        f"# {nom}\n\n"
        f"> {titre}\n\n"
        "Projet créé automatiquement par le Pipeline Agence.\n"
        "Brief original dans `PIPELINE/01_BRIEF.md`.\n\n"
        "## Statut\n\nEn cours de cadrage — voir `_SUIVI.md`.\n"
    )
    with open(os.path.join(projet_path, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    # GATE 1
    creer_gate(
        projet_path, 1, "BRIEF",
        "Le brief a été généré automatiquement à partir de ta conversation ChatGPT.",
        "Le brief est-il fidèle à ton idée ? Le périmètre est-il correct ?"
    )

    # Enregistrer dans _PROJETS.md
    enregistrer_projet(nom, projet_path, titre)

    log(f"Projet {nom} créé dans {projet_path}")
    return projet_path


def enregistrer_projet(nom, projet_path, titre):
    """Ajoute le projet dans _PROJETS.md."""
    rel_path = os.path.relpath(projet_path, os.path.dirname(os.path.dirname(PROJETS_FILE)))
    ligne = f"| **{nom}** | `{rel_path}/` | {titre} | 💡 idée |\n"

    if os.path.exists(PROJETS_FILE):
        with open(PROJETS_FILE, encoding="utf-8") as f:
            contenu = f.read()
        if nom not in contenu:
            # Insérer avant la section "Projets archivés"
            contenu = contenu.replace(
                "\n## Projets archivés",
                f"{ligne}\n## Projets archivés"
            )
            with open(PROJETS_FILE, "w", encoding="utf-8") as f:
                f.write(contenu)


# --- GÉNÉRATION D'ÉTAPES ---

def etape_suivante(etape):
    """Retourne l'étape suivante ou None si terminé."""
    idx = ETAPES.index(etape)
    return ETAPES[idx + 1] if idx + 1 < len(ETAPES) else None


def generer_etape(projet_path, etape, commentaires_nathalie=""):
    """Génère le livrable d'une étape via l'API Anthropic."""
    nom = os.path.basename(projet_path)

    # Accumuler le contexte (tous les livrables précédents)
    contexte = ""
    for step in ETAPES:
        doc_path = os.path.join(projet_path, "PIPELINE", GATE_MAP[step][1])
        if os.path.exists(doc_path):
            with open(doc_path, encoding="utf-8") as f:
                contexte += f"\n\n---\n## {step}\n\n{f.read()}"
        if step == etape:
            break

    # Charger le template si dispo
    template = ""
    tpl_name = TEMPLATE_MAP.get(etape)
    if tpl_name:
        tpl_path = os.path.join(TEMPLATES_DIR, tpl_name)
        if os.path.exists(tpl_path):
            with open(tpl_path, encoding="utf-8") as f:
                template = f.read()

    system = (
        "Tu es un chef de projet technique senior dans une agence digitale. "
        "Tu produis des documents de projet structurés, factuels, opérationnels. "
        "Pas de pitch, pas de flatterie, pas d'emojis. "
        "Tout en français. Sois précis et concret."
    )

    retours = ""
    if commentaires_nathalie:
        retours = f"\n\nRetours de Nathalie à intégrer :\n{commentaires_nathalie}"

    if etape == "BUILD":
        instruction = (
            "Produis un RAPPORT DE CONSTRUCTION détaillé : "
            "architecture implémentée, fichiers à créer, code clé, "
            "tests à écrire, points d'attention. "
            "Ce document servira de guide pour la session de développement."
        )
    elif etape == "DEPLOY":
        instruction = (
            "Produis un PLAN DE DÉPLOIEMENT ET MARKETING : "
            "environnement cible, checklist déploiement, configuration, "
            "positionnement, assets marketing, plan de lancement, campagnes."
        )
    else:
        instruction = f"Produis le document : **{etape}**"
        if template:
            instruction += f"\n\nEn suivant ce template :\n\n{template}"

    prompt = f"Projet : {nom}\n\nContexte accumulé :\n{contexte}{retours}\n\n{instruction}"

    resultat = call_claude(prompt, system)

    # Écrire le livrable
    doc_name = GATE_MAP[etape][1]
    doc_path = os.path.join(projet_path, "PIPELINE", doc_name)
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(resultat)

    # Créer la GATE
    gate_num = ETAPES.index(etape) + 1
    creer_gate(
        projet_path, gate_num, etape,
        f"Le {etape} a été généré. Voir `PIPELINE/{doc_name}`.",
        "Le contenu te convient ? Des ajustements nécessaires ?"
    )

    # MAJ _SUIVI.md
    maj_suivi(projet_path, etape)

    log(f"[{nom}] {etape} généré → GATE {gate_num} créée")
    return doc_path


def maj_suivi(projet_path, etape):
    """Met à jour le _SUIVI.md du projet."""
    suivi_path = os.path.join(projet_path, "_SUIVI.md")
    if not os.path.exists(suivi_path):
        return
    date = datetime.now().strftime("%Y-%m-%d")
    with open(suivi_path, encoding="utf-8") as f:
        contenu = f.read()
    # Ajouter la ligne d'historique
    contenu = contenu.replace(
        "## Historique\n",
        f"## Historique\n\n- {date} : {etape} généré, GATE en attente\n"
    )
    # MAJ date
    contenu = re.sub(
        r'\*\*Dernière MAJ\*\* : .+',
        f'**Dernière MAJ** : {date}',
        contenu
    )
    # MAJ pipeline stage
    contenu = re.sub(
        r'\*\*Pipeline\*\* : .+',
        f'**Pipeline** : {etape} ⏳',
        contenu
    )
    with open(suivi_path, "w", encoding="utf-8") as f:
        f.write(contenu)


# --- POINT D'ENTRÉE ---

def run():
    """Point d'entrée principal. Appelé par le dispatcher."""
    state = charger_state()
    changements = False

    # --- A. Scanner les nouveaux dépôts dans TODO/ ---
    if os.path.exists(TODO_DIR):
        for fichier in sorted(os.listdir(TODO_DIR)):
            if fichier.startswith("."):
                continue
            if fichier in state.get("processed_files", []):
                continue
            filepath = os.path.join(TODO_DIR, fichier)
            if not os.path.isfile(filepath):
                continue

            log(f"Nouveau dépôt détecté : {fichier}")

            try:
                if fichier.endswith(".json"):
                    nom, brief, titre = generer_brief(filepath)
                else:
                    log(f"Format non supporté pour l'instant : {fichier}")
                    continue

                projet_path = creer_projet(nom, brief, titre, filepath)

                state.setdefault("processed_files", []).append(fichier)
                state.setdefault("projects", {})[nom] = {
                    "source": fichier,
                    "created": datetime.now().isoformat(),
                    "stage": "BRIEF",
                    "stage_status": "GATE_PENDING",
                    "path": projet_path
                }

                notifier(nom, "BRIEF", f"Brief généré à partir de : {titre}")
                changements = True

            except Exception as e:
                log(f"ERREUR traitement {fichier} : {e}")

    # --- B. Progresser les projets existants ---
    for nom, info in list(state.get("projects", {}).items()):
        if info.get("stage_status") != "GATE_PENDING":
            continue

        projet_path = info["path"]
        etape = info["stage"]
        statut, commentaires = lire_gate(projet_path, etape)

        if statut is None:
            continue

        if statut == "KILL":
            info["stage_status"] = "KILLED"
            log(f"[{nom}] KILL par Nathalie à l'étape {etape}")
            changements = True
            continue

        if statut == "AJUSTER":
            log(f"[{nom}] AJUSTER demandé à l'étape {etape}")
            try:
                generer_etape(projet_path, etape, commentaires)
                notifier(nom, f"{etape} (ajusté)", "Version ajustée selon tes retours.")
            except Exception as e:
                log(f"ERREUR ajustement {nom}/{etape} : {e}")
            changements = True
            continue

        if statut == "GO":
            suivante = etape_suivante(etape)
            if suivante is None:
                info["stage_status"] = "DONE"
                log(f"[{nom}] Pipeline terminé !")
                notifier(nom, "TERMINÉ", "Tous les livrables sont produits.")
                changements = True
                continue

            log(f"[{nom}] GO → passage à {suivante}")
            try:
                generer_etape(projet_path, suivante)
                info["stage"] = suivante
                info["stage_status"] = "GATE_PENDING"
                notifier(nom, suivante)
            except Exception as e:
                log(f"ERREUR génération {nom}/{suivante} : {e}")
            changements = True

    # --- C. Sauvegarder ---
    if changements:
        sauver_state(state)
        log("State sauvegardé.")


if __name__ == "__main__":
    run()
