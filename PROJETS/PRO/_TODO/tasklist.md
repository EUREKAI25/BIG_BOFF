OBJECTIF : CRÉER SCRIPT QUI TRANSFORME UN BRIEF EN CHANTIERS ET TACHES PUIS LES EXÉCUTE
# lister et  récupérer  les fonctions
 génériques à partir du squelette qu'on a généré, qu'on a exécuté directement sans les enregistrer dans le chat. 
 ## On récupère le squelette,
 ## on récupère après la liste des fonctions, je sais plus comment on s'y est pris, 
# fonctions python : /Users/nathalie/Dropbox/____BIG_BOFF___/__install/functions
## générer
## convertir en méthode d'objet
 ensuite on en fait des fonctions pythons, ensuite on en fait des fonctions, des objets, on rattache les méthodes à des objets, 
##  ensuite on en fait des méthodes centrales, 
## on les rattache à des méthodes centrales, on les rattache à des steps, 

# fonction de conversion
Python < SystemLanguage
fonction qui convertit python en json proprietaire et réciproquement (convert_from_json, convert_to_json)
crée fonction qui récupère les relations des json

1. on convertit le brief en projet avec steps /chantiers et steps récursives
5. on crée le zip avec chantiers zippés
2. on récupère tous les objets à créer + leurs méthodes
3. on exécute les tâches dans l'ordre (séquentiel / parallèle)
4. on vérifie pour validation

# scenario create object
get schema, execute : deploy par itérations sur elements
selon sens (up, down, lateral) on itere sur la liste de siblings dc chaque objet doit avoir siblings ds I.D.


# scan 
## ensuite on crée la méthode scan de l'objet chat, 
## la méthode scan de l'objet répertoire, 
## du coup pour l'objet système il y aura la méthode scanAndDo 
qui sera une méthode de type execute, qui prendra en get une méthode read qui sera en l'occurrence le scan qu'on vient de créer, en execute on récupère la fonction, en validate il faut que la fonction soit rattachée à une méthode centrale, à un step que les tests soient passés, et en render on enregistre la fonction dans la base de données, et dans le catalogue, du coup une fois qu'on a ça,
# catalogue
 CREER CATALOGUES
 objets à partir de brief to objects, json_to_objects
 relations à partir des json
 fonction centrale qui execute les methodes centrales (read prompt, update prompt - update doit dépendre du contexte on peut vouloir mettre à jour le contenu mais aussi le convertir en )

# bootstrap
## squelette
toute création de fonction doit commencer par un scenario squelette testé / validé puis paramétré avec des datas testées validées 
## créer bootstrap depuis brief
### fonction brief to done
### brief to chantiers
### doc to objects 
A partir d'un document, on extrait la liste des objets, on les envoie sur le catalogue, et après, on crée la fonction qui convertit n'importe quelle fonction en n'importe quel langage. En l'occurrence Python pour l'instant.

methods + 
#### brief_to tasks 
tasks
### chantiers execute
#### lister objets requis
##### getcreate objects
respect du schema.
###### method : 
- centralmethod
- stepcategory
- inputs
- outputs
- rules
- dscription
- success_validation : methodes validate à exécuter (types de validatemethod + inputs)
######  agent
- profile
- role
- type (architect, strategiist, executor, manager)
## brief botstrap
### config
 Ensuite, on peut créer la fonction Bootstrap qui est définie depuis l'Admin, avec des droits maximum. Le Bootstrap va ouvrir une page de configuration depuis laquelle on peut définir les paramètres d'hébergement, de connexion à l'administration, de connexion à l'IA, avec le choix des modèles disponibles. Ça suppose de créer l'outil Provider, l'objet prompt, l'objet... Dans un premier temps, on fait toutes ces fonctions-là
