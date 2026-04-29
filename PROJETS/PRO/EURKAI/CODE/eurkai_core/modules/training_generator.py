"""
training_generator
Module EURKAI agnostique de génération de formations structurées.

Prend un sujet et des paramètres pédagogiques abstraits,
retourne une structure de formation complète organisée par logiques.

Toute spécialisation (métier, secteur, public cible) est injectée
exclusivement via le manifest du projet appelant — ce module ne sait
pas pour qui ni dans quel domaine il génère.

Usage :
    from modules.training_generator import run
    result = run({
        "topic":      "Utiliser l'IA dans son travail",
        "level":      "beginner",
        "objectives": ["comprendre les usages IA", "rédiger des prompts efficaces"],
        "logics":     ["editorial", "technical", "strategic"],
        "format":     "standard",
        "catalog":    catalog,          # optionnel — active le mode LLM
    })

Contrat de sortie :
    {
        "status":   "success" | "partial" | "error",
        "training": {
            "training_title": str,
            "level":          str,
            "modules":        [
                {
                    "logic_type": str,
                    "sections":   [
                        {
                            "title":        str,
                            "description":  str,
                            "key_concepts": [str],
                            "examples":     [str],
                            "exercises":    [str],
                            "prompts":      [str],
                        }
                    ],
                }
            ],
            "summary":    str,
            "next_steps": [str],
        },
        "meta": {
            "mode":    "llm" | "deterministic",
            "errors":  [],
        },
    }
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "training_generator",
    "version":     "1.0.0",
    "type":        "module",
    "layer":       "generation",
    "inputs":      ["topic", "level", "objectives", "logics", "format"],
    "outputs":     ["training"],
    "description": "Génère une structure de formation pédagogique agnostique depuis des logiques abstraites.",
}

# Logiques disponibles — extensible sans modifier le module
LOGIC_LABELS = {
    "editorial":    "Compréhension & Communication",
    "technical":    "Technique & Outils",
    "strategic":    "Stratégie & Vision",
    "operational":  "Mise en pratique & Workflow",
    "cognitive":    "Méthodes de pensée & Réflexion",
    "collaborative":"Collaboration & Partage",
    "creative":     "Créativité & Innovation",
}

# Nombre de sections par format
FORMAT_SECTIONS = {"short": 2, "standard": 3, "long": 5}

# ── Point d'entrée ────────────────────────────────────────────────────────────

def run(input_data):
    topic      = input_data.get("topic", "").strip()
    level      = input_data.get("level", "intermediate")
    objectives = input_data.get("objectives") or []
    logics     = input_data.get("logics") or ["editorial", "technical", "operational"]
    fmt        = input_data.get("format", "standard")
    catalog    = input_data.get("catalog")

    if not topic:
        return {"status": "error", "error": "topic:missing", "training": None, "meta": {"mode": None, "errors": ["topic manquant"]}}

    # Mode LLM si catalog disponible
    if catalog is not None:
        result = _generate_llm(topic, level, objectives, logics, fmt, catalog)
        if result["status"] == "success":
            return result

    # Fallback déterministe
    return _generate_deterministic(topic, level, objectives, logics, fmt)


# ── Mode LLM ─────────────────────────────────────────────────────────────────

def _generate_llm(topic, level, objectives, logics, fmt, catalog):
    try:
        from core.functions.prompt_execute import execute as prompt_execute
    except ImportError:
        return {"status": "error", "error": "prompt_execute:import_failed"}

    n_sections = FORMAT_SECTIONS.get(fmt, 3)
    obj_str    = "\n".join(f"- {o}" for o in objectives) if objectives else "- non spécifié"
    logic_labels = [LOGIC_LABELS.get(l, l) for l in logics]

    prompt = f"""Tu es un expert en ingénierie pédagogique. Génère une formation structurée.

PARAMÈTRES :
- Sujet : {topic}
- Niveau : {level}
- Objectifs :
{obj_str}
- Logiques pédagogiques à couvrir : {', '.join(logics)} ({', '.join(logic_labels)})
- Format : {fmt} ({n_sections} sections par logique)

