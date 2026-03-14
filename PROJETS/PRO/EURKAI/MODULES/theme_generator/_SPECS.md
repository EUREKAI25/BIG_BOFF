# SPECS — Module `theme_generator` v3

> Architecture cible — moteur de décision esthétique
> Version : draft 3.0 | Date : 2026-03-14
> Changelog v3 : couche décision explicite, CompatibilityEngine, contraintes, budgets,
>                cohérence de famille, DecisionTrace, dérive combinatoire

---

## Préambule — Le vrai problème

Le risque n'est pas de manquer d'assets. C'est de produire un thème **incohérent** quand les
bibliothèques grossissent.

Symptômes typiques d'un mauvais moteur de décision :
- "meilleur score individuel" dans chaque dimension → résultat sans cohérence globale
- ornements festifs + typographie mono tech + texture metallic → clash
- system "en fait trop" dès que le DNA est riche → surcharge visuelle
- impossible d'expliquer pourquoi telle combinaison a été choisie

L'architecture v3 répond à ça avec une **pipeline de décision explicite** en 6 étapes,
des **budgets esthétiques**, un **scoring de cohérence de famille**, et une **trace complète**.

---

## 1. Architecture V3 — Vue d'ensemble

```
INPUT
  image | screenshot | mockup | logo | moodboard | preset | manual
         ↓ (analyseur IA externe)
      ThemeDNA (tags ouverts, style_tags, font_roles, requested_variants)
         ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │                  PIPELINE DE DÉCISION v3                        │
  │                                                                  │
  │  1. ThemeInterpreter                                             │
  │     normalise + enrichit + extrait contraintes                   │
  │         ↓ InterpretedDNA + ConstraintSet                        │
  │                                                                  │
  │  2. CandidateSelector                                            │
  │     interroge bibliothèques → sets de candidats scorés           │
  │         ↓ CandidateSets (top-K par dimension)                   │
  │                                                                  │
  │  3. CompatibilityEngine                                          │
  │     filtre hard constraints + ajuste scores + vérifie budgets    │
  │         ↓ FilteredCandidateSets + BudgetState                   │
  │                                                                  │
  │  4. ThemeResolver                                                │
  │     scoring cohérence famille + sélection finale                 │
  │         ↓ ResolvedAssets + DecisionTrace                        │
  │                                                                  │
  │  5. ThemeCompiler                                                │
  │     palette + typo + layout + motion + variantes                 │
  │         ↓ ThemeTokens (base + variants)                         │
  │                                                                  │
  │  6. Renderer                                                     │
  │     CSS | SCSS | JSON tokens | (futur: Figma, PDF)               │
  └──────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    CSS variables         SCSS tokens          JSON tokens
    + composants          (.scss files)       (app/print/brand)
    + DecisionTrace
```

---

## 2. Modules — Responsabilités précises

### 2.1 ThemeInterpreter

**Rôle :** Premier contact avec le ThemeDNA brut.
Normalise, enrichit, et prépare les contraintes de rendu.

Responsabilités :
- Normaliser les tags (lowercase, déduplication, expansion de synonymes)
- Inférer des tags implicites (`"festive"` → ajoute `"playful"`, `"colorful"` si absents)
- Détecter le contexte de rendu principal depuis `targets` (web → priorité lisibilité mobile, print → résolution, etc.)
- Construire le `ConstraintSet` : hard constraints issues du contexte + préférences depuis les tags
- Calculer les `AestheticBudgets` initiaux selon `complexity_level` et `visual_density`
- Produire un `InterpretedDNA` : ThemeDNA + tags inférés + ConstraintSet + AestheticBudgets

Ce module ne touche pas aux bibliothèques. Il ne fait que préparer.

```python
class ThemeInterpreter:
    def interpret(self, dna: ThemeDNA) -> InterpretedDNA:
        normalized  = self._normalize_tags(dna)
        inferred    = self._infer_tags(normalized)
        constraints = self._build_constraints(inferred)
        budgets     = self._calculate_budgets(inferred)
        return InterpretedDNA(dna=inferred, constraints=constraints, budgets=budgets)
```

---

### 2.2 CandidateSelector

**Rôle :** Interroger les bibliothèques et produire des sets de candidats.

