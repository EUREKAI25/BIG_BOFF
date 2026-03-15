# brand_generator — Suivi

## Objectif
Générer 3 directions créatives de marque (BrandDirection A/B/C) cohérentes et distinctes
à partir d'un project_brief + BrandDNA.
Point d'entrée stratégique du pipeline design EURKAI — guide tous les modules en aval.

## Statut
🟢 Actif — v0.1.0 skeleton complet, en attente d'intégration llm_executor

## Architecture

```
brand_generator/
├── brand_generator/
│   ├── __init__.py           ✅ exports publics
│   ├── schemas.py            ✅ BrandDNA, PaletteProfile, TypographyProfile, BrandDirection, I/O
│   ├── analyzer.py           ✅ brief + BrandDNA → CreativeContext (axes de contraste par secteur)
│   ├── direction_builder.py  ✅ CreativeContext → prompt LLM + parse JSON → BrandDirection ×3
│   ├── generator.py          ✅ orchestration + retry LLM
│   └── router.py             ✅ POST /v1/brand/directions (FastAPI)
├── pyproject.toml            ✅
├── MANIFEST.json             ✅ downstream_contract documenté
└── _SUIVI.md                 ✅ (ce fichier)
```

## Décisions d'architecture clés

### BrandDNA
- `BrandDNA` importé depuis `logo_generator.schemas` (évite la duplication)
- Fallback local si `logo_generator` non installé

### Génération via LLM
- Appel `llm_executor` (texte, pas image) — distinct de `model_executor` (Recraft)
- Prompt structuré avec schéma JSON cible + valeurs autorisées par champ
- Retry automatique sur JSON invalide (max_retries=2)

### Axes de contraste
- `analyzer.py` infère les axes selon le secteur (`_SECTOR_CONTRAST_AXES` dict)
- 12 secteurs couverts (fintech, health, food, fashion, saas, education, etc.)
- Fallback générique : minimal/geometric | expressive/rounded | bold/editorial

### Compatibilité aval
Chaque BrandDirection mappe directement sur les inputs des modules aval :

| Module | Champs utilisés |
|---|---|
| `logo_generator` | logo_structure, symbol_preference, wordmark_weight, icon_complexity, style_tags, palette_profile |
| `font_generator` | typography_profile, style_tags, mood_keywords |
| `palette_generator` | palette_profile, style_tags, mood_keywords |
| `webdesign_generator` | layout_density, whitespace_level, grid_style, component_roundness, contrast_level |
| `image_generator` | image_style, illustration_style, motion_energy, mood_keywords |

### MANIFEST.json
- `downstream_contract` documente explicitement les champs par module aval
- Compatible `ContractRegistry` du `pipeline_validator`

## Historique

| Date       | Action |
|------------|--------|
| 2026-03-15 | Création du module (skeleton complet v0.1.0) |

## Prochaines étapes

- [ ] Intégrer `llm_executor` EURKAI (import réel)
- [ ] Tests unitaires (analyzer, direction_builder parse, schemas)
- [ ] Connecter `BrandDirection` → `LogoDNA` (mapper les champs logo)
- [ ] Connecter `BrandDirection` → inputs `palette_generator` / `font_generator`
- [ ] Enregistrer dans `pipeline_validator` ContractRegistry
