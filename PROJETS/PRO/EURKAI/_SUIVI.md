# EURKAI — Suivi

pis> Écosystème autonome d'orchestration de projets — Architecture fractale, auto-optimisant, langage propriétaire

**Statut** : 🟢 actif — construction progressive, approche pragmatique
**Créé** : 2026-02-10 (refonte complète, ancien historique dans ARCHIVES/)
**Dernière MAJ** : 2026-03-22 — session 15

---

## Vision

EURKAI est un écosystème entièrement autonome, capable de s'auto-évaluer et de s'auto-optimiser.

### Architecture fondamentale

**TOUT est objet** : `env`, `function`, `method`, `class`, `module`, `scenario`, `user`, `facture`...

**Principes EURKAI** :
1. **Atome = function** (fait UNE chose, réutilisable)
2. **Method = import function** (flexibilité totale)
3. **Scenario = orchestration** (articule methods, ne fait rien lui-même)
4. **Toute method est scenario** (même si n'appelle qu'une function)
5. **Héritage universel** : tout hérite d'`Object` (ident, created_at, version, validate(), test())
6. **Injection dynamique** : methods transversales injectées selon contexte

**Architecture fractale** : la même structure orchestrateur/agents/validator se répète à toutes les échelles (projet, étape, tâche, action).

À terme, le système sera **full dynamique** avec un **langage propriétaire** simplifiant le développement pour les IA comme pour les humains.

**Philosophie** : construction par le bas, modularité maximale, amélioration continue, apprentissage pas à pas.

---

## Objectif immédiat

**Idée → Artefacts actionnables**

Permettre de transformer une idée (export ChatGPT) en projet déployable avec des artefacts concrets :
- BRIEF structuré
- CDC (Cahier des Charges)
- SPECS techniques
- Code fonctionnel
- Déploiement

**Sans sur-ingénierie.** Approche pragmatique d'abord, sophistication ensuite.

---

## Architecture

### Structure fractale de base

```
ORCHESTRATOR
  ├─ Définit étapes + rôles + priorités
  ├─ Délègue aux AGENTS (outputs standardisés)
  └─ Transmet à VALIDATOR

AGENTS (n)
  └─ Produisent outputs selon MANIFEST (interface standard)

VALIDATOR
  └─ Vérifie conformité au MANIFEST
```

Cette structure s'applique :
- **Niveau projet** : orchestrator projet → agents étapes → validator livrable
- **Niveau étape** : orchestrator étape → agents tâches → validator étape
- **Niveau tâche** : orchestrator tâche → agents actions → validator action

**Avantage** : toute optimisation à une échelle se répercute instantanément sur l'ensemble du système.

---

## Agents prévus

| Agent | Rôle | Modèle | Statut |
|---|---|---|---|
| **INTAKE** | Parse idées, crée brief | Haiku | ⚪ à créer |
| **ARCHITECT** | Produit CDC, specs | Haiku | ⚪ à créer |
| **BUILDER** | Compose seeds/schemas/manifests selon règles | Aucun (règles) | ⚪ futur |
| **DEPLOYER** | Exécute déploiement selon plan | Aucun (règles) | ⚪ futur |
| **CURATOR** | Ménage, tags, doublons | Haiku | 🟡 partiel (Pulse) |
| **VALIDATOR** | Vérifie conformité MANIFEST | Aucun (règles) | ⚪ à créer |
| **META** | Auto-évaluation, optimisation | Aucun (métriques) | ⚪ futur |

**Note importante** : BUILDER, DEPLOYER, CURATOR, META ne raisonnent pas — ce sont des **exécutants** suivant des règles imposées. Seuls INTAKE et ARCHITECT utilisent des LLMs.

---

## Modularité

### Bibliothèque de modules (`MODULES/`)

Tout code réutilisable est extrait en **module standalone** :
- Login / Register
- Auth (JWT, session, OAuth)
- Payment (Stripe, PayPal)
- Upload (images, fichiers)
- Email (templates, envoi)
- etc.

**Format** :
```
MODULES/<nom_module>/
├── MANIFEST.json      # Interface standard (inputs, outputs, config)
├── README.md          # Documentation
├── src/               # Code agnostique (pas de dépendance projet)
├── tests/             # Tests
└── examples/          # Exemples d'utilisation
```

**Avantage** : chaque nouveau projet qui nécessite une brique existante la réutilise. EURKAI se construit peu à peu par accumulation.

---

## Connexion au CORE

**Principe** : tout projet est "branché" sur le core EURKAI.

Le core fournit :
- Orchestration (planning, rôles, priorités)
- État partagé (base centralisée)
- Métriques (temps, coût, qualité)
- Optimisation continue
- APIs communes (auth, notifs, storage)

**Détachement** : possible mais coupe le projet de toute la puissance du système (scalabilité, optimisation, modules partagés).

---

## Approche actuelle (pas à pas)

### Phase 1 : Workflow manuel optimisé ✅ en cours

```
1. Nathalie : Export ChatGPT → CLAUDE/TODO/
2. Claude (Sonnet) : Produit BRIEF, CDC, SPECS (session interactive)
3. Nathalie : Validation à chaque étape
4. Claude : Génère code, réutilise MODULES/ si applicable
5. Claude : Déploiement + push GitHub
```

**Coût** : inclus dans abonnement Max (90€/mois), pas de surcoût.

### Phase 2 : Automatisation partielle ⚪ futur proche

- Agent INTAKE autonome (parse TODO/, génère brief sans intervention)
- Agent ARCHITECT autonome (CDC + specs depuis brief validé)
- VALIDATOR basique (checks syntaxe, structure, conformité)

**Coût estimé** : ~1-2€/projet avec Haiku.

### Phase 3 : EURKAI complet ⚪ vision long terme

- Orchestrateur maître
- Tous agents opérationnels
- Langage propriétaire
- Auto-optimisation
- Full autonomie

---

## Organisation actuelle

### Workflow de création projet

Voir [`CLAUDE/PROCESS.md`](../../../CLAUDE/PROCESS.md) pour le détail complet.

**Résumé** :
1. Idée → BRIEF (validation)
2. BRIEF → Projet structuré dans `PROJETS/PRO/<NOM>/`
3. CDC → SPECS → BUILD → DEPLOY
4. Extraction modules réutilisables → `EURKAI/MODULES/`
5. Push GitHub

### Fichiers de pilotage

