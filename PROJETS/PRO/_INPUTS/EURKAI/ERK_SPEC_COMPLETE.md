# ERK — EUREKAI Rule Kernel

## Spécification Complète v1.1

**Version:** 1.1.0  
**Statut:** RELEASE CANDIDATE  
**Date:** 2025-12-07  
**Auteur:** Architecture EUREKAI  

---

## 1. Introduction

### 1.1 Objectif

ERK (EUREKAI Rule Kernel) est le langage logique opératoire unifié d'EUREKAI. Il sert de fondation syntaxique et sémantique pour :

- Les **règles** de validation et de comportement
- Les **méthodes** et leur logique d'exécution
- Les **formules** de calcul (style Excel-like)
- Les **diagnostics** SuperEngage
- Les **transformations** entre objets
- Tout **code généré ou exécuté** par les agents IA

ERK garantit une cohérence totale entre les différentes couches du système fractal, depuis la définition des ObjectTypes jusqu'à l'exécution runtime par les agents.

### 1.2 Principes Fondateurs

| Principe | Description |
|----------|-------------|
| **Lisibilité** | Syntaxe proche du langage naturel, compréhensible par humains et IA |
| **Déterminisme** | Même entrée → même sortie, toujours |
| **Traçabilité** | Chaque évaluation produit une trace exploitable |
| **Sécurité** | Pas d'effets de bord non contrôlés, sandbox obligatoire |
| **Extensibilité** | Nouvelles fonctions via Standard Library sans modifier le cœur |

### 1.3 Compatibilité

ERK est conçu pour s'intégrer nativement avec :

- **XFractal** : système de lineage et d'héritage fractal
- **IVC×DRO** : pattern Identity-View-Context × Definition-Rule-Option
- **GEVR** : cycle Get-Execute-Validate-Render
- **SuperEngage** : protocole d'engagement et scoring des agents
- **MetaSchema** : schéma de validation structurelle

---

## 2. Grammaire Formelle ERK v1.1

### 2.1 Notation BNF

```bnf
(* === ERK v1.1 Grammar === *)

program          ::= statement+

statement        ::= rule_statement
                   | method_statement
                   | formula_statement
                   | diagnostic_statement

(* --- RULES --- *)
rule_statement   ::= action ':' rule_body

action           ::= 'must' | 'must_not' | 'enable' | 'disable' 
                   | 'allow' | 'deny' | 'require' | 'forbid'
                   | 'check' | 'validate' | 'warn' | 'suggest'

rule_body        ::= expression
                   | if_expression
                   | when_expression
                   | suggest_expression

if_expression    ::= 'IF' expression 'THEN' result_expr ('ELSE' result_expr)?

when_expression  ::= 'WHEN' expression 'THEN' result_expr

suggest_expression ::= 'SUGGEST' identifier '(' arguments? ')'

result_expr      ::= expression | suggest_expression

(* --- EXPRESSIONS --- *)
expression       ::= or_expression

or_expression    ::= and_expression ('OR' and_expression)*

and_expression   ::= not_expression ('AND' not_expression)*

not_expression   ::= 'NOT' not_expression
                   | comparison

comparison       ::= term (comparator term)?

comparator       ::= '==' | '!=' | '>' | '<' | '>=' | '<=' 
                   | 'IN' | 'NOT IN' | 'MATCHES' | 'CONTAINS'

term             ::= primary accessor*

accessor         ::= '.' identifier
                   | '.' identifier '(' arguments? ')'
                   | '[' expression ']'

primary          ::= 'this'
                   | 'ctx'
                   | 'parent'
                   | identifier
                   | literal
                   | '(' expression ')'
                   | array_literal

(* --- METHODS --- *)
method_statement ::= 'METHOD' identifier '(' parameters? ')' ':' return_type
                     method_body

method_body      ::= '{' step+ '}'

step             ::= 'STEP' identifier ':' step_body

step_body        ::= assignment
                   | invocation
                   | conditional_step
                   | return_statement

assignment       ::= identifier '=' expression

invocation       ::= expression '.' identifier '(' arguments? ')'

conditional_step ::= 'IF' expression 'THEN' step_body ('ELSE' step_body)?

return_statement ::= 'RETURN' expression

(* --- FORMULAS --- *)
formula_statement ::= 'FORMULA' identifier '=' formula_expression

formula_expression ::= function_call
                     | arithmetic_expression
                     | formula_expression operator formula_expression

function_call    ::= identifier '(' arguments? ')'

arithmetic_expression ::= term (('+' | '-' | '*' | '/' | '%' | '^') term)*

(* --- DIAGNOSTICS --- *)
diagnostic_statement ::= 'DIAGNOSTIC' identifier '{' diagnostic_body '}'

diagnostic_body  ::= 'CONTEXT:' context_def
                     'EVALUATE:' evaluate_def
                     'SCORE:' score_def
                     'RECOMMEND:' recommend_def

(* --- PRIMITIVES --- *)
literal          ::= boolean | string | number | null

boolean          ::= 'true' | 'false'

string           ::= '"' character* '"'
                   | "'" character* "'"

number           ::= integer | float

integer          ::= digit+

float            ::= digit+ '.' digit+

null             ::= 'null'

array_literal    ::= '[' (expression (',' expression)*)? ']'

identifier       ::= letter (letter | digit | '_')*

parameters       ::= parameter (',' parameter)*

parameter        ::= identifier ':' type_name ('=' literal)?

arguments        ::= expression (',' expression)*

return_type      ::= type_name

type_name        ::= 'bool' | 'string' | 'int' | 'float' 
                   | 'array' | 'object' | 'any' | 'void'
                   | identifier

(* --- LEXICAL --- *)
letter           ::= [a-zA-Z_]
digit            ::= [0-9]
character        ::= (* any unicode character except quote *)
```

