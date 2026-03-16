# EURKAI — Object Contract (MVP)

> Complément de _ARCHITECTURE_MVP.md
> Date : 2026-03-16

---

## Principe

Tout objet EURKAI peut porter quatre blocs optionnels en plus de sa structure `definition / rules / options` :

```
object_type {
    definition
    rules
    options

    completion       // quand l'objet est "fini"
    defaults         // valeurs si champ absent
    stubs            // version minimale exécutable
    tests            // tests générables automatiquement
}
```

Ces blocs sont optionnels pour l'instant mais constituent le contrat cible pour tout objet testé ou généré automatiquement.

---

## 1. completion

Définit quand un objet est complet — pour arrêter une conversation, une récursion, ou valider un livrable.

```python
completion = {
    "required_fields": ["summary", "goal", "problem"],
    "stop_condition": "required_fields_filled"
}
```

- Évalué sur l'objet courant uniquement
- `stop_condition` MVP = `"required_fields_filled"` (tous les champs requis non vides)
- Extensible plus tard (ex : `"at_least_one_of"`, validation croisée)

---

## 2. defaults

Valeurs de remplacement si un champ est absent. Simples et prévisibles.

```python
defaults = {
    "user_name": "Utilisateur",
    "language": "fr",
    "status": "draft"
}
```

- Valeurs scalaires uniquement pour le MVP
- Appliqués à l'instanciation si le champ est `None` ou absent
- Ne remplacent pas une valeur existante

---

## 3. stubs

Version minimale exécutable d'un objet — pour prototypage, tests, exécution sans données réelles.

```python
stubs = {
    "user_name": lambda obj: obj.get("user_name") or "Dupont",
    "summary":   lambda obj: f"Stub summary for {obj.get('project', 'unknown')}",
    "features":  lambda obj: ["feature_stub_1", "feature_stub_2"]
}
```

- Un stub = une fonction `(obj) → valeur`
- Si le champ existe → on le garde ; sinon → on applique le stub
- Différence avec defaults : le stub peut calculer à partir de l'objet

---

## 4. tests

Bloc minimal pour générer des tests automatiques.

```python
tests = [
    {
        "name": "test_completion",
        "input": {"summary": "x", "goal": "y", "problem": "z"},
        "expected": {"is_complete": True}
    },
    {
        "name": "test_stub_fallback",
        "input": {},
        "expected": {"user_name": "Dupont"}
    }
]
```

- Chaque test : `name`, `input`, `expected`
- Génération automatique possible depuis `completion` + `stubs` + `defaults`
- Format compatible pytest sans dépendance supplémentaire

---

## 5. Génération automatique (module à venir)

Un module `object_generator` pourra, à partir du contrat d'un objet :

| Source | Ce qu'il génère |
|---|---|
| `completion.required_fields` | test "champ manquant → is_complete = False" |
| `defaults` | test "valeur absente → valeur par défaut appliquée" |
| `stubs` | instance minimale pour tout test qui en a besoin |
| `tests[]` | cas pytest directs |

Pour le MVP, ce module n'est pas encore créé — les blocs `completion / defaults / stubs / tests` sont définis dans chaque objet et utilisés manuellement.

---

## Exemple complet — Brief

```python
Brief = {
    "definition": "Cadrage du problème et des objectifs",
    "rules":      "Tous les champs required_fields doivent être renseignés",
    "options":    {},

    "completion": {
        "required_fields": [
            "summary", "problem", "goal",
            "user_goal", "validation_criteria",
            "target_users", "value_proposition"
        ],
        "stop_condition": "required_fields_filled"
    },

    "defaults": {
        "language": "fr",
        "status":   "draft"
    },

    "stubs": {
        "summary":           lambda o: "Stub — projet sans nom",
        "problem":           lambda o: "Stub — problème non défini",
        "goal":              lambda o: "Stub — objectif non défini",
        "user_goal":         lambda o: "Stub — objectif utilisateur non défini",
        "validation_criteria": lambda o: "Stub — critères non définis",
        "target_users":      lambda o: "Stub — utilisateurs non définis",
        "value_proposition": lambda o: "Stub — proposition de valeur non définie"
    },

    "tests": [
        {
            "name": "brief_complete",
            "input": {
                "summary": "x", "problem": "y", "goal": "z",
                "user_goal": "a", "validation_criteria": "b",
                "target_users": "c", "value_proposition": "d"
            },
            "expected": {"is_complete": True}
        },
        {
            "name": "brief_incomplete_missing_goal",
            "input": {"summary": "x", "problem": "y"},
            "expected": {"is_complete": False}
        }
    ]
}
```

---

## Règle de catalogage

```json
{
  "type": "util"
}
```

Le module `object_generator` (futur) sera catalogué `type = util`, pas `type = module`.
