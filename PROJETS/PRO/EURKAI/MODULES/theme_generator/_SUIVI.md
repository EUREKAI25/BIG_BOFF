# _SUIVI — Module `theme_generator`

> Module EURKAI — Générateur de CSS dynamique à partir d'un ThemePreset
> Créé le : 2026-03-14

---

## État actuel

**Version :** 0.1.0 (en cours d'architecture pour v2/v3)
**Statut :** 🟢 Actif — architecture v3 validée, Phase 1 imminente
**Package :** `eurkai-theme-generator` (installable via pip)

---

## Ce que fait le module (périmètre actuel)

### Point d'entrée

```python
from theme_generator import ThemeGenerator
gen = ThemeGenerator()

gen.generate(preset)            # CSS complet
gen.generate_variables(preset)  # Uniquement :root { ... }
```

### Ce qu'il génère

À partir d'un `ThemePreset` (dict), il produit du **CSS pur** (pas de SCSS compilé) :

| Méthode | Contenu généré |
|---|---|
| `generate_variables()` | Bloc `:root { }` avec toutes les variables CSS |
| `generate()` | Variables + reset + utilitaires grid + composants |

### Variables CSS générées (`:root`)

- **Couleurs** : `--color-primary`, `--color-primary-light/dark`, `--color-secondary-*`, couleurs sémantiques (text, bg, border) + adaptation dark mode
- **Shadows** : `--shadow-sm/md/lg/xl`
- **Border radius** : `--border-radius-sm/md/lg/xl`
- **Typographie** : `--font-family-headings/body`, tailles xs→4xl, poids, line-heights
- **Espacement** : `--spacing-xs/sm/md/lg/xl/2xl/3xl`
- **Animations** : `--transition-speed/easing/fast/base/slow`, `--hover-lift`, `--hover-scale`

### Composants générés (mode `generate()`)

- Reset CSS + base typographique
- Grid 12 colonnes responsive
- `.btn`, `.btn-primary`, `.btn-secondary` (3 variants : filled/outline/ghost selon style preset)
- `.card` avec hover
- Inputs / textarea / select avec focus ring

### Style presets supportés

`rounded` | `flat` | `elevated` | `minimal` | `bold` | `dark`

Charge via `theme_composer.style_presets.get_style_preset()` — fallback sur valeurs par défaut intégrées si `theme_composer` absent.

### Animation styles

`none` | `subtle` | `moderate` | `rich`

---

## Architecture / dépendances

```
theme_generator/
├── generator.py         # ThemeGenerator + helpers privés
├── __init__.py          # export ThemeGenerator, version 0.1.0
└── pyproject.toml       # package eurkai-theme-generator, dépend pydantic>=2.5
```

**Dépendance optionnelle :** `theme_composer` (style presets) — non inclus dans le package, résolu à l'import.

---

## Consommateurs connus

| Projet | Fichier | Usage |
|---|---|---|
| EURKAI/MODULES/page_builder | `src/renderer/css.py` | `generate_variables()` — fournit le `:root` ; page_builder gère le reste via SCSS |
| EURKAI/MODULES/AUTOSITES | `generate.py`, `api/main.py` | Génération CSS pour les sites auto |
| PRESENCE_IA | `libs/theme_generator/` (copie) | Idem — copie locale synchronisée manuellement |
| PRESENCE_IA | `src/api/routes/theme_admin.py` | Admin UI (GET/POST `/admin/theme`) — stocke le ThemePreset en SQLite, appelle `invalidate_scss_cache()` après save |

---

## Limites actuelles (v0.1.0)

- Génère du CSS pur uniquement — pas de compilation SCSS réelle
- Pas de tests unitaires dans le package
- Couleurs dérivées (light/dark) doivent être fournies explicitement dans le preset — pas de calcul automatique depuis une seule couleur de base
- Pas de support HSL / hex natif — attend du `rgb(...)` en entrée
- `theme_composer` (style presets) est une dépendance externe non packagée — couplage fragile
- Copie dans PRESENCE_IA synchronisée manuellement → risque de divergence

---

## Historique des modifications

| Date | Action |
|---|---|
| 2026-02-20 | Création initiale v0.1.0 (synchrone avec page_builder v0.1.0) |
| 2026-03-14 | Création _SUIVI.md + _SPECS.md v1 — état de l'art documenté |
| 2026-03-14 | _SPECS.md v2 — tags ouverts (List[str]), shape_library, texture_library, variantes, font_roles, theme_resolver |
| 2026-03-14 | _SPECS.md v3 — pipeline décision explicite 6 étapes, CompatibilityEngine, contraintes hard/strong/soft/bonus, AestheticBudgets, cohérence famille, DecisionTrace, dérive combinatoire formalisée |
| 2026-03-14 | _SPECS_PLATFORM.md v1 — Design Capability Layer (DCL) au-dessus du VIE : capabilities, endpoints, workflows, recipes SaaS, artefacts, ExecutionTrace |
| 2026-03-15 | Création module `pipeline_validator` MVP (ContractRegistry, PipelineValidator, router FastAPI — POST /v1/pipeline/prevalidate) |
| 2026-03-15 | Création catalogue `EURKAI/catalogs/seeds/` (LandingPageSeed, WebsiteSeed, SaaSSeed + index.json) |
| 2026-03-15 | Création module `logo_generator` v0.1.0 complet (schemas, prompt_builder, generator, arbitration, vector_optimizer, exporter, router) |

---

## Architecture cible (v3) — résumé

Voir `_SPECS.md` pour le détail complet.

**Nouveau pipeline :**
`ThemeDNA → ThemeInterpreter → CandidateSelector → CompatibilityEngine → ThemeResolver → ThemeCompiler → Renderer`

**Nouveaux modules VIE à créer :**
`theme_dna` · `theme_interpreter` · `candidate_selector` · `compatibility_engine` · `theme_resolver` · `theme_compiler` · `variant_engine` · `decision_trace` · `palette_system` · renderers (CSS/SCSS/JSON)

**Couche DCL au-dessus du VIE (voir `_SPECS_PLATFORM.md`) :**
`capabilities` · `endpoints` · `workflows` · `recipes` · `schemas` · `artifacts` · `execution_trace`
→ Cible finale : package `eurkai-design-platform` dans `EURKAI/MODULES/design_platform/`

**Nouvelles bibliothèques :**
`border_library` · `shape_library` · `texture_library` · `ornament_library` · `typography_profiles` · `icon_library` · `layout_patterns` · `motion_profiles`

**`generator.py` existant : inchangé — rétrocompat v1 garantie**

---

## Prochaine étape

Phase 1 — Foundation :
- [ ] `theme_dna.py` (ThemeDNA, FontRoles, PaletteProfile — tags List[str])
- [ ] `palette_system.py` (normalisation hex/rgb/hsl, dérivation auto)
- [ ] `theme_tokens.py` (ThemeTokens, ThemeVariant)
- [ ] `constraints.py` (ConstraintSet, AestheticBudgets, BudgetState)
- [ ] Tests unitaires

---
