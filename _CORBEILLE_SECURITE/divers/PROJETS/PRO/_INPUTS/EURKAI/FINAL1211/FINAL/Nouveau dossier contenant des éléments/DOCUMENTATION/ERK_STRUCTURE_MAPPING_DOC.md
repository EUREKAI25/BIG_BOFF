# ERK — Structure Mapping & Fractal Generator
Version: 0.1 (draft)

Ce mini-langage sert à **définir la structure d’un type d’objet** (template de type), de façon
agnostique et ultra-compacte, en séparant :
- la **récursivité / composition** (`element_list`),
- l’**ancrage fractal** (où ça vit dans la double fractale),
- les **règles d’attributes** et les **valeurs par défaut**,
- les **requêtes** haut-niveau (syntaxe _query-ERK_).

Il est pensé pour être :
- lisible à l’œil nu,
- parsable automatiquement,
- suffisant pour **reconstituer la fractale** et générer les objets concrets.

---

## 1. Syntaxe de base — Définir une liste d’éléments

Forme canonique :

```text
<ParentType>.element_list = [elem1 REQUIRED, elem2, elem3 REQUIRED] IN <fractal.slot>
```

Exemple pour le DOM :

```text
html.element_list = [head REQUIRED, body REQUIRED, footer] IN view.definition
body.element_list = [header, container REQUIRED, modal, sidebar] IN view.definition
```

Signification :

- `html.element_list` : le type `html` possède une liste interne `element_list`.
- La liste contient les éléments `head`, `body`, `footer` :
  - `head` et `body` sont **obligatoires** (`REQUIRED`),
  - `footer` est **optionnel**.
- `IN view.definition` : l’ensemble de cette structure est **rattaché à la case
  `view.definition` de la double fractale** (IVC×DRO).

> Règle : on ne met ici que **l’objet le plus haut** du type (ex : `html`), le reste se déduit
> par récursivité et lineage.


### 1.1. Variante simple (sugar syntax)

On peut aussi écrire, pour documenter très localement :

```text
head IN html.element_list REQUIRED
```

C’est logiquement équivalent à une entrée correspondante dans la ligne canonique, mais **la
version canonique est celle utilisée par le parser**. La forme locale est surtout utile pour
la documentation ou les patches rapides.


---

## 2. Règles d’attributs globaux

On peut définir des règles d’attributes **transversales**, par motif :

```text
*.element_list.* ATTRIBUTE[class, id, data]
```

Signification :

- `*` = wildcard
- `*.element_list.*` : tous les éléments dans toutes les `element_list` de tous les types.
- `ATTRIBUTE[...]` : chaque élément est **autorisé** (ou encouragé) à porter `class`, `id`, `data`.

Cette règle est globale, indépendante d’un type particulier, et sera stockée dans la section
`global_attribute_rules` de la fractale générée.


---

## 3. Longueur du lineage & valeurs par défaut

Concept clé : **plus le lineage est long, plus l’objet est précis et paramétré.**

- Si on écrit simplement :

  ```text
  head IN html.element_list REQUIRED
  ```

  lorsqu’on instancie un objet de type `html` **sans fournir de détails sur `head`**, alors
  le système utilise les **templates et valeurs par défaut** de `head` (police, scripts, etc.),
  paramétrables en backoffice.

- Si on va plus loin dans le lineage, par exemple :

  ```text
  html.body.container.section.module.front
  ```

  alors on peut **surcharger ou détailler** chaque niveau : `body`, `container`, `section`,
  `module`, `front`.

> Règle ergonomique :  
> - **Lineage court** → objet généré à partir des valeurs par défaut.  
> - **Lineage long** → objet finement paramétré.  
>
> Le même principe s’appliquera à tous les types (DOM, projet, scénario, entité, module…).


---

## 4. Fractale & emplacement dans IVC×DRO

On ne mélange pas la **logique fractale** et la **logique opérationnelle**.

- La logique fractale dit : « Où vit cet objet dans IVC×DRO ? »  
  Exemple : `IN view.definition`, `IN identity.definition`, `IN context.rules`, etc.

- La logique opérationnelle dit : « Comment il se comporte ? Avec quels attributs, quelles
  méthodes secondaires, quelles formules ? »

Pour chaque type d’objet (ex : `html`, `project`, `scenario`, `entity`…), on indique **une seule
fois** dans quel slot fractal il vit, via le `IN <fractal.slot>` à la fin de la ligne.


---

## 5. Modules et dérivés

Une fois qu’on a ce template de type, on peut décliner de nombreux métatypes :
- `metaproject`
- `metatemplate`
- `metascenario`
- `metaentity`
- etc.

Tous partagent **le même schéma fractal**, seule la liste d’éléments et de sous-objets change.
On n’a donc qu’**un seul template de type fractal**, et **n** templates de structure spécifiques
par objet.


---

## 6. Requêtes ERK sur la fractale & la base de données

La syntaxe ERK de structure se prête naturellement aux requêtes.

### 6.1. Requête « objet »

- `*.element_list.*`  
  → Renvoie « tout le système » : tous les types, toutes leurs listes d’éléments, tous les éléments.

- `html.element_list.*`  
  → Tous les éléments déclarés dans `html.element_list` seulement.

### 6.2. Requête « relation-of » (RDF-like)

On avait prévu des objets de type `<objecttype>_of` pour simplifier les requêtes :

- `* invoice_of sale(BETWEEN march 2025)`  
  → Toutes les factures (`invoice`) liées à des `sale` entre mars 2025 et une date donnée.

L’idée est que, à terme, **les requêtes haut-niveau en ERK** permettent de naviguer la fractale,
les triples RDF, et les données métier avec une syntaxe unique.


---

## 7. Générateur de fractale (vue logique)

Le générateur lit un fichier `.erk` contenant des lignes du type :

```text
html.element_list = [head REQUIRED, body REQUIRED, footer] IN view.definition
body.element_list = [header, container REQUIRED, modal, sidebar] IN view.definition
*.element_list.* ATTRIBUTE[class, id, data]
```

Et produit un JSON du type :

```json
{
  "objects": {
    "html": {
      "fractal_slot": "view.definition",
      "lists": {
        "element_list": [
          {"name": "head", "required": true},
          {"name": "body", "required": true},
          {"name": "footer", "required": false}
        ]
      }
    },
    "body": {
      "fractal_slot": "view.definition",
      "lists": {
        "element_list": [
          {"name": "header", "required": false},
          {"name": "container", "required": true},
          {"name": "modal", "required": false},
          {"name": "sidebar", "required": false}
        ]
      }
    }
  },
  "global_attribute_rules": [
    {
      "pattern": "*.element_list.*",
      "attributes": ["class", "id", "data"]
    }
  ]
}
```

Ce JSON est ensuite exploitable par :
- les méthodes centrales,
- les méthodes secondaires,
- les modules (DOM, projets, scénarios, entités),
- les outils de validation, de génération et d’optimisation.


---

## 8. Mode d’emploi minimal

1. **Créer un fichier `.erk`** pour un type d’objet (ex : `erk_structure_mapping_dom.erk`).
2. Y déclarer les `*.element_list` et les `ATTRIBUTE[...]` globaux.
3. Lancer le script `erk_fractal_generator.py` en lui donnant le fichier `.erk` en entrée.
4. Récupérer le JSON généré (`*_fractal.json`) et l’injecter dans :
   - la MRG,
   - les scénarios,
   - les modules d’interface,
   - le moteur de requêtes ERK.

À partir de là, l’IA et les modules de génération peuvent **instancier soit des objets complets
(defaults), soit des objets paramétrables**, simplement en choisissant la longueur du lineage
et les éléments explicitement fournis.
