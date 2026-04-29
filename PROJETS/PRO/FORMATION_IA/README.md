# FORMATION_IA

Offre de formation IA pour entreprises françaises construite sur le module EURKAI `training_generator`.

## Prérequis

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key   # ou via .env EURKAI
```

## Lancer la démo

```bash
cd PROJETS/PRO/EURKAI/CODE/eurkai_core
python ../../FORMATION_IA/demo/run_demo.py
```

La démo génère une formation complète sur "Utiliser l'IA dans son travail quotidien" et exporte :
- `demo/output_demo.json` — structure complète
- `demo/output_demo.html` — rendu consultable dans le navigateur

## Structure du module

```python
from modules.training_generator import run

result = run({
    "topic":      "Votre sujet",
    "level":      "beginner",          # beginner | intermediate | advanced
    "objectives": ["objectif 1", ...],
    "logics":     ["editorial", "technical", "operational"],  # logiques à activer
    "format":     "standard",          # short | standard | long
    "catalog":    catalog,             # None = mode déterministe
})
```

## Architecture

```
FORMATION_IA/
├── _SUIVI.md           — suivi du projet
├── README.md           — ce fichier
├── demo/               — démo exécutable
│   ├── run_demo.py     — script de génération
│   ├── output_demo.json
│   └── output_demo.html
└── manifests/          — manifests offres A/B/C (à venir)
```
