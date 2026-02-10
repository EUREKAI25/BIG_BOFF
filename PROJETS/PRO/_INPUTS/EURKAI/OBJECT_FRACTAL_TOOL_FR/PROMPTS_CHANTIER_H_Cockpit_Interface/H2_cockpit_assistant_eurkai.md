
# H2 — Intégration de l’Assistant Eurkai dans le Cockpit

## Objectif
Implémenter l’Assistant Eurkai décrit dans `NOTE_ASSISTANT_EURKAI.md` :
- onglet Input libre (texte + upload de fichier),
- onglet Discussion IA (chat read-only + bouton “Générer”),
- onglet Historique (inputs passés + résultats fractaux),
et relier tout ça à `Super.orchestrate` côté backend.

## Ce que tu dois produire
- Le contrat d’API pour `Super.orchestrate({ input })` vu depuis le Cockpit.
- La structure des messages échangés pour :
  - envoyer du texte brut,
  - envoyer des fichiers (brief, cahier des charges, JSON, manifest…),
  - récupérer le résultat structuré (projet, suggestions, logs).
- Le modèle interne pour l’historique des actions (ID d’input, scénario exécuté, diff fractal associé).

## Contraintes
- L’Assistant ne fait **aucune modification directe** sur la fractale :
  - il reçoit des résultats,
  - le Cockpit les affiche,
  - les writes réels passeront plus tard par des actions validées.
- L’IA utilisée dans l’onglet Discussion IA ne manipule pas le Core :
  - elle ne sert qu’à clarifier l’idée / le brief.
