
# PROMPT G3/11 — Déploiement autonome multi-projets

## CONTEXTE

EURKAI sait déjà :
- définir des projets,
- les booter individuellement (F3/6),
- les optimiser et les tester (G1/9, G2/10).

Tu dois maintenant concevoir le **déploiement autonome multi-projets** :

- plusieurs projets EURKAI coexistent,
- EURKAI supervise leur état,
- EURKAI peut déployer / mettre à jour / monitorer chacun.

## CE QUE TU AS EN INPUT

- Un ensemble de manifests ou de définitions de projets.
- Des pipelines de bootstrapping et de test.
- Un besoin de supervision centralisée.

## CE QUE TU DOIS PRODUIRE

1. Un modèle de **Portfolio EURKAI** :

   - liste de projets,
   - état de chaque projet (version, statut, incidents),
   - liens vers les logs / monitors.

2. Une API, par ex. :

   - `deployProject(projectId)`
   - `updateProject(projectId)`
   - `getProjectStatus(projectId)`

3. Des stratégies de mise à jour :

   - safe deploy,
   - canary,
   - rollback.

## CONTRAINTES

- La supervision doit :
  - respecter les règles de sécurité,
  - être résiliente aux erreurs d’un projet isolé.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Le modèle de Portfolio.
2. La description des API de déploiement.
3. Des scénarios d’usage (ajout d’un nouveau projet, MAJ d’un existant…).
4. Des cas de test.

## CHECKLIST DE VALIDATION

- [ ] Le portfolio multi-projets est bien défini.
- [ ] Les API de déploiement / mise à jour / statut sont claires.
- [ ] Tu as fourni des exemples + cas de test.
