EURKAI — FORMULAS
Catalogue de référence v1
Date : 2026-04-02
Statut : STABLE — source de vérité unique

-- Les formules sont les briques atomiques pour exprimer les conditions de règles.
-- Elles sont déterministes : même entrée → même sortie.
-- Elles sont combinables récursivement.
-- Syntaxe dans une RuleList : .condition = FORMULE(args)

Catégories : ARITHMETIC | EXISTENCE | COMPARISON | LOGIC | COLLECTION | STRING | STRUCTURE | NAVIGATION


================================
1. ARITHMETIC
================================

-- Opérations numériques de base.

ADD(a, b)           → number      addition
SUB(a, b)           → number      soustraction
MUL(a, b)           → number      multiplication
DIV(a, b)           → number      division (b != 0)
MOD(a, b)           → number      modulo
ABS(a)              → number      valeur absolue
ROUND(a, n)         → number      arrondi à n décimales
CEIL(a)             → int         arrondi supérieur
FLOOR(a)            → int         arrondi inférieur
POW(a, b)           → number      a puissance b
MIN_NUM(a, b)       → number      minimum entre deux nombres
MAX_NUM(a, b)       → number      maximum entre deux nombres
CLAMP(a, min, max)  → number      force a dans [min, max]

-- Exemples en condition de règle :
-- .condition = GT(DIV(value, total), 0)
-- .condition = EQ(MOD(count, 2), 0)   -- est pair


================================
2. EXISTENCE
================================

-- Teste la présence ou l'absence d'une valeur.

ISNULL(x)           → bool        x est null
ISNOTNULL(x)        → bool        x n'est pas null
IS_EMPTY(x)         → bool        x est vide (string, list ou dict vide)
IS_NOT_EMPTY(x)     → bool        x n'est pas vide
EXISTS(x)           → bool        x existe dans le contexte
TYPEOF(x, type)     → bool        x est du type donné

-- Types valides pour TYPEOF : string, int, number, bool, date, json, lineage, list, dict

-- Exemples :
-- .condition = ISNOTNULL(value)
-- .condition = AND(EXISTS(name), IS_NOT_EMPTY(name))
-- .condition = TYPEOF(value, number)


================================
3. COMPARISON
================================

-- Compare deux valeurs. Retourne bool.

EQ(a, b)            → bool        a == b
NEQ(a, b)           → bool        a != b
GT(a, b)            → bool        a > b
GTE(a, b)           → bool        a >= b
LT(a, b)            → bool        a < b
LTE(a, b)           → bool        a <= b
BETWEEN(a, min, max)→ bool        min <= a <= max (bornes incluses)
IN(a, list)         → bool        a est dans la liste
NOT_IN(a, list)     → bool        a n'est pas dans la liste

-- Exemples :
-- .condition = BETWEEN(temperature, 0, 2)
-- .condition = IN(status, ["active", "ready", "pending"])
-- .condition = GTE(score, 80)


================================
4. LOGIC
================================

-- Opérateurs logiques. Combinaison de conditions.

AND(a, b)           → bool        a ET b (les deux vrais)
OR(a, b)            → bool        a OU b (au moins un vrai)
NOT(a)              → bool        négation de a
XOR(a, b)           → bool        l'un ou l'autre, pas les deux
IF(cond, then, else)→ any         si cond alors then sinon else

-- Exemples :
-- .condition = AND(ISNOTNULL(name), NEQ(name, ""))
-- .condition = OR(EQ(status, "active"), EQ(status, "ready"))
-- .condition = NOT(ISNULL(value))
-- .condition = IF(TYPEOF(x, number), GTE(x, 0), IS_NOT_EMPTY(x))


================================
5. COLLECTION
================================

-- Opérations sur listes et dicts.