| Fichier | Rôle |
|---|---|
| `CLAUDE/PROCESS.md` | Règles de création projet |
| `CLAUDE/_AUTO_BRIEF.md` | État global des travaux |
| `CLAUDE/_PROJETS.md` | Liste exhaustive projets |
| `CLAUDE/_CRON.md` | Tâches planifiées |
| `_HUB.md` | Carte centrale BIG_BOFF |

---

## Projets liés

| Projet | Rôle dans EURKAI |
|---|---|
| **BIG_BOFF Search** | Agent SEARCH — moteur recherche par tags (84k éléments) |
| **Pipeline Agence** | Preuve de concept orchestration autonome (à refondre) |
| **TIP_CALCULATOR** | Premier projet test du workflow optimisé |

---

## Prochaines étapes

### ✅ FAIT — Design Engine fixes (2026-03-18 session 2)

#### A) Images — ✅ FAIT
- `_picsum_panel()` : photos Picsum avec overlay `mix-blend-mode:color` → duotone palette-match
- `_visual_panel()` : router archetype-aware — editorial/craft/lifestyle/product → Picsum, tech/brutalist/experimental → CSS panels
- Tous les hero builders (split, asymmetric, layered, fullbleed) + section pull_quote → `_visual_panel()`
- Playful heroes enrichi : `["centered","layered","split"]` pour plus de variété
- Validé : Maison Calva 20/20, Bouton d'Or 10/10, Forges du Nord 20/20 avec photos. Synaptic/Brut 0/0 (CSS panels, correct).

#### B) Palettes — ✅ FAIT
- Surfaces tintées par hue : dark bg `#080b0b` (teinté) au lieu de `#080808` pur, pale/light avec hint de teinte
- Secondary shift editorial : `[40,60,80°]` au lieu de `[15,20,30°]` → contraste secondaire plus marqué
- Accent vibrant : saturation min garantie 0.65, formule `max(0.65, p_s*1.3)`

#### C) Section diversity — ✅ FAIT
- Pools 4 → 6-8 sections par structure
- Cross-attitude mixing : editorial pool inclut stats+process, product pool inclut pull_quote+features_cards
- Flows narrative/fragmented : 35% de chance de démarrer par stats/pull_quote/manifesto

### ✅ FAIT — Design Plan Module (2026-03-19 session 5)

- **`MODULES/design_plan/`** — générateur de plan de design strict (avant le rendu)
  - `src/design_plan.py` : `generate_design_plan(brief, seed, style_dna, theme_hints)`
  - **Output JSON strict** : layout_strategy, hero, composition, visual_tension, rhythm, constraints, section_types, cta_strategy
  - **9 layout strategies** : editorial_flow, magazine_spread, vertical_narrative, asymmetrical_split, staggered_blocks, modular_grid, brutalist_stack, layered_overlap, diagonal_tension
  - **4 profils** : editorial, structural, bold, commercial — extrait du brief par keyword matching
  - **Contraintes** : toujours_forbidden (centered_hero, uniform_card_grid...) + contraintes layout-spécifiques + contraintes hero-spécifiques + tension-spécifiques
  - **`DesignPlan.apply_to_rc(rc)`** : intégration directe dans le rendering contract
  - **`DesignPlan.validate()`** : auto-validation des contraintes internes
  - **`diff_plans()` / `plans_are_distinct()`** : vérification de distinctivité
  - Déterministe : même seed = même plan. 10/10 paires distinctes sur 5 seeds.
  - `MANIFEST.json` + `__init__.py` + 38 tests ✅ (zéro LLM, zéro dépendance)

### ✅ FAIT — Design Learning Module (2026-03-19 session 5)

- **`MODULES/design_learning/`** — couche d'apprentissage heuristique (pas de ML)
  - `src/design_learning.py` : `DesignLearning` class, `Pattern` dataclass
  - **`record_fix(context, problem, fix_params, improvement)`** — enregistre un pattern réussi
  - **`record_from_loop_result(loop_result, initial_scores, rc)`** — enregistre depuis LoopResult
  - **`retrieve_relevant_patterns(context, top_k=3)`** — matching scoré par dimensions de contexte
  - **`suggest_preemptive_adjustments(zone_contexts) → FullPatch`** — patch proactif avant premier render
  - **`mark_preemptive_result(pattern_id, success)`** — feedback boucle → success_rate pattern
  - **Context dimensions** : zone (poids×2), background_type, text_color_class, theme_type (poids×1 each)
  - **`derive_context(zone, rc)`** — dérive le contexte depuis le rendering contract
  - **Déduplication** : patterns identiques mergés, valeurs numériques moyennées
  - **Fiabilité** : success_rate < 60% après 3+ usages → exclu des suggestions
  - **Stockage JSON atomique** : `data/design_patterns.json`, max 500 patterns, purge LRU
  - `MANIFEST.json` + `__init__.py` + 37 tests ✅ (zéro dépendance externe)
  - **Boucle complète** : generate → apply_learned → render → capture → audit → fix → learn

### ✅ FAIT — Auto Fix Engine (2026-03-19 session 5)

- **`MODULES/auto_fix_engine/`** — moteur de correction automatique non-destructif
  - `src/auto_fix_engine.py` : `AutoFixEngine`, boucle `run_correction_loop()`
  - **6 fix types** : `text_contrast`, `overlay_increase`, `background_simplify`, `cta_emphasis`, `typography_safety`, `text_plate`
  - **`classify_issue(problem_str) → FixType`** — keyword matching déterministe (sans LLM)
  - **`compute_fix(fix_type, severity, zone, current) → ZonePatch`** — corrections progressives/incrémentales
  - **`ZonePatch`** : paramètres nommés (text_color, overlay_opacity, blur_px, cta_font_weight, font_weight...) — pas de CSS brut
  - **`FullPatch`** : dict zone → ZonePatch, merge intelligent, is_empty(), to_dict()
  - **`apply_css_patch(html, patch) → str`** — injection `<style id="auto-fix-engine">` via `[data-audit=zone]` selectors, idempotent
  - **Boucle** : `capture_fn` + `audit_fn` injectées (zéro couplage) → convergence détectée → arrêt propre
  - `MANIFEST.json` + `__init__.py` + 40 tests ✅ (zéro API, zéro réseau)

### ✅ FAIT — Vision Audit Module (2026-03-19 session 5)

