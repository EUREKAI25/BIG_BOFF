"""
training_generator v2.0.0
Module EURKAI agnostique de génération de formations interactives structurées.

Produit un PARCOURS PÉDAGOGIQUE complet — pas seulement du contenu :
  chapters > lessons > content_blocks + interactive_tasks

Toute spécialisation (métier, secteur, public) vient du manifest appelant.
Ce module ne sait pas pour qui ni dans quel domaine il génère.

Usage :
    from modules.training_generator import run
    result = run({
        "topic":      "Utiliser l'IA dans son travail quotidien",
        "level":      "beginner",
        "objectives": ["comprendre les usages IA", "rédiger des prompts efficaces"],
        "logics":     ["editorial", "technical", "operational"],
        "format":     "standard",
        "catalog":    catalog,  # None = mode déterministe
    })

Contrat de sortie :
    {
      "status":   "success" | "error",
      "training": {
        "training_title":  str,
        "level":           str,
        "estimated_duration": str,
        "progression": {
          "total_chapters": int,
          "total_lessons":  int,
          "total_tasks":    int,
          "completion_status": "not_started"
        },
        "chapters": [
          {
            "chapter_id": "ch_1",
            "order": 1,
            "title": str,
            "logic_type": str,
            "objective": str,
            "status": "available" | "locked",
            "estimated_duration": str,
            "lessons": [
              {
                "lesson_id": "ls_1_1",
                "order": 1,
                "title": str,
                "objective": str,
                "status": "available" | "locked",
                "content_blocks": [
                  {"type": "theory|example|method|warning|prompt|checklist",
                   "title": str, "content": str}
                ],
                "interactive_tasks": [
                  {
                    "task_id": "task_1_1_1",
                    "type": "question|exercise|prompt_practice|self_assessment|checklist",
                    "instruction": str,
                    "expected_user_action": str,
                    "validation_mode": "manual|self_check",
                    "success_criteria": [str]
                  }
                ],
                "completion_rules": {
                  "required_tasks": [str],
                  "minimum_score":  null,
                  "can_skip":       false
                }
              }
            ],
            "chapter_validation": {
              "type": "quiz|practical_case|checklist|reflection",
              "instructions": str,
              "success_criteria": [str]
            }
          }
        ],
        "final_validation": { "type": str, "instructions": str, "success_criteria": [str] },
        "certificate_data": { "enabled": true, ... }
      },
      "meta": {"mode": "llm" | "deterministic", "errors": []}
    }
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "training_generator",
    "version":     "2.0.0",
    "type":        "module",
    "layer":       "generation",
    "inputs":      ["topic", "level", "objectives", "logics", "format", "catalog", "theme"],
    "outputs":     ["training"],
    "description": "Génère un parcours de formation interactif structuré en chapitres > leçons > tâches.",
}

LOGIC_LABELS = {
    "editorial":     "Comprendre & Communiquer",
    "technical":     "Maîtriser les Outils",
    "strategic":     "Vision & Stratégie",
    "operational":   "Mise en Pratique",
    "cognitive":     "Esprit Critique & Réflexion",
    "collaborative": "Collaboration & Partage",
    "creative":      "Créativité & Innovation",
}

FORMAT_LESSONS  = {"short": 2, "standard": 3, "long": 5}
FORMAT_DURATION = {"short": "1h30", "standard": "2h30", "long": "4h"}

# Thème par défaut — utilisé si aucun thème n'est fourni.
# Le design final appartient au projet consommateur du module.
DEFAULT_THEME = {
    "mode": "default",
    "tokens": {
        "primary":     "#1a1a2e",
        "accent":      "#e94560",
        "background":  "#f0f2f5",
        "surface":     "#ffffff",
        "text":        "#2d3436",
        "muted":       "#636e72",
        "border":      "#e0e3e8",
        "radius":      "8px",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    },
    "layout": {
        "navigation":      "sidebar",
        "chapter_display": "accordion",
        "lesson_display":  "accordion",
    },
}


def _resolve_theme(theme_input):
    """Fusionne le thème fourni avec DEFAULT_THEME.
    Les tokens du projet ne sont jamais écrasés par les valeurs par défaut."""
    if not theme_input:
        return {k: (v.copy() if isinstance(v, dict) else v) for k, v in DEFAULT_THEME.items()}
    return {
        "mode":   theme_input.get("mode", "custom"),
        "tokens": {**DEFAULT_THEME["tokens"], **theme_input.get("tokens", {})},
        "layout": {**DEFAULT_THEME["layout"], **theme_input.get("layout", {})},
    }


# ── Point d'entrée ────────────────────────────────────────────────────────────

def run(input_data):
    topic      = (input_data.get("topic") or "").strip()
    level      = input_data.get("level", "intermediate")
    objectives = input_data.get("objectives") or []
    logics     = input_data.get("logics") or ["editorial", "technical", "operational"]
    fmt        = input_data.get("format", "standard")
    catalog    = input_data.get("catalog")
    theme      = input_data.get("theme")

    resolved_theme = _resolve_theme(theme)

    if not topic:
        return {
            "status": "error", "error": "topic:missing",
            "training": None, "meta": {"mode": None, "errors": ["topic manquant"]}
        }

    if catalog is not None:
        result = _generate_llm(topic, level, objectives, logics, fmt, catalog)
        if result["status"] == "success":
            result["meta"]["theme"] = resolved_theme
            return result

    result = _generate_deterministic(topic, level, objectives, logics, fmt)
    result["meta"]["theme"] = resolved_theme
    return result


# ── Mode LLM ──────────────────────────────────────────────────────────────────

def _generate_llm(topic, level, objectives, logics, fmt, catalog):
    try:
        from core.functions.prompt_execute import execute as prompt_execute
    except ImportError:
        return {"status": "error", "error": "prompt_execute:import_failed"}

    n_lessons = FORMAT_LESSONS.get(fmt, 3)
    obj_str   = "\n".join(f"- {o}" for o in objectives) if objectives else "- non spécifié"

    prompt = f"""Tu es un expert en ingénierie pédagogique.
Génère un parcours de formation interactif structuré en chapitres, leçons et tâches.

PARAMÈTRES :
- Sujet : {topic}
- Niveau : {level}
- Objectifs :
{obj_str}
- Logiques (1 chapitre par logique) : {', '.join(logics)}
- Format : {fmt} ({n_lessons} leçons par chapitre)

RÈGLES ABSOLUES :
- Contenu 100% agnostique (aucun métier / secteur / outil spécifique)
- Chaque leçon doit demander une action concrète à l'apprenant
- Types content_block : theory | example | method | warning | prompt | checklist
- Types task : question | exercise | prompt_practice | self_assessment | checklist
- validation_mode : toujours "self_check" ou "manual"
- Premier chapitre status="available", les autres "locked"
- Première leçon de chaque chapitre status="available", les autres "locked"