Responsabilités :
- Pour chaque dimension (border, shape, texture, ornament, font×6_rôles, layout, motion),
  interroger la bibliothèque correspondante
- Scorer chaque candidat par tag matching (Jaccard entre DNA tags et asset tags)
- Limiter à top-K candidats par dimension (K configurable, défaut 8)
- **Ne filtre pas encore** — laisse CompatibilityEngine décider

```python
class CandidateSelector:
    def select(self, idna: InterpretedDNA) -> CandidateSets:
        return CandidateSets(
            border   = self._query(border_library,   idna, k=8),
            shapes   = self._query(shape_library,    idna, k=8),
            texture  = self._query(texture_library,  idna, k=8),
            ornament = self._query(ornament_library, idna, k=8),
            fonts    = self._query_fonts(typography_profiles, idna, k=5),
            layout   = self._query(layout_patterns,  idna, k=5),
            motion   = self._query(motion_profiles,  idna, k=5),
        )

    def _jaccard(self, dna_tags: List[str], asset_tags: List[str]) -> float:
        s1, s2 = set(dna_tags), set(asset_tags)
        if not s1 and not s2: return 0.0
        return len(s1 & s2) / len(s1 | s2)
```

---

### 2.3 CompatibilityEngine

**Rôle :** Arbitre de cohérence. Module central de la v3.

Responsabilités :
1. **Filtrage hard constraints** — élimine les candidats qui violent une contrainte dure
2. **Ajustement de scores** selon niveaux de préférences (×1.5, +0.2, +0.1)
3. **Vérification des incompatibilités** — pénalise les combinaisons interdites
4. **Gestion des budgets esthétiques** — accumule les coûts, réduit les scores si budget dépassé
5. **Compatibilité multi-support** — filtre selon `targets` (ex: glass texture → pas print)
6. Produit `FilteredCandidateSets` + `BudgetState` + liste des rejets documentés

```python
class CompatibilityEngine:
    def filter(self,
               candidates: CandidateSets,
               idna: InterpretedDNA) -> FilteredResult:

        rejected  = []
        adjusted  = candidates.copy()

        # 1. Hard constraints (élimine)
        adjusted, new_rejected = self._apply_hard_constraints(adjusted, idna.constraints)
        rejected += new_rejected

        # 2. Incompatibilités entre assets (pénalise paires)
        adjusted = self._apply_incompatibilities(adjusted)

        # 3. Compatibilité multi-support
        adjusted, new_rejected = self._filter_by_targets(adjusted, idna.dna.targets)
        rejected += new_rejected

        # 4. Niveaux de préférence (ajuste scores)
        adjusted = self._apply_preference_levels(adjusted, idna.constraints)

        # 5. Budgets (pénalise si coût > budget)
        adjusted, budget_state = self._apply_budgets(adjusted, idna.budgets)

        return FilteredResult(candidates=adjusted, rejected=rejected, budget_state=budget_state)
```

---

### 2.4 ThemeResolver

**Rôle :** Décision finale avec vision globale.

Responsabilités :
- Détecter la famille visuelle dominante (via clustering de tags)
- Calculer un bonus de cohérence inter-dimensions (voir section 5)
- Sélectionner le meilleur asset par dimension en tenant compte de la cohérence globale
- Conserver les alternatives (2e et 3e choix) pour la trace
- Produire `ResolvedAssets` + `DecisionTrace` complet

```python
class ThemeResolver:
    def resolve(self, filtered: FilteredResult, idna: InterpretedDNA) -> Resolution:
        family        = self._detect_family(idna.dna)
        cohered       = self._apply_family_coherence(filtered.candidates, family)
        final_choices = self._select_final(cohered)
        alternatives  = self._select_alternatives(cohered, final_choices)
        trace         = self._build_trace(idna, filtered, final_choices, alternatives, family)
        return Resolution(assets=final_choices, trace=trace)
```

---

### 2.5 ThemeCompiler

**Rôle :** Assemble les tokens.

Responsabilités :
- `palette_system` : hex → ColorTokens (dérivation light/dark/sémantiques)
- `font_roles` → TypographyTokens (6 rôles complets)
- `ResolvedAssets` → ShapeTokens, TextureTokens, BorderTokens, etc.
- `variant_engine` : calcule les overrides pour chaque variante demandée
- Produit le `ThemeTokens` complet

