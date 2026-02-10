# ERK — Langage propriétaire EUREKAI  
Version: 1.0 (draft) — 2025-11-29

Ce document définit la **spécification de base du langage ERK** utilisé par EUREKAI pour :  

- décrire la structure du système (layers, planes, element_list, schemas),  
- adresser les objets via un **lineage hiérarchique**,  
- exprimer des **requêtes structurées** sur les objets et leurs relations,  
- définir des **règles** et **contraintes** sous forme de vecteurs structurés,  
- s’articuler avec les **formules propriétaires** (FORMULAS) sans dépendre d’un langage d’exécution
  particulier (Python, JS, etc.).  

ERK est **agnostique du runtime** et sert uniquement de couche de description / articulation.

---

## 1. Scope & principes

### 1.1 Objectif d’ERK

`Object:ERK_Language`  
`Description.FR = "Langage propriétaire de description du système EUREKAI (planes, element_list, lineage, requêtes, règles, formules)."`

ERK sert à :

- décrire les objets et leurs types (Object, ObjectType, SchemaCatalog),  
- décrire les vecteurs associés (Attr, Rel, Method, Rule, Schema, Formula…),  
- définir la position fractale des objets (planes, element_list, lineage),  
- exprimer des requêtes structurées sur la fractale,  
- définir des règles / contraintes de façon **structurée**, pas en texte libre,  
- connecter ces objets / vecteurs aux **FORMULAS** (formules propriétaires universelles).

### 1.2 Conventions générales

- Les fichiers ERK utilisent l’extension `.erk`.
- Un fichier ERK est composé de blocs structurés, en texte lisible, sans indentation obligatoire
  pour le parseur, mais l’indentation est utilisée pour la lisibilité humaine.
- Les commentaires peuvent être notés avec `--` en début de ligne.

Exemple de bloc simple :

```text
Object:ExampleObject
  Description.FR = "Objet d’exemple."
```

---

## 2. Lexique & éléments de base

ERK repose sur un ensemble de **préfixes** et de **types de vecteurs** stables.  
Ce dictionnaire définit les briques fondamentales du langage.

### 2.1 Objets & types d’objets

- `Object:<Name>`  
  Représente un objet logique du système (MetaSchema, SchemaCatalog, ERKLanguage, Unit, Formula…).  
  - `<Name>` est en `UpperCamelCase` (ex: `MetaSchema`, `SchemaCatalog`, `ERKLanguage`).

- `ObjectType:<Domain>:<Name>`  
  Définit un *type d’objet* (ex: `ObjectType:Measure:Unit`, `ObjectType:ERK:MetaGrammar`).

- `SchemaCatalog:ObjectType:<Domain>:<Name>`  
  Associe un ObjectType à la liste de ses bundles (attributes, relations, methods, rules).

Exemple (issu de FORMULAS) :

```text
ObjectType:Measure:Unit

Object:Unit
  Description.FR = "Unité de mesure."

SchemaCatalog:ObjectType:Measure:Unit
  ElementList:
    AttributeBundle = Vector:UnitAttributeBundle
    RelationBundle  = Vector:UnitRelationBundle
    MethodBundle    = Vector:UnitMethodBundle
    RuleBundle      = Vector:UnitRuleBundle
```

### 2.2 Vecteurs (Vector:…)

Les vecteurs sont les “atomes” adressables : attributs, relations, méthodes, règles, schemas, formules.

Préfixes principaux :

- `Vector:Attr.<Object>.<Name>`  
- `Vector:Rel.<Object>.<Name>[.<Target>]`  
- `Vector:Method.<Object>.<Action>`  
- `Vector:Rule.<Object>.<RuleName>`  
- `Vector:Schema.<Object>.<SchemaName>`  
- `Vector:Formula.<Name>` ou `Vector:Formula<Name>` (selon conventions FORMULAS)  
- `Vector:<ObjectName>AttributeBundle`  
- `Vector:<ObjectName>RelationBundle`  
- `Vector:<ObjectName>MethodBundle`  
- `Vector:<ObjectName>RuleBundle`  