### 2.2 Structure des Identifiants

Les identifiants ERK suivent une convention hiérarchique :

```
<category>.<domain>.<name>

Exemples:
  rule.validation.name_required
  method.agent.execute
  formula.engage.rate
  diagnostic.super.engage_full
```

**Catégories réservées :**

| Catégorie | Usage |
|-----------|-------|
| `rule` | Règles de validation/comportement |
| `method` | Méthodes exécutables |
| `formula` | Formules de calcul |
| `diagnostic` | Diagnostics SuperEngage |
| `transform` | Transformations d'objets |
| `gate` | Gates de validation GEVR |

---

## 3. Mots-clés Officiels

### 3.1 Actions de Règles

| Mot-clé | Sémantique | Effet si violation |
|---------|------------|-------------------|
| `must` | Obligation stricte | BLOCK + ERROR |
| `must_not` | Interdiction stricte | BLOCK + ERROR |
| `enable` | Activation conditionnelle | Désactivé si false |
| `disable` | Désactivation conditionnelle | Activé si false |
| `allow` | Permission | DENY si false |
| `deny` | Refus explicite | Toujours refusé |
| `require` | Prérequis | BLOCK si absent |
| `forbid` | Interdiction absolue | BLOCK + CRITICAL |
| `check` | Vérification souple | WARNING si false |
| `validate` | Validation structurelle | ERROR si invalid |
| `warn` | Avertissement | WARNING (non bloquant) |
| `suggest` | Suggestion IA | Proposé, non imposé |



### 3.2 Opérateurs Logiques

| Opérateur | Description | Priorité |
|-----------|-------------|----------|
| `NOT` | Négation logique | 1 (haute) |
| `AND` | Conjonction logique | 2 |
| `OR` | Disjonction logique | 3 |

### 3.3 Opérateurs de Comparaison

| Opérateur | Description | Types supportés |
|-----------|-------------|-----------------|
| `==` | Égalité stricte | Tous |
| `!=` | Inégalité | Tous |
| `>` | Supérieur | number, string |
| `<` | Inférieur | number, string |
| `>=` | Supérieur ou égal | number, string |
| `<=` | Inférieur ou égal | number, string |
| `IN` | Appartenance | array, string |
| `NOT IN` | Non-appartenance | array, string |
| `MATCHES` | Expression régulière | string |
| `CONTAINS` | Contient élément | array, string, object |

### 3.4 Structures de Contrôle

| Mot-clé | Usage |
|---------|-------|
| `IF` | Début de condition |
| `THEN` | Branche vraie |
| `ELSE` | Branche fausse (optionnel) |
| `WHEN` | Condition contextuelle |
| `SUGGEST` | Proposition d'action |

### 3.5 Références Spéciales

| Référence | Description |
|-----------|-------------|
| `this` | Objet courant évalué |
| `ctx` | Contexte d'exécution |
| `parent` | Objet parent dans le lineage |
| `root` | Objet racine du lineage |

