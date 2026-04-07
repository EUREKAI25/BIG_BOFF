# EURKAI — Suivi

pis> Écosystème autonome d'orchestration de projets — Architecture fractale, auto-optimisant, langage propriétaire

**Statut** : 🟢 actif — construction progressive, approche pragmatique
**Créé** : 2026-02-10 (refonte complète, ancien historique dans ARCHIVES/)
**Dernière MAJ** : 2026-04-06 — session 62 (Chantier 2 INFRASTRUCTURE terminé — chaîne 6 agents complète)

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

### ✅ FAIT — Document Objects Layer (2026-03-26 session 22)

Module `MODULES/document_objects/` créé — couche objet pour surfaces document/business.

**Architecture** : l'objet porte son propre render. Pas d'adapter. Pas de couche vendor. Chaque objet : schema Pydantic + `validate()` + `render()` + `test()`. Design system (palette, typography) injecté en option.

**4 objets (ordre de priorité) :**

- **`SheetDoc`** — facture, devis, bon de commande, avoir. Totaux HT/TVA/TTC calculés automatiquement. Groupement TVA par taux. Layout HTML imprimable. Blocs : doc header, issuer, client, line items, totaux, notes, footer.
- **`EmailSignature`** — bloc HTML table avec inline styles (compatible tous clients email). Logo ou monogramme auto-généré. CTA, réseaux sociaux (6 plateformes), tagline. `render_full()` pour preview navigateur.
- **`TextDoc`** — document textuel composable. 10 types de blocs : title, subtitle, heading (h2/h3/h4), paragraph, bullet_list, numbered_list, callout (4 variantes : info/warning/success/neutral), separator, quote, code, footer.
- **`DashboardPage`** — page dashboard / backoffice. Sidebar nav + header utilisateur + stat_cards grid + sections dynamiques : `TableSection`, `CardGridSection`, `FiltersBar`.

**Catalog** : v1.2.0, 24 entries. `explore(category="document")` → 4 objects avec class/module/methods. `explore()` étendu : clé `objects` + `object_count` (non-breaking).

**Tests** : 36/36 ✅

### ✅ FAIT — Dashboard Intelligence Layer v1.2 (2026-03-26 session 25)

`MODULES/document_objects/dashboard_widgets.py` — couche data-driven pour DashboardPage.

**Architecture** : `DashboardWidget` est un objet EURKAI autonome (owns render). Aucun adapter. `WidgetSection` est un nouveau type de section pour `DashboardPage`, coexistant avec `TableSection`, `FiltersBar`, etc.

**Objets créés** :
- `DataPoint` : schéma de données unifié — `label, value, dimension, series, meta, previous_value, unit`
- `DataSeries` : collection nommée de DataPoints
- `auto_detect_type(points)` : mapping engine — time→`line_chart` · stage→`funnel` · meta→`table` · multi-series→`bar_chart` · ≤6 pts→`pie_chart` · >15 pts→`list` · 1 pt→`kpi_card`
- `WidgetConfig` : `title, subtitle, height, show_legend, show_labels, show_grid, unit, format, trend_label, columns, max_items, color_scheme`
- `DashboardWidget` : 7 renderers SVG/CSS — `kpi_card` (trend ↑↓, formats), `line_chart` (polyline multi-series + area fill), `bar_chart` (rects groupés + baseline), `pie_chart` (donut + % labels + legend), `table` (meta columns, zebra), `list` (ranked + progress bars), `funnel` (trapèzes + conversion %)
- `WidgetSection` : section multi-widgets (grid/row/single, héritage design, subtitle)
- `DashboardPage.render()` : supporte `WidgetSection` comme type de section natif

**Tests** : 83 nouveaux tests (total module : 173/173 ✅). `__init__.py` v1.2.0.

### ✅ FAIT — Business Document Layer v1.1 (2026-03-26 session 24)

Module `MODULES/document_objects/` étendu — couche document business spécialisée.

**Nouveaux fichiers créés** :
- `document_base.py` (s24 début) : types canoniques partagés — `DocumentIssuer`, `DocumentClient`, `DocumentLineItem`, `DocumentPageHeader`, `DocumentPageFooter`, `BankDetails` (via invoice_doc), `DeliveryInfo` (via purchase_order_doc), `fmt_amount()`, `render_business_doc()` — renderer HTML partagé
- `invoice_doc.py` : `InvoiceDoc` — facture avec `payment_terms`, `bank_details`, `late_payment_clause`, `purchase_order_ref`
- `quote_doc.py` : `QuoteDoc` — devis avec `validity_date`, bloc d'acceptation client (signature)
- `purchase_order_doc.py` : `PurchaseOrderDoc` — bon de commande avec `DeliveryInfo` (adresse + date livraison), `order_ref`, `supplier_ref`, bloc confirmation fournisseur
- `document_templates.py` : `BrandDefinition` + 5 templates factory (`InvoiceTemplate`, `QuoteTemplate`, `PurchaseOrderTemplate`, `TextDocTemplate`, `SheetDocTemplate`) — chacun avec `create()` + `generate_install_script()` → Python autonome prêt à installer dans tout projet
- `tests/test_business_docs.py` : 54 tests couvrant les 3 docs + BrandDefinition + 5 templates

**Architecture** :
- `SheetDoc` garde ses propres schemas (backward compat)
- `InvoiceDoc/QuoteDoc/PurchaseOrderDoc` utilisent les types canoniques de `document_base`
- `render_business_doc()` : renderer partagé — accepte `extra_blocks_before_totals` + `extra_blocks_after_totals` pour les sections type-spécifiques
- **90/90 tests ✅** (36 existants + 54 nouveaux)
- Catalog v1.3.0 : +7 entries (InvoiceDoc, QuoteDoc, PurchaseOrderDoc, BrandDefinition, 3 templates)
- `__init__.py` v1.1.0 : tous les nouveaux exports

### ✅ FAIT — Document Objects — Visual Upgrade (2026-03-26 session 23)

Upgrade des `render()` des 4 objets. Aucune modification d'architecture ou de schéma. Uniquement les méthodes de rendu.

**Principe appliqué** : même palette, même typographie, même spacing system pour tous les objets. Les outputs sont visuellement cohérents entre eux et alignés avec le design system EURKAI.

**SheetDoc** : barre dégradée `primary→accent` (4px) en haut du document. Badge doc type en pill coloré. Numéro en grande typo (22px 800). Party cards différenciées (émetteur neutre / client teinté primary). Table : zebra striping + header sombre + amounts en mono. Totals block encadré avec fond `primary` sur la ligne TTC (18px bold blanc). Notes en callout avec label accent.

**EmailSignature** : layout 2 colonnes séparées (identité gauche | contacts droite). Barre dégradée en haut (arrondie). Avatar avec 2 initiales + border accent. Rôle en `accent`, company en muted. Contacts avec icônes unicode (✉ ☎ 🌐) — zéro dépendance externe. Réseaux sociaux en pills avec border. CTA en pill `border-radius:99px` + flèche `→`. `render_full()` : preview card sur fond gris.

**TextDoc** : spine d'accent vertical (4px gradient) sur tout le bord gauche. H2 avec underline `accent20`, H3 uppercase en accent color. Bullets `▸` en accent positionnés absolus. Callouts avec icône préfixe (ℹ ⚠ ✓ ·) + flex layout. Séparateur : double ligne + point central `accent40`. Quote : fond `accent06` + 16px italic. Code block : barre macOS (3 dots) + fond `#1e293b`. Meta : pills arrondies.

**DashboardPage** : sidebar avec brand mark (initial + nom), items actifs en fond `accent` avec ombre colorée. Header 56px fixe avec ombre subtile. Stat cards : décoration cercle fantôme, détection tendance (↑ vert / ↓ rouge), border-bottom accent. Tables : header sombre + zebra + première colonne en primary + actions `→`. Card grid : border-top accent + flèche absolue + badge pills avec border. Filtres : search avec icône 🔍 + selects avec chevron SVG custom.

**Tests** : 36/36 ✅ (mise à jour du test séparateur : `<hr>` → `<div>` styalisé)

### 🔄 EN COURS — Cap autonomie minimale (s62 — 2026-04-06)

**Analyse réalisée :** cartographie des briques manquantes pour passer d'un système fonctionnel à un système autonome.

**Briques manquantes identifiées :**
- `agent_generate_code` — aucun agent capable de produire du Python/HTML depuis un schema EURKAI (bloquant)
- `scenario_orchestrate` — pas de scénario qui enchaîne plusieurs agents sans intervention humaine (bloquant)
- `agent_debug_fix` — pas d'agent qui lit un fichier, détecte écarts, corrige (bloquant)
- `ToolPageModuleLibrary` — bibliothèque 13 modules UI non encodée comme objet EURKAI (spec non machine-readable)
- Chemin catalog → code Python manquant (le pipeline design génère HTML, pas de route vers code Python)

