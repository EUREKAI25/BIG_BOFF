
# PROMPT B2/2 — ERK étendu (conditions & contexte)

## CONTEXTE

L’étape B1/1 a produit un **interpréteur ERK minimal** capable de :
- parser des règles simples,
- les évaluer sur un objet,
- retourner un résultat structuré,
- sans modifier la fractale.

Tu dois maintenant **étendre ERK** pour gérer des **conditions plus riches** et un **contexte d’évaluation**.

Cette étape prépare l’utilisation d’ERK dans :
- les MetaRules de structure,
- les scénarios GEVR,
- plus tard : les actions système (B3/3).

## CE QUE TU AS EN INPUT

- L’API ERK minimale de B1/1 :
  - `parseErk(ruleText) -> ast`
  - `evaluateErk(ast, context) -> { status, details }`
- Des règles ERK existantes sous forme de texte.
- Un contexte d’exécution potentiellement enrichissable :
  - informations sur l’objet courant,
  - éventuellement quelques flags globaux simples (state, layer, etc.).

Tu peux supposer :
- que la console d’évaluation ERK existe déjà,
- que le store fractal est cohérent.

## CE QUE TU DOIS PRODUIRE

1. Une extension de la grammaire ERK pour gérer :

   - `IF / THEN / ELSE` simples,
   - des conditions de type `WHEN`,
   - des combinaisons logiques (AND, OR, NOT) plus expressives,
   - des comparaisons sur des attributs,
   - l’utilisation de variables de contexte (`ctx.something`).

2. La mise à jour de l’AST et de l’évaluateur ERK pour :
   - prendre en compte ces nouvelles constructions,
   - retourner des résultats détaillés (quelle branche a été suivie, etc.).

3. Des **exemples de règles ERK étendues**, par exemple :
   - `IF this.priority == "natural" THEN enable ELSE disable`
   - `WHEN ctx.layer == "System" AND this.type == "Agent" THEN allow`

4. Des **cas de test** montrant :
   - différents contextes d’évaluation,
   - des conditions vraies / fausses,
   - des branches alternatives bien gérées.

## CONTRAINTES

- Ne casse **rien** de ce qui a été défini en B1/1 :
  - les anciennes règles doivent toujours fonctionner.
- La syntaxe doit rester **lisible**, alignée avec la philosophie ERK.
- Pas d’effets de bord : B2/2 reste une étape d’**évaluation pure**, pas de modification du store.
- Tu dois penser à la **traçabilité** :
  - il doit être facile de savoir *pourquoi* une règle a renvoyé `ok` ou `error`.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une description de la **nouvelle grammaire** ERK supportée :
   - formes possibles d’IF / THEN / ELSE,
   - utilisation de `WHEN`,
   - structure des conditions.

2. La description de la **mise à jour de l’AST** :
   - nouveaux types de nœuds,
   - comment ils sont évalués.

3. Des **exemples de règles** complètes + leur **évaluation attendue**
   dans différents contextes (`ctx`).

4. Des **propositions de tests** :
   - cas unitaires (règle + contexte + résultat attendu),
   - éventuellement un début de stratégie de tests automatisables.

## CHECKLIST DE VALIDATION

- [ ] Les règles simples de B1/1 continuent de fonctionner sans modification.
- [ ] Les règles conditionnelles avec IF / THEN / ELSE sont supportées.
- [ ] Les règles de type WHEN (conditions sur le contexte) sont supportées.
- [ ] Le résultat de l’évaluation inclut des **informations de traçabilité**
      (branches, parties évaluées, etc.).
- [ ] Tu as fourni plusieurs exemples de règles + contextes + résultats attendus.
- [ ] La conception reste clairement extensible pour B3/3 (actions système).