**Règle :** la première partie (`Attr.`, `Rel.`, `Method.`, `Rule.`, `Schema.`, `Formula.`) exprime la **famille** du vecteur.  
Son rôle (attribut, relation, méthode, etc.) est donc déductible du simple préfixe.

### 2.3 Bundles

Un *bundle* est un vecteur qui regroupe une liste d’autres vecteurs du même type (attributes, relations…)

```text
Vector:<ObjectName>AttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.<ObjectName>.<Attribute1>,
    Vector:Attr.<ObjectName>.<Attribute2>
  ]

Vector:<ObjectName>RelationBundle
  Type  = Bundle.Relation
  Items = [
    Vector:Rel.<ObjectName>.<RelationName>.<Target>
  ]

Vector:<ObjectName>MethodBundle
  Type  = Bundle.Method
  Items = [
    Vector:Method.<ObjectName>.<ActionName>
  ]

Vector:<ObjectName>RuleBundle
  Type  = Bundle.Rule
  Items = [
    Vector:Rule.<ObjectName>.<RuleName>
  ]
```

Des sous-bundles peuvent être ajoutés avec un qualificateur `:Inherited`, `:Injected`, `:Owned` :

```text
Vector:<ObjectName>AttributeBundle:Inherited
Vector:<ObjectName>AttributeBundle:Injected
Vector:<ObjectName>AttributeBundle:Owned
```

### 2.4 Planes & element_list

Un *plane* est une “couche logique” de la fractale (core, meta_core, security…).  
Chaque plane a un `element_list` listant les sous-éléments qu’il contient.

Exemple de définition (inspirée de NOMENCLATURE / ERK_LANGAGE) :

```text
system.element_list = [
  core REQUIRED,
  meta_core REQUIRED,
  security REQUIRED,
  rules_central_supertools REQUIRED,
  secondary_methods REQUIRED,
  library REQUIRED,
  entities REQUIRED,
  agency REQUIRED,
  ai REQUIRED,
  erk_language REQUIRED
] IN system.definition
```

La syntaxe `IN <scope>.<slot>` ancre la liste dans un scope précis.

### 2.5 Lineage

Un **lineage ERK** est une chaîne hiérarchique de segments séparés par des points :

```text
Example.Lineage.1 = html.body.container.section.module.front
Example.Lineage.2 = system.core.meta_core.security.rules_central_supertools
```

- chaque segment est un identifiant logique (layer, objet, slot…),  
- plus le lineage est long, plus l’objet est précis,  
- un lineage peut être complet (objet concret) ou partiel (pattern).

---

## 3. Requêtes ERK

ERK dispose d’une mini-syntaxe de requêtes structurées.

### 3.1 Patron général

```text
<pattern> ATTRIBUTE[<Attr1>, <Attr2>, …]
```

Exemple (issu d’ERK_LANGAGE) :

```text
*.element_list.* ATTRIBUTE[class, id, data]
```

Signification :

- `*.element_list.*` : tous les `element_list` de tous les scopes,  
- `ATTRIBUTE[...]` : projection des attributs demandés (`class`, `id`, `data`).

La logique expressive complète des requêtes est définie par :

- un **pattern de cible** (lineage ou wildcard),  
- une **projection** (`ATTRIBUTE[...]`),  
- éventuellement un **scope** (`IN <scope>.<slot>`),  
- éventuellement des **conditions** (filtres) à formaliser via des vecteurs de type Rule/Formula.

---

## 4. Modélisation des règles & contraintes

### 4.1 Principe

Une règle ERK n’est *pas* une phrase floue ; c’est un **vecteur structuré** de type `Rule`.  
La phrase en langage naturel (FR) est **un attribut de description**,  
mais la logique exploitable doit être dans des champs structurés.

Exemple de modèle générique :