RÈGLES ABSOLUES :
- Contenu 100% agnostique : aucune référence à un métier, secteur ou outil spécifique
- Exemples universels, applicables à n'importe quel contexte professionnel
- Ton pédagogique clair, progressif, sans jargon inutile
- Chaque section doit avoir : title, description, key_concepts (3-5), examples (2-3), exercises (2-3), prompts (1-3 si pertinent)

RETOURNE UNIQUEMENT du JSON valide avec exactement cette structure :
{{
  "training_title": "string",
  "level": "string",
  "modules": [
    {{
      "logic_type": "string (identifiant de la logique)",
      "sections": [
        {{
          "title": "string",
          "description": "string",
          "key_concepts": ["string"],
          "examples": ["string"],
          "exercises": ["string"],
          "prompts": ["string"]
        }}
      ]
    }}
  ],
  "summary": "string",
  "next_steps": ["string"]
}}"""

    result = prompt_execute("llm", prompt, {"max_tokens": 6000, "temperature": 1}, catalog)

    if not result.get("success"):
        return {"status": "error", "error": result.get("error", "llm:failed")}

    try:
        raw = result["content"].strip()
        # Nettoyer les backticks éventuels
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        training = json.loads(raw.strip())
        return {
            "status":   "success",
            "training": training,
            "meta":     {"mode": "llm", "errors": []},
        }
    except (json.JSONDecodeError, KeyError) as e:
        return {"status": "error", "error": f"json_parse:{e}"}


# ── Mode déterministe (fallback) ──────────────────────────────────────────────

def _generate_deterministic(topic, level, objectives, logics, fmt):
    n_sections = FORMAT_SECTIONS.get(fmt, 3)
    modules    = []

    for logic in logics:
        label    = LOGIC_LABELS.get(logic, logic.capitalize())
        sections = _build_sections(topic, logic, label, objectives, n_sections)
        modules.append({"logic_type": logic, "sections": sections})

    obj_text = objectives[0] if objectives else f"maîtriser {topic}"

    training = {
        "training_title": f"Formation : {topic}",
        "level":          level,
        "modules":        modules,
        "summary":        (
            f"Cette formation couvre {topic} selon {len(logics)} logiques pédagogiques "
            f"({', '.join(logics)}). Elle s'adresse à un niveau {level} "
            f"et vise à {obj_text}."
        ),
        "next_steps": [
            "Mettre en pratique sur un cas concret issu de votre contexte",
            "Identifier 2 à 3 situations récurrentes où appliquer ce qui a été appris",
            "Partager les apprentissages avec son équipe",
        ],
    }

    return {
        "status":   "success",
        "training": training,
        "meta":     {"mode": "deterministic", "errors": []},
    }


def _build_sections(topic, logic, label, objectives, n):
    templates = _section_templates(topic, logic, label, objectives)
    return templates[:n]


def _section_templates(topic, logic, label, objectives):
    base = {
        "editorial": [
            {
                "title":        f"Comprendre {topic} — les fondamentaux",
                "description":  f"Introduction aux concepts clés de {topic}. Cette section pose les bases conceptuelles nécessaires pour progresser.",
                "key_concepts": ["Définition et périmètre", "Pourquoi c'est pertinent aujourd'hui", "Mythes et réalités", "Potentiel et limites"],
                "examples":     ["Situation A : comprendre un concept complexe rapidement", "Situation B : expliquer un sujet à un non-spécialiste"],
                "exercises":    ["En 3 phrases, reformuler ce que vous avez compris de ce sujet", "Identifier 2 idées reçues et les corriger"],
                "prompts":      [f"Explique-moi {topic} comme si j'étais débutant, en 5 points clés"],
            },
            {
                "title":        f"Vocabulaire et repères essentiels",
                "description":  f"Les termes et concepts incontournables pour parler de {topic} avec précision et confiance.",
                "key_concepts": ["Lexique de base", "Distinctions importantes", "Repères temporels", "Sources fiables"],
                "examples":     ["Utiliser le bon vocabulaire dans un email professionnel", "Comprendre une documentation sans formation préalable"],
                "exercises":    ["Créer un glossaire personnel de 10 termes", "Reformuler 3 définitions dans vos propres mots"],
                "prompts":      [f"Définis les 5 termes les plus importants liés à {topic}"],
            },
            {
                "title":        f"Communiquer efficacement autour de {topic}",
                "description":  "Savoir transmettre, expliquer et argumenter sur ce sujet dans un contexte professionnel.",
                "key_concepts": ["Clarté du message", "Adaptation au public", "Argumentation structurée", "Gestion des objections"],
                "examples":     ["Présenter un sujet technique à une direction non spécialisée", "Rédiger une synthèse claire et concise"],
                "exercises":    ["Préparer une explication de 2 minutes sur ce sujet", "Rédiger un email de synthèse sur ce que vous avez appris"],
                "prompts":      ["Aide-moi à rédiger une explication simple de ce concept pour un collègue non spécialiste"],
            },
        ],
        "technical": [
            {
                "title":        f"Les outils et méthodes associés à {topic}",
                "description":  "Panorama des ressources techniques disponibles et comment les utiliser efficacement.",
                "key_concepts": ["Catégories d'outils", "Critères de choix", "Interfaces et prise en main", "Bonnes pratiques d'usage"],
                "examples":     ["Choisir l'outil adapté à un besoin précis", "Comparer deux solutions avant de décider"],
                "exercises":    ["Tester un outil pendant 15 minutes et noter vos observations", "Lister les outils que vous utilisez déjà et identifier les lacunes"],
                "prompts":      [f"Quels sont les meilleurs outils pour {topic} ? Compare-les selon critères : facilité, coût, performance"],
            },
            {
                "title":        "Mise en place technique — premiers pas",
                "description":  "Comment configurer, paramétrer et démarrer concrètement, sans technicité excessive.",
                "key_concepts": ["Configuration initiale", "Paramètres essentiels", "Premiers tests", "Pièges courants"],
                "examples":     ["Première utilisation d'un outil en moins de 30 minutes", "Éviter les erreurs de débutant les plus fréquentes"],
                "exercises":    ["Suivre un tutoriel de démarrage rapide", "Réaliser une première tâche concrète avec l'outil choisi"],
                "prompts":      ["Guide-moi pas à pas pour commencer à utiliser [outil] pour [objectif précis]"],
            },
            {
                "title":        "Optimisation et montée en compétence",
                "description":  "Aller au-delà des fonctions de base pour gagner en efficacité et en maîtrise.",
                "key_concepts": ["Fonctions avancées", "Raccourcis et astuces", "Intégration dans son flux de travail", "Automatisation simple"],
                "examples":     ["Réduire de 50% le temps passé sur une tâche récurrente", "Créer un modèle réutilisable"],
                "exercises":    ["Identifier une tâche répétitive et automatiser une étape", "Partager une astuce découverte avec un collègue"],
                "prompts":      ["Donne-moi 5 astuces avancées pour [outil] que la plupart des utilisateurs ne connaissent pas"],
            },
            {
                "title":        "Sécurité, confidentialité et bonnes pratiques",
                "description":  "Utiliser les outils de façon responsable, sécurisée et conforme.",
                "key_concepts": ["Données sensibles", "Règles de confidentialité", "RGPD et conformité", "Ce qu'il ne faut jamais faire"],
                "examples":     ["Vérifier ce qu'on peut partager ou non avec un outil externe", "Protéger les données clients"],
                "exercises":    ["Identifier 3 informations de votre activité qui ne doivent pas être partagées", "Lire la politique de confidentialité d'un outil que vous utilisez"],
                "prompts":      ["Quelles sont les règles de sécurité essentielles à respecter quand on utilise [type d'outil] en entreprise ?"],
            },
            {
                "title":        "Veille et évolution continue",
                "description":  "Rester à jour dans un domaine qui évolue rapidement, sans y passer trop de temps.",
                "key_concepts": ["Sources fiables", "Fréquence de veille", "Signaux d'alerte", "Partage d'informations"],
                "examples":     ["Mettre en place une routine de veille en 15 min/semaine", "Distinguer l'essentiel du bruit médiatique"],
                "exercises":    ["Identifier 3 sources de veille pertinentes pour votre activité", "S'abonner à une newsletter de référence"],
                "prompts":      ["Quelles sont les meilleures sources pour se tenir informé sur [sujet] sans y passer trop de temps ?"],
            },
        ],
        "strategic": [
            {
                "title":        f"Enjeux et opportunités de {topic} pour votre organisation",
                "description":  "Comprendre pourquoi ce sujet est stratégique aujourd'hui et quelles opportunités il représente.",
                "key_concepts": ["Tendances de fond", "Avantages concurrentiels", "Risques à ne pas ignorer", "Horizon temporel"],
                "examples":     ["Organisation A ayant pris de l'avance — résultats concrets", "Organisation B ayant tardé — conséquences"],
                "exercises":    ["Identifier 3 opportunités concrètes pour votre contexte", "Évaluer votre niveau de maturité actuel sur ce sujet"],
                "prompts":      [f"Quels sont les enjeux stratégiques de {topic} pour une organisation comme la mienne en 2026 ?"],
            },
            {
                "title":        "Prioriser et décider : comment arbitrer",
                "description":  "Méthodes pour prendre de bonnes décisions rapidement dans un environnement incertain.",
                "key_concepts": ["Critères de priorisation", "Matrice effort/impact", "Décision avec information partielle", "Test & apprentissage"],
                "examples":     ["Choisir entre deux options sans toutes les données", "Lancer un test à moindre coût avant d'investir"],
                "exercises":    ["Appliquer la matrice effort/impact à 5 actions possibles", "Définir les 3 critères qui guident vos décisions sur ce sujet"],
                "prompts":      ["Aide-moi à prioriser ces actions selon leur impact potentiel et leur facilité de mise en œuvre : [liste]"],
            },
            {
                "title":        "Construire un plan d'action réaliste",
                "description":  "Transformer une intention stratégique en étapes concrètes, planifiées et mesurables.",
                "key_concepts": ["Objectifs SMART", "Jalons et livrables", "Indicateurs de succès", "Révision et adaptation"],
                "examples":     ["Plan 90 jours pour lancer une première initiative", "Définir un succès mesurable pour éviter l'ambiguïté"],
                "exercises":    ["Rédiger un plan d'action sur 30/60/90 jours", "Définir 3 indicateurs qui confirmeront que vous avancez dans le bon sens"],
                "prompts":      ["Génère un plan d'action sur 90 jours pour [objectif précis], avec jalons et indicateurs de succès"],
            },
        ],
        "operational": [
            {
                "title":        f"Intégrer {topic} dans son quotidien professionnel",
                "description":  "Comment passer de la théorie à la pratique, immédiatement et sans friction.",
                "key_concepts": ["Quick wins", "Intégration progressive", "Gestion du changement personnel", "Habitudes durables"],
                "examples":     ["Commencer par une seule tâche et l'améliorer progressivement", "Remplacer une habitude existante par une nouvelle plus efficace"],
                "exercises":    ["Identifier la première tâche de votre quotidien où vous allez appliquer ce que vous avez appris", "Planifier 3 utilisations concrètes cette semaine"],
                "prompts":      [f"Comment puis-je intégrer {topic} dans mes tâches quotidiennes de façon simple et progressive ?"],
            },
            {
                "title":        "Créer ses propres workflows et templates",
                "description":  "Construire des processus reproductibles pour gagner en efficacité sur le long terme.",
                "key_concepts": ["Standardisation", "Templates réutilisables", "Documentation minimale", "Amélioration continue"],
                "examples":     ["Créer un template pour un rapport hebdomadaire", "Documenter un processus en 5 étapes pour le partager"],
                "exercises":    ["Créer un template pour une tâche que vous faites au moins 1x/semaine", "Documenter votre processus actuel pour le premier point d'amélioration identifié"],
                "prompts":      ["Aide-moi à créer un template réutilisable pour [tâche récurrente précise]"],
            },
            {
                "title":        "Mesurer et améliorer en continu",
                "description":  "Mettre en place des boucles de feedback simples pour progresser régulièrement.",
                "key_concepts": ["Mesure de l'efficacité", "Rétrospective personnelle", "Ajustements itératifs", "Partage d'expérience"],
                "examples":     ["Bilan hebdomadaire en 10 minutes", "Identifier ce qui fonctionne vs ce qui freine"],
                "exercises":    ["Faire un bilan après 1 semaine de pratique : qu'est-ce qui a bien fonctionné ?", "Identifier le 1 ajustement qui aurait le plus d'impact"],
                "prompts":      ["Aide-moi à analyser ce qui a fonctionné et ce qui n'a pas fonctionné cette semaine dans mon utilisation de [sujet]"],
            },
        ],
        "cognitive": [
            {
                "title":        "Développer son esprit critique face à l'information",
                "description":  "Apprendre à évaluer, questionner et valider les informations reçues.",
                "key_concepts": ["Sources primaires vs secondaires", "Biais cognitifs courants", "Vérification croisée", "Scepticisme constructif"],
                "examples":     ["Vérifier une affirmation avant de la relayer", "Identifier un biais dans un raisonnement"],
                "exercises":    ["Prendre une information récente et identifier comment la vérifier", "Lister 3 biais cognitifs qui peuvent influencer vos décisions"],
                "prompts":      ["Aide-moi à analyser cette information de façon critique : [information à analyser]"],
            },
            {
                "title":        "Structurer sa réflexion et résoudre des problèmes complexes",
                "description":  "Méthodes pour décomposer, analyser et résoudre efficacement des problèmes multidimensionnels.",
                "key_concepts": ["Décomposition du problème", "Arbre de causes", "Solutions créatives", "Test d'hypothèses"],
                "examples":     ["Résoudre un blocage en identifiant la cause racine", "Générer 10 idées en 10 minutes avec une méthode structurée"],
                "exercises":    ["Choisir un problème actuel et le décomposer en sous-problèmes", "Identifier 3 solutions potentielles en 5 minutes"],
                "prompts":      ["Aide-moi à structurer ma réflexion pour résoudre ce problème : [description du problème]"],
            },
        ],
        "collaborative": [
            {
                "title":        "Partager et diffuser les bonnes pratiques",
                "description":  "Comment créer une dynamique de montée en compétence collective.",
                "key_concepts": ["Culture d'apprentissage", "Documentation partagée", "Formats de partage", "Reconnaissance des contributions"],
                "examples":     ["Organiser un retour d'expérience en équipe", "Créer une base de connaissance partagée"],
                "exercises":    ["Préparer un partage de 5 minutes sur ce que vous avez appris", "Identifier un collègue à qui transmettre une pratique utile"],
                "prompts":      ["Aide-moi à préparer un retour d'expérience sur [sujet] pour partager avec mon équipe"],
            },
        ],
        "creative": [
            {
                "title":        "Explorer de nouvelles façons de faire",
                "description":  "Sortir des sentiers battus pour innover dans ses pratiques professionnelles.",
                "key_concepts": ["Pensée latérale", "Expérimentation rapide", "Tolérance à l'erreur", "Inspiration externe"],
                "examples":     ["Adapter une pratique d'un autre domaine à son propre contexte", "Tester une idée non conventionnelle à faible risque"],
                "exercises":    ["Imaginer comment votre concurrent idéal utiliserait ce sujet", "Proposer une application originale à votre contexte"],
                "prompts":      [f"Quelles sont les utilisations les plus créatives et inattendues de {topic} dans un contexte professionnel ?"],
            },
        ],
    }

    return base.get(logic, [
        {
            "title":        f"{LOGIC_LABELS.get(logic, logic).capitalize()} — introduction",
            "description":  f"Introduction à la logique {logic} appliquée à {topic}.",
            "key_concepts": ["Concept A", "Concept B", "Concept C"],
            "examples":     ["Exemple générique A", "Exemple générique B"],
            "exercises":    ["Exercice pratique A", "Exercice pratique B"],
            "prompts":      [f"Comment appliquer une approche {logic} à {topic} ?"],
        }
    ])


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_input = {
        "topic":      "Utiliser l'IA dans son travail quotidien",
        "level":      "beginner",
        "objectives": [
            "Comprendre ce qu'est l'IA et ce qu'elle peut faire concrètement",
            "Rédiger des prompts efficaces",
            "Identifier des cas d'usage immédiatement applicables",
        ],
        "logics":  ["editorial", "technical", "operational"],
        "format":  "standard",
        "catalog": None,  # mode déterministe
    }
    r = run(test_input)
    print(f"status : {r['status']}")
    print(f"mode   : {r['meta']['mode']}")
    training = r.get("training", {})
    print(f"titre  : {training.get('training_title')}")
    for m in training.get("modules", []):
        print(f"  [{m['logic_type']}] {len(m['sections'])} section(s)")
