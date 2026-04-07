SCOPE v0

--------------------------------
1. Position
--------------------------------

Scope est un objet.

- Scope hérite de Object.
- Scope figure dans owned_element_list.
- Scope peut être :
  - null
  - *
  - ou une valeur définie

--------------------------------
2. Sens
--------------------------------

scope = périmètre d’application

Il répond à :
- où cela s’applique ?
- sur quoi cela agit ?
- jusqu’où cela vaut ?

--------------------------------
3. Valeurs minimales
--------------------------------

null
- scope non défini
- scope à résoudre par héritage, injection ou méthode

*
- scope universel
- aucune restriction de périmètre

value
- scope explicitement défini par l’objet courant

--------------------------------
4. Rôle
--------------------------------

Scope contextualise :
- contract.required_element_list
- contract.validation_rule_list
- rules
- methods
- scenarios
- permissions
- roles
- plugability

--------------------------------
5. Forme minimale
--------------------------------

Scope.owned_element_list.option_list {
  value
  default_value
  automated_value
}

--------------------------------
6. Lecture des valeurs
--------------------------------

value
- scope explicitement porté par l’objet courant

default_value
- scope par défaut si aucun scope owned n’est défini

automated_value
- méthode permettant de résoudre le scope automatiquement
- si automated = true

--------------------------------
7. Règles
--------------------------------

- Scope peut être null.
- Scope peut être *.
- Scope peut être défini localement.
- Si scope = null, il doit être résolu par héritage, injection ou automated_value.
- Si scope = *, le périmètre est universel.
- Si scope est défini localement, il override le scope hérité ou injecté.
- automated = true signifie que le scope peut être résolu sans payload explicite.

--------------------------------
8. Héritage / affinage
--------------------------------

- Category peut porter un scope.
- Tag peut affiner le scope de la Category de l’objet.
- Le scope local de l’objet peut override le scope issu de Category ou Tag.
- Un Tag affine / complète ; il ne remplace pas à lui seul la logique portée par Category sauf override explicite plus local.

Ordre pratique de résolution :
owned.value
> tag-affined scope
> category scope
> inherited/default_value
> automated_value

--------------------------------
9. Exemples de lecture
--------------------------------

- Method.contract.scope
- Scenario.scope
- Rule.scope
- Category.scope
- Tag.scope

--------------------------------
10. Règle courte
--------------------------------

Scope contextualise le périmètre d’application.
Il ne décrit pas ce qu’est l’objet.
Il décrit où, sur quoi et jusqu’où il vaut.