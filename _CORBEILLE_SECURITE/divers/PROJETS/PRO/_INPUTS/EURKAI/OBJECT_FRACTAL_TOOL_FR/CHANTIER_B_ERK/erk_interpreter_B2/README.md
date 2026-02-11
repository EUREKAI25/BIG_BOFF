# ERK Interpreter - EUREKAI B1/1

**Interpréteur ERK Minimal** pour le système EUREKAI.

## ✅ Checklist de Validation B1/1

- [x] Une règle ERK simple associée à un objet peut être : chargée → parsée → évaluée → retourner un résultat structuré
- [x] La console permet d'appeler `ERK.eval(objectId, ruleName, context?)` et d'afficher un retour compréhensible
- [x] En cas de règle invalide, un message d'erreur clair est produit (sans planter le système)
- [x] L'interpréteur est clairement conçu comme **extensible** pour B2/2
- [x] Plusieurs **exemples de règles + 56 cas de test** validant le comportement

---

## Architecture

```
erk/
├── __init__.py          # API publique: ERK.eval(), ERK.parse()
├── ast_nodes.py         # Nœuds AST (Literal, Binary, Method, Rule...)
├── lexer.py             # Tokenization des règles ERK
├── parser.py            # Construction de l'AST (grammaire LL(1))
├── evaluator.py         # Évaluation de l'AST dans un contexte
├── errors.py            # Exceptions ERK typées
├── console.py           # Intégration console Cockpit
├── demo.py              # Script de démonstration
└── tests/
    └── test_erk.py      # 56 tests complets
```

### Responsabilités des modules

| Module | Responsabilité |
|--------|----------------|
| `lexer.py` | Tokenize le texte ERK en tokens typés (AND, OR, ==, identifiants...) |
| `parser.py` | Construit l'AST selon la grammaire ERK |
| `evaluator.py` | Évalue l'AST dans un contexte (this, objects, lineages) |
| `console.py` | Interface pour le Cockpit (ERK.eval, ERK.parse, etc.) |
| `errors.py` | Exceptions typées avec contexte (ligne, colonne, détails) |

---

## Syntaxe ERK (V1)

### Structure d'une règle

```
action: expression
```

### Actions supportées

| Action | Sémantique |
|--------|------------|
| `enable` | Active une fonctionnalité si `true` |
| `disable` | Désactive une fonctionnalité si `true` |
| `allow` | Autorise une action si `true` |
| `deny` | Refuse une action si `true` (résultat inversé) |
| `require` | Exige une condition (erreur si `false`) |
| `validate` | Valide une contrainte |
| `check` | Vérifie une condition |

### Expressions

```
# Littéraux
true, false, null
"string", 'string'
42, 3.14

# Références
this                          # Objet courant
this.property                 # Accès membre
this.nested.deep.value        # Accès imbriqué

# Opérateurs logiques
expr AND expr
expr OR expr
NOT expr

# Comparaisons
a == b    a != b
a > b     a >= b
a < b     a <= b

# Appels de méthodes
this.flags.contains("value")
this.config.has("key")
this.name.startsWith("prefix")

# Tableaux
[1, 2, 3]
["a", "b", "c"]
```

### Méthodes built-in

| Méthode | Description |
|---------|-------------|
| `contains(value)` | Vérifie si contient la valeur |
| `has(key)` | Vérifie si la clé existe |
| `isEmpty()` | Vérifie si vide |
| `isNotEmpty()` | Vérifie si non vide |
| `length()` | Retourne la longueur |
| `startsWith(prefix)` | Vérifie le préfixe |
| `endsWith(suffix)` | Vérifie le suffixe |
| `get(key, default?)` | Récupère une valeur avec défaut |
| `hasFlag(name)` | Vérifie un flag dans `.flags` |
| `inLineage(name)` | Vérifie l'appartenance à un lineage |

---

## Exemples de règles ERK

```python
# Vérification de flags
enable: this.flags.contains("prompt_enabled")

# Type et priorité
allow: this.type == "Agent" AND this.priority == "natural"

# Refus conditionnel
deny: this.status == "suspended" OR this.credits <= 0

# Configuration requise
require: this.config.has("api_key") AND this.config.api_key.isNotEmpty()

# Autorisation complexe
allow: (this.role == "admin" OR this.permissions.contains("write")) AND this.verified == true
```

---

## Usage Console

### Configuration avec un store

