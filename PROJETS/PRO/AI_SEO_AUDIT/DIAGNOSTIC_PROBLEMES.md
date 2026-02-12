# Diagnostic des problèmes AI_SEO_AUDIT

**Date** : 2026-02-12
**Statut MVP** : ✅ Fonctionnel mais 2 problèmes critiques détectés

---

## ❌ Problème 1 : Résultats de l'IA en anglais

### Localisation
- **Fichier** : `src/core/interface/ai_provider.py`
- **Lignes** : 94-96

### Cause
Le système prompt envoyé à OpenAI est hardcodé en anglais :

```python
"content": "You are a helpful assistant providing recommendations for local businesses. Always provide specific company names when recommending businesses."
```

De plus, dans `src/orchestrator/agents/audit_agent.py` (lignes 97-101), le prompt utilisateur est aussi en anglais :

```python
prompt = f"""User is looking for recommendations. Please provide a helpful, structured response.

Query: {query}

Please list your top recommendations in order of preference."""
```

### Impact
- Les réponses de ChatGPT sont en anglais
- Même si l'utilisateur a spécifié `language="fr"`, cette information n'est jamais utilisée dans les prompts
- Résultats incompréhensibles pour un utilisateur français

---

## ❌ Problème 2 : Descriptions des gaps et recommendations peu claires

### Localisation
- **Fichier** : `src/orchestrator/agents/analyze_agent.py` (lignes 124-165)
- **Fichier** : `src/orchestrator/agents/generate_agent.py` (tout le fichier)

### Causes

1. **Dans analyze_agent.py** : Les descriptions des gaps sont génériques et en anglais/franglais :
   ```python
   description=f"Company mentioned in only {mentioned_count}/{total_queries} queries ({mention_rate*100:.0f}%)"
   # ❌ Mélange anglais/français, peu explicite
   ```

2. **Dans generate_agent.py** : Les recommandations utilisent des placeholders non remplis :
   ```python
   "content": f"{company} est reconnu pour [expertise principale]. "
              f"Nous offrons [services/produits] à [audience cible]."
   # ❌ [expertise principale] reste tel quel dans le résultat
   ```

3. **Aucune traduction** : Tout est en français hardcodé, même si l'audit demande une autre langue

### Impact
- Gaps affichés avec des textes incomplets ou mal formatés
- Recommendations avec des placeholders visibles ([expertise principale], [X années], etc.)
- Impossible de comprendre ce qu'il faut faire concrètement

---

## 📊 Ce qui fonctionne bien

✅ Architecture fractale (Orchestrator + 3 Agents)
✅ Base de données et modèles
✅ Routes API et endpoints
✅ Templates HTML/CSS/JS
✅ Logique de scoring et d'analyse
✅ Structure EURKAI respectée

---

## 🔧 Solutions proposées

### Solution 1 : Gestion multilingue des prompts

**Créer un module de prompts internationalisés** :

1. Créer `src/core/config/prompts.py` avec des dictionnaires par langue :
   ```python
   SYSTEM_PROMPTS = {
       "fr": "Tu es un assistant qui recommande des entreprises locales...",
       "en": "You are a helpful assistant recommending local businesses...",
   }
   ```

2. Modifier `ai_provider.py` pour accepter un paramètre `language` et utiliser le bon prompt

3. Passer la langue depuis `audit_service.py` → `orchestrator` → `audit_agent` → `ai_provider`

### Solution 2 : Descriptions claires et traduites des gaps

1. Créer des templates de descriptions par langue dans `analyze_agent.py`
2. Remplacer les textes génériques par des descriptions exploitables
3. Exemple :
   ```python
   # ❌ Avant
   "Company mentioned in only 2/3 queries (66%)"

   # ✅ Après
   "Votre entreprise n'apparaît que dans 2 requêtes sur 3. Cela signifie que l'IA ne vous recommande pas assez souvent. Vos concurrents sont plus visibles."
   ```

### Solution 3 : Génération intelligente des recommendations

Au lieu de placeholders statiques, utiliser l'analyse pour générer du contenu pertinent :

1. Analyser le secteur pour déduire l'expertise (restaurant → gastronomie, etc.)
2. Utiliser les données de l'audit (concurrents, gaps) pour personnaliser
3. Générer du contenu réel au lieu de placeholders

Exemple :
```python
# ❌ Avant
f"{company} est reconnu pour [expertise principale]"

# ✅ Après
f"{company} peut se démarquer en mettant en avant sa cuisine {sector_expertise[sector]}"
```

---

## ⚡ Plan de correction

### Priorité 1 (Critique) - 30 min
- [ ] Ajouter gestion multilingue dans `ai_provider.py`
- [ ] Créer module `prompts.py` avec prompts FR/EN
- [ ] Passer paramètre `language` dans toute la chaîne

### Priorité 2 (Important) - 20 min
- [ ] Réécrire descriptions des gaps en français clair
- [ ] Ajouter explications compréhensibles ("Pourquoi c'est important", "Ce que ça implique")

### Priorité 3 (Nice-to-have) - 30 min
- [ ] Remplacer placeholders par contenu généré intelligemment
- [ ] Utiliser les données de l'analyse pour personnaliser

**Temps total estimé** : 1h20

---

## 📝 Notes

- Le code actuel est excellent structurellement
- Les problèmes sont uniquement dans le contenu textuel/prompts
- Une fois corrigé, le MVP sera 100% fonctionnel et prêt pour demo
