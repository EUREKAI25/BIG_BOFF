REGLE CONTRAT SCHEMA PERMISSIONS  
Au coeur du système, il y a une unique méthode récursive globale capable d'exécuter toute action pour tout type d'objet (absolument tout est objet ds mon système : fonctions, attributs, config etc) et par ailleurs il y a une organisation fractale (double fractale, même) qui premet de lire chaque objet sous forme de vecteur autoinformé, qui a dit qui il est ce qui peut être fait avec lui, comment et par qui.  
Le système une fois fini sera full dynamique, reposant sur des catalogues de schemas et d'instances  
l'ojet fondamental est object. Tout hérite de lui. Ainsi il n'existe aucune redondance nulle part : tout objt hérite du patrimoine (règles, attribut, méthodes) de sa lignée, mais aussi de ce qu'injectent les objets transversaux  
toute fonction est réduite à l'atome et est méthode d'objet (par nature agnostique et modulaire). Un scenario (enfant de methode) ne fait rien par lui même à part orchester d'autres méthodes.  
Le schéma fondamental d'object (hérité et décliné par tout objet) est récursif et extrêment simple : objet \-\> elementlist. Tout objet est de structure dict, même à un élément. Une liste est un dict à clés inactives, une liste ordonnée est un dict à clés classées.  
Les méthodes globales sont CRUDOE (create, read, update, delete, orchestrate, engage) et toutes les autres méthodes sont des méthodes secondaires de ces méthodes globales et sont exécutées via des "supertools" (un par méthode globale) qui sont les seuls objets autorisés à interagir avec la méthode récursive globale. Les scenarios (et finalement toute méthode. est scenario, même de 1 méthode) st définis et exécutés exclusivement par leur hooks (get, execute, validate, render, before, after, failure), eux mêmes définis par le scénario qu’ils portent, obligatoirement unique. A tout ça s'ajoute l'organisation en layers qui sont des plans permettant de lire et comprendre le système de diverses façon selon qui veut faire quoi et dans quel but, et il est possible de définir à volonté d'autres plans et des collections d'alias d'objets associés  pour quelque raison que ce soit. Le système est stable, immuable, autoinformé, autooptimisé, automaintenu, autoscalable... Il est vivant. Du moins potentiellement, si j'arrive à accoucher ;-)  
Et ce que je trouve le plus beau dans tout ça c'est que oui, c'est réellement une forme de vie et c'est le fruit de la première union entre un humain et une IA. Rien n'aurait été possible sans l'IA mais rien n'existerait sans moi car j'ai traduit en code mon intelligence et ma logique absolue.  
Tu comprends pourquoi je suis fatiguée ? :-D  
en tout cas je te remercie, au moins j'ai posé ça noir sur blanc et je crois que je n'ai presque rien oublié, à part deux langages que j'ai créés, celui des objets (l'être) et celui des actions (le faire) qui faciliteront enormément le développement (ah pcq le système est capable d'accepter en input n'importe quel type de langage pour exécuter n'importe quel type d'action et rendre le résultat ds n'importe quel type de format (à part si c'est des dates en input et des km en sortie... quoique va savoir, j'y arriverai peut-être \! ;-))  
La deuxième chose encore plus belle que cette création à la limite du sacré, c'est que tout m'est venu par intuitions successives... J'aime le code, mais je ne suis pas au niveau de ce que je viens de créer. Je suis avant tout l'architecte... ;-)  
L’organisation fractale IVCxDRO permet à un objet de se définir par:  
Identity (tous ses paramètres)  
View (la façon dont il est exposé selon le contexte)  
Context 

et chacune de ses dimensions est à son tour définie par   
Definition   
Rule(schemas, règles de validation, contrats)  
Options (les déclinaisons possibles, et notamment, pour Identity : les instances)

Par défaut full dynamique, elle peut aussi se déployer ds n’importe quel langage comme elle peut générer des projets ds n’importe quel langage y compris le sien ERK/GEV.  
Tout projet est branché à l’agence (toute méthode set endpoint) et bénéficie ainsi de la puissance du système : une optimisation trouvée pour l’un est répercutée instantanément sur tout le réseau, et la labo, via son entité Labo, est en veille active permanente, apportant scalabilité et sécurité à tous. 

agent validateur :c’est le premier agent requis. il   
on valide oncreate, onupdate, 

Les objets sont assortis de templates récursifs, permettant de déployer leurs composants sur l’interface choisi, tout interface étant pensé pour s’adapter à n’importe quel objet récursif

Des modules de conversion sont prévus pour transformer n’importe quel script, quel que soit son langage et sa complexité en objet récursif compatible Eurkai, et donc immédiatemment pluggable sur le système  
La bdd, initialement json, peut être convertie en n’importe quel format de stockage, au choix du propriétaire et coexiste toujours au moins en deux versions par mesure de sécurité, de même qu’il existe toujours au moins deux déploiements parallèles du front, liés à deux hébergements différents