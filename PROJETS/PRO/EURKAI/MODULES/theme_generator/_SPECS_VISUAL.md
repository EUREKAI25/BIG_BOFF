# theme_generator — Extension visuelle (v3+)

> Complément de `_SPECS.md` v3.
> Date : 2026-03-16

---

## Principe

Le `theme_generator` reste un compilateur déterministe. Il ne dépend pas d'images.

L'extension visuelle ajoute un pipeline **en amont** qui produit un `ThemePreset` depuis une source visuelle.

```
[NOUVEAU]   image / mockup / logo / preset manuel
                ↓
            visual_analysis          ← adaptateur pluggable
                ↓
            style_dna.json           ← structure intermédiaire
                ↓
            theme_translation        ← nouveau module
                ↓
[EXISTANT]  ThemePreset
                ↓
            theme_generator → SCSS
```

La chaîne existante `ThemePreset → theme_generator → SCSS` reste inchangée.

---

## 1. style_dna

Structure intermédiaire produite par `visual_analysis` et consommée par `theme_translation`.

```python
@dataclass
class StyleDNA:
    # Couleurs
    palette_profile: PaletteProfile         # couleurs dominantes + rôles sémantiques

    # Typographie (profils, pas de fonts identifiées)
    typography_profile: TypographyProfile   # display / body / accent profiles

    # Géométrie
    geometry_profile: GeometryProfile       # sharp / rounded / organic / angular
    border_profile: BorderProfile           # style de bordure dominant
    ornament_profile: OrnamentProfile       # densité, famille, placement

    # Layout
    layout_profile: LayoutProfile           # dense / spacious / editorial / grid

    # Ton
    emotional_tone: str                     # calm / bold / playful / premium / raw
    complexity_level: str                   # minimal / moderate / rich
    aesthetic_tags: List[str]               # ["brutalist", "editorial", "organic", ...]
```

### PaletteProfile

```python
@dataclass
class PaletteProfile:
    dominant: List[str]     # hex — 2-3 couleurs dominantes
    accent: List[str]       # hex — 1-2 couleurs d'accent
    neutral: List[str]      # hex — fond + texte
    temperature: str        # cold / neutral / warm
    saturation: str         # very_low / low / medium / high / very_high
    contrast: str           # low / medium / high
```

### TypographyProfile

```python
@dataclass
class TypographyProfile:
    display: str    # ex: "bold_condensed_geometric"
    body: str       # ex: "neutral_humanist_sans"
    accent: str     # ex: "handwritten_marker"  (optionnel)
```

Profils de display reconnus : `bold_condensed_geometric`, `thin_elegant_serif`, `grotesque_heavy`, `editorial_contrast`, `tech_mono`, `playful_rounded`, `neutral_sans`

Profils de body reconnus : `neutral_humanist_sans`, `warm_serif`, `editorial_serif`, `geometric_sans`, `readable_slab`

### GeometryProfile

```python
@dataclass
class GeometryProfile:
    border_radius: str   # none / sharp / small / medium / large / circular
    shape_family: str    # geometric / organic / irregular / strict
    stroke_weight: str   # thin / regular / bold / heavy
    symmetry: str        # strict / balanced / free
```

### OrnamentProfile

```python
@dataclass
class OrnamentProfile:
    has_ornaments: bool
    family: Optional[str]           # ex: "candles", "botanical", "geometric_frame"
    density: str                    # none / light / medium / heavy
    placement: List[str]            # ["top", "corners", "scattered"]
    rendering: str                  # svg_parametric / pattern / asset_pack / none
```

### LayoutProfile

```python
@dataclass
class LayoutProfile:
    rhythm: str         # tight / balanced / spacious / editorial
    grid_type: str      # strict / modular / asymmetric / freeform
    density: str        # minimal / moderate / dense
```

---

## 2. visual_analysis — adaptateur pluggable

Interface unique. L'implémentation est interchangeable.

```python
def visual_analysis(source: VisualSource) -> StyleDNA:
    ...
```

```python
@dataclass
class VisualSource:
    type: str                       # "image" | "screenshot" | "logo" | "mockup" | "preset" | "manual"
    path: Optional[Path]            # fichier local
    url: Optional[str]              # URL
    raw_json: Optional[dict]        # injection directe (MVP / tests)
```

### Implémentations MVP (sans vision LLM)

| Impl | Description |
|---|---|
| `MockVisualAnalysis` | Retourne un `StyleDNA` hardcodé — pour tests |
| `JsonVisualAnalysis` | Lit un `style_dna.json` fourni manuellement |
| `PresetVisualAnalysis` | Convertit un `ThemePreset` existant en `StyleDNA` |

