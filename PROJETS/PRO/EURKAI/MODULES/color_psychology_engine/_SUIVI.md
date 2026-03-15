# color_psychology_engine — Suivi

## Objectif
Fournir des recommandations colorées sémantiques basées sur la psychologie des couleurs.
Alimente `palette_generator` — ne génère pas de palettes lui-même.

## Statut
🟢 Actif — v0.1.0 complet

## Architecture

```
color_psychology_engine/
├── schemas.py              ✅ PsychologyInput, ColorRecommendation
├── industry_color_map.py   ✅ 19 secteurs + aliases (profils preferred/accent/neutral/avoid)
├── emotion_color_map.py    ✅ 40+ émotions, 16 tones, 10 audiences, 14 style_tags
├── weighting_engine.py     ✅ ColorScoreAggregator (vote pondéré)
├── suggestion_resolver.py  ✅ orchestration + résolution temperature/saturation/contrast
├── router.py               ✅ POST /v1/color/psychology
└── __init__.py             ✅ exports publics
```

## Poids des signaux
| Source | Poids |
|---|---|
| industry | 40% |
| brand_values | 30% |
| tone | 20% |
| style_tags | 7% |
| exploration | 3% |

L'audience est un modificateur (pas une source indépendante).

## Secteurs couverts (19)
finance, fintech, healthcare, technology, saas, luxury, fashion, food, food_premium,
wellness, sport, education, real_estate, eco, gaming, nonprofit, beauty, kids, travel

## Émotions / valeurs (40+)
trust, authority, stability, energy, innovation, nature, premium, warmth, playful,
minimal, clinical, precision, disruption, creativity, calm, elegance...

## Output → palette_generator
```python
from color_psychology_engine import get_color_recommendation, PsychologyInput
from palette_generator import generate_palette
from palette_generator.schemas import PaletteInput, PaletteScenario

rec = get_color_recommendation(PsychologyInput(industry="finance", tone="premium"))
# rec.preferred_colors → ["navy", "deep_blue", ...]
# → utiliser pour guider le choix de base_color dans palette_generator
```

## Historique
| Date | Action |
|---|---|
| 2026-03-15 | Création v0.1.0 |

## Prochaines étapes
- [ ] Tests unitaires (weighting, resolver, secteurs edge cases)
- [ ] Ajouter `region` dans le resolver (ex: rouge = danger en Occident, chance en Asie)
- [ ] Connecter formellement `brand_generator` → `color_psychology_engine` → `palette_generator`
- [ ] Ajouter mapping `ColorRecommendation` → `PaletteInput.style_tags` dans palette_generator
