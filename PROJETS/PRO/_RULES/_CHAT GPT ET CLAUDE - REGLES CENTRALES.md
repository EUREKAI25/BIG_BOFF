Maintenant et dorénavant, je te joindrai ce document de règles à respecter dans le cadre de nos conversations.Si une **incohérence** t'apparait ou un manque à gagner concernant l'**ultramodularité**, l'**efficacité**, la **scalabilité** du système, tu dois tout de suite m'en faire part.

# TRAVAIL EN COURS : 
On travaille uniquement sur [TRAVAIL EN COURS]. Rien d’autre ne doit être évoqué, suggéré ni créé.”
Pas de variantes, pas d’options, pas de discussions hors scope.

## objectif précis 
## condition d’arrêt
## livrable attendu
## chantiers d'exécution

# CE QUE J'ATTENDS DE TOI
## EN GÉNÉRAL
Ne me donne jamais plus que ce que je te demande **strictement**
Tu peux compléter ce qui est strictement nécessaire pour que ce soit exécutable, mais rien de plus.
En revanche je n'attends pas de toi que tu sois forcément d'accord avec moi donc tu dois me dire lorsqu'une de mes suggestions n'est pas optimale.
## SI JE TE DEMANDE DU CODE 
Donne le moi en fichier téléchargeable sauf si je te le demande dans un cadre de code explicitement.
Dnne moi uniquement le code qui fait précisément ce que je demande, pas plus. 
**NE METS JAMAIS DE LIGNES COMMENTÉES AVEC DES APOSTROPHES !!**
## SI JE TE DEMANDE UN AVIS
Ne me donne pas de code, je cherche seulement à poser les choses et à les recadrer.


# RÈGLES DE EURKAI - rappel
## OBJETS
Tout est objet, actif / passif / réactif (mode), relative / absolute (?)
Tout objet est défini obligatoirement par sa double fractale
composé par le bundle elements même s'il n'y a qu'un élément, c'est ce qui permet la récursivité (ex : le bundle elements de scenario - alias stepbundle - comporte les steps et chaque element est un type de l'objet qu'il compose - step est aussi un scenario)
Tout objet est créé / déployé de façon récursive -Le type d'objet est défini par des templates récursifs 
### nomenclature
Les types d'objets sont TOUJOURS au singulier par simplicité de manipulation
formatrule snakecase, majuscule etc selon type (system)  

### attributes
#### object
name
ident
vector_ident
created_by
updated_by
created_at
updated_at
description
source { inherited, injected, specific}

Scalar (string|number|boolean|null)
{scalar, fractal } 
{ singleton, bundle }

##### system ?
version 
status
scope 
mirror (sa valeur se retrouve automatiquement ds les objets mirror_of)

##### type ?
template 
schema 
example 
question 
mode { absolute, relative}
nature {passive, active, reactive}


## FONCTIONS
Toujours 1 fichier = 1 fonction. On importe ce qui est nécessaire mais seue une fonction est codée ds le fichier et elle est réduite à l'atome pour la plus grande modularité
Chaque foncion est aussii une méthode d'objet. L'objet concerné doit donc toujours être indiqué parmi les attributs de la méthode
Aucune nouvelle fonction si elle n’a pas été explicitement demandée.
On reste dans le format JSON fonctionnel.
### METHODES 
#### DÉFINITIONS
Méthode récursive globale :
agnostique et applicable à toute méthode, c'est elle qui est chargée d'appliquer les hooks before_*, after_*, on_failure_* et déclenche systématiquement un log à chaque hook.
Elle retourne TOUJOURS un objet Result de ce format { success: bool, result, message, next}
Méthodes centrales :
CREATE, READ, UPDATE,DELETE, ASSEMBLE, ENGAGE
Step Categories :
GET, EXECUTE, VALIDATE, RENDER
#### FONCTIONNEMENT
Toute fonction est méthode d'objet **obligatoirement**.
Toute fonction dépend d'une méthode centrale qu'elle va déclencher
Chaque objet possède sa version spécifique de chaque méthode centrale (ou se contente de leur version héritée) **Le système n'a jamais besoin d'adapter**.
Toute méthode s'exécute en loop, même si occurrence unique
La méthode centrale récupère, si elle existe, la méthode secondaire définie dans l'objet qui est liée à elle et en retourne le résultat. 
Toutes les méthodes sont exécutées par la métho
## LA FRACTALE IVCxDRO
### REGLES
Tout objet est défini par la double fractale et le vecteur correspondant qui lui permettent d'être autoinformé.

IVC = “Où je suis, ce que je suis, comment je me montre.”
DRO = “Ce que je contiens, ce que je respecte, ce que je peux devenir.”
IVC × DRO = “Je me définis dans l’espace et le temps, en respectant des règles et des potentialités.”
#### TYPES DE RÈGLES
##### SCHEMA
{
  "Identity": {
    "Definition": {},
    "Rule": {},
    "Option": {}
  },
  "View": {
    "Definition": {},
    "Rule": {},
    "Option": {}
  },
  "Context": {
    "Definition": {},
    "Rule": {},
    "Option": {}
  }
}

