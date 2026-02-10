
# PROMPT F2/5 — Génération de modules (code / templates / configs)

## CONTEXTE

Le Manifest fractal (F1/4) fournit maintenant une vue exportable de la fractale.  
Tu dois concevoir la **génération de modules** :

- à partir du manifest,
- générer du code squelette,
- des templates,
- des fichiers de configuration.

Cela prépare le **bootstrapping complet** (F3/6).

## CE QUE TU AS EN INPUT

- Le format du manifest (F1/4).
- Des décisions sur les cibles possibles :
  - ex : Python, Node.js, config YAML, etc.
- La structure d’un projet EURKAI (D2).

## CE QUE TU DOIS PRODUIRE

1. Une **stratégie de génération** :

   - comment un objet dans le manifest devient un module de code,
   - comment les relations deviennent des dépendances,
   - comment les scénarios deviennent des scripts / tâches.

2. Une API conceptuelle, par ex. :

   - `generateModules(manifest, targetStack) -> fileTree`

3. Des **exemples de mapping** :
   - un petit manifest → un petit projet squelette.

## CONTRAINTES

- La génération doit respecter :
  - les règles d’héritage,
  - les lineages,
  - les MetaRules (autant que possible).
- Elle ne doit pas écraser le travail manuel futur :
  - prévoir des zones “générées” vs “manuelles”.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La description de la stratégie de génération.
2. Le format de `fileTree` (résultat).
3. Des exemples concrets.
4. Des cas de test (manifest simple → arborescence générée attendue).

## CHECKLIST DE VALIDATION

- [ ] La stratégie de génération est claire et alignée avec la fractale.
- [ ] Un manifest simple peut donner un squelette de projet cohérent.
- [ ] Les frontières entre code généré et code humain sont définies.
- [ ] Tu as fourni des exemples + cas de test.
