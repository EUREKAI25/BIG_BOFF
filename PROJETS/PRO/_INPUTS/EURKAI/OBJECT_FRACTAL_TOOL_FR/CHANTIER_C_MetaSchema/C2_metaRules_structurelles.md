
# PROMPT C2/2 — MetaRules de structure (invariants)

## CONTEXTE

Les lineages assistés (C1/1) permettent déjà de **proposer** des parents pour les objets.  
Maintenant, il est nécessaire de définir et d’appliquer des **MetaRules de structure** :

- des invariants globaux sur la fractale EURKAI,
- des contraintes du type “tout ObjectType doit avoir X, Y, Z”,
- des validations pour repérer les anomalies et les incohérences.

Ces MetaRules s’appuient sur :
- le MetaSchema (tout objet = bundle),
- le langage ERK (B1/1, B2/2),
- la structure actuelle des objets.

## CE QUE TU AS EN INPUT

- La fractale complète :
  - ObjectTypes,
  - lineages,
  - bundles (attributes, methods, rules, relations).
- ERK étendu (capable d’exprimer des conditions).
- Une première liste (même implicite) d’invariants souhaités, par exemple :
  - chaque objet doit avoir un `id`,
  - chaque objet doit avoir un `type`,
  - certains objets doivent avoir au moins une méthode centrale,
  - aucun cycle de lineage n’est toléré.

## CE QUE TU DOIS PRODUIRE

1. Une **liste structurée** de MetaRules de structure,
   en langage proche d’ERK, par exemple :

   - `FOR ALL ObjectType: require attribute "id"`
   - `FOR ALL Agent: require method "prompt"`
   - `FOR ALL Project: require relation depends_on Core:Config`

2. Une **API de vérification** :

   - `checkMetaRules() -> { ok, errors[] }`
   - chaque erreur doit inclure :
     - l’objet concerné,
     - la règle violée,
     - un message explicite.

3. L’intégration possible avec la console / cockpit :
   - possibilité de lancer un audit global,
   - affichage des erreurs structurées.

4. Des **exemples concrets** de MetaRules
   et de leur application sur des objets exemples.

## CONTRAINTES

- C2/2 ne doit pas modifier automatiquement la fractale :
  - cette étape se limite à la **détection**.
- Les MetaRules doivent être :
  - lisibles,
  - modifiables,
  - organisées (par type d’objet, par layer, etc.).
- L’exécution doit être suffisamment efficiente
  pour être lancée régulièrement (ex : avant un déploiement).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une spécification claire du **formalisme des MetaRules** :
   - syntaxe,
   - sémantique,
   - exemples.

2. La description de l’API de vérification :
   - signature,
   - structure des rapports d’erreur.

3. Des **exemples de MetaRules** appliquées à des cas concrets,
   avec explication des erreurs détectées.

4. Des **cas de test** pour vérifier que :
   - les objets valides passent,
   - les objets invalides sont correctement signalés.

## CHECKLIST DE VALIDATION

- [ ] Les MetaRules couvrent les invariants les plus fondamentaux d’EURKAI.
- [ ] Une fonction d’audit global permet de lister les violations de structure.
- [ ] Chaque violation est clairement reliée à l’objet et à la règle concernée.
- [ ] Tu as fourni plusieurs exemples + cas de test pour valider le système.