---

## 4. Structures Syntaxiques

### 4.1 Règles

#### 4.1.1 Obligation (must)

```erk
must: this.name != null AND this.name.length > 0
```

#### 4.1.2 Interdiction (must_not)

```erk
must_not: this.status == "deleted" AND this.hasChildren == true
```

#### 4.1.3 Conditionnelle (IF/THEN/ELSE)

```erk
enable: IF this.priority == "high" THEN true ELSE this.hasApproval
```

#### 4.1.4 Contextuelle (WHEN/THEN)

```erk
allow: WHEN ctx.layer == "System" AND ctx.mode == "strict" THEN true
```

#### 4.1.5 Suggestion (SUGGEST)

```erk
suggest: IF this.score < 0.5 THEN SUGGEST improve_prompt(this.prompt, "clarity")
```

### 4.2 Méthodes

```erk
METHOD execute(task: object, options: object = {}): Result {
  
  STEP validate:
    IF NOT task.isValid THEN RETURN Result.error("Invalid task")
  
  STEP prepare:
    context = this.buildContext(task, options)
    inputs = this.resolveInputs(context)
  
  STEP run:
    IF options.async == true THEN
      output = this.executeAsync(inputs)
    ELSE
      output = this.executeSync(inputs)
  
  STEP finalize:
    result = this.wrapResult(output)
    this.logExecution(result)
    RETURN result
}
```

### 4.3 Formules

#### 4.3.1 Formule Simple

```erk
FORMULA engage.rate = (successes / attempts) * 100
```

#### 4.3.2 Formule Composite

```erk
FORMULA agent.score = 
  (0.4 * metrics.accuracy) + 
  (0.3 * metrics.speed) + 
  (0.2 * metrics.reliability) + 
  (0.1 * metrics.cost_efficiency)
```

#### 4.3.3 Formule avec Fonctions

```erk
FORMULA risk.level = 
  IF(severity > 8, "critical",
    IF(severity > 5, "high",
      IF(severity > 2, "medium", "low")))
```

### 4.4 Diagnostics SuperEngage

```erk
DIAGNOSTIC super.engage_full {
  
  CONTEXT:
    agent = ctx.current_agent
    scenario = ctx.scenario
    history = agent.executionHistory.last(100)
  
  EVALUATE:
    accuracy = history.filter(h => h.success).length / history.length
    latency_avg = math.average(history.map(h => h.duration))
    error_rate = history.filter(h => h.hasError).length / history.length
    coherence = semantic.score(agent.responses, scenario.expected)
  
  SCORE:
    pgcd = (accuracy >= 0.9 AND error_rate <= 0.05) ? 1.0 : 0.0
    ppcm = math.clamp(coherence * 0.6 + (1 - latency_avg/1000) * 0.4, 0, 1)
    overall = 0.4 * pgcd + 0.3 * ppcm + 0.3 * (1 - error_rate)
  
  RECOMMEND:
    IF overall < 0.3 THEN SUGGEST disengage(agent)
    IF overall >= 0.3 AND overall < 0.7 THEN SUGGEST review(agent)
    IF overall >= 0.7 THEN SUGGEST approve(agent)
    IF overall >= 0.95 AND error_rate < 0.01 THEN SUGGEST auto_approve(agent)
}
```

### 4.5 Mappings (Transformations)

```erk
TRANSFORM AgentDTO FROM Agent {
  id = this.id
  name = this.name
  type = this.lineage.last()
  capabilities = this.resolvedElements.methods.map(m => m.name)
  status = IF this.isEngaged THEN "active" ELSE "idle"
  score = formula.agent.score(this)
}
```

---

## 5. Standard Library ERK

### 5.1 Fonctions String

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `string.len` | `(s: string): int` | Longueur de la chaîne |
| `string.upper` | `(s: string): string` | Convertit en majuscules |
| `string.lower` | `(s: string): string` | Convertit en minuscules |
| `string.trim` | `(s: string): string` | Supprime espaces début/fin |
| `string.split` | `(s: string, sep: string): array` | Découpe en tableau |
| `string.join` | `(arr: array, sep: string): string` | Joint un tableau |
| `string.replace` | `(s: string, old: string, new: string): string` | Remplace occurrences |
| `string.contains` | `(s: string, sub: string): bool` | Contient sous-chaîne |
| `string.startsWith` | `(s: string, prefix: string): bool` | Commence par |
| `string.endsWith` | `(s: string, suffix: string): bool` | Termine par |
| `string.matches` | `(s: string, pattern: string): bool` | Match regex |
| `string.extract` | `(s: string, pattern: string): string` | Extrait via regex |

