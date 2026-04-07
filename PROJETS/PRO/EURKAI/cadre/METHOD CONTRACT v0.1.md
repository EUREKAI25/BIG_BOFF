METHOD CONTRACT v0.1

--------------------------------
1. Règle d’application
--------------------------------

Un Contract s’applique par défaut à l’objet qui le porte.

--------------------------------
2. Position
--------------------------------

MethodContract est la valeur de :
- Method.contract

Il ne redéfinit pas la structure de Contract.
Il en définit le contenu spécifique pour Method.

--------------------------------
3. Rôle
--------------------------------

MethodContract cadre la validité d’une Method.

Il garantit qu’une Method est :
- appelable
- affectée à un objet
- orchestrable
- testable
- validable

--------------------------------
4. Contenu minimal
--------------------------------

Method.contract.required_element_list {
  input
  output
  payload
  target_object
  orchestrate_scenario
  validation_rule_list
  test_list
}

--------------------------------
5. Validation minimale
--------------------------------

Method.contract.validation_rule_list {
  has_input
  has_output
  has_payload
  has_target_object
  has_orchestrate_scenario
  has_validation_rule_list
  has_test_list
}

--------------------------------
6. Scope
--------------------------------

Method.contract.scope

- peut être null
- peut être *
- peut être défini explicitement
- contextualise les exigences du contract

--------------------------------
7. Injection
--------------------------------

- input, output, payload, target_object, orchestrate_scenario,
  validation_rule_list et test_list existent dans Method
  par injection de MethodContract
- Method ne redéfinit pas leur structure
- Method en définit uniquement les valeurs

--------------------------------
8. Non-redondance
--------------------------------

- Method ne copie pas la structure du contract
- elle respecte les exigences
- elle ne définit que ses spécificités

--------------------------------
9. Orchestration
--------------------------------

- orchestrate_scenario est unique
- il organise 1..N milestone.scenario_list
- il porte la logique d’exécution
- la Method reste un contrat

--------------------------------
10. Règle courte
--------------------------------

Une Method est valide si tous les éléments requis par MethodContract existent
et si toutes les règles de validation sont satisfaites.