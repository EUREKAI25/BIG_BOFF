
# PROMPT E1/7 — SuperTools centraux (SuperCreate, SuperRead, SuperUpdate, SuperDelete, SuperEvaluate, SuperOrchestrate)

## CONTEXTE

Les scénarios GEVR et Orchestrate sont définis (D1–D3).  
La fractale est stable, ERK et MetaRules sont en place.

Tu dois maintenant définir les **SuperTools centraux** d’EURKAI, qui représentent
les grandes méthodes transversales :

- SuperCreate
- SuperRead
- SuperUpdate
- SuperDelete
- SuperEvaluate
- SuperOrchestrate (interface avec D3)

Ces SuperTools sont l’API “haut niveau” d’EURKAI, utilisée aussi bien par :
- les humains (via UI),
- que les agents IA.

## CE QUE TU AS EN INPUT

- La structure fractale (objets, lineages, bundles).
- Les scénarios existants (D1–D3).
- Les règles ERK pour sécurité, structure, etc.

## CE QUE TU DOIS PRODUIRE

1. Une **définition claire** de chaque SuperTool :

   - ses responsabilités,
   - ses inputs,
   - ses outputs,
   - ses limites (ce qu’il ne fait PAS).

2. Une **API unifiée**, par exemple :

   - `Super.create(params)`
   - `Super.read(params)`
   - `Super.update(params)`
   - `Super.delete(params)`
   - `Super.evaluate(params)`
   - `Super.orchestrate(params)`

   ou équivalent, mais cohérent.

3. Le lien entre SuperTools et scénarios GEVR :
   - ex : SuperCreate peut invoquer des scénarios de création / génération,
   - SuperEvaluate peut invoquer des scénarios d’audit.

4. Des **exemples d’utilisation** pour chaque SuperTool.

## CONTRAINTES

- Les SuperTools ne doivent pas court-circuiter la logique :
  - ils doivent utiliser GEVR, ERK, MetaRules, et non contourner la structure.
- Ils doivent respecter :
  - les règles de sécurité (Layer 0 / Layer 1),
  - la séparation entre Core (structure) et Agence (projets).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une fiche détaillée par SuperTool :
   - rôle,
   - signature,
   - déroulé interne (en texte ou pseudo-code).

2. Des **exemples de requêtes** :
   - pour créer un objet,
   - lire un projet,
   - mettre à jour un bundle,
   - évaluer la qualité d’un projet.

3. Des **cas de test** :
   - appels simples,
   - appels complexes,
   - erreurs gérées.

## CHECKLIST DE VALIDATION

- [ ] Tous les SuperTools centraux sont définis de manière claire et cohérente.
- [ ] Chacun a une signature et une responsabilité bien délimitées.
- [ ] Les SuperTools utilisent la machinerie GEVR / ERK / MetaRules, pas l’inverse.
- [ ] Tu as fourni des exemples + cas de test pour chacun.