LENGTH(list)            → int         nombre d'éléments
COUNT(list, condition)  → int         nombre d'éléments satisfaisant condition
GET_ITEM(list, index)   → any         élément à l'index donné
FIRST(list)             → any         premier élément
LAST(list)              → any         dernier élément
MAP(list, formula)      → list        applique formula à chaque élément
FILTER(list, condition) → list        garde les éléments satisfaisant condition
ANY(list, condition)    → bool        au moins un élément satisfait condition
ALL(list, condition)    → bool        tous les éléments satisfont condition
NONE(list, condition)   → bool        aucun élément ne satisfait condition
SUM(list)               → number      somme des éléments numériques
AVG(list)               → number      moyenne des éléments numériques
MIN_VAL(list)           → number      valeur minimale
MAX_VAL(list)           → number      valeur maximale
CONTAINS(list, value)   → bool        la liste contient value

-- Exemples :
-- .condition = GT(LENGTH(items), 0)
-- .condition = ALL(scores, GTE(score, 0))
-- .condition = ANY(tags, EQ(tag, "required"))


================================
6. STRING
================================

-- Opérations sur chaînes de caractères.

CONCAT(a, b)            → string      concaténation
SPLIT(str, sep)         → list        découpe selon séparateur
REPLACE(str, old, new)  → string      remplacement
MATCHES_REGEX(str, pat) → bool        correspond au pattern regex
STARTS_WITH(str, prefix)→ bool        commence par prefix
ENDS_WITH(str, suffix)  → bool        finit par suffix
CONTAINS_STR(str, sub)  → string      contient la sous-chaîne
UPPERCASE(str)          → string      en majuscules
LOWERCASE(str)          → string      en minuscules
TRIM(str)               → string      supprime espaces en début/fin
STR_LENGTH(str)         → int         longueur de la chaîne

-- Exemples :
-- .condition = MATCHES_REGEX(ident, "^[A-Z][A-Za-z0-9_]*$")
-- .condition = GTE(STR_LENGTH(name), 2)
-- .condition = STARTS_WITH(lineage, "Object:")


================================
7. STRUCTURE
================================

-- Navigation et manipulation de dicts (objets structurés).

HAS_FIELD(obj, key)     → bool        obj possède le champ key
GET_FIELD(obj, key)     → any         valeur du champ key dans obj
SET_FIELD(obj, key, val)→ obj         obj avec key = val (non-mutant)
KEYS(obj)               → list        liste des clés de obj
VALUES(obj)             → list        liste des valeurs de obj

-- Exemples :
-- .condition = HAS_FIELD(obj, "schema")
-- .condition = ISNOTNULL(GET_FIELD(obj, "ident"))
-- .condition = CONTAINS(KEYS(obj), "name")


================================
8. NAVIGATION
================================

-- Résolution de chemins dans un lineage ou une structure imbriquée.
-- Utilise la notation pointée (a.b.c) pour les chemins.

PATH_GET(obj, path)     → any         valeur au chemin donné (ex: "a.b.c")
PATH_SET(obj, path, val)→ obj         obj avec valeur posée au chemin
PATH_EXISTS(obj, path)  → bool        le chemin existe dans obj

-- Exemples :
-- .condition = PATH_EXISTS(obj, "owned_element_list.base_list.name")
-- .condition = ISNOTNULL(PATH_GET(obj, "schema"))


================================
9. USAGE EN RÈGLE (SYNTHÈSE)
================================

-- Syntaxe standard d'une règle ERK utilisant les formulas :

NomRegle IN Object:MonObjet:RuleList
  .type = validation
  .condition = FORMULE(args)
  .severity = error | warning | info
  .message = "Message si règle non respectée"

-- Exemples concrets :

HasName IN Object:Page:RuleList
  .type = validation
  .condition = AND(EXISTS(name), IS_NOT_EMPTY(name))
  .severity = error
  .message = "Le champ name est requis et ne peut pas être vide"

ValidTemperature IN Object:Agent:RuleList
  .type = validation
  .condition = BETWEEN(temperature, 0, 2)
  .severity = error
  .message = "La température doit être entre 0 et 2"

ValidIdent IN Object:Page:RuleList
  .type = validation
  .condition = MATCHES_REGEX(ident, "^[A-Z][A-Za-z0-9_]*$")
  .severity = error
  .message = "L'ident doit être en PascalCase"

HasSchema IN Object:Page:RuleList
  .type = validation
  .condition = HAS_FIELD(obj, "schema")
  .severity = error
  .message = "Tout objet doit référencer un schema"