```python
from erk import ERK, ERKConsole, StoreAdapter

# Créer le store
store = StoreAdapter()
store.objects = {
    "agent_001": {"id": "agent_001", "status": "active", "credits": 100}
}
store.rules = {
    "agent_001": {
        "can_execute": "allow: this.status == 'active' AND this.credits > 0"
    }
}

# Configurer ERK
ERK.configure(store)

# Évaluer
result = ERK.eval("agent_001", "can_execute")
# {'ok': True, 'rule': 'can_execute', 'action': 'allow', ...}
```

### Évaluation rapide (sans store)

```python
from erk import ERK

result = ERK.quick_eval(
    "check: this.level >= 5 AND this.verified",
    {"this": {"level": 10, "verified": True}}
)
# {'ok': True, 'rule': 'inline', 'action': 'check', ...}
```

### Validation de syntaxe

```python
result = ERK.validate("enable: this.flags.contains('active')")
# {'valid': True}

result = ERK.validate("enable: this.value ==")
# {'valid': False, 'error': 'ERKParseError: ...'}
```

### Parsing pour debug

```python
result = ERK.parse("allow: this.x == 1 AND this.y == 2")
# {'ok': True, 'ast': {...}}
```

---

## Structure du résultat

```python
{
    "ok": True,              # Succès de l'évaluation
    "rule": "can_execute",   # Nom de la règle
    "action": "allow",       # Action de la règle
    "value": True,           # Valeur brute de l'expression
    "reason": "condition met",  # Raison lisible
    "details": {             # Détails additionnels
        "expression_value": True
    }
}
```

### En cas d'erreur

```python
{
    "ok": False,
    "rule": "invalid_rule",
    "action": "unknown",
    "reason": "Object 'xxx' not found",
    "error": True,
    "details": {"exception": "ERKReferenceError"}
}
```

---

## Extensibilité pour B2/2

L'architecture est conçue pour faciliter les extensions futures :

### Ajout de nouvelles actions
```python
# Dans evaluator.py: _interpret_result()
if action == 'new_action':
    return custom_logic(value)
```

### Ajout de nouvelles méthodes
```python
# Dans evaluator.py: BUILTIN_METHODS
BUILTIN_METHODS = {
    ...
    'newMethod': '_method_new_method',
}

def _method_new_method(self, obj, args, node):
    # Implementation
    pass
```

### Ajout de nouveaux opérateurs
```python
# Dans lexer.py: OPERATORS
# Dans parser.py: parse_expression()
# Dans evaluator.py: _eval_binary_op()
```

### Intégration avec le store réel
```python
# Sous-classer StoreAdapter pour connecter au vrai store JSON
class CockpitStoreAdapter(StoreAdapter):
    def __init__(self, cockpit_store):
        self.store = cockpit_store
    
    def get_object(self, object_id):
        return self.store.get_object(object_id)
    
    def get_rule(self, object_id, rule_name):
        obj = self.store.get_object(object_id)
        return obj.get('rules', {}).get(rule_name)
```

---

## Tests

```bash
# Lancer tous les tests
python -m pytest erk/tests/test_erk.py -v

# Résultat: 56 passed
```

### Couverture des tests

- **Lexer**: tokens, opérateurs, mots-clés, strings, nombres
- **Parser**: règles, comparaisons, AND/OR/NOT, méthodes, tableaux
- **Evaluator**: littéraux, accès membres, opérateurs, méthodes
- **Console**: eval, validate, parse, list_rules, eval_all
- **Exemples ERK**: règles réalistes documentées
- **Robustesse**: null, chaînes vides, imbrication profonde, short-circuit

---

## Démonstration

```bash
python -m erk.demo
```

Affiche une démonstration complète avec :
1. Évaluation basique avec store
2. Évaluation rapide sans store
3. Gestion des erreurs
4. Évaluation de toutes les règles d'un objet
5. Parsing et affichage AST
6. Démonstration des méthodes built-in

---

## Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `__init__.py` | ~130 | API publique et façade ERK |
| `ast_nodes.py` | ~100 | Définition des nœuds AST |
| `lexer.py` | ~200 | Tokenization |
| `parser.py` | ~280 | Construction AST |
| `evaluator.py` | ~400 | Évaluation |
| `console.py` | ~180 | Intégration console |
| `errors.py` | ~90 | Exceptions typées |
| `demo.py` | ~230 | Démonstration |
| `test_erk.py` | ~450 | 56 tests |
| **Total** | **~2060** | |
