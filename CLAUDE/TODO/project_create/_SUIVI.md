# _SUIVI — PROJECT_CREATE

## Objectif
Système multi-agents à rôles étanches pour générer des projets complets à partir d'un brief.
Pipeline : **Brief → Split → Triage → Build → QA → Backlog**

## Statut : 🟢 actif

---

## Historique

### 2026-02-27
- ✅ Pipeline de base validée (runner.py sans appels IA réels)
- ✅ Intégration Anthropic API — chargement `.env` local ou `~/.bigboff/secrets.env`
- ✅ 5 agents chaînés avec contexte passé de l'un à l'autre
- ✅ Enregistrement dans `_PROJETS.md`
- ✅ Fichiers : runner.py, .env.example, _SUIVI.md, readme.md, 5 prompts
- ✅ Fix `lib/cache_get.py` : lookup dans `cache["entries"]` (et non racine du dict)
- ✅ Fix `lib/cache_set.py` : TTL lu depuis `cache["ttl_seconds"]` (et non hardcodé 3600)
- ✅ Feature pipeline : injection automatique de contexte lib/ dans BUILD (`lib_context`)
- ✅ Fix `lib/identify_expired_entries.py` : itère `cache["entries"].items()`
- ✅ Ajout `lib/cache_cleanup.py` : wrapper orchestrant identify + remove
- ✅ Fix parser : plusieurs `## ATOMIC` dans une réponse SPLIT → tous traités (`atomics`)
- ✅ Fix parser : headings `# ATOMIC` (h1) reconnus en plus de `## ATOMIC`
- ✅ Fix parser : `#` strippé des clés → champs `## name:` correctement parsés
- ✅ Fix parser : `flush_current()` ajouté sur `## STEPS` → plus de perte de la dernière ATOMIC
- ✅ Test réel : brief queue FIFO → 5 fonctions en 1 passe
- ✅ Test réel : brief rate limiter → 4 fonctions, retry QA auto sur consume (dépendance inlinée)
- ✅ Feature parser : mode `mixed` (ATOMIC + STEPS dans une même réponse SPLIT)
- ✅ Test réel : mini DB 6 opérations (create, insert, select, update, delete, count) — démo validée
- ✅ Fix lib : filter_rows + project_columns gèrent where_fn=None / cols=None
- ✅ Lib validée : create_table, insert, select, update, delete, count, filter_rows, project_columns
- ✅ MAX_DEPTH supprimé — arrêt sur atomicité, garde-fou à 10 (anti-boucle)
- ✅ project.json — config globale optionnelle injectée dans SPLIT + BUILD
- ✅ CLI : --config pour passer un project.json explicite
- ✅ project.json.example ajouté (stack, conventions, schéma, produits)
- ✅ brief.py : agent conversationnel (une question à la fois, propose des defaults)
- ✅ prompts/agent_brief.md : guide la conversation → produit project.json
- ✅ fix brief.py : boucle input pour éviter message vide (400 API)
- ✅ prompt brief : détecte profil technique/non-tech, adapte le vocabulaire
- ✅ fix brief.py : extract_spec accepte `## SPEC COMPLETE`, `**SPEC COMPLETE**` ou autre (regex assouplie)
- ✅ prompt brief : ⛔ Ne jamais demander "qui développe ?" ni "êtes-vous développeur ?"
- ✅ refactor brief.py : détection JSON sans marqueur (structure "project" suffit), sauvegarde `project.json` + `.history.json`
- ✅ prompt brief : suppression marqueur SPEC COMPLETE — agent produit un bloc JSON pur après validation
- ✅ feature brief : checklist `[Points restants]` injectée dans chaque message user — guide l'agent sans répétition
- ✅ fix brief.py : strip `[Points restants]` et `[OK:]` des réponses agent (affichage propre)
- ✅ validé : 7 échanges, 0 répétition de question, JSON correct (test site photographe)
- ✅ fix runner.py : MAX_DEPTH=2 règle métier — Brief→STEPS(d=1)→ATOMICs(d=2), plus de STEPS dans des STEPS
- ✅ fix agent_split.md : ATOMIC = "livrer du code maintenant" (pas < 50 lignes), préférence ATOMIC, max 4 steps
- ✅ validé : pipeline FastAPI 2 endpoints en ~2min, profondeur respectée
- ✅ fix runner.py : eval_expected avec 3 passes (literal_eval → eval(namespace) → skip)
- ✅ fix runner.py : args eval avec fallback (FastAPI objects → skip comparaison)
- ✅ fix runner.py : parse_qa() — verdict QA respecté, PASS QA accepté même si test_stub KO
- ✅ fix agent_split.md : fonctions réseau → example_expected: "*", objets framework → example_input: ""
- ✅ fix agent_qa.md : erreurs réseau/SMTP/module externe → ## PASS (logique correcte, env limité)
- ✅ feature brief.py : `outputs/<projet>/project.json` + `logs/<projet>.history.json` (répertoires auto-créés)
- ✅ CLI : `--outdir` pour surcharger le répertoire de sortie
- ✅ feature brief : `product_registry.json` — registre vivant des types de produits (auto-enrichi)
- ✅ brief.py : charge le registry → injecte types connus dans prompt → enregistre nouveaux types après spec
- ✅ agent_brief.md : `{registry_context}` placeholder + champ `taxonomy` dans JSON de sortie

---

## Architecture

```
project_create/
├── runner.py          — Pipeline principal (CLI)
├── prompts/           — Prompts système des 5 agents
│   ├── agent_split.md
│   ├── agent_triage.md
│   ├── agent_build.md
│   ├── agent_qa.md
│   └── agent_backlog.md
├── examples/          — Sorties sauvegardées (à venir)
├── .env.example       — Template variables d'env
├── _SUIVI.md          — Ce fichier
└── readme.md          — Description projet
```

## Usage

```bash
# Utilise automatiquement ~/.bigboff/secrets.env
python3 runner.py "Créer une todo app"

# Ou avec .env local
cp .env.example .env  # Remplir ANTHROPIC_API_KEY
python3 runner.py "Créer une API REST"

# Changer de modèle
PROJECT_CREATE_MODEL=claude-sonnet-4-6 python3 runner.py "brief"
```

---

## Prochaines étapes (NEXT)

- [ ] Sauvegarder les sorties dans `examples/` avec horodatage
- [ ] Mode `--save` pour conserver les outputs
- [ ] Loop automatique QA → BUILD en cas de FAIL
- [ ] Intégration EURKAI comme module réutilisable
- [ ] CLI avec `--model`, `--save`, `--dry-run`