```text
Vector:Rule.Nomenclature.ObjectName
  Type                 = Rule.Nomenclature
  AppliesTo            = "ObjectName"
  Constraint.Level     = MUST         -- MUST | SHOULD | MAY
  Constraint.Case      = "UpperCamel"
  Constraint.Charset   = "A-Za-z0-9_"
  Constraint.Pattern   = "^[A-Z][A-Za-z0-9_]*$"
  Severity             = "error"      -- error | warning | info
  Description.FR       = "Les noms d’objets doivent commencer par une majuscule et utiliser UpperCamelCase."
```

Ici :

- `Constraint.Level` formalise les notions de **MUST / SHOULD / MAY** (vocabulaire autorisé ERK).  
- `Constraint.*` regroupe les différents paramètres de la contrainte.  
- `Severity` permet de distinguer une contrainte bloquante d’un simple warning.

### 4.2 Exemple pour les bundles

```text
Vector:Rule.Nomenclature.BundleName
  Type               = Rule.Nomenclature
  AppliesTo          = "Bundle"
  Constraint.Level   = MUST
  Constraint.Pattern = "<ObjectName><Kind>Bundle[:Qualifier]"
  Constraint.KindSet = ["Attribute", "Relation", "Method", "Rule"]
  Constraint.QualifierSet = ["Inherited", "Injected", "Owned"]
  Description.FR     = "Les noms de bundles suivent le pattern <ObjectName><Kind>Bundle[:Qualifier]."
```

### 4.3 Règles globales d’identifiants

On peut définir un bundle de règles :

```text
Vector:ERKLanguageRuleBundle
  Type  = Bundle.Rule
  Items = [
    Vector:Rule.ERKLanguage.ValidIdentifier,
    Vector:Rule.ERKLanguage.ValidLineage,
    Vector:Rule.ERKLanguage.ValidElementList,
    Vector:Rule.ERKLanguage.ValidQuery
  ]
```

Chaque `Vector:Rule.ERKLanguage.*` est défini avec le même schéma que ci-dessus.

---

## 5. Intégration avec les FORMULAS

Le fichier `FORMULAS` définit le **socle des formules universelles** (time, space, math, structure).  
ERK ne redéfinit pas le contenu mathématique des formules, mais fournit le **format standard** pour les référencer.

### 5.1 Objet FORMULAS

```text
Object:FORMULAS
  Description.FR = "Socle des formules universelles (time, space, math, structure) et de leurs unités."
```

### 5.2 Schéma minimal d’une formule

Une formule est vue comme un `Object:Formula` avec un schema standard :

```text
ObjectType:Formula:Generic

Object:MetaFormula
  Description.FR = "Structure générale d’une formule (nom, catégorie, signature, literal)."

SchemaCatalog:ObjectType:Formula:Generic
  ElementList:
    AttributeBundle = Vector:MetaFormulaAttributeBundle
    RelationBundle  = Vector:MetaFormulaRelationBundle
    MethodBundle    = Vector:MetaFormulaMethodBundle
    RuleBundle      = Vector:MetaFormulaRuleBundle

Vector:MetaFormulaAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.MetaFormula.Name,
    Vector:Attr.MetaFormula.VectorIdent,
    Vector:Attr.MetaFormula.Category,
    Vector:Attr.MetaFormula.InputType,
    Vector:Attr.MetaFormula.OutputType,
    Vector:Attr.MetaFormula.Literal,
    Vector:Attr.MetaFormula.DescriptionFR
  ]
```

Une formule concrète comme `ISNULL` se décrit alors ainsi :

```text
Object:FormulaISNULL
  Description.FR = "Retourne TRUE si la valeur est nulle, sinon FALSE."

Vector:Attr.MetaFormula.Name
  Value = "ISNULL"

Vector:Attr.MetaFormula.VectorIdent
  Value = "Vector:FormulaISNULL"

Vector:Attr.MetaFormula.Category
  Value = "FormulaCategory:EXISTENCE"

Vector:Attr.MetaFormula.InputType
  Value = "Any"

Vector:Attr.MetaFormula.OutputType
  Value = "Boolean"
```

