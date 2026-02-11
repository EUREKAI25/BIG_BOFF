# NOTE — ASSISTANT EURKAI (Input libre + Upload + Dialogue IA)
# Version conceptuelle — à intégrer après l’étape G

## 1. Objectif
Offrir dans le Cockpit un point d’entrée unique permettant :
- de saisir un texte libre (idée, besoin, intention)
- de charger un fichier (brief, cahier des charges, JSON, manifest…)
- de dialoguer avec une IA pour clarifier le besoin
- puis de déclencher automatiquement le scénario adapté
- tout en préservant le contrôle total de l’utilisateur (aucune action automatique sans validation)

L’Assistant Eurkai est l’interface humaine la plus haute du système.
Il ne crée rien lui-même : il transmet l’intention à Orchestrate.

---

## 2. Structure (3 onglets)
L’Assistant Eurkai comporte trois zones fonctionnelles :

### Onglet A — INPUT LIBRE
> « Saisis une idée ou charge un document. »

Contenu :
- Champ texte simple  
- Bouton “Charger un fichier”
- Types supportés : .txt, .md, .pdf (texte), .json, .yaml, .erk, .docx
- Bouton “Envoyer à Orchestrate”

Rôle :
- Transmettre l’input brut à `Super.orchestrate(input)`  
- Ne jamais interpréter localement

---

### Onglet B — DISCUSSION IA
> « Dialogue pour affiner l’idée avant génération. »

Fonctionnement :
- Mini-chat intégré
- L’IA ne peut que clarifier, proposer, reformuler
- Mode strictement **read-only** vis-à-vis du Core (aucun write)
- Un bouton “Générer à partir de cette conversation”

Rôle :
- Produire une version « clarifiée » ou « validée » de l’idée
- Ne rien exécuter tant que l’utilisateur n’appuie pas sur “Générer”

---

### Onglet C — HISTORIQUE
> « Visualise les inputs passés et leurs résultats fractaux. »

Contenu :
- Liste chronologique des input → scénarios exécutés
- Aperçu fractal des objets créés ou modifiés
- Possibilité de recharger un input pour le réexécuter
- Journal de tous les retours GEVR
- Affichage du “diff fractal” pour chaque action

Rôle :
- Tracer toute l’activité de création
- Offrir un mécanisme transparent de versioning humain

---

## 3. Pipeline d’exécution (simple et strict)
Le Cockpit n’exécute jamais rien.  
Il appelle **toujours la même commande** :

```
Super.orchestrate({
    input: <texte|fichier|conversation_finale>
})
```

Étapes internes (contrôlées par EURKAI) :
1. Analyse de l’intention  
2. Choix du MetaScénario approprié  
3. Exécution GEVR :  
   - GET  
   - EXECUTE  
   - VALIDATE  
   - RENDER  
4. Retour structuré au Cockpit  
5. Affichage immédiat de la fractale (lecture seule)  
6. Validation par l’utilisateur avant toute mise à jour réelle

---

## 4. Règles fondamentales
- Le cockpit **ne modifie rien** : il ne fait qu’afficher et transmettre.  
- L’IA ne peut **modifier la fractale** qu’en passant par GEVR + SuperTools.  
- Aucune action IA n’est exécutée sans **validation explicite**.  
- Le système doit toujours pouvoir **justifier** :  
  - le scénario choisi  
  - la structure générée  
  - les règles appliquées  
  - les validations effectuées  
- Toute création doit être représentée sous forme de **fragments fractaux complets**.

---

## 5. Bénéfices structurels
- Entrée unique pour tous les types de demandes  
- Intégration universelle : projets internes, nouveaux services, stratégies, modules  
- Pipeline minimaliste : un seul appel pour tout scénario  
- Complètement aligné avec :  
  - MetaSchema  
  - MetaRules  
  - MetaScénario Projet EURKAI  
  - SuperTools  
  - GEVR  
- Maintien du contrôle humain absolu  
- Extensible sans modifier aucun Layer

---

## 6. Vision finale
À terme, l’Assistant Eurkai devient :
- l’espace où une idée brute devient un projet complet  
- l’espace où un besoin devient une fonctionnalité  
- l’espace où une intention devient une structure fractale  
- l’espace où un texte devient un produit EURKAI déployé

C’est le point d’entrée naturel de tout processus créatif dans l’agence.