STRUCTURE JSON EXACTE (respecter les IDs) :
{{
  "training_title": "...",
  "level": "...",
  "estimated_duration": "...",
  "progression": {{"total_chapters": N, "total_lessons": N, "total_tasks": N, "completion_status": "not_started"}},
  "chapters": [
    {{
      "chapter_id": "ch_1",
      "order": 1,
      "title": "...",
      "logic_type": "{logics[0] if logics else 'editorial'}",
      "objective": "...",
      "status": "available",
      "estimated_duration": "...",
      "lessons": [
        {{
          "lesson_id": "ls_1_1",
          "order": 1,
          "title": "...",
          "objective": "...",
          "status": "available",
          "content_blocks": [{{"type": "theory", "title": "...", "content": "..."}}],
          "interactive_tasks": [
            {{
              "task_id": "task_1_1_1",
              "type": "self_assessment",
              "instruction": "...",
              "expected_user_action": "...",
              "validation_mode": "self_check",
              "success_criteria": ["..."]
            }}
          ],
          "completion_rules": {{"required_tasks": ["task_1_1_1"], "minimum_score": null, "can_skip": false}}
        }}
      ],
      "chapter_validation": {{"type": "reflection", "instructions": "...", "success_criteria": ["..."]}}
    }}
  ],
  "final_validation": {{"type": "action_plan", "instructions": "...", "success_criteria": ["..."]}},
  "certificate_data": {{"enabled": true, "requires_completion": true, "tracked_items": ["chapters_completed","lessons_completed","tasks_completed","final_validation_completed"]}}
}}

