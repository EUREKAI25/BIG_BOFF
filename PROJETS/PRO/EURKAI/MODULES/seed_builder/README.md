# seed_builder — Analyseur de maquettes EURKAI

Génère des **seeds de pages** à partir de maquettes/wireframes analysés par Claude Vision.

La seed est la **source de vérité unique** qui pilote :
- Le renderer (quels blocs afficher, quelle structure)
- L'admin (quels champs proposer à l'édition)
- L'agent de contenu (quoi remplir depuis un brief)

## Flux

```
mockups/landing_a.png
       ↓ Claude Vision
seeds/landing_a.json      ← PageSeed (sections + fields)
mockups/_done/landing_a.png
```

## Usage

### En ligne de commande

```bash
pip install -e .

# Analyser une image
seed-build analyze mockups/landing_a.png --id landing_service_a

# Traiter toutes les maquettes en attente
seed-build watch

# Afficher le résumé d'une seed
seed-build show seeds/landing_service_a.json
```

### En Python

```python
from seed_builder import MockupAnalyzer, process_pending_mockups

# Analyser une image
analyzer = MockupAnalyzer()  # lit ANTHROPIC_API_KEY
seed = analyzer.analyze("mockups/landing_a.png")
print(seed.sections)

# Traiter toutes les images en attente (session-start)
process_pending_mockups(mockups_dir="mockups/", seeds_dir="seeds/")
```

## Structure des répertoires

```
seed_builder/
├── mockups/          ← déposer les images ici
│   └── _done/        ← archivage automatique après traitement
├── seeds/            ← seeds JSON générées
└── seed_builder/
    ├── schemas.py    ← PageSeed, SeedSection, SeedField (Pydantic)
    ├── analyzer.py   ← Claude Vision → PageSeed
    ├── watcher.py    ← traitement batch + archivage
    └── cli.py        ← commandes seed-build
```

## Format de la seed

```json
{
  "template_id": "landing_service_a",
  "page_type": "landing",
  "description": "Landing avec hero + bénéfices + pricing",
  "responsive": {
    "mobile": "100%", "tablet": "768px", "desktop": "1200px"
  },
  "sections": [
    {
      "key": "hero",
      "order": 1,
      "block_type": "hero_block",
      "full_width": true,
      "structure": { "bg_type": "image", "min_height": "90vh", "text_position": "left" },
      "fields": [
        { "key": "title",     "label": "Titre principal", "type": "text",     "required": true },
        { "key": "subtitle",  "label": "Sous-titre",      "type": "textarea"  },
        { "key": "cta_label", "label": "Texte du bouton", "type": "text"      },
        { "key": "bg_src",    "label": "Image de fond",   "type": "image"     }
      ]
    }
  ]
}
```

## Blocs disponibles

| block_type | Usage |
|---|---|
| `hero_block` | Grande section d'accroche |
| `navbar_block` | Navigation |
| `stat_block` | Chiffres/stats en ligne |
| `steps_block` | Étapes ou bénéfices en colonnes |
| `faq_block` | Questions/réponses |
| `pricing_block` | Cartes tarifaires |
| `cta_block` | Appel à l'action |
| `testimonial_block` | Témoignages |
| `content_block` | Texte + image générique |
| `footer_block` | Pied de page |