### 5.2 Fonctions List/Array

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `list.len` | `(arr: array): int` | Nombre d'éléments |
| `list.contains` | `(arr: array, item: any): bool` | Contient élément |
| `list.first` | `(arr: array): any` | Premier élément |
| `list.last` | `(arr: array): any` | Dernier élément |
| `list.at` | `(arr: array, idx: int): any` | Élément à l'index |
| `list.slice` | `(arr: array, start: int, end: int): array` | Sous-tableau |
| `list.filter` | `(arr: array, predicate: func): array` | Filtre éléments |
| `list.map` | `(arr: array, transform: func): array` | Transforme éléments |
| `list.reduce` | `(arr: array, reducer: func, init: any): any` | Réduit à une valeur |
| `list.sort` | `(arr: array, key?: string): array` | Trie le tableau |
| `list.unique` | `(arr: array): array` | Élimine doublons |
| `list.flatten` | `(arr: array): array` | Aplatit récursivement |

### 5.3 Fonctions Math

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `math.abs` | `(n: number): number` | Valeur absolue |
| `math.round` | `(n: number, decimals?: int): number` | Arrondit |
| `math.floor` | `(n: number): int` | Arrondit vers le bas |
| `math.ceil` | `(n: number): int` | Arrondit vers le haut |
| `math.clamp` | `(n: number, min: number, max: number): number` | Borne une valeur |
| `math.min` | `(...nums: number[]): number` | Minimum |
| `math.max` | `(...nums: number[]): number` | Maximum |
| `math.sum` | `(arr: array): number` | Somme |
| `math.average` | `(arr: array): number` | Moyenne |
| `math.median` | `(arr: array): number` | Médiane |
| `math.pow` | `(base: number, exp: number): number` | Puissance |
| `math.sqrt` | `(n: number): number` | Racine carrée |
| `math.log` | `(n: number, base?: number): number` | Logarithme |

### 5.4 Fonctions Vector (Lineage)

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `vector.resolve` | `(lineage: string): object` | Résout un lineage complet |
| `vector.parent` | `(lineage: string): string` | Retourne le parent |
| `vector.root` | `(lineage: string): string` | Retourne la racine |
| `vector.depth` | `(lineage: string): int` | Profondeur dans l'arbre |
| `vector.ancestors` | `(lineage: string): array` | Liste des ancêtres |
| `vector.children` | `(lineage: string): array` | Enfants directs |
| `vector.descendants` | `(lineage: string, depth?: int): array` | Tous les descendants |
| `vector.isAncestorOf` | `(lineage: string, descendant: string): bool` | Est ancêtre de |
| `vector.commonAncestor` | `(l1: string, l2: string): string` | Ancêtre commun |

### 5.5 Fonctions Engage

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `engage.rate` | `(agent: object): float` | Taux de succès |
| `engage.score` | `(agent: object): float` | Score global |
| `engage.history` | `(agent: object, n?: int): array` | Historique d'exécutions |
| `engage.explain` | `(score: float): string` | Explication textuelle |
| `engage.compare` | `(agents: array): array` | Compare et classe agents |
| `engage.recommend` | `(agent: object): object` | Recommandation d'action |
| `engage.canExecute` | `(agent: object, task: object): bool` | Peut exécuter tâche |
| `engage.estimate` | `(agent: object, task: object): object` | Estime durée/coût |

### 5.6 Fonctions Object

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `object.get` | `(obj: object, path: string): any` | Accès par chemin |
| `object.set` | `(obj: object, path: string, value: any): object` | Modifie (immutable) |
| `object.has` | `(obj: object, key: string): bool` | Possède la clé |
| `object.keys` | `(obj: object): array` | Liste des clés |
| `object.values` | `(obj: object): array` | Liste des valeurs |
| `object.merge` | `(obj1: object, obj2: object): object` | Fusionne objets |
| `object.pick` | `(obj: object, keys: array): object` | Sélectionne clés |
| `object.omit` | `(obj: object, keys: array): object` | Exclut clés |

