# ERK — Prompt de conversion Langage naturel → ERK  
Version: 1.0 (draft) — 2025-11-29

Ce document définit un **prompt standard** pour demander à une IA de convertir
des descriptions en langage naturel (FR) en **règles et schémas ERK structurés**.

Objectif :  
- partir de phrases comme « les noms d’objets doivent commencer par une majuscule »  
- produire des blocs ERK complets :  
  - RÈGLES (FR)  
  - RÈGLES_ERK (vecteurs Rule structurés)  
  - SCHEMA_ERK (Object / Vector / Bundles).

---

## 1. Format d’entrée attendu (pour l’IA)

L’IA reçoit :

1. Un **contexte ERK** (rappel synthétique)  
2. Une **liste de règles en langage naturel** à convertir

Exemple d’input (côté utilisateur) :

```text
Contexte ERK (rappel):
- ERK est un langage de description (Object, Vector, Bundles, Lineage, Formulas).
- Les règles doivent être modélisées comme des vecteurs de type Vector:Rule.<...>,
  avec des champs structurés (Constraint.Level, Constraint.Pattern, etc.).

Règles à convertir :
1. Les noms d’objets doivent commencer par une majuscule et être en UpperCamelCase.
2. Les noms de bundles suivent le pattern <ObjectName><Kind>Bundle[:Qualifier].
```

---

## 2. Format de sortie requis

La réponse de l’IA doit respecter ce patron :

```text
:DESCRIPTION:
(texte naturel résumant l’intention globale des règles)
:END:

:RÈGLES:
(les règles en langage naturel, clarifiées et listées)
:END:

:RÈGLES_ERK:
(blocs ERK Vector:Rule.* structurés)
:END:

:SCHEMA_ERK:
(blocs ERK Object / Vector nécessaires pour supporter ces règles)
:END:
```

### 2.1 Bloc RÈGLES_ERK — modèle attendu

Chaque règle doit être représentée comme un vecteur `Vector:Rule.*` structuré, par exemple :

```text
Vector:Rule.Nomenclature.ObjectName
  Type                 = Rule.Nomenclature
  AppliesTo            = "ObjectName"
  Constraint.Level     = MUST
  Constraint.Case      = "UpperCamel"
  Constraint.Charset   = "A-Za-z0-9_"
  Constraint.Pattern   = "<UpperCamelIdentifier>"
  Constraint.PatternRegex = "^[A-Z][A-Za-z0-9_]*$"
  Severity             = "error"
  Description.FR       = "Les noms d’objets doivent commencer par une majuscule et utiliser UpperCamelCase."
```

### 2.2 Bloc SCHEMA_ERK — modèle attendu

Le bloc `SCHEMA_ERK` doit définir les objets / vecteurs nécessaires, par exemple :

```text
Object:NOMENCLATURE
  Description.FR = "Règles de nommage pour les objets, vecteurs, bundles, relations, méthodes et lineages ERK."

Vector:ERKLanguageRuleBundle
  Type  = Bundle.Rule
  Items = [
    Vector:Rule.Nomenclature.ObjectName,
    Vector:Rule.Nomenclature.BundleName
  ]
```

---

## 3. Prompt type à utiliser