###
## edit bootstrap (admin)
parmi autres objets éditables on peut  ajuster n'importe quel scenario de n'importe quel projet
niveau superadmin requis
## execute bootstrap 
Comme ça, on peut générer le script qui permet de créer le package d'installation qui lance le bootstrap, envoie sur la page d'administration du site depuis laquelle on peut générer le projet d'agence, et par défaut, on tombe sur la page qui permet de générer un projet, on configure le projet en cours. Si c'est moi et que c'est la première installation, c'est le projet de l'agence. Et si c'est moi et que ce n'est pas la première installation, je tombe sur la page qui permet de générer n'importe quel projet. Et si c'est pas moi, on est censé avoir accès au paramètre du type de projet qui correspond aux permissions de l'utilisateur. En l'occurrence, son projet à lui, configurable ou non. 
# admin assistant
## formulaire 
## chat 
### text
### vocal
Ensuite, on prépare la page HTML, depuis laquelle on peut diffuser un outil informulaire qui va permettre de demander un brief, de pouvoir parler à l'IA qui va enregistrer le brief. 
### api 
 Ensuite, ça pourra envoyer une fonction qui va transférer le brief en chantier, et ensuite exécuter les chantiers. Tout ça sera des API, le scénario Brief-to-Task, enfin peu importe. Une fois qu'on a ça, on en fait un module qui est présent sur la page Admin. Pour tout ça, il faut qu'on s'assure que tout est bien récupéré depuis le vecteur. 
#### intégrer fonctions récupérées
## missions (=briefs)
création recursive de projets
- quel objet / projet ?
- quelle étape du projet s'il existe ? quel élément concené dans le object.elements_bundle ?
- split du projet quelles étapes ? elements / steps
- comment ça s'articule ? validation / enchainement
- planning / tasks
A partir de là, je dois avoir depuis l'admin l'outil qui permet de discuter avec mon assistant et lui envoyer un brief à l'oral ou à partir d'un document qu'on upload. Et ça, il va s'occuper tout seul de générer les chantiers, les tâches, le planning, l'exécution, et exécuter aux dates données. 
# admin
## accueil admin
 Mais aussi, depuis la page d'accueil, mes tâches les plus urgentes, avec leur état. 

## tasks admin
Donc, ça veut dire que j'ai sur mon admin la liste des tâches en cours. J'ai mon module BigBuff qui m'affiche la liste des tâches sur la page tâches.
### bigboff
générer fonctions bigboff ? retruver ce qu'on a préparé pr big boff
#### fonctions
# hooks
task.execute.after_validate
 Quand une tâche est exécutée dans les logs, l'agent va indiquer ce qu'il a fait, comment il l'a fait et pourquoi il l'a fait. 
# automation
 ## reports
 ### efficacité du système
 ### optimisation du système
 ## veille
 ## resources
 ### livres blancs
## agents
### audit_agent
 Après, on prépare un brief pour la maintenance qui sera d'aller vérifier régulièrement les nouveaux logs, les analyser, créer un rapport à un rythme qu'on peut paramétrer depuis l'admin qui va analyser l'efficacité du système, la rapidité du système, voir si c'est possible de faire mieux à travers une veille qui va récupérer des ressources pertinentes pour pouvoir évaluer son travail. On va faire une veille des outils IA disponibles pour éventuellement comparer les solutions et voir si on peut faire mieux en termes de qualité de production. Pour ça, il faut un agent qui audite, qui est compétent pour évaluer la pertinence de la réponse par rapport à la question en fonction des critères de qualité qu'on a définis par ailleurs. Pour tout ça, il me faut les schémas de prompt. Pour faire les schémas de prompt, je pense que le mieux c'est d'abord de créer les prompts, ensuite de les convertir en prompts dynamiques avec les données à injecter. Pour ces modèles de schémas de prompt à injecter, eux-mêmes dépendent d'un template plus global qui sera un objet du système.

 quel est l'objet concerné ?

 que faut-il faire avec ça ?
 - type categorie (iso, reducer, generator)
 - quelle action exécuter (getcreate) ?
 - exécuter 
 - - get recup datas concernées (inputs ou default)

ex : mettre en place un outil de veille 
thématique
sources disponibles
- options (chaines possibles)
- content (transcription, book...)