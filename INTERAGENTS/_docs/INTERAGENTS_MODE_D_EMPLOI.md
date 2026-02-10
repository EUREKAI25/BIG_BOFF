# INTERAGENTS — Mode d’emploi simple et concret

## À quoi sert INTERAGENTS ?

INTERAGENTS est un outil qui permet de lancer des tâches pilotées par une IA, de vérifier automatiquement les résultats, et de recommencer tant que le résultat n’est pas valide.

Il fonctionne **sans interface graphique** : tout se fait avec des fichiers simples et une commande dans le terminal.

---

## Où décrire ce que l’on veut faire ?

### 1 Le fichier de tâche (le “quoi” + le “comment”)

Ce que tu veux faire est décrit dans **un petit fichier JSON** appelé fichier de tâche.

📁 Emplacement :
APP/examples/

Tu peux :
- utiliser `basic_run.json`
- ou créer un nouveau fichier dans ce dossier

Ce fichier indique :
- quelle tâche lancer
- combien de fois INTERAGENTS peut réessayer
- quand considérer que le résultat est validé

---

### 2) Le fichier prompt (les instructions pour l’IA)

Le détail de ce que l’IA doit faire est écrit dans un **fichier texte** appelé *prompt*.

📁 Emplacement :
APP/prompts/

Exemple existant :
prompts/noop.md

Ce fichier explique clairement à l’IA :
- ce qu’elle doit produire
- sous quelle forme
- sans poser de questions

---

### Lien entre les deux

Le fichier JSON pointe vers le fichier prompt grâce au champ :
prompt_path

👉 Le JSON dit **comment lancer la tâche**  
👉 Le prompt dit **quoi faire exactement**

---

## Est-ce qu’il existe déjà une interface ?

Non.

Pour l’instant :
- pas d’interface graphique
- pas de formulaire
- pas de dashboard

L’interface, c’est :
- les fichiers dans `examples/` et `prompts/`
- le terminal

---

## Comment utiliser INTERAGENTS concrètement (pas à pas)

### Étape 1 — Écrire le prompt

Tu crées ou modifies un fichier dans :
APP/prompts/

---

### Étape 2 — Créer ou modifier un fichier de tâche

Tu crées ou modifies un fichier dans :
APP/examples/

Tu relies ce fichier au prompt avec `prompt_path`.

---

### Étape 3 — Lancer la tâche

Depuis le dossier APP :
interagents run examples/nom_du_fichier.json

---

## Que fait INTERAGENTS tout seul ?

Pendant l’exécution, INTERAGENTS :

1. appelle l’IA  
2. reçoit une réponse  
3. vérifie si le résultat est acceptable  
4. recommence si nécessaire  
5. s’arrête uniquement quand c’est validé  
6. garde un historique complet  

---

## Où sont stockés les résultats ?

Tout est enregistré automatiquement dans :
APP/workspace/

- runs/ : historique détaillé  
- outputs/ : fichiers produits  
- state/ : état interne  

---

## Comment savoir si une tâche a réussi ?

À la fin :
- le terminal affiche success ou failed
- le nombre d’itérations est indiqué
- les fichiers générés sont listés

Commande utile :
interagents status ID_DE_LA_TÂCHE

---

## En résumé

- Tu écris **ce que tu veux** dans un prompt
- Tu décris **comment l’exécuter** dans un JSON
- INTERAGENTS exécute, vérifie, recommence
- Les résultats sont stockés automatiquement