### 5.7 Fonctions Date

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `date.now` | `(): string` | Date/heure ISO actuelle |
| `date.parse` | `(s: string, format?: string): date` | Parse une date |
| `date.format` | `(d: date, format: string): string` | Formate une date |
| `date.add` | `(d: date, amount: int, unit: string): date` | Ajoute durée |
| `date.diff` | `(d1: date, d2: date, unit: string): int` | Différence |
| `date.isBefore` | `(d1: date, d2: date): bool` | Est avant |
| `date.isAfter` | `(d1: date, d2: date): bool` | Est après |
| `date.between` | `(d: date, start: date, end: date): bool` | Dans intervalle |

### 5.8 Fonctions Type

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `type.of` | `(value: any): string` | Type de la valeur |
| `type.is` | `(value: any, typeName: string): bool` | Vérifie le type |
| `type.cast` | `(value: any, typeName: string): any` | Convertit type |
| `type.isNull` | `(value: any): bool` | Est null |
| `type.isArray` | `(value: any): bool` | Est un tableau |
| `type.isObject` | `(value: any): bool` | Est un objet |

---

## 6. Conventions de Codage ERK

### 6.1 Indentation

- Utiliser **2 espaces** pour l'indentation (pas de tabs)
- Aligner les blocs THEN/ELSE au même niveau que IF
- Indenter le contenu des METHOD et DIAGNOSTIC

```erk
(* BON *)
enable: IF this.active == true 
        THEN this.permissions.includes("write")
        ELSE false

(* MAUVAIS *)
enable:IF this.active==true THEN this.permissions.includes("write") ELSE false
```

### 6.2 Structuration

- Une règle par ligne pour les règles simples
- Bloc multi-lignes pour les conditions complexes
- Séparer les sections logiques par une ligne vide

```erk
(* Section: Validations de base *)
must: this.id != null
must: this.name != null AND this.name.length > 0

(* Section: Permissions *)
allow: WHEN ctx.user.role == "admin" THEN true
deny: this.status == "locked" AND ctx.user.role != "admin"
```

### 6.3 Nommage

| Élément | Convention | Exemple |
|---------|------------|---------|
| Identifiants | camelCase | `userName`, `maxRetries` |
| Constantes | UPPER_SNAKE | `MAX_ATTEMPTS`, `DEFAULT_TIMEOUT` |
| Types | PascalCase | `Agent`, `TaskResult` |
| Fonctions stdlib | module.function | `string.len`, `math.clamp` |
| Règles | category.domain.name | `rule.agent.must_have_model` |

### 6.4 Commentaires

```erk
(* Commentaire sur une ligne *)

(*
  Commentaire
  multi-lignes
*)

must: this.model != null  (* Commentaire en fin de ligne *)
```

### 6.5 Principes d'Écriture

1. **Clarté avant concision** : privilégier la lisibilité à la brièveté
2. **Explicite avant implicite** : éviter les comportements cachés
3. **Fail-fast** : détecter les erreurs au plus tôt
4. **Immutabilité** : préférer les transformations aux mutations
5. **Composabilité** : découper en fonctions réutilisables

---

## 7. Exemples Canoniques

### 7.1 Règles (10 exemples)

```erk
(* R01 - Obligation de nom *)
must: this.name != null AND string.len(this.name) >= 2

(* R02 - Interdiction de suppression avec enfants *)
must_not: this.toDelete == true AND list.len(this.children) > 0

(* R03 - Activation conditionnelle de prompt *)
enable: IF this.model != null THEN true ELSE false

(* R04 - Permission basée sur le contexte *)
allow: WHEN ctx.layer == "System" AND ctx.user.role IN ["admin", "operator"] THEN true

(* R05 - Validation de lineage *)
validate: this.lineage MATCHES "^Object(:[A-Z][a-zA-Z0-9]*)+$"

(* R06 - Prérequis d'engagement *)
require: this.status == "ready" AND engage.canExecute(this, ctx.task)

(* R07 - Interdiction absolue sur données sensibles *)
forbid: this.classification == "TOP_SECRET" AND ctx.clearance < 5

(* R08 - Avertissement de performance *)
warn: IF engage.rate(this) < 0.6 THEN "Performance dégradée, considérer révision"

(* R09 - Vérification de cohérence *)
check: list.len(this.elementList.AttributeList.owned_bundle) > 0 
       OR list.len(this.elementList.RelationList.owned_bundle) > 0

(* R10 - Suggestion d'amélioration *)
suggest: IF this.score < 0.5 
         THEN SUGGEST optimize_agent(this, { focus: "accuracy" })
```

