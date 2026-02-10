# TEST 04 — Vue fractale & Console de test

Checklist :

- [ ] En sélectionnant un ObjectType, je vois son XFractal :
  - [ ] attributs,
  - [ ] méthodes secondaires,
  - [ ] règles ERK,
  - [ ] relations.
- [ ] Chaque élément indique clairement :
  - [ ] s’il est owned / inherited / injected,
  - [ ] sa source si non-owned.
- [ ] Le contrôle de profondeur limite bien l’héritage affiché.
- [ ] Le vecteur associé (lineage) est cliquable et ouvre la vue fractale détaillée.
- [ ] Dans la console de test :
  - [ ] je peux saisir une expression simple (ex : `fakeMethod({test:1}).result.message`),
  - [ ] je reçois un résultat mock ou un message d’erreur compréhensible.
