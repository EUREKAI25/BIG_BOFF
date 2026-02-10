# QUESTIONS_architecture_clarifications — Réponses pour l’agent IA
> Version réécrite entièrement avec la nouvelle règle officielle de lineage et d’accès.

Ce document fournit les réponses complètes et actualisées pour l’agent IA, afin de construire l’outil de modélisation (« Object Fractal Cockpit ») : définition des objets, héritages, schémas, règles, relations, lineages et tests.

Aucun traitement PPCM/PGCD n’est intégré dans cette version (il sera ajouté dans un Layer dédié plus tard).

---

# 0. Rôle de l’outil

L’outil sert à :
- créer / définir / éditer les **ObjectTypes**,
- définir les **schémas** (bundles + ElementList),
- poser les **attributs**, **règles ERK**, **relations**,
- définir et valider la **nomenclature** (lineage, nommage etc),
- visualiser la **fractale** (héritage, injection, structure),
- tester localement via une **console semi-réelle**.

Il aide l’architecte à structurer et concrétiser sa pensée dans un espace contrôlé, cohérent et sans oubli.

---

# 1. Règle OFFICIELLE — Lineage & Accès

## 1.1. Deux séparateurs : chacun un rôle STRICT

### **“ : ” = la généalogie fractale (structure parent → enfant)**

Il exprime la descendance :
```
Parent:Child
Parent:Child:GrandChild
```

Il construit l’arbre fractal interne.

### **“ . ” = l’accès interne (éléments, attributs, méthodes)**

Il exprime ce que contient l’objet :
```
Object.element
Object.attribute
Object.method()
Object.method(params)
```

### **LES DEUX COMBINÉS**
```
Parent:Child.attribute
Parent:Child.method()
Parent:Child.bundle.element
Parent:Child.method(params)
```

Exemples :
```
L0:Core:Object.name
L3:Library:Schema:Project.structure.fields.add()
L5:Entities:Agent:TechLead.permissions.get("edit")
L4:Scenario:Onboarding.steps[2].validate()
```

RÈGLE À RETENIR :
- **“ : ” = structure / famille**
- **“ . ” = contenu / action**

---

# 2. Planes IVC × DRO

Ces 6 plans sont :
- **structurels** (internes au MetaSchema),
- **non édités directement** dans l’UI,
- **visibles en lecture** via la fractale.

Les plans :
- Identity
- View
- Context
- Definition
- Rule
- Option

Chaque ObjectType projette ses éléments sur ces plans dans son modèle interne.

---

# 3. Relations canoniques (version figée)

Les trois relations autorisées :
- **inherits_from** : héritage fractal officiel
- **depends_on** : dépendance structurelle
- **related_to** : lien sémantique

Aucune autre relation n’existe, mais des alias sont automatiquement générés.
Dès que objectA depends_on objectB ou objectA related_to objectB ça crée   Alias:objectA_of depends_on Relation:related_to ou Alias:objectA_of Relation:related_to

---

# 4. Nomenclature du lineage

## 4.1. Structure canonique

La structure canonique combine :

- « : » pour la généalogie (parent → enfant)
- « . » pour l’accès interne (attributs et méthodes)

### Formes possibles :

```
<ParentObjectType>:<ChildObjectType>.<Attribute>
```

```
<ParentObjectType>:<ChildObjectType>.<Method>
```

```
<ParentObjectType>:<ChildObjectType>.<Method>()
```

```
<ParentObjectType>:<ChildObjectType>.<Method>(<params>)
```

### Déclinaisons sur plusieurs niveaux :

```
<A>:<B>:<C>.<Attribute>
```

```
<A>:<B>:<C>.<Method>()
```

```
<A>:<B>:<C>.<Method>(<params>)
```

### Déclinaisons internes supplémentaires :

```
<A>:<B>.bundle.<element>
```

```
<A>:<B>.structure.<field>.add()
```

```
<A>:<B>.<method>(<params>)
```

```
<A>:<B>.<attribute>
```


Exemples :
```
Object:Entity:User:userX.name
Entity:Agent:TechLeadAgent.create(<ObjectVector>)
```

## 4.2. Regex stricte
```

- Segment d’objet (généalogie) :  
  `OBJ = [A-Z][A-Za-z0-9]*`

- Segment interne (attribut ou méthode, sans paramètres) :  
  `INT = [a-z][A-Za-z0-9]*`
```

**Lineage complet (0 → n ascendants, 0 → n attributs/méthodes)**
```regex
^([A-Z][A-Za-z0-9]*)(:[A-Z][A-Za-z0-9]*)*(\.[a-z][A-Za-z0-9]*)*$
```

## 4.3. Contraintes imposées à l’outil
- autocomplétion obligatoire,
- validation à la saisie,
- création assistée des parents intermédiaires (option future).

---

# 5. Définition opérationnelle du vecteur

Un vecteur est l’**unité centrale** du langage interne.

### Structure type :
```json
{
  "lineage": "Entity:Agent:AIAgent",
  "plane": "Definition",
  "payload": {
    "schema": {},
    "rules": [],
    "relations": []
  },
  "meta": {
    "version": "1.0.0",
    "state": "draft"
  }
}
```

Un vecteur est :
- lisible,
- exécutable,
- transportable,
- auto-descriptif.

---

# 6. Fonctionnalités de l’outil

## 6.1. Panel A – Explorateur de lineages
- navigation,
- création,
- duplication,
- renommage,
- suppression,
- autocomplétion.

## 6.2. Panel B – Tags, catégories, alias
- organisation transversale,
- filtres,
- grouping.

## 6.3. Panel C – Éditeur de schéma
- bundle + ElementList,
- attributs et types,
- règles ERK,
- relations,
- projection IVC×DRO (automatique),
- génération catalogue.

## 6.4. Panel D – Vue fractale + console
- héritage fractal,
- injection / diffusion,
- coloration planes,
- console semi-réelle pour tester règles et méthodes.

---

# 7. Console semi-réelle : règles

- Aucun appel externe.
- Pas de création d’artefacts système.
- Évaluation de :
  - règles ERK,
  - MetaSchema,
  - contraintes,
  - cohérence interne,
  - relations.
- Retour sous forme :
```json
{
  "status": "ok|error",
  "messages": [],
  "outputs": {}
}
```

---

# 8. Architecture technique

Modèle hybride :
- **Front statique** (HTML/JS)
- **Backend minimal** pour :
  - parsing ERK,
  - validate MetaSchema,
  - générer fractales,
  - gérer catalogues.

---

# 9. Hypothèses validées

1. IVC×DRO visibles en lecture, non éditables.
2. Relations : uniquement depends_on / related_to / inherits_from.
3. Lineage strict (regex + autocomplétion).
4. Vecteur = lineage + plane + payload + meta.
5. Console = semi-réelle.
6. L’outil ne gère pas encore PPCM/PGCD.
7. Méthodes = récursives, objets = bundles.

---

# 10. Résumé pour implementation

L’outil doit permettre :

- création et édition des ObjectTypes,
- gestion des relations canoniques,
- nomenclature strictement validée,
- visualisation fractale complète,
- tests locaux via console,
- cohérence avec :
  - MetaSchema,
  - ERK,
  - Formulas.

Fin du document.
