# SUBLYM — Suivi

> Pipeline de génération de vidéos de manifestation de rêves — Photo-réaliste, cohérence AI, optimisation coût/temps

**Statut** : 🟢 actif — optimisation pipeline en cours
**Créé** : 2026-02-10
**Dernière MAJ** : 2026-02-10 20:00

---

## Objectif

Créer un pipeline autonome transformant un rêve utilisateur en vidéo photo-réaliste de manifestation :
- **Input** : Description de rêve (texte)
- **Output** : Vidéo 30s (5 scènes × 6s) photo-réaliste cohérente
- **Contraintes** :
  - Cohérence visuelle 100% (même personne, même lieu)
  - Coût < 1€ par vidéo (objectif : 30€/mois pour 6-8 vidéos)
  - Temps < 2 minutes (objectif : génération quasi-instantanée)
  - Qualité professionnelle (utilisable en production)

---

## État actuel

### Pipeline v7 (baseline)
- ✅ Fonctionnel : génère scénarios cohérents à 100%
- ❌ Coût : ~2-4€ par scénario (trop élevé)
- ❌ Temps : 10-15 minutes (trop lent)
- ❌ Appels LLM : ~168 appels (triple validation V1/V2/V3)

**Problème** : Chaque question = 1 génération + 3 validations = 4 appels LLM
**Résultat** : 11 étapes × questions multiples × 4 = explosion du nombre d'appels

### Pipeline v8 (optimisation en cours)
- 🟡 Architecture batch : regroupement par scène
- 🟡 Objectif : 9 appels au lieu de 168 (-95%)
- 🟡 Coût visé : ~0.15€ (GPT-4o) ou ~0.02€ (GPT-4o-mini)
- 🟡 Temps visé : 1-2 minutes
- 🟡 Qualité : maintenue via schémas JSON stricts + few-shot examples

---

## Architecture

### Stack technique
- **Génération scénario** : GPT-4o (température 0.3-0.4)
- **Génération images** : Flux Kontext Pro (cohérence 2-3 retries)
- **Génération vidéo** : MiniMax avec keyframe chaining
- **Validation** : Pydantic schemas (validation structurelle)

### Workflow cible
```
Rêve (texte)
  ↓
SCENARIO AGENT v8 (9 appels, 1-2min, ~0.15€)
  ├─ Blocages + Pitch global
  ├─ Découpage 5 scènes
  ├─ Paramètres TOUTES scènes (batch)
  ├─ Keyframes TOUTES scènes (batch)
  ├─ Pitchs + Attitudes TOUTES scènes (batch)
  ├─ Palettes globale + par scène (batch)
  ├─ Cadrages TOUTES scènes (batch)
  ├─ Rythme
  └─ Prompts finaux TOUTES scènes (batch)
  ↓
JSON structuré (scénario complet)
  ↓
IMAGE AGENT (5 scènes × 2-3 retries Flux)
  ↓
VIDEO AGENT (MiniMax keyframe chaining)
  ↓
Vidéo finale 30s
```

---

## Décisions

- **2026-02-10 20:50** : **RÈGLE NARRATIVE AJOUTÉE : Scène 1 = PRÉPARATIFS / MOMENT DE BASCULE**
  - La première scène DOIT montrer l'action concrète qui lance le rêve (réserver billet, préparer valise, etc.)
  - C'est le passage de l'intention à la réalisation
  - Exemple : "Je rêve d'aller à Rio" → Scène 1 = réserver le billet d'avion en ligne
- **2026-02-10 20:00** : Création projet SUBLYM structuré selon standards EURKAI
- **2026-02-10 20:00** : Validation Approche 2 (consolidation batch, 9 appels)
- **2026-02-10 19:30** : Analyse pipeline_v7 — 168 appels identifiés, optimisation possible
- **2026-02-10** : Focus photo-réaliste solo uniquement (couple = phase 2)
- **2026-02-10** : St-Valentin abandonné (deadline impossible, feature couple pas prête)

---

## Historique

- **2026-02-10 20:50** : Règle narrative "Scène 1 = Préparatifs" ajoutée au pipeline v8
- **2026-02-10 20:45** : session_test.json créé (rêve : rencontrer l'amour à Paris)
- **2026-02-10 20:00** : Création projet SUBLYM avec structure EURKAI (PIPELINE/, src/, tests/, docs/)
- **2026-02-10 19:30** : Analyse détaillée pipeline_v7 (168 appels, 10-15min, 2-4€)
- **2026-02-08** : Pipeline v7 opérationnel (triple validation, séquentiel)
- **2026-02-05** : Pipeline photos-only MVP (0.29 EUR / 8 photos / 2 min)
- **2026-02** : Tests Flux Kontext Pro (cohérence 100% avec 2-3 retries)
- **2026-01** : Exploration MiniMax, keyframe chaining, anomalies vidéo identifiées

---

## Prochaines étapes

### Immédiat (aujourd'hui)
- [ ] Créer pipeline_v8_batch.py (architecture 9 appels)
- [ ] Documenter specs optimisation dans PIPELINE/01_SPECS_OPTIMISATION.md
- [ ] Tester v8 sur un rêve existant (comparaison v7 vs v8)
- [ ] Valider qualité output (cohérence maintenue ?)

### Court terme (semaine)
- [ ] Fine-tuning prompts batch (few-shot examples)
- [ ] Schémas Pydantic pour validation structurelle
- [ ] Tests automatisés (pytest)
- [ ] Intégration IMAGE AGENT + VIDEO AGENT

### Moyen terme (mois)
- [ ] MVP complet photo-réaliste solo
- [ ] Dashboard monitoring (coût, temps, qualité)
- [ ] API publique (webhook + job status)
- [ ] Module EURKAI réutilisable (scenario_generator)
