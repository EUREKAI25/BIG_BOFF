# QUESTIONS — Clarifications pour l'architecture Object Fractal Tool

## 1. Structure des Plans (IVC × DRO)

Les 6 Plans sont mentionnés (Identity, View, Context, Definition, Rule, Option) mais leur articulation reste floue :

- **Q1.1** : Chaque ObjectType possède-t-il les 6 Plans simultanément, ou certains Plans sont-ils optionnels selon le type ?
- **Q1.2** : Le MetaSchema avec ses ElementLists (Attribute, Relation, Method, Rule) s'applique-t-il **à chaque Plan individuellement** ou **une seule fois au niveau de l'ObjectType** ?
- **Q1.3** : Y a-t-il une hiérarchie entre Plans ? (ex: Identity prime sur View, Definition contraint Rule…)

---

## 2. Relation X ↔ XFractal

- **Q2.1** : XFractal est-il un **objet distinct** avec son propre ID, ou une **vue calculée** à la demande sur X ?
- **Q2.2** : XFractal est-il stocké en JSON à côté de X, ou généré dynamiquement par résolution de l'héritage ?
- **Q2.3** : Si XFractal est stocké, à quelle fréquence est-il recalculé ? (à chaque modification d'un ancêtre ?)

---

## 3. Nomenclature des lineages

Le document mentionne une regex à définir :

- **Q3.1** : Quel est le séparateur de lineage ? (`.` comme `Root.Category.SubType` ? `/` ? `::` ?)
- **Q3.2** : Y a-t-il des segments réservés ou interdits ? (ex: pas de chiffres en début ?)
- **Q3.3** : Le lineage encode-t-il uniquement l'héritage, ou aussi d'autres informations (version, scope…) ?
- **Q3.4** : Exemple concret d'un lineage valide à 3+ niveaux ?

---

## 4. Les 3 relations fondamentales

Le spec mentionne "3 relations fondamentales, le reste en alias" :

- **Q4.1** : Quelles sont ces 3 relations ? (composition, dépendance, association ? parent-child, uses, implements ?)
- **Q4.2** : Un alias est-il simplement un renommage d'une relation fondamentale, ou peut-il combiner plusieurs relations ?
- **Q4.3** : Les relations sont-elles typées avec cardinalité ? (1:1, 1:N, N:N)

---

## 5. Injection et logiques transversales

- **Q5.1** : Qu'est-ce qui déclenche une injection ? (présence d'un tag ? appartenance à une catégorie ? lineage match via pattern ?)
- **Q5.2** : Les injections sont-elles déclarées dans un fichier/objet séparé (style "providers") ou inline dans chaque ObjectType ?
- **Q5.3** : Priorité en cas de conflit : owned > injected > inherited ? Ou autre ordre ?

---

## 6. Schémas de Bundle

- **Q6.1** : Un schéma de Bundle définit-il les éléments **attendus** (validation) ou **possibles** (contrainte souple) ?
- **Q6.2** : Le schéma peut-il imposer des types d'éléments enfants ? (ex: "ce Bundle ne peut contenir que des Attributes")
- **Q6.3** : Les quantités (min/max) sont-elles définies par type d'élément ou globalement ?

---

## 7. Règles ERK

- **Q7.1** : Que signifie ERK ? (Enable-Require-Kill ? Autre acronyme ?)
- **Q7.2** : Une règle ERK s'applique-t-elle à un élément, à un Bundle, ou à l'ObjectType entier ?
- **Q7.3** : Format attendu d'une règle ? (condition → action ? expression logique ?)

---

## 8. Console de test

- **Q8.1** : L'expression `methodA(inputs).result.message` suppose un **runtime d'exécution**. Les méthodes sont-elles :
  - De simples déclarations (signature + description) ?
  - Du code exécutable (JS embarqué) ?
  - Des références à des fonctions externes ?
- **Q8.2** : Le test se fait-il sur des **instances** concrètes ou sur le **type** (simulation) ?

---

## 9. Étapes 01-04

Le prompt mentionne des étapes 01, 02, 03, 04 à intégrer :

- **Q9.1** : Peux-tu lister brièvement ce que chaque étape couvre ? (ex: 01 = lineages, 02 = fractale, 03 = tags, 04 = console ?)
- **Q9.2** : Ces étapes sont-elles séquentielles (chaque étape dépend de la précédente) ou parallélisables ?

---

## 10. Données initiales

- **Q10.1** : Y a-t-il un ObjectType "racine" (Root, Object, Entity…) dont tous les autres héritent ?
- **Q10.2** : Faut-il prévoir des ObjectTypes "système" pré-définis ? (ex: Attribute, Method, Rule comme ObjectTypes eux-mêmes ?)
- **Q10.3** : Le catalogue d'instances (vecteurs) est-il dans le même fichier JSON que les types, ou séparé ?

---

## Résumé des priorités

Pour avancer sur l'architecture, les questions **critiques** sont :
1. Q2 (relation X/XFractal — stockage vs calcul)
2. Q3 (nomenclature lineage — besoin de la regex)
3. Q4 (3 relations fondamentales)
4. Q5.3 (priorité owned/inherited/injected)

Les autres peuvent être affinées en cours de route.

---

*Document généré pour clarification — Object Fractal Tool v1*