### 7.2 Méthodes (3 exemples)

```erk
(* M01 - Méthode d'exécution agent *)
METHOD prompt(input: string, options: object = {}): Response {
  
  STEP validate:
    IF string.len(input) == 0 THEN RETURN Response.error("Empty input")
    IF string.len(input) > 100000 THEN RETURN Response.error("Input too large")
  
  STEP prepare:
    context = this.buildContext(options)
    enriched_input = this.enrichPrompt(input, context)
  
  STEP execute:
    raw_response = this.model.generate(enriched_input, {
      temperature: options.temperature ?? this.temperature,
      max_tokens: options.max_tokens ?? 4096
    })
  
  STEP validate_output:
    IF NOT this.validateResponse(raw_response) THEN
      RETURN Response.error("Invalid response format")
  
  STEP finalize:
    response = Response.success(raw_response)
    this.logExecution(input, response)
    RETURN response
}

(* M02 - Méthode de validation GEVR *)
METHOD validate_gevr(inputs: object): ValidationResult {
  
  STEP check_structure:
    errors = []
    IF NOT object.has(inputs, "get") THEN list.push(errors, "Missing GET phase")
    IF NOT object.has(inputs, "execute") THEN list.push(errors, "Missing EXECUTE phase")
  
  STEP validate_gates:
    gates = this.resolvedElements.rules.filter(r => r.type == "gate")
    gate_results = gates.map(g => {
      result: ERK.eval(this.id, g.id, inputs),
      gate: g
    })
  
  STEP aggregate:
    failed = gate_results.filter(gr => gr.result.success == false)
    IF list.len(failed) > 0 THEN
      RETURN ValidationResult.fail(failed.map(f => f.gate.id))
  
  STEP success:
    RETURN ValidationResult.pass()
}

(* M03 - Méthode de transformation *)
METHOD transform_to_dto(target_type: string): object {
  
  STEP resolve:
    transformer = this.catalog.getTransformer(this.lineage, target_type)
    IF transformer == null THEN 
      RETURN { error: "No transformer found" }
  
  STEP map:
    dto = {}
    transformer.mappings.forEach(m => {
      value = object.get(this, m.source)
      IF m.transform != null THEN
        value = ERK.eval_formula(m.transform, { value: value })
      object.set(dto, m.target, value)
    })
  
  STEP validate:
    schema = this.catalog.getSchema(target_type)
    IF NOT schema.validate(dto) THEN
      RETURN { error: "DTO validation failed", details: schema.errors }
  
  STEP return:
    RETURN dto
}
```

### 7.3 Formules (2 exemples)

```erk
(* F01 - Score d'agent pondéré *)
FORMULA agent.weighted_score = 
  math.clamp(
    (0.40 * metrics.accuracy) +
    (0.25 * metrics.reliability) +
    (0.20 * (1 - metrics.latency / 10000)) +
    (0.10 * metrics.cost_efficiency) +
    (0.05 * metrics.user_satisfaction),
    0, 1
  )

(* F02 - Calcul de risque composite *)
FORMULA risk.composite_level = 
  IF(
    severity >= 9 OR (severity >= 7 AND probability >= 0.8),
    "CRITICAL",
    IF(
      severity >= 7 OR (severity >= 5 AND probability >= 0.6),
      "HIGH",
      IF(
        severity >= 4 OR probability >= 0.4,
        "MEDIUM",
        "LOW"
      )
    )
  )
```

### 7.4 Diagnostic SuperEngage (1 exemple complet)

