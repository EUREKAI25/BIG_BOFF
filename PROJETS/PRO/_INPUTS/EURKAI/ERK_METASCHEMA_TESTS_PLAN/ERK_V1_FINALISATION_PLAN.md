# ERK v1 → v1.1 / v2 — Plan de finalisation

Objectif : passer d’un ERK « utilisable » à un ERK « stable », documenté, testable, pour qu’IA + humains puissent l’utiliser sans ambiguïté.

---

## 1. Lexique et mots-clés

### 1.1. Mots-clés réservés (à figer)
- `must`, `must_not`
- `when`, `then`
- `and`, `or`, `not`
- `in`, `not_in`, `contains`
- `method`, `formula`
- `returns`, `steps`
- `true`, `false`
- `null` (optionnel)
- types spéciaux : `Status:`, `Vector:`, etc.

### 1.2. Décisions à prendre
- Liste exhaustive des mots-clés v1.1
- Décider si l’on autorise d’autres formes : `elif`, `else`, etc. (recommandation : NON en v1.1)
- Décider si les booléens sont toujours implicites (ex : `must_not Flag.xyz`) ou si on autorise aussi `= true` par compatibilité.

---

## 2. Grammaire minimale

### 2.1. Types de lignes ERK

1. Règle globale :
   - `must <expression>`
   - `must_not <expression>`

2. Conditionnel :
   - `when <condition> then <effet>`

3. Définition de méthode :
   - `method <Object:Type.method()> =`
   - bloc `steps:` ou conditionnel

4. Définition de formule :
   - `formula <Nom> = <expression>`

5. Commentaire :
   - `# commentaire`

### 2.2. À figer
- Structure exacte d’un fichier ERK :
  - titre + description en commentaire
  - puis blocs de règles / méthodes / formules

Exemple de squelette :

```erk
# ERK:PROJECT_WEBSITE_RULES
# Règles principales pour Project:Website

must Project:Website.status in ["draft","live"]

when Project:Website.status = "live"
then Project:Website.url != ""

method Project:Website.deploy() =
    when config.valid
    then system.execute(deploy_script)

formula Response.score =
    SuperEngage.rate(content, objective)
```

---

## 3. Intégration au MetaSchema

### 3.1. Objet ERKRule

À prévoir dans le MetaSchema :
- `Object:ERKRule`
  - attrs : `id`, `name`, `scope`, `priority`, `source_file`, `line`, `enabled`
  - rels : `depends_on` (autres règles), `related_to` (objets ciblés)
  - methods : `validate()`, `apply()`, `diagnose()`

### 3.2. Objet ERKScript (fichier complet)
- `Object:ERKScript`
  - attrs : `name`, `description`, `version`, `content`
  - rels : `element_of` : RuleSet, Scenario, Module, SuperTool

---

## 4. Catalogue des types de règles

Lister explicitement :
- Règles de **structure** (attributs requis, types, etc.)
- Règles de **comportement** (méthodes, transitions)
- Règles de **sécurité**
- Règles de **qualité IA** (score, hallucinations, etc.)
- Règles de **dépendances** (ordre d’exécution, prérequis)

Décider :
- quelles familles existent en v1.1
- comment on les nomme : `Rule.Structure.*`, `Rule.Security.*`, etc.

---

## 5. Stratégie de tests ERK

Prévoir :
- un set minimal de fichiers ERK d’exemple
- un validateur ERK (syntaxe + sémantique de base)
- des cas de test :
  - règles valides
  - règles invalides
  - diagnostics attendus

Livrables :
- `ERK_TESTS_MINIMAL.md`
- `examples/erk/` avec 3–5 fichiers de référence.

---

## 6. Convention pour les fonctions et le code en ERK

Décider :
- comment on écrit les corps de méthode (simple ou pseudo-code)
- si ERK doit rester purement déclaratif en v1.1 (recommandé)
- ou si on autorise des expressions opérationnelles plus poussées

Recommandation v1.1 :
- ERK = déclaratif / logique
- Le code impératif (Python/JS) vit ailleurs mais peut référencer ERK pour les contraintes et les décisions.

---

## 7. Étapes concrètes

1. Geler la liste des mots-clés v1.1
2. Finaliser la syntaxe des 4 types de lignes ERK
3. Créer les objets `ERKRule` et `ERKScript` dans le MetaSchema
4. Écrire un ou deux fichiers ERK de référence (Prompt, Response, Project)
5. Définir un premier validateur ERK (même manuel)
6. Relier ERK aux SuperTools (SuperEngage notamment) par des règles standard.

Une fois ces étapes validées, ERK peut être considéré comme **stabilisé v1.1**, prêt pour écriture de règles et de méthodes.
