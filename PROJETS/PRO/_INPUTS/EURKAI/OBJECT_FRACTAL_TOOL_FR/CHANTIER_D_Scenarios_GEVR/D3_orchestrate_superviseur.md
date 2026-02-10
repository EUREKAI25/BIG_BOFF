
# PROMPT D3/6 — Orchestrate (Superviseur de scénarios)

## CONTEXTE

Tu disposes maintenant :
- de scénarios GEVR (D1/4),
- du MetaScénario “Projet EURKAI” (D2/5),
- de la fractale, d’ERK, des MetaRules.

Il faut maintenant introduire le **SuperTool Orchestrate** :
- un orchestrateur capable de :
  - choisir quel scénario exécuter,
  - les enchaîner,
  - gérer les erreurs,
  - redemander des infos si nécessaire.

Orchestrate est le **chef d’orchestre logique** de l’exécution.

## CE QUE TU AS EN INPUT

- Un catalogue de scénarios GEVR :
  - `Scenario.AnalyzeObject`,
  - `Scenario.CreateProjectSkeleton`,
  - `Scenario.ProjetEURKAI`,
  - etc.
- La structure du Projet EURKAI sortant de D2/5.
- Le besoin utilisateur, typiquement :
  - “Prends cette idée et fais-en un projet EURKAI complet.”

## CE QUE TU DOIS PRODUIRE

1. Le **rôle exact** d’Orchestrate :

   - sélectionner un scénario en fonction du contexte,
   - lancer sa/leurs exécution(s),
   - interpréter les résultats,
   - décider de la prochaine étape (ou de s’arrêter).

2. Une **API d’appel** :

   - `Orchestrate.run(request) -> { status, logs, result }`

   où `request` peut être :
   - une idée,
   - un brief,
   - une demande de transformation sur un projet existant.

3. Une logique de **gestion d’erreurs et de manques** :

   - si un scénario manque d’informations,
     Orchestrate doit :
     - soit demander des compléments (à l’humain ou à une IA),
     - soit proposer des hypothèses.

4. Des **exemples complets** :
   - entrée (idée / brief),
   - décisions d’Orchestrate (quel scénario choisi),
   - déroulé,
   - sorties.

## CONTRAINTES

- Orchestrate ne doit pas être monolithique :
  - il doit pouvoir être étendu par de nouveaux scénarios.
- Il doit respecter :
  - les limites de sécurité (Layer 0),
  - les MetaRules,
  - la logique des layers (ne pas laisser un scénario toucher à tout).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. Une description complète du comportement d’Orchestrate.
2. La signature de `Orchestrate.run`.
3. La logique de sélection de scénarios (en texte ou pseudo-code).
4. Des exemples d’utilisation (input → orchestration → output).
5. Des cas de test (scénario simple, scénario avec erreur, scénario avec manque d’info).

## CHECKLIST DE VALIDATION

- [ ] Orchestrate sait choisir et exécuter un scénario adapté au contexte.
- [ ] Orchestrate produit des logs compréhensibles pour chaque étape clé.
- [ ] En cas de manque d’info, il ne plante pas : il remonte une demande claire.
- [ ] Tu as fourni des exemples + cas de test.
