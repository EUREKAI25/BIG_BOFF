# ERK v1 — Langage Officiel Eurkai

Version minimale, opérationnelle, complète pour écrire règles, méthodes, transformations et logiques internes.

---

## 1. Objectif

ERK est le langage logique d’Eurkai. Il sert à :
- exprimer des règles (must / must_not / when … then …)
- décrire des méthodes (method …)
- définir des formules (formula …)
- écrire des diagnostics et des conditions
- être lisible par un humain, interprétable par une IA, exécutable par le système.

ERK n’est pas limité aux “règles” : les fonctions écrites par les agents,
et le code logique des développeurs, peuvent être exprimés en ERK.

---

## 2. Référencer un objet

On utilise la nomenclature lineage :

```text
Type:SubType.Attribute
Type:SubType.Method()
Vector:Something.state
```

Exemples :

```text
Object:Prompt.role
Object:Prompt.build()
Project:Website.version
Vector:RuleSet.state
```

---

## 3. Littéraux

```text
"texte"
12
0.7
true / false
["a", "b", "c"]
Status:Valid
```

---

## 4. Logique de base

Opérateurs :

```text
=       égal
!=      différent
> < >= <=
in      appartient
not_in  n’appartient pas
contains  contient
```

Connecteurs :

```text
and
or
not
```

---

## 5. Types de lignes ERK

### 5.1. Règles globales

```text
must <expression>
must_not <expression>
```

- `must expr`    → expr doit être vraie
- `must_not expr` → expr doit être fausse

Exemples :

```text
must Object:Prompt.role in ["system","user","assistant"]
must_not Object:Response.contains_hallucination
```

### 5.2. Conditionnel

```text
when <condition> then <effet>
```

Exemples :

```text
when Object:Prompt.role = "system"
then Object:Prompt.context != ""
```

```text
when Object:Response.score < 0.7
then SuperEngage.diagnose(Object:Prompt, Object:Response)
```

### 5.3. Méthodes

Une méthode est un bloc nommé, attaché à un objet.

```text
method Object:Prompt.build() =
    steps:
        - compute context
        - merge role
        - validate rules
    returns Object:Prompt.final
```

Méthode minimaliste conditionnelle :

```text
method Project:Website.deploy() =
    when config.valid
    then system.execute(deploy_script)
```

### 5.4. Formules

```text
formula Response.score =
    SuperEngage.rate(content, objective)
```

---

## 6. Diagnostic et qualité IA

Exemple complet :

```text
must_not Object:Response.contains_hallucination

when Object:Response.score < 0.7
then SuperEngage.diagnose(Object:Prompt, Object:Response)
```

Puis la méthode associée :

```text
method SuperEngage.diagnose() =
    steps:
        - analyze mismatches
        - identify_missing_context
        - identify_unclear_objective
        - suggest_refine
    returns Diagnosis
```

L’implémentation réelle (Python/JS) peut vivre ailleurs ; ERK fournit
la grammaire logique et les contrats.

---

## 7. Commentaires

Commentaires simples :

```text
# Ceci est un commentaire ERK
```

---

## 8. Bonnes pratiques

- Garder les lignes relativement courtes et structurées.
- Toujours référencer les objets via leur lineage complet.
- Ne pas multiplier les synonymes : un même concept = un même nom.
- Centraliser les règles par domaine logique (Prompt, Response, Project…).
- Utiliser ERK pour décrire les décisions, pas les détails d’implémentation.

---

## 9. Exemple de fichier ERK complet

```erk
# ERK:PROJECT_WEBSITE_RULES
# Règles principales pour Project:Website

must Project:Website.status in ["draft","live"]

when Project:Website.status = "live"
then Project:Website.url != ""

must_not Object:Response.contains_hallucination

when Object:Response.score < 0.7
then SuperEngage.diagnose(Object:Prompt, Object:Response)

method Project:Website.deploy() =
    when config.valid
    then system.execute(deploy_script)

formula Response.score =
    SuperEngage.rate(content, objective)
```

---

Fin de la notice ERK v1.
Cette version est suffisante pour commencer à écrire
toutes les règles, méthodes et formules de base d’Eurkai.
