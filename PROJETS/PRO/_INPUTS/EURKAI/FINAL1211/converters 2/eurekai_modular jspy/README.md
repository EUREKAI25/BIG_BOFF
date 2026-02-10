# EUREKAI Modular

Convertit des scripts JS en architecture modulaire avec manifests et API.

## Structure

```
eurekai_modular/
├── convert.py          # Convertit JS → manifest + backend
├── register.py         # Enregistre manifest → registry (hookAfter)
├── server.py           # Serveur Flask agnostique
├── catalog/
│   ├── manifests/      # Manifests JSON des modules
│   ├── backend/        # Code Python des modules backend
│   ├── store.py        # Store (vecteurs, données)
│   └── registry.json   # Index de tous les modules
└── static/
    ├── eurekai.js      # Client JS unique
    └── demo.html       # Page de démo
```

## Usage

### 1. Convertir un JS

```python
from convert import convert
from register import register

# Convertir
manifest_path, backend_path = convert('mon_script.js')

# Enregistrer (hookAfter)
register(manifest_path)
```

### 2. Lancer le serveur

```bash
pip install flask
python server.py
```

### 3. Utiliser dans une page HTML

```html
<script src="/static/eurekai.js"></script>
<script>
  EUREKAI.init({ apiEndpoint: '/api' }).setToken('mon-token');
  
  // Charger des modules
  await EUREKAI.load(['utils', 'traverse']);
  
  // Appeler des fonctions
  const result = await EUREKAI.call('traverse.getAncestors', { lineage: 'Object:Entity' });
</script>
```

## Route API

```
GET /api/{object}/{centralMethod}/{methodAlias}?vector={id}&token={token}
```

Exemples :
```
GET /api/Traverse/Read/getAncestors?vector={"lineage":"Object:Entity"}&token=xxx
GET /api/Utils/Execute/formatDate?vector=vec_123&token=xxx
```

## Types de modules

### Frontend
- Exécuté localement dans le navigateur
- Code inclus dans le manifest
- Pas d'appel API

### Backend  
- Exécuté sur le serveur Python
- Code dans `catalog/backend/`
- Appel API via fetch

Le type est détecté automatiquement :
- Utilise `Store`, `fetch`, `require` → backend
- Fonction pure sans dépendances → frontend