RETOURNE UNIQUEMENT du JSON valide."""

    result = prompt_execute("llm", prompt, {"max_tokens": 8000, "temperature": 1}, catalog)
    if not result.get("success"):
        return {"status": "error", "error": result.get("error", "llm:failed")}

    try:
        raw = result["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        training = json.loads(raw.strip())
        return {"status": "success", "training": training, "meta": {"mode": "llm", "errors": []}}
    except (json.JSONDecodeError, KeyError) as e:
        return {"status": "error", "error": f"json_parse:{e}"}


# ── Mode déterministe ─────────────────────────────────────────────────────────

def _generate_deterministic(topic, level, objectives, logics, fmt):
    n_lessons = FORMAT_LESSONS.get(fmt, 3)
    chapters  = []

    for i, logic in enumerate(logics):
        ch = _build_chapter(i + 1, logic, topic, objectives, n_lessons)
        ch["status"] = "available" if i == 0 else "locked"
        chapters.append(ch)

    total_tasks   = sum(len(ls["interactive_tasks"]) for ch in chapters for ls in ch["lessons"])
    total_lessons = sum(len(ch["lessons"]) for ch in chapters)

    return {
        "status": "success",
        "training": {
            "training_title":     f"Formation : {topic}",
            "level":              level,
            "estimated_duration": FORMAT_DURATION.get(fmt, "2h30"),
            "progression": {
                "total_chapters":    len(chapters),
                "total_lessons":     total_lessons,
                "total_tasks":       total_tasks,
                "completion_status": "not_started",
            },
            "chapters":          chapters,
            "final_validation":  _final_validation(topic),
            "certificate_data": {
                "enabled":             True,
                "requires_completion": True,
                "tracked_items": [
                    "chapters_completed", "lessons_completed",
                    "tasks_completed",    "final_validation_completed"
                ],
            },
        },
        "meta": {"mode": "deterministic", "errors": []},
    }


def _build_chapter(order, logic, topic, objectives, n_lessons):
    tmpl    = _chapter_template(logic, topic, objectives)
    lessons = [
        _build_lesson(order, j + 1, lt)
        for j, lt in enumerate(tmpl["lessons"][:n_lessons])
    ]
    return {
        "chapter_id":         f"ch_{order}",
        "order":               order,
        "title":               tmpl["title"],
        "logic_type":          logic,
        "objective":           tmpl["objective"],
        "status":              "locked",
        "estimated_duration":  tmpl["duration"],
        "lessons":             lessons,
        "chapter_validation":  tmpl["validation"],
    }


def _build_lesson(ch_order, lesson_order, template):
    task_ids = [f"task_{ch_order}_{lesson_order}_{k+1}"
                for k in range(len(template["interactive_tasks"]))]
    tasks = [{**t, "task_id": task_ids[i]}
             for i, t in enumerate(template["interactive_tasks"])]
    return {
        "lesson_id":   f"ls_{ch_order}_{lesson_order}",
        "order":        lesson_order,
        "title":        template["title"],
        "objective":    template["objective"],
        "status":       "available" if lesson_order == 1 else "locked",
        "content_blocks":    template["content_blocks"],
        "interactive_tasks": tasks,
        "completion_rules": {
            "required_tasks": task_ids,
            "minimum_score":  None,
            "can_skip":       False,
        },
    }


def _final_validation(topic):
    return {
        "type": "action_plan",
        "instructions": (
            f"Pour valider cette formation sur '{topic}', rédigez votre plan d'action personnel : "
            "identifiez 3 actions concrètes à mettre en œuvre dans les 7 prochains jours, "
            "avec un responsable, une date et un indicateur de succès pour chacune."
        ),
        "success_criteria": [
            "3 actions concrètes identifiées",
            "Chaque action est spécifique et mesurable",
            "Délai de mise en œuvre défini pour chaque action",
            "Premier pas clairement décidé",
        ],
    }


# ── Dispatch templates ────────────────────────────────────────────────────────

def _chapter_template(logic, topic, objectives):
    fn = {
        "editorial":     _tmpl_editorial,
        "technical":     _tmpl_technical,
        "strategic":     _tmpl_strategic,
        "operational":   _tmpl_operational,
        "cognitive":     _tmpl_cognitive,
        "collaborative": _tmpl_collaborative,
        "creative":      _tmpl_creative,
    }.get(logic, _tmpl_generic)
    return fn(topic, objectives)


# ── Templates ─────────────────────────────────────────────────────────────────

def _tmpl_editorial(topic, _obj):
    t = topic
    return {
        "title":     f"Comprendre et communiquer sur {t}",
        "objective": f"Maîtriser les fondamentaux de {t} et savoir l'expliquer clairement.",
        "duration":  "45min",
        "lessons": [
            {
                "title":     "Les fondamentaux — ce que vous devez savoir",
                "objective": f"Comprendre ce qu'est {t}, ce que ça change réellement, et corriger les idées reçues.",
                "content_blocks": [
                    {
                        "type":    "theory",
                        "title":   f"Qu'est-ce que {t} ?",
                        "content": (
                            f"{t} désigne un ensemble de méthodes, d'outils et de pratiques qui transforment "
                            f"la façon de travailler. L'essentiel : c'est un moyen, pas une fin. "
                            f"Ce qui compte, c'est ce que ça permet de faire concrètement."
                        ),
                    },
                    {
                        "type":    "example",
                        "title":   "Ce que ça change en pratique",
                        "content": (
                            f"Avec {t}, une tâche qui prenait 1h peut être réduite à 10 minutes. "
                            f"L'exemple le plus universel : rédiger un document depuis une structure "
                            f"générée automatiquement, plutôt que depuis une page blanche."
                        ),
                    },
                    {
                        "type":    "warning",
                        "title":   "3 idées reçues à corriger maintenant",
                        "content": (
                            "1. « C'est réservé aux experts » — FAUX : les outils actuels sont accessibles à tous.\n"
                            "2. « Ça va remplacer mon travail » — NUANCÉ : certaines tâches, pas votre valeur ajoutée.\n"
                            "3. « C'est trop long à apprendre » — FAUX : opérationnel en quelques heures."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "self_assessment",
                        "instruction":           "Avant de continuer, évaluez votre niveau de connaissance actuel sur ce sujet (1 = débutant, 5 = expert).",
                        "expected_user_action":  "Choisir une note de 1 à 5",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Votre point de départ est noté"],
                    },
                    {
                        "type":                  "question",
                        "instruction":           f"En 2-3 phrases, expliquez ce qu'est {t} comme si vous deviez l'expliquer à un collègue non technique.",
                        "expected_user_action":  "Rédiger une explication simple, sans jargon",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Explication compréhensible sans connaissance préalable", "Pas de jargon inutile"],
                    },
                ],
            },
            {
                "title":     "Expliquer et convaincre — construire son discours",
                "objective": f"Savoir présenter {t} clairement à différents interlocuteurs.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "La structure en 3 temps pour tout expliquer",
                        "content": (
                            "1. CONTEXTE : pourquoi ce sujet est pertinent maintenant ?\n"
                            "2. CONCRET : qu'est-ce que ça change dans la pratique ?\n"
                            "3. ACTION : qu'est-ce qu'on fait avec ça ?\n\n"
                            "Cette structure fonctionne pour 2 minutes comme pour 30 minutes."
                        ),
                    },
                    {
                        "type":    "prompt",
                        "title":   "Prompt à utiliser",
                        "content": f"Aide-moi à préparer une explication de 2 minutes sur {t} pour [mon directeur / mon équipe / un client]. Je veux mettre en avant les bénéfices concrets sans jargon technique.",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "prompt_practice",
                        "instruction":           "Utilisez le prompt ci-dessus, adaptez-le à votre contexte, et notez la présentation générée.",
                        "expected_user_action":  "Lancer le prompt, lire le résultat, l'ajuster si besoin",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Présentation générée", "Dure moins de 2 minutes à lire"],
                    },
                    {
                        "type":                  "exercise",
                        "instruction":           "Préparez un retour d'expérience de 5 minutes à partager avec votre équipe après cette formation.",
                        "expected_user_action":  "Rédiger les 3 points clés à transmettre",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["3 points identifiés", "Chaque point illustré par un exemple"],
                    },
                ],
            },
            {
                "title":     "Synthétiser et documenter ses apprentissages",
                "objective": "Créer une ressource personnelle réutilisable.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "La note de synthèse en 5 éléments",
                        "content": (
                            "1. Définition en 1 phrase\n"
                            "2. 3 bénéfices concrets\n"
                            "3. 2 limites ou points de vigilance\n"
                            "4. 1 exemple d'application dans votre contexte\n"
                            "5. Prochaine étape recommandée\n\n"
                            "Format idéal : une page max, relisible en 3 minutes."
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Checklist de validation",
                        "content": (
                            "✓ J'ai défini le sujet en mes propres mots\n"
                            "✓ J'ai identifié au moins 2 bénéfices pour mon contexte\n"
                            "✓ J'ai noté une limite ou un point de vigilance\n"
                            "✓ J'ai un exemple concret à partager\n"
                            "✓ Je sais quelle est ma prochaine action"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Rédigez votre synthèse personnelle sur {t} en suivant la structure en 5 éléments.",
                        "expected_user_action":  "Créer une fiche synthèse en moins d'une page",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Synthèse rédigée", "Les 5 éléments sont présents"],
                    },
                    {
                        "type":                  "self_assessment",
                        "instruction":           "Êtes-vous maintenant à l'aise pour expliquer ce sujet à un collègue ?",
                        "expected_user_action":  "Évaluer honnêtement votre niveau de confiance sur 5",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Progression évaluée"],
                    },
                ],
            },
            {
                "title":     "Rester à jour sans se noyer",
                "objective": "Mettre en place une veille efficace en 15 minutes par semaine.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Veille intelligente",
                        "content": f"Règle simple : 1 source principale + 1 revue hebdo + 1 alerte sur les évolutions majeures.\nPour {t}, priorité aux retours d'expérience concrets plutôt qu'aux annonces de tendances.",
                    },
                    {
                        "type":    "warning",
                        "title":   "Danger : la surcharge d'information",
                        "content": "Filtrez sans pitié :\n• Priorité 1 : ce qui impacte votre pratique immédiate\n• Priorité 2 : tendances de fond (1x/mois suffit)\n• À ignorer : le buzz et les annonces marketing",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Identifiez 2 sources de veille pertinentes et définissez à quelle fréquence vous les consultez.",
                        "expected_user_action":  "Lister 2 sources + fréquence de consultation",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["2 sources identifiées", "Fréquence définie"],
                    },
                ],
            },
            {
                "title":     "Consolidation et évaluation du chapitre",
                "objective": "Vérifier l'ensemble des acquis avant de passer à la suite.",
                "content_blocks": [
                    {
                        "type":    "checklist",
                        "title":   "Ce que vous devez maintenant maîtriser",
                        "content": (
                            f"✓ Définir {t} en termes simples\n"
                            "✓ Identifier ses bénéfices pour votre contexte\n"
                            "✓ Expliquer le sujet à un non-spécialiste\n"
                            "✓ Éviter les 3 idées reçues principales\n"
                            "✓ Avoir une source de veille active"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "checklist",
                        "instruction":           "Cochez chaque élément que vous maîtrisez maintenant.",
                        "expected_user_action":  "Vérifier honnêtement chaque point",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Au moins 4 éléments sur 5 cochés"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "reflection",
            "instructions": f"En quoi {t} change-t-il quelque chose pour vous personnellement ou professionnellement ? Donnez un exemple concret en 5-10 phrases.",
            "success_criteria": [
                "Réponse rédigée",
                "Au moins un exemple concret",
                "Lien avec votre contexte personnel ou professionnel",
            ],
        },
    }


def _tmpl_technical(topic, _obj):
    t = topic
    return {
        "title":     f"Maîtriser les outils et méthodes liés à {t}",
        "objective": "Choisir les bons outils, les prendre en main et adopter les bonnes pratiques.",
        "duration":  "50min",
        "lessons": [
            {
                "title":     "Panorama — quels outils pour quels besoins",
                "objective": "Comprendre l'écosystème disponible et identifier les outils pertinents.",
                "content_blocks": [
                    {
                        "type":    "theory",
                        "title":   "Catégories d'outils à connaître",
                        "content": (
                            f"Pour {t}, les outils se classent en :\n"
                            "• Outils d'exploration : comprendre et découvrir\n"
                            "• Outils de production : créer et générer\n"
                            "• Outils d'organisation : structurer et gérer\n"
                            "• Outils d'analyse : mesurer et optimiser"
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Critères pour choisir un outil",
                        "content": (
                            "✓ Opérationnel en moins de 30 minutes\n"
                            "✓ Coût justifié par le gain de temps\n"
                            "✓ Compatible avec vos outils existants\n"
                            "✓ Données protégées (RGPD)\n"
                            "✓ Support disponible si blocage"
                        ),
                    },
                    {
                        "type":    "warning",
                        "title":   "Pièges courants",
                        "content": (
                            "❌ Changer d'outil toutes les semaines\n"
                            "❌ Prendre le plus complexe par défaut\n"
                            "❌ Ignorer la confidentialité des données\n"
                            "❌ Vouloir tout maîtriser avant de commencer"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "self_assessment",
                        "instruction":           f"Listez les outils liés à {t} que vous utilisez déjà et évaluez votre niveau pour chacun (1-5).",
                        "expected_user_action":  "État des lieux de ses outils actuels",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["État des lieux réalisé"],
                    },
                    {
                        "type":                  "question",
                        "instruction":           "Quel est votre besoin prioritaire que vous aimeriez adresser avec un outil adapté ?",
                        "expected_user_action":  "Formuler son besoin principal en 1-2 phrases",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Besoin clairement formulé"],
                    },
                ],
            },
            {
                "title":     "Premiers pas — prise en main pratique",
                "objective": "Être opérationnel sur un outil en moins de 30 minutes.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Méthode en 4 étapes pour tout outil",
                        "content": (
                            "1. OBJECTIF SIMPLE : choisir UNE tâche à réaliser avec l'outil\n"
                            "2. PREMIER TEST : essayer sans lire la doc (intuition)\n"
                            "3. RÉSULTAT : noter ce qui a marché et ce qui a bloqué\n"
                            "4. AMÉLIORATION : chercher la réponse à UN seul problème\n\n"
                            "Approche itérative > approche exhaustive."
                        ),
                    },
                    {
                        "type":    "prompt",
                        "title":   "Prompt pour apprendre vite",
                        "content": "Je veux apprendre à utiliser [nom de l'outil] pour [objectif précis]. Donne-moi les 5 étapes essentielles pour être opérationnel en 30 minutes.",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Choisissez un outil lié à {t} peu utilisé. Passez 15 minutes dessus et notez : qu'avez-vous réussi à faire ?",
                        "expected_user_action":  "Tester un outil et noter le résultat obtenu",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Un outil testé", "Au moins un résultat concret obtenu"],
                    },
                    {
                        "type":                  "prompt_practice",
                        "instruction":           "Utilisez le prompt ci-dessus pour obtenir un guide de démarrage rapide pour cet outil.",
                        "expected_user_action":  "Adapter le prompt et lancer",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Guide généré et consulté"],
                    },
                ],
            },
            {
                "title":     "Optimiser — aller au-delà des bases",
                "objective": "Gagner en efficacité et éviter les erreurs courantes.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Règle des 20/80 appliquée aux outils",
                        "content": (
                            "20% des fonctionnalités couvrent 80% des besoins.\n"
                            "Identifiez ces 20% pour votre usage spécifique :\n"
                            "Listez vos 5 tâches les plus fréquentes → cherchez la fonction qui les simplifie\n"
                            "→ Maîtrisez ces 5 fonctions avant tout le reste."
                        ),
                    },
                    {
                        "type":    "example",
                        "title":   "Astuces universelles",
                        "content": (
                            "• Créer des templates pour les tâches répétitives\n"
                            "• Apprendre les raccourcis clavier dès le début\n"
                            "• Tester en brouillon avant de finaliser\n"
                            "• Tenir un fichier de notes avec ses astuces préférées"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Créez votre premier template réutilisable pour une tâche liée à {t} que vous faites souvent.",
                        "expected_user_action":  "Créer et sauvegarder un template",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Template créé", "Sauvegardé et accessible"],
                    },
                    {
                        "type":                  "checklist",
                        "instruction":           "Validez l'adoption des bonnes pratiques techniques.",
                        "expected_user_action":  "Cocher les pratiques adoptées",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Au moins 3 pratiques adoptées sur 4"],
                    },
                ],
            },
            {
                "title":     "Sécurité et confidentialité",
                "objective": "Utiliser les outils de façon responsable et conforme.",
                "content_blocks": [
                    {
                        "type":    "warning",
                        "title":   "Ce que vous ne devez jamais partager",
                        "content": (
                            "❌ Données clients identifiables\n"
                            "❌ Informations confidentielles de l'entreprise\n"
                            "❌ Mots de passe ou accès\n"
                            "❌ Données financières non publiques\n\n"
                            "Règle simple : si vous ne le posteriez pas sur LinkedIn,\nne le mettez pas dans un outil cloud non validé."
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Vérifications avant d'utiliser un outil",
                        "content": (
                            "✓ L'outil respecte le RGPD\n"
                            "✓ Données non utilisées pour entraîner des modèles sans consentement\n"
                            "✓ L'entreprise autorise cet outil\n"
                            "✓ Données sensibles anonymisées avant utilisation"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Identifiez 3 types d'informations de votre activité que vous ne devez pas partager avec des outils externes.",
                        "expected_user_action":  "Lister ses données sensibles spécifiques",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["3 types identifiés", "Règle claire pour chaque type"],
                    },
                ],
            },
            {
                "title":     "Intégration dans son flux de travail",
                "objective": "Faire des outils une habitude professionnelle naturelle.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Créer une nouvelle habitude en 3 semaines",
                        "content": (
                            "Semaine 1 : utiliser l'outil sur UNE tâche précise, tous les jours\n"
                            "Semaine 2 : élargir à 2-3 tâches\n"
                            "Semaine 3 : évaluer le gain et décider\n\n"
                            "Forcez-vous à l'utiliser même quand c'est plus lent au début."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Planifiez votre intégration de {t} : quelle tâche, quel outil, quelle fréquence, pendant les 3 prochaines semaines.",
                        "expected_user_action":  "Rédiger un plan d'intégration en 3 lignes",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Plan écrit", "Première utilisation planifiée"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "practical_case",
            "instructions": f"Réalisez une vraie tâche liée à {t} avec au moins un outil. Décrivez ce que vous avez fait, le résultat obtenu et ce que vous avez appris.",
            "success_criteria": ["Tâche réalisée avec un outil", "Résultat documenté", "Un apprentissage identifié"],
        },
    }


def _tmpl_strategic(topic, _obj):
    t = topic
    return {
        "title":     f"Construire sa stratégie autour de {t}",
        "objective": f"Comprendre les enjeux stratégiques de {t} et construire un plan d'action.",
        "duration":  "55min",
        "lessons": [
            {
                "title":     "Comprendre les enjeux — où en est-on vraiment",
                "objective": f"Avoir une vision claire des enjeux de {t} et identifier sa propre position.",
                "content_blocks": [
                    {
                        "type":    "theory",
                        "title":   "Pourquoi ce sujet est stratégique aujourd'hui",
                        "content": (
                            f"{t} représente à la fois une opportunité et un risque selon la position qu'on adopte.\n"
                            "Enjeux principaux :\n"
                            "• Productivité et compétitivité\n"
                            "• Attraction et rétention des talents\n"
                            "• Conformité réglementaire\n"
                            "• Qualité et rapidité de décision"
                        ),
                    },
                    {
                        "type":    "example",
                        "title":   "Ce que font les organisations en avance",
                        "content": (
                            "Points communs des organisations qui ont de l'avance :\n"
                            "• Un champion interne qui porte le sujet\n"
                            "• Elles partent de problèmes réels, pas de la technologie\n"
                            "• Elles forment et embarquent leurs équipes\n"
                            "• Elles mesurent dès le début"
                        ),
                    },
                    {
                        "type":    "warning",
                        "title":   "Les risques à ne pas ignorer",
                        "content": (
                            f"❌ Attendre la solution parfaite\n"
                            f"❌ Partir de la technologie plutôt du problème\n"
                            f"❌ Ne pas impliquer les équipes\n"
                            f"⚠️ Le vrai risque : ne rien faire pendant que le monde change."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "self_assessment",
                        "instruction":           f"Notez votre organisation sur {t} : Connaissance (1-5), Utilisation (1-5), Stratégie (1-5), Culture (1-5).",
                        "expected_user_action":  "Auto-évaluation sur 4 dimensions",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Évaluation sur 4 dimensions réalisée"],
                    },
                    {
                        "type":                  "question",
                        "instruction":           f"Quel est le principal risque si votre organisation n'avance pas sur {t} dans les 12 prochains mois ?",
                        "expected_user_action":  "Répondre en 2-3 phrases de façon concrète",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Risque principal identifié", "Formulé de façon concrète"],
                    },
                ],
            },
            {
                "title":     "Prioriser et décider — mettre le bon focus",
                "objective": "Identifier les actions à fort impact et arbitrer sans attendre l'information parfaite.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "La matrice Effort / Impact",
                        "content": (
                            "Classez chaque action selon :\n"
                            "• Impact estimé (fort / faible)\n"
                            "• Effort nécessaire (fort / faible)\n\n"
                            "Priorité 1 : Fort impact + Faible effort → Démarrez maintenant\n"
                            "Priorité 2 : Fort impact + Fort effort → Planifiez\n"
                            "Évitez : Faible impact + Fort effort\n\n"
                            "Règle : commencez par un quick win visible."
                        ),
                    },
                    {
                        "type":    "example",
                        "title":   "Décider avec information partielle",
                        "content": (
                            "1. Identifiez ce que vous savez vs supposez\n"
                            "2. Quelle est la décision la moins risquée ?\n"
                            "3. Comment tester rapidement avant de vous engager ?\n"
                            "4. Qu'est-ce que vous coûterait de ne pas décider ?\n\n"
                            "L'indécision est une décision — souvent la plus coûteuse."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Listez 5 actions possibles pour avancer sur {t}. Classez-les avec la matrice effort/impact.",
                        "expected_user_action":  "Créer un tableau 5 actions × 2 critères",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["5 actions listées", "Classées sur effort et impact", "Action prioritaire identifiée"],
                    },
                    {
                        "type":                  "question",
                        "instruction":           "Quelle est votre action n°1 à lancer cette semaine ? Justifiez en 2 phrases.",
                        "expected_user_action":  "Identifier et justifier l'action prioritaire",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Action n°1 identifiée", "Justification claire"],
                    },
                ],
            },
            {
                "title":     "Construire un plan d'action 30/60/90 jours",
                "objective": "Transformer sa stratégie en étapes concrètes, planifiées et mesurables.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Le plan 30/60/90 jours",
                        "content": (
                            "30 JOURS — Quick wins\n"
                            "• Actions immédiates, faible risque, résultats rapides\n"
                            "• Objectif : créer de l'élan\n\n"
                            "60 JOURS — Consolidation\n"
                            "• S'appuyer sur les apprentissages du premier mois\n\n"
                            "90 JOURS — Impact\n"
                            "• Actions plus investies, basées sur les données\n\n"
                            "Règle : révisez chaque mois. Le plan est vivant."
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Un bon indicateur de succès est :",
                        "content": (
                            "✓ Mesurable (chiffre ou état clair)\n"
                            "✓ Atteignable dans le délai défini\n"
                            "✓ Lié directement à l'action\n"
                            "✓ Connu de toutes les parties prenantes\n"
                            "✓ Révisable si le contexte change"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Rédigez votre plan 30/60/90 jours pour avancer sur {t}. Minimum 1 action par horizon avec un indicateur de succès.",
                        "expected_user_action":  "Rédiger un plan structuré en 3 horizons",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["3 horizons définis", "1 action minimum par horizon", "Indicateur de succès pour chaque action"],
                    },
                    {
                        "type":                  "checklist",
                        "instruction":           "Validez que votre plan est solide en cochant chaque critère.",
                        "expected_user_action":  "Vérifier les 5 critères d'un bon indicateur",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Plan validé sur les 5 critères"],
                    },
                ],
            },
            {
                "title":     "Embarquer les parties prenantes",
                "objective": "Obtenir l'adhésion et créer une dynamique collective.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Cartographier ses alliés et ses freins",
                        "content": (
                            "Avant d'agir, identifiez :\n"
                            "• Qui sont vos alliés naturels ?\n"
                            "• Qui sont les décideurs à convaincre ?\n"
                            "• Qui pourrait résister et pourquoi ?\n\n"
                            "Stratégie : commencez par les alliés → créez des résultats visibles\n"
                            "→ embarquez les décideurs avec des preuves."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Cartographiez vos parties prenantes sur {t} : 3 alliés, 2 décideurs, 1 frein probable.",
                        "expected_user_action":  "Créer une carte simple des parties prenantes",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Carte réalisée", "Premier allié identifié pour démarrer"],
                    },
                ],
            },
            {
                "title":     "Mesurer et ajuster — boucle de feedback",
                "objective": "Mettre en place des mécanismes simples pour apprendre en continu.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Rétrospective mensuelle en 4 questions",
                        "content": (
                            "1. QU'EST-CE QUI A FONCTIONNÉ ? → maintenir et amplifier\n"
                            "2. QU'EST-CE QUI N'A PAS FONCTIONNÉ ? → corriger ou abandonner\n"
                            "3. QU'EST-CE QU'ON A APPRIS ? → capitaliser\n"
                            "4. QU'EST-CE QU'ON FAIT DIFFÉREMMENT ? → intégrer au plan\n\n"
                            "Format : 30 minutes, 1x/mois, parties prenantes clés."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Définissez votre routine de suivi de l'avancement sur {t} : fréquence, format, participants.",
                        "expected_user_action":  "Rédiger sa routine de suivi",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Routine définie et planifiée"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "practical_case",
            "instructions": f"Présentez votre plan d'action personnel sur {t} en 1 page : contexte (où j'en suis), priorités (mes 3 actions), engagement (quand je commence).",
            "success_criteria": ["Contexte documenté", "3 actions prioritaires identifiées", "Date de début définie"],
        },
    }


def _tmpl_operational(topic, _obj):
    t = topic
    return {
        "title":     f"Intégrer {t} dans son quotidien professionnel",
        "objective": f"Passer de la théorie à la pratique : utiliser {t} dans ses tâches réelles.",
        "duration":  "50min",
        "lessons": [
            {
                "title":     "Identifier ses quick wins — où commencer",
                "objective": "Trouver les 2-3 tâches où gagner immédiatement en efficacité.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Chasse aux quick wins",
                        "content": (
                            f"Un quick win {t} idéal :\n"
                            "✓ Tâche répétitive (au moins 1x/semaine)\n"
                            "✓ Prend du temps disproportionné\n"
                            "✓ Résultat mesurable\n\n"
                            "Candidats courants : rédaction d'emails, rapports récurrents,\nrecherches d'info, tri et classification."
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Détection de quick wins",
                        "content": (
                            "Parcourez votre semaine dernière :\n"
                            "☐ Plus d'1h sur une tâche répétitive ?\n"
                            "☐ Recherche d'info qui aurait pu être synthétisée ?\n"
                            "☐ Document rédigé depuis une page blanche ?\n"
                            "☐ Emails similaires envoyés plusieurs fois ?\n"
                            "☐ Temps perdu à formater ou structurer ?"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "checklist",
                        "instruction":           "Parcourez la checklist ci-dessus. Cochez les tâches candidates dans votre semaine dernière.",
                        "expected_user_action":  "Scanner sa semaine et cocher les candidats",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Au moins 1 tâche candidate identifiée"],
                    },
                    {
                        "type":                  "exercise",
                        "instruction":           f"Choisissez votre quick win n°1 : la tâche sur laquelle tester {t} dès aujourd'hui. Décrivez-la en 2 phrases.",
                        "expected_user_action":  "Choisir et décrire une tâche précise",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Quick win n°1 identifié et décrit"],
                    },
                ],
            },
            {
                "title":     "Créer ses premiers templates",
                "objective": "Construire des templates réutilisables pour ses tâches récurrentes.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Anatomie d'un bon template",
                        "content": (
                            "1. CONTEXTE : à quoi sert ce template ?\n"
                            "2. VARIABLES : quelles infos sont adaptées à chaque usage ?\n"
                            "3. STRUCTURE FIXE : les éléments qui ne changent pas\n"
                            "4. EXEMPLE : 1 résultat attendu\n\n"
                            "Formule : [contexte] + [variables] = résultat attendu"
                        ),
                    },
                    {
                        "type":    "prompt",
                        "title":   "Prompt pour créer un template",
                        "content": "Aide-moi à créer un template pour [tâche précise]. Ce template sera utilisé [fréquence] pour [objectif]. Les variables à personnaliser sont : [liste]. Le résultat doit être [format].",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "prompt_practice",
                        "instruction":           "Adaptez le prompt ci-dessus à votre quick win n°1 et générez votre premier template.",
                        "expected_user_action":  "Adapter le prompt et générer un template",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Template généré", "Testé sur un exemple réel"],
                    },
                    {
                        "type":                  "exercise",
                        "instruction":           "Sauvegardez votre template dans un endroit accessible et testez-le sur un cas réel.",
                        "expected_user_action":  "Sauvegarder et utiliser le template",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Template sauvegardé", "Testé au moins une fois"],
                    },
                ],
            },
            {
                "title":     "Mesurer et améliorer — boucle d'itération",
                "objective": "Évaluer ce qui fonctionne et affiner progressivement.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Boucle d'amélioration en 4 étapes",
                        "content": (
                            "1. FAIRE → réaliser la tâche avec la nouvelle approche\n"
                            "2. NOTER → temps passé, qualité, difficultés\n"
                            "3. COMPARER → vs votre ancienne méthode\n"
                            "4. AJUSTER → modifier ce qui ne fonctionne pas\n\n"
                            "Fréquence : bilan rapide chaque semaine (10 min)."
                        ),
                    },
                    {
                        "type":    "checklist",
                        "title":   "Indicateurs simples à suivre",
                        "content": (
                            "✓ Temps gagné par semaine (minutes)\n"
                            "✓ Qualité du résultat (mieux / pareil / moins bien)\n"
                            "✓ Difficulté ressentie (1-5)\n"
                            "✓ Taux d'utilisation de ses templates\n"
                            "✓ Satisfaction globale (envie de continuer ?)"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "self_assessment",
                        "instruction":           f"Après 1 semaine de pratique : évaluez l'impact de {t} sur votre efficacité quotidienne.",
                        "expected_user_action":  "Remplir son bilan de première semaine",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Bilan réalisé sur les 5 indicateurs"],
                    },
                    {
                        "type":                  "exercise",
                        "instruction":           "Identifiez l'ajustement n°1 pour améliorer votre pratique la semaine prochaine.",
                        "expected_user_action":  "Définir un ajustement concret",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Ajustement identifié et planifié"],
                    },
                ],
            },
            {
                "title":     "Partager et créer une dynamique d'équipe",
                "objective": "Faire bénéficier son équipe de ses apprentissages.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Le partage en 5 minutes",
                        "content": (
                            "Format :\n"
                            "1. Ce que j'ai testé\n"
                            "2. Ce que ça m'a apporté (résultat concret)\n"
                            "3. Comment faire (étapes simples)\n"
                            "4. Ce que je vous recommande d'essayer\n\n"
                            "La démonstration convainc mieux que le discours."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Préparez votre mini-retour d'expérience de 5 minutes pour votre équipe.",
                        "expected_user_action":  "Rédiger les 4 points du format de partage",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["4 points rédigés", "Résultat concret mentionné"],
                    },
                ],
            },
            {
                "title":     "Construire une routine durable",
                "objective": "Transformer l'utilisation occasionnelle en habitude professionnelle.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Ancrer une habitude en 21 jours",
                        "content": (
                            f"Jour 1-7 : utiliser {t} pour UNE tâche, tous les jours\n"
                            "Jour 8-14 : ajouter une 2e tâche\n"
                            "Jour 15-21 : évaluer et consolider\n\n"
                            "Clé : liez la nouvelle habitude à un déclencheur existant.\n"
                            "Exemple : « Quand j'ouvre mes emails, j'utilise mon template pour... »"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Rédigez votre plan d'habitude pour les 21 prochains jours avec {t} : quelle tâche, quel moment, quel outil.",
                        "expected_user_action":  "Rédiger son plan d'habitude",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Plan rédigé", "Habitude liée à un déclencheur existant"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "practical_case",
            "instructions": f"Montrez une réalisation concrète : un template créé, une tâche réalisée avec {t}, ou votre bilan de première semaine.",
            "success_criteria": ["Réalisation concrète documentée", "Résultat mesurable obtenu", "Prochaine étape définie"],
        },
    }


def _tmpl_cognitive(topic, _obj):
    t = topic
    return {
        "title":     f"Développer son esprit critique sur {t}",
        "objective": "Apprendre à questionner, analyser et prendre du recul.",
        "duration":  "40min",
        "lessons": [
            {
                "title":     "Évaluer l'information et éviter les biais",
                "objective": "Distinguer le vrai du bruit et reconnaître ses propres biais.",
                "content_blocks": [
                    {
                        "type":    "theory",
                        "title":   "Biais cognitifs les plus courants",
                        "content": (
                            "• Biais de confirmation : chercher ce qui confirme nos croyances\n"
                            "• Biais d'ancrage : rester influencé par la première information reçue\n"
                            "• Effet de halo : bonne première impression qui colore tout\n"
                            "• FOMO : peur de manquer quelque chose\n\n"
                            "La conscience de ces biais ne les élimine pas — elle permet de les compenser."
                        ),
                    },
                    {
                        "type":    "method",
                        "title":   "Vérification en 3 questions",
                        "content": (
                            "1. D'où vient cette information ? (source primaire vs secondaire)\n"
                            "2. Qui en bénéficie si je la crois ? (intérêts en jeu)\n"
                            "3. Qu'est-ce qui me permettrait de la réfuter ?"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Trouvez une affirmation récente lue sur {t} et appliquez les 3 questions de vérification.",
                        "expected_user_action":  "Analyser une affirmation avec la méthode",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["3 questions appliquées", "Conclusion formulée"],
                    },
                    {
                        "type":                  "self_assessment",
                        "instruction":           "Identifiez votre biais cognitif le plus fréquent dans ce domaine et comment le compenser.",
                        "expected_user_action":  "Nommer son biais + stratégie de compensation",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Biais identifié", "Stratégie de compensation définie"],
                    },
                ],
            },
            {
                "title":     "Structurer sa pensée pour décider",
                "objective": "Utiliser des méthodes simples pour résoudre des problèmes complexes.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Décomposer pour mieux comprendre",
                        "content": (
                            "1. Formuler le problème en 1 phrase\n"
                            "2. Lister les sous-problèmes\n"
                            "3. Identifier le sous-problème racine\n"
                            "4. Résoudre ce sous-problème en premier\n"
                            "5. Vérifier si cela résout le problème global"
                        ),
                    },
                    {
                        "type":    "prompt",
                        "title":   "Prompt utile",
                        "content": f"Aide-moi à décomposer ce problème lié à {t} : [description]. Quelles sont les causes racines possibles et par laquelle commencer ?",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Choisissez un problème réel avec {t} et décomposez-le en sous-problèmes.",
                        "expected_user_action":  "Créer un arbre de problèmes",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Problème décomposé", "Cause racine identifiée"],
                    },
                ],
            },
            {
                "title":     "Apprendre de ses expériences",
                "objective": "Transformer chaque expérience en apprentissage durable.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Rétrospective personnelle en 4 questions",
                        "content": (
                            "• Qu'est-ce qui s'est passé ? (faits)\n"
                            "• Pourquoi ? (analyse)\n"
                            "• Qu'est-ce que j'apprends ? (insight)\n"
                            "• Que ferais-je différemment ? (action)\n\n"
                            "10 minutes, une fois par semaine."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Faites une rétrospective sur votre expérience avec {t} : ce qui a bien marché, pas marché, et ce que vous faites différemment.",
                        "expected_user_action":  "Rédiger sa rétrospective en 4 points",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Rétrospective rédigée", "1 insight et 1 action identifiés"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "reflection",
            "instructions": f"Quel est, selon vous, le principal mythe ou erreur de compréhension autour de {t}, et pourquoi est-il important de le corriger ?",
            "success_criteria": ["Mythe identifié", "Argumentation structurée", "Implication pratique mentionnée"],
        },
    }


def _tmpl_collaborative(topic, _obj):
    t = topic
    return {
        "title":     f"Partager et progresser ensemble sur {t}",
        "objective": "Créer une dynamique collective d'apprentissage.",
        "duration":  "35min",
        "lessons": [
            {
                "title":     "Partager efficacement ce qu'on sait",
                "objective": "Transmettre ses connaissances de façon utile et engageante.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Format de partage en 4 étapes",
                        "content": (
                            "1. ACCROCHE : question ou fait surprenant\n"
                            "2. CONTENU : 3 points clés max\n"
                            "3. DÉMONSTRATION : exemple ou démo courte\n"
                            "4. INVITATION : « Qui veut essayer ? »\n\n"
                            "Temps idéal : 5-10 minutes."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Préparez un partage de 5 minutes sur {t} pour votre équipe en suivant le format 4 étapes.",
                        "expected_user_action":  "Rédiger le contenu du partage",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["4 étapes rédigées", "Exemple concret inclus"],
                    },
                ],
            },
            {
                "title":     "Documenter pour capitaliser",
                "objective": "Créer des ressources réutilisables par toute l'équipe.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Documentation minimale viable",
                        "content": (
                            "Une bonne documentation d'équipe :\n"
                            "• S'écrit en 15 minutes max\n"
                            "• Se lit en 5 minutes\n"
                            "• Contient : quoi faire, comment faire, pièges\n"
                            "• Est mise à jour quand les pratiques changent\n\n"
                            "Ne documentez que ce que vous utilisez."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Rédigez une fiche pratique d'1 page sur {t} pour un collègue débutant.",
                        "expected_user_action":  "Créer une fiche pratique",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Fiche rédigée en max 1 page", "Contient quoi / comment / pièges"],
                    },
                ],
            },
            {
                "title":     "Construire une culture d'apprentissage",
                "objective": "Mettre en place des rituels simples pour progresser ensemble.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Rituels simples d'équipe",
                        "content": (
                            f"• Partage de tip hebdomadaire (5 min en réunion)\n"
                            f"• Base de connaissances partagée (1 page, MAJ mensuelle)\n"
                            f"• Challenge mensuel sur {t}\n"
                            f"• Rétrospective trimestrielle"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Proposez un rituel d'équipe simple pour maintenir la dynamique d'apprentissage.",
                        "expected_user_action":  "Décrire format, fréquence, responsable",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Rituel défini", "Prêt à proposer à l'équipe"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "checklist",
            "instructions": f"Partagez réellement quelque chose que vous avez appris sur {t} avec au moins 1 collègue. Décrivez ce que vous avez partagé et la réaction obtenue.",
            "success_criteria": ["Partage réalisé", "Retour du collègue noté"],
        },
    }


def _tmpl_creative(topic, _obj):
    t = topic
    return {
        "title":     f"Explorer de nouvelles possibilités avec {t}",
        "objective": "Développer un regard créatif pour innover dans ses pratiques.",
        "duration":  "35min",
        "lessons": [
            {
                "title":     "Penser autrement — sortir des sentiers battus",
                "objective": "Générer des idées nouvelles et non conventionnelles.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Technique SCAMPER",
                        "content": (
                            f"Pour innover sur {t} :\n"
                            "S — Substituer : que pourrait-on remplacer ?\n"
                            "C — Combiner : avec quoi associer ?\n"
                            "A — Adapter : qu'est-ce qui existe ailleurs à adapter ?\n"
                            "M — Magnifier/Minimiser : plus grand ou plus petit ?\n"
                            "P — Proposer d'autres usages : à quoi d'autre ça sert ?\n"
                            "E — Éliminer : qu'est-ce qui est inutile ?\n"
                            "R — Réorganiser/Inverser : et si on faisait l'inverse ?"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Appliquez SCAMPER à {t} dans votre contexte. Générez au moins 5 idées, même les plus folles.",
                        "expected_user_action":  "Générer 5 idées avec SCAMPER",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["5 idées générées", "Au moins 1 idée vraiment originale"],
                    },
                ],
            },
            {
                "title":     "Tester rapidement à faible coût",
                "objective": "Valider une idée créative sans investissement important.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Test en 48 heures",
                        "content": (
                            "1. Reformuler l'idée en 1 phrase\n"
                            "2. Quel est le plus petit test possible ?\n"
                            "3. Comment mesurer si ça marche ?\n"
                            "4. Tester en 48 heures\n"
                            "5. Décider : continuer, pivoter ou abandonner\n\n"
                            "Si vous ne pouvez pas tester en 48h → l'idée est trop grande. Découpez-la."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Choisissez votre idée préférée et concevez un test en 48 heures.",
                        "expected_user_action":  "Décrire le test minimal viable",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Test défini", "Réalisable en 48h", "Indicateur de succès clair"],
                    },
                ],
            },
            {
                "title":     "Cultiver un mindset d'amélioration continue",
                "objective": "Développer l'habitude de questionner et d'améliorer.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "La question des 10%",
                        "content": (
                            f"Posez-vous régulièrement : « Comment améliorer cela de 10% ? »\n"
                            "Pas 100% (trop ambitieux), pas 1% (trop petit).\n"
                            "10% : atteignable, impactant, créateur d'élan.\n\n"
                            "Appliquez-le à vos processus, outils, habitudes de travail."
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Identifiez 3 aspects de votre utilisation de {t} à améliorer de 10% chacun.",
                        "expected_user_action":  "Lister 3 améliorations de 10%",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["3 améliorations identifiées", "Chacune réaliste et actionnable"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "practical_case",
            "instructions": f"Testez réellement une idée créative liée à {t} pendant 48 heures et documentez le résultat.",
            "success_criteria": ["Test réalisé", "Résultat documenté", "Décision prise (continuer/pivoter/abandonner)"],
        },
    }


def _tmpl_generic(topic, _obj):
    t = topic
    return {
        "title":     f"{t} — fondamentaux",
        "objective": f"Acquérir les bases pour progresser sur {t}.",
        "duration":  "40min",
        "lessons": [
            {
                "title":     "Introduction et fondamentaux",
                "objective": f"Comprendre les bases essentielles de {t}.",
                "content_blocks": [
                    {
                        "type":    "theory",
                        "title":   f"Qu'est-ce que {t} ?",
                        "content": f"Introduction aux concepts fondamentaux de {t}. Ce module couvre les éléments essentiels pour démarrer de façon concrète et progressive.",
                    },
                    {
                        "type":    "example",
                        "title":   "Application pratique",
                        "content": f"Exemple d'application de {t} dans un contexte professionnel courant.",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "self_assessment",
                        "instruction":           f"Évaluez votre niveau de connaissance actuel sur {t} (1 = débutant, 5 = expert).",
                        "expected_user_action":  "Se noter de 1 à 5",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Point de départ évalué"],
                    },
                ],
            },
            {
                "title":     "Mise en pratique",
                "objective": "Appliquer les fondamentaux à un cas concret.",
                "content_blocks": [
                    {
                        "type":    "method",
                        "title":   "Comment procéder",
                        "content": f"Méthode step-by-step pour appliquer {t} efficacement dans votre contexte.",
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           f"Réalisez un exercice pratique sur {t} en appliquant la méthode décrite.",
                        "expected_user_action":  "Réaliser l'exercice et noter le résultat",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Exercice réalisé", "Résultat noté"],
                    },
                ],
            },
            {
                "title":     "Consolidation et prochaines étapes",
                "objective": "Consolider les acquis et définir la suite.",
                "content_blocks": [
                    {
                        "type":    "checklist",
                        "title":   "Ce que vous devez maintenant savoir faire",
                        "content": (
                            f"✓ Comprendre les fondamentaux de {t}\n"
                            "✓ L'appliquer dans un cas simple\n"
                            "✓ Identifier les prochaines étapes"
                        ),
                    },
                ],
                "interactive_tasks": [
                    {
                        "type":                  "exercise",
                        "instruction":           "Identifiez votre prochaine action pour progresser sur ce sujet.",
                        "expected_user_action":  "Définir une action concrète pour la semaine prochaine",
                        "validation_mode":       "self_check",
                        "success_criteria":      ["Action identifiée et planifiée"],
                    },
                ],
            },
        ],
        "validation": {
            "type":         "reflection",
            "instructions": f"En 5-10 phrases, décrivez ce que vous avez appris et comment vous allez l'utiliser.",
            "success_criteria": ["Bilan rédigé", "Application concrète mentionnée"],
        },
    }


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    r = run({
        "topic":      "Utiliser l'IA dans son travail quotidien",
        "level":      "beginner",
        "objectives": [
            "Comprendre ce qu'est l'IA et ce qu'elle peut faire concrètement",
            "Rédiger des prompts efficaces",
        ],
        "logics":  ["editorial", "technical", "operational"],
        "format":  "standard",
        "catalog": None,
    })
    t  = r.get("training", {})
    p  = t.get("progression", {})
    print(f"status : {r['status']}  mode : {r['meta']['mode']}")
    print(f"titre  : {t.get('training_title')}")
    print(f"durée  : {t.get('estimated_duration')}")
    print(f"{p.get('total_chapters')} chapitres / {p.get('total_lessons')} leçons / {p.get('total_tasks')} tâches")
    for ch in t.get("chapters", []):
        n_t = sum(len(ls["interactive_tasks"]) for ls in ch["lessons"])
        print(f"  [{ch['order']}] {ch['title'][:60]} — {len(ch['lessons'])} leçons / {n_t} tâches")
