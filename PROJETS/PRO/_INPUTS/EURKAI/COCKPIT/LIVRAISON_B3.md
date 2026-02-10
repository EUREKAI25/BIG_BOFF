# LIVRAISON B3/3 — ERK → Actions système

## Résumé

Cette livraison implémente l'étape B3/3 de l'interpréteur ERK: les **actions système proposées** (modifications contrôlées).

## Ce qui a été livré

### 1. Nouveaux fichiers

| Fichier | Description |
|---------|-------------|
| `erk/actions.py` | Module complet des actions (types, structures, validation) |
| `erk/tests/test_erk_b3.py` | 48 tests couvrant tous les cas B3 |
| `erk/README_B3.md` | Documentation complète B3 |

### 2. Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `erk/lexer.py` | Token `SUGGEST` ajouté |
| `erk/ast_nodes.py` | Nœuds `SuggestNode`, `SuggestBlockNode` |
| `erk/parser.py` | Parsing de `SUGGEST function(target, args...)` |
| `erk/evaluator.py` | Collecte d'actions, `evaluate_with_actions()` |
| `erk/console.py` | Méthodes `apply()`, `apply_all()` |
| `erk/__init__.py` | Exports B3, version 3.0.0 |

## Syntaxe SUGGEST

```erk
# Syntaxe de base
SUGGEST function(target, params...)

# Exemples
SUGGEST addTag(this, "core")
SUGGEST mark(this, "toReview")
SUGGEST enableMethod(this, "prompt")
SUGGEST setAttribute(this, "status", "active")

# Dans des conditions
IF NOT this.tags.contains("core") THEN SUGGEST addTag(this, "core")
WHEN ctx.mode == "strict" THEN SUGGEST enableMethod(this, "validate")
```

## Format de sortie standard

```json
{
  "type": "add_tag",
  "target": "Object:Agent:Core",
  "params": { "tag": "core" },
  "reason": "rule: ensure_core_tag"
}
```

## API principale

```python
# Via la façade ERK
result = ERK.quick_eval_with_actions(rule_text, context)
# result["suggested_actions"] contient les actions

# Via la console
result = console.apply("object_id", "rule_name")
# result["actions"] contient les actions proposées

# Via le module directement
from erk import evaluate_with_actions, parse
ast = parse(rule_text)
result = evaluate_with_actions(ast, context, "rule_name")
# result.suggested_actions est une liste de SuggestedAction
```

## Types d'actions supportés

- **Tags**: `addTag`, `removeTag`
- **Marquage**: `mark`, `unmark`, `setFlag`, `clearFlag`
- **Méthodes**: `enableMethod`, `disableMethod`
- **Attributs**: `setAttribute`, `increment`, `decrement`
- **Lifecycle**: `activate`, `deactivate`, `archive`
- **Notification**: `notify`, `log`

## Contraintes respectées

| Contrainte | Statut |
|------------|--------|
| Aucune action appliquée automatiquement | ✅ |
| Actions idempotentes | ✅ |
| Actions bien ciblées (référence claire) | ✅ |
| Actions tracées (règle d'origine) | ✅ |
| Erreurs d'actions n'interrompent pas l'évaluation | ✅ |

## Tests

```bash
# Tests B3 uniquement (48 tests)
pytest erk/tests/test_erk_b3.py -v

# Tous les tests (B1 + B2 + B3)
pytest erk/tests/ -v
# Résultat: 89 tests passés
```

### Couverture des tests B3

- Rétrocompatibilité B1/B2 (4 tests)
- Lexer SUGGEST (2 tests)
- Parser SUGGEST (7 tests)
- Évaluation/Collecte (7 tests)
- Types d'actions (7 tests)
- Validation actions (4 tests)
- Console B3 (5 tests)
- Façade ERK B3 (1 test)
- Cas limites (5 tests)
- Format de sortie (2 tests)
- Exemples documentés (3 tests)
- Intégration complète (1 test)

## Flux d'exécution

```
User/Agent
    │
    ▼
ERK.apply(objectId, ruleName)
    │
    ▼
┌─────────────────────────────────┐
│  Évaluation + Collecte Actions  │
│  (aucune modification du store) │
└─────────────────────────────────┘
    │
    ▼
ActionResult {
    status: "ok",
    actions: [...],
    log: "..."
}
    │
    ▼
UI / Orchestrator
    │
    ▼
Décision d'appliquer ou non
```

## Checklist de validation

- [x] Les règles peuvent générer des **actions proposées** sous forme structurée
- [x] Aucune action n'est appliquée automatiquement à la fractale
- [x] Les actions proposées incluent: type, cible, paramètres, règle d'origine
- [x] L'évaluation ERK reste robuste même avec règles invalides
- [x] Exemples complets de règles + actions + cas de test
- [x] Rétrocompatibilité B1/1 et B2/2 maintenue

## Version

**ERK Interpreter v3.0.0** — B3/3 Actions système (modifications contrôlées)
