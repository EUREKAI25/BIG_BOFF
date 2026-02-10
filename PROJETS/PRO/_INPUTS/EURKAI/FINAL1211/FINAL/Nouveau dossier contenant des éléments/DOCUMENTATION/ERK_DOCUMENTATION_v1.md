# ================================================================
# ERK — EUREKAI Rule Kernel
# Documentation du langage v1
# ================================================================

## Vue d'ensemble

ERK est le langage déclaratif d'EUREKAI pour définir des objets, 
leurs attributs, relations, méthodes et règles dans une architecture 
fractale où **tout est objet**.

---

## 1. Principes fondamentaux

### 1.1 Tout est objet
Chaque élément du système est un objet avec un **lineage** unique.

### 1.2 Héritage par lineage
Le lineage encode la hiérarchie : `Parent:Enfant:PetitEnfant`

### 1.3 Quatre types de relations canoniques
- `inherits_from` — héritage (implicite via lineage)
- `depends_on` — dépendance fonctionnelle
- `related_to` — association sémantique
- `contains` — composition (implicite via attributs/méthodes)

### 1.4 Racine unique
Tous les objets descendent de `Object`

---

## 2. Syntaxe

### 2.1 Déclaration d'objet

```erk
Object:Parent:Enfant:
```

Le `:` final indique une déclaration. Le lineage est automatiquement 
validé et les ancêtres sont créés si nécessaires.

**Règles de nommage :**
- Commence par une majuscule
- Alphanumérique + underscore : `[A-Z][A-Za-z0-9_]*`
- Segments séparés par `:`

**Exemples valides :**
```erk
Object:Entity:Agent:
Object:Scenario:Step:GetStep:LoadCatalog_Get:
Object:AI:Provider:Anthropic:
```

### 2.2 Attributs

**Syntaxe simple (type implicite string) :**
```erk
Object:Entity:Agent:
  [scope, profile, maxTokens]
```

**Syntaxe avec type :**
```erk
Object:Config:
  [key:str, value:str, enabled:bool, count:int]
```

**Syntaxe avec valeur :**
```erk
Object:AI:Provider:Anthropic:
  [name=Anthropic, apiUrl=https://api.anthropic.com, apiKey=ENV:ANTHROPIC_API_KEY]
```

**Types supportés :**
- `str` / `string` — chaîne de caractères (défaut)
- `int` — entier
- `bool` — booléen
- `date` — date/datetime
- `json` — objet JSON

### 2.3 Relations

**Syntaxe :**
```erk
Object:Entity:Agent:
  [depends_on Security:Role, depends_on Structure:DataSet:Catalog]
```

**Types de relations :**
| Relation | Alias | Signification |
|----------|-------|---------------|
| `inherits_from` | `type_of` | Hérite de (implicite via lineage) |
| `depends_on` | — | Requiert pour fonctionner |
| `related_to` | `scope_of` | Associé sémantiquement |

**Cibles de relation :**
- Lineage complet : `Security:Role:Architect`
- Lineage relatif : `Role:Architect` (préfixé auto avec `Object:`)

### 2.4 Blocs multiples

Un objet peut avoir plusieurs blocs `[...]` :

```erk
Object:Entity:Agent:ArchitectAgent:
  [name=ArchitectAgent, scope=core, profile=architect, maxTokens=4096]
  [depends_on Security:Role:Architect]
```

Le premier bloc contient les attributs, les suivants les relations.

### 2.5 Commentaires

```erk
# Commentaire ligne complète
// Commentaire alternatif

Object:Example:  # Commentaire en fin de ligne (non supporté)
```

### 2.6 Sections

Les sections organisent le fichier (ignorées par le parser) :

```erk
# ================================================================
# SECTION : Entities
# ================================================================
```

---

## 3. Fichiers types

### 3.1 Catalogue (définitions)

Définit les **ObjectTypes** — la structure du système.

```erk
# catalog_definitions.txt

# --- Core ---
Object:
  [path]

Object:Entity:
  [scope]

Object:Entity:Agent:
  [profile, maxTokens]
  [depends_on Security:Role]
```

### 3.2 Seeds (instances)

Définit les **instances** initiales avec valeurs.

```erk
# seeds.txt

Object:AI:Provider:Anthropic:
  [name=Anthropic, apiUrl=https://api.anthropic.com]

Object:Entity:Agent:ArchitectAgent:
  [name=ArchitectAgent, scope=core, profile=architect]
  [depends_on Security:Role:Architect]
```

### 3.3 Scénarios (GEVR)

Définit les **scénarios** d'exécution.

```erk
# scenario_bootstrap.txt

Object:Scenario:Bootstrap:InitSystem:
  [name=InitSystem, status=pending, priority=1]
  [pipeline=bootstrap, queue=system]

Object:Scenario:Step:GetStep:LoadCatalog_Get:
  [name=LoadCatalog_Get, order=1, action=get]
  [source=file, query=catalog_definitions.txt]
  [depends_on Scenario:Task:LoadCatalog]
```