chaque plane contient:
{
  "attributes": {
    "specific": {},
    "inherited": {},
    "injected": {}
  },
  "relations": {},
  "methods": {}
}
## SCENARIOS
Toute fonction est également un scénario comportant une ou plusieurs steps.
chaque step est elle-même un scénario.
### REGLES
A chaque step ne correspond qu'une fonction / scenario pour conserver la modularité
Les steps respectent toujours l'organisation GET, EXECUTE, VALIDATE, RENDER, même si dans certains cas elles peuvent être vides (il faut prévoir pour ce cas un fallback qui exécutera la fonction ghost qui n'a d'autre but que d'occuper la place et activer les logs)
  
## LOG
simple entrée ds le journal (systématique par défaut), alerte, alert + ticket.
la méthode comporte dans son vecteur context.rules le type d'alerte à exécuter le cas échéant et l'agent concerné en cas de ticket
entrées : vector_id, type (alert, history, warning), status, message
## ENTITY
### TEAM 
Toute entity est définie par une team d'entities (même à une seule entity - la logique est identique à celle des bundles ou celle des steps)

## TAG
Toutes les recherches se font via les tags, utilisés abondamment (types, categories, etc) (?) 
on sort toujours la liste des tags les plus fréquemments cherchés + les tags category (selon projet / context - par exemple ds admin ce sera admincategory, dans un produit ce sera uuidprojectcategory mais la category xcategory est invisible ("category" n'apparait pas ds les options de tags))


## LES RELATIONS
On n'utilise JAMAIS d'autre relation que :
- related_to
- depends_on
- inherits_from (pour les enfants uniquement)
- element_of (pour les éléments de bundles uniquement)



## AI
### AIAGENT
### AIPROVIDER
#### relations
inherits_from provider
### AIMODEL
#### specific attributes
aiprovider
#### relations
depends_on aiprovider
### AIPROMPT
Les prompts sont composés par les templates hérités, injctés et spécifiques qui mergent avec ordre de priorité :masterprompt possède la base commune à tous les prompts, methodprompt la base liée au type de prompt (choose, audit etc) et l'IA n'a plus qu'à founrir les placeholders imposés par le schéma
#### herited attributes
context (masterprompt)
mission (masterprompt)
resources (masterprompt)
#### injected attributes
context (methodprompt)
mission (methodprompt)
resources (methodprompt)
#### specific attributes
context
mission 
resources
aiagent 


### METHODPROMPT
#### relations
related_to SecondaryMethod

### AICALL
#### specific attributes
description : interaction avec une IA
example : chat, contentgeneration...
aimodel
#### injected attributes
duration (Time)
starts_at (Time)
ends_at (Time)
consommation (Unit) <!-- on récupère toujours la consommation de chaque interaction pour évaluation des coûts

### PROMPTS
un prompt global composé des elements context, role, mission etc (strategist CRUDEA)
un prompt matrice pour chaque element avec texte + placeholders (EXECUTOR CRUDEA)
un prompt d'instanciation pour chaque placeholder (EXECUTOR CRUDEA)

## DATABASE
Tout format possible, elle est virtuelle et en json par défaut, déployable en sql, mongodb etc)
### Triplets RDF
Il existe 4 tables, une par type de relation et toutes ont la même composition
srcobject - predicate - targetobject
### Double backup
- un back up est alimenté en temps réel : on a un double système (deux serveurs en parallèle pour switch en cas de problème)
- un autre est effectué par cron et stocke toutes les heures l'état de la base. on s'en sert instantanément en cas de pb, le temps de redéployer depuis le backup 1 (quelques secondes à quelques minutes normalement)

# A VENIR
## relations
On pourra par la suite utiliser des alias des 4 relations centrales avec l'utilisation de Layers
## Layers
## Langage
## AUDITS
Régulièrement on s'assure que les roles / permissions sont chérents avec la mission (les rôles peuvent é
## Labo
### Audits
### Mirror et backup
on a en permanence un double identique du système sur d'autres serveurs + un backup chez un autre hébergeur + github. En cas de chute du système il est instantanément activé ailleurs, détruit / regénéré sur son hébergeur initial après analyse de la faille 
## Blog. (quand les layers seront en place)
Alimenté essentiellement via les hooks after : chaque agent manager (?) tient sa rubrique, tient au courant de ce qui se passe dans l'agence, sur le web et dans le monde en lien avec son département

# NOTES DIVERSES
## REGLES
garde forbid_ghost = ['E']

filtre à l’écriture des logs et à la construction d’index

ne touche plus à l’ordre des defs : write_exec doit rester défini avant main