# __LAYER 0__RELATIONS

## 0. Rôle de cette note

Cette note fixe **la liste des relations autorisées** dans la fractale ERK
(au niveau runtime) et la manière dont certaines relations sont **dérivées**
à partir de la structure (`element_list`).

Elle sert de référence canonique pour tout le système.

---

## 1. Les 3 relations primitives

Au runtime, on n’utilise que **3 relations primitives** :

1. **related_to(A, B)**  
   - Lien sémantique “général” entre deux objets.  
   - Relation faible, potentiellement symétrique selon le contexte.  
   - Sert à exprimer “A est lié à B” sans notion de dépendance stricte.

2. **depends_on(A, B)**  
   - A **a besoin** de B pour exister ou fonctionner correctement.  
   - Directionnelle : `depends_on(A, B)` ≠ `depends_on(B, A)`.  
   - Exemple : `Website:Eurekai_website depends_on Project:Eurekai`.

3. **inherits_from(A, B)**  
   - A **hérite** de B (lignée).  
   - Sert à construire la chaîne qui permet de résoudre :
     - les attributs,
     - les bundles,
     - les comportements,
     en remontant dans la lignée en cas d’absence de valeur locale.

> 🚫 Il n’existe pas de `instance_of` au runtime :  
> la lignée se fait par `inherits_from`.

---

## 2. Relation dérivée : element_of

La relation **element_of** n’est **pas** une primitive.  
Elle est **dérivée** de la structure fractale via `element_list`.

**Règle dérivée canonique :**

```text
IF A IN B.element_list
THEN A element_of B