---

### 2.6 Renderer

**Rôle :** Traduit ThemeTokens en formats de sortie.

| Renderer | Output | Cible |
|---|---|---|
| `CSSRenderer` | CSS variables + composants | Web |
| `SCSSRenderer` | Fichiers `.scss` avec `$variables` | Web (build) |
| `JSONRenderer` | Design tokens JSON | App (RN/Flutter), Figma |
| `PrintRenderer` | CSS pour Paged.js / WeasyPrint | Print |
| `BrandRenderer` | (future phase) | Charte PDF |

Chaque renderer est indépendant et peut être invoqué seul.

---

## 3. Modèles de données v3

### 3.1 InterpretedDNA

```python
@dataclass
class InterpretedDNA:
    dna: ThemeDNA               # DNA original + tags inférés ajoutés
    inferred_tags: List[str]    # tags ajoutés par l'interpréteur (traçabilité)
    constraints: ConstraintSet
    budgets: AestheticBudgets
    render_context: RenderContext
```

### 3.2 ConstraintSet

```python
@dataclass
class ConstraintSet:
    hard_constraints:   List[Constraint]   # binaire pass/fail → élimine l'asset
    strong_preferences: List[Constraint]   # score × 1.5 si OK, × 0.6 si KO
    soft_preferences:   List[Constraint]   # score + 0.2 si OK, neutre si KO
    creative_bonuses:   List[Constraint]   # score + 0.1 si OK (encourage originalité)

@dataclass
class Constraint:
    id: str                     # ex: "mobile_readability"
    description: str
    level: str                  # "hard" | "strong" | "soft" | "bonus"
    applies_to: List[str]       # dimensions concernées ex: ["font_body", "motion"]
    condition: str              # expression lisible ex: "font_size_min >= 14px"
    source: str                 # "target:web:mobile" | "tone:serious" | "manual"
```

### Exemples de contraintes générées automatiquement

```python
# target: web → hard constraint automatique
Constraint(
    id="mobile_readability",
    level="hard",
    applies_to=["font_body", "font_data"],
    condition="min_readable_size >= 14px",
    source="target:web"
)

# style_tags contient "festive" → soft preference
Constraint(
    id="festive_ornaments",
    level="soft",
    applies_to=["ornament"],
    condition="ornament_family intersects ['festive', 'sparkle', 'botanical']",
    source="style_tag:festive"
)

# emotional_tone contient "luxe" → strong preference
Constraint(
    id="luxe_typography",
    level="strong",
    applies_to=["font_display", "font_accent"],
    condition="typography_tags intersects ['serif', 'editorial', 'luxe']",
    source="tone:luxe"
)

# creative_bonus : encourage une texture inattendue si originality_budget disponible
Constraint(
    id="unexpected_texture",
    level="bonus",
    applies_to=["texture"],
    condition="texture not in ['none', 'grain/light']",
    source="creative_engine"
)
```

### 3.3 AestheticBudgets

```python
@dataclass
class AestheticBudgets:
    """
    Chaque budget est une capacité totale à dépenser sur l'ensemble du thème.
    Les assets déclarent leur coût dans leurs métadonnées (aesthetic_costs).
    Si la somme des coûts sélectionnés dépasse le budget → pénalité de score progressive.
    """
    ornament_budget:     int   # 0-10  — quelle densité ornementale est acceptable
    complexity_budget:   int   # 0-10  — complexité globale (formes, effets, variantes)
    visual_noise_budget: int   # 0-10  — tolérance au bruit visuel (grain, textures lourdes)
    originality_budget:  int   # 0-10  — espace pour éléments inattendus
    motion_budget:       int   # 0-10  — intensité des animations

# Calcul automatique depuis InterpretedDNA
def calculate_budgets(dna: ThemeDNA) -> AestheticBudgets:
    c = dna.complexity_level  # 1-5
    d = {"sparse": 0, "balanced": 1, "dense": 2}.get(dna.visual_density, 1)
    return AestheticBudgets(
        ornament_budget     = c + d,          # 1-7
        complexity_budget   = c * 2,          # 2-10
        visual_noise_budget = c + d - 1,      # 0-6
        originality_budget  = 3,              # fixe par défaut, ajustable
        motion_budget       = c,              # 1-5
    )
```

