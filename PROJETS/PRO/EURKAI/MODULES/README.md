# EURKAI MODULES

Système modulaire pour créer des pages web en scrapant et reproduisant le design de sites existants.

## Architecture

```
Site web existant
      ↓
┌─────────────────┐
│ 1. SCRAPER      │ → Extrait styles réels (computed styles)
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. THEME        │ → Analyse + Règles d'harmonie + LLM
│    COMPOSER     │ → Crée ThemePreset (seed propriétaire)
└────────┬────────┘
         ↓
┌─────────────────┐
│ 3. THEME        │ → Génère CSS complet
│    GENERATOR    │ → Applique règles d'harmonie
└────────┬────────┘
         ↓
┌─────────────────┐
│ 4. PAGE         │ → Rend page HTML
│    BUILDER      │ → Modules réutilisables
└─────────────────┘
```

## Modules

### 1. Scraper (`scraper/`)

**Rôle** : Extraire les design tokens d'un site web.

**Fonctionnalités** :
- Parse HTML avec Playwright
- Extrait `getComputedStyle()` de tous les éléments visibles
- Groupe par type de composant (buttons, inputs, cards, headings)
- Capture screenshot pour analyse LLM
- API FastAPI indépendante

**Usage** :
```python
from scraper import SiteScraper

scraper = SiteScraper()
raw_styles = scraper.scrape("https://stripe.com")

# Résultat :
# - colors: ["rgb(102, 126, 234)", ...]
# - shadows: ["0 4px 6px rgba(0,0,0,0.1)", ...]
# - fonts: ["Inter, sans-serif", ...]
# - component_styles: {buttons: [...], inputs: [...]}
# - screenshot_base64: "..."
```

### 2. Theme Composer (`theme_composer/`)

**Rôle** : Transformer tokens bruts → ThemePreset cohérent.

**Fonctionnalités** :
- **Clustering couleurs** (K-means HSL) → primary/secondary/neutral
- **Détection relations** (lighten, darken, alpha)
- **Analyse patterns** (comment les boutons utilisent les couleurs)
- **Matching Google Fonts** (+ fallbacks intelligents)
- **Analyse LLM** (mood, use_case, caractéristiques)

**Usage** :
```python
from composer import ThemeComposer

composer = ThemeComposer()
preset = composer.compose(
    raw_data=raw_styles.model_dump(),
    screenshot_base64=raw_styles.screenshot_base64
)

# Résultat : ThemePreset
# - name: "Modern SaaS"
# - mood: "minimal"
# - use_case: "saas"
# - color_system: {primary: {base, light, dark}, secondary: {...}}
# - font_family_headings: "Inter"
# - shadow_system: {sm, md, lg, xl}
# - button_pattern: {...}
```

### 3. Theme Generator (`theme_generator/`)

**Rôle** : Générer CSS complet à partir du ThemePreset.

**Fonctionnalités** :
- Génère variables CSS (60+ dérivées)
- Applique patterns détectés aux composants
- Crée styles harmonieux (boutons, inputs, cards, modules)

**Usage** :
```python
from generator import ThemeGenerator

generator = ThemeGenerator()
css = generator.generate(preset.model_dump())

# Résultat : CSS complet
# - @import Google Fonts
# - :root { --color-primary: ...; }
# - .btn-primary { ... }
# - .hero { ... }
```

### 4. Page Builder (`page_builder/`)

**Rôle** : Construire des pages modulaires.

**Modules** : Hero, Pricing, Testimonials, Proof, Text, CTA

**Usage** : Voir `page_builder/README.md`

---

## Pipeline complet

**Exemple** :
```bash
python example_pipeline.py https://stripe.com --output ./output
```

**Étapes** :
1. Scrape https://stripe.com
2. Analyse et crée ThemePreset
3. Génère CSS
4. Crée page démo HTML

**Fichiers générés** :
- `stripe.com_raw.json` (tokens bruts)
- `stripe.com_preset.json` (seed propriétaire)
- `stripe.com_theme.css` (CSS complet)
- `stripe.com_demo.html` (page de démo)

---

## Installation

```bash
# Scraper
cd scraper
pip install -e .
playwright install chromium

# Theme Composer
cd theme_composer
pip install -e .

# Theme Generator
cd theme_generator
pip install -e .

# Page Builder
cd page_builder
pip install -e .
```

---

## Variables d'environnement

```bash
# Pour analyse LLM (optionnel)
export ANTHROPIC_API_KEY="sk-ant-..."

# Pour matching Google Fonts (optionnel)
export GOOGLE_FONTS_API_KEY="..."
```

---

## Roadmap

**MVP (fait)** :
- ✅ Scraper avec computed styles
- ✅ Theme Composer avec règles d'harmonie
- ✅ Theme Generator
- ✅ Intégration LLM (Claude)
- ✅ Google Fonts matching

**Prochaines étapes** :
- [ ] API unifiée (orchestrateur des 3 modules)
- [ ] Catalogue de seeds pré-générés
- [ ] Interface web (upload screenshot → génère theme)
- [ ] Variantes automatiques (mutations de seed)
- [ ] Support use-cases spécifiques (e-commerce, blog, etc.)

---

## Licence

MIT
