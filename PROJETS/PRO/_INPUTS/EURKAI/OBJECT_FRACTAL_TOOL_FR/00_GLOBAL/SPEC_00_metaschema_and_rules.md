# SPEC 00 — Metaschema & Règles (VERSION NATHALIE)

Ce fichier définit le **MetaSchema** global et les règles de base nécessaires à l’Object Fractal Tool.

---

# 1. MetaSchema global

## DESCRIPTION
MetaSchema définit la structure récursive canonique de tous les ObjectTypes.

## STRUCTURE ELEMENTLIST
Chaque Plan (Identity, View, Context, Definition, Rule, Option) contient un ElementList :

ElementList :
  AttributeList :
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  RelationList :
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  MethodList :
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  RuleList :
    - inherited_bundle
    - injected_bundle
    - owned_bundle

## SÉMANTIQUE DES BUNDLES
- **inherited_bundle** : contenu hérité des ObjectTypes parents.
- **injected_bundle** : contenu injecté dynamiquement (providers, environnement, injections basées sur le lineage, etc.).
- **owned_bundle** : contenu défini directement pour l’ObjectType lui-même.

## INTÉGRATION AU SCHEMACATALOG
Chaque ObjectType déploie le MetaSchema en remplissant ses Bundles avec :
- AttributeBundle = {inherited / injected / owned}
- RelationBundle  = {inherited / injected / owned}
- MethodBundle    = {inherited / injected / owned}
- RuleBundle      = {inherited / injected / owned}

## VUE JSON SIMPLIFIÉE
```json
{
  "MetaSchema": {
    "ElementList": {
      "AttributeList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "RelationList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "MethodList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "RuleList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      }
    }
  }
}
```

Compléments à préciser par Nathalie :
- Les différents **Planes** (Identity, View, Context, Definition, Rule, Option) et leur rôle exact.
- Comment chaque Plane se projette dans la structure concrète d’un ObjectType.
- Comment X et XFractal sont liés dans la pratique (clé de référence, stockage, etc.).

---

# 2. Nomenclature des lineages & regex

À compléter par Nathalie :

- Décrire ici la **nomenclature** des lineages (structure, séparateurs, conventions).
- Ajouter la **regex officielle** qui valide tout lineage.

Format suggéré :
- Explication en langage naturel (exemples).
- Regex :

```regex
^VOTRE_REGEX_ICI$
```

---

# 3. Relations fondamentales

Nathalie doit définir ici :
- Les **3 relations fondamentales** (nom, sens, sémantique).
- Pour chacune :
  - Nom canonique.
  - Direction (A→B, B→A ou bidirectionnelle).
  - Signification dans la fractale (composition ? dépendance ? association ?).
  - Impact éventuel sur l’héritage ou XFractal.

Exemples de champs à remplir :
- Relation 1 :
  - nom :
  - description :
  - direction :
  - alias possibles :
- Relation 2 :
  - …
- Relation 3 :
  - …

---

# 4. Méta-logiques (optionnel mais recommandé)

Si souhaité, lister ici les **familles de méta-logiques** (conditionnelle, temporelle, associative, identitaire, structurelle, événementielle, évaluative, etc.).

Pour chaque famille :
- Nom.
- Description simple.
- Effet typique sur un ObjectType (attributs injectés, méthodes secondaires ajoutées, types de règles ERK associés).

Ces familles serviront ensuite de base pour les logiques transversales (injected_bundle).