ERK permet simplement :

- d’énumérer les formules disponibles,  
- de typer leurs entrées / sorties,  
- de les attacher à des objets ou des règles via des `Vector:Relation.*` ou `Vector:Rule.*`.

---

## 6. Mapping structurel & fractal

Le document `ERK_STRUCTURE_MAPPING_DOC` définit un mini-langage pour décrire la **structure d’un type d’objet** :

- `element_list` (composition / récursivité),  
- ancrage dans la double fractale (planes IVC × DRO),  
- règles d’attributes globales,  
- requêtes haut niveau.

ERK fournit la grammaire de base pour :

- déclarer un **object type** (`ObjectType:…`),  
- déclarer son **schema** (`SchemaCatalog:ObjectType:…`),  
- référencer des bundles et des vecteurs,  
- décrire les mappings dans des fichiers `.erk` dédiés.

---

## 7. Dictionnaire ERK v1 (briques stables)

Cette section liste les **mots-clés et familles** stables du langage ERK
(tout ce qui structure le langage lui‑même, pas les objets métier).

### 7.1 Préfixes / familles

- `Object:` — déclaration d’un objet.  
- `ObjectType:` — déclaration d’un type d’objet.  
- `SchemaCatalog:` — association ObjectType → Bundles.  
- `Vector:Attr.` — attribut.  
- `Vector:Rel.` — relation.  
- `Vector:Method.` — méthode.  
- `Vector:Rule.` — règle / contrainte.  
- `Vector:Schema.` — schéma / template.  
- `Vector:Formula.` — vecteur représentant une formule.  
- `Bundle.Attribute` — type de bundle d’attributs.  
- `Bundle.Relation` — type de bundle de relations.  
- `Bundle.Method` — type de bundle de méthodes.  
- `Bundle.Rule` — type de bundle de règles.

### 7.2 Champs standards pour les règles

- `Type` — type logique du vecteur (Rule.Nomenclature, Rule.ERKLanguage, etc.).  
- `AppliesTo` — cible principale (ObjectName, Bundle, Identifier, Lineage…).  
- `Constraint.Level` — valeurs autorisées : MUST, SHOULD, MAY.  
- `Constraint.Pattern` — pattern lisible (ex: `<ObjectName><Kind>Bundle[:Qualifier]`).  
- `Constraint.Case` — convention de casse (UpperCamel, lower_snake, etc.).  
- `Constraint.Charset` — jeu de caractères autorisés.  
- `Constraint.KindSet` — liste fermée de types autorisés.  
- `Constraint.QualifierSet` — liste fermée de qualificateurs.  
- `Severity` — valeurs autorisées : error, warning, info.  
- `Description.FR` — description en langage naturel.

### 7.3 Champs standards pour les formules

- `VectorIdent` — identifiant de vecteur (`Vector:FormulaXXX`).  
- `Name` — nom court de la formule (`ISNULL`, `ABS`, `ROUND`, etc.).  
- `Category` — catégorie fonctionnelle (`FormulaCategory:EXISTENCE`, `:ARITHMETIC`, etc.).  
- `InputType` — type d’entrée (Any, Number, Boolean, DateTime…).  
- `OutputType` — type de sortie.  
- `Literal` — représentation textuelle ou expression interne.  
- `Description.FR` — description en français.

---

## 8. Résumé

ERK est un **DSL minimal** pour :

- décrire les objets, vecteurs et bundles,  
- structurer la fractale (planes, element_list, lineage),  
- exprimer des requêtes sur les objets,  
- définir des règles comme **vecteurs structurés** (avec `Constraint.*`, `Severity`, etc.),  
- référencer des **formules propriétaires** via un schéma standard.

Tout ce qui concerne la logique métier, les événements (`Vector:Event.*`), les hooks, etc.  
est **adressable** dans ERK (via leurs vecteurs), mais **n’appartient pas** au langage ERK lui‑même :  
ERK se contente de fournir la grammaire qui permet de les décrire et de les combiner.
