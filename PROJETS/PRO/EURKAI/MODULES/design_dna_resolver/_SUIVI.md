# design_dna_resolver — Suivi

## Objectif
Point d'entrée du pipeline design EURKAI.
Convertit un brief (texte ou dict) en DesignDNA structuré consommable par tous les modules aval.
Zero LLM, sortie déterministe, standalone.

## Statut
🟢 Actif — v0.1.0 complet

## Architecture

```
design_dna_resolver/
├── schemas.py              ✅ BriefInput, PaletteBias, DesignDNA
├── brief_parser.py         ✅ parse dict structuré + extraction texte libre par mots-clés
├── concept_normalizer.py   ✅ normalisation industry/tone/audience → forme canonique
├── archetype_inference.py  ✅ vote pondéré → 12 archetypes (startup_clean, luxury_minimal...)
├── style_mapper.py         ✅ archetype → profil style complet (typo/icone/layout/visuel/palette)
├── dna_builder.py          ✅ orchestrateur → DesignDNA final
├── router.py               ✅ POST /v1/design/dna
└── __init__.py             ✅ resolve() = point d'entrée public
```

## Archetypes (12)
| Archétype | Secteurs typiques | Ton |
|---|---|---|
| luxury_minimal | luxury, fashion, beauty | premium, elegant |
| startup_clean | saas, fintech, tech | modern, minimal |
| editorial_magazine | fashion, media | editorial, bold |
| tech_futurist | gaming, technology | dark, neon |
| creative_studio | agences, design | vibrant, expressive |
| brutalist | art, architecture | raw, bold |
| organic_natural | eco, wellness, food | organic, warm |
| playful_brand | kids, food, B2C | fun, colorful |
| corporate_pro | finance, real_estate | professional |
| premium_craft | food_premium, artisan | artisan, warm |
| bold_challenger | sport, energy drinks | bold, dynamic |
| warm_human | nonprofit, healthcare | warm, accessible |

## Pipeline EURKAI
```
brief
  ↓
design_dna_resolver → DesignDNA
  ↓
color_psychology_engine (palette_bias)
  ↓
palette_generator
  ↓
logo_generator / font_generator / webdesign_generator / media_generator
```

## Exemple
```python
from design_dna_resolver import resolve

dna = resolve({
    "project_name": "NovaBank",
    "industry": "finance",
    "values": ["trust", "innovation"],
    "tone": "modern premium",
    "target_audience": "young professionals",
    "keywords": ["digital", "secure", "simple"],
})

print(dna.style_archetype)        # "startup_clean"
print(dna.typography_style)       # "geometric_sans"
print(dna.logo_structure_hint)    # "icon_wordmark"
print(dna.palette_bias.preferred_colors)  # ["electric_blue", "navy", "indigo"]
```

## Historique
| Date | Action |
|---|---|
| 2026-03-15 | Création v0.1.0 |

## Prochaines étapes
- [ ] Tests unitaires (inference correcte par secteur + tone)
- [ ] Enrichir extraction texte libre (brief_parser)
- [ ] Ajouter `region` dans le resolver (influence culturelle palette)
- [ ] Connecter formellement brand_generator → design_dna_resolver en première étape
- [ ] Valider les 12 archetypes avec des exemples réels
