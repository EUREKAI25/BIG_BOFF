
# PROMPT G2/10 — Méta-tests & auto-debug fractal

## CONTEXTE

Les outils PGCD/PPCM logiques sont définis (G1/9).  
Tu dois maintenant concevoir un système de **méta-tests** capable de :

- générer des cas de test à partir de la fractale,
- vérifier la cohérence après chaque modification importante,
- aider à détecter des régressions.

## CE QUE TU AS EN INPUT

- La fractale,
- les MetaRules,
- les scénarios GEVR,
- les SuperTools.

## CE QUE TU DOIS PRODUIRE

1. Une hiérarchie de tests :

   - tests de structure (MetaRules),
   - tests de relations (MetaRelations),
   - tests de scénarios (GEVR),
   - tests d’intégration (SuperTools).

2. Une API, par ex. :

   - `runMetaTests(scope) -> report`

   où `scope` peut être :
   - tout le système,
   - un projet,
   - un sous-ensemble d’objets.

3. Des exemples de rapports de test.

## CONTRAINTES

- Le système doit être :
  - extensible,
  - lisible,
  - capable de tourner fréquemment.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La description de la hiérarchie de tests.
2. La signature de `runMetaTests`.
3. Des exemples de rapports.
4. Des cas de test.

## CHECKLIST DE VALIDATION

- [ ] Les niveaux de tests sont bien définis.
- [ ] `runMetaTests` peut théoriquement couvrir ces niveaux.
- [ ] Tu as fourni des exemples + cas de test.
