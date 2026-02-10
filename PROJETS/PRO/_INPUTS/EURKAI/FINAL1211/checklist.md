# Phase 1 — Fondations ✅ DONE

 Cockpit v27 avec parser ERK
 Catalogue 229 ObjectTypes
 Seeds 35 instances
 Bootstrap GEVR 32 instances
 Runtime GEVR avec handlers réels
 Bootstrap fonctionnel (26ms, 293 objets)


# Phase 2 — Autonomie (Maintenant)
Objectif: Le système peut créer et exécuter ses propres scénarios

Lecture fichier réelle — get:file lit vraiment les fichiers uploadés ok
Scénario CreateObject — GEVR qui crée un nouvel objet dans le store ok
Scénario ExecuteQuery — GEVR qui exécute une requête et retourne les résultats
Console GEVR — Exécuter des scénarios depuis la console


# Phase 3 — Agent Interface
Objectif: Claude peut piloter EUREKAI

API interne — Exposer executeScenario(), createObject(), query()
Prompt système — Documentation pour que Claude comprenne EUREKAI
Boucle Agent — Claude lit l'état, décide, exécute, valide


# Phase 4 — Génération
Objectif: EUREKAI génère du code/contenu réel

Templates fractals — Objets qui se transforment en output
Scénario GenerateCode — Produit du code à partir de templates
Scénario DeployArtifact — Exporte des fichiers (HTML, JS, JSON)


# Phase 5 — Multi-domaine
Objectif: EUREKAI gère plusieurs projets

Domaines isolés — Chaque projet a son catalogue
Import/Export domaines — Partager des catalogues
Orchestration multi-agents — Plusieurs agents collaborent

création complète d'un objet à partir d'un brief ou d'un schema (manifedt ?) ou cahier des charges, ou simple idée. je pensais à un lifecycle de specsDocument. On peut plus ou moins accompagner le user selon le paramétrage du projet (autonomy 0 à 100) 0, il faut tout paramétrer soi-même en fournissant les docs (tuto dispo pour les remplir),3 collaboratif : équipe d'agents + user, réunions de travail, intégration des avis client5, full autonome, x refontes possibles selon abonnement 
=> creation depuis cockpit / autonome - seeds

création de projet

# next
## cockpit
transformer cockpit en template recursif + scripts js fetch api
checkboxes pr voir seulement info, warn, alert etc ds les logs

## create
Marche 5 — Scénario CreateObject : Créer des objets via pipeline GEVR
créer objet grace à schema - get:create selon rules (autonome : assisté)
templates
produits (div sites - div formats - extensions)
redéploiement autres langages (clonage)

## prompts
agent envoie role, profile
prompt envoie la structure
projet et produit envoient context
object envoie mission
bootstrap ou strategist ou autre envoie goal

## marketing
audit site - scraping
analytics - tag manager

##  book content
livre autonome
-> erk et eurkai pour les nuls + eurkai pour les assos, eurkai pour changer le monde etc
## logs
tagger les logs pour analyse simplifiée ?

## automation
### autodeploy
déploiement local + github + from github : token + from link + token + token daté
déploiement cloud

### sandbox pour tests labo
 avec walker
## maintenance
checker doublons

## service audit avec waker
à utiliser pour maintenance - commercialisé

## extension vscode

ADD BIBI
connecté bdd
schéma de templates rcursifs puis prompt pour alimenter ces templates -> opérationnel direct
  
  seed template (html, prompt, seeds)
  seed module
  seed projet
  seed entity il leur faut des templates ?
update template (récursif ?)
suivi serveur html ?

objectif - extension pour créer des projets et seeds de produit (accès user, abonné ou sueradmin)
quelles étapes ? zéro info en dur, tut ds ctatalogue vecteurs, toute action = methde d'objet

E) Publier l'extension

Créer le README
Ajouter icône et screenshots
Publier sur VS Code Marketplace

## edition / backoffice 
IS Attribut:Prioriy.editable ds les règles pr pouvoir gérer ds le back office les listes editables par un drag&drop

## Agent API : Exposer une API JSON pour pilotage externe

## others 
Marche 5 — Persistence : Sauvegarder/restaurer l'état
Marche 5 — Watch/Triggers : Réagir automatiquement aux changements


stabilité et modularité  totale ? full dynamique ?
erk

pas  lifecycle mais options ( ex langues available/allowed rien à voir avec cycle)

# DONE

[script convert url -> dom : medias : js : css](converters/dom_extractor)
[script cnvert js -> js. light = api py (depuis script)](<converters/eurekai_modular jspy>)
script cnvert js -> js. light = api py (depuis js scrapé)
[console cockpit + schemas](eurekai-cockpit)



outil scan & do :
seeds de methodes de maintenance
VOIR logs depuis onglet avec ajout des tags (logname) par saisie semiauto pr définir ce qu'on veut voir + telecharger et enregistrer ds système



auto-correction : claude génère de nouveau fichiers en plus - fonction de compilation de datas - redéploiement des fichiers .gev (dc template de ces fichiers)

-> crons de ces méthodes
scan systeme -> fichiers à créer / corriger 

création d'objet récursif - teplate objet récursif 
tester template html, prompts, secenarios complexes via ia

tester gevr 
auto création de prompts:
- prompt central recursif
bootstrap pr autonomisation
cockpit / extension / agence elle-même ds les seeds
sécuriser au max les seeds (doubles sur double github) double serveurs et double bdd 

seeds pour créer modules (module = api)
nouveau 
- projet
- produit (site web, extension, app, livre, post)
- service (veille, audits)
- api
- template (depuis url à scrap)
- 
- 
