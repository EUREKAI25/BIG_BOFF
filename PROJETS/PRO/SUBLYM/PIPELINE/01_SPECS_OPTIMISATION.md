# SPECS — Optimisation Pipeline v7 → v8

> Documentation technique de l'optimisation du pipeline de génération de scénarios

**Créé** : 2026-02-10
**Auteur** : Claude Opus 4.6 + Nathalie
**Statut** : 🟡 en développement

---

## Problème

Le pipeline_v7 fonctionne parfaitement (cohérence 100%) mais coûte trop cher en temps et argent :

- **168 appels LLM** pour un scénario de 5 scènes
- **10-15 minutes** de génération
- **~2.70€** par scénario (GPT-4o)

**Cause** : Triple validation (V1, V2, V3) pour chaque question + itération par scène

### Analyse détaillée v7

**Structure actuelle** :
```
Chaque question = 1 génération + 3 validations = 4 appels LLM

11 étapes × questions multiples × 4 appels :
1. Blocages + affirmations : 2 × 4 = 8 appels
2. Pitch global : 1 × 4 = 4 appels
3. Découpage : 1 × 4 = 4 appels
4. Paramètres (5 scènes) : 5 × 4 = 20 appels
5. Keyframes (5 scènes) : 5 × 4 = 20 appels
6. Pitchs individuels (5 scènes) : 5 × 4 = 20 appels
7. Attitudes (5 scènes) : 5 × 4 = 20 appels
8. Palettes (1 + 5) : 6 × 4 = 24 appels
9. Cadrages (5 scènes) : 5 × 4 = 20 appels
10. Rythme : 1 × 4 = 4 appels
11. Prompts finaux (5 + 1) : 6 × 4 = 24 appels

TOTAL : 168 appels
```

---

## Solution : Approche Batch (v8)

**Principe** : Consolider les questions par scène en un seul appel LLM

### Architecture v8 (9 appels)

```
1. Blocages + Pitch global (1 appel)
   → Génère blocages émotionnels + affirmations + pitch narratif global

2. Découpage 5 scènes (1 appel)
   → Découpe en 5 scènes avec transitions

3. Paramètres TOUTES scènes (1 appel)
   → Lieu/moment/action/tenues pour les 5 scènes d'un coup

4. Keyframes TOUTES scènes (1 appel)
   → Start/end pour chaque scène (5 × 2 keyframes)

5. Pitchs + Attitudes TOUTES scènes (1 appel)
   → Narratif + mouvements pour les 5 scènes

6. Palettes globale + par scène (1 appel)
   → 1 palette globale + 5 déclinaisons

7. Cadrages TOUTES scènes (1 appel)
   → Plan/mouvement/angle justifiés pour les 5 scènes

8. Rythme (1 appel)
   → Répartition durées avec justifications

9. Prompts finaux TOUTES scènes (1 appel)
   → 5 prompts vidéo + 1 prompt audio
```

### Gains attendus

| Métrique | v7 | v8 | Amélioration |
|---|---|---|---|
| Appels LLM | 168 | 9 | **-95%** |
| Temps | 10-15min | 1-2min | **-83%** |
| Coût (GPT-4o) | ~2.70€ | ~0.15€ | **-94%** |
| Coût (GPT-4o-mini) | ~0.08€ | ~0.005€ | **-94%** |
| Qualité | 100% | À valider | TBD |

---

## Stratégie de mise en œuvre

### 1. Schémas JSON ultra-stricts

**Avant (v7)** :
```python
system = "Réponds avec un JSON. SCHÉMA: {...}"
```

**Après (v8)** :
```python
from pydantic import BaseModel, Field, validator

class SceneParams(BaseModel):
    scene_id: int = Field(..., ge=1, le=10)
    lieu_precis: str = Field(..., min_length=10, max_length=200)
    moment: str = Field(..., pattern=r"(matin|midi|après-midi|soir|nuit)")
    action: str = Field(..., min_length=20, max_length=300)
    tenue_protagoniste: str = Field(..., min_length=10)
    tenue_partenaire: str = Field(..., min_length=10)

    @validator('moment')
    def validate_moment(cls, v):
        valid = ["matin", "midi", "après-midi", "soir", "nuit"]
        if v.lower() not in valid:
            raise ValueError(f"Moment doit être : {valid}")
        return v.lower()

class AllScenesParams(BaseModel):
    scenes: List[SceneParams]
    metadata: dict
```

### 2. Few-shot examples dans les prompts

**Template prompt batch** :
```python
system_prompt = f"""
{PRODUCTION_RULES}

EXEMPLE DE RÉPONSE ATTENDUE :
{{
    "scenes": [
        {{
            "scene_id": 1,
            "lieu_precis": "Terrasse d'un café parisien, table d'angle vue sur rue pavée",
            "moment": "après-midi",
            "action": "Protagoniste lit un livre, regard distrait vers la rue, sourire léger",
            "tenue_protagoniste": "Robe d'été légère couleur crème, sandales dorées",
            "tenue_partenaire": "Chemise lin blanc, jean délavé, chaussures bateau"
        }},
        {{
            "scene_id": 2,
            "lieu_precis": "Pont des Arts, côté rive gauche, milieu du pont",
            "moment": "soir",
            "action": "Marche côte à côte, échange de regards complices, main qui frôle main",
            "tenue_protagoniste": "Même tenue (continuité temporelle)",
            "tenue_partenaire": "Même tenue (continuité temporelle)"
        }}
    ],
    "metadata": {{
        "coherence_check": "Tenues cohérentes entre scènes 1-2 (même journée)",
        "transitions": ["Café → Pont : déplacement logique dans Paris"]
    }}
}}

GÉNÈRE maintenant les paramètres pour les {nb_scenes} scènes du rêve.
CONTEXTE :
{context}

SCÈNES À PARAMÉTRER :
{json.dumps(decoupage, indent=2, ensure_ascii=False)}
"""
```

