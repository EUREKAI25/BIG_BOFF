# _SUIVI — Module `scan_and_do`

> Module EURKAI — MVP de la Méthode Récursive Globale (MRG)
> Créé le : 2026-03-16

---

## État actuel

**Version :** 0.1.0
**Statut :** 🟢 Stable — MVP complet, 7/7 tests ✅
**Package :** `eurkai-scan-and-do` (installable via pip)

---

## Ce que fait le module (périmètre actuel)

### Point d'entrée

```python
from scan_and_do import scan_and_do, Scenario

class MyScenario(Scenario):
    def execute(self, key: str, obj: dict) -> None:
        ...  # logique métier ici

scan_and_do(objects_dict, MyScenario())
```

### Principe

`scan_and_do(objects_dict, scenario)` ≡ `mrg(what, how)`

Pour chaque entrée du dictionnaire :
1. Récupérer l'objet courant
2. Passer à `scenario.execute(key, obj)`
3. Laisser le scénario décider

**Le moteur n'agrège rien, ne valide rien, n'interprète rien.**

### Règles invariantes

- Ne jamais valider le contenu des objets
- Ne jamais agréger les résultats
- Ne jamais interpréter la structure des objets
- Toute logique métier appartient au scénario

### Nature : `iso`

Le module ne produit pas, ne réduit pas — il exécute. Les outputs sont gérés en interne par le scénario.

---

## Architecture

```
scan_and_do/
├── scan_and_do/
│   ├── __init__.py      # export scan_and_do, Scenario
│   ├── engine.py        # scan_and_do() + Scenario(ABC)
│   ├── catalog.py       # métadonnées CATALOG
│   └── stub.py          # PrintScenario — exemple minimal
├── tests/
│   └── test_scan_and_do.py   # 7 tests
├── pyproject.toml
├── MANIFEST.json
└── _SUIVI.md
```

**Dépendances :** aucune (stdlib uniquement)

---

## Évolution future (hors MVP)

```python
# v1 : hooks before/after
before_hook.execute(key, obj)
scenario.execute(key, obj)
after_hook.execute(key, obj)
```

Interface `execute(key, obj)` : **inchangée** — rétrocompat garantie.

---

## Consommateurs prévus

| Projet | Usage |
|---|---|
| CLAUDE/TODO/project_create | Runner d'agents sur liste de projets |
| MODULES/design_exploration_engine | Itération sur directions de design |
| Tout pipeline EURKAI | Itération générique sur objets |

---

## Historique

| Date | Action |
|---|---|
| 2026-03-16 | Création module MVP complet : engine.py, catalog.py, __init__.py, stub.py, tests, pyproject.toml, MANIFEST.json |
| 2026-03-16 | 7/7 tests ✅ |
