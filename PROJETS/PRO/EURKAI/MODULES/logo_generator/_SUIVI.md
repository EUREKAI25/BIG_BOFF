# logo_generator — Suivi

## Objectif
Module EURKAI de génération de logos vectoriels SVG via Recraft v3.
Produit 5 variantes par marque (logo, horizontal, icon, monochrome, favicon).

## Statut
🟢 Actif — v0.1.0 skeleton complet, en attente d'intégration model_executor

## Architecture

```
logo_generator/
├── logo_generator/
│   ├── __init__.py          ✅ exports publics
│   ├── schemas.py           ✅ BrandDNA, LogoDNA, ArbitrationConfig, LogoOutput
│   ├── prompt_builder.py    ✅ LogoDNA → prompts Recraft (concept + variantes)
│   ├── generator.py         ✅ model_executor calls → N LogoConcept
│   ├── arbitration.py       ✅ none/ai/human selection
│   ├── vector_optimizer.py  ✅ normalize + flag_only (jamais de suppression)
│   ├── exporter.py          ✅ 5 variantes → SVG files sur disque
│   └── router.py            ✅ POST /v1/logo/generate (FastAPI)
├── pyproject.toml           ✅
├── MANIFEST.json            ✅
└── _SUIVI.md                ✅ (ce fichier)
```

## Décisions d'architecture clés

### BrandDNA / LogoDNA
- `BrandDNA` = racine commune à tous les modules visuels
- `LogoDNA extends BrandDNA` avec : symbol_preference, composition_style, wordmark_weight, icon_complexity, background_mode
- Pas de DesignDNA générique — BrandDNA est la racine

### Pipeline
1. `generate_concepts()` → N prompts Recraft → N LogoConcept avec SVG + flags
2. `select_concept()` → selon ArbitrationMode (none/ai/human)
3. `export_variants()` → 5 prompts dédiés → 5 SVG fichiers

### vector_optimizer
- **RÈGLE ABSOLUE** : flag uniquement, jamais de suppression de shapes
- Opérations autorisées : normaliser viewBox, supprimer groupes vides, nettoyer commentaires
- Flags : FLAG_BG_RECT, FLAG_INVISIBLE_SHAPE, FLAG_FULL_SIZE_RECT

### Arbitration
- `none` → concept[0] automatiquement
- `ai` → scoring heuristique (flags = pénalités) → meilleur score
- `human` → retourne all_concepts, attente sélection manuelle via /v1/logo/select (à implémenter)

### Background
- `background_mode = "transparent"` par défaut
- Prompt force : "transparent background, no background fill"
- vector_optimizer FLAG les rects suspects mais ne les supprime jamais

### Variantes
Chaque variante = prompt dédié Recraft (pas de dérivation programmatique) :
- `logo.svg` — layout principal
- `logo_horizontal.svg` — icône + texte en ligne
- `logo_icon.svg` — icône seule
- `logo_monochrome.svg` — monochrome noir
- `favicon.svg` — ultra-simplifié 16px

## Historique

| Date       | Action |
|------------|--------|
| 2026-03-15 | Création du module (skeleton complet v0.1.0) |
| 2026-03-15 | Ajout LogoStructure (9 types) — règles de composition par structure dans prompt_builder |

## Prochaines étapes

- [ ] Intégrer `model_executor` EURKAI (import réel)
- [ ] Implémenter `POST /v1/logo/select` (mode human — 2e appel)
- [ ] Tests unitaires (prompt_builder, vector_optimizer, arbitration)
- [ ] Connecter à `pipeline_validator` (ContractRegistry auto depuis MANIFEST.json)
- [ ] Intégrer dans DCL (DesignCapability : generate_logo_concepts, select_logo, export_logo_variants)
