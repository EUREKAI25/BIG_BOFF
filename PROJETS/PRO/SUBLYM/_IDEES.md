# Idées — SUBLYM

> Idées d'améliorations, de fonctionnalités futures, de variations.
> Pas d'engagement, juste un espace pour capturer les idées au fil de l'eau.

---

## Optimisations pipeline

- [ ] Approche 3 (mega-prompt unique) : 1 seul appel, risqué mais ultra-rapide
- [ ] Parallélisation vraie : lancer plusieurs scènes en parallèle (async)
- [ ] Cache LLM : si rêve similaire déjà traité, réutiliser parties du scénario
- [ ] Fine-tuning GPT-4o sur scénarios validés (réduire coût via mini)
- [ ] Validation post-génération uniquement (pas pendant)

## Fonctionnalités vidéo

- [ ] Support couple (2 personnes cohérentes)
- [ ] Durées variables (15s, 30s, 60s, 2min)
- [ ] Styles visuels (cinéma, anime, peinture, etc.)
- [ ] Transitions personnalisées entre scènes
- [ ] Bande son adaptative (génération musicale IA)
- [ ] Voix-off narrative (TTS émotionnel)

## UX/Produit

- [ ] Preview scénario avant génération (validation utilisateur)
- [ ] Ajustements en temps réel (régénérer une scène spécifique)
- [ ] Historique des vidéos générées (galerie utilisateur)
- [ ] Export multi-formats (MP4, GIF, story Instagram)
- [ ] Partage social (liens publics, watermark optionnel)

## Monétisation

- [ ] Freemium : 1 vidéo/mois gratuite, 30€ pour 6-8 vidéos
- [ ] Abonnement pro : vidéos illimitées + styles premium
- [ ] API B2B : intégration pour coachs, thérapeutes
- [ ] Marketplace : templates de rêves pré-configurés

## Technique

- [ ] Module EURKAI standalone (scenario_generator réutilisable)
- [ ] Docker + Kubernetes (scalabilité)
- [ ] Queue système (Redis + workers)
- [ ] Monitoring temps réel (Grafana + Prometheus)
- [ ] A/B testing prompts (quality metrics)
- [ ] Self-healing : retry automatique si échec
