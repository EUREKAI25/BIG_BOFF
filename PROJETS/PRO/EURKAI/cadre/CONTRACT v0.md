CONTRACT v0

--------------------------------
1. Nature
--------------------------------

Contract est un objet.

- Il hérite de Object.
- Il ne redéfinit rien de ce qui est déjà acquis.
- Il n’exécute rien.

--------------------------------
2. Rôle
--------------------------------

Contract cadre la validité d’un objet.

- Il impose la présence d’éléments requis.
- Il définit les conditions minimales pour qu’un objet soit utilisable dans un contexte donné.
- Il sert de base aux scénarios de validation.

--------------------------------
3. Principe
--------------------------------

Un Contract ne contient que des spécificités.

Il ne duplique aucune structure héritée.

--------------------------------
4. Spécificités
--------------------------------

Contract.owned_element_list {

  required_element_list

  validation_rule_list
  scope
}

--------------------------------
5. required_element_list
--------------------------------

- Liste des éléments requis pour que l’objet soit valide.
- Ces éléments peuvent être :
  - attributs
  - méthodes
  - relations
  - options

Règle :
- chaque élément listé doit exister dans l’objet validé

--------------------------------
6. validation_rule_list
--------------------------------

- Liste de règles de validation applicables.
- Ces règles sont des objets Rule.
- Elles sont exécutées lors des scénarios de validation.

--------------------------------
7. Injection
--------------------------------

- Contract est injecté dans un objet.
- L’objet ne copie pas la structure du Contract.
- Il en respecte les exigences.

--------------------------------
8. Validation
--------------------------------

Un objet est valide vis-à-vis d’un Contract si :

- tous les éléments de required_element_list sont présents
- toutes les règles de validation_rule_list sont satisfaites

Sinon :
- validation.failure

--------------------------------
9. Non-redondance
--------------------------------

- Contract n’impose jamais une redéfinition explicite
  d’un élément déjà disponible par héritage ou injection
- il impose seulement sa présence et sa validité

--------------------------------
10. Position dans le système
--------------------------------

Contract est utilisé pour :

- MethodContract
- ScenarioContract (plus tard)
- tout objet nécessitant un cadre de validité explicite