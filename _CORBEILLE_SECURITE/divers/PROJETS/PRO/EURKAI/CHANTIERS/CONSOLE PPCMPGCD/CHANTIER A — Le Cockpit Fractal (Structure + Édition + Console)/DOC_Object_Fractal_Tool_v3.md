# Object Fractal Tool v3 — Documentation

## Vue d'ensemble

L'Object Fractal Tool est un éditeur visuel pour concevoir et manipuler des **ObjectTypes** selon une architecture fractale. Chaque objet hérite de ses ancêtres et peut définir ses propres attributs, méthodes, relations et règles.

---

## Architecture des données

### Structure d'un ObjectType

```javascript
{
  id: "uuid-xxx",
  lineage: "Object:Entity:Agent",    // Chemin complet (séparateur ":")
  name: "Agent",                      // Nom court (dernier segment)
  parent: "Object:Entity",            // Lineage du parent (null si racine)
  toFinalize: false,                  // true = créé automatiquement, à compléter
  tags: ["ai", "core"],               // Tags associés
  elementList: {
    AttributeList: {
      owned_bundle: [...],            // Définis sur cet objet
      inherited_bundle: [...],        // Hérités (calculés dynamiquement)
      injected_bundle: [...]          // Injectés par tags/logique transversale
    },
    MethodList: { ... },
    RelationList: { ... },
    RuleList: { ... }
  }
}
```

### Règles de nommage

| Élément | Format | Exemple |
|---------|--------|---------|
| Lineage | PascalCase, séparateur `:` | `Object:Entity:Agent:AIAgent` |
| Attribut | camelCase | `createdAt`, `modelName` |
| Méthode | camelCase | `execute()`, `validate()` |
| Tag | lowercase | `ai`, `core`, `storage` |

### Types d'éléments

| Source | Couleur | Description |
|--------|---------|-------------|
| **owned** | 🟢 Vert | Défini directement sur l'objet |
| **inherited** | 🔵 Bleu | Hérité d'un ancêtre |
| **injected** | 🟣 Violet | Injecté par tag ou logique transversale |

---

## Interface utilisateur

### Onglet Explorateur

**3 colonnes :**

1. **Arbre (gauche)** — Hiérarchie des ObjectTypes
   - Clic = sélection
   - Drag & drop = re-parenting
   - Bouton `+` = ajouter un tag

2. **Vue Fractale (centre)** — Détail de l'objet sélectionné
   - Chaîne d'héritage (cartes cliquables)
   - Éléments groupés par type (Attrs, Methods, Rels, Rules)
   - Tags et Alias intégrés dans la carte courante
   - Section "Relations sortantes" et "Enfants directs"
   - Console de test inline

3. **Tags (droite)** — Gestion des tags
   - Création de tags
   - Drag & drop vers l'arbre ou les cartes
   - Clic droit = menu contextuel (catégorie, supprimer)

### Onglet Console

Console de test avancée avec :
- Sélecteur d'ObjectType avec autocomplétion
- Liste des méthodes disponibles (cliquables)
- Historique des commandes
- Résultats JSON formatés

### Onglet JSON

- Visualisation du store complet
- Export/Import JSON
- Objet sélectionné mis en avant (`_selected`)

---

## Fonctionnalités principales

### Création d'ObjectTypes

**Input en haut de page :** Saisir un lineage et appuyer sur Entrée.

| Saisie | Comportement |
|--------|-------------|
| `Foo` | Crée racine `Foo` |
| `Object:Entity:User` | Crée `User` sous `Object:Entity` existant |
| `Foo:Bar:Baz` | Crée `Foo`, `Foo:Bar`, `Foo:Bar:Baz` automatiquement |
| `Entity:Agent` (Entity existe ailleurs) | Modal : "Rattacher à Object:Entity ?" |

### Édition des éléments

Sur la carte de l'objet courant (bordure verte) :

- **Boutons `+ Attribut`, `+ Méthode`, `+ Relation`, `+ Règle`**
- **Clic sur élément owned** → édition inline
- **Bouton `×`** sur élément → suppression

### Suppression d'ObjectType

