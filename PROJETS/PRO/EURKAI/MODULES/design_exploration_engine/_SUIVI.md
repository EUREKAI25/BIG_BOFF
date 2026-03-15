# design_exploration_engine — Suivi

## Objectif
Génère N directions créatives distinctes à partir d'un DesignDNA.
Mime le processus agence : le client voit 2–5 pistes stylistiques différenciées.
Chaque direction est passable directement aux modules de génération aval.
Zero LLM, sortie déterministe, standalone.

## Statut
🟢 Actif — v0.1.0 complet

## Architecture

```
design_exploration_engine/
├── schemas.py              ✅ DesignDirection, ExplorationInput, ExplorationOutput
├── archetype_variator.py   ✅ sélection N archétypes distincts (source → natural → contrast → wild_card)
├── palette_variator.py     ✅ palette_bias sémantique par archétype
├── typography_variator.py  ✅ typography_style + wordmark_weight par archétype
├── direction_builder.py    ✅ assemble DesignDirection complète
├── direction_generator.py  ✅ orchestrateur → ExplorationOutput
├── router.py               ✅ POST /v1/design/explore
└── __init__.py             ✅ explore() = point d'entrée public
```

## Stratégie de variation

| Direction | Relation | Description |
|---|---|---|
| direction_1 | source | Fidèle au brief — archétype original |
| direction_2 | natural | Variation harmonieuse — archétype voisin |
| direction_3 | contrast | Direction contrastée — territoire différent |
| direction_4 | wild_card | Direction audacieuse — rupture créative |
| direction_5 | alternate | Exploration complémentaire |

## Familles de direction (6)
- `clean_modern` — startup_clean, corporate_pro, editorial_magazine
- `premium_luxury` — luxury_minimal, premium_craft, editorial_magazine
- `tech_futuristic` — tech_futurist, startup_clean, bold_challenger
- `creative_experimental` — creative_studio, brutalist, editorial_magazine
- `organic_nature` — organic_natural, warm_human, premium_craft
- `bold_energetic` — bold_challenger, tech_futurist, playful_brand

## Exemple
```python
from design_exploration_engine import explore

output = explore({
    "style_archetype": "startup_clean",
    "industry": "finance",
    "brand_values": ["trust", "innovation"],
    "tone": "modern_premium",
}, n_directions=3)

# direction_1 : Clean Tech      (startup_clean)    → fidèle au brief
# direction_2 : Corporate Pro   (corporate_pro)    → variation naturelle
# direction_3 : Editorial Bold  (editorial_magazine) → contraste créatif
```

## Pipeline EURKAI
```
brief
  ↓
design_dna_resolver → DesignDNA
  ↓
design_exploration_engine → [direction_1, direction_2, direction_3]
  ↓ (pour chaque direction)
palette_generator / logo_generator / font_generator / webdesign_generator / media_generator
  ↓
visual_consistency_validator
```

## Historique
| Date | Action |
|---|---|
| 2026-03-15 | Création v0.1.0 |

## Prochaines étapes
- [ ] Tests unitaires (diversité correcte des directions)
- [ ] Permettre de "fixer" une direction et régénérer les autres
- [ ] Ajouter un score de différenciation inter-directions
- [ ] Support de contraintes client (ex: "pas trop sombre", "doit rester tech")
- [ ] Connecter formellement à l'orchestrateur pipeline EURKAI