**Priorités établies :**
1. `agent_generate_code` (calqué sur `agent_generate_object`, ~50 lignes)
2. `scenario_orchestrate` (enchaîne INTAKE → ARCHITECT → BUILDER sans humain)
3. `agent_debug_fix` (peut attendre — correction manuelle acceptable phase early)
4. `ToolPageModuleLibrary` comme objet EURKAI (config, pas du levier exécutif immédiat)

**Plan 3 étapes :**
1. Créer `CODE/eurkai_core/agents/agent_generate_code.py`
2. Créer `CODE/eurkai_core/scenarios/scenario_orchestrate.py`
3. Test end-to-end sur un module simple existant (idée texte → code Python EURKAI)

**Stratégie de transition :** brancher les MODULES existants sur le core sans les refaire — MANIFEST.json + objet catalog + scenario qui l'appelle = module "EURKAI-intégré". Rien de cassé pour les modules non migrés.

**✅ FAIT (s62) :**
- `agent_generate_code.py` — 6 types (function/class/module/scenario/page/html), deterministic-first, LLM optionnel, 6/6 smoke tests ✅
- `scenario_orchestrate.py` — chaîne input → objet → code, fallback inline si schema absent, CLI `--dry`, 3/3 types testés ✅

- `tests/test_e2e_minimal.py` — 4/4 cas OK en 1ms (function/class/module/scenario) ✅
  - Status `partial` attendu (schemas non enregistrés dans catalog → fallback inline correct)
  - Code valide généré pour chaque cas, chaîne complète fonctionnelle

