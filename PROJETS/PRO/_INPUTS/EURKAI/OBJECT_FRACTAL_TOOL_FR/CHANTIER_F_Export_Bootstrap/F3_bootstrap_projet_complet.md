
# PROMPT F3/6 — Bootstrapping complet d’un projet EURKAI

## CONTEXTE

Le manifest fractal existe (F1/4)  
La génération de modules est définie (F2/5).

Tu dois maintenant concevoir le **bootstrapping complet** d’un projet :

- lire un manifest de projet EURKAI,
- générer les fichiers nécessaires,
- créer les configs,
- préparer un premier lancement (tests, dev, etc.).

## CE QUE TU AS EN INPUT

- Un manifest spécifique à un projet (issu du MetaScénario Projet EURKAI).
- La stratégie de génération de modules (F2/5).
- Des informations supplémentaires sur l’environnement (chemins, options, etc.).

## CE QUE TU DOIS PRODUIRE

1. La définition d’un **pipeline de bootstrapping** :

   - lecture du manifest,
   - génération des modules,
   - écriture sur disque,
   - initialisation (ex : création de virtualenv, install de deps, etc.),
   - exécution de premiers tests basiques.

2. Une API conceptuelle :

   - `bootstrapProject(manifest, options) -> { status, paths, logs }`

3. Des **exemples** :
   - bootstrapping d’un blog EURKAI,
   - bootstrapping d’un labo EURKAI.

## CONTRAINTES

- Le bootstrapping doit être :
  - reproductible,
  - loggé,
  - réversible (au moins partiellement).
- Il doit respecter les décisions structurelles d’EURKAI :
  - ne pas “innover” dans l’architecture,
  - suivre ce qui est décrit dans la fractale.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La description complète du pipeline de bootstrapping.
2. La signature de `bootstrapProject`.
3. Des exemples de scénarios complets (entrée → actions → sortie).
4. Des cas de test (projet minimal, projet moyen).

## CHECKLIST DE VALIDATION

- [ ] Le pipeline de bootstrapping est défini étape par étape.
- [ ] La fonction peut théoriquement prendre un manifest et produire un projet complet.
- [ ] Les logs et points de contrôle sont prévus.
- [ ] Tu as fourni des exemples + cas de test.
