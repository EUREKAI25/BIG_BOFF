# TEST 01 — Explorateur de lineages

Checklist de test manuel :

- [ ] Je peux charger un JSON initial et voir un arbre d’ObjectTypes.
- [ ] Quand je clique sur un ObjectType :
  - [ ] sa lignée apparaît au centre,
  - [ ] une vue fractale textuelle affiche au moins la chaîne des ancêtres.
- [ ] Le contrôle de profondeur réduit bien ce qui est affiché.
- [ ] Si je drag & drop un ObjectType sous un autre :
  - [ ] son parent est mis à jour dans le JSON,
  - [ ] son lineage est recalculé,
  - [ ] la regex de nomenclature est respectée.
- [ ] Si je saisis un nouveau lineage dans l’input :
  - [ ] les nœuds manquants sont créés,
  - [ ] ils sont marqués `toFinalize: true`,
  - [ ] l’arbre se met à jour et les affiche.