### 3. Temperature basse pour cohérence

```python
# v7 : temperature=0.7 (créatif)
# v8 : temperature=0.3 (cohérent)

response = llm._call(system, user, temp=0.3)
```

### 4. Validation + Retry intelligent

```python
def _ask_batch(self, step: str, prompt: str, schema: Type[BaseModel], max_retries: int = 2):
    """Question batch avec validation Pydantic."""
    for attempt in range(max_retries):
        try:
            response = self.llm._call(system, user, temp=0.3)

            # Validation Pydantic
            validated = schema(**response)

            self.audit.log(f"✅ Validation réussie (tentative {attempt+1})")
            return validated.dict()

        except ValidationError as e:
            self.audit.log(f"❌ Validation échouée : {e}")

            if attempt < max_retries - 1:
                # Retry avec feedback
                user += f"\n\nERREURS DÉTECTÉES:\n{e}\nCORRIGE et régénère."
            else:
                raise
```

### 5. Contexte cumulatif

```python
def _build_context(self) -> str:
    """Construit le contexte cumulatif pour chaque étape."""
    ctx = f"RÊVE: {self.v6['dream']}\n\n"

    if self.scenario.get("blocages_emotionnels"):
        ctx += f"BLOCAGES: {json.dumps(self.scenario['blocages_emotionnels'])}\n\n"

    if self.scenario.get("pitch_global"):
        ctx += f"PITCH: {self.scenario['pitch_global']}\n\n"

    if self.scenario.get("decoupage"):
        ctx += f"SCÈNES:\n{json.dumps(self.scenario['decoupage'], indent=2)}\n\n"

    if self.scenario.get("parametres_scenes"):
        ctx += f"PARAMÈTRES:\n{json.dumps(self.scenario['parametres_scenes'], indent=2)}\n\n"

    return ctx
```

---

## Risques et mitigations

### Risque 1 : Perte de qualité (hallucinations)
**Mitigation** :
- Schémas Pydantic stricts (validation structurelle)
- Few-shot examples (format exact attendu)
- Temperature basse (0.3 au lieu de 0.7)
- PRODUCTION_RULES injectées dans CHAQUE prompt

### Risque 2 : Incohérence entre scènes
**Mitigation** :
- Contexte cumulatif (chaque étape voit les précédentes)
- Metadata de cohérence dans les réponses
- Validation croisée (vérifier tenues constantes, transitions logiques)

### Risque 3 : Schéma trop complexe (timeout)
**Mitigation** :
- max_tokens=8000 (au lieu de 4000)
- Timeout 180s (au lieu de 120s)
- Retry automatique si timeout

### Risque 4 : Coût caché (retries multiples)
**Mitigation** :
- max_retries=2 (pas plus)
- Logging détaillé (audit des échecs)
- Fallback v7 si v8 échoue systématiquement

---

## Plan de tests

### Test 1 : Validation structurelle
```bash
pytest tests/test_schemas.py -v
# Vérifie que tous les schémas Pydantic sont valides
```

### Test 2 : Comparaison v7 vs v8
```bash
python tests/compare_v7_v8.py session.json
# Génère le même rêve avec v7 et v8
# Compare : qualité, cohérence, coût, temps
```

### Test 3 : Stress test (10 rêves variés)
```bash
python tests/stress_test.py dreams_dataset.json
# 10 rêves différents (solo, couple, voyage, carrière, etc.)
# Métriques : taux de succès, coût moyen, temps moyen
```

### Critères de validation

| Critère | Seuil acceptable | Seuil optimal |
|---|---|---|
| Taux de succès | > 80% | > 95% |
| Coût moyen | < 0.30€ | < 0.15€ |
| Temps moyen | < 3min | < 2min |
| Cohérence visuelle | > 70% | > 90% |
| Respect PRODUCTION_RULES | > 85% | > 95% |

---

## Prochaines étapes

1. [ ] Implémenter pipeline_v8_batch.py (classe ScenarioGeneratorBatch)
2. [ ] Créer schémas Pydantic (src/schemas.py)
3. [ ] Créer tests unitaires (tests/test_schemas.py)
4. [ ] Test comparatif v7 vs v8 sur 1 rêve
5. [ ] Ajustement prompts si qualité insuffisante
6. [ ] Stress test 10 rêves
7. [ ] Documentation finale + merge en production

---

## Annexe : Dépendances séquentielles

**Dépendances strictes respectées dans v8** :
```
Blocages/Pitch (parallèles, pas de dépendance mutuelle)
    ↓
Découpage (dépend du pitch)
    ↓
Paramètres (dépend du découpage)
    ↓
Keyframes (dépend des paramètres)
    ↓
Pitchs + Attitudes (dépendent des keyframes)
    ↓  ↓  ↓
Palettes  Cadrages  (dépendent des paramètres)
    ↓  ↓  ↓
Rythme (dépend du découpage)
    ↓
Prompts finaux (dépend de TOUT)
```

**Optimisation future possible** : Paralléliser Palettes + Cadrages (indépendants) → **7 appels au lieu de 9**
