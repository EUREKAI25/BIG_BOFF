# Eurkai — Layer 0 — Conventions fondatrices (v1)

> Objectif : figer les conventions *définitives* de nommage et de structuration pour éviter toute confusion entre GEV / ERK / Formulas / Rules, et servir de base unique à la documentation exhaustive.

## 1. Identité

### 1.1 Objet (lineage)
- Séparateur de lineage : `:`
- Séparateur de membre/attribut : `.`
- Un objet est adressé par son lineage, ex : `Object:Scenario:MaintenanceScenario`

### 1.2 Instance (standard)
- Forme : `<Object>@<ObjectInstanceSlug>`
- Exemple : `Task@rule_list_qualify`, `Class@User`, `Method@User_create`

> `@` est réservé aux **instances** (et uniquement aux instances).

### 1.3 Tag
- Forme : `<Tag>#<Object>`
- Exemple : `Category#Object:Scenario:MaintenanceScenario`, `Maintenance#Task@...`

> `#` est réservé aux **tags**.

### 1.4 Alias
- Forme : `<Alias>&<Object>`
- Exemple : `MaintenanceValidate&Scenario@MaintenanceScenario`

> `&` est réservé aux **alias** (noms alternatifs non ambigus).

## 2. Labels (L)
- Les valeurs “en dur” vivent dans `*.l.gev` (labels).
- Un label a toujours :
  - un `slug` (auto)
  - un `scalar_type` (ex : `str`, `int`, `bool`, `dict`, etc.)
- Un schéma ne “met pas un label en valeur directe” : il référence une **méthode** / un **vecteur** qui retourne le label.

## 3. Paramètres et listes (structure canonique)
### 3.1 Listes “fondamentales”
Chaque objet expose (au minimum, même vides) :
- `attribute_list`
- `rule_list`
- `method_list`
- `option_list`
- `tree_list`

`tree_list` contient :
- `parent_list`
- `child_list`
- `sibling_list`

### 3.2 Sourcing / override (règle globale)
Priorité d’override :
- inherited < injected < owned

- `owned_*` : défini sur l’objet actif
- `inherited_*` : venant de `parent_list` (chaîne calculée)
- `injected_*` : injecté depuis les paramètres (un objet peut être paramètre d’un autre)

> Pas d’héritage “de classes” requis : la généalogie s’exprime via `tree_list` + `IN`.

## 4. Mode d’objet
Tout objet expose :
- `mode` ∈ {active, passive, reactive}

## 5. Storage
- Le stockage est **contextuel** (catalog / db / directory…).
- Résolution recommandée : `LayerStorageMapping` (un seul point de décision).
- La source de vérité peut rester catalog-first ; le mapping sert aux déploiements et aux contextes d’exécution.

## 6. Objets auto / triggers
Tout objet expose :
- `auto.bool`

Règle :
- si `auto.bool == true` alors `trigger_list` est requis (>= 1 élément).

## 7. Éditabilité et veille
Tout objet expose :
- `edit.bool`
- `watch.bool`
- `watch_rythm` (résolu par méthode / vecteur)

## 8. Organisation “schema → scenario/vector → label”
Modèle final (modularité maximale, catalogues compacts) :
- `Schema.object.parameter = ScenarioVector`
- `ScenarioVector -> LabelVector -> Label`

Les vecteurs peuvent être introduits progressivement (sans bloquer le runtime).
