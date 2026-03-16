"""
scan_and_do.catalog
────────────────────
Métadonnées du module compatibles avec le catalogue d'objets EURKAI.
"""

CATALOG = {
    # ── Identification ────────────────────────────────────────────────────────
    "name":        "scan_and_do",
    "path":        "EURKAI/MODULES/scan_and_do",
    "description": (
        "Moteur d'exécution générique (MVP de la MRG). "
        "Itère sur un dictionnaire d'objets et délègue chaque entrée à un scénario. "
        "Agnostique — aucune logique métier."
    ),
    "examples": [
        "Exécuter un scénario de génération sur une liste d'URLs",
        "Appliquer un traitement sur une collection de modules",
        "Lancer un pipeline sur un ensemble d'entités",
    ],

    # ── Mission & règles ──────────────────────────────────────────────────────
    "mission": "Fournir le mécanisme d'itération universel du système",
    "goal":    "Séparer l'itération (scan_and_do) de la logique métier (scenario)",
    "rules": [
        "Ne jamais valider le contenu des objets",
        "Ne jamais agréger les résultats",
        "Ne jamais interpréter la structure des objets",
        "Toute logique métier appartient au scénario",
    ],

    # ── Interfaces ────────────────────────────────────────────────────────────
    "inputs": {
        "objects_dict": "dict — clés arbitraires, valeurs = objets quelconques",
        "scenario":     "Scenario — instance implémentant execute(key, obj)",
    },
    "outputs": "None — les outputs sont gérés en interne par le scénario",
    "options": {
        "hooks": "before_hook / after_hook (hors MVP — évolution future)",
    },

    # ── Classification ────────────────────────────────────────────────────────
    "method_of":          "system",
    "target_object_type": "scenario",
    "nature":             "iso",   # ne produit pas, ne réduit pas — exécute

    # ── Tags ─────────────────────────────────────────────────────────────────
    "tags": ["mrg", "execution", "iteration", "generic", "core", "system"],

    # ── Statut ────────────────────────────────────────────────────────────────
    "status": "stable",
    "status_options": ["draft", "stable", "deprecated"],

    # ── Stub ─────────────────────────────────────────────────────────────────
    "stub": {
        "description": "Scénario minimal qui affiche chaque objet",
        "input": {
            "objects_dict": {"a": {"x": 1}, "b": {"x": 2}},
            "scenario":     "PrintScenario (voir stub.py)",
        },
        "expected_behavior": "Affiche 'a: {x: 1}' puis 'b: {x: 2}'",
    },

    # ── Version ───────────────────────────────────────────────────────────────
    "v0": {
        "scope":    "Itération simple, un seul niveau, pas de récursion",
        "excluded": ["hooks", "récursion", "agrégation", "validation"],
        "next":     "Ajout before_hook / after_hook sans modifier l'interface",
    },
}
