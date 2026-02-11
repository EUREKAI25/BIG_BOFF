# AI_SEO_AUDIT

> Service d'audit et d'optimisation de la visibilité des entreprises dans les réponses des intelligences artificielles (ChatGPT, Claude, Gemini, etc.)

## Contexte

Les IA conversationnelles deviennent des intermédiaires directs de recommandation. Leurs critères de visibilité diffèrent du SEO classique (pas de backlinks, pas de Google Ads). Ce projet propose un service d'audit automatisé pour mesurer et améliorer la visibilité des entreprises dans les réponses IA.

## MVP (Phase 1)

- **Scope** : Mono-IA (ChatGPT uniquement)
- **Secteur test** : Restauration
- **Durée** : 2-3 jours
- **Stack** : Python + Flask/FastAPI + PostgreSQL + Redis

## Fonctionnalités MVP

1. **Audit automatisé** : interroger ChatGPT avec requêtes métiers
2. **Analyse comparative** : identifier concurrents cités
3. **Diagnostic** : causes d'absence/faible visibilité
4. **Interface basique** : formulaire paramétrage + affichage résultats

## Installation

*(À compléter après BUILD)*

```bash
# Créer environnement virtuel
python3 -m venv venv
source venv/activate

# Installer dépendances
pip install -r requirements.txt

# Configurer variables d'environnement
cp .env.example .env
# Éditer .env avec clés API

# Initialiser base de données
python src/setup_db.py

# Lancer serveur
python src/server.py
```

## Utilisation

*(À compléter après BUILD)*

## Architecture

Voir `PIPELINE/03_SPECS.md` pour l'architecture détaillée (objets EURKAI, modules, endpoints).

## Statut

Voir [_SUIVI.md](_SUIVI.md) pour le suivi détaillé du projet.

## Documentation

- [PIPELINE/01_BRIEF.md](PIPELINE/01_BRIEF.md) : Brief initial validé
- [PIPELINE/02_CDC.md](PIPELINE/02_CDC.md) : Cahier des Charges
- [PIPELINE/03_SPECS.md](PIPELINE/03_SPECS.md) : Spécifications techniques
- [_IDEES.md](_IDEES.md) : Idées d'améliorations futures
