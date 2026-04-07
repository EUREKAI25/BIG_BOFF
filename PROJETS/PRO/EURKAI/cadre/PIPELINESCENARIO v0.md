PIPELINESCENARIO v0

--------------------------------
1. Position
--------------------------------

Scenario
→ PipelineScenario

--------------------------------
2. Rôle
--------------------------------

PipelineScenario est un Scenario majeur du système.

Il sert à :
- porter le chaînage d’un pipeline
- supporter le debug
- supporter la validation inter-étapes
- supporter le monitoring d’exécution

--------------------------------
3. Héritage
--------------------------------

PipelineScenario hérite de Scenario.

Il ne redéfinit pas ce qui est déjà acquis.

--------------------------------
4. Spécificités minimales
--------------------------------

PipelineScenario.owned_element_list {
  chain_list
}

--------------------------------
5. Règles minimales
--------------------------------

- PipelineScenario porte un chain_list lisible
- chaque élément du chain_list correspond à une étape exécutable ou validable
- les spécificités supplémentaires seront précisées plus tard