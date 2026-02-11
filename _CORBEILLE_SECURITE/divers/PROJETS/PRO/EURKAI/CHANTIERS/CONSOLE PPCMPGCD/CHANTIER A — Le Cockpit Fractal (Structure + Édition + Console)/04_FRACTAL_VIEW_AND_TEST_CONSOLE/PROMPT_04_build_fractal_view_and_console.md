# PROMPT 04 — Construire la vue fractale & la console de test

Tu es une IA développeuse front.

Lis :
- `SPEC_04_fractal_view_and_console.md`
- Les structures de données définies en 00_GLOBAL
- Et le code déjà implémenté pour 01, 02, 03.

Tâche :
- Implémenter une vue **Fractale & Tests** qui :
  1. Pour l’ObjectType ou vecteur sélectionné :
     - affiche le XFractal :
       - attributs,
       - méthodes secondaires,
       - règles ERK,
       - relations,
     - indique pour chaque élément s’il est :
       - owned,
       - inherited,
       - injected,
     - indique la **source** des éléments inherited/injected,
     - permet de limiter la profondeur de l’héritage affiché.
  2. Ajoute une **console de test** :
     - un input pour saisir une expression de la forme `methodA(inputs).result.message`,
     - interpréter cette expression en appelant des fonctions JS mock,
     - afficher le résultat ou un message d’erreur clair.

Contraintes :
- Réutiliser au maximum les composants existants.
- Garder le code modulaire, extensible.

Output :
- Code HTML/JS pour cette vue ou module dédié.
