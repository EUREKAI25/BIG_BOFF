# ================================================================
# ERK — EUREKAI Rule Kernel
# Documentation du langage v2
# ================================================================

## Vue d'ensemble

ERK est le langage déclaratif d'EUREKAI pour définir des objets,
leurs attributs, relations, méthodes et règles dans une architecture
fractale où **tout est objet**.

---

## 1. Principes fondamentaux

### 1.1 Tout est objet
Chaque élément du système est un objet avec un **lineage** unique.
Variables, fonctions, configurations — tout est objet ou alias d'objet.

### 1.2 Héritage par lineage
Le lineage encode la hiérarchie : `Parent:Enfant:PetitEnfant`

### 1.3 Trois relations canoniques
| Relation | Signification |
|----------|---------------|
| `inherits_from` | Héritage structurel (implicite via lineage) |
| `depends_on` | Dépendance fonctionnelle |
| `related_to` | Association sémantique |

### 1.4 Racine unique
Tous les objets descendent de `Object`

### 1.5 MRG — Machine Récursive Générique
Toute exécution passe par la MRG. Les méthodes sont :
- **Centrales** : CRUDOE (Create, Read, Update, Delete, Orchestrate, Engage)
- **Secondaires** : rattachées à une méthode centrale

---

## 2. Syntaxe de base

### 2.1 Déclaration d'objet

```erk
Object:Parent:Enfant:
```

Le `:` final indique une déclaration. Les ancêtres sont créés si nécessaires.

**Règles de nommage :**
- Commence par une majuscule
- Alphanumérique + underscore : `[A-Z][A-Za-z0-9_]*`
- Segments séparés par `:`

### 2.2 Attributs

**Dans AttributeList :**
```erk
temperature IN Agent:AttributeList
  .type = number
  .default = 0.7
```

**Syntaxe courte :**
```erk
Agent.temperature = 0.7
# Équivalent à : temperature IN Agent:AttributeList, temperature.value = 0.7
```

**Types supportés :**
- `str` / `string` — chaîne (défaut)
- `int` — entier
- `number` — nombre décimal
- `bool` — booléen
- `date` — date/datetime
- `json` — objet JSON
- `lineage` — référence à un objet

### 2.3 Méthodes

```erk
CreateFrom IN Agent:MethodList
  .parent = Create
  .params = [source]
```

**Syntaxe courte :**
```erk
Agent.method:CreateFrom
# Équivalent à : CreateFrom IN Agent:MethodList
```

### 2.4 Règles

```erk
NotEmpty IN Agent:RuleList
  .type = validation
  .condition = value != ""
  .message = "Ne peut pas être vide"
```

**Syntaxe courte :**
```erk
Agent.rule:NotEmpty
```

### 2.5 Relations

```erk
Agent depends_on Role
Agent related_to Context
```

---

## 3. Alias et raccourcis

### 3.1 Alias de relations

| Alias | Canonique | Contexte |
|-------|-----------|----------|
| `IN` | `related_to` | + appartenance à dataset |
| `tag_of` | `related_to` | + ancêtre Tag |
| `type_of` | `inherits_from` | héritage explicite |
| `scope_of` | `related_to` | contexte/périmètre |

### 3.2 Notation ancêtres/descendants

| Notation | Signification |
|----------|---------------|
| `:Tag` | Est descendant de Tag (a Tag comme ancêtre) |
| `Tag:` | Est ancêtre de Tag |
| `.Tag` | A Tag comme attribut |
| `Tag.` | Est attribut de Tag |

### 3.3 Raccourcis bundle

```erk
X.attr      → attr IN X:AttributeList
X.method    → method IN X:MethodList
X.rule      → rule IN X:RuleList
X.relation  → relation IN X:RelationList
```

---

## 4. Structures de données

### 4.1 Dataset

Tout conteneur est un **dataset**. Deux formes :

**List** (clés numériques incrémentées) :
```erk
TabList:
  [0]: Explorer
  [1]: Créer
  [2]: Console
```

**Dict** (clés quelconques) :
```erk
Config:
  [apiKey]: "xxx"
  [maxTokens]: 4096
```

