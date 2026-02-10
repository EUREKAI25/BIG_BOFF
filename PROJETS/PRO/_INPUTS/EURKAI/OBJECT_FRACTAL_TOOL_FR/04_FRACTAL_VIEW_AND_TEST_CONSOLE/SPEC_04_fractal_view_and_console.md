# SPEC 04 — Vue fractale & Console de test

But : proposer une vue détaillée de **XFractal** et une petite **console de test**.

Fonctionnalités :

1. **Vue fractale (XFractal)**
   - Pour l’ObjectType (ou vecteur) sélectionné, afficher :
     - les attributs,
     - les méthodes secondaires,
     - les règles ERK,
     - les relations.
   - Regrouper chaque élément par :
     - **owned**,
     - **inherited**,
     - **injected**.
   - Pour chaque élément non-owned, afficher la **source** :
     - ancêtre,
     - ou logique transversale / tag.
   - Contrôle de profondeur :
     - slider ou input numérique pour limiter le nombre de niveaux d’héritage affichés.
     - au-delà, montrer un indicateur “suite…” ou équivalent.

2. **Vecteurs & navigation**
   - Chaque lineage correspond virtuellement à un **vecteur** dans le catalogue.
   - Dans l’interface, cliquer sur un vecteur ou sur le lineage doit permettre :
     - d’ouvrir la vue fractale complète correspondante.

3. **Console de test**
   - Input permettant de saisir des expressions du type :
     - `methodA(inputs).result.message`
   - Pour la V1, les méthodes peuvent être mockées (simulées) :
     - le but est de tester le câblage et la navigation, pas la logique métier réelle.
   - Afficher :
     - le résultat simulé,
     - ou un message d’erreur lisible.

Remarques :
- Cette vue sert à l’architecte (toi) pour **diagnostiquer et valider** la cohérence de la fractale.
- Elle doit réutiliser les mêmes structures JSON que les autres modules.
