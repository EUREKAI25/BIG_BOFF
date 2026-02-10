# 🧩 Prompt Claude — Catalogue ERK structurel (sans instances)

## 🎯 OBJECTIF
Produire un **catalogue ERK structurel** qui décrira :
- comment sont modélisés les objets ERK dans le système (règles, méthodes, formules, diagnostics, etc.),
- comment le cockpit peut les lister, filtrer, et utiliser,
- **sans créer d’instances métier concrètes** (pas de SuperCreate, pas de Projets réels, etc.).

L’objectif est d’avoir une base 100 % agnostique sur laquelle je pourrai,
plus tard, créer moi-même toutes les entrées réelles via le cockpit.

Le langage à utiliser pour les règles internes reste **ERK**, tel que défini
dans `ERK_SPEC_COMPLETE.md`.

---

## 📌 CONTRAINTES FONDAMENTALES

1. **Aucune création d’objets métier concrets.**
   - Tu peux définir des *types* génériques (Rule, Method, Formula, Diagnostic, CatalogueEntry, etc.).
   - Tu ne dois pas créer d’objets tels que : SuperCreate, SuperRead, ProjetX, ModuleY, etc.
   - Tu peux fournir 1–2 exemples génériques, mais ils doivent être présentés comme *exemples pédagogiques*, pas comme des données initiales obligatoires.

2. **MetaSchema agnostique.**
   - Le catalogue décrit la *structure* des entrées (champs, types, contraintes ERK).
   - Il ne préjuge pas de la liste future des objets.
   - Tous les objets réels seront créés **uniquement via le cockpit**.

3. **Compatibilité avec ERK_SPEC_COMPLETE.**
   - Les champs, types, et règles doivent être cohérents avec la spécification ERK (grammaire, mots-clés, standard library).

---

## 🧱 CE QUE TU DOIS PRODUIRE

Tu dois produire un fichier **ERK_CATALOGUE_SCHEMA.md** qui décrit :

### 1. Les types d’entrées du catalogue

Par exemple (à ajuster / compléter si nécessaire) :

- `Catalogue:RuleDefinition`
- `Catalogue:MethodDefinition`
- `Catalogue:FormulaDefinition`
- `Catalogue:DiagnosticDefinition`
- `Catalogue:TransformDefinition`

Chaque type doit avoir :

- un `id` interne,
- un `name` humain lisible,
- une `category` (rule / method / formula / diagnostic / transform),
- un `erk_id` (identifiant ERK canonique : p.ex. `rule.validation.name_required`),
- un champ `erk_code` (le bloc ERK lui-même),
- des `tags`,
- des `relations` (depends_on, related_to, inherits_from),
- des métadonnées (version, status, createdAt, updatedAt, author, etc.).

### 2. La structure d’une entrée de catalogue

Pour chaque type d’entrée, tu dois décrire précisément :

- les champs obligatoires,
- les champs optionnels,
- les règles ERK de validation internes (ex : un RuleDefinition doit avoir un `erk_code` non vide, un `erk_id` unique, etc.).

Donne cette structure *de façon canonique*, comme une sorte de “schema ERK des catalogues”.

### 3. Règles ERK associées au catalogue

Tu dois écrire les règles ERK de base qui garantissent l’intégrité du catalogue, par exemple :

- unicité de `erk_id`,
- cohérence entre `category` et le type de bloc ERK (rule / method / formula / diagnostic),
- obligation d’avoir un `erk_code` syntactiquement valide,
- impossibilité de supprimer une entrée encore référencée par d’autres objets (via depends_on / related_to).

Ces règles doivent être écrites en ERK, en cohérence avec `ERK_SPEC_COMPLETE.md`.

### 4. Quelques exemples pédagogiques (mais pas prescriptifs)

Fournis 2 ou 3 exemples de lignes de catalogue sous forme JSON-like
pour illustrer comment une entrée de type RuleDefinition ou MethodDefinition
serait stockée, mais :
- indique bien dans le texte que ce sont **des exemples pédagogiques**,
- précise que **le système réel démarrera avec un catalogue vide**, que je remplirai via le cockpit.

---

## 📤 LIVRABLE ATTENDU

Un fichier unique : **ERK_CATALOGUE_SCHEMA.md**, structuré comme une documentation technique officielle, comprenant :

1. Une vue d’ensemble du rôle du catalogue ERK.
2. La liste des types d’entrées de catalogue.
3. Le détail des champs pour chaque type.
4. Les règles ERK d’intégrité du catalogue.
5. Quelques exemples pédagogiques (marqués comme tels).

Le tout **sans aucun objet métier concret** figé.
