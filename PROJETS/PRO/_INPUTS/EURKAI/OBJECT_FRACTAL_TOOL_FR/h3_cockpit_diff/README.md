# H3 — Cockpit Diff & Validation

Module de visualisation et validation des différences fractales proposées par les SuperTools EUREKAI.

## 🎯 Objectif

Permettre à l'utilisateur de :
1. **Visualiser** les changements proposés par les scénarios SuperTools
2. **Valider manuellement** chaque modification (accept / reject / modify)
3. **Appliquer** les changements validés via les SuperTools appropriés
4. **Tracer** toutes les décisions dans un journal d'audit

## 📁 Structure

```
h3_cockpit_diff/
├── backend/
│   ├── models/           # Dataclasses Pydantic
│   │   ├── enums.py      # Énumérations (Operation, Decision, etc.)
│   │   ├── diff_models.py # Modèles principaux (DiffGlobal, DiffObject, etc.)
│   │   └── __init__.py
│   ├── services/
│   │   ├── interfaces.py  # Protocols pour SuperTools (mockables)
│   │   ├── diff_service.py # Service principal avec logique GEVR
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_models.py      # Tests des dataclasses
│   │   ├── test_diff_service.py # Tests du service
│   │   └── conftest.py
│   └── requirements.txt
│
└── frontend/
    ├── types/
    │   └── diff.ts        # Types TypeScript miroirs des modèles Python
    ├── stores/
    │   ├── diffStore.ts   # Store Pinia pour la gestion d'état
    │   └── diffStore.test.ts
    ├── components/
    │   ├── DiffList.vue           # Liste des changements avec filtres
    │   ├── DiffListItem.vue       # Élément de liste individuel
    │   ├── DiffDetail.vue         # Détail d'un changement
    │   ├── BundleDiffViewer.vue   # Visualisation des bundles modifiés
    │   ├── DecisionControls.vue   # Boutons accept/reject/modify
    │   └── ConfirmationModal.vue  # Modal de confirmation
    └── views/
        └── DiffValidationView.vue # Page principale
```

## 🔧 Backend

### Modèles (Pydantic)

- **DiffGlobal** : Diff complet entre état actuel et état proposé
- **DiffObject** : Diff sur un objet fractal individuel
- **DiffBundle** : Diff sur un bundle (attributes, methods, rules, relations, tags)
- **DiffAuditLog** : Journal d'audit pour traçabilité

### DiffService (Logique GEVR)

```python
# GET : Récupération
diff = await service.get_diff(diff_id)
pending = await service.get_pending_diffs()

# EXECUTE : Calcul de diff
diff = await service.compute_diff(
    current_objects=[...],
    proposed_objects=[...],
    scenario_id="scenario-123"
)

# VALIDATE : Décisions utilisateur
await service.register_decision(diff_id, DecisionRequest(...), user_id)
await service.accept_all_pending(diff_id, user_id)

# RENDER : Application
result = await service.apply_diff(ApplyDiffRequest(
    diff_id=diff_id,
    user_id=user_id,
    dry_run=False
))
```

### Interfaces (Protocols)

Les SuperTools sont abstraits via des protocols pour permettre le mocking :

```python
class SuperCreateProtocol(Protocol):
    async def execute(self, object_type, path, **kwargs) -> SuperToolResult: ...

class SuperUpdateProtocol(Protocol):
    async def execute(self, object_id, **kwargs) -> SuperToolResult: ...

class SuperDeleteProtocol(Protocol):
    async def execute(self, object_id, soft_delete=True) -> SuperToolResult: ...
```

## 🖥️ Frontend

### Store Pinia (diffStore)

```typescript
const store = useDiffStore()

// Chargement
await store.loadDiff(diffId)

// Décisions locales
store.acceptObject(diffObjectId)
store.rejectObject(diffObjectId)
store.modifyObject(diffObjectId, overrides, comment)

// Actions bulk
store.acceptAllPending()
store.rejectAllPending()
store.resetAllDecisions()

// Application
await store.submitDecisions(userId)
const result = await store.applyDiff(userId)
```

### Composants Vue

- **DiffValidationView** : Page principale avec layout split
- **DiffList** : Liste filtrable et groupable
- **DiffDetail** : Détail avec bundles et contrôles de décision
- **ConfirmationModal** : Confirmation avant application

## 🧪 Tests

### Backend (pytest)

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Couverture :
- ✅ Validation Pydantic (cas valides et erreurs)
- ✅ Calcul de diff (création, modification, suppression)
- ✅ Décisions utilisateur (accept, reject, modify)
- ✅ Application via SuperTools mockés
- ✅ Cas d'erreur et sécurité

### Frontend (vitest)

```bash
cd frontend
npm install
npm run test
```

Couverture :
- ✅ État initial du store
- ✅ Décisions locales
- ✅ Filtrage et groupement
- ✅ Communication backend mockée

## 🔒 Garde-fous de sécurité

1. **Aucune écriture directe** : Toutes les mutations passent par les SuperTools injectés
2. **Validation explicite** : Rien n'est appliqué tant que non explicitement accepté
3. **Journalisation** : Chaque décision et application est tracée dans l'audit log
4. **Dry run** : Possibilité de prévisualiser avant application réelle

## 📝 TODO - Intégrations futures

```python
# TODO: Implémenter les SuperTools réels
# TODO: Connecter au FractalRepository réel
# TODO: Intégrer l'authentification utilisateur
# TODO: Ajouter les endpoints API REST
# TODO: Persister les diffs dans une base de données
```

## 📦 API REST (À implémenter)

```
GET    /api/cockpit/diffs              # Liste des diffs pending
GET    /api/cockpit/diffs/{id}         # Détail d'un diff
POST   /api/cockpit/diffs/{id}/preview # Prévisualisation
POST   /api/cockpit/diffs/{id}/decide  # Enregistrer les décisions
POST   /api/cockpit/diffs/{id}/apply   # Appliquer le diff
GET    /api/cockpit/diffs/{id}/log     # Journal d'audit
```