### Application des budgets dans le scoring

```
Pour chaque asset sélectionné :
  budget_remaining -= asset.aesthetic_costs[budget_name]

  Si budget_remaining >= 0 : pas de pénalité
  Si budget_remaining == -1 : score × 0.8
  Si budget_remaining == -2 : score × 0.6
  Si budget_remaining < -2  : score × 0.3 (quasi-éliminé sauf si seul candidat)

Les budgets s'appliquent de façon cumulée : si texture + ornement + border consomment
ensemble trop d'ornament_budget → le moteur arbitre en faveur des assets à moindre coût.
```

### 3.4 BudgetState

```python
@dataclass
class BudgetState:
    """État des budgets après sélection — publié dans DecisionTrace."""
    budgets_initial:  AestheticBudgets
    costs_by_asset:   Dict[str, Dict[str, int]]   # asset_ref → {budget: coût}
    totals_used:      Dict[str, int]               # budget → coût total
    overruns:         List[BudgetOverrun]

@dataclass
class BudgetOverrun:
    budget_name:   str
    limit:         int
    used:          int
    overrun_by:    int
    affected_assets: List[str]
    penalty_applied: float
```

### 3.5 RenderContext

```python
@dataclass
class RenderContext:
    targets:            List[str]    # ["web", "app", "print", "brand"]
    primary_target:     str          # target principal pour les arbitrages
    mobile_first:       bool
    supports_animation: bool         # False pour print, True pour web/app
    supports_svg:       bool
    supports_custom_fonts: bool
```

---

## 4. Métadonnées des assets

Chaque asset dans chaque bibliothèque porte ces métadonnées dans son `index.json`.
C'est la base sur laquelle travaille le `CompatibilityEngine`.

### Structure d'entrée dans `index.json`

```json
{
  "id": "shape/wave/bottom_gentle",
  "label": "Wave bottom — douce",
  "category": "wave",
  "tags": ["wave", "organic", "soft", "section_divider", "gentle"],

  "compatibility": {
    "compatible_with": [
      "border/organic_soft",
      "texture/grain",
      "texture/paper",
      "ornament/botanical"
    ],
    "avoid_with": [
      "border/ornamental/candles",
      "texture/metallic"
    ],
    "forbidden_combinations": [
      {
        "assets": ["texture/metallic/gold", "ornament/botanical"],
        "reason": "clash matériaux : métal + nature organique"
      },
      {
        "assets": ["shape/wave", "border/hand_drawn", "texture/noise/heavy"],
        "reason": "triple surcharge visuelle organique"
      }
    ],
    "recommended_tones": ["warm", "organic", "soft", "nature", "health"],
    "not_recommended_for": ["print", "brand"]
  },

  "support": {
    "supports":    ["web", "app"],
    "not_for":     ["print"],
    "requires":    ["svg_support"],
    "degrades_to": "straight_border"
  },

  "constraints": {
    "min_complexity": 1,
    "max_complexity": 4,
    "min_visual_density": "sparse",
    "max_visual_density": "balanced",
    "not_with_tones": ["technical", "serious", "corporate"]
  },

  "aesthetic_costs": {
    "ornament_budget":     0,
    "complexity_budget":   1,
    "visual_noise_budget": 1,
    "originality_budget":  2,
    "motion_budget":       0
  },

  "assets": {
    "svg": "wave_bottom_gentle.svg",
    "css": "wave_bottom_gentle.css",
    "preview": "wave_bottom_gentle.png"
  },

  "meta": {
    "added": "2026-03-14",
    "version": "1.0",
    "author": "eurkai"
  }
}
```

---

## 5. Logique de scoring v3

### 5.1 Score initial (CandidateSelector)

```
score_initial = jaccard(dna_all_tags, asset_tags)

dna_all_tags = union de :
  geometry_profile + border_family + ornament_family +
  typography_profile + layout_profile + emotional_tone + style_tags
```

### 5.2 Ajustements CompatibilityEngine