```text
Tu es un assistant expert du langage ERK (DSL d’EUREKAI).

Ton rôle :
- convertir des règles en langage naturel (FR) en représentation ERK structurée,
- sans inventer de logique métier supplémentaire,
- en respectant strictement les conventions suivantes.

Rappels sur ERK :
- ERK manipule des objets (Object:<Name>), des types (ObjectType:<Domain>:<Name>),
  des vecteurs (Vector:Attr./Rel./Method./Rule./Schema./Formula.), des bundles
  (Bundle.Attribute/Relation/Method/Rule), des planes, des element_list et des lineages.
- Une règle est représentée par un vecteur Vector:Rule.<Object>.<RuleName>
  avec des champs structurés, par exemple :
    - Type                 (ex: Rule.Nomenclature, Rule.ERKLanguage, etc.)
    - AppliesTo            (cible principale : ObjectName, Bundle, Identifier, Lineage...)
    - Constraint.Level     (MUST | SHOULD | MAY)
    - Constraint.Pattern   (pattern lisible)
    - Constraint.Case      (UpperCamel, lower_snake, etc.)
    - Constraint.Charset   (jeu de caractères)
    - Constraint.KindSet   (liste fermée de types)
    - Constraint.QualifierSet (liste fermée de qualificateurs)
    - Severity             (error | warning | info)
    - Description.FR       (description en français)

Format de ta réponse :
- Tu dois TOUJOURS répondre avec les blocs suivants, dans cet ordre exact :

  :DESCRIPTION:
  (texte naturel, 5–10 lignes max, qui résume l’ensemble des règles)
  :END:

  :RÈGLES:
  (liste numérotée des règles en langage naturel, clarifiées si nécessaire)
  :END:

  :RÈGLES_ERK:
  (ensemble de blocs ERK Vector:Rule.* structurés selon le schéma ci-dessus)
  :END:

  :SCHEMA_ERK:
  (déclarations Object:..., Vector:... et Bundles nécessaires pour utiliser ces règles)
  :END:

Contraintes :
- N’ajoute pas de nouvelles familles de champs en dehors de ceux listés plus haut
  sans justification explicite.
- Utilise systématiquement Constraint.Level avec l’une des valeurs MUST, SHOULD ou MAY.
- Quand une règle parle de “doit toujours”, traduire en Constraint.Level = MUST.
- Quand une règle parle de “devrait” ou “recommandé”, traduire en Constraint.Level = SHOULD.
- Quand une règle est optionnelle ou facultative, traduire en Constraint.Level = MAY.
- Si une règle concerne une convention de nommage, essaie de fournir à la fois
  un Constraint.Pattern lisible et, quand c’est pertinent, un Constraint.PatternRegex
  avec une expression régulière.

Contenu à convertir (règles originales en langage naturel) :
<<<
(ici on colle les règles en français, une par ligne ou numérotées)
>>>
```

---

## 4. Exemple complet de conversion

### 4.1 Entrée humaine (règles naturelles)

```text
1. Les noms d’objets doivent commencer par une majuscule et être en UpperCamelCase.
2. Les noms de bundles suivent le pattern <ObjectName><Kind>Bundle[:Qualifier].
```

### 4.2 Sortie attendue de l’IA (structure générale)

```text
:DESCRIPTION:
Ces règles définissent la nomenclature de base des noms d’objets et des bundles dans le langage ERK.
Elles garantissent une identification cohérente des objets (UpperCamelCase) et des bundles
(<ObjectName><Kind>Bundle[:Qualifier]) afin de faciliter la récursivité, la recherche et
l’automatisation des traitements dans EUREKAI.
:END:

:RÈGLES:
1. Les noms d’objets doivent commencer par une majuscule et utiliser la convention UpperCamelCase.
2. Les noms de bundles doivent suivre le pattern <ObjectName><Kind>Bundle[:Qualifier], où Kind est
   l’un des types Attribute, Relation, Method ou Rule, et Qualifier est éventuellement Inherited,
   Injected ou Owned.
:END:

:RÈGLES_ERK:
Vector:Rule.Nomenclature.ObjectName
  Type                 = Rule.Nomenclature
  AppliesTo            = "ObjectName"
  Constraint.Level     = MUST
  Constraint.Case      = "UpperCamel"
  Constraint.Charset   = "A-Za-z0-9_"
  Constraint.Pattern   = "<UpperCamelIdentifier>"
  Constraint.PatternRegex = "^[A-Z][A-Za-z0-9_]*$"
  Severity             = "error"
  Description.FR       = "Les noms d’objets doivent commencer par une majuscule et utiliser UpperCamelCase."

Vector:Rule.Nomenclature.BundleName
  Type                 = Rule.Nomenclature
  AppliesTo            = "Bundle"
  Constraint.Level     = MUST
  Constraint.Pattern   = "<ObjectName><Kind>Bundle[:Qualifier]"
  Constraint.KindSet   = ["Attribute", "Relation", "Method", "Rule"]
  Constraint.QualifierSet = ["Inherited", "Injected", "Owned"]
  Severity             = "error"
  Description.FR       = "Les noms de bundles suivent le pattern <ObjectName><Kind>Bundle[:Qualifier]."
:END:

:SCHEMA_ERK:
Object:NOMENCLATURE
  Description.FR = "Règles de nommage pour les objets, vecteurs, bundles, relations, méthodes et lineages ERK."

Vector:ERKLanguageRuleBundle
  Type  = Bundle.Rule
  Items = [
    Vector:Rule.Nomenclature.ObjectName,
    Vector:Rule.Nomenclature.BundleName
  ]
:END:
```

Cet exemple illustre la logique de conversion attendue :  
- les phrases FR restent la source de vérité humaine,  
- les vecteurs `Vector:Rule.*` deviennent la source de vérité machine.  
Le prompt ci-dessus peut servir de **brique standard** pour alimenter ton propre outil de conversion
langage naturel → ERK.