### 4.2 Opérateur IN

```erk
X IN Y
```

- Si Y est List → cherche dans values
- Si Y est Dict → cherche dans keys ET values
- Précision possible : `X IN Y.keys` ou `X IN Y.values`

### 4.3 Scope (contrainte de types)

```erk
TabList.scope = [Page, Category, Tag, Module]
```

Seuls les objets de ces types peuvent être IN TabList.

---

## 5. Contextes d'interprétation

### 5.1 Les trois contextes

| Contexte | Préfixe | Résultat |
|----------|---------|----------|
| ASSERTION | (aucun) | bool (validation) |
| ACTION | `DO` | Create/Update |
| CONDITION | `IF` | bool pour branching |

### 5.2 Exemples

```erk
# ASSERTION — retourne bool
Agent.temperature > 0

# ACTION — exécute Create/Update
DO Agent.temperature = 0.8

# CONDITION — branchement
IF Agent.temperature > 1 THEN Agent.status = "hot"
```

### 5.3 Hooks

```erk
IF ACTION           → hookAfter (si succès)
IF NOT ACTION       → hookFailure (si échec)
BEFORE ACTION       → hookBefore
```

**Exemple :**
```erk
BEFORE DO Agent.save THEN Agent.validate
IF DO Agent.save THEN Log.success
IF NOT DO Agent.save THEN Log.error
```

---

## 6. Opérateurs temporels

### 6.1 WHEN — Watcher polymorphe

Le comportement de WHEN dépend du contexte :

| Contexte | Comportement |
|----------|--------------|
| + LoopBehavior | While (boucle continue) |
| + Task | Veille (attente event) |
| + Trigger/Date | Planner (cron) |

**Exemples :**
```erk
# While — boucle tant que vrai
WHEN Queue.hasItems DO Queue.process
  .behavior = LoopBehavior

# Veille — attend l'événement
WHEN User.login DO Session.create
  .behavior = WatchBehavior

# Cron — planifié
WHEN "0 8 * * *" DO Report.generate
  .behavior = CronBehavior
```

### 6.2 UNTIL

```erk
DO Process.run UNTIL Process.complete
```

Exécute jusqu'à ce que la condition soit vraie.

---

## 7. Opérateurs logiques et arithmétiques

### 7.1 Logiques

| Opérateur | Signification |
|-----------|---------------|
| `AND` | Et logique |
| `OR` | Ou logique |
| `NOT` | Négation |
| `XOR` | Ou exclusif |

```erk
IF User.isAdmin AND User.isActive THEN Access.grant
IF NOT Error.exists OR Force.override THEN Process.continue
```

### 7.2 Comparaison

| Opérateur | Signification |
|-----------|---------------|
| `=` | Égal |
| `!=` | Différent |
| `<` | Inférieur |
| `>` | Supérieur |
| `<=` | Inférieur ou égal |
| `>=` | Supérieur ou égal |

### 7.3 Arithmétiques

| Opérateur | Signification |
|-----------|---------------|
| `+` | Addition |
| `-` | Soustraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Modulo |
| `^` | Puissance |

```erk
Total.value = Price.value * Quantity.value
Discount.percent = 100 - (Sale.price / Original.price * 100)
```

### 7.4 Formulas sur objets quantifiables

Les objets avec `.unit` supportent les opérations :
```erk
Distance:
  .value = 100
  .unit = km

Time:
  .value = 2
  .unit = h

Speed = Distance / Time
# Speed.value = 50, Speed.unit = km/h
```

---

## 8. Fichiers et extensions

### 8.1 Extensions

