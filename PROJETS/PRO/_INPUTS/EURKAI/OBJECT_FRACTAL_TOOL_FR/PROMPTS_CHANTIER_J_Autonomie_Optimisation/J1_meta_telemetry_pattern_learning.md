
# J1 — Méta-télémétrie & apprentissage de patterns d’utilisation

## Objectif
Mettre en place un système de télémétrie “meta” permettant :
- d’observer comment les projets et scénarios sont réellement utilisés,
- de détecter des patterns récurrents,
- d’identifier des points de friction,
- de nourrir les outils PGCD/PPCM logiques et les suggestions d’amélioration.

## Ce que tu dois produire
- Un modèle de données pour les événements d’usage : qui, quoi, quand, sur quel objet/scénario.
- Une stratégie d’agrégation / anonymisation (respect de la vie privée et du cadre éthique).
- Des exemples de métriques utiles :
  - scénarios les plus utilisés,
  - modules les plus réutilisés,
  - erreurs fréquentes,
  - temps moyen d’exécution par type d’action.

## Contraintes
- Ne pas lier directement ces métriques à des décisions automatiques de modification : à ce stade, elles nourrissent uniquement l’analyse et les outils d’optimisation.
