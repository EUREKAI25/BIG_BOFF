# visual_consistency_validator — Suivi

## Objectif
Valide la cohérence de tous les assets visuels générés contre un DesignDNA.
Runs AFTER all generation modules (logo, palette, font, icons, UI, media).
Zero LLM, sortie déterministe, standalone.

## Statut
🟢 Actif — v0.1.0 complet

## Architecture

```
visual_consistency_validator/
├── schemas.py              ✅ ValidationInput, CheckResult, ValidationReport + asset descriptors
├── palette_checker.py      ✅ preferred/avoid colors, saturation, temperature
├── typography_checker.py   ✅ style × archetype, weight_hint
├── icon_style_checker.py   ✅ style × archetype, corner_radius, weight
├── visual_style_checker.py ✅ image_style, composition, motion_energy
├── layout_checker.py       ✅ layout_style, visual_style, spacing, border_radius
├── scoring_engine.py       ✅ pondération normalisée → score global + statut
├── validator.py            ✅ orchestrateur → validate(input) → ValidationReport
├── router.py               ✅ POST /v1/design/validate
└── __init__.py             ✅ validate() = point d'entrée public
```

## Checkers et pondérations
| Checker | Poids | Asset requis |
|---|---|---|
| palette | 25 % | PaletteAsset |
| typography | 20 % | TypographyAsset |
| icon_style | 20 % | IconAsset |
| visual_style | 20 % | VisualAsset |
| layout | 15 % | UIThemeAsset |

Seuls les checkers dont l'asset est fourni sont exécutés.
Les poids sont renormalisés à 1.0 sur les checkers présents.

## Seuils
| Statut | Score |
|---|---|
| valid | ≥ 0.80 |
| needs_revision | 0.60 – 0.79 |
| rejected | < 0.60 |

## Exemple de sortie
```json
{
  "status": "valid",
  "overall_score": 0.91,
  "palette_score": 0.92,
  "typography_score": 1.0,
  "icon_style_score": 0.95,
  "visual_style_score": null,
  "layout_score": 0.93,
  "warnings": [],
  "suggestions": [],
  "threshold": 0.80
}
```

## Pipeline EURKAI
```
brief
  ↓
design_dna_resolver → DesignDNA
  ↓
color_psychology_engine → palette_generator
  ↓
logo_generator / font_generator / icon_font_generator / webdesign_generator / media_generator
  ↓
visual_consistency_validator → ValidationReport
```

## Historique
| Date | Action |
|---|---|
| 2026-03-15 | Création v0.1.0 |

## Prochaines étapes
- [ ] Tests unitaires (score correct par archétype + asset)
- [ ] Checker dédié `logo_checker` (logo_structure × DesignDNA)
- [ ] Option `verbose=True` pour inclure les CheckResults détaillés dans la réponse API
- [ ] Intégration dans le pipeline orchestrateur EURKAI
- [ ] Règles cross-checkers (ex: palette temperature × visual_style cohérence)