```
# Hard constraint : binaire
if violates_hard_constraint(asset):
    score = 0 → éliminé, ajouté à rejected_candidates

# Incompatibilité pairwise
for other_selected_asset in current_selection:
    if asset.id in other_selected_asset.avoid_with:
        score *= 0.5   # pénalité forte mais pas éliminatoire

# Combinaison interdite (3+ assets)
if combination in asset.forbidden_combinations:
    score = 0 → éliminé avec raison documentée

# Multi-support
if primary_target not in asset.supports:
    score = 0 → éliminé

# Niveaux de préférence
for constraint in strong_preferences:
    if satisfies(asset, constraint): score *= 1.5
    else:                            score *= 0.6

for constraint in soft_preferences:
    if satisfies(asset, constraint): score += 0.2

for constraint in creative_bonuses:
    if satisfies(asset, constraint): score += 0.1

# Budgets (cumulatif sur ensemble sélection en cours)
budget_penalty = calculate_budget_penalty(asset, current_budget_state)
score *= (1.0 - budget_penalty)   # 0.0 → 0.7 selon dépassement
```

### 5.3 Bonus de cohérence de famille (ThemeResolver)

```
# Détection de la famille dominante
family = detect_dominant_family(dna_all_tags)
# ex: "editorial_warm_organic" si tags matchent famille à 70%+

# Pour chaque candidat, bonus si son profil appartient à la famille
FAMILY_BONUS = 0.15   # ajustable

for dimension, candidates in filtered_candidates:
    for candidate in candidates:
        family_alignment = jaccard(candidate.tags, family.preferred_tags[dimension])
        candidate.score += family_alignment * FAMILY_BONUS

# Effet : deux assets "moins bons" individuellement mais cohérents entre eux
# peuvent battre deux assets "meilleurs" mais discordants
```

### Familles visuelles définies (extensible via JSON)

```json
{
  "editorial_warm_organic": {
    "tags": ["editorial", "warm", "organic", "soft", "serif", "nature"],
    "preferred_per_dimension": {
      "typography": ["editorial", "serif", "luxe"],
      "border":     ["organic_soft", "hand_drawn"],
      "shape":      ["wave", "blob", "organic"],
      "ornament":   ["botanical", "minimal_dots"],
      "texture":    ["grain", "paper"],
      "layout":     ["editorial", "split", "asymmetric"]
    }
  },
  "minimal_tech_geometric": {
    "tags": ["minimal", "geometric", "tech", "clean", "sharp"],
    "preferred_per_dimension": {
      "typography": ["geometric", "mono", "technical"],
      "border":     ["straight", "thin"],
      "shape":      ["clip_paths", "asymmetric_panels"],
      "ornament":   [],
      "texture":    ["glass", "noise/subtle"],
      "layout":     ["card_grid", "structured"]
    }
  },
  "festive_playful_colorful": {
    "tags": ["festive", "playful", "colorful", "joyful", "celebration"],
    "preferred_per_dimension": {
      "typography": ["handwritten", "playful", "rounded"],
      "border":     ["ornamental", "festive"],
      "shape":      ["blobs", "stickers"],
      "ornament":   ["festive", "sparkle"],
      "texture":    ["none", "grain/light"],
      "layout":     ["centered", "hero_focus"]
    }
  }
  // ... extensible sans modifier le code — ajout via JSON uniquement
}
```

### 5.4 Score final

```
score_final = score_initial
            × compatibility_multipliers     # paires avoid_with
            × preference_multipliers        # strong_preferences
            + preference_addends            # soft + bonus
            + family_coherence_bonus        # cohérence famille
            × budget_penalty_factor         # dépassements budgets
```

---

## 6. DecisionTrace — format complet

Produit par `ThemeResolver`, attaché à chaque `ResolvedAssets`.
Permet de comprendre chaque décision, rejouer la résolution, auditer, débugger.

