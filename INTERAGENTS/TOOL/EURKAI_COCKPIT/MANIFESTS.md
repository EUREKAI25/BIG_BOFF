# EURKAI_COCKPIT — MANIFESTS (ModuleManifest v1)

**Version** : 1.0.0  
**Date** : 2025-01-12  
**Statut** : VERROUILLÉ

---

## 1. Objectif

Définir le format standard pour déclarer les modules plug-and-play,
permettant la vérification de compatibilité inputs/outputs.

---

## 2. Structure ModuleManifest v1

### 2.1 Schéma JSON

```json
{
  "$schema": "https://eurkai.local/schemas/manifest-v1.json",
  "name": "string (unique, kebab-case)",
  "version": "string (semver)",
  "description": "string (optionnel)",
  "author": "string (optionnel)",
  "inputs": [
    {
      "name": "string (snake_case)",
      "type": "string | number | boolean | object | array | file",
      "required": true | false,
      "description": "string (optionnel)",
      "default": "any (optionnel, si required=false)"
    }
  ],
  "outputs": [
    {
      "name": "string (snake_case)",
      "type": "string | number | boolean | object | array | file",
      "description": "string (optionnel)"
    }
  ],
  "constraints": {
    "min_memory_mb": "number (optionnel)",
    "requires_gpu": "boolean (optionnel)",
    "timeout_seconds": "number (optionnel)"
  },
  "dependencies": [
    {
      "module": "string (nom du module)",
      "version": "string (semver range, ex: ^1.0.0)",
      "note": "string (déclaratif seulement, non résolu)"
    }
  ],
  "tags": ["string", ...]
}
```

### 2.2 Types supportés v1

| Type | Description | Exemple |
|------|-------------|--------|
| `string` | Texte UTF-8 | `"hello"` |
| `number` | Entier ou flottant | `42`, `3.14` |
| `boolean` | Vrai/faux | `true`, `false` |
| `object` | JSON object | `{"key": "value"}` |
| `array` | JSON array | `[1, 2, 3]` |
| `file` | Chemin fichier local | `"/path/to/file.txt"` |

> ⚠️ Pas de JSON Schema complet en v1. Typage simple uniquement.

---

## 3. Exemples

### 3.1 Module simple — text-summarizer

```json
{
  "$schema": "https://eurkai.local/schemas/manifest-v1.json",
  "name": "text-summarizer",
  "version": "1.0.0",
  "description": "Résume un texte long en points clés",
  "author": "eurkai-team",
  "inputs": [
    {
      "name": "text",
      "type": "string",
      "required": true,
      "description": "Texte à résumer"
    },
    {
      "name": "max_points",
      "type": "number",
      "required": false,
      "default": 5,
      "description": "Nombre max de points"
    }
  ],
  "outputs": [
    {
      "name": "summary",
      "type": "array",
      "description": "Liste de points clés"
    }
  ],
  "constraints": {
    "timeout_seconds": 30
  },
  "dependencies": [],
  "tags": ["nlp", "summarization"]
}
```

### 3.2 Module avec dépendance déclarative — report-generator

```json
{
  "$schema": "https://eurkai.local/schemas/manifest-v1.json",
  "name": "report-generator",
  "version": "1.0.0",
  "description": "Génère un rapport PDF à partir de données",
  "inputs": [
    {
      "name": "data",
      "type": "object",
      "required": true
    },
    {
      "name": "template",
      "type": "file",
      "required": false,
      "default": "default.html"
    }
  ],
  "outputs": [
    {
      "name": "pdf_path",
      "type": "file"
    }
  ],
  "constraints": {
    "min_memory_mb": 256
  },
  "dependencies": [
    {
      "module": "text-summarizer",
      "version": "^1.0.0",
      "note": "Utilisé pour résumer les sections longues"
    }
  ],
  "tags": ["reporting", "pdf"]
}
```

---

## 4. Compatibilité Inputs/Outputs

### 4.1 Règle de compatibilité

Deux modules sont **compatibles** si :

```
Module A.outputs ∩ Module B.inputs ≠ ∅
```

Plus précisément, pour chaque output de A :
- Il existe un input de B avec le **même type**
- Les noms peuvent différer (mapping manuel)

### 4.2 Algorithme de vérification

```python
def check_compatibility(module_a: Manifest, module_b: Manifest) -> dict:
    """
    Vérifie si les outputs de A peuvent alimenter les inputs de B.
    Retourne les mappings possibles.
    """
    mappings = []
    
    for output in module_a["outputs"]:
        for input_ in module_b["inputs"]:
            if output["type"] == input_["type"]:
                mappings.append({
                    "from": f"{module_a['name']}.{output['name']}",
                    "to": f"{module_b['name']}.{input_['name']}",
                    "type": output["type"]
                })
    
    # Vérifier que tous les inputs required de B sont satisfaits
    required_inputs = [i for i in module_b["inputs"] if i["required"]]
    satisfied = set()
    
    for m in mappings:
        input_name = m["to"].split(".")[1]
        satisfied.add(input_name)
    
    missing = [i["name"] for i in required_inputs if i["name"] not in satisfied]
    
    return {
        "compatible": len(missing) == 0,
        "mappings": mappings,
        "missing_required": missing
    }
```

### 4.3 API Endpoint

```http
GET /api/modules/compatible?from=text-summarizer&to=report-generator
```

Réponse :

```json
{
  "success": true,
  "data": {
    "compatible": false,
    "mappings": [],
    "missing_required": ["data"],
    "suggestion": "text-summarizer outputs 'array', report-generator needs 'object' for 'data'"
  }
}
```

---

## 5. Registry (stockage)

### 5.1 Table SQLite

Voir `SPEC_V1.md` — table `module_manifests`.

### 5.2 Opérations

| Action | Endpoint | Validation |
|--------|----------|------------|
| Register | POST /api/modules | JSON Schema, nom unique |
| Update | POST /api/modules (même nom, version >) | SemVer supérieur requis |
| List | GET /api/modules | — |
| Delete | DELETE /api/modules/{id} | — |

### 5.3 Règle de versioning modules

- Même nom + même version = **rejet** (conflit)
- Même nom + version supérieure = **mise à jour**
- Breaking change dans i/o = **MAJOR bump obligatoire**

---

## 6. Limitations v1

| Limitation | Raison | Évolution future |
|------------|--------|------------------|
| Pas de JSON Schema complet | Simplicité MVP | v2 possible |
| Pas de résolution auto dépendances | Complexité | Orchestrateur futur |
| Types simples uniquement | MVP | Unions, generics v2 |
| Pas de marketplace | Local-first | Post-MVP |

---

## 7. Validation Manifest

### 7.1 Règles de validation

```python
VALIDATION_RULES = {
    "name": {
        "pattern": r"^[a-z][a-z0-9-]*[a-z0-9]$",
        "min_length": 3,
        "max_length": 50
    },
    "version": {
        "pattern": r"^\d+\.\d+\.\d+$"  # semver strict
    },
    "inputs[].name": {
        "pattern": r"^[a-z][a-z0-9_]*$"
    },
    "inputs[].type": {
        "enum": ["string", "number", "boolean", "object", "array", "file"]
    }
}
```

### 7.2 Erreurs possibles

| Code | Message |
|------|--------|
| `MANIFEST_INVALID_NAME` | Nom invalide (format kebab-case) |
| `MANIFEST_INVALID_VERSION` | Version non semver |
| `MANIFEST_DUPLICATE` | Nom+version déjà existant |
| `MANIFEST_INVALID_TYPE` | Type input/output non supporté |

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-01-12 | Initial manifest spec |