| Extension | Usage |
|-----------|-------|
| `.erk` | Fichier ERK générique |
| `.s.gev` | Seed (données initiales) |
| `.t.gev` | Type (définition ObjectType) |
| `.i.gev` | Instance (instance d'objet) |
| `.m.gev` | Manifest (déploiement) |

### 8.2 Structure projet

```
mon-projet/
  .erk/
    config.json         ← configuration projet
    fractale.json       ← état de la fractale
  seeds/
    master.s.gev        ← données initiales
  types/
    entities.t.gev      ← définitions types
  instances/
    agents.i.gev        ← instances
  manifests/
    app.m.gev           ← manifests déploiement
```

---

## 9. Template dynamique

### 9.1 Principe

Le template est **agnostique** et **récursif**. Il ne contient que des placeholders :

```html
<html>
  <head data-lineage="Object:Web:HeadList">{{Object:Web:HeadList}}</head>
  <body data-lineage="Object:Web:BodyList">{{Object:Web:BodyList}}</body>
</html>
```

### 9.2 Wrapper

Chaque objet a un attribut `wrapper` qui définit son rendu :

| Valeur | Rendu |
|--------|-------|
| `"div"` | `<div>{{content}}</div>` |
| `"div.modal"` | `<div class="modal">{{content}}</div>` |
| `"p#intro"` | `<p id="intro">{{content}}</p>` |
| `"div.a.b#c"` | `<div id="c" class="a b">{{content}}</div>` |
| `""` (vide) | `{{content}}` (pas de wrapper) |

### 9.3 Déploiement récursif

```
MRG.deploy("Object:Web:Page")
  → charge manifest Object:Web:Page
  → trouve {{Object:Web:Page:HeaderList}}
  → deploy récursif sur HeaderList
  → trouve {{Object:Web:Page:ContentList}}
  → deploy récursif sur ContentList
  → ... jusqu'aux feuilles
```

---

## 10. GEVR — Pattern d'exécution

### 10.1 Structure

Chaque tâche suit **Get → Execute → Validate → Render** :

```
Task
  ├── GetStep      : Récupérer les données
  ├── ExecuteStep  : Exécuter l'action
  ├── ValidateStep : Valider le résultat
  └── RenderStep   : Produire la sortie
```

### 10.2 Attributs des Steps

**GetStep :**
```erk
GetStep:
  .source = file | store | api | context
  .query = "..."
```

**ExecuteStep :**
```erk
ExecuteStep:
  .method = methodName
  .params = [param1, param2]
```

**ValidateStep :**
```erk
ValidateStep:
  .schema = SchemaName
  .rules = [Rule1, Rule2]
```

**RenderStep :**
```erk
RenderStep:
  .template = TemplateName
  .format = json | html | event
```

---

## 11. Résolution et héritage

### 11.1 Priorité de résolution

1. **owned** — définis sur l'objet
2. **injected** — injectés par relation
3. **inherited** — hérités du parent

### 11.2 Attributs automatiques

Générés automatiquement :
- `lineage` — chemin complet
- `name` — dernier segment
- `parent` — lineage du parent
- `manifestPath` — chemin du manifest

---

## 12. Référence rapide

```erk
# Déclaration
Object:Parent:Child:

# Attributs
Child.attr = value
attr IN Child:AttributeList

# Méthodes
Child.method:DoSomething
DoSomething IN Child:MethodList

# Règles
Child.rule:MustBeValid
MustBeValid IN Child:RuleList

# Relations
Child depends_on Other
Child related_to Another
X IN SomeList

# Contextes
value > 0                    # ASSERTION → bool
DO Child.attr = value        # ACTION → Create/Update
IF cond THEN action          # CONDITION → branching

# Hooks
BEFORE DO X THEN Y           # hookBefore
IF DO X THEN Y               # hookAfter
IF NOT DO X THEN Y           # hookFailure

# Temporels
WHEN event DO action         # watcher
DO action UNTIL condition    # boucle jusqu'à

# Logiques
X AND Y, X OR Y, NOT X, X XOR Y

# Comparaison
=, !=, <, >, <=, >=

# Arithmétiques
+, -, *, /, %, ^
```

---

## Changelog

- **v2** — Refonte complète (2025-01-13)
  - Contextes ASSERTION / ACTION / CONDITION
  - Hooks (BEFORE, IF, IF NOT)
  - WHEN polymorphe (while, veille, cron)
  - UNTIL
  - Formulas arithmétiques
  - Notation ancêtres/descendants
  - Extensions fichiers (.erk, .s.gev, .t.gev, .i.gev, .m.gev)
  - Template dynamique avec wrapper
  
- **v1** — Version initiale (2025-01-11)

---

© EUREKAI 2025
