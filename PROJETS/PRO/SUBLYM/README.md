# SUBLYM

> Pipeline de génération de vidéos de manifestation de rêves — Photo-réaliste, cohérence AI, optimisation coût/temps

## Description

SUBLYM transforme une description de rêve (texte) en vidéo photo-réaliste de 30 secondes montrant la réalisation du rêve. Le pipeline génère automatiquement le scénario, les images et la vidéo finale avec cohérence visuelle garantie.

**Exemple** : "Je veux rencontrer l'amour à Paris" → Vidéo 30s de 5 scènes (rencontre café, balade Seine, dîner romantique, etc.)

## Stack technique

- **Scénario** : GPT-4o (génération structurée JSON)
- **Images** : Flux Kontext Pro (photo-réalisme + cohérence)
- **Vidéo** : MiniMax (keyframe chaining)
- **Validation** : Pydantic (schemas stricts)

## Installation

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM

# Installer dépendances
pip install -r requirements.txt

# Configurer clés API
cp .env.example .env
# Éditer .env avec tes clés OpenAI, Anthropic, etc.
```

## Utilisation

### Pipeline v7 (baseline)
```bash
python src/pipeline_v7.py session.json 5 6
# Arguments : fichier_input nb_scenes duree_par_scene
# Output : scenario_YYYYMMDD_HHMMSS.json + audit.txt
```

### Pipeline v8 (optimisé — en développement)
```bash
python src/pipeline_v8_batch.py session.json
# Output : scenario_YYYYMMDD_HHMMSS.json
# 9 appels au lieu de 168, 1-2min au lieu de 10-15min
```

## Métriques

| Version | Appels LLM | Temps | Coût (GPT-4o) | Qualité |
|---|---|---|---|---|
| v7 (baseline) | 168 | 10-15min | ~2.70€ | 100% |
| v8 (batch) | 9 | 1-2min | ~0.15€ | À valider |

## Statut

Voir [_SUIVI.md](_SUIVI.md)

## Documentation

- [PIPELINE/01_SPECS_OPTIMISATION.md](PIPELINE/01_SPECS_OPTIMISATION.md) — Détails optimisation v7 → v8
- [docs/PRODUCTION_RULES.md](docs/PRODUCTION_RULES.md) — Contraintes de génération vidéo IA