```json
{
  "version": "1.0",
  "timestamp": "2026-03-14T14:32:00Z",
  "theme_name": "Thalasso Editorial",

  "input": {
    "raw_dna_summary": "source: screenshot, complexity: 3, tone: [warm, organic, soft]",
    "normalized_tags": ["warm", "organic", "soft", "editorial", "nature", "wellness"],
    "inferred_tags":   ["botanical", "serif", "gentle"],
    "targets":         ["web", "app"],
    "render_context":  { "primary_target": "web", "mobile_first": true }
  },

  "constraints": {
    "hard_constraints": [
      { "id": "mobile_readability", "source": "target:web", "applied_to": ["font_body"] }
    ],
    "strong_preferences": [
      { "id": "organic_aesthetic",  "source": "tone:warm+organic",   "multiplier_ok": 1.5 }
    ],
    "soft_preferences": [
      { "id": "botanical_ornament", "source": "inferred_tag:botanical", "bonus": 0.2 }
    ],
    "creative_bonuses": [
      { "id": "unexpected_texture", "source": "creative_engine", "bonus": 0.1 }
    ]
  },

  "budgets_applied": {
    "ornament_budget":     { "limit": 4, "used": 3, "status": "ok" },
    "complexity_budget":   { "limit": 6, "used": 5, "status": "ok" },
    "visual_noise_budget": { "limit": 3, "used": 3, "status": "at_limit" },
    "originality_budget":  { "limit": 3, "used": 2, "status": "ok" },
    "motion_budget":       { "limit": 3, "used": 2, "status": "ok" }
  },

  "candidate_sets": {
    "border": [
      { "ref": "border/organic_soft/v1",  "initial_score": 0.72 },
      { "ref": "border/hand_drawn/rough", "initial_score": 0.61 },
      { "ref": "border/straight/default", "initial_score": 0.28 }
    ],
    "texture": [
      { "ref": "texture/grain/light",  "initial_score": 0.68 },
      { "ref": "texture/paper/cream",  "initial_score": 0.65 },
      { "ref": "texture/glass/frosted","initial_score": 0.31 }
    ]
  },

  "rejected_candidates": {
    "texture": [
      {
        "ref": "texture/metallic/gold",
        "reason": "forbidden_combination: texture/metallic + ornament/botanical",
        "score_at_rejection": 0.0
      }
    ],
    "motion": [
      {
        "ref": "motion/expressive",
        "reason": "hard_constraint: motion_budget dépassé (coût 5 > budget 3)",
        "score_at_rejection": 0.0
      }
    ]
  },

  "score_breakdown": {
    "border/organic_soft/v1": {
      "initial_tag_match":         0.72,
      "compatibility_multiplier":  1.0,
      "strong_preference_factor":  1.5,
      "soft_preference_bonus":     0.0,
      "creative_bonus":            0.0,
      "family_coherence_bonus":    0.15,
      "budget_penalty_factor":     1.0,
      "final_score":               1.23
    },
    "texture/paper/cream": {
      "initial_tag_match":         0.65,
      "compatibility_multiplier":  1.0,
      "strong_preference_factor":  1.5,
      "soft_preference_bonus":     0.0,
      "creative_bonus":            0.1,
      "family_coherence_bonus":    0.12,
      "budget_penalty_factor":     0.8,
      "final_score":               0.98,
      "note": "texture/grain/light éliminée car visual_noise_budget at_limit"
    }
  },

  "family_coherence": {
    "detected_family":     "editorial_warm_organic",
    "detection_confidence": 0.78,
    "dimension_alignment": {
      "typography": { "aligned": true,  "score": 0.85 },
      "border":     { "aligned": true,  "score": 0.80 },
      "shape":      { "aligned": true,  "score": 0.72 },
      "ornament":   { "aligned": true,  "score": 0.68 },
      "texture":    { "aligned": false, "score": 0.41, "note": "paper/cream choisi sur grain — cohérence légèrement moindre mais budget respecté" },
      "layout":     { "aligned": true,  "score": 0.77 }
    },
    "global_coherence_score": 0.82
  },

  "final_choices": {
    "border":   { "ref": "border/organic_soft/v1",   "final_score": 1.23 },
    "shapes":   [{ "ref": "shape/wave/bottom_gentle","final_score": 1.10 }],
    "texture":  { "ref": "texture/paper/cream",      "final_score": 0.98 },
    "ornament": { "ref": "ornament/botanical/spring", "final_score": 0.95 },
    "layout":   { "ref": "layout/editorial_split",   "final_score": 1.05 },
    "motion":   { "ref": "motion/subtle",            "final_score": 0.88 }
  },

  "alternative_choices": {
    "border": [
      { "ref": "border/hand_drawn/rough", "final_score": 0.79, "note": "plus original, moins cohérent avec texture paper" }
    ],
    "texture": [
      { "ref": "texture/grain/light", "final_score": 0.91, "note": "écarté : visual_noise_budget at_limit, paper/cream préféré" }
    ]
  },

  "explanation_summary": "Thème résolu comme 'editorial_warm_organic' (confiance 78%). La border organic_soft et l'ornement botanical sont fortement alignés avec les tones warm+organic. La texture paper/cream a été préférée à grain/light car le visual_noise_budget était à la limite après le shape wave. L'ornement metallic/gold a été rejeté (combinaison interdite avec botanical). Cohérence globale : 0.82/1.0."
}
```

