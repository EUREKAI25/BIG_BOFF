
# PROMPT E2/8 — Mode IA assistée (agents IA cadrés par EURKAI)

## CONTEXTE

Les SuperTools sont définis (E1/7).  
Tu peux piloter la fractale via des méthodes haut niveau cohérentes.

Tu dois maintenant définir le **Mode IA assistée**, c’est-à-dire :

- comment des agents IA externes (comme ChatGPT / Claude) interagissent avec EURKAI,
- ce qu’ils ont le droit de faire,
- à travers **quels canaux** (SuperTools uniquement),
- avec quels garde-fous.

L’objectif est de :
- déléguer le travail pénible (complétion, génération, refactoring),
- tout en gardant le contrôle **stratégique et structurel**.

## CE QUE TU AS EN INPUT

- Définition des SuperTools (E1/7).
- Règles Core/Security et Core/AI (Layer 0).
- Tes préférences explicites :
  - l’IA ne doit jamais modifier le Core,
  - l’IA ne décide pas seule du déploiement,
  - l’IA propose, EURKAI et toi disposez.

## CE QUE TU DOIS PRODUIRE

1. Un **modèle de rôle** pour un agent IA EURKAI :

   - ce qu’il peut faire,
   - ce qu’il ne peut jamais faire,
   - comment il doit utiliser les SuperTools.

2. Un ensemble de **protocoles d’interaction** :

   - par exemple :
     - “Pour compléter les bundles d’un objet : utilise SuperUpdate sur tel endpoint.”
     - “Pour proposer une nouvelle structure : génère un plan + demande validation humaine.”

3. La description des **modes de fonctionnement** possibles :

   - `suggest-only` : l’IA ne fait que proposer,
   - `auto-with-review` : l’IA applique mais doit générer un diff à valider,
   - `read-only` : l’IA ne fait que explorer.

4. Des **exemples de sessions** IA ↔ EURKAI, montrant comment :

   - un agent IA analyse un projet,
   - propose des modifications via SuperTools,
   - attend une validation.

## CONTRAINTES

- Le Mode IA assistée doit être :
  - explicite,
  - documenté,
  - traçable (logs de toutes les actions IA).
- Il doit être impossible, dans cette conception,
  qu’une IA touche directement au Core (Layer 0).

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La définition d’un ou plusieurs **profils d’agent IA**.
2. La description des **flux d’interaction** :
   - comment un agent IA reçoit une tâche,
   - comment il interagit avec EURKAI,
   - comment ses actions sont validées ou refusées.

3. Des **exemples de dialogues ou d’échanges** structurés.

4. Des **cas de test** :
   - un agent IA discipliné,
   - un agent IA qui propose quelque chose d’interdit (et comment c’est géré).

## CHECKLIST DE VALIDATION

- [ ] Le Mode IA assistée est défini de manière claire et exploitable.
- [ ] Les actions IA passent uniquement par les SuperTools.
- [ ] Les garde-fous de sécurité sont bien pris en compte.
- [ ] Tu as fourni des exemples + cas de test.