- **`MODULES/vision_audit/`** — module standalone d'audit visuel via LLM vision
  - `src/vision_audit.py` : `VisionAudit` class + `audit_screenshot()` + `audit_page()` + `audit_from_capture_results()`
  - Modèle : `claude-haiku-4-5-20251001` (vision, coût minimal, configurable)
  - Output structuré strict : `readability_pass`, `global_score`, `issues[]`, `quick_fixes[]`
  - `AuditIssue` : zone, problem, severity (low/medium/high), confidence, suggested_fix
  - `AuditResult` : dataclass complet + `to_dict()` + `repr()` + `ok` property
  - `build_audit_prompt()` : template réutilisable, strictness HIGH pour hero/nav/primary_cta
  - Parsing robuste : `_extract_json()` (clean / markdown / embedded), `_validate_structure()`
  - `summarize_results()` : agrégat multi-zones (pass/fail/avg_score/high_issues)
  - Intégration `screenshot_capture` : `audit_from_capture_results(list[CaptureResult])`
  - `MANIFEST.json` + `__init__.py` + 23 tests ✅ (zéro appel API)
  - CLI : `--image`, `--zone`, `--viewport`, `--batch <json>`, `--output <json>`

### ✅ FAIT — Screenshot Capture Module (2026-03-19 session 5)

- **`MODULES/screenshot_capture/`** — module standalone Playwright déterministe
  - `src/screenshot_capture.py` : `ScreenshotCapture` class, 5 modes (full_page, viewport, selector, audit_zone, all_zones)
  - `MANIFEST.json` : spec complète (inputs, outputs, viewports, zones, render strategy)
  - `__init__.py` : exports propres
  - `tests/test_capture.py` : 6 tests unitaires ✅ (imports, presets, selectors, dataclass, output path, resolve viewport)
- **`data-audit` tags** injectés automatiquement via `_inject_audit_tags()` (post-processing dans `_lp_dynamic_page`)
  - Zones taguées : `nav`, `hero`, `first_section`, `section-1/2/3`, `final_cta`
  - Approche non-invasive : zero changement dans les 8 renderers individuels
- **`demo_capture.py`** — démo end-to-end : génère HTML + serveur local + capture full_page + viewport + zones audit

### ✅ FAIT — Visual Decorators Engine (2026-03-20 session 8)

- **`MODULES/visual_decorators/`** — couche de signature visuelle décorative. Cohérente, intentionnelle, non aléatoire.
  - **`generate_visual_decorators(visual_intent) -> dict`** — input : VisualIntent, output : schéma strict 5 blocs
  - **Output JSON** : `borders` (style/thickness/radius/pattern) + `dividers` (type/style) + `icons` (style/stroke/corner_style/complexity) + `motifs` (type/usage) + `overlays` (type/intensity)
  - **7 presets émotionnels** : trust / excitement / desire / calm / curiosity / authority / default
  - **6 style family overrides** : prime sur tout (editorial_luxury → double thin frame ; brutalist → thick solid grid-fragment ; tech_minimal → dot-pattern ; etc.)
  - **5 brand positioning adjustments** : fine-tune appliqué après emotional_goal
  - **Ajustements intensity** : low → retire motifs/overlays, réduit borders ; high → peut ajouter overlay léger
  - **Ajustements density** : density=low → jamais full-bleed pour les motifs
  - **4 preuves spec** : gaming (sharp/glow/diagonal-cut), dating (rounded/blob/warm), finance (none/none/sharp/thin), luxury (double/thin/no-motifs)
  - **101/101 tests ✅** (7 suites, zéro API)

### ✅ FAIT — Contextual Design Alignment (2026-03-20 session 8)

- **Extension `visual_intent_engine` v1.1.0** — alignement sémantique automatique : le brief parle, le design écoute.
  - **`_extract_context(brief) -> dict`** : extraction automatique depuis le brief
    - `product_type` : 13 types détectés par mots-clés (ecommerce, saas, event, gaming, dating, finance, luxury, health, education, food, travel, agency, editorial)
    - `target_audience` : 5 audiences (young_adult, professional, senior, mass_market, niche, general)
    - `emotional_goal` : 6 objectifs (trust, excitement, desire, calm, curiosity, authority) — par défaut depuis product_type, override si signal explicite dans le brief
    - `brand_positioning` : 5 positionnements (premium, accessible, disruptive, playful, serious) — idem
  - **`_apply_context_adjustments(intent, context, mode) -> dict`** : application différenciée selon le mode
    - `default` : le contexte DRIVE composition_bias + color_strategy + typography_strategy + techniques
    - `reference` : le contexte ajuste color/typo uniquement — la référence guide la structure (composition_bias préservé)
    - `strong` / `hybrid` : le contexte ajoute uniquement aux constraints (style family prime)
  - **`EMOTIONAL_GOAL_ADJUSTMENTS`** : 6 presets (trust/excitement/desire/calm/curiosity/authority) avec composition_bias, techniques_add/remove, color_strategy, typography_strategy
  - **`BRAND_POSITIONING_ADJUSTMENTS`** : 5 presets (premium/accessible/disruptive/playful/serious) appliqués après emotional_goal (fine-tune)
  - **Output enrichi** : champ `context` systématiquement présent dans le résultat JSON
  - **4 preuves spec** : dating (desire+playful → image-dominant + vibrant), gaming (excitement+disruptive → high density + high contrast), finance (trust+serious → text-dominant + neutral + regular), luxury (desire+premium → low density + neutral)
  - **Backward compatible** : résultats strong/hybrid inchangés
  - **258/258 tests ✅** (15 suites, 3 nouvelles pour context)

### ✅ FAIT — Visual Intent Engine v1.0 (2026-03-20 session 8)

- **`MODULES/visual_intent_engine/`** — direction artistique AVANT le design plan. Intention uniquement — zéro HTML, zéro CSS.
  - **4 modes auto-détectés** :
    - `default` — propre, lisible, risque minimal (aucun input fort)
    - `strong` — direction forte depuis une style family (via `constraints.force` ou `style_dna.archetype`)
    - `reference` — extraction principes visuels depuis image (vision API Claude Haiku)
    - `hybrid` — blend style + référence (style → ton/intensité, référence → structure)
  - **6 style families** : `editorial_luxury`, `brutalist`, `tech_minimal`, `experimental_grid`, `premium_brand`, `bold_marketing`
  - **Output JSON strict** : mode, art_direction, composition_bias, visual_techniques, color_strategy, typography_strategy, constraints
  - **`intent_to_plan_overrides()`** : traduit l'intent en overrides pour `generate_design_plan()`
  - **Brief signal enrichment** : mots-clés brief → ajustements légers (luxury, festival, saas, magazine...)
  - **User constraints** : `force`/`avoid` fusionnés, style family names filtrés automatiquement
  - **Schema validation** : `_validate_and_clean()` — zéro champ manquant, valeurs invalides corrigées
  - **Graceful fallback** : si vision API indisponible → intent default valide retourné
  - **127/127 tests ✅** (zéro API, mocks pour reference/hybrid)