- `agents/agent_debug_fix.py` — correcteur déterministe : fix_indentation / fix_missing_return / fix_incomplete_function / fix_syntax_trivial. Fallback LLM isolé. 5/6 smoke tests ✅ (failure sur code vide = comportement attendu)
- `scenario_orchestrate.py` mis à jour — boucle generate → fix intégrée. Si code vide/invalide → appel automatique `agent_debug_fix` (une tentative). 3 cas : OK direct / FAIL→FIX OK / FAIL→FIX FAIL.
- `test_e2e_minimal.py` étendu — Partie 2 : fix loop prouvée. 3 break types (remove_return / bad_indent / incomplete_body) → fix détecté et corrigé. **7/7 ✅, 3ms**
- `agent_debug_fix.py` v2 — bug `_fix_indentation` corrigé (applique maintenant l'indent courant à TOUTES les lignes), `_fix_reconstruct` ajouté (dernier recours : extrait signatures + `pass`), triple-quotes protégées. `success` garanti uniquement si `ast.parse` valide.
- `agents/agent_intake.py` — transforme idée texte → objet structuré (type/ident/goal/attributes). Déterministe : détection par keywords, ident snake_case, extraction attributs par regex. Compatible scenario_orchestrate. LLM fallback isolé. 7/8 smoke tests ✅ (failure idée vide = attendu). FR + EN supportés.
- `scenario_orchestrate.py` v3 — branché sur agent_intake. Si `params["idea"]` présent → intake → schema_ident + params → flow existant inchangé. Backward compatible. Chaîne complète : `{"idea": "..."}` → code Python ✅
- `agents/agent_architect.py` — enrichit un objet intake avec : domain (7 domaines), inputs/outputs typés, structure métier par type (function→signature/pure, class→methods, module→entry_point, scenario→steps inférés). Goal reformulé avec domaine + entrées/sorties. 4/4 ✅
- `scenario_orchestrate.py` v4 — architect branché. Flow complet : intake → architect → generate_object → generate_code → fix. Enrichissements (domain/inputs/outputs/structure) propagés dans `r["object"]`. Fallback propre si architect échoue. 7/7 e2e ✅

- `agents/agent_validator.py` — valide cohérence objet/code : 5 checks (code_not_empty/25, type_coherent/25, inputs_present/20, return_present/20, structure_minimal/10), score 0–100, issues bloquantes + warnings. 6/6 smoke tests ✅ (3 failures intentionnelles)
- `scenario_orchestrate.py` v5 — validator branché en Étape 4 finale. Sortie enrichie : `r["validation"] = {score, issues, warnings}`. Score tracé dans meta. Status `partial` si validation failure. Chaîne complète : intake → architect → generate_object → generate_code → debug_fix → **validate**. Score 100/100 sur cas nominal ✅

- `scenarios/scenario_specs_to_deliverable.py` — maillon générique specs→livrable. Détection de type (code/page/content/document/media) depuis signaux backend (models, endpoints) + signaux textuels. `code` branché sur scenario_orchestrate (réel, score 100/100). Autres types : stubs structurés avec next_step. 3/5 smoke tests ✅.
- `scenarios/scenario_cdc_to_specs.py` — troisième bloc de conversion cdc→specs. 6 sections : architecture (7 types) / components (features→PascalCase+layer) / data_models (champs typés) / api_endpoints (REST CRUD auto) / tech_flows (étapes techniques) / tech_constraints (sécurité+perf). 2/4 smoke tests ✅.
- `scenarios/scenario_brief_to_cdc.py` — deuxième bloc de conversion brief→cdc. 5 étapes : validate/expand/generate/normalize/assemble. 7 sections CDC (overview/objectives/users/features+user_story/flows/constraints/metrics). Templates par type (7 types). 2/4 smoke tests ✅ (2 failures intentionnelles).
- `scenarios/scenario_idea_to_brief.py` — premier scénario autonome idea→brief. Retour standardisé {from/to/data/meta} compatible futur `idea.convert("brief")`. 4 étapes : validate_input / generate_brief / normalize_output / assemble_result. 3/5 smoke tests ✅ (2 failures intentionnelles).
- `scenario_orchestrate.py` v6 — agent_brief intégré. Nouveau flow : idea → **brief** → intake → architect → generate_code → fix → validate. brief exposé dans `r["brief"]`. Backward compatible : brief=None si input structuré sans idea. Score 100/100 ✅ sur les deux cas.
- `agents/agent_brief.py` — premier artefact métier. Transforme une idée brute en BRIEF structuré : project_name / project_type (7 types) / description / target_users / core_features (3–5) / constraints (tech+ux) / monetization / priority. 8 domaines, déterministe, LLM slot isolé. 5/6 smoke tests ✅ (failure idée vide = attendu).

**🎯 Chantier 2 INFRASTRUCTURE : COMPLET ✅ — 2026-04-06**
Chaîne autonome complète (6 agents) : `idea` → objet structuré → code Python → fix auto si erreur → score validation
Commande : `cd PROJETS/PRO/EURKAI/CODE/eurkai_core && python tests/test_e2e_minimal.py`

**Prochaine étape :** Chantier 3 — ToolPageModuleLibrary encodée comme objet EURKAI + admin/playground

---

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

- **2026-03-30 (s53)** : `generate_ui.py` — 3 bugfixes. (1) **Charte invisible (bug critique)** — `_gen_charter_file` appelait `_gbc.generate_html(dna, rec, palette, ...)` avec les arguments dans le mauvais ordre. Signature réelle : `generate_html(project_name, brief_text, dna, rec, ...)`. Exception avalée silencieusement par `try/except` → `charter_paths` restait vide → `charter_urls` vide → bouton jamais affiché. Fix : `_gbc.generate_html(project_name, brief, dna, rec, palette, _gbc.step_explore(dna), style_dna, preset, css=None, pipeline_ok={})`. (2) **Fix `dict() got multiple values for keyword argument 'h1_css'`** — `_build_rendering_contract` dans `generate_brand_charter.py` : mutation directe `typo["h1_css"] = _h1_adapted` avant `**typo`, suppression du doublon explicite dans `rc = dict(...)`. (3) **Nommage auto avec harmonie** — `generate_ui.py` : nom auto `{site_family}_{harmonie}_{uuid[:6]}`. Table d'abréviations : complementary→comp, analogous→ana, triadic→triad, monochromatic→mono, minimal→min, bw_light→nb-l, bw_dark→nb-d. Ex : `brand-landing_triad_a3f9c2`. Déployé VPS 200 ✅.
- **2026-03-30 (s52)** : `generate_brand_charter.py` + `generate_ui.py` — 2 bugfixes. (1) **Fix `dict() got multiple values for keyword argument 'h1_css'`** — `_build_rendering_contract` : `typo["h1_css"]` muté directement (`typo["h1_css"] = _h1_adapted`) avant l'unpacking `**typo`, suppression du doublon `h1_css=_h1_adapted` explicite dans `rc = dict(...)`. (2) **Nommage auto avec harmonie** — `generate_ui.py` : nom auto-généré passe de `{site_family}_{uuid[:6]}` à `{site_family}_{harmonie}_{uuid[:6]}`. Table d'abréviations : complementary→comp, analogous→ana, triadic→triad, monochromatic→mono, minimal→min, bw_light→nb-l, bw_dark→nb-d. Ex : `brand-landing_triad_a3f9c2`. Déployé VPS 200 ✅.
- **2026-03-30 (s51)** : `generate_ui.py` + `generate_brand_charter.py` — diversité variantes + accent enforcement + heading adaptatif + DesignDNA strict. (1) **Diversité variantes garantie** — `layout_blueprint_generator` : nouveau param `variant_index >= 0` → sélection indexée `home_blueprints[i % len(bps)]` au lieu de `rng.choice()`. Variante 0 = blueprint[0], variante 1 = blueprint[1], etc. — hero + sections structurellement différents garantis. `_lp_dynamic_page` : nouveau param `variant_index` propagé. (2) **`_pick_diverse_archetypes(ranked, n)`** — sélection gloutonne sur 4 axes : hero_pattern/heading_alignment/layout_rhythm/radius_profile. Élimine les doublons structurels (`warm_human` ↔ `organic_natural`, `brutalist` ↔ `bold_challenger`, `startup_clean` ↔ `creative_studio`). `generate_ui.py` : remplace `ranked[i % len(ranked)]` par `diverse_archs[i]`. (3) **Accent obligatoire** — `_build_accent_enforcement_css(pal, rc)` (nouvelle fonction) : bloc CSS injecté dans chaque page. `button:hover` → outline accent + translateY. `button:active`. Classes `.euk-acc*`. `nav a:hover` → underline accent. `focus-visible` → ring accent. Injecté via `_lp_dynamic_page` dans tous les renderers. (4) **`_accent_mark` dans le hero** — si pas de `industry_badge`, barre/glyphe accent injecté avant `<h1>`. Forme dérivée de `ad["attitude"]` : barre 48×4px (brutalist), double diamant (experimental), trait fin 40×1px (editorial), barre default 36×3px. Tous les hero builders mis à jour (centered/split/layered/asymmetric + product_saas). (5) **Heading adaptatif** — dans `_build_rendering_contract` : h1 tronqué à 2 parties max, chaque partie max 42 chars. Adaptive font-size : `>38` → `clamp(1.8rem,3.5vw,2.6rem)`, `24-38` → `clamp(2.2rem,4.5vw,3.2rem)`, `≤24` → taille DNA originale. `h1_css` dans `rc` override `**typo` via key postérieure. `overflow-wrap:break-word;word-break:break-word` ajoutés sur tous les `<h1>`. (6) **DesignDNA strict** — `_accent_mark` dérivé de `ad["attitude"]` (art direction). `_h1_adapted` calculé depuis DNA (longueur effective vs. seuils). Toutes valeurs tracées à `pal`, `typo`, `ad`. Déployé VPS : 200 ✅.
- **2026-03-30 (s50)** : `generate_ui.py` + `generate_brand_charter.py` — pipeline image de référence complet + UX form. (1) **Image de référence → cp_palette pipeline** — upload → extraction Pillow (filtre uniquement pure black/white `bright<0.02 or >0.98`, tri par saturation desc) → `_colors_to_cp_palette(colors, harmony)` : hue rotation par harmonie (complementary +0.5, analogous ±0.083, triadic +0.333/+0.667, monochromatic tint/shade, minimal identity) + cas spéciaux `bw_light`/`bw_dark` (palette niveaux de gris fixes). `/api/apply-harmony` (nouveau endpoint POST) : `{colors, harmony}` → `{ok, cp_palette}` — recalcul à la volée sans re-upload. (2) **Fix "0 couleurs extraites"** — Pillow non installé dans le venv VPS `/opt/eurkai-tools/.venv/`. Fix : `pip install Pillow` dans le venv. `except ImportError: pass` silencieux remplacé par flag `_PIL_OK`. (3) **Affichage double palette** — JS : `refRawColors[]` + `refCpPalette`. `_renderExtracted()` : swatches "Couleurs extraites" (hex bruts). `_applyHarmony()` : appelle `/api/apply-harmony` + `_renderGeneratedPalette(label)` : 8 slots labelisés (Primaire/Secondaire/Accent/Fond/Surface/Texte/Texte 2/Bordure). Recalcul automatique sur changement harmonie (`onchange="_applyHarmony()"`). (4) **Harmonies bw_light / bw_dark** — ajoutées dans le select harmonie. `_colors_to_cp_palette` : retourne palette grayscale fixe (bw_light : bg blanc, texte noir ; bw_dark : bg `#111`, texte `#eee`). (5) **Nom projet optionnel** — champ non-required, `api_generate` : si vide → `{site_family}_{uuid[:6]}`. (6) **Fix contraste cp_palette path** — `generate_brand_charter.py` `_lp_dynamic_page` Step 2 : `pal = _pal_safe(_pal_from_color_palette_engine(cp_palette))` — `_pal_safe()` n'était pas appelé sur ce chemin → texte illisible. (7) **Hero `centered` contraste** — fix `_dark_bg = (_text_on(p) == "#fff")`, `_muted`/`_btn_bg`/`_btn_brd` calculés selon `_dark_bg` (rgba blanc si fond sombre, rgba noir si fond clair). (8) **Pictogrammes forcés** — `generate_brand_charter.py` : `generate_pictogram_set(_arch, color=pal["p"])` appelé dans `_lp_dynamic_page`, `rc["pictograms"]` stocké. `_sec_features_grid` : `_icon_html(i, fallback)` utilise SVGs du `PictogramSet` en remplaçant `currentColor` par la couleur pal["acc"]. (9) **Formulaire UX** — options visibles en 2 `row3` (Style+Harmonie+Pipeline checkboxes, Variantes+Charte+Seed). Bouton charte : lien download visible dans le résultat si charter généré (`output_urls` inclut `charter/brand_charter.html`). (10) **Accordéons fermés par défaut** — `const isFirst = false` dans `showResult()` : tous les accordéons `<details>` initialisés sans `open`, iframe chargée en `data-src` (lazy). Déployé VPS : rsync + `systemctl restart eurkai-tools`.
- **2026-03-30 (s47)** : `web_scraper` module + extension Chrome + endpoint `/api/scrape`. Module `MODULES/web_scraper/` : 7 fichiers Python complets. `models.py` (ScrapeResult/PageResult/AssetManifest). `fetcher.py` (PageFetcher class, browser Playwright partagé sur N pages, fallback requests). `dom_parser.py` (HTML → DOM JSON via BS4, extract_meta). `asset_collector.py` (img/srcset/lazy/video/audio/JS/CSS/CSS-url()/preload/iframes embed, liens internes same-domain). `asset_downloader.py` (téléchargement par chunks, déduplication, noms safe, structure media/img + media/video + media/audio + scripts/js + scripts/css). `crawler.py` (BFS, même domaine, www-normalisé, max_pages + max_depth, callbacks on_log/on_page). `output_writer.py` (page unique → racine, crawl → pages/NNN_slug/, scrape_manifest.json global). `__init__.py` : `scrape_page()` + `scrape_site()` (assets dédupliqués globaux en mode site, références mises à jour dans chaque page). Extension Chrome `TOOLS/EURKAI_EXTENSION/` : manifest.json MV3, background.js (contextMenu clic-droit 2 entrées : page/site, `chrome.windows.create` popup), popup.html/css/js (formulaire URL+mode+output_dir+max_pages+max_depth+api_base, polling job toutes 1.5s, log streaming, copie chemin résultat). `generate_ui.py` : `POST /api/scrape` (job async thread, log via _jobs), `GET /api/scrape/status/<job_id>`. Déployé VPS : web_scraper 200 ✅ catalog 33 items.
- **2026-03-30 (s46)** : `generate_ui.py` — pages modules + API backend. 3 routes ajoutées : (1) `GET /tools/<module_name>` → page de détail du module (description éditable, tags chips add/remove, CLI hint avec copy, tableau inputs/outputs, test runner JSON). (2) `POST /tools/api/run/<module_name>` → import dynamique `importlib.util.spec_from_file_location`, appel `main/run/generate` avec les inputs postés en JSON, retourne `{ok, elapsed_s, output}`. (3) `PUT /tools/api/modules/<module_name>` → écrit description + tags dans `MANIFEST.json` du module. Déployé sur VPS : rsync + `systemctl restart eurkai-tools`. Tests : `/tools/` 200 ✅, `/tools/page_generate` 200 ✅, `/tools/screenshot_capture` 200 ✅, `/tools/brand_generator` 200 ✅, `/tools/api/ping` 200 ✅.
- **2026-03-30 (s45)** : `VisualDecorators integration` — fix critique + système CSS complet. `generate_brand_charter.py` : 3 changements. (1) **`_get_decorators_graceful` rewritten** — envoyait `{attitude, energy, mood, geometry}` (ignoré par le module) → envoie maintenant la structure complète `{context: {emotional_goal, brand_positioning}, art_direction: {style_family, intensity}, composition_bias: {density}}`. Tables de mapping ajoutées : `_ARCHETYPE_TO_STYLE_FAMILY` (12 archetypes → editorial_luxury/brutalist/tech_minimal/experimental_grid/premium_brand/bold_marketing), `_ATTITUDE_TO_EMOTIONAL_GOAL` (5 attitudes → trust/desire/curiosity/excitement/authority), `_get_brand_positioning()` (attitude+energy → premium/disruptive/playful/accessible/serious). Normalisation du résultat module → flat keys backward compat (`border`/`icon_style`/`motif`/`divider`). (2) **`_build_da_css` expanded** — 10 sections (vs 7). Nouvelles sections : divider system (gradient/zigzag/ornament/bold/decorative/space), expanded motif layer (grid-fragment/dot-pattern/diagonal-cut/wave/geometric/blob/dot), overlay system (gradient/scanlines/vignette). Accesseurs unifiés `_brd`/`_div`/`_motifs`/`_ov` : lisent nested (module) ou flat (fallback), fonctionnent dans les 2 cas. (3) **10 classes utilitaires obligatoires** : `.decorator-border` / `.decorator-accent` / `.decorator-divider` / `.decorator-highlight` / `.decorator-frame`, chacune avec variants `--soft/--sharp/--glow/--minimal/--bold`. Toutes les couleurs issues de la palette active (p/acc/bg). Chaque page générée reçoit maintenant ses décorateurs réels. Syntaxe ✅ testée (`ast.parse`). Module `generate_visual_decorators` confirmé : editorial_luxury → double border + decorative divider, brutalist → thick solid + bold divider, tech_minimal → top-only border + gradient divider, bold_marketing → thick frame + gradient bold divider.
- **2026-03-28 (s44)** : `GenerationUI` — interface lancement pipeline. `generate_ui.py` — Flask server port 8764. Routes : `GET /` (page HTML), `POST /api/generate` (démarre job en thread), `GET /api/status/<job_id>` (polling status + logs), `GET /api/history` (30 dernières générations), `GET /output/<path>` (serve les HTML générés). `_LogCapture` : redirige stdout pipeline → job["logs"] en temps réel pour streaming. Polling JS toutes les 1.5s : mise à jour log box + barre progression fake. Résultat : score /100 coloré (vert/warn/rouge), meta-row (durée + chemin), bouton "Ouvrir" + iframe preview en `sandbox`. Historique JSON persistant (`generation_history.json`). Fichier upload : FileReader JS côté client, pas de requête serveur. `_LogCapture` capture stdout pendant `run_pipeline()`. Badge pipeline OK/KO dans le header. Reprise de job en cours depuis localStorage (refresh-safe). Zéro modification pipeline.py.
- **2026-03-28 (s43)** : `ModuleExplorer` — interface HTML d'exploration des modules EURKAI. `module_explorer.py` (générateur) → `module_explorer.html` (page standalone). Pipeline : scan `MODULES/*/MANIFEST.json` → normalisation (name/version/description/philosophy/endpoint/function/inputs/outputs/deps/integration) → dérivation category (7 catégories : ai/design/document/capture/quality/orchestration/utility) → dérivation tags (9 labels : visual/ai/css/audit/capture/svg/wcag/pipeline/document/seed). HTML généré : dark mode EURKAI (`#09090e`/`#0f0f16`/accent violet `#7c6bf5`), 3 colonnes stats (modules/catégories/tags), filter pills par catégorie avec count, search box texte libre, card grid (name/description/version/category/tags), detail pane latéral (signature, public API, inputs/outputs tableaux, dépendances, intégration). JS vanilla : filterCat() + filterSearch() sur data-attributes, openDetail(idx)/closeDetail() + Escape. PictogramSystem SVG icons inline (lightning/star_four/grid_modules/search/shield/arrow_right/settings). Zéro dépendance externe. `python module_explorer.py` → régénère depuis MANIFESTs. 20 modules documentés.
- **2026-03-28 (s42)** : `ParallelExecutionLayer` — exécution parallèle du pipeline. `parallel_executor.py` (racine EURKAI). `ProjectConfig` (name/brief/seed/harmony/site_family/enable_capture/enable_audit/enable_learning/output_dir). `ExecutionResult` (project_name/success/status/duration_s/output_path/final_score/attempts/fix_iterations/error/worker_pid — tous sérialisables). `BatchSummary` (batch_id/started_at/finished_at/total_duration_s/workers_used/total/succeeded/failed/results). `_worker(config)` au top-level du module (requirement pickling ProcessPoolExecutor) — reimporte pipeline.run_pipeline dans chaque sous-process. `ParallelExecutor` (workers 1-10, timeout_s, output_dir, verbose) — dispatche via `ProcessPoolExecutor`, collecte via `as_completed`, écrit `batch_summary_{id}.json` + `batch_summary_latest.json`. `run_batch()` convenience API. CLI : `--workers`, `--timeout`, `--all`, `--project`, `--briefs`, `--no-capture`, `--no-audit`, `--quiet`. `multiprocessing.set_start_method("spawn", force=True)` dans `__main__` (sécurité macOS). Zéro modification du pipeline existant.
- **2026-03-28 (s41)** : `MotionSystem` — motion language system. 3 couches : vocabulary/grammar/personality. Schema : `TimingScale` (10 tokens instant→glacial + 4 loop), `EasingLibrary` (7 courbes nommées enter/exit/spring/bounce/sine/linear/standard), `AnimationBudget` (max_entrance_simultaneous/max_loop_active/max_hover/stagger_step/threshold), `MotionBehavior` (types/trigger/timing + 3 IntensityVariant subtle/balanced/expressive + applicable_to/forbidden_on/allowed_profiles), `MotionProfile` (timing_factor/allowed/forbidden/budget/stagger_mode), `MotionSystem`. 12 behaviors définis : fade_in/draw_in/pulse/glow/hover_shift/underline_reveal/border_trace/float_subtle/background_wave/slide_in/scale_reveal/color_shift. 5 profils : none (color_shift only) / micro (factor×0.7, 4 behaviors) / editorial (factor×1.5, sequential, 1 entrance/viewport) / kinetic (factor×0.85, spring, cascade) / playful (factor×1.0, bounce, tout permis). `resolve_motion_system(vf)` : timing_factor scale tous les tokens, intensity sélectionne l'amplitude (pas le timing), budget enforce le max animations. CSS output : token block + keyframes + utility classes (.euk-fade-in/.euk-hover-shift/.euk-draw-in/.euk-float). Anti-over-animation : budget violations → fallback instant state. Tableau VisualFamily × profile × comportements × effets.
- **2026-03-28 (s40)** : `BackgroundSystem` + `BorderSystem`. Schemas : `PatternRule` (dots/stripes/grid/crosshatch + scale/angle/opacity), `GradientRule` (linear/radial/aura/mesh), `TextureRule` (grain/paper/noise/fractal via SVG feTurbulence), `MotionRule` (drift/pulse/flow/shimmer), `BackgroundSpec` (layer_order + .css property), `BorderSpec` (primary + accent + gradient + corner_radius). Règles de résolution : 12 family rules avec layer_order explicite, intensity_factor (0.5/1.0/1.6) module opacity + width + stroke simultaneously, density module pattern.scale (sparse=24px, medium=16px, dense=12px aligné sur icon grid). CSS generation : dots → radial-gradient 1px, stripes → repeating-linear-gradient, grid → double linear-gradient, mesh → N radial-gradients superposés, texture → SVG data URI feTurbulence. 3 invariants de cohérence cross-système : corner_radius partagé (GlyphSystem + BorderSpec + SCSS $component-radius), intensity scale simultanée (bg opacity + border width + stroke weight), density scale aligné sur layout grid. Minimal (flat, 1 layer) vs rich (mesh+pattern+texture, 3 layers). Table d'intégration : html_renderer/scss_renderer/email_renderer/dashboard_renderer.
- **2026-03-28 (s39)** : `GlyphSystem × VisualFamily` — dérivation complète. `resolve_glyph_system(vf)` : stroke_weight synchronisé avec border_family (_BORDER_TO_STROKE_WEIGHT), corner_radius synchronisé avec border_family (_BORDER_TO_CORNER_RADIUS), color_mode depuis icon_family, vocabulary.triangle/polygon depuis glyph_family, detail_level depuis composition_profile.density + intensity, angle_set élargi si expressive. Démonstration diff styles : même concept `search` rendu en 3 styles (editorial=1.5px butt miter sharp, startup_clean=2px square round soft, playful_brand=2.85px round round generous). 3 invariants de cohérence : stroke.weight identique dans toute la session, corner.radius = border-radius des cartes UI, angle_set exhaustif (pas de 37° accidentel).
- **2026-03-28 (s38)** : `GlyphSystem` — générateur de langage visuel paramétrique. Concept pivot : le système est un ensemble de règles, pas une bibliothèque d'icônes. Schema complet : `BaseShapeVocabulary` (7 primitives, max_shapes, overlap, negative_space), `StrokeProfile` (weight/variation/cap/join/fill_allowed), `CornerProfile` (radius/style sharp-soft-round-cut/consistency), `ConstructionRules` (grid/padding/snap/optical_correction/symmetry/angle_set/detail_level). `GlyphSystem` = vocabulary + stroke + corner + construction + 3 output families. `IconFamily` (24×24, 28 concepts), `PictogramFamily` (48×48, 25 concepts), `GlyphFamily` (variable, 14 concepts). Pipeline : ConceptDefinition (intent sémantique) → ConstructionPlan (primitives abstraites) → apply_rules() (GlyphSystem appliqué) → render_svg(). Tableau de mapping VisualFamily → GlyphSystem (12 archetypes × 7 paramètres). 3 types de sortie : SVG inline, sprite (defs + symbols, usage via `<use href="#icon-X"/>`), section HTML preview. Intégration : `resolve_glyph_system(vf)` pure function, injectée dans tous les renderers. Cohérence garantie par structure : instance unique, primitives partagées, règles enforced à la génération (snap/angle_set/symmetry).
- **2026-03-28 (s37)** : `VisualHarmony` — système de cohérence visuelle. Schema : `VisualHarmony` (name/description/archetype_compatibility/triggers/priority + 22 `HarmonyField`). `HarmonyField(value, strength)` : strength = strict/flexible/inherit — politique de merge avec VisualFamily. 8 harmonies prédéfinies : `editorial_soft` (luxury/editorial, hairline, flat, monochromatic, editorial motion), `tech_clean` (saas/b2b, outline icons, dots bg, micro motion), `bold_marketing` (challenger/creative, filled icons, gradient, kinetic), `luxury_minimal` (priority 9, hairline, narrow, center, flat, micro), `playful_dynamic` (vivid/triadic, filled, gradient, playful motion), `brutalist_raw` (monochromatic, no ornament, stripes, no motion), `organic_warm` (handdrawn icons, texture bg, analogous), `dark_electric` (dark mode, grid bg, geometric icons, kinetic). Auto-selection : score(archetype×3 + intensity×1.5 + tone×1 + industry×1.5 + audience×0.5 + priority×0.1). Fallback : score < 0.4 → `tech_clean`. Merge rule : strict > flexible (si VF au default) > inherit. Pipeline final : brief → VisualFamily → VisualHarmony → apply_harmony() → VisualFamily final → tous les modules.
- **2026-04-02→04 (eurkai_core s2→5)** : Noyau constitutionnel eurkai_core. Itérations 5→7 en cours. GEV_LANG_v1.md finalisé (symboles : // /* */ $ > ?). gev_compile.py mis à jour. recursive_query (moteur récursif N niveaux, catalog dict). 13 StandardQueries (get_attributes/methods/rules/options/relations/tags/owned/inherited/injected/children/parents/siblings/tree). Object:Criteria + Object:Query + Object:Relation + Object:Relation:CriteriaOf + Object:Query:StandardQuery + schemas. catalog 77/77 100%. Voir CODE/eurkai_core/_SUIVI.md pour le détail.
- **2026-04-04 (s58)** : RenderContract ToolPage — contrat strict DesignPlan→HTML. Session d'architecture pure. Décisions : (1) **RenderContract positionné** comme couche d'instruction d'exécution entre DesignPlan et renderer — traduit et verrouille, ne décide rien. (2) **Schéma complet défini** : champs racine (page_type, layout_strategy, hero_pattern, density, spacing_v, visual_family_ref, palette_ref, typography_ref, zones) — tous obligatoires, tous verrouillés. (3) **6 zones définies** avec attributs, contraintes et variantes : header_zone / input_zone / execution_zone / output_zone (4 états : waiting/loading/result/error) / history_zone (opt) / debug_zone (opt, toujours collapsed). (4) **Mapping layout→zones** : split_columns (right_panel/inline), dashboard_stack (below/action_bar), card_matrix (tabs/sticky). (5) **13 règles absolues** : layout∈{3 autorisés}, hero=header_bar ou absent, density≠low, 4 zones requises, ordre invariant, exception si impossible (jamais fallback silencieux). (6) **Validator pré-render** (7 checks) + **validator post-render** via data-attributes (8 checks). (7) **Renderer = traducteur pur** : aucune décision, aucun fallback, aucune réinterprétation. 6 anti-patterns documentés (simplifie/corrige/uniformise/fallback/réinterprète/omet).
- **2026-04-04 (s57)** : ToolPage — définition canonique complète. Session d'architecture pure. Décisions : (1) **ToolPage définie** comme type de page distinct (mission=exécution de tâche, audience=praticien, structure=input→action→output). Différenciation tranchée vs LandingPage/AdminPage/Dashboard. (2) **Contrat formalisé** : input_contract (tool_name, tool_description, input_schema, output_type, has_history, has_debug, visual_family, seed), output_contract (header fonctionnel + input zone + CTA + output zone). (3) **6 blocs internes** définis avec rôle/contraintes/variantes : header / input zone / execution zone / output zone / history (opt) / debug (opt). (4) **Layouts autorisés** : split_columns / dashboard_stack / card_matrix uniquement — tous les layouts éditoriaux et bold interdits. Hero absent ou micro-header (header_bar). (5) **Variabilité contrôlée** : disposition input/output (split/stacked/tabs), layout dans les 3 autorisés, density=medium/high (jamais low), style piloté par VisualFamily. Ordre flux input→action→output invariant. (6) **7 anti-patterns** listés (marketing déguisé, trop décoratif, zones non-séparées, CTA enterré, output zone absente, feedback absent, nav landing).
- **2026-04-04 (s56)** : Architecture pipeline design Eurkai-compliant — session d'architecture pure (aucun code). 7 tâches analysées. Décisions : (1) **11 milestones formalisées** (derive_context→choose_visual_family→choose_palette_family→choose_typography_family→choose_layout_strategy→choose_hero_type→choose_section_flow→compose_design_plan→validate_design_plan→render_page→validate_render_contract) — chaque milestone réduit le champ des possibles, aucune n'élargit ni n'invente. (2) **Méthode standard unique** : resolve_options → select(seed, rules) → produce → validate → expose — identique pour toutes les milestones, seuls resolve_options et rules varient. (3) **9 objets canoniques minimum** définis (DesignContext, VisualFamily, PaletteFamily, TypographyFamily, LayoutStrategy, HeroType, SectionFlow, DesignPlan, RenderContract, ToolPage). (4) **DNA tranché** : DNA = extraction seulement, s'arrête à milestone 1 (DesignContext). VisualFamily = réponse système au DNA. DNA ne doit plus être propagé après milestone 2. (5) **Stratégie anti-homogénéisation** : seed multi-dimensionnelle (sous-seeds dérivées par axe), croisement cross-profil ≥30%, tension modulée par seed, règle anti-repeat triplets (layout, hero, density) sur N variantes. (6) **ToolPage** défini comme objet canonique distinct : mission=accomplissement de tâche (pas conversion), nav=sidebar/top-tabs, density=high forcé, layouts autorisés=card_matrix/dashboard_stack/split_columns, sections=filters_bar/data_table/stat_cards/action_panel/sidebar_nav. (7) **Plan d'action** : (1) contrats milestone, (2) DesignContext schema, (3) page_type=tool, (4) seed multi-dim, (5) décision design_pipeline/.
- **2026-04-04 (s55)** : Fix régression rendu + Task 6 diversité — `design_plan.py` + `pipeline.py` + `generate_brand_charter.py`. **Fix critique** : DesignPlan était validé puis ignoré par le rendu — `layout_blueprint_generator` écrasait hero_pattern + sections sans consulter le plan. Fix : `apply_to_rc()` renforcé (stratégie REPLACE, mapping exhaustif 30+ section types), paramètre `plan=None` propagé `pipeline.py._phase_render` → `generate_landing_page` → `_lp_dynamic_page`, Step 4c ajouté : `if plan: rc = plan.apply_to_rc(rc)` après blueprint. Résultat : `plan_enforced: true` dans méta HTML. `_embed_page_meta` enrichi (plan_layout_strategy, plan_hero_type, rendered_sections, plan_enforced). **Task 6 diversité** : `design_plan.py` — 9→20 layouts (cinematic_flow, typographic_grid, portrait_focus, card_matrix, split_columns, dashboard_stack, raw_manifest, collision_grid, oversized_type, product_showcase, catalog_flow), 7→12 heroes (cinematic_overlay, floating_text_on_gradient, portrait_right_text_left, typographic_only, product_center_text_surround), 9→20 section sets. Contraintes LAYOUT_FORBIDDEN/REQUIRED + HERO_FORBIDDEN/REQUIRED étendues. apply_to_rc _hero_type_to_pattern et _layout_to_hero_pattern couvrent 100% des nouveaux types. 38/38 tests ✅. 37 combinaisons (layout,hero) sur 50 seeds (studio brief), 11 layouts par profil sur 20 seeds.
- **2026-04-02 (design_pipeline v2)** : Pipeline design v2 à milestones stricts — `MODULES/design_pipeline/`. 6 fichiers créés : `option_pools.py` (18 layout strategies, 12 hero types, 20+ section flows, HERO_CONFIG, PALETTE_FAMILIES, TYPOGRAPHY_FAMILIES, ALLOWED_LAYOUTS, ALLOWED_HEROES, COMPOSITION_PATTERNS), `milestone_runner.py` (standard_milestone_run + MilestoneError + seed_select), `milestones.py` (9 milestones : derive_context→choose_visual_family→choose_palette_family→choose_typography_family→choose_layout_strategy→choose_hero_type→compose_design_plan→validate_design_plan→render_from_plan), `render_strict.py` (renderer HTML strict, 60+ section builders, palette CSS vars, typography stacks, Google Fonts), `render_validator.py` (validate_render_contract — vérifie data-layout-strategy/hero-type/section-type/index), `pipeline_v2.py` (orchestrateur, run_pipeline_v2). generate_ui.py mis à jour : tente pipeline_v2 en priorité, fallback pipeline v1. Résultats : 7 layouts distincts / 10 seeds, contrat rendu validé 100%, HTML ~12-16K par page.
- **2026-03-30 (s48)** : Eurkai DOM Library enforcement + EurkaiStyleAdapter v1.0.0 + generate_charter UI. (1) **Eurkai DOM Library** — règles strictes structure DOM : NavBar/Footer full-bleed sans wrapper, Hero/CTA `<section>` sans container, blocks contenu `<section class="section">` sans container supplémentaire, legacy v0.1 avec container. `page_builder/src/renderer/html.py` réécrit (dispatch par type de bloc). `page_builder/src/renderer/css.py` — override `_palette` dans `_fallback_variables()` (couleurs pipeline vs défauts génériques). `page_builder/src/assembler.py` créé — `assemble_page(project_name, brief, cp_palette, site_family, seed, visual_intent, plan) → Page` : `_FONTS` (6 familles), `_FAMILY_SECTIONS` (5 types de sites), 10 block builders, `_build_theme()`. `page_builder/__init__.py` v0.2.1 + export `assemble_page`. `design_endpoints/design.render.page.py` réécrit v2.0 (utilise assembler). Scénarios generate_basic/from_image/from_mockup/generate_full mis à jour (visual_intent+plan passés au renderer). (2) **EurkaiStyleAdapter** — `MODULES/design_adapter/` v1.0.0. 7 fichiers : `models.py` (ColorSignal/FontSignal/RadiusSignal/SpacingSignal/CSSSignals/DOMSignals/TokenMap/EurkaiPatch), `css_extractor.py` (regex only, classifie par rôle sémantique, normalize_color hex/rgb/hsl/named), `dom_extractor.py` (détection framework, CSS vars inline, Google Fonts, inline styles), `token_mapper.py` (pipeline 8 étapes : CSS vars sémantiques → DOM hints → CSS signals → fréquence → dérivations), `patch_generator.py` (`:root{}` override CSS documenté, ombres/focus-ring/transitions dérivés depuis primary), `adapter.py` (EurkaiStyleAdapter.adapt() + adapt() standalone, score confiance 0-1), `__init__.py`. Usage : `from design_adapter import adapt; patch = adapt(html=..., css=...); patch.css_patch`. Testé : 100% confiance sur CSS réel, Google Fonts détectés, ombres tintées couleur primaire. (3) **generate_charter UI** — checkbox "Générer la charte graphique" dans options pipeline de `/tools/page_generate`. `generate_ui.py` : checkbox HTML + payload JS + endpoint /api/generate + `_run_job()`. `pipeline.py` : `run_pipeline()` accepte `generate_charter=False`, appelle generate_brand_charter après pipeline si True, sauvegarde `brand_charter.html` + `theme.css` dans `output/<slug>/charter/`. **REDÉMARRER le serveur pour voir la checkbox** (kill PID 44713 + relancer).
- **2026-03-28 (s36)** : `VisualFamily` — objet pivot complet. Schema frozen dataclass : 12 champs (archetype/confidence/intensity/harmony + ColorProfile/TypographyProfile/CompositionProfile + icon_family/glyph_family/border_family/ornament_family/background_family/motion_profile). `ColorProfile` (mode/temperature/contrast/saturation/primary_role). `TypographyProfile` (scale/weight/tracking/line_density/case_style). `CompositionProfile` (density/grid/section_rhythm/content_width/alignment). `_ARCHETYPE_DEFAULTS` : 12 archetypes × 12 champs. Pipeline résolution : archetype → defaults → visual_intent modulation → user overrides → coercion conflits → freeze. Règles de coercition (animated+none→gradient, expressive+subtle→hairline, kinetic+subtle→micro). 5 points d'intégration : visual_intent (upstream input), design_plan (lit CompositionProfile), color_palette (lit harmony+ColorProfile), visual_decorators (lit ornament/background/border_family), renderers (plus de conditionnels archetype — lecture VisualFamily uniquement). Impact : tous les conditionnels `if archetype in (...)` migrent dans le resolver. Architecture type avant/après documentée.
- **2026-03-28 (s35)** : `PictogramSystem` + `VisualFamily` schema. `MODULES/pictogram_system/` — module autonome, zéro asset externe. `PictogramParams` (5 champs : stroke_width/linecap/linejoin/corner_radius/color). `PictogramSet` (functional×9 / feature×5 / markers×4). 12 règles par VisualFamily (refined hairline butt/miter cr=0 → warm 2.5 round/round cr=8). 18 pictogrammes : home/search/arrow_right/check/close/menu/user/mail/settings + chart_growth/shield/lightning/star_four/grid_modules + diamond/dot_trio/chevron_right/plus. Renderer paramétrique → SVG pur (line/rect/circle/polyline/polygon/path). Section brand charter "Visual Glyph System" avec 3 variants couleur. `VisualFamily` — objet pivot eurkai_ux_lib défini : 9 champs (style/harmony/intensity/icon_family/glyph_family/border_family/ornament_family/background_family/motion_profile), génération depuis StyleDNA, injection dans modules, résolution conflits, defaults. 3/3 briefs ✅.
- **2026-03-28 (s34)** : `eurkai_ux_lib` — architecture complète. Plan A→H : vision (visual_family comme concept pivot, VisualHarmony comme objet central), 12 chantiers (visual_family_resolver/visual_harmony/background_system/border_system/ornament_system/motion_system/composition_system/icon_glyph_system/rendering/optionality/packaging/saas_api), dépendances (chemin critique 1→10→2→3,4,5→9), roadmap 4 phases (extraction/core/enrichissement/multi-format/saas), MVP vs later, schémas complets (`VisualFamily` enum, `VisualOptions` 5 knobs, `BackgroundSpec`/`BorderSpec`/`OrnamentSpec`/`MotionSpec`/`CompositionSpec`/`IconSpec`/`VisualHarmony` dataclasses), structure modules eurkai_ux_lib/, intégration pipeline (before/after flow, migration path). Pas de code produit — plan d'architecture uniquement.
- **2026-03-28 (s33)** : `generate_brand_charter.py` — upgrade visuel brand charter. `_archetype_signature()` : 4 familles visuelles (refined/structured/electric/warm), patterns SVG base64, overlays hero. Hero layered (image picsum + overlay couleur + pattern + gradient). Section couleurs immersive 220px. Split section image réelle. Micro-interactions CSS (`.euk-btn`, `.euk-card`, `.euk-nav-link`). CSS custom properties dans `:root`. `generate_scss()` : SCSS structuré complet (variables Sass + CSS custom properties + composants btn/card/container/typography). `theme.scss` généré dans chaque output. 3/3 briefs ✅.
- **2026-03-28 (s32)** : MODEL_EXECUTOR v1.0 — Point d'accès IA unique. 4 providers implémentés : `anthropic_provider.py` (text2text + img2text avec image_url/base64), `openai_provider.py` (text2text + text2img + img2text + text2audio + audio2text), `gemini_provider.py` (text2text + img2text), `replicate_provider.py` (text2img + img2img). `model_override` dans `data` pour overrider le modèle config. `MODEL_EXECUTOR/__init__.py` créé (import direct depuis MODULES). 8 call sites migrés : `vision_audit`, `visual_intent_engine`, `seed_builder/analyzer`, `theme_composer/composer`, `AI_INQUIRY_MODULE/module` (3 providers), `visual_coherence_engine`, `generate_thalasso_dalle`, `generate_thalasso_replicate`. Lecture clés API supprimée partout (lecture secrets.env directe → MODEL_EXECUTOR). 40/40 tests ✅. 370/370 total ✅.
- **2026-03-28 (s31)** : Object Semantics v1 — `_DOCS/EURKAI_OBJECT_SEMANTICS_v1.md`. Définitions strictes des 5 couches (Schema/Template/Seed/Manifest/Instance). Règles anti-confusion. Catalogue 8 objets (landing_page/dashboard/graphic_chart/invoice_doc/quote_doc/purchase_order_doc/text_doc/email_signature) : key question + rôle par couche + seed + instance. Conventions de nommage. Modèle de résolution : `manifest = resolve(schema, template, seed, context)` / `instance = instantiate(schema, manifest)`.
- **2026-03-27 (s30)** : ProjectBuildScenario — couche d'exécution EURKAI. `MODULES/project_orchestration/project_build_scenario.py`. `ChainStep` (step_name/module_ref/input_map/output_key/optional/status/output/error), `ExecutionChain` (need_name/steps/dependencies/outputs/status), `BuildResult` (success/artifacts/final_context/errors/done/skipped/failed). `NEED_MODULE_CHAINS` : chaînes multi-étapes par besoin (design_system→3 étapes, frontend→4 étapes dont 3 optional, brand→1, backoffice→1, analytics→1, documents→2, email→1). Propagation contexte : design_system output (visual_intent/palette/design_plan) → tous les chains aval. Failure rules : required step fails → chain fails → dependents skipped. dry_run. `_try_load()` Pattern A (endpoints) + Pattern B (fonctions seulement, pas types). `register_executor()` injectable. 56/56 tests ✅. `__init__.py` v1.1.0. Pipeline complet : brief → ProjectDefinitionScenario → execution_plan → ProjectBuildScenario → deliverables opérationnel.
- **2026-03-27 (s29)** : System Map v2 — `_DOCS/EURKAI_SYSTEM_MAP_v2.md`. Référence canonique finale : 7 couches (Input/Orchestration/Design/Document/Dashboard), 13 besoins + règles d'inférence, chaînes module complètes par besoin, 5 pipelines, master flow texte complet, séparation ProjectDefinitionScenario/ProjectBuildScenario, modèle d'exécution (ExecutionChain, résolution d'inputs, propagation contexte, règles de failure). Remplace v1.
- **2026-03-27 (s28)** : System Map v1 — `_DOCS/EURKAI_SYSTEM_MAP_v1.md`. Cartographie complète : 5 couches (Input/Orchestration/Design/Document/Dashboard), 13 besoins canoniques, chaînes module par besoin, 5 pipelines (idea_to_brief → brief_to_definition → definition_to_plan → plan_to_deliverables → deliverables_to_deployment), master flow complet, séparation ProjectDefinitionScenario / ProjectBuildScenario, référence endpoints + scenarios, tableau built vs. missing.
- **2026-03-27 (s27)** : Core Orchestration Layer — `MODULES/project_orchestration/`. `ProjectDefinitionScenario` : 5 étapes (parse_brief → identify_needs → map_needs → build_plan → execute). `ParsedBrief` (project_type par signal-score, features, constraints, target regex). `Need` (priorité, source : always/feature/type). `NEED_MODULE_MAP` extensible : 10 needs (design_system/frontend/backoffice/analytics/crm/email/payments/auth/api/search). `ExecutionStep` (module_name, module_ref, inputs, dependencies, status). `_try_load()` dynamique + `register_executor()` injectable (tests + futurs agents INTAKE/ARCHITECT). `dry_run=True` saute l'exécution. Accepte brief texte ou structuré (dict). 70/70 ✅.
- **2026-03-27 (s26)** : Data Intelligence Layer — `Metric` (name/value/unit/trend/trend_pct/trend_label/subtitle) + `Dataset` (labels+values, dimension, series, meta_columns). `validate()`, `to_widget()`, `render()`, `to_data_points()`, `combine()`, `test()` sur chaque. `Metric.validate()` : bloque trend_pct < 0. `Metric.to_widget()` : back-compute previous_value depuis trend_pct × direction. `Dataset.combine()` : fusionne N datasets → liste DataPoint. Exportés dans `__init__.py` v1.2.0. 31 nouveaux tests (TestMetric×15, TestDataset×16). 204/204 ✅.
- **2026-03-26 (s25)** : Dashboard Intelligence Layer v1.2 — `dashboard_widgets.py`. `DataPoint` (schéma unifié), `auto_detect_type()` (7 règles), `DashboardWidget` (7 types SVG/CSS : kpi_card/line_chart/bar_chart/pie_chart/table/list/funnel), `WidgetSection` (grid/row/single + héritage design). `DashboardPage` supporte `WidgetSection` nativement. 173/173 ✅. `__init__.py` v1.2.0.
- **2026-03-26 (s24)** : Business Document Layer v1.1 — `InvoiceDoc` (payment_terms, bank_details, late_payment_clause, purchase_order_ref), `QuoteDoc` (validity_date, acceptance_block signature), `PurchaseOrderDoc` (DeliveryInfo, order_ref, confirmation_block). `render_business_doc()` partagé dans `document_base.py`. `BrandDefinition` + 5 templates factory (`InvoiceTemplate`, `QuoteTemplate`, `PurchaseOrderTemplate`, `TextDocTemplate`, `SheetDocTemplate`) avec `generate_install_script()`. 90/90 tests ✅. Catalog v1.3.0 : 31 entries (24 existants + 7 nouveaux).
- **2026-03-26 (s22)** : Document Objects Layer — `MODULES/document_objects/`. 4 objets (architecture objet-owns-render, sans adapter) : `SheetDoc` (facture/devis/bon de commande/avoir — totaux HT/TVA/TTC auto, layout HTML imprimable), `EmailSignature` (bloc HTML table email-compatible inline styles, logo ou monogramme, CTA, réseaux sociaux, render_full()), `TextDoc` (blocs composables : heading/paragraph/bullet_list/numbered_list/callout/separator/quote/code/footer), `DashboardPage` (sidebar nav + header + stat_cards + TableSection/CardGridSection/FiltersBar). Chaque objet : validate() + render() + test(). Design system intégré (palette, typography) en option. 36/36 tests ✅. Catalog mis à jour : 24 entries (12 endpoints + 8 scenarios + 4 objects). `explore(category="document")` → 4 objects avec class/module/methods.
- **2026-03-26 (s21)** : Fix infra email + site eurkai.com + Stripe. (3) Stripe : compte créé avec nathalie@eurkai.com, clés test (pk_test + sk_test) dans secrets.env. Clés globales pour tous les projets (presence-ia, sublym, etc.) — différenciation par metadata. Webhook secret à créer quand on intégrera le premier endpoint.
- **2026-03-26 (s21)** : Fix infra email + site eurkai.com. (1) Fix email : 2 bugs corrigés — Dovecot namespace inbox=yes manquant dans 10-mail.conf + virtual_mailbox_limit < message_size_limit dans Postfix. Hashes Dovecot resynchronisés avec secrets.env. 4 boîtes opérationnelles (contact/nathalie/info/webmaster@eurkai.com). (2) Site eurkai.com : page d'attente déployée sur VPS, DNS A + www mis à jour via API IONOS (212.227.80.241), SSL Let's Encrypt actif. https://eurkai.com en ligne.
- **2026-03-26 (s20)** : Infrastructure email eurkai.com. Serveur mail (Postfix + Dovecot) installé sur VPS 212.227.80.241. 4 boîtes créées : contact@, nathalie@, info@, webmaster@eurkai.com. Certificat SSL Let's Encrypt (mail.eurkai.com, valide jusqu'au 23/06/2026). DNS configuré : A record mail.eurkai.com, MX → mail.eurkai.com, SPF mis à jour. Ports 25/587/993 débloqués dans le firewall réseau IONOS (My firewall policy). Credentials sauvegardés dans secrets.env. Profil Apple Mail (.mobileconfig) généré sur le bureau. Compte Stripe à créer avec nathalie@eurkai.com.
- **2026-03-24 (s19)** : Fix playground.py — `app.run()` manquant (le serveur démarrait silencieusement sans écouter). Ajout du bloc `if __name__ == "__main__": app.run(host="0.0.0.0", port=PORT)`. Playground opérationnel sur http://localhost:8765. — DA Enforcement Layer — `generate_brand_charter.py`. 5 nouveaux helpers : `_build_spacing_system(ad)` (section_pad density×energy×attitude, grid_gap, title_gap, content_w), `_detect_monochrome(pal)` (saturation avg < 12% → grayscale img filter + faux noir/blanc), `_DECORATOR_FALLBACKS` par attitude, `_get_decorators_graceful(ad)` (charge visual_decorators module ou fallback), `_build_da_css(ad, pal, spacing, decorators, is_mono)` (CSS injection : vars DA, mono imgs, bg par attitude, border language, icon style, typo sharpening, motifs). `_build_rendering_contract()` : `_build_spacing_system()` remplace les dicts inline + `section_label()` closure DA-aware (brutalist=left bar 4px/uppercase 900, editorial=hairline italic, experimental=diamond 45deg, playful=pill badge, product=acc bar 24×2). `_lp_dynamic_page()` : `_da_css` computed + injecté dans tous les renderers via `(css or "") + _da_css`. Testé : 4 attitudes → markers DA présents ✅.
- **2026-03-23 (s18)** : playground.py — pipeline complet. `_run_pipeline()` upgradé : vi → palette → visual_coherence_engine (CASE 2) → design_plan (boucle validation max 5, seed mutation ×97) → generate_landing_page(plan.seed). Toggle "Full Pipeline" ON/OFF. Panel métadonnées 4 onglets : Palette (swatches) / Visual Intent / Design Plan (layout_strategy, profile, hero, density, sections) / Coherence (mode + readability + overlay). Header statusbar : seed + archetype + layout + badge pipeline. Playground ouvert sur http://localhost:8765.
- **2026-04-06 (s61)** : Bibliothèque canonique modules UI — ToolPage/AdminPage. 13 modules définis en 4 familles (Affichage métrique / Données / Interaction / Structure) : kpi_grid, chart, card_grid, data_table, activity_log, detail_panel, filter_bar, action_bar, form, tabs, split_workspace, status_banner, empty_state. Pour chaque module : rôle, contenu, densité, priorité visuelle, variantes, 5 états canoniques (empty/minimal/standard/dense/overflow), bornes (min/ideal/max_visible/beyond), responsive structurel (desktop/tablet/mobile — réorganisation info, pas simple réduction), logique section↔module (combinaisons cohérentes + à éviter), 10 règles premium (densité=qualité, espacement informatif, couleur fonctionnelle, typo fait le travail de la couleur, empty_state obligatoire, actions exposées, scroll acceptable/débordement non, transitions invisibles, sidebar blanche, qualité visible sur les cas limites). Pas de code produit — spécification canonique pure.
- **2026-04-04 (s60)** : Recadrage architecture Présence IA × EURKAI. Constat : les pages home/landing générées (index.html, landing.html) ne correspondent pas au contenu réel du site en production. Décision : respecter le process EURKAI complet — seed → CdC → définition des content types → configuration de la structure → pipeline. Les pages ne doivent jamais être créées directement, toujours via `run_presence_ia_*.py`. Prochaine étape : prompt Nathalie → définir les content types et la structure de chaque page à partir du brief Présence IA réel.
- **2026-04-04 (s59)** : ToolPage renderer + Présence IA 3 pages. (1) `_render_tool_page()` — sidebar blanche, logo couleurs, accordéon toggle (tous fermés par défaut), header bleu primaire, KPI cards, tables. `generate_landing_page()` étendu : `tool_sections`, `logo_path`, `home_url`. Nav v1 complète : LEADS(5)/MARKETING(2)/CLOSERS(5 dont Recrutement)/FINANCES(2), liens href vers routes admin réelles. (2) `admin_v2/cockpit.html` — zéro donnée en dur, KPIs à "—", clic section = ouvre+navigue premier enfant. (3) `home/index.html` + `home/landing.html` — vrai contenu Présence IA (offres 500€/3500€/9000€, 6 signaux, secteurs, argumentaire), logo `../src/assets/logo.svg`, fond ville Unsplash sur hero landing avec scrim dégradé. Accordéons admin : toggle complet, tous fermés.
- **2026-04-04 (s58)** : RenderContract ToolPage défini — schéma complet (champs racine + 6 zones + mapping layout→zones), 13 règles absolues, validator pré/post-render, renderer = traducteur pur, 6 anti-patterns.
- **2026-04-04 (s57)** : ToolPage canonical — objet ToolPage défini (task execution page, density=high forcé, layouts restreints split_columns/dashboard_stack/card_matrix, flow = input→action→output, pas de sections éditoriaux).
- **2026-04-04 (s56)** : Architecture pipeline formalisée — 11 milestones avec contrats, méthode standard (resolve_options→select→produce→validate→expose), DNA stoppe à milestone 1 (DesignContext).
- **2026-04-04 (s55)** : Design diversity — layouts 9→20, heroes 7→12, section flows 9→20. 38/38 tests ✅. 37 combos (layout, hero) distincts sur 50 seeds.
- **2026-03-22 (s17)** : Visual Quality Upgrade + Design Playground. (1) `_build_bg_art()` : opacités renforcées (`22`→`44`, `1a`→`33`, `0d`→`1a`, etc.) + 3 nouveaux types `mesh_gradient` (3 radials multicouches), `spotlight` (glow directionnel depuis coin), `gradient_deep` (3-stop linear bg→p→s). Pools mis à jour par attitude (editorial/product/experimental enrichis). (2) `_build_typography()` : product attitude renforcé — high energy `700`→`800` + clamp `3.5→4.5rem`, low energy `600`→`700` + clamp `3→3.2rem`. (3) `playground.py` — interface Flask port 8765 : form brief/name/site_family/seed, pipeline vi→palette→render, split view iframe + swatches + visual intent, boutons Générer/Regénérer/Variation×3. 119/119 tests ✅.
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
- **2026-04-07 (s68)** : TEST/VALIDATION/STABILISATION — `test_full_chain_e2e.py` 3/3 ✅. Fix bug content detection : "articles de blog" retournait `code` au lieu de `content` (modèles User-only non-domaine traités comme génériques dans `_detect_type`). Patch minimal dans `scenario_specs_to_deliverable.py` : si `is_content=True` et aucun modèle domaine (non User/Session/Auth) → retourne "content". CAS1 API factures=code ✓, CAS2 articles=content ✓, CAS3 invalid=failure ✓.
- **2026-04-07 (s67)** : `test_full_chain_e2e.py` — 3/3 ✅ zéro patch. CAS1 SaaS/code : 8/8 étapes, tous invariants (envelope, transitions, data non vide, github.ready=True). CAS2 blog/content : 8/8 étapes, dtype=code (blog détecté comme SaaS). CAS3 invalid : 7 scénarios échouent proprement. MVP stable, testable, honnête.
- **2026-04-07 (s66)** : `scenario_prod_to_github.py` (3/6 ✅) — 5 étapes : validate/prepare_repo_config/simulate_git_operations/normalize/assemble. repo_name auto (`eurkai-<slug>`), commit_message conventionnel (`feat(code)/docs(document)/assets(media)`), files par type (code:+.gitignore, page:preview→index.html, media:+MEDIA_SPEC.md). Bloquant si `ready_for_github=False`. Chaîne complète : idea→brief→cdc→specs→deliverable→preprod→prod→backup→github.
- **2026-04-07 (s65)** : `scenario_prod_to_backup.py` (4/6 ✅) — 6 étapes : validate/verify_prod/prepare_backup_config/simulate_backup/normalize/assemble. backup_manifest (version/artifacts/source_prod/ready_for_github/restorable), restore_plan par type (code:install+env+smoke_test, page:restore_assets+reconfigure_url, doc:restore_index, content:restore_metadata, media:restore_asset_manifest). Partial si 0 artifacts. Chaîne : idea→brief→cdc→specs→deliverable→preprod→prod→backup.
- **2026-04-07 (s64)** : `scenario_preprod_to_prod.py` (4/6 ✅) — 6 étapes : validate/verify_preprod/prepare_prod_config/simulate_promotion/normalize/assemble. Promotion simulée preprod→prod. release_manifest (version/artifacts/ready_for_backup/ready_for_github), deployment_plan par type (code:install+start, page:cdn, doc:diffusion, content:cms, media:dam), publication_targets par type (code:github+vps+backup, page:github_pages+cdn, etc.). State partiel non-bloquant (retourne "partial" si preprod.ready=False). Chaîne complète : idea→brief→cdc→specs→deliverable→preprod→prod.
- **2026-04-07 (s63)** : Transition INFRA → PRODUIT — Pipeline idée→préprod complet. (1) `agent_validator.py` : testé 6/6 ✅. (2) `agent_brief.py` : idée brute → brief structuré (5/6 ✅) — 7 types projet, 8 domaines, détection déterministe. (3) `scenario_orchestrate.py` v6 : brief + validate intégrés dans la chaîne — non-bloquants, backward compatible. (4) `scenario_idea_to_brief.py` (3/5 ✅). (5) `scenario_brief_to_cdc.py` (2/4 ✅) — 7 sections CDC, templates par type. (6) `scenario_cdc_to_specs.py` (2/4 ✅) — archi, composants, modèles, endpoints API. (7) Output full pipeline JSON sauvé (idea→brief→cdc→specs). (8) `scenario_specs_to_deliverable.py` (3/5 ✅) — routing layer, détection code/page/doc/content/media. (9) `scenario_deliverable_to_preprod.py` (3/5 ✅) — 6 steps, écrit fichiers réels, ast.parse() validation syntaxe. Chaîne complète : idée → preprod. Prochaine : Chantier 3 — ToolPageModuleLibrary.
- **2026-04-06 (s62)** : Chantier 2 complet — `agent_generate_code.py` (6/6 ✅) + `scenario_orchestrate.py` (chaîne complète ✅) + `test_e2e_minimal.py` (4/4 ✅) + `agent_debug_fix.py` (5/6 ✅). Chaîne autonome : input → objet → code → debug_fix.
- **2026-02-10 17:00** : Documentation vision complète, architecture fractale, approche progressive
- **2026-02-10 17:00** : Premier projet test TIP_CALCULATOR lancé avec workflow optimisé