---

## 7. Dérive combinatoire — formalisation

### Pourquoi le problème apparaît

Avec N dimensions et K candidats par dimension :
`combinations = K^N`

En pratique avec les bibliothèques EURKAI à maturité :
- 10 dimensions (border, 6×font_roles, shape, texture, ornament, layout, motion)
- 20 candidats par dimension en moyenne
- `20^10 = 10 240 000 000 000` combinaisons → intraitable

### À partir de quel seuil c'est critique

| Bibliothèque | Assets | Seuil critique atteint |
|---|---|---|
| < 10 assets/dim | ~5^10 = 10M | Non critique (greedy suffisant) |
| 10-30 assets/dim | ~20^10 = 10T | Critique sans architecture dédiée |
| > 30 assets/dim | > 30^10 | Impossible sans contraintes fortes |

EURKAI atteindra le seuil critique dès ~50 assets par bibliothèque (objectif à 6 mois).

### Comment l'architecture v3 le limite

**1. Filtrage précoce par étapes (pipeline séquentiel)**
Chaque étape réduit l'espace de recherche avant l'étape suivante :
- Hard constraints : élimine 40-70% des candidats avant tout scoring
- Incompatibilités : élimine 20-40% supplémentaires
- Top-K = 8 : cap absolu sur les candidats retenus par dimension

**2. Greedy avec cohérence globale (pas de recherche exhaustive)**
Le ThemeResolver ne cherche pas la combinaison globale optimale.
Il sélectionne dimension par dimension dans un ordre fixe,
en mettant à jour le budget et le score de cohérence à chaque choix.
Complexité : `O(N × K)` = linéaire, pas exponentielle.

Ordre de résolution (du plus contraint au moins contraint) :
```
1. font_body        (hard constraint mobile readability → filtre fort)
2. layout           (détermine le contexte spatial de tout le reste)
3. font_display     (contraint par layout)
4. border           (contraint par geometry_profile)
5. shape            (contraint par border + layout)
6. texture          (contraint par visual_noise_budget restant)
7. ornament         (contraint par ornament_budget restant)
8. font_accent/mono/data/button (contraints par font_display + body)
9. motion           (contraint par motion_budget restant)
```

**3. Bonus de cohérence de famille (évite la dispersion)**
Plutôt que chercher l'optimum global, on favorise les clusters cohérents.
Un asset "moyen mais familier" bat un asset "excellent mais isolé".
C'est ce qui évite les thèmes paradoxalement bons composant par composant
mais incohérents globalement.

**4. Budgets esthétiques (coupe les combinaisons trop chargées)**
Les budgets s'accumulent : si ornament + texture + border consomment
déjà tout le visual_noise_budget, la 4e dimension "bruitée" sera pénalisée
même si elle score bien individuellement.

**Résultat pratique :** complexité O(N × K) avec N=10, K=8 = 80 évaluations.
Extensible à des milliers d'assets sans changement d'architecture.

---

## 8. Bibliothèques — structure v3 (mise à jour)

```
theme_assets/
├── _families.json              ← familles visuelles (extension possible sans code)
├── border_library/
│   └── index.json              ← métadonnées complètes (compatible_with, aesthetic_costs...)
├── shape_library/
│   └── index.json
├── texture_library/
│   └── index.json
├── ornament_library/
│   └── index.json
├── typography_profiles/
│   └── index.json
├── icon_library/
│   └── index.json
├── layout_patterns/
│   └── index.json
├── motion_profiles/
│   └── index.json
└── palette_system/
    └── index.json
```

Chaque `index.json` suit la structure de métadonnées définie en section 4.
Le CompatibilityEngine charge ces index au démarrage (ou à chaque requête si hot-reload).

---

## 9. Pipeline complet v3

