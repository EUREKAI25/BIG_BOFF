
# PROMPT F1/4 — Manifest fractal (export JSON officiel)

## CONTEXTE

EURKAI dispose maintenant :
- d’une fractale stable,
- de MetaRules,
- de scénarios GEVR,
- de SuperTools,
- d’un Mode IA assistée.

Tu dois maintenant définir un **format d’export officiel** de la fractale :
le **Manifest fractal**.

Ce manifest doit contenir tout ce qui est nécessaire pour :
- reconstruire l’état d’EURKAI ailleurs,
- générer du code et des projets (F2, F3),
- faire des backups cohérents.

## CE QUE TU AS EN INPUT

- La structure fractale :
  - ObjectTypes,
  - lineages,
  - bundles (attributes, methods, rules, relations),
  - scénarios,
  - tags, catégories, alias.

## CE QUE TU DOIS PRODUIRE

1. La **spécification du Manifest fractal**, par exemple en JSON :

   - sections :
     - `objects`,
     - `relations`,
     - `scenarios`,
     - `meta`,
     - etc.

2. La description des **champs obligatoires** pour chaque type d’entrée.

3. Une API d’export :

   - `exportManifest() -> manifestJSON`

4. Des **exemples de manifest** :
   - fragment pour quelques objets,
   - manifest minimal mais cohérent.

## CONTRAINTES

- Le manifest doit être :
  - complet,
  - versionné (inclure un numéro de version de schéma),
  - lisible par d’autres outils.
- Il doit être possible de :
  - exporter,
  - puis réimporter (plus tard) sans perte de cohérence.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La structure JSON (ou équivalent) du manifest.
2. La liste des champs obligatoires / optionnels.
3. Des exemples de manifest partiel / complet.
4. Des cas de test :
   - export d’un sous-ensemble,
   - export complet.

## CHECKLIST DE VALIDATION

- [ ] La structure du manifest fractal est clairement définie.
- [ ] Tous les éléments critiques de la fractale sont représentés.
- [ ] Il est réaliste de reconstruire la fractale à partir du manifest.
- [ ] Tu as fourni des exemples + cas de test.
