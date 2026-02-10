# AUTO FUNCTION BUILDER

Système automatisé de génération de fonctions Python avec tests, validation et correction IA.

## Vue d'ensemble

AUTO FUNCTION BUILDER est un système complet qui génère automatiquement :
- Des fonctions Python conformes aux conventions EUREKAI
- Des tests unitaires complets (pytest)
- Des rapports de validation
- Des métadonnées structurées
- De la documentation

Le système utilise l'IA (GPT-4 ou Claude) pour l'analyse, la génération de code et la correction automatique.

## Architecture

Le système suit une architecture GEVR (Get-Execute-Validate-Render) :

```
GET → EXECUTE → [FIX] → VALIDATE → RENDER
```

### Phase GET
Collecte et préparation de tous les paramètres nécessaires :
- Normalisation du brief utilisateur
- Détermination du nom de fonction
- Sélection du langage
- Chargement des contraintes
- Chargement du contexte de code
- Résolution des chemins

### Phase EXECUTE
Génération du code et des tests :
- Analyse du brief (IA)
- Construction du squelette
- Génération du code (IA)
- Écriture de la fonction
- Génération des tests (IA)
- Écriture des tests
- Exécution des tests

### Boucle FIX (optionnelle)
Si les tests échouent, correction automatique (max 3 tentatives) :
- Extraction des erreurs
- Génération de correction (IA)
- Réécriture du code
- Relance des tests
- Validation du succès

### Phase VALIDATE
Validation globale :
- Cohérence spec/code
- Respect des conventions
- Tests complets et passants
- Métadonnées complètes

### Phase RENDER
Production des artefacts finaux :
- Rapport de validation (Markdown)
- Index des outputs
- Logs finaux

## Installation

### Prérequis

```bash
Python >= 3.11
```

### Dépendances

```bash
pip install pytest openai anthropic
```

Ou avec le fichier requirements.txt :

```bash
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` avec vos clés API :

```
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4
OPENAI_API_KEY=votre_clé_ici

# ou pour Anthropic
DEFAULT_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=votre_clé_ici
```

## Utilisation

### Utilisation basique

```python
from auto_function_builder_get import auto_function_builder_get
from auto_function_builder_execute import auto_function_builder_execute
from auto_function_builder_fix import auto_function_builder_fix
from auto_function_builder_validate import auto_function_builder_validate
from auto_function_builder_render import auto_function_builder_render
from auto_function_builder_finalize import auto_function_builder_finalize

# 1. Initialiser le builder_state
builder_state = {
    "project": {
        "name": "mon_projet",
        "root": "/chemin/vers/projet"
    },
    "function_request": {
        "brief_raw": """
        Je veux une fonction qui lit un fichier texte et compte 
        le nombre de lignes non vides.
        """
    }
}

# 2. Exécuter le pipeline complet
builder_state = auto_function_builder_get(builder_state)
builder_state = auto_function_builder_execute(builder_state)

# 3. Si tests échoués, tenter la correction
if builder_state["tests"]["status"] == "failed":
    builder_state = auto_function_builder_fix(builder_state)

# 4. Finaliser et valider
builder_state = auto_function_builder_finalize(builder_state)
builder_state = auto_function_builder_validate(builder_state)

# 5. Générer les outputs
builder_state = auto_function_builder_render(builder_state)

# 6. Résultat
print(f"Statut: {builder_state['validation']['global_status']}")
print(f"Fichiers générés: {len(builder_state['outputs_index'])}")
```

### Exemple avec script complet

Voir `example_usage.py` pour un exemple complet.

## Structure des fichiers

```
AUTO_FUNCTION_BUILDER/
├── report_actions.py              # Système de logging
├── call_llm.py                    # Interface IA générique
├── auto_function_builder_*.py     # Modules principaux
├── _OUTPUTS/                      # Sorties générées
│   ├── FUNCTIONS/                 # Fonctions générées
│   ├── TESTS/                     # Tests générés
│   ├── REPORTS/                   # Rapports de validation
│   ├── LOGS/                      # Logs JSON
│   └── METADATA/                  # Métadonnées JSON
└── README.md
```

## Conventions EUREKAI

Le code généré respecte strictement les conventions EUREKAI :

### Fonctions
- Une fonction par fichier
- Docstring Google-style obligatoire
- Pas de `print()`, utiliser `report_actions()`
- Nommage snake_case
- Imports propres et organisés

### Tests
- Framework pytest
- Minimum 3 cas de test
- Cas nominal, erreur, et limite obligatoires
- Noms explicites : `test_<fonction>_<scenario>`

### Métadonnées
Chaque fonction générée inclut :
- name, description, version
- author, dates (created_at, updated_at)
- language, object_type, module
- tags, dependencies, scenarios
- inputs_schema, outputs_schema

## Format builder_state

Le `builder_state` est l'objet central qui transporte l'état complet :

```json
{
  "project": {...},
  "function_request": {...},
  "constraints": {...},
  "paths": {...},
  "code_context": {...},
  "function_spec": {...},
  "artifacts": {...},
  "tests": {...},
  "fix": {...},
  "validation": {...},
  "outputs_index": [...]
}
```

Voir `ARCHITECTURE.md` pour les détails complets.

## Templates de prompts IA

Les prompts IA utilisés sont disponibles dans `PROMPTS_TEMPLATES.md`.

Ils suivent tous la même structure :
- RÔLE : rôle spécifique de l'IA
- OBJECTIF : tâche précise
- CONTEXTE PROJET : informations du projet
- CONTRAINTES : règles à respecter
- FORMAT DE RÉPONSE : JSON structuré

## Tests

Pour exécuter les tests du système lui-même :

```bash
pytest tests/
```

## Limitations connues

1. **Langage** : Supporte uniquement Python pour le moment
2. **Providers IA** : OpenAI et Anthropic uniquement
3. **Boucle FIX** : Maximum 3 tentatives de correction
4. **Complexité** : Fonctions simples à moyennes (pas de classes complexes)

## Évolutions futures

- [ ] Support de plus de langages (JavaScript, TypeScript)
- [ ] Génération de classes complètes
- [ ] Intégration avec plus de providers IA
- [ ] Interface CLI dédiée
- [ ] Interface web
- [ ] Génération de documentation complète (Sphinx, etc.)

## Contribution

Ce système fait partie du projet EUREKAI / laNostr'AI.

## Licence

Propriétaire - laNostr'AI / EUREKAI

## Support

Pour toute question ou problème :
- Consulter `ARCHITECTURE.md` pour les détails techniques
- Consulter `EXAMPLES.md` pour plus d'exemples
- Vérifier les logs dans `_OUTPUTS/LOGS/`

---

**Généré automatiquement par AUTO FUNCTION BUILDER v1.0.0**
