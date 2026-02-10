
# INTERAGENTS — Note d’orchestration (humaine, dernière fois 🤞)

Cette note est **pour toi**, pas pour les agents.
Elle décrit **l’organisation des chantiers**, leur **ordre d’exécution**, les **ressources nécessaires** et **les règles de jeu** pendant que **TU joues l’orchestrateur** (une dernière fois, si tout va bien).

---

## 1. Objectif global

Mettre en place un système **minimal mais fiable** permettant à des IA :
- de générer **du code Python autonome** (module ou projet),
- de s’auto‑organiser par chantiers,
- de s’auto‑corriger via tests,
- sans te solliciter sauf **blocage réel**.

Aucun objectif produit / business ici.
Uniquement : **fiabilité + automatisation**.

---

## 2. Organisation générale des chantiers

### Vue d’ensemble

L’exécution est organisée en **3 groupes** :
- Groupes **séquentiels** : dépendances fortes
- Groupes **parallèles** : travail indépendant

---

### GROUPE G1 — Séquentiel (fondations conceptuelles)

1. **C01 — Requirements & Acceptance Contract (planner)**  
   → Définir précisément :
   - ce que le système doit faire
   - ce que “réussi” veut dire
   - les contrats JSON agents
   - les seuils de validation

2. **C02 — Prompt Dictionary & Dispatch Model (planner)**  
   → Définir :
   - le dictionnaire de prompts interne
   - la logique de dispatch (séquence / parallèle)
   - la gestion du contexte
   - la logique de questions vers l’orchestrateur

➡️ **Rien de technique ne commence avant la fin de G1.**

---

### GROUPE G2 — Séquentiel (implémentation cœur)

3. **C03 — Core Orchestrator Skeleton (coder)**  
   → Implémenter :
   - `run_job()` (API Python)
   - CLI `if __name__ == "__main__"`
   - gestion d’un workspace par run
   - stockage de l’état (JSON disque)
   - dispatch vers AgentAdapter (mock au départ)

4. **C04 — Question Routing (ask_orchestrator)**  
   → Implémenter :
   - questions agent → orchestrateur
   - réponse uniquement si certitude 100%
   - escalade vers toi uniquement si incertain
   - états : RUNNING / WAITING / NEEDS_USER_INPUT

5. **C05 — Python Runner + Validation Loop**  
   → Implémenter :
   - écriture des fichiers générés
   - exécution `pytest`
   - capture stdout / stderr
   - boucle de correction :
     - max iterations
     - `passes_in_a_row` (2 par défaut)

➡️ À la fin de G2, le système **fonctionne techniquement**.

---

### GROUPE G3 — Parallèle (une fois G2 terminé)

6. **C06 — Tests Orchestrateur & Runner (tester)**  
7. **C07 — Exemples & Documentation (reviewer)**  

➡️ Ces deux chantiers peuvent être lancés **en parallèle**.

---

## 3. Règle centrale : PRE-FLIGHT (non négociable)

Avant toute action, chaque agent DOIT déclarer :

- qu’il a **toutes les informations**
- qu’il n’a **aucune hypothèse implicite**
- qu’il est **certain à 100%**

Sinon : il s’arrête et pose une question.

### Règle pratique pour TOI (orchestrateur humain)

Quand un agent pose une question :
1. Tu réponds **uniquement** si :
   - la réponse est explicitement connue
   - aucune interprétation n’est nécessaire
2. Si tu hésites → **tu considères que tu ne sais pas**
3. Dans ce cas seulement → le système doit demander à l’utilisateur (toi)

Objectif : **zéro invention silencieuse**.

---

## 4. Ressources requises (MVP)

### Environnement technique
- Python 3.10+ (3.11 recommandé)
- pip
- pytest (obligatoire)
- Accès filesystem local
- Pas de réseau

### Commandes autorisées (allowlist minimale)
- python / python3
- pip
- pytest

### Contraintes
- Pas d’accès Internet
- Pas de dépendances externes non locales
- Timeouts sur commandes
- Limite d’itérations de correction

---

## 5. Ce que TU dois faire (et seulement ça)

Pendant cette phase :

- Tu joues **l’orchestrateur**
- Tu lances les chantiers dans l’ordre défini
- Tu réponds aux questions **uniquement** si tu es sûre à 100%
- Tu observes :
  - où ça bloque
  - ce qui doit devenir automatique ensuite

Tu **ne codes pas à la place des agents**.
Tu **n’inventes pas pour leur faire plaisir**.

---

## 6. Critère de succès final

Tu peux t’arrêter quand :

- Un prompt simple du type :
  > “Génère un module Python d’inscription avec email + mot de passe, output JSON”

produit :
- un dossier autonome
- du code fonctionnel
- des tests qui passent
- sans intervention humaine

À partir de là :
👉 l’orchestrateur peut devenir une IA  
👉 et toi tu sors définitivement de la boucle.

---

Fin.