- **`generate_design_plan()` modifié** — accepte `visual_intent=...` (backward compatible)
  - profile override : `visual_intent → _extract_profile()` remplacé si style fort
  - layout boost/avoid : layouts favorisés/évités selon asymmetry + style family
  - density override : direct depuis `composition_bias.density`
  - tension override : depuis `art_direction.intensity` + style family
  - tension methods : priorité aux techniques du visual_intent, complétées par pool
  - extra required/forbidden : fusionnés dans les constraints du plan

### ✅ FAIT — Batch Visual Generation (2026-03-19 session 7)

- **`generate_batch_samples.py`** — générateur de batch visuel, 12 pages complètes
  - **4 familles** : ecommerce, event, editorial, saas (3 pages chacune)
  - **Pipeline complet** pour chaque page : design_plan → validation → render → capture → audit → fix → output
  - **Structure de sortie** : `output/samples/{family}/{slug}/page.html + screenshot.png + meta.json`
  - **Index HTML** : `output/samples/index.html` — grille visuelle, thumbnails, liens, metadata
  - **Screenshots full-page** via Playwright (ScreenshotCapture) — viewport desktop
  - **meta.json** par page : project_name, family, brief, seed, design_plan summary, pipeline status
  - **Chargement auto** ANTHROPIC_API_KEY depuis `~/.bigboff/secrets.env` si absente
  - CLI : `--family ecommerce` (filtrer), `--no-screenshots` (rapidité), `--open` (ouvre index), `--quiet`
  - **12/12 ✅ — 12/12 screenshots ✅ — 174s total** (~14s/page)

### ✅ FAIT — Tests d'intégration pipeline (2026-03-19 session 7)

- **`test_pipeline_integration.py`** — suite d'intégration complète : 18/18 ✅
  - **Test 1** (5 sous-tests) — Design Validator bloque les patterns interdits
    - `centered_hero` → FAIL score=10, hard constraint détecté
    - `uniform_card_grid` → FAIL score=50
    - `cta_visual_isolation` absent → FAIL required manquant
    - Accumulation violations medium/minor → score=50 < seuil 70
    - Layout valide de référence → PASS score=100
  - **Test 2** — Variation réelle entre tentatives (seeds 42→139→236→333→430)
    - 10/10 paires de plans distinctes (12-15 dimensions de diff)
    - 4 layout strategies distinctes sur 5 tentatives
    - 4 hero types distincts sur 5 tentatives
  - **Test 3** — Boucle FAIL→retry→PASS prouvée
    - Scénario : renderer injecte `centered_hero` aux tentatives 1 et 2 → FAIL
    - Tentative 3 : layout réel → PASS score=100
    - Critères : au moins 1 FAIL avant PASS ✅, PASS dans max_attempts ✅, layout changé ✅
  - **Test 4** — Pipeline e2e complet (--no-capture --no-audit)
    - Convergence en 1 tentative, durée 712ms
    - Artefacts sauvés : HTML 17.9kb + design_plan JSON + pipeline_result JSON
  - **Test 5** — Full-regen seed+1000 : 15 dimensions différentes, score=100 ✅
- **Fix** : `diff_plans()` et `plans_are_distinct()` attendent des `DesignPlan` objects (pas `.to_dict()`)

### ✅ FAIT — Design Validator Module (2026-03-19 session 6)

- **`MODULES/design_validator/`** — validateur PASS/FAIL pur (zéro API, zéro LLM)
  - `src/design_validator.py` : `DesignValidator`, `ValidationResult`, `validate_layout()`
  - **10 checks** : forbidden patterns (hard constraint), required items (hard constraint), correspondance hero type/positioning/text_placement, répétitions layout (auto-calcul depuis sections), symétrie globale interdite, count sections (3-8), présence CTA, densité
  - **Score** : 100 − Σ pénalités (major=50, medium=20, minor=5), plancher 0, seuil PASS=70
  - **Hard constraints** : forbidden/required → `valid=False` même si score ≥ 70
  - **`_is_grid_like(section)`** : vérifie `type` ET `layout_variant` (fix `standard_nav_hero_grid_footer`)
  - `MANIFEST.json` + `__init__.py` + 56/56 tests ✅

### ✅ FAIT — Pipeline orchestrateur central (2026-03-19 session 6)

- **`pipeline.py`** — orchestrateur central : 7 phases strictes, zéro bypass, zéro silent failure
  - Phase 1 `context` : style_dna + palette + theme
  - Phase 2 `design_plan` : boucle max 5 tentatives, seed muté ×97 par tentative, render BLOQUÉ si plan invalide
  - Phase 3 `preemptive_learning` : suggestions avant premier render
  - Phase 4 `render` : génération HTML, uniquement si plan validé
  - Phase 5 `fix_loop` : capture→audit→patch, max 3 itérations, `_InMemoryServer` thread-safe
  - Phase 6 `learning` : enregistrement patterns depuis résultats
  - Phase 7 `output` : artefacts HTML + design_plan JSON + pipeline_result JSON
  - **`_extract_layout_from_plan(plan)`** : layout synthétique pour validation pre-render
  - **`_mutate_seed(base, attempt)`** : `base + attempt × 97`
  - **Full-regen fallback** : seed+1000 si toutes les tentatives échouent
  - **Graceful degradation** : chaque module wrappé try/except, `_modules` dict
  - CLI : `--brief`, `--name`, `--seed`, `--no-capture`, `--no-audit`, `--json`, `--modules`
  - 7/7 modules chargés, test e2e < 1s (sans capture)

### ✅ FAIT — Responsive + fixes visuels (2026-03-19 session 4)

- **Responsive CSS** : media query `max-width:900px` + règles globales (overflow-x:hidden, overflow-wrap)
  - Grids → 1 colonne sur mobile (attribute selectors `[style*='grid-template-columns:...']`)
  - Container padding 48px → 20px sur mobile
  - Heroes split/asymmetric : empilement vertical, panels réduits
  - Nav : liens cachés sur mobile, padding réduit
