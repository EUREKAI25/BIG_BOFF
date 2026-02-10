# ARCH 00 — Architecture Object Fractal Tool

> Version 1.0 — Document d'architecture technique  
> Basé sur SPEC_00 et QUESTIONS_architecture_clarifications_REPONSE_NEW

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structures de données JSON](#2-structures-de-données-json)
3. [Composants UI](#3-composants-ui)
4. [Flux de mise à jour](#4-flux-de-mise-à-jour)
5. [Intégration des étapes 01-04](#5-intégration-des-étapes-01-04)
6. [Extensibilité](#6-extensibilité)
7. [Annexes](#7-annexes)

---

## 1. Vue d'ensemble

### 1.1. Objectif

L'**Object Fractal Tool** (ou "Cockpit") est un outil de modélisation permettant de :

- Créer, éditer et organiser des **ObjectTypes** structurés en fractale
- Visualiser l'héritage et les injections via une **vue fractale**
- Valider la **nomenclature** (lineages) en temps réel
- Tester des expressions via une **console semi-réelle**

### 1.2. Principes fondamentaux

```
┌─────────────────────────────────────────────────────────────┐
│                    RÈGLES CANONIQUES                        │
├─────────────────────────────────────────────────────────────┤
│  Séparateur ":"  →  Généalogie (Parent:Child:GrandChild)   │
│  Séparateur "."  →  Accès interne (Object.attribute)       │
│  Combiné         →  Parent:Child.attribute                  │
├─────────────────────────────────────────────────────────────┤
│  Relations       →  inherits_from | depends_on | related_to │
│  Plans IVC×DRO   →  Lecture seule, projection automatique   │
│  Bundles         →  owned | inherited | injected            │
└─────────────────────────────────────────────────────────────┘
```

### 1.3. Stack technique V1

| Couche | Technologie | Rôle |
|--------|-------------|------|
| Front | HTML + JS (vanilla ou framework léger) | UI interactive |
| Données | Fichiers JSON | Persistance locale |
| Backend | Minimal (optionnel) | Parsing ERK, validation, génération fractale |

---

## 2. Structures de données JSON

### 2.1. Vue globale des fichiers

```
/data
  ├── objectTypes.json      # Définitions des ObjectTypes
  ├── lineageIndex.json     # Index de navigation rapide
  ├── tags.json             # Tags et catégories
  ├── aliases.json          # Alias des relations
  ├── schemas.json          # Schémas de Bundles
  ├── vectors.json          # Instances (vecteurs)
  └── config.json           # Configuration globale
```

### 2.2. ObjectType

Chaque ObjectType est un Bundle auto-descriptif.

```json
{
  "id": "uuid-unique",
  "lineage": "Entity:Agent:AIAgent",
  "name": "AIAgent",
  "parent": "Entity:Agent",
  
  "planes": {
    "Identity": { "locked": true },
    "View": {},
    "Context": {},
    "Definition": {},
    "Rule": {},
    "Option": {}
  },
  
  "elementList": {
    "AttributeList": {
      "inherited_bundle": [],
      "injected_bundle": [],
      "owned_bundle": [
        {
          "name": "model",
          "type": "string",
          "required": true,
          "default": null,
          "source": "owned"
        }
      ]
    },
    "RelationList": {
      "inherited_bundle": [],
      "injected_bundle": [],
      "owned_bundle": [
        {
          "type": "depends_on",
          "target": "Core:Config",
          "cardinality": "1:1",
          "source": "owned"
        }
      ]
    },
    "MethodList": {
      "inherited_bundle": [],
      "injected_bundle": [],
      "owned_bundle": [
        {
          "name": "execute",
          "signature": "execute(params: Object): Result",
          "description": "Exécute l'agent avec les paramètres donnés",
          "source": "owned"
        }
      ]
    },
    "RuleList": {
      "inherited_bundle": [],
      "injected_bundle": [],
      "owned_bundle": [
        {
          "id": "rule-001",
          "type": "ERK",
          "condition": "this.model != null",
          "action": "enable",
          "target": "this.execute",
          "source": "owned"
        }
      ]
    }
  },
  
  "meta": {
    "version": "1.0.0",
    "state": "draft",
    "created": "2025-01-15T10:00:00Z",
    "updated": "2025-01-15T10:00:00Z"
  }
}
```

### 2.3. XFractal (vue calculée)

XFractal est **généré dynamiquement** par résolution de l'héritage. Il n'est pas stocké mais calculé à la demande.

```json
{
  "lineage": "Entity:Agent:AIAgent",
  "resolved": {
    "attributes": [
      { "name": "id", "source": "inherited", "from": "Entity" },
      { "name": "name", "source": "inherited", "from": "Entity:Agent" },
      { "name": "model", "source": "owned", "from": "Entity:Agent:AIAgent" },
      { "name": "logLevel", "source": "injected", "from": "Provider:Logging" }
    ],
    "methods": [
      { "name": "create", "source": "inherited", "from": "Entity" },
      { "name": "execute", "source": "owned", "from": "Entity:Agent:AIAgent" }
    ],
    "rules": [],
    "relations": []
  },
  "computedAt": "2025-01-15T10:30:00Z"
}
```

### 2.4. Lineage Index

Index plat pour navigation rapide et validation.

```json
{
  "index": {
    "Entity": {
      "id": "uuid-1",
      "children": ["Entity:Agent", "Entity:Resource"],
      "depth": 1
    },
    "Entity:Agent": {
      "id": "uuid-2",
      "parent": "Entity",
      "children": ["Entity:Agent:AIAgent", "Entity:Agent:HumanAgent"],
      "depth": 2
    },
    "Entity:Agent:AIAgent": {
      "id": "uuid-3",
      "parent": "Entity:Agent",
      "children": [],
      "depth": 3
    }
  },
  "roots": ["Core", "Entity", "Schema", "Provider"]
}
```

### 2.5. Tags et Catégories

```json
{
  "tags": [
    {
      "id": "tag-001",
      "name": "critical",
      "color": "#ff0000",
      "targets": ["Entity:Agent:AIAgent", "Core:Config"]
    }
  ],
  "categories": [
    {
      "id": "cat-001",
      "name": "Agents",
      "description": "Tous les types d'agents",
      "pattern": "Entity:Agent:*"
    }
  ]
}
```

### 2.6. Alias

Les alias sont auto-générés depuis les relations `depends_on` et `related_to`.

```json
{
  "aliases": [
    {
      "id": "alias-001",
      "name": "AIAgent_of",
      "baseRelation": "depends_on",
      "source": "Entity:Agent:AIAgent",
      "target": "Core:Config",
      "autoGenerated": true
    }
  ]
}
```

### 2.7. Schémas de Bundle

Définit les contraintes structurelles d'un Bundle.

```json
{
  "schemas": {
    "AgentSchema": {
      "id": "schema-001",
      "appliesTo": "Entity:Agent:*",
      "constraints": {
        "AttributeList": {
          "required": ["name", "status"],
          "allowed": ["name", "status", "model", "config"],
          "min": 2,
          "max": 10
        },
        "RelationList": {
          "required": [],
          "allowedTypes": ["depends_on", "related_to"],
          "max": 5
        },
        "MethodList": {
          "required": ["execute"],
          "max": 20
        },
        "RuleList": {
          "allowedTypes": ["ERK"],
          "max": 50
        }
      }
    }
  }
}
```

### 2.8. Vecteurs (instances)

```json
{
  "vectors": [
    {
      "id": "vec-001",
      "lineage": "Entity:Agent:AIAgent",
      "plane": "Definition",
      "payload": {
        "model": "claude-sonnet-4-20250514",
        "status": "active"
      },
      "meta": {
        "version": "1.0.0",
        "state": "validated",
        "created": "2025-01-15T10:00:00Z"
      }
    }
  ]
}
```

---

## 3. Composants UI

### 3.1. Layout général

```
┌─────────────────────────────────────────────────────────────────────┐
│                          HEADER / TOOLBAR                           │
│  [Nouveau] [Sauvegarder] [Exporter] [Importer]    🔍 Recherche     │
├───────────────┬─────────────────────────────────┬───────────────────┤
│               │                                 │                   │
│   PANEL A     │         PANEL C                 │     PANEL B       │
│               │                                 │                   │
│  Explorateur  │    Éditeur de schéma            │  Tags/Catégories  │
│  de lineages  │    + Vue fractale               │  Alias            │
│               │                                 │                   │
│  (Arbre)      │    [Onglets: Schema|Fractal]    │  (Sidebar)        │
│               │                                 │                   │
├───────────────┴─────────────────────────────────┴───────────────────┤
│                          PANEL D                                    │
│                     Console semi-réelle                             │
│  > Entity:Agent:AIAgent.execute({task:"test"})                     │
│  { "status": "ok", "outputs": {...} }                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2. Panel A — Explorateur de lineages

**Fonctions :**
- Affichage arborescent des ObjectTypes
- Navigation par clic
- Création (+ bouton contextuel)
- Renommage (double-clic ou F2)
- Suppression (avec confirmation)
- Duplication
- Drag & drop pour réorganiser (si autorisé par les règles)

**Données affichées :**
```
▼ Entity
  ▼ Agent
    ├─ AIAgent          [tag: critical]
    └─ HumanAgent
  ▼ Resource
    └─ Document
▼ Core
  └─ Config
▼ Schema
  └─ AgentSchema
```

**Validation temps réel :**
- Regex appliquée à chaque saisie
- Autocomplétion des segments existants
- Alerte si lineage invalide

### 3.3. Panel B — Tags, Catégories, Alias

**Sections :**

1. **Tags** : liste filtrable, assignation par drag ou menu
2. **Catégories** : groupements par pattern, filtrage de l'arbre
3. **Alias** : liste en lecture (auto-générés), possibilité de renommer

**Interactions :**
- Clic sur tag → filtre l'arbre (Panel A)
- Clic sur alias → navigue vers la source

### 3.4. Panel C — Éditeur de schéma + Vue fractale

**Onglet 1 : Éditeur de schéma**

Interface formulaire pour éditer l'ObjectType sélectionné :

```
┌─────────────────────────────────────────────────┐
│ ObjectType: Entity:Agent:AIAgent                │
├─────────────────────────────────────────────────┤
│ ▼ Attributes (owned)                            │
│   [+] Ajouter                                   │
│   ├─ model: string [required] [✎] [✕]          │
│   └─ config: object [optional] [✎] [✕]         │
├─────────────────────────────────────────────────┤
│ ▼ Relations                                     │
│   [+] Ajouter                                   │
│   └─ depends_on → Core:Config (1:1) [✎] [✕]    │
├─────────────────────────────────────────────────┤
│ ▼ Methods                                       │
│   [+] Ajouter                                   │
│   └─ execute(params): Result [✎] [✕]           │
├─────────────────────────────────────────────────┤
│ ▼ Rules ERK                                     │
│   [+] Ajouter                                   │
│   └─ IF model != null THEN enable execute [✎]  │
└─────────────────────────────────────────────────┘
```

**Onglet 2 : Vue fractale**

Visualisation de XFractal (résolu) avec coloration par source :

```
┌─────────────────────────────────────────────────┐
│ XFractal: Entity:Agent:AIAgent                  │
├─────────────────────────────────────────────────┤
│ Attributes:                                     │
│   🟢 id        [inherited: Entity]              │
│   🟢 name      [inherited: Entity:Agent]        │
│   🔵 model     [owned]                          │
│   🟣 logLevel  [injected: Provider:Logging]     │
├─────────────────────────────────────────────────┤
│ Methods:                                        │
│   🟢 create    [inherited: Entity]              │
│   🔵 execute   [owned]                          │
├─────────────────────────────────────────────────┤
│ Légende: 🟢 inherited  🔵 owned  🟣 injected    │
└─────────────────────────────────────────────────┘
```

**Projection IVC×DRO :**
- Disponible en mode "avancé"
- Affiche sur quel Plan chaque élément est projeté
- Non éditable (lecture seule)

### 3.5. Panel D — Console semi-réelle

**Fonctions :**
- Saisie d'expressions (avec autocomplétion)
- Évaluation locale (pas d'appel externe)
- Validation des règles ERK
- Test de cohérence MetaSchema

**Format d'entrée :**
```
Entity:Agent:AIAgent.execute({task: "analyze"})
Entity:Agent:AIAgent.model
```

**Format de sortie :**
```json
{
  "status": "ok",
  "messages": ["Method signature valid", "All ERK rules passed"],
  "outputs": {
    "returnType": "Result",
    "mock": { "success": true }
  }
}
```

**Erreurs possibles :**
```json
{
  "status": "error",
  "messages": ["ERK rule failed: model is null", "Method 'execute' is disabled"],
  "outputs": {}
}
```

---

## 4. Flux de mise à jour

### 4.1. Principe général

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   UI Event   │ ──▶ │   Validator  │ ──▶ │  JSON Store  │
│  (user action)│     │  (business   │     │  (persist)   │
│              │     │   rules)     │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Notifier   │
                     │  (update UI) │
                     └──────────────┘
```

### 4.2. Actions et leurs effets

| Action UI | Validation | Mise à jour JSON | Effet cascade |
|-----------|------------|------------------|---------------|
| Créer ObjectType | Regex lineage, parent existe | objectTypes.json, lineageIndex.json | — |
| Renommer ObjectType | Regex, pas de doublon | objectTypes.json, lineageIndex.json, aliases.json | MAJ enfants |
| Supprimer ObjectType | Pas d'enfants (ou suppression récursive) | objectTypes.json, lineageIndex.json | MAJ relations |
| Ajouter attribut | Nom unique, type valide | objectTypes.json | — |
| Modifier règle ERK | Syntaxe valide | objectTypes.json | Réévaluation console |
| Ajouter relation | Type canonique, target existe | objectTypes.json, aliases.json | Génération alias |
| Drag & drop tag | — | tags.json | — |
| Créer vecteur | Conforme au schéma | vectors.json | — |

### 4.3. Validation en temps réel

**Lineage :**
```javascript
const LINEAGE_REGEX = /^([A-Z][A-Za-z0-9]*)(:[A-Z][A-Za-z0-9]*)*(\.[a-z][A-Za-z0-9]*)*$/;

function validateLineage(input) {
  return LINEAGE_REGEX.test(input);
}
```

**Relation :**
```javascript
const CANONICAL_RELATIONS = ['inherits_from', 'depends_on', 'related_to'];

function validateRelation(type) {
  return CANONICAL_RELATIONS.includes(type);
}
```

### 4.4. Calcul de XFractal

Algorithme de résolution (pseudo-code) :

```
function computeXFractal(lineage):
    result = { attributes: [], methods: [], rules: [], relations: [] }
    
    // 1. Résoudre l'héritage (inherited_bundle)
    ancestors = getAncestors(lineage)  // [Entity, Entity:Agent, Entity:Agent:AIAgent]
    for ancestor in ancestors:
        for element in ancestor.elementList.*.inherited_bundle:
            result.add(element, source="inherited", from=ancestor.lineage)
    
    // 2. Appliquer les owned
    current = getObjectType(lineage)
    for element in current.elementList.*.owned_bundle:
        result.add(element, source="owned", from=lineage)
    
    // 3. Appliquer les injections (par tags, catégories, providers)
    injections = resolveInjections(lineage)
    for injection in injections:
        result.add(injection.element, source="injected", from=injection.provider)
    
    // 4. Résoudre les conflits (owned > injected > inherited)
    result = resolveConflicts(result)
    
    return result
```

**Priorité de résolution :**
```
owned > injected > inherited
```

---

## 5. Intégration des étapes 01-04

### 5.1. Cartographie des étapes

| Étape | Focus | Composants concernés | Fichiers JSON |
|-------|-------|---------------------|---------------|
| 01 | Lineages & navigation | Panel A (Explorateur) | objectTypes.json, lineageIndex.json |
| 02 | Vue fractale & héritage | Panel C (Vue fractale) | (calcul dynamique XFractal) |
| 03 | Tags, catégories, alias | Panel B (Sidebar) | tags.json, aliases.json |
| 04 | Console & tests | Panel D (Console) | vectors.json |

### 5.2. Dépendances entre étapes

```
     ┌─────┐
     │ 01  │  Lineages (fondation)
     └──┬──┘
        │
   ┌────┴────┐
   │         │
┌──▼──┐   ┌──▼──┐
│ 02  │   │ 03  │  Fractale & Tags (parallélisables)
└──┬──┘   └──┬──┘
   │         │
   └────┬────┘
        │
     ┌──▼──┐
     │ 04  │  Console (nécessite 01 + 02)
     └─────┘
```

### 5.3. Points d'intégration par étape

**Étape 01 — Lineages :**
- Implémenter `lineageIndex.json` et sa gestion
- Créer le composant arbre (Panel A)
- Valider la regex à chaque action
- API : `createObjectType()`, `renameObjectType()`, `deleteObjectType()`

**Étape 02 — Vue fractale :**
- Implémenter `computeXFractal()`
- Créer le composant de visualisation (Panel C, onglet Fractale)
- Coloration par source (owned/inherited/injected)
- API : `getXFractal(lineage)`

**Étape 03 — Tags & Alias :**
- Implémenter `tags.json` et `aliases.json`
- Créer Panel B
- Auto-génération des alias sur création de relation
- API : `addTag()`, `removeTag()`, `getAliases()`

**Étape 04 — Console :**
- Implémenter le parser d'expressions
- Évaluateur de règles ERK
- Créer Panel D
- API : `evaluate(expression)`, `validateERK(rule)`

---

## 6. Extensibilité

### 6.1. Ajout de nouveaux champs

La structure JSON est conçue pour accepter de nouveaux champs sans casser l'existant :

```json
{
  "elementList": {
    "AttributeList": { ... },
    "RelationList": { ... },
    "MethodList": { ... },
    "RuleList": { ... },
    "FutureList": { ... }  // ← Nouveau type d'élément
  }
}
```

### 6.2. Points d'extension prévus

| Extension | Mécanisme | Impact |
|-----------|-----------|--------|
| Nouveau type d'élément | Ajouter dans ElementList | Mettre à jour l'éditeur |
| Nouvelle relation | Impossible (3 canoniques figées) | Via alias uniquement |
| Nouveau Plan | Ajouter dans `planes` | Mettre à jour la projection |
| Backend réel | Remplacer JSON par API REST | Modifier le store |
| PPCM/PGCD | Layer dédié (futur) | Nouveau composant |

### 6.3. Architecture modulaire suggérée

```
/src
  /core
    ├── lineage.js        # Validation, parsing, index
    ├── fractal.js        # Calcul XFractal
    ├── erk.js            # Parsing et évaluation ERK
    └── store.js          # Lecture/écriture JSON
  /ui
    ├── explorer.js       # Panel A
    ├── sidebar.js        # Panel B
    ├── editor.js         # Panel C (schéma)
    ├── fractalView.js    # Panel C (fractale)
    └── console.js        # Panel D
  /utils
    ├── regex.js          # Constantes regex
    └── events.js         # Système de notification
```

---

## 7. Annexes

### 7.1. Regex officielle

```regex
^([A-Z][A-Za-z0-9]*)(:[A-Z][A-Za-z0-9]*)*(\.[a-z][A-Za-z0-9]*)*$
```

**Exemples valides :**
- `Entity`
- `Entity:Agent`
- `Entity:Agent:AIAgent`
- `Entity:Agent:AIAgent.model`
- `Entity:Agent:AIAgent.execute`

**Exemples invalides :**
- `entity` (minuscule)
- `Entity.Agent` (mauvais séparateur)
- `Entity:agent` (segment enfant en minuscule)
- `Entity::Agent` (double séparateur)

### 7.2. Relations canoniques

| Relation | Direction | Sémantique | Génère alias |
|----------|-----------|------------|--------------|
| `inherits_from` | A → B | A hérite de B | Non |
| `depends_on` | A → B | A dépend de B | Oui : `A_of` |
| `related_to` | A ↔ B | Lien sémantique | Oui : `A_of`, `B_of` |

### 7.3. Priorité de résolution

```
1. owned        (priorité maximale)
2. injected     (priorité moyenne)
3. inherited    (priorité minimale)
```

En cas de conflit sur un même attribut/méthode, la source de plus haute priorité gagne.

### 7.4. Structure d'une règle ERK

```json
{
  "id": "rule-unique-id",
  "type": "ERK",
  "condition": "<expression booléenne>",
  "action": "enable | require | kill",
  "target": "<lineage.element>",
  "source": "owned | inherited | injected",
  "from": "<lineage source si non-owned>"
}
```

**Actions ERK :**
- `enable` : active l'élément cible si la condition est vraie
- `require` : rend l'élément obligatoire si la condition est vraie
- `kill` : désactive l'élément si la condition est vraie

---

## Checklist de validation (TEST_00)

- [x] Les structures JSON permettent de représenter :
  - [x] les ObjectTypes
  - [x] les lineages
  - [x] les tags / catégories
  - [x] les alias
  - [x] les schémas de Bundles
  - [x] les XFractals (avec owned/inherited/injected)
- [x] On peut distinguer clairement **owned**, **inherited**, **injected** dans les données
- [x] La nomenclature de lineage peut être validée par une regex unique
- [x] L'ajout futur de champs ne casse pas l'architecture
- [x] Chaque étape (01, 02, 03, 04) a un point d'intégration clair

---

*Document d'architecture — Object Fractal Tool v1.0*
