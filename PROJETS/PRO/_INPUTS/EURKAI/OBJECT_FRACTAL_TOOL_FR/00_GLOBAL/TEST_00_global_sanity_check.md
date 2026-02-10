# TEST 00 — Vérifications globales

Checklist pour valider la conception générale :

- [ ] Les structures JSON permettent de représenter :
  - [ ] les ObjectTypes,
  - [ ] les lineages,
  - [ ] les tags / catégories,
  - [ ] les alias,
  - [ ] les schémas de Bundles,
  - [ ] les XFractals (attributs, méthodes, règles, relations, avec owned/inherited/injected).
- [ ] On peut distinguer clairement **owned**, **inherited**, **injected** dans les données.
- [ ] La nomenclature de lineage peut être validée par une regex unique.
- [ ] L’ajout futur de champs ne casse pas l’architecture.
- [ ] Chaque étape suivante (01, 02, 03, 04) a un point d’intégration clair dans cette architecture.