- **Typographie** : clamp max réduits à la source
  - brutalist/experimental : `8rem` → `5rem`, editorial : `5.5rem` → `4rem`, playful : `4.5rem` → `3.5rem`
  - fullbleed hero : `7rem` → `4.5rem`
  - h3_css : `.95rem` → `1.1rem`
  - `section_label` : `<span>` 9px → `<h2>` sémantique 0.7rem uppercase
- **Nav** : logo calé à gauche (`padding:0 24px` direct sur `<nav>`, suppression du container centré)
- **word-break** : remplacement de `break-word` (trop agressif, coupe au caractère) par `overflow-wrap:break-word`

### ✅ FAIT — EMAIL_WARMING_MODULE (2026-03-20 — session PRESENCE_IA)

- **`MODULES/EMAIL_WARMING_MODULE/`** — module de warming email bidirectionnel, standalone, réutilisable par tout projet EURKAI
  - **`models.py`** : 4 modèles SQLAlchemy — `WarmingPoolDB`, `WarmingSenderDB`, `WarmingReceiverDB`, `WarmingSessionDB`
  - **`database.py`** : CRUD complet + `db_session_stats`
  - **`module.py`** : `WarmingEngine` — `run_session(pool_id)`, `_send_via_brevo()`, `_process_receiver_imap()`, `scheduler_job()` (wrapper APScheduler)
  - **`api/routes/warming.py`** : FastAPI routes — list/create/update pools, senders/receivers, trigger manuel, stats
  - **`configs/presence_ia_seed.json`** : 25 senders Brevo (5 domaines × 5 adresses) + 2 receivers IMAP IONOS
  - **`configs/seed_loader.py`** : `load_seed(project_name, db)` — init pool+senders+receivers depuis JSON, résout `ENV:VAR_NAME`
  - **`__init__.py`** : exports publics (`WarmingEngine`, `init_db`, `make_session`, models, enums)
  - **Ramp-up** : j1=4, j4=8, j8=12, j15=16, j22=20 emails/session (toutes les 4h)
  - **Bidirectionnel** : envoi Brevo (`X-Warming:1`) + IMAP mark-read + auto-reply Brevo
  - **Origine** : extrait du job inline PRESENCE_IA (qui continue en //) → transformé en module EURKAI
  - **Usage** : `load_seed("presence_ia", db)` + `APScheduler.add_job(WarmingEngine.scheduler_job, "interval", hours=4, args=[pool_id, db_url, key])`

### ✅ FAIT — Palette-driven renderer (2026-03-20 session 8)

- **`generate_brand_charter.py`** — renderer entièrement piloté par palette. Zéro couleur hardcodée.
  - **`_pal_from_color_palette_engine(cp: dict) -> dict`** — bridge Color Palette Engine → pal interne
    - Mappage explicite : `primary→p`, `secondary→s`, `accent→acc`, `background→bg`, `surface→bg2`, `text_primary→fg`, `text_secondary→fg2`, `border→bdr`, states préservés
    - `mode` calculé depuis luminance du background (< 0.3 → dark)
  - **`_build_css_vars(pal: dict) -> str`** — émet `:root { --color-primary:...; ... }` depuis les tokens pal
    - 9 variables CSS : `--color-primary/secondary/accent/bg/surface/text/text-muted/border/on-primary`
    - + `--color-success/warning/error` si présents dans states
    - **Single source of truth** — toutes les couleurs référencées depuis ce bloc
  - **CSS vars injectées dans chaque page** — `_reset` utilise `var(--color-bg)` et `var(--color-text)` au lieu de valeurs inline
  - **`generate_landing_page(... cp_palette=None)`** — nouveau paramètre : Color Palette Engine dict
    - Priorité : `cp_palette` > `palette_output` > build interne
    - **Auditabilité** : chaque couleur rendue est traçable au token (`--color-primary` → `cp['primary']`)
  - **Warm mode fix** : `bg="#f6efe4"` etc. remplacés par valeurs hsl dérivées de la teinte de base
  - **Tests** : 4 cas spec (gaming/dating/finance/luxury) — primary et CSS vars corrects dans chaque rendu

### ✅ FAIT — Color Palette Engine (2026-03-20 session 8)

- **`MODULES/color_palette/`** — système de couleurs cohérent, accessible, contextuel. WCAG AA garanti.
  - **`generate_palette(visual_intent, context=None) -> dict`** — input : VisualIntent + context optionnel, output : palette strict 10 clés
  - **Output JSON** : `primary`, `secondary`, `accent`, `background`, `surface`, `text_primary`, `text_secondary`, `border`, `states` (success/warning/error), `contrast_score` (body_text/large_text)
  - **Garantie WCAG AA** : `_fix_contrast()` itératif (±2% lightness, 60 steps max) — text_primary/bg ≥ 4.5:1, text_secondary/surface ≥ 4.5:1
  - **Déterminisme total** : même visual_intent → même palette toujours. Zéro aléatoire.
  - **Hues par emotional_goal** : trust=220° (bleu), excitement=350° (rouge-rose), desire=340° (rose), calm=168° (teal), curiosity=268° (violet), authority=218° (marine)
  - **Accent offset** : rotation complémentaire ou split-complémentaire selon emotional_goal
  - **Brand positioning modifiers** : premium (−18 sat), disruptive (+15 sat, offset 180°), playful (+12 sat, offset 60°), serious (−15 sat)
  - **Dark/light mode** : produit_type → `_DARK_PRODUCTS` (gaming/luxury/event/agency/editorial) vs `_LIGHT_PRODUCTS` (saas/finance/health/ecommerce/dating...)
  - **Context override** : `generate_palette(intent, context=ctx)` — écrase `visual_intent["context"]`, incluant pour `_is_dark_mode()`
  - **6 style family palettes prédéfinies** : editorial_luxury (cream/gold/near-black), brutalist (blanc/rouge/noir), tech_minimal (bleu Google/blanc), experimental_grid (fuchsia/violet/near-black), premium_brand (or chaud/warm-black), bold_marketing (orange-rouge/jaune/noir)
  - **MANIFEST.json** : spec complète (schema, priority_logic, guarantees, examples)
  - **194/194 tests ✅** (8 suites : WCAG math, schema, contrast guarantee, 5 spec cases, style family override, no duplicate roles, context override)

### ✅ FAIT — Review Batch — Human Review Mode (2026-03-22 session 9)

- **`review_batch.py`** — outil de review visuelle rapide. 8 pages, pipeline complet, index navigable.
  - **8 pages** : 2 × ecommerce / event / editorial / saas — briefs distincts, seeds espacés
  - **Pipeline complet** : design_plan → validation → render → screenshot → vision_audit → auto_fix
  - **Visual Intent + Color Palette** calculés pour chaque page et enregistrés dans meta.json
  - **meta.json** par page : project_name, site_family, brief, seed, design_plan summary, pipeline status, fix_iterations, final_score, visual_intent summary, palette summary (primary/bg/text/accent/WCAG grade)
  - **Index HTML** : dark UI, cards par famille, thumbnails, intent tags, swatches palette, grade WCAG, 4 champs review :
    - `structure: ✓/✗` — plan validé
    - `readability: ✓/✗` — score ≥ 70 (nécessite screenshots)
    - `fix: N` — itérations auto-fix
    - `score: N` — lisibilité finale
  - **review_summary.json** : total_pages, success_count, validation_pass_count, readability_pass_count, avg_fix_iterations, avg_duration_ms, by_family, pages_with_issues
  - **CLI** : `--family` / `--count N` / `--no-screenshots` / `--open` / `--quiet`
  - **Testé** : 8/8 ✅ en 81s (sans screenshots) · structure_valid 8/8

### ✅ FAIT — Review Batch complet avec vision audit réel (2026-03-22 session 11)

- **`review_batch.py --open`** — 8/8 pages + screenshots (full_page + hero) en 481s. Vision audit opérationnel.
- **Fix clé** : `_load_api_key_if_missing()` charge toujours depuis `secrets.env` (override la clé révoquée de l'env shell).
- **Nouveaux outputs** : `hero.png` par page, meta.json au format spec (`validation`, `readability`, `fix_iterations`, `design_plan_summary`, `visual_intent_summary`, `palette_summary`), liens Full/Hero/meta dans index.

**Résultats vision audit (seuil 70) :**
- ✓ Volta Design (ec_02) : 88 — 1 iter
- ✓ Revue Matière (ed_01) : 88 — 1 iter
- ✓ Fluxo (sa_02) : 88 — 1 iter
- ✓ Synaptic (sa_01) : 84 — 3 iter
- ✓ Nuit Sonore (ev_01) : 75 — 3 iter
- ✗ Maison Rouge (ec_01) : 69 — 3 iter (stagne)
- ✗ Forum Climat (ev_02) : 69 — 3 iter (stagne)
- ✗ Studio Pellicule (ed_02) : 69 — 3 iter (stagne)

**5/8 readability ✓.** Zones récurrentes en défaut : `nav`, `hero`, `full_page`. Gap identifié : pas de logo dans le nav (renderer génère le slug en texte brut).

### ✅ FAIT — visual_coherence_engine v1.0.0 (2026-03-22 session 12)

Module `MODULES/visual_coherence_engine/` créé — règle bidirectionnelle stricte image ↔ palette.

**CASE 1 — image_drives_palette** : image de référence fournie → analyse PIL (hue dominante circulaire, luminosité, saturation, température, contraste) → génère palette depuis l'image.

**CASE 2 — palette_drives_image** : standard pipeline → palette d'abord → calcule ajustements CSS (duotone overlay, opacity adaptée au mode, filter, blend_mode) + règles de lisibilité WCAG AA.

**Sorties** : `{mode, palette, image_adjustments: {duotone, overlay_color, overlay_opacity, filter, blend_mode}, readability_rules: {text_on_image, min_overlay_for_wcag, gradient_scrim, recommended_text_color}, conflicts}`.

**Intégration generate_brand_charter.py** : `_picsum_panel()` utilise maintenant `_coherence_adjustments()` (overlay_opacity et filter pilotés par le moteur, plus hardcodés). `_coherence_ok=True` confirmé.

**Tests** : 11/11 ✅ (utilitaires couleur, WCAG, run CASE 2 light/dark, readability rules, no-palette fallback, integration check).

### ✅ FAIT — CASE 3 design_reference_drives_plan (2026-03-22 session 13)

Extension du visual_coherence_engine v1.1.0 + chaîne complète.

**3 modes de référence:**
- `reference_type="image"` → `image_drives_palette` (CASE 1, inchangé)
- `reference_type="none"` → `palette_drives_image` (CASE 2, inchangé)
- `reference_type="screenshot"|"mockup"` → `design_reference_drives_plan` (CASE 3, nouveau)

**CASE 3 — ce qui est extrait :** dominance (text/image/balanced), density (low/medium/high), hierarchy (calm/strong/aggressive), spacing (tight/balanced/airy), composition_bias, palette_hint. Double analyse : pixel stats (PIL/stdlib) + vision API Anthropic (graceful fallback).

**Propagation en chaîne :**
1. `visual_coherence_engine.run(reference_type="screenshot")` → `reference_analysis`
2. `visual_intent_engine.generate_visual_intent(reference_analysis=...)` → composition_bias overridé, typography_strategy depuis hierarchy
3. `design_plan.generate_design_plan(reference_analysis=...)` → profile, density, tension, layout_boost — inputs durs, priment sur visual_intent

**Condition d'échec explicite :** si screenshot/mockup fourni mais analyse échoue → fallback + conflict dans `conflicts[]`

**Tests :** 71/71 ✅ (18 cohérence + 15 intent + 38 plan)

### ✅ FAIT — Nav logo mark (2026-03-22 session 14)

`_nav_logo_mark()` helper ajouté dans `generate_brand_charter.py`. Génère un carré coloré 28px avec initiales de la marque en CSS HTML — identifiant visuel de marque dans le nav sans fichiers image.

Patché sur les 6 renderers nav : studio, event, ecommerce, brand_landing, saas, organic/editorial.

**Résultat review_batch — 8/8 ✅ (était 5/8) :**
- ec_01 Maison Rouge : 87 ✅ (était 69 fail)
- ec_02 Volta Design : 88 ✅
- ev_01 Nuit Sonore : 77 ✅
- ev_02 Forum Climat : 87 ✅ (était 69 fail)
- ed_01 Revue Matière : 88 ✅
- ed_02 Studio Pellicule : 70 ✅ (était 69 fail)
- sa_01 Synaptic : 88 ✅
- sa_02 Fluxo : 88 ✅

### Prochaines étapes (post session 14)

- **Priorité 1** : Câbler `reference_analysis` dans `pipeline.py` — passer `reference_type` + `reference_image` à `pipeline.run()` pour activer CASE 3 dans le vrai pipeline
- **Priorité 2** : Passer `visual_coherence_engine.run()` dans `pipeline.py` pour les pages avec images (familles `editorial`, `ecommerce`) — utiliser l'output complet (readability_rules, conflicts) dans le fix loop

**État couche visuelle** : visual_intent_engine (v1.1.0) + visual_decorators (v1.0) + color_palette (v1.0) + visual_coherence_engine (v1.0.0) + palette-driven renderer + review_batch = système complet et validé.

### Immédiat (semaine 1) — FAIT ✅

- [x] Structurer EURKAI proprement
- [x] Archiver ancien EURKAI → ARCHIVES/
- [x] Documenter vision + approche dans `_SUIVI.md`
- [x] Push GitHub

### Court terme (mois 1)

- [ ] Créer 3-5 modules standalone (auth, email, upload)
- [ ] Refondre Pipeline Agence selon architecture fractale
- [ ] Documenter protocole inter-agents (`CORE/PROTOCOL.md`)
- [ ] Définir format MANIFEST standard (`CORE/MANIFEST_SPEC.md`)

### Moyen terme (trimestre 1)

- [ ] Agent INTAKE autonome
- [ ] Agent ARCHITECT autonome
- [ ] Agent VALIDATOR basique
- [ ] Orchestrateur léger (gestion d'état, métriques)
- [ ] 10+ projets générés via workflow EURKAI

---

## Métriques de succès

| Métrique | Cible | Actuel |
|---|---|---|
| Temps idée → déploiement | < 2h | ~4-6h (manuel) |
| Coût par projet | < 2€ | 0€ (inclus Max) |
| Taux de réutilisation modules | > 50% | 0% (démarrage) |
| Projets actifs | 10+ | 3 |
| Autonomie (% sans intervention) | 80%+ | 10% |

---

## Décisions

- **2026-02-10 19:00** : Architecture orientée objet universelle documentée (TOUT est objet)
- **2026-02-10 19:00** : Validation objets/héritage via formulaire GitHub Pages (étape SPECS)
- **2026-02-10 19:00** : Règles EURKAI formalisées (atome=function, method=import, scenario=orchestration)
- **2026-02-10 18:45** : TIP_CALCULATOR déployé — premier projet complet A→Z ✅
- **2026-02-10 18:30** : PROCESS.md + STANDARDS.md créés (règles standardisées)
- **2026-02-10 17:00** : Refonte complète EURKAI, approche pragmatique pas à pas
- **2026-02-10** : Workflow manuel optimisé d'abord, automatisation ensuite
- **2026-02-10** : Sonnet par défaut pour minimiser coût quota
- **2026-02-10** : Structure fractale dès le début, même si simple
- **2026-02-10** : Modules standalone prioritaires (construction par le bas)
- **2026-02-10** : Apprentissage pas à pas (règles révélées au fil des projets, pas tout d'un coup)

---

## Historique

- **2026-03-22 (s16)** : Brand Identity Engine — `MODULES/brand_identity/` v1.0.0. `generate_brand_identity(brief, vi, palette, context, reference)` → brand_core + logo + icons + typography + visual_signature. Purement déterministe, zéro appel externe. 10 contextes (gaming/luxury/dating/finance/editorial/ecommerce/event/playful/premium/startup/default). Typo contextuelle (Rajdhani, Cormorant Garamond, Playfair Display…). Logo SVG spec + generation_prompt Recraft-compatible. Overrides depuis reference_analysis CASE 3. 4 nouveaux endpoints (design.brand.generate, design.logo.generate, design.icons.generate, design.typography.generate). 2 nouveaux scénarios (design.brand.generate_full, design.brand.generate_from_reference). Catalog v1.1.0 : 12 endpoints + 8 scénarios. Fix sys.modules : design.coherence.apply.py migré vers importlib (bug shim visual_coherence_engine via generate_brand_charter). 119/119 tests ✅.
- **2026-03-22 (s15)** : Design Endpoint System — 8 endpoints + 6 scénarios + catalog JSON + design.explore(). 68/68 tests ✅. MODULES/design_endpoints/, MODULES/design_scenarios/, MODULES/design_catalog/. Convention <category>.<object>.<action>.
- **2026-03-22 (s14)** : Nav logo mark — `_nav_logo_mark()` dans generate_brand_charter.py. Carré coloré avec initiales, patché 6 renderers. Review batch 8/8 ✅ (était 5/8). Scores : ec_01=87, ev_02=87, ed_02=70 (les 3 pages bloquées à 69 passent désormais).
- **2026-03-22 (s13)** : CASE 3 `design_reference_drives_plan` — visual_coherence_engine v1.1.0. Propagation référence → visual_intent → design_plan. Pixel + vision API analysis. 71/71 tests ✅.
- **2026-03-22 (s12)** : `visual_coherence_engine` v1.0.0 — règle bidirectionnelle image↔palette. CASE 1 : analyse PIL (hue circulaire, luminosité, temp, contraste) → palette from image. CASE 2 : palette → overlay CSS dynamique (opacity mode-aware, WCAG). Intégré dans `_picsum_panel()`. 11/11 tests ✅.
- **2026-03-22 (s11)** : Review batch complet — vision audit réel avec clé valide. 8/8 pages, full_page + hero screenshots, 481s. 5/8 readability ✓ (seuil 70). 3 pages stagnent à 69 (nav/hero défaillants). Gap : pas de logo dans le nav. Fix `_load_api_key_if_missing()` pour toujours préférer secrets.env. Meta.json au format spec.
- **2026-03-22 (s10)** : `review_batch.py --open` — run réel avec Playwright. 8/8 pages + screenshots en 117s. Diagnostic vision_audit : 401 invalid x-api-key (clé shell révoquée). Pages visuellement correctes (screenshots inspectés). Fix : sourcer clé valide depuis ~/.bigboff/secrets.env.
- **2026-03-22 (s9)** : `review_batch.py` — Human Review Mode. 8 pages (2×4 familles), pipeline complet, index HTML dark avec thumbnails/intent/palette/review flags, review_summary.json. CLI --family/--count/--no-screenshots/--open/--quiet. 8/8 ✅ en 81s.
- **2026-03-20 (s8)** : Palette-driven renderer — `_pal_from_color_palette_engine()` + `_build_css_vars()` dans generate_brand_charter.py. CSS vars `:root{--color-*}` injectées dans chaque page. `generate_landing_page(cp_palette=)`. Warm mode fix. 4/4 cas spec validés.
- **2026-03-20 (s8)** : `color_palette` module complet — `generate_palette(visual_intent, context=None)`. WCAG AA garanti via `_fix_contrast()` itératif. 6 style family palettes prédéfinies. Dark/light mode via product_type. Context override corrigé (`_is_dark_mode()` reçoit ctx résolu). 194/194 tests ✅.
- **2026-03-20 (s8)** : `visual_decorators` module complet — `generate_visual_decorators(visual_intent)`. 7 presets émotionnels, 6 style family overrides, 5 brand positioning adjustments, ajustements intensity/density. 101/101 tests ✅. Demo HTML générée.
- **2026-03-20 (s8)** : `visual_intent_engine` v1.1.0 — Contextual Design Alignment. `_extract_context(brief)` + `_apply_context_adjustments(intent, context, mode)`. 13 product_types, 6 emotional_goals, 5 brand_positionings. Champ `context` systématiquement présent. 258/258 tests ✅.
- **2026-03-19 (s7)** : `test_pipeline_integration.py` — tests d'intégration complets. 18/18 ✅. 5 suites : (1) validator bloque forbidden patterns (5 scénarios), (2) retry produit variation réelle (10/10 paires distinctes, 12-15 dimensions de diff), (3) boucle FAIL→retry→PASS simulée (2 FAIL forcés, PASS à tentative 3), (4) pipeline e2e complet en 712ms, (5) full-regen seed+1000 différent (15 dims, score=100). Fix : `diff_plans()` et `plans_are_distinct()` attendent des DesignPlan objects, pas des dicts.
- **2026-03-19 (s6)** : `pipeline.py` — orchestrateur central complet. 7 phases : context → design_plan loop (max 5, mutation seed ×97) → preemptive learning → render (bloqué si plan invalide) → fix loop (capture→audit→patch, max 3) → learning → output. 7/7 modules chargés. Test e2e : ✅ success maison-calva + synaptic en <1s (sans capture). CLI : --brief, --name, --seed, --no-capture, --no-audit, --json, --modules.
- **2026-03-19 (s6)** : `design_validator` module complet — validateur PASS/FAIL pur (zéro API, zéro LLM). 10 checks : forbidden/required (hard constraints), correspondance hero (type/positioning/text_placement), détection répétitions (auto-calcul depuis sections si absent), symétrie globale interdite, count sections, présence CTA, densité. Score 0→100 (seuil 70), hard constraint → FAIL même si score ≥ 70. 56/56 tests ✅.
- **2026-03-19 (s5)** : `design_plan` module complet — plan déterministe AVANT render. 9 strategies layout, 4 profils (editorial/structural/bold/commercial), constraints builder (always_forbidden + layout/hero/tension-specific), apply_to_rc(), validate(), diff_plans(), plans_are_distinct(). 38 tests ✅. 10/10 paires distinctes sur 5 seeds.
- **2026-03-19 (s5)** : `screenshot_capture` module standalone — Playwright, 5 modes capture, `data-audit` tags via `_inject_audit_tags()` post-processing (nav/hero/first_section/section-1,2,3/final_cta), 6 tests ✅, `demo_capture.py`. Contraste sections : `_sec_vt()` retourne sec_bg (4e valeur), `_sec_colors()` helper, 14 sections corrigées. E-commerce catalog renderer réécrit ex nihilo.
- **2026-03-18 (s3)** : Refactor architectural palette — `_pal_from_palette_output()` zéro couleur en dur, surfaces issues de `bw_variant` du palette_generator. `generate_landing_page()` accepte `palette_output` + `harmony`. Tester : switcher harmonies dans barre (Complément./Analogue/Triade/Mono/Minimal). Fix contraste fullbleed (scrim gradient). Fix overflow h1 (break-word, max 7rem).
- **2026-03-18 (s2)** : Design Engine fixes — A) images Picsum duotone + router archetype-aware, B) palettes tintées par hue + secondary shift agressif, C) section pools 4→6-8 + cross-attitude mixing
- **2026-03-18 04:00** : SESSION INTERROMPUE — état stable, serveur OK, 3 problèmes identifiés pour prochaine session
- **2026-03-18 03:00** : Design Instantiation Engine v3 complet — Generative Section Engine : section = layout × copy × visual (3-4 variants/section), _cp() pools par attitude, _sec_vt() visual treatment, _build_visual_system(), _css_visual_panel() 10+ variants palette-dérivés, archetype override via brief signals. Des milliers de combinaisons réelles.
- **2026-03-16 23:30** : `generate_landing_page()` — générateur de landing pages brandées complètes par projet. RenderingContract strict (12 archetypes), direction selection par signaux brief, 3 templates full-page (editorial / playful / SaaS). Output : `landing_page.html` par projet.
- **2026-03-16 22:50** : `render_preview` → `render_direction_preview()` — 3 previews par direction créative, chacun bindé à un RenderingContract strict. ARCHETYPE_CONTRACTS couvre 12 archetypes. Direction selection via signaux brief.
- **2026-03-16 21:45** : `generate_brand_charter.py` — orchestrateur test pipeline design complet (5/5 modules OK, 3 briefs, HTML brand charter)
- **2026-03-16** : `scan_and_do` MVP complet (7/7 tests ✅) — moteur MRG générique
- **2026-03-16** : `theme_generator` phase 1 visuelle (StyleDNA, font_map, theme_translation, visual_analysis — 14/14 tests ✅)
- **2026-03-15** : `conversational_brief` extrait vers EURKAI/MODULES (injectable, agnostique)
- **2026-03-15** : `_ARCHITECTURE_MVP.md` + `_OBJECT_CONTRACT.md` — documents de référence EURKAI
- **2026-03-15** : `visual_consistency_validator` + `design_exploration_engine` complets
- **2026-02-10 19:00** : Architecture orientée objet EURKAI formalisée (atome/method/scenario/injection)
- **2026-02-10 18:45** : TIP_CALCULATOR déployé en production — https://eurekai25.github.io/tip-calculator/
- **2026-02-10 18:30** : PROCESS.md + STANDARDS.md créés, catalogue modules initialisé
- **2026-02-10 17:00** : Création nouveau EURKAI propre, ancien archivé dans `ARCHIVES/EURKAI_HISTORIQUE/`
- **2026-02-10 17:00** : Documentation vision complète, architecture fractale, approche progressive
- **2026-02-10 17:00** : Premier projet test TIP_CALCULATOR lancé avec workflow optimisé
