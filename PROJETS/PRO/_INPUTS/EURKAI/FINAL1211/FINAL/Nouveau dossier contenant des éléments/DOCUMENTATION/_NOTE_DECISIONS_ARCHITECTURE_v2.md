# EUREKAI - Note récapitulative : Décisions Architecture & Roadmap

Date : 2025-12-14 (mise à jour)

---

## 1. Architecture des données

### Séparation Core / Client

- **Core (agence)** : Seeds, Templates, Vectors → partagés entre tous les projets, ultra protégé
- **Client (projet)** : Manifests, Instances → spécifiques au projet
- Les ressources partagées sont accessibles via API (pas de duplication)
- Tout enrichissement pour un client bénéficie au core pour tous

### Infrastructure

- 1 cube Ionos par client
- 1 docker par projet (isolation au sein du cube)
- Le core reste séparé, accessible par API

### Définitions clarifiées

| Terme | Définition |
|-------|------------|
| **Object** | Définition dans le schema (le type). Object est la racine, la fractale elle-même est Object |
| **Schema** | Structure définissant les types, attributs et relations possibles |
| **Seed** | Représentant du type, exemplaire de référence avec valeurs par défaut |
| **Template** | MetaTemplate personnalisé pour un cas d'usage, récursif agnostique, adapté au type |
| **Manifest** | Fichier de configuration qui, combiné au schema, produit l'instance |
| **Instance** | Schema + Manifest = Instance finale |

---

## 2. Héritage et valeurs

- La **première valeur** d'un attribut dans la chaîne d'héritage = valeur par défaut
- Chaque génération peut **override** les valeurs héritées (attribut `override = true` par défaut sur chaque Attribut)
- **Jamais de valeur vide** → placeholder défini au niveau initial
- Le placeholder peut être adaptatif quand il est défini par une méthode ou une règle
- Les **Rules** filtrent/paramètrent ce qui est hérité ou injecté (quasi invisibles, interviennent pour validation + définition capacities/permissions/cadre)

---

## 3. Identité et nommage

### Unicité

- **Nom unique par type**
- Exception pour **Entity** : dédoublonnage sur `name + firstname + email`
- Pas besoin d'UUID

### Alias

- Format automatique : `@SousTypeTypeName`
- Relation : `depends_on Type:SousType.Name`
- La règle de doublon sur Name garantit l'unicité des alias

### Nommage des objets

- Format : `Object:Type:SousTypeType` (ex: `Object:Scenario:ValidationScenario`)
- Jamais de pluriel dans les noms, on parle DU type ou de LA liste d'objets

---

## 4. Attributs

- Tout est objet, donc un attribut est un type d'objet
- Format : `Attribute.depends_on <ObjectTypeA> AND IN <ObjectTypeBList>`
- Les listes sont toujours des objets séparés (ex: `MilestoneList IN ProjectAttributeList`)
- Jamais de listes inline dans les attributs
- Attribut `override = true` par défaut (peut être mis à false)

---

## 5. Routes API

### Format standard

```
/api/<objecttype>/<centralmethod>/<secondarymethod>/<vector>?<token>
```

### Exemples

- `/api/project/update/switch/<project_id>?token=xxx`
- `/api/walker/execute/walk/<filter_id>?token=xxx`
- `/api/manifest/create/fromIdea/<idea_id>?token=xxx`

---

## 6. Scenarios et Pipelines

### Structure

- Un **Scenario** est exécuté par une ou plusieurs `Scenario:MilestoneScenario`
- Les **MilestoneScenario** portent les steps GEVR
- **Milestone** a un attribut `state` (pas l'inverse)
- **Milestone** porte l'attribut `questions` (QuestionList) permettant à l'agent IA de créer l'objet
- **Milestones sont génériques** à tous les Scenarios (pas seulement Projects)

### Pipeline Source

```
IdeaVector → BriefVector → SpecVector → ManifestVector
```

- On peut démarrer n'importe où
- On peut ne vouloir qu'un Brief ou qu'un Manifest
- Ce sont les objets Source qui portent la méthode Create
- `ManifestCreate` depuis Idea → son GET récupère Spec à partir de Idea
- `SpecCreate` → son GET récupère Brief à partir de Idea
- La pipeline s'exécute en cascade via les GET de chaque étape

### Question

```
Object:Question:
  .override = false  // par nature
  .compile = true    // si on veut
```

---

## 7. Plan B (sans IA)

- Chaque Scenario doit être exécutable sans IA (manuellement ou script)
- C'est le seul cas permettant de sauter directement à l'étape finale
- À définir plus tard mais à prévoir dans l'architecture

---

## 8. Validation de règle

- Outil unique agnostique de validation
- Prend n'importe quelle Rule
- Trouve les objets concernés
- Vérifie les conditions
- Rapporte l'état
- Les scenarios de validation serviront aussi pour les crons de maintenance

---

## 9. Cockpit

### Trois interfaces

- **Cockpit VSCode** (extension) → dans VSCode
- **Cockpit HTML** (navigateur) → standalone
- **Cockpit Admin** → module visible depuis le backoffice de l'agence

Tous utilisent la même API Python (serveur MRG), en ligne ET locale.

### Gestion des projets

- 5 derniers projets visibles
- Bouton "Ouvrir un projet" affiche la liste exhaustive des projets, classés par ordre inversement chronologique
- Bouton "Nouveau projet" (à paramétrer après définition des objets)
- Un projet = un dossier isolé (pas de mélange avec autres fichiers .gev)

### Connexion au serveur

- Le cockpit VSCode se connecte au serveur Python si disponible
- Fallback JS local si serveur non disponible
- Indicateur de status : "● Python API" (vert) ou "○ Local JS" (gris)

---

## 10. Logs

- Les logs sont incontournables dans 100% des cas
- C'est la méthode `call` qui s'en charge
- Tout hook provoque un log (même vide : "début", "fin", "arrêt")
- Pas d'attribut `log = true/false`, c'est systématique
