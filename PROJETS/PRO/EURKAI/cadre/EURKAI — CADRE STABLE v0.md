EURKAI — CADRE STABLE v0.3

--------------------------------
1. Principes fondamentaux
--------------------------------

- On ne définit que les spécificités.
- Tout le reste est hérité ou injecté.
- On ne définit pas ce que les objets ne sont pas.
- Le catalogue ne contient que des spécificités.
- Les valeurs complètes sont résolues à la demande.
- automated = no explicit payload value required

--------------------------------
2. Object
--------------------------------

Object.owned_element_list.base_list {
  name
  description
  example
  version
  ident
  kind
  created_at
  updated_at
  created_by
  updated_by
  status
  lifecycle
  category
  tag_list
  automated
  how
}

Object.owned_element_list.tree_list {
  parent_list
  child_list
  sibling_list
}

Object.owned_element_list.method_list

Object.owned_element_list.rule_list {
  structural_rule_list
  constitutional_rule_list
}

Object.owned_element_list.option_list {
  value
  default_value
  automated_value
  instance_list
}

Object.owned_element_list.relation_list

Object.owned_element_list.transversal_parameter_list

--------------------------------
3. Parameter
--------------------------------

Parameter est un objet transversal.

Règle :
- tout Parameter s’applique à l’objet dont il est paramètre

Parameter inclut :
- Attribute
- Method
- Rule
- Relation
- Option
- Contract

--------------------------------
4. Contract
--------------------------------

Contract est un Parameter:Attribute de Object.

Object
- schema
- contract

Rôle :
- cadre la validité d’usage d’un objet
- ne définit pas de structure
- ne duplique rien

Règle d’existence :

Contract doit exposer :
- required_element_list
- validation_rule_list
- scope

--------------------------------
5. Scope
--------------------------------

Scope est un objet.

Valeurs :
- null
- *
- explicite

Règles :
- null → à résoudre
- * → universel
- value → override local

Hiérarchie :
owned.value
> tag-affined
> category
> inherited/default
> automated

--------------------------------
6. Method
--------------------------------

Method est un Parameter.

Relation :

relation_list {
  method_of
  is_secondarymethod_of
}

Règles :
- method_of → objet auquel la méthode s’applique
- is_secondarymethod_of → CentralMethod associée

--------------------------------
7. MethodContract
--------------------------------

Method.contract

--------------------------------
Contenu minimal
--------------------------------

required_element_list {
  input
  output
  payload
  method_of
  orchestrate_scenario
  validation_rule_list
  test_list
}

validation_rule_list {
  has_input
  has_output
  has_payload
  has_method_of
  has_orchestrate_scenario
  has_validation_rule_list
  has_test_list
}

scope
- null | * | explicite

--------------------------------
Injection
--------------------------------

Ces éléments existent dans Method par injection du contract.

Method ne définit que leurs valeurs.

--------------------------------
8. CentralMethod
--------------------------------

Create
Read
Update
Store
Orchestrate
Engage

Règle :
- toute exécution démarre par une CentralMethod

--------------------------------
9. Scenario
--------------------------------

Scenario est un objet.

Hérite de :
- category
- tag_list
- trigger_list

Spécificités :

- agent
- milestone.scenario_list
- execute.behavior

--------------------------------
Agent
--------------------------------

scenario.agent
- résolu ou généré
- dépend de category et règles associées

category
- porte roles et permissions

tag
- affine, ne crée pas

--------------------------------
Exécution
--------------------------------

execute.behavior = parallel
fallback = sequence

--------------------------------
10. CentralScenario
--------------------------------

Scenario
→ CentralScenario
  → CreateScenario
  → ReadScenario
  → UpdateScenario
  → StoreScenario
  → OrchestrateScenario
  → EngageScenario

Règle :
- chaque scénario central est lié à une CentralMethod
- ne définit que ses spécificités

--------------------------------
11. Axes opératoires
--------------------------------

WHY
- trigger_list

WHAT
- SuperGet
- result

HOW
- CentralMethod (CRUSOE)

Règles :

- how appartient à what
- how n’est défini que par les opérations
- SuperGet met à jour what.how

--------------------------------
12. SuperMethods
--------------------------------

SuperGet
SuperExecute
SuperValidate
SuperRender

--------------------------------
13. Exécution
--------------------------------

run =
if get and execute :
  if validate then success else failure
after

--------------------------------
14. Parallélisme
--------------------------------

- exécution par dict
- parallèle par défaut
- fallback séquentiel
- dépendances déclarées par method / milestone.step

--------------------------------
15. Reset / logs
--------------------------------

how.execute.after[] = value.reset

Logs :
- manipulés uniquement par l’agent du scenario

--------------------------------
16. Règle de non-duplication
--------------------------------

- pas de copie
- seulement override

Une donnée owned est spécifique
si elle diffère de sa valeur automatisée