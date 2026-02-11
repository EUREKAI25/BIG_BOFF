# ERK B2/2 - Interpréteur de Règles EUREKAI Étendu

## Vue d'ensemble

Cette version étend l'interpréteur ERK minimal (B1/1) avec :

- **Conditions IF/THEN/ELSE** pour des règles conditionnelles riches
- **Conditions WHEN/THEN** pour des règles contextuelles
- **Accès au contexte `ctx`** pour les variables d'exécution
- **Traçabilité complète** des évaluations

## Nouvelle Grammaire ERK

### Constructions B2 ajoutées

```
rule         := action ':' expression
              | action ':' if_expr
              | action ':' when_expr

if_expr      := 'IF' expression 'THEN' expression ['ELSE' expression]
when_expr    := 'WHEN' expression 'THEN' expression

primary      := 'this' | 'ctx' | IDENTIFIER | literal | '(' expression ')' | array
```

### Syntaxe IF/THEN/ELSE

```
IF condition THEN résultat_si_vrai [ELSE résultat_si_faux]
```

**Exemples :**

```erk
# Avec ELSE
enable: IF this.priority == "natural" THEN true ELSE false

# Sans ELSE (retourne False si condition fausse)
allow: IF this.credits > 0 THEN true

# Conditions complexes
enable: IF this.status == "active" AND this.credits > 0 THEN true ELSE false

# IF imbriqués
check: IF this.role == "admin" THEN true ELSE IF this.role == "moderator" THEN true ELSE false
```

### Syntaxe WHEN/THEN

```
WHEN condition THEN résultat
```

Utilisé principalement pour les conditions basées sur le contexte d'exécution.

**Exemples :**

```erk
# Condition sur le contexte
allow: WHEN ctx.layer == "System" THEN true

# Combinaison this et ctx
allow: WHEN ctx.layer == "System" AND this.type == "Agent" THEN true

# Condition sur le mode
require: WHEN ctx.mode == "strict" THEN true
```

### Accès au contexte `ctx`

Le contexte d'exécution est accessible via `ctx.propriété`.

**Structure du contexte :**

```python
context = {
    "this": {                    # L'objet courant
        "type": "Agent",
        "priority": "natural",
        ...
    },
    "ctx": {                     # B2: Variables de contexte
        "layer": "System",       # Couche d'exécution
        "mode": "normal",        # Mode (strict, normal, permissive)
        "state": "active",       # État global
        ...
    },
    "objects": {...},            # Objets par ID
    "lineages": {...},           # Lineages
    "globals": {...}             # Variables globales
}
```

**Exemples d'utilisation :**

```erk
# Accès simple
check: ctx.layer == "System"

# Accès imbriqué
check: ctx.config.mode == "strict"

# Avec méthodes
check: ctx.flags.contains("debug")

# Combinaison
allow: this.role == "admin" AND ctx.mode == "elevated"
```

## Mise à jour de l'AST

### Nouveaux types de nœuds

| NodeType | Classe | Description |
|----------|--------|-------------|
| `CTX` | `CtxNode` | Référence au contexte `ctx` |
| `IF_THEN_ELSE` | `IfThenElseNode` | Expression conditionnelle |
| `WHEN_THEN` | `WhenThenNode` | Condition contextuelle |

### Structure IfThenElseNode

```python
@dataclass
class IfThenElseNode(ASTNode):
    condition: ASTNode      # La condition à évaluer
    then_branch: ASTNode    # Résultat si condition vraie
    else_branch: ASTNode    # Résultat si condition fausse (optionnel)
```

### Structure WhenThenNode

```python
@dataclass
class WhenThenNode(ASTNode):
    condition: ASTNode      # La condition (implique souvent ctx)
    then_result: ASTNode    # Résultat si condition vraie
```

## Traçabilité

### EvalTrace

Chaque évaluation produit une trace complète des décisions prises.

```python
from erk import evaluate_rule, parse

ast = parse("enable: IF this.active THEN true ELSE false")
result = evaluate_rule(ast, context, "my_rule", enable_trace=True)

# Résumé de la trace
print(result.trace.to_summary())
# {
#     "total_events": 5,
#     "branches_taken": ["Branch taken: THEN"],
#     "conditions_evaluated": 3,
#     "conditions_true": 2,
#     "conditions_false": 1
# }

# Trace complète
print(result.to_dict_full())
# Inclut "trace_full" avec tous les événements
```

### Types d'événements de trace

| Type | Description |
|------|-------------|
| `EVAL_START` | Début d'évaluation |
| `EVAL_END` | Fin d'évaluation |
| `CONDITION_CHECK` | Vérification d'une condition |
| `BRANCH_TAKEN` | Branche suivie |
| `BRANCH_SKIPPED` | Branche ignorée |
| `VALUE_RESOLVED` | Valeur résolue |
| `METHOD_CALLED` | Méthode appelée |
| `ERROR` | Erreur rencontrée |

## Exemples de règles et résultats

### Exemple 1 : Priorité naturelle

```python
# Règle
rule = "enable: IF this.priority == 'natural' THEN true ELSE false"

# Contexte 1 : priority = natural
context = {"this": {"priority": "natural"}}
result = ERK.quick_eval(rule, context)
# {"ok": True, "value": True, "reason": "condition met"}

# Contexte 2 : priority = high
context = {"this": {"priority": "high"}}
result = ERK.quick_eval(rule, context)
# {"ok": False, "value": False, "reason": "condition not met"}
```

### Exemple 2 : Couche système et type agent

```python
# Règle
rule = "allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true"

# Contexte 1 : Layer System + Agent
context = {
    "this": {"type": "Agent"},
    "ctx": {"layer": "System"}
}
result = ERK.quick_eval(rule, context)
# {"ok": True, ...}

# Contexte 2 : Layer User
context = {
    "this": {"type": "Agent"},
    "ctx": {"layer": "User"}
}
result = ERK.quick_eval(rule, context)
# {"ok": False, ...}
```

### Exemple 3 : Règle complexe avec traçabilité

```python
rule = """
enable: IF this.role == "admin" THEN true 
        ELSE IF this.permissions.contains("write") AND ctx.mode == "elevated" THEN true 
        ELSE false
"""

context = {
    "this": {"role": "user", "permissions": ["read", "write"]},
    "ctx": {"mode": "elevated"}
}

ast = parse(rule)
result = evaluate_rule(ast, context, "complex_rule", enable_trace=True)

# Trace montre :
# 1. IF condition "role == admin" → False
# 2. Branch skipped: THEN
# 3. Branch taken: ELSE
# 4. IF condition "permissions.contains('write')" → True
# 5. AND right operand "ctx.mode == 'elevated'" → True
# 6. Branch taken: THEN
# Result: True
```

## Tests

### Exécution des tests

```bash
cd erk_b2
python -m pytest erk/tests/ -v
```

### Couverture de tests

- **41 tests B2** : nouvelles fonctionnalités
- **56 tests B1** : rétrocompatibilité

Tous les 97 tests passent.

## Extensibilité pour B3/3

La conception prépare l'intégration d'actions système :

1. **Résultats typés** : Les branches IF/THEN peuvent retourner des identifiants d'action (`enable`, `disable`, `allow`, `deny`) qui pourront déclencher des effets de bord en B3.

2. **Contexte enrichi** : `ctx` peut contenir des métadonnées système pour les actions.

3. **Traçabilité** : La trace complète permet d'auditer les décisions avant exécution d'actions.

4. **Architecture extensible** : 
   - Ajouter un `ActionExecutor` qui interprète les résultats
   - Les `IfThenElseNode` peuvent produire des `ActionNode`
   - La trace servira de journal d'audit

## Checklist de validation

- [x] Les règles simples de B1/1 continuent de fonctionner sans modification
- [x] Les règles conditionnelles avec IF/THEN/ELSE sont supportées
- [x] Les règles de type WHEN (conditions sur le contexte) sont supportées
- [x] Le résultat de l'évaluation inclut des informations de traçabilité
- [x] Plusieurs exemples de règles + contextes + résultats attendus fournis
- [x] La conception reste clairement extensible pour B3/3 (actions système)