### Implémentations futures (hors MVP)

| Impl | Description |
|---|---|
| `ClaudeVisionAnalysis` | Claude Vision → StyleDNA |
| `GPTVisionAnalysis` | GPT-4V → StyleDNA |
| `HeuristicAnalysis` | Colorsys + statistiques pixel → StyleDNA partiel |

Sélection via config :

```python
visual_analysis = get_visual_analysis_adapter(config.visual_analysis_backend)
# config.visual_analysis_backend = "mock" | "json" | "preset" | "claude" | "gpt"
```

---

## 3. theme_translation

Convertit un `StyleDNA` en `ThemePreset` compatible avec le `theme_generator` existant.

```python
def translate(style_dna: StyleDNA) -> ThemePreset:
    ...
```

### Mapping principal

| StyleDNA | ThemePreset |
|---|---|
| `palette_profile.dominant[0]` | `primary_color` |
| `palette_profile.dominant[1]` | `secondary_color` |
| `palette_profile.accent[0]` | `accent_color` |
| `palette_profile.neutral` | `background_color`, `text_color` |
| `typography_profile.display` → font mapping | `heading_font` |
| `typography_profile.body` → font mapping | `body_font` |
| `geometry_profile.border_radius` | `border_radius_style` |
| `geometry_profile.stroke_weight` | → `shadow_style` |
| `layout_profile.rhythm` | `spacing_scale` |
| `complexity_level` | `animation_style` |
| `emotional_tone` → style preset | `style` (rounded/flat/elevated/minimal/bold/dark) |

### Font mapping (interne)

```python
FONT_MAP = {
    "display": {
        "bold_condensed_geometric": ["Anton", "Bebas Neue", "League Spartan"],
        "thin_elegant_serif":       ["Playfair Display", "Cormorant", "EB Garamond"],
        "grotesque_heavy":          ["Space Grotesk", "DM Sans", "Syne"],
        "editorial_contrast":       ["Fraunces", "Bodoni Moda"],
        "tech_mono":                ["JetBrains Mono", "Space Mono", "Fira Code"],
        "playful_rounded":          ["Nunito", "Fredoka", "Poppins"],
        "neutral_sans":             ["Inter", "Manrope", "Source Sans 3"],
    },
    "body": {
        "neutral_humanist_sans":    ["Inter", "Manrope", "Source Sans 3"],
        "warm_serif":               ["Lora", "Merriweather", "PT Serif"],
        "editorial_serif":          ["Playfair Display", "EB Garamond"],
        "geometric_sans":           ["DM Sans", "Jost", "Outfit"],
        "readable_slab":            ["Roboto Slab", "Zilla Slab"],
    }
}
```

### Tone → style preset

```python
TONE_TO_PRESET = {
    "premium": "minimal",
    "bold":    "bold",
    "calm":    "flat",
    "playful": "rounded",
    "raw":     "dark",
    "tech":    "dark",
}
```

---

## 4. Intégration dans v3

La `StyleDNA` s'insère comme **source alternative** au `ThemeDNA` de la chaîne v3.

```
[v3]    ThemeDNA  ──────────────────────────────→ VIE pipeline → ThemePreset
                                                                       ↓
[ext]   StyleDNA → theme_translation → ThemePreset → theme_generator → SCSS
```

Pour le MVP : `theme_translation` court-circuite le VIE et produit directement un `ThemePreset`.
Quand le VIE sera implémenté, `StyleDNA` pourra être mappé vers `ThemeDNA` pour passer par la chaîne complète.

---

## 5. Nouveaux fichiers à créer

```
theme_generator/
├── generator.py              (inchangé)
├── style_dna.py              ← nouveaux dataclasses StyleDNA + sous-profils
├── visual_analysis.py        ← interface + adapters MVP (mock, json, preset)
├── theme_translation.py      ← StyleDNA → ThemePreset
└── font_map.py               ← FONT_MAP + TONE_TO_PRESET
```

Aucun fichier existant modifié.

---

## 6. Priorités MVP

| Étape | Livrable | Dépendance |
|---|---|---|
| 1 | `style_dna.py` — dataclasses | aucune |
| 2 | `font_map.py` — mappings | aucune |
| 3 | `theme_translation.py` | style_dna + font_map |
| 4 | `visual_analysis.py` — adapters mock/json/preset | style_dna |
| 5 | Tests : `StyleDNA` → `ThemePreset` → CSS | tout ce qui précède |

Phase vision LLM : hors MVP — branchée sur `visual_analysis` interface sans modifier le reste.
