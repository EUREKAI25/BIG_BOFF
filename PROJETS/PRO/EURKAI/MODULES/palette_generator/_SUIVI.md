# palette_generator — Suivi

## Objectif
Module EURKAI standalone de génération de palettes chromatiques.
Entièrement algorithmique (Python stdlib colorsys) — aucun LLM, aucune dépendance externe requise.
Pillow optionnel pour l'export PNG.

## Statut
🟢 Actif — v0.1.0 complet

## Architecture

```
palette_generator/
├── palette_generator/
│   ├── __init__.py                ✅ exports publics
│   ├── schemas.py                 ✅ ColorValue, TonalScale, Palette, PaletteSet, I/O, enums
│   ├── color_utils.py             ✅ conversions hex↔rgb↔hsl, WCAG luminance, tint/shade/rotate
│   ├── harmony_engine.py          ✅ 6 harmonies + minimal (algorithmes HSL)
│   ├── color_scale_generator.py   ✅ scales 100→900 (courbe non-linéaire, réduction saturation extrêmes)
│   ├── bw_palette_generator.py    ✅ false_blacks / false_whites influencés par la teinte de base
│   ├── metal_palette_generator.py ✅ 8 finitions + auto-détection selon teinte d'entrée
│   ├── contrast_validator.py      ✅ WCAG AA/AAA + correction auto lightness + ui_safe
│   ├── palette_scenarios.py       ✅ 7 scénarios avec règles de composition
│   ├── palette_exporter.py        ✅ palette.json, design_tokens.json, palette.svg, palette.png
│   ├── generator.py               ✅ orchestrateur principal
│   └── router.py                  ✅ POST /v1/palette/generate (FastAPI)
├── pyproject.toml                 ✅
├── MANIFEST.json                  ✅
└── _SUIVI.md                      ✅ (ce fichier)
```

## Décisions d'architecture clés

### Standalone total
- Aucune dépendance sur logo_generator, brand_generator, ou autres modules EURKAI
- BrandDNAInput défini localement (champs utiles seulement)
- Pillow optionnel (install extra `[png]`)

### Algorithmes
- **Harmonies** : calculs HSL purs via colorsys (stdlib)
- **Scales 100→900** : courbe non-linéaire + réduction saturation aux extrêmes (comportement Adobe/Tailwind)
- **BW** : 3 familles (warm/cool/green) selon la teinte H de la couleur de base
- **Metal** : 8 profils de référence + blend 20% teinte d'entrée + auto-détection
- **WCAG** : luminance relative + ratio, correction par pas de 5% lightness

### Scénarios
7 scénarios configurent automatiquement les harmonies générées, WCAG, metal, etc. :

| Scénario | Harmonies | BW | Metal | WCAG |
|---|---|---|---|---|
| brand_palette | comp + analog + mono + triad | ✅ | ✅ | ❌ |
| ui_palette | comp + mono + analog | ✅ | ❌ | ✅ AA |
| illustration_palette | analog + triad + tetrad + split | ✅ | ❌ | ❌ |
| minimal_palette | mono | ✅ | ❌ | ✅ AA |
| dark_mode_palette | mono + comp | ✅ | ✅ | ✅ AA |
| data_visualization_palette | triad + tetrad + split | ❌ | ❌ | ✅ AA |

### Design tokens
Format : `{"color.primary.500": "#3B82F6", "color.background": "#FFF", ...}`
Compatible Tailwind CSS, Style Dictionary, Figma Tokens.

### Couche Content (à implémenter)
Selon le prompt original, les Content objects appellent palette_generator :
```python
ImageContent.get_palette(base_color, scenario="illustration_palette")
UIContent.get_palette(base_color, scenario="ui_palette")
LogoContent.get_palette(base_color, scenario="brand_palette")
```
→ À créer dans un module `content_types` séparé (pas dans palette_generator).

## Historique

| Date       | Action |
|------------|--------|
| 2026-03-15 | Création du module (skeleton complet v0.1.0) |

## Prochaines étapes

- [ ] Tests unitaires (color_utils, harmony_engine, contrast_validator, scale_generator)
- [ ] Créer module `content_types` avec ImageContent, UIContent, LogoContent
- [ ] Connecter `brand_generator.BrandDirection.palette_profile` → `PaletteInput`
- [ ] Connecter `theme_generator` pour consommer les design_tokens
- [ ] Valider les algorithmes visuellement (générer des swatches de test)