```erk
DIAGNOSTIC super.engage_agent_evaluation {
  
  CONTEXT:
    agent = ctx.agent
    scenario = ctx.scenario
    task_pool = ctx.available_tasks
    history = agent.executionHistory.last(50)
    peers = ctx.peer_agents.filter(p => p.type == agent.type)
  
  EVALUATE:
    (* Métriques de base *)
    success_rate = history.filter(h => h.success).length / math.max(history.length, 1)
    error_rate = history.filter(h => h.hasError).length / math.max(history.length, 1)
    avg_latency = math.average(history.map(h => h.duration))
    
    (* Métriques avancées *)
    consistency = math.stddev(history.map(h => h.quality_score)) 
    adaptability = agent.adaptationScore ?? 0.5
    
    (* Comparaison avec pairs *)
    peer_avg_success = math.average(peers.map(p => engage.rate(p)))
    relative_performance = success_rate / math.max(peer_avg_success, 0.01)
    
    (* Capacité restante *)
    workload = agent.currentTasks.length / agent.maxConcurrent
    available_capacity = 1 - workload
  
  SCORE:
    (* PGCD: seuil minimal de cohérence *)
    pgcd_pass = success_rate >= 0.85 
                AND error_rate <= 0.10 
                AND avg_latency <= 5000
    pgcd = pgcd_pass ? 1.0 : 0.0
    
    (* PPCM: potentiel maximal *)
    ppcm = math.clamp(
      (0.35 * success_rate) +
      (0.25 * (1 - consistency)) +
      (0.20 * adaptability) +
      (0.20 * relative_performance),
      0, 1
    )
    
    (* Score final *)
    risk = error_rate * 0.6 + (avg_latency / 10000) * 0.4
    overall = (0.40 * pgcd) + (0.30 * ppcm) + (0.30 * (1 - risk))
  
  RECOMMEND:
    (* Décisions automatiques *)
    IF overall < 0.30 THEN 
      SUGGEST disengage(agent, { reason: "Performance critique", auto: false })
    
    IF overall >= 0.30 AND overall < 0.50 THEN
      SUGGEST review(agent, { 
        priority: "high",
        focus: ["error_rate", "latency"],
        deadline: date.add(date.now(), 24, "hours")
      })
    
    IF overall >= 0.50 AND overall < 0.70 THEN
      SUGGEST monitor(agent, { 
        interval: 3600,
        alerts: ["degradation", "error_spike"]
      })
    
    IF overall >= 0.70 AND overall < 0.95 THEN
      SUGGEST approve(agent, { 
        scope: task_pool.filter(t => t.complexity <= "medium"),
        review_after: 100
      })
    
    IF overall >= 0.95 AND error_rate < 0.02 AND available_capacity > 0.3 THEN
      SUGGEST auto_approve(agent, {
        scope: task_pool,
        max_concurrent: agent.maxConcurrent,
        escalation_threshold: 0.85
      })
    
    (* Suggestions d'optimisation *)
    IF avg_latency > 3000 AND success_rate > 0.9 THEN
      SUGGEST optimize(agent, { focus: "speed", preserve: "accuracy" })
    
    IF consistency > 0.3 THEN
      SUGGEST stabilize(agent, { 
        method: "ensemble",
        validation_passes: 3
      })
}
```

---

## 8. Sécurité & Garde-fous IA

### 8.1 Principes de Sécurité

| Principe | Description |
|----------|-------------|
| **Sandbox** | Toute évaluation ERK s'exécute dans un environnement isolé |
| **Timeout** | Limite de temps d'exécution (défaut: 5000ms) |
| **Depth limit** | Profondeur maximale de récursion (défaut: 100) |
| **Memory limit** | Mémoire maximale allouée (défaut: 64MB) |
| **No side effects** | Aucune modification d'état hors du contexte explicite |

### 8.2 Ce que l'IA PEUT Modifier

| Domaine | Permissions | Conditions |
|---------|-------------|------------|
| **Suggestions** | Créer, proposer | Toujours soumis à validation humaine |
| **Attributs optionnels** | Modifier valeurs | Si marqués `ai_writable: true` |
| **Scores/métriques** | Calculer, mettre à jour | Selon formules définies |
| **Logs** | Créer entrées | Toujours autorisé |
| **Cache** | Invalider, recalculer | Dans son périmètre |

### 8.3 Ce que l'IA NE PEUT PAS Modifier

| Domaine | Protection | Enforcement |
|---------|------------|-------------|
| **Attributs `immutable`** | Lecture seule absolue | HARD_BLOCK + CRITICAL |
| **Règles système** | Modification interdite | Signature Ed25519 requise |
| **Lineages existants** | Renommage interdit | Intégrité référentielle |
| **Seuils de sécurité** | Modification interdite | Audit + alerte immédiate |
| **Logs d'audit** | Append-only | Merkle chain + signature |
| **Permissions utilisateur** | Escalade interdite | Vérification multi-niveau |

### 8.4 Validation SuperEngage

SuperEngage agit comme gardien final avec les pouvoirs suivants :