- Bouton `🗑 Supprimer cet ObjectType`
- Alerte listant les dépendances (enfants, relations, alias)
- Suppression cascade des enfants et nettoyage des relations

### Navigation

- **Cartes ancêtres** : Clic pour naviguer vers cet objet
- **Relations sortantes** : Clic sur la cible
- **Enfants directs** : Chips cliquables
- **Breadcrumb** : Racines L1 en haut

---

## Console de test

### Syntaxe des expressions

```
Lineage.method({args}).path.to.result
```

**Exemples :**

```javascript
// Appel simple
Object:Entity.create({name: "test"})

// Avec navigation dans le résultat
Object:Entity:Agent:AIAgent.prompt({input: "hello"}).response.text

// Validation
Object:Entity.validate()

// Méthode héritée
Object:Entity:Agent:AIAgent.create({model: "gpt-4"})
```

### Résultats mockés

Les méthodes retournent des résultats simulés basés sur leur nom :

| Méthode | Résultat mock |
|---------|---------------|
| `create` | `{ success: true, result: { id, lineage, createdAt, ...args } }` |
| `update` | `{ success: true, result: { id, updatedAt, ...args } }` |
| `delete` | `{ success: true, deleted: true }` |
| `validate` | `{ valid: true, errors: [] }` |
| `execute` | `{ success: true, result: { status: "completed" } }` |
| `prompt` | `{ success: true, response: { text, tokens, model } }` |
| Autre | `{ success: true, method, args, result: { mock: true } }` |

### Gestion des erreurs

| Erreur | Message |
|--------|---------|
| Syntaxe invalide | `Format attendu: Lineage.method(args)` |
| ObjectType non trouvé | `ObjectType non trouvé: Foo` |
| Méthode non trouvée | `Méthode non trouvée: bar sur Foo` + liste des méthodes disponibles |
| Propriété non trouvée | `Property 'xxx' not found` |

---

## Règles ERK (Enable/Require/Kill)

### Structure

```javascript
{
  id: "rule-001",
  type: "ERK",
  condition: "this.model != null",
  action: "enable",        // enable | require | kill
  target: "this.prompt",
  source: "owned"
}
```

### Actions

| Action | Effet |
|--------|-------|
| `enable` | Active l'élément si condition vraie |
| `require` | Rend obligatoire si condition vraie |
| `kill` | Désactive si condition vraie |

### Exemples

```javascript
// Activer prompt() seulement si model est défini
{ condition: "this.model != null", action: "enable", target: "this.prompt" }

// Rendre email obligatoire
{ condition: "this.role == 'admin'", action: "require", target: "this.email" }

// Désactiver stream() si température > 1
{ condition: "this.temperature > 1", action: "kill", target: "this.stream" }
```

---

## Héritage dynamique

L'héritage est **calculé à l'affichage**, pas stocké statiquement :

1. Remontée de la chaîne des ancêtres
2. Collecte des `owned_bundle` de chaque ancêtre
3. Marquage comme `inherited` avec source

**Conséquence :** Ajouter un attribut à `Object:Entity` le propage automatiquement à tous ses descendants (`Agent`, `AIAgent`, `HumanAgent`, `Resource`, etc.)

---

## Raccourcis et astuces

| Action | Comment |
|--------|---------|
| Créer rapidement | Taper le lineage complet dans l'input |
| Naviguer vers parent | Cliquer sur la carte ancêtre |
| Ajouter tag | Bouton `+` dans l'arbre ou drag & drop |
| Tester méthode | Console inline ou onglet Console |
| Exporter | Onglet JSON → Télécharger |
| Importer | Onglet JSON → Importer |

---

## Limitations actuelles

- Les règles ERK sont stockées mais **pas exécutées** (affichage seulement)
- Les méthodes sont **mockées**, pas de vraie logique métier
- Pas de validation de schéma en temps réel
- Pas de persistence (rechargement = reset)

---

## Prochaines étapes potentielles

1. **Persistence** — localStorage ou export/import auto
2. **Validation de schéma** — Vérification des contraintes en temps réel
3. **Exécution ERK** — Évaluation réelle des règles
4. **Injection par tags** — Logique pour injecter automatiquement des éléments selon les tags
5. **Visualisation graphe** — Vue en graphe des relations
