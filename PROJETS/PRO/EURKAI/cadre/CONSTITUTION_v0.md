EURKAI — CONSTITUTION v0

--------------------------------
0. Convention de nommage
--------------------------------

- Objets → PascalCase
- Attributs / Méthodes / Règles → snake_case
- Un nom ne peut être affecté qu’à un seul type d’objet


--------------------------------
1. Axiomes fondamentaux
--------------------------------

A1. Tout est objet.

A2. Tout objet est un dict.

A3. Tout objet est un container.

A4. Tout objet possède une elementlist.

A5. elementlist peut être vide.

A6. Seul l’objet racine n’appartient à aucun container.

A7. Tout objet non racine appartient à exactement un container.


--------------------------------
2. Structure fondamentale
--------------------------------

Schéma fondamental :

object = dict = container → elementlist

- elementlist contient des objets
- chaque objet est lui-même container et possède sa propre elementlist
- la structure est récursive


--------------------------------
3. Structures
--------------------------------

Structure
→ Dict
→ List

- Dict = structure clé → valeur
- List = dict spécialisé à clés actionnables
- List peut être ordonnée ou non (via attribut order)


--------------------------------
4. Composition (lecture structurelle)
--------------------------------

- container
- elementlist

Remarque :
Le terme organizationelement est utilisé provisoirement pour désigner les éléments liés à cette logique.


--------------------------------
5. Objets de cadrage
--------------------------------

Rule
→ Schema

Field

Attribute
Relation
Option

Kind (provisoire)


--------------------------------
6. Exécution
--------------------------------

Function
→ Method

- Method = mission exécutée via une function du même nom
- Les méthodes appartiennent à l’objet qu’elles manipulent ou décrivent

Scenario

- Scenario ne s’exécute pas lui-même
- Il définit une séquence de méthodes
- Cette séquence est destinée à être convertie en hooks/triggers


--------------------------------
7. Attributs fondamentaux
--------------------------------

name
description
example
version
ident

goal (optionnel)

value
default_value


--------------------------------
8. Attributs qualifiants
--------------------------------

order
size
count


--------------------------------
9. Types simples
--------------------------------

string
int
number
bool


--------------------------------
10. Règles globales
--------------------------------

- Un objet a 0 ou 1 container (0 uniquement pour la racine)
- Tout objet possède une elementlist
- elementlist peut être vide
- Un nom correspond à un seul type d’objet
- kind est temporaire (remplacé plus tard par la lignée)
- Les règles de schéma cadrent les structures autorisées
- Les méthodes portent l’exécution, les objets ne s’exécutent pas eux-mêmes


--------------------------------
11. Objets métier initiaux
--------------------------------

Palette

Méthodes associées :
- create
- generate
- update
- decline
- validate


--------------------------------
12. Remarques d’implémentation
--------------------------------

- Les objets métier non existants peuvent être créés dynamiquement via scénario de type get_create
- Les structures sont manipulées par ident, donc les noms peuvent évoluer sans impact
- Les hooks (before, execute, validate, etc.) seront introduits ultérieurement