```erk
(* Règles de garde SuperEngage - IMMUTABLES *)

(* SE-001: Aucune exécution sans approbation *)
forbid: ctx.execution_request != null 
        AND ctx.approval == null

(* SE-002: Suggestions contraintes au catalogue *)
forbid: ctx.suggestion.type NOT IN catalog.allowed_suggestion_types

(* SE-003: Modifications IA tracées *)
must: ctx.ai_modification != null 
      => ctx.ai_modification.logged == true 
         AND ctx.ai_modification.signature != null

(* SE-004: Rollback disponible *)
must: ctx.ai_modification != null 
      => ctx.rollback_point != null

(* SE-005: Limite de confiance *)
forbid: ctx.auto_approve == true 
        AND (ctx.agent.trust_level < 0.95 OR ctx.task.risk_level > "low")
```

### 8.5 Processus de Correction

Lorsqu'une anomalie est détectée :

```
1. DETECT  → Anomalie identifiée par règle ERK
2. BLOCK   → Opération bloquée immédiatement  
3. LOG     → Événement consigné avec signature
4. ALERT   → Notification selon gravité
5. ANALYZE → SuperEngage évalue la situation
6. SUGGEST → Proposition de correction (si possible)
7. REVIEW  → Validation humaine requise
8. APPLY   → Correction appliquée (si approuvée)
9. VERIFY  → Vérification post-correction
```

---

## 9. Codes d'Erreur

| Code | Type | Description |
|------|------|-------------|
| `#PARSE!` | Syntaxe | Erreur de parsing ERK |
| `#TYPE!` | Type | Incompatibilité de types |
| `#VALUE!` | Valeur | Valeur invalide ou hors bornes |
| `#REF!` | Référence | Référence non résolue |
| `#NULL!` | Null | Accès à valeur null |
| `#PERM!` | Permission | Opération non autorisée |
| `#TIMEOUT!` | Timeout | Dépassement temps d'exécution |
| `#DEPTH!` | Profondeur | Récursion trop profonde |
| `#MEMORY!` | Mémoire | Limite mémoire atteinte |
| `#N/A` | Non applicable | Résultat non disponible |

---

## 10. Appendices

### A. Tableau de Priorité des Opérateurs

| Priorité | Opérateurs | Associativité |
|----------|------------|---------------|
| 1 | `()` | N/A |
| 2 | `.` `[]` | Gauche |
| 3 | `NOT` `-` (unaire) | Droite |
| 4 | `^` | Droite |
| 5 | `*` `/` `%` | Gauche |
| 6 | `+` `-` | Gauche |
| 7 | `>` `<` `>=` `<=` | Gauche |
| 8 | `==` `!=` `IN` `MATCHES` | Gauche |
| 9 | `AND` | Gauche |
| 10 | `OR` | Gauche |
| 11 | `IF` `WHEN` | Droite |

### B. Types Primitifs

| Type | Description | Exemple |
|------|-------------|---------|
| `bool` | Booléen | `true`, `false` |
| `int` | Entier 64 bits | `42`, `-17` |
| `float` | Flottant 64 bits | `3.14`, `-0.5` |
| `string` | Chaîne Unicode | `"hello"`, `'world'` |
| `array` | Tableau ordonné | `[1, 2, 3]` |
| `object` | Dictionnaire clé-valeur | `{ a: 1, b: 2 }` |
| `null` | Valeur nulle | `null` |
| `date` | Date/heure ISO | `"2025-12-07T10:30:00Z"` |

### C. Mots Réservés

```
AND, CONTEXT, DIAGNOSTIC, DISABLE, ELSE, ENABLE, EVALUATE, 
false, FORBID, FORMULA, IF, IN, MATCHES, METHOD, must, must_not,
NOT, null, OR, RECOMMEND, REQUIRE, RETURN, SCORE, STEP, SUGGEST, 
THEN, this, ctx, parent, root, TRANSFORM, true, VALIDATE, WARN, WHEN
```

---

## Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0.0 | 2025-11-01 | Version initiale (B1) |
| 1.0.1 | 2025-11-15 | Ajout IF/THEN/ELSE, ctx (B2) |
| 1.0.2 | 2025-11-25 | Ajout SUGGEST, actions système (B3) |
| 1.1.0 | 2025-12-07 | Spécification complète, Standard Library, Diagnostics |

---

*© 2025 EUREKAI Architecture — Document généré selon les standards ISO/IEC 14977 (EBNF)*
