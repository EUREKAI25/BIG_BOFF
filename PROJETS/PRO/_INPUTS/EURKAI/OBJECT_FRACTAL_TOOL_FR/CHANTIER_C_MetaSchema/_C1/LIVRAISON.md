# LIVRAISON C1/1 — Lineages Assistés

## ✅ CHECKLIST DE VALIDATION

- [x] Pour tout objet sans parent clair, le système peut fournir zéro, une ou plusieurs suggestions
- [x] Les suggestions sont accompagnées de scores et de raisons
- [x] Aucun changement n'est fait à la fractale sans validation explicite
- [x] Plusieurs exemples + cas de test fournis pour vérifier le comportement

---

## 📦 Fichiers Livrés

| Fichier | Description |
|---------|-------------|
| `lineage_suggester.py` | Module principal avec stratégies de scoring |
| `test_examples.py` | Tests et exemples exécutables |
| `LineageSuggesterPanel.jsx` | Composant React pour intégration cockpit |

---

## 🎯 Stratégie de Suggestion

### Approche Multi-Critères

Le système utilise 4 stratégies pondérées :

```
Pattern Matching     40%  →  Correspondance des segments de lineage
Similarité Lexicale  25%  →  Distance sur les noms
Proximité Structure  20%  →  Profondeur dans l'arbre
Cohérence Type       15%  →  Compatibilité IVC×DRO
```

### Algorithme

1. Pour un objet orphelin, parcourir tous les candidats du store
2. Calculer un score par stratégie (0-1)
3. Combiner avec pondération
4. Filtrer par seuil minimum (default: 0.3)
5. Retourner les N meilleurs triés par score

---

## 📊 Structure de Retour

```python
{
    "parentId": "core_agent_llm",      # ID du parent suggéré
    "score": 0.675,                     # Score combiné (0-1)
    "scorePercent": 67.5,               # Score en pourcentage
    "reason": "Parent direct: Core:Agent:LLM → Core:Agent:LLM:GPT",
    "details": {
        "pattern": 1.0,
        "lexical": 0.0,
        "structural": 1.0,
        "type_coherence": 0.5
    }
}
```

---

## 🧪 Résultats des Tests

```
✅ Cas 1: Parent évident      → LLM détecté comme parent de GPT (67.5%)
✅ Cas 2: Parents ambigus     → Core suggéré pour APIAgent (71.7%)
✅ Cas 3: Aucun parent        → Aucune suggestion >50% pour objet exotique
✅ Cas 4: Nouveau projet      → Project détecté pour Portfolio (78.4%)
✅ Cas 5: Règle hiérarchique  → Validation détecté avec cohérence D→R
✅ Batch suggestions          → Traitement en lot fonctionnel

Total: 6/6 tests passés
```

---

## 🔌 API Principale

```python
from lineage_suggester import suggest_parents, FractalObject

# Créer le store
store = {
    "core": FractalObject(id="core", name="Core", lineage="Core", ...),
    "orphan": FractalObject(id="orphan", name="GPT", lineage="Core:Agent:LLM:GPT", parent_id=None, ...)
}

# Obtenir suggestions
suggestions = suggest_parents("orphan", store)
# → [{ parentId: "core_agent_llm", score: 0.675, reason: "..." }, ...]
```

---

## 🚀 Extensibilité

Le système est conçu pour être enrichi :

1. **Nouvelles stratégies** : Hériter de `SuggestionStrategy`
2. **Ajustement poids** : Modifier `weight` de chaque stratégie
3. **ERK** : Ajouter une stratégie basée sur l'évaluation de règles
4. **IA** : Intégrer embeddings pour similarité sémantique
5. **Stats** : Apprendre des choix utilisateurs passés

---

## 📝 Notes d'Implémentation

- Le parent direct (1 niveau au-dessus avec segments matchant) est fortement favorisé
- Les cycles d'héritage sont détectés et exclus
- Les seuils et limites sont configurables
- Le batch processing permet de traiter tous les orphelins d'un coup
