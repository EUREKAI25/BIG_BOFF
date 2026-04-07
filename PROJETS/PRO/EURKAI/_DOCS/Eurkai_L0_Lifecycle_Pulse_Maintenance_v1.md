# Eurkai — Layer 0 — Lifecycle, Pulse, Maintenance/Automation/Optimization (v1)

## 1. Lifecycle

### 1.1 Pourquoi
Les statuts ne doivent pas être “dispersés” dans les objets. On regroupe :
- l’ensemble des statuts possibles
- les règles de transition
- les règles de validation associées

### 1.2 Lifecycle (objet)
- `Lifecycle` regroupe :
  - `status_list` (liste ordonnée de statuts)
  - `transition_list` (paires source->cible)
  - `rule_list` (règles de validation des transitions)

### 1.3 Statuts (base recommandée)
Cette séquence est une base stable (ajustable par lifecycle spécifique) :
- draft
- ready
- todo
- running
- success
- failure
- archived

> La transition `todo -> running` est généralement verrouillée (réservée au Pulse / executor).

## 2. Pulse

### 2.1 Définition
`Pulse` est un module standalone qui s’exécute chaque seconde.

### 2.2 Rôle
À chaque tick :
- lit les tâches planifiées
- applique la règle : si `now >= execution_date` et `status == todo` alors la tâche devient exécutable
- déclenche le scenario qui passe les tâches dans le bon statut (ex : `running`) et lance l’exécution

> Le Pulse met à jour le `task_status` de façon déterministe.

### 2.3 Output attendu
- tick_id / ts
- liste des tâches “promues” (todo -> running)
- liste des tâches “ignorées” (pas encore dûes, déjà running, etc.)
- logs (trace_id)

## 3. Maintenance / Automation / Optimization

### 3.1 Point commun
Ce sont trois **collections de tâches** activées par triggers (souvent cron-like).

### 3.2 Différences (intention)
- Maintenance : stabilité, conformité, intégrité, cohérence des catalogues et de la fractale
- Optimization : performance, coût, simplification, refactor, réduction de redondance, tuning
- Automation : exécution régulière de workflows métier / techniques (peut être plus “action-oriented”)

### 3.3 Pattern canonique
- `Category:Maintenance` (tag / catégorie)
- `Scenario@MaintenanceScenario` (orchestration)
- Exécution : `each Maintenance.child_list.todo_task.execute` (tâches activées par le Pulse)

## 4. Fréquence d’exécution
- Un scenario de maintenance porte :
  - `frequency` (résolu par méthode / vecteur, jamais valeur brute)
  - et/ou `method` (méthode d’exécution)

> Exemple conceptuel : `frequency = <vecteur de la méthode exécutée qui récupère le label de frequency>`.

## 5. Résultats standardisés (validation / checks)
Pour toute opération qui produit un résultat :
- `result.success.bool`
- `result.message` (label ou texte)
- `result.error.errortype@...` (si échec)