```
ThemeDNA (tags ouverts)
    │
    ▼ ThemeInterpreter
InterpretedDNA
├── dna enrichi (tags inférés)
├── ConstraintSet (hard / strong / soft / bonus)
├── AestheticBudgets (calculés depuis complexity + density)
└── RenderContext (targets, mobile_first, svg_support...)
    │
    ▼ CandidateSelector
CandidateSets
└── 10 dimensions × top-8 candidats scorés (Jaccard)
    │
    ▼ CompatibilityEngine
FilteredResult
├── FilteredCandidateSets (scores ajustés)
├── RejectedCandidates (avec raison documentée)
└── BudgetState (coûts accumulés)
    │
    ▼ ThemeResolver
Resolution
├── ResolvedAssets (sélection finale par dimension)
├── AlternativeAssets (2e/3e choix)
└── DecisionTrace (trace complète JSON)
    │
    ▼ ThemeCompiler
ThemeTokens
├── colors (dérivés auto)
├── typography (6 rôles)
├── spacing / radius / shadows
├── borders / shapes / textures / ornaments
├── layout / motion
└── variants (dark, soft, playful, editorial, high_contrast...)
    │
    ├── ▼ CSSRenderer      → CSS variables + composants
    ├── ▼ SCSSRenderer     → $variables + mixins
    ├── ▼ JSONRenderer     → design tokens (app / figma)
    └── ▼ PrintRenderer    → CSS Paged.js (future)
```

---

## 10. Plan de migration — mise en œuvre progressive

### Phase 1 — Foundation (rétrocompat garantie)
- [ ] `theme_dna.py` : ThemeDNA, FontRoles, FontSpec, PaletteProfile (tags List[str])
- [ ] `palette_system.py` : normalisation hex/rgb/hsl, dérivation auto light/dark
- [ ] `theme_tokens.py` : ThemeTokens, ThemeVariant (dataclasses)
- [ ] `constraints.py` : ConstraintSet, Constraint, AestheticBudgets, BudgetState
- [ ] Tests unitaires complets
- [ ] `generator.py` : inchangé, rétrocompat v1 garantie

### Phase 2 — Bibliothèques (structures + index.json)
- [ ] Créer structure `theme_assets/` + `_families.json` (3 familles initiales)
- [ ] `border_library/index.json` + interface Python + 5 assets minimum
- [ ] `shape_library/index.json` + interface + premiers SVG (waves, blobs)
- [ ] `texture_library/index.json` + interface + CSS (grain, glass, mesh)
- [ ] `ornament_library/index.json` + interface
- [ ] `typography_profiles/index.json` + 4 profils initiaux
- [ ] Interface commune `BaseLibrary` avec `get()`, `search_by_tags()`, `list()`
- [ ] Tests unitaires

### Phase 3 — Pipeline de décision
- [ ] `theme_interpreter.py` : normalisation + inférence tags + construction ConstraintSet
- [ ] `candidate_selector.py` : Jaccard scoring + top-K par dimension
- [ ] `compatibility_engine.py` : filtres hard, incompatibilités, préférences, budgets
- [ ] `theme_resolver.py` : cohérence famille + sélection finale + alternatives
- [ ] `decision_trace.py` : construction et sérialisation du JSON de trace
- [ ] Tests unitaires (cas: budget dépassé, famille inconnue, tous candidats éliminés)

### Phase 4 — Compiler + Renderers
- [ ] `theme_compiler.py` : orchestration complète → ThemeTokens
- [ ] `variant_engine.py` : calcul overrides par variante
- [ ] `css_renderer.py` : CSS variables + composants (remplace generator pour nouveau chemin)
- [ ] `scss_renderer.py` : export SCSS tokens
- [ ] `json_renderer.py` : export design tokens JSON
- [ ] `theme_library/` : 10 thèmes de base

### Phase 5 — Intégration EURKAI
- [ ] Package pip versionné : `eurkai-theme-generator==0.3.0`
- [ ] Fin des copies manuelles PRESENCE_IA
- [ ] CLI : `theme-gen resolve <dna.json>` → affiche trace + preview HTML
- [ ] Documentation d'extension (comment ajouter un asset à une bibliothèque)

---

*Prochaine étape : validation v3 → démarrer Phase 1*