---

## 4. GEVR — Pattern d'exécution

### 4.1 Structure

Chaque tâche suit le pattern **Get → Execute → Validate → Render** :

```
Task
  ├── GetStep      : Récupérer les données
  ├── ExecuteStep  : Exécuter l'action
  ├── ValidateStep : Valider le résultat
  └── RenderStep   : Produire la sortie
```

### 4.2 Attributs des Steps

**GetStep :**
```erk
[source=file|store|api|context, query=...]
```

**ExecuteStep :**
```erk
[method=methodName, params=param1|param2]
```

**ValidateStep :**
```erk
[schema=SchemaName, rules=Rule1|Rule2|Rule3]
```

**RenderStep :**
```erk
[template=TemplateName, format=json|html|event]
```

### 4.3 Lifecycle

```
pending → processing → done | failed
```

---

## 5. Héritage et résolution

### 5.1 Héritage implicite

Un objet hérite automatiquement de son parent :

```erk
Object:Entity:Agent:ArchitectAgent:
```

Hérite de : `Object` → `Object:Entity` → `Object:Entity:Agent`

### 5.2 Résolution des attributs

Les attributs sont résolus par ordre de priorité :
1. **owned** — définis sur l'objet
2. **injected** — injectés par relation
3. **inherited** — hérités du parent

### 5.3 Attributs automatiques

Trois attributs sont générés automatiquement :
- `lineage` — chemin complet
- `name` — dernier segment
- `parent` — lineage du parent

---

## 6. Sécurité (RBAC)

### 6.1 Rôles

```erk
Object:Security:Role:Architect:
  [layer=core]
  [scope_of Security:Permission:SchemaPermission]
  [scope_of Security:Permission:RulePermission]
```

### 6.2 Permissions

```erk
Object:Security:Permission:CreatePermission:
  [action=create, target=*]
```

### 6.3 Agents et Rôles

```erk
Object:Entity:Agent:ArchitectAgent:
  [depends_on Security:Role:Architect]
```

---

## 7. Prompts (AI)

### 7.1 Types de prompts

| Type | Usage |
|------|-------|
| `ContextPrompt` | Contexte système global |
| `RolePrompt` | Instructions selon le rôle |
| `MissionPrompt` | Objectif de la tâche |
| `GoalPrompt` | Critères de succès |

### 7.2 Exemple

```erk
Object:AI:Prompt:ContextPrompt:SystemContext:
  [name=SystemContext, scope=global, injection=system]
  [content=Tu es un agent EUREKAI opérant dans une architecture fractale.]

Object:AI:Prompt:RolePrompt:ArchitectRole:
  [name=ArchitectRole, role=Architect]
  [instructions=Tu conçois et maintiens la structure fractale du système.]
```

---

## 8. Export Agent JSON

### 8.1 Format

```json
{
  "Object:Entity:Agent:ArchitectAgent": {
    "attribute": {
      "lineage": "Object:Entity:Agent:ArchitectAgent",
      "name": "ArchitectAgent",
      "parent": "Object:Entity:Agent",
      "scope": "core",
      "profile": "architect",
      "maxTokens": "4096"
    },
    "relation": {
      "inherits_from": ["Object:Entity:Agent"],
      "depends_on": ["Object:Security:Role:Architect"]
    },
    "method": [],
    "rule": []
  }
}
```

### 8.2 Règles d'export

- `lineage`, `name`, `parent` → valeurs réelles (automated)
- Autres attributs → valeur si définie, sinon type
- Relations → tableau de lineages cibles

---

## 9. Bonnes pratiques

### 9.1 Nommage

- **ObjectTypes** : PascalCase (`ArchitectAgent`)
- **Attributs** : camelCase (`maxTokens`)
- **Relations** : snake_case (`depends_on`)

### 9.2 Organisation

```
catalog_definitions.txt   # Structure (ObjectTypes)
seeds.txt                 # Instances initiales
bootstrap_gevr.txt        # Scénario d'init
scenario_*.txt            # Autres scénarios
```

### 9.3 Relations

- Utiliser `depends_on` pour les dépendances techniques
- Utiliser `related_to` pour les associations métier
- Éviter les relations circulaires

### 9.4 Valeurs

- Variables d'env : `ENV:VARIABLE_NAME`
- Listes : `value1|value2|value3`
- Références : lineage complet ou relatif

---

## 10. Référence rapide

```erk
# Déclaration
Object:Parent:Child:

# Attributs simples
  [attr1, attr2, attr3]

# Attributs typés
  [attr1:str, attr2:int, attr3:bool]

# Attributs avec valeurs
  [attr1=value1, attr2=value2]

# Relations
  [depends_on Target:Lineage]
  [related_to Other:Lineage]

# Commentaires
# Ceci est un commentaire
```

---

## Changelog

- **v1** — Version initiale (2025-01-11)
  - Syntaxe de base
  - Support attributs avec valeurs
  - Pattern GEVR documenté
  - Export Agent JSON

---

© EUREKAI 2025
