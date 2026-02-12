# SUBLYM — Quick Start

Guide rapide pour lancer le pipeline de génération images + vidéos.

## Prérequis

### 1. Clés API configurées

Vérifier que `~/.bigboff/secrets.env` contient :
```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
MINIMAX_API_KEY=sk-api-...
FAL_KEY=...  # Optionnel (Flux Kontext)
```

### 2. Environnement Python

```bash
pip install google-genai openai python-dotenv
```

## Lancement rapide

### Pipeline PARALLÈLE (recommandé - 5× plus rapide)

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM
bash run_pipeline_parallel.sh
```

**Résultat :**
- ⏱️ Temps : ~5 minutes
- 💰 Coût : ~2.50€
- 📁 Output : `outputs/YYYYMMDD_HHMMSS/`

### Pipeline SÉQUENTIEL (ancien)

```bash
bash run_pipeline.sh gemini-native
```

**Résultat :**
- ⏱️ Temps : ~25 minutes
- 💰 Coût : ~2.50€
- 📁 Output : `outputs/YYYYMMDD_HHMMSS/`

## Que va-t-il se passer ?

1. **Chargement scénario** : `scenario_v8_20260211_221456.json` (Voyage Maldives)
2. **Photos référence** : 5 photos Mickael chargées
3. **Génération images** :
   - 5 scènes générées en parallèle
   - Validation stricte (ressemblance ≥ 0.80, qualité, dents, regard)
   - Jusqu'à 7 tentatives par scène
   - Temps : ~65s total (parallèle) ou ~5.5 min (séquentiel)
4. **Génération vidéos** :
   - 5 vidéos générées en parallèle depuis images validées
   - Scène 1 = 10s, scènes 2-5 = 6s
   - Temps : ~4 min total (parallèle) ou ~20 min (séquentiel)

## Voir les résultats

```bash
# Dernière exécution
ls -lt outputs/ | head -5

# Ouvrir dossier images
open outputs/20260212_143000/images/

# Ouvrir dossier vidéos
open outputs/20260212_143000/videos/
```

## Tests de validation

### Tester validation image Gemini

```bash
python test_validation_gemini.py
```

Affiche les scores de ressemblance, qualité, dents, regard.

### Voir prompt complet généré

```bash
python test_prompt_generation.py
```

Affiche le prompt v8 avec toutes les règles critiques.

## Troubleshooting

### "GEMINI_API_KEY manquant"

```bash
# Vérifier le symlink .env
ls -la .env
# Doit pointer vers ~/.bigboff/secrets.env

# Ajouter la clé si manquante
echo 'GEMINI_API_KEY=AIza...' >> ~/.bigboff/secrets.env
```

### "Image validation échoue systématiquement"

- Ressemblance < 0.80 → Normal, jusqu'à 7 tentatives
- Dents visibles → Normal, régénération automatique
- Si échec après 7 tentatives → Image conservée pour analyse

### "MiniMax timeout"

- Timeout augmenté à 900s (15 min)
- Certaines vidéos peuvent prendre plus longtemps
- Pipeline continue même si 1-2 vidéos échouent

## Architecture pipeline

```
Scénario v8 (JSON)
    ↓
┌───────────────────────────────────┐
│  IMAGES (Gemini 3 Pro)            │
│  - 5 scènes en PARALLÈLE          │
│  - 5 photos référence             │
│  - Validation stricte             │
│  - 7 tentatives max               │
│  → ~65s / ~1.00€                  │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│  VIDÉOS (MiniMax)                 │
│  - 5 scènes en PARALLÈLE          │
│  - 10s + 6s×4                     │
│  - Timeout 900s                   │
│  → ~4 min / ~1.53€                │
└───────────────────────────────────┘
    ↓
outputs/YYYYMMDD_HHMMSS/
    ├── images/  (5 PNG validées)
    └── videos/  (5 MP4)
```

## Décisions techniques

### Pourquoi Gemini 3 Pro (0.18€) vs Flux (0.04€) ?

- ✅ Ressemblance garantie : 0.90 (vs variable avec Flux)
- ✅ 5 photos référence supportées
- ✅ Validation stricte réussie du 1er coup
- ❌ +350% coût mais qualité professionnelle

### Pourquoi parallélisation ?

- ✅ Gain temps : 5× plus rapide (5 min vs 25 min)
- ✅ Pas de surcoût (même nb d'API calls)
- ✅ 5 workers = 5 scènes en même temps

## Prochaines étapes

1. 🚀 Lancer pipeline complet : `bash run_pipeline_parallel.sh`
2. ✅ Valider résultats (5 images + 5 vidéos)
3. 🔗 Connecter frontend SUBLYM_APP_PUB
4. 📊 Monitoring coût/temps/qualité

---

**Documentation complète** : Voir `_SUIVI.md`
