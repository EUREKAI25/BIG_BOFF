# EUREKAI - Todolist & Livrables

Date : 2025-12-14

---

## Phase 1 : Walker & Test MRG

### Objectif
Valider le parcours de la fractale avec le premier agent du labo.

### Tâches

1.1 [installer walker](<installer walker.md>) ok

1.3. **Route API**
- [ ] Ajouter endpoint `/api/walker/execute/walk/<filter_id>`

1.4. **Test initial**
- [ ] Affecter scan=ghost à Object
- [ ] Exécuter Walker (all, 1111)
- [ ] Valider : noeuds == logs == objets

### Livrables Phase 1
- `walker.s.gev` - définition de l'agent
- `eurekai_server.py` mis à jour avec Walker
- Logs du premier parcours complet
- Rapport de validation

---

## Phase 2 : Agent Audit

### Objectif
Analyser les logs générés par Walker.

### Tâches

2.1. **Définir AuditAgent en .gev**
- [ ] Créer Object:Agent:AuditAgent
- [ ] Définir ses méthodes : analyze, report, alert

2.2. **Implémenter Audit dans le serveur Python**
- [ ] Parser les logs
- [ ] Comparer statistiques (noeuds, logs, objets)
- [ ] Détecter anomalies
- [ ] Générer rapport

2.3. **Route API**
- [ ] Ajouter endpoint `/api/audit/execute/analyze/<log_id>`

### Livrables Phase 2
- `audit.s.gev` - définition de l'agent
- `eurekai_server.py` mis à jour avec Audit
- Premier rapport d'audit

---

## Phase 3 : Objets fondamentaux

### Objectif
Définir les objets requis pour les Scenarios et Projects.

### Tâches

3.1. **Object:Scenario**
- [ ] Définir structure de base
- [ ] Attribut milestoneList

3.2. **Object:Scenario:MilestoneScenario**
- [ ] Steps GEVR
- [ ] Attribut questions (QuestionList)
- [ ] Attribut state

3.3. **Object:Question**
- [ ] Attribut override = false
- [ ] Attribut compile = true

3.4. **Object:State**
- [ ] Valeurs possibles : pending, running, done, error, paused

3.5. **Object:Pipeline**
- [ ] Attribut milestoneList
- [ ] Méthodes : start, pause, resume, stop

### Livrables Phase 3
- `scenario.s.gev`
- `milestone.s.gev`
- `question.s.gev`
- `state.s.gev`
- `pipeline.s.gev`

---

## Phase 4 : Validation agnostique

### Objectif
Outil unique pour valider n'importe quelle Rule.

### Tâches

4.1. **Scenario:ValidationScenario**
- [ ] GET : récupère la Rule et ses objets cibles
- [ ] EXECUTE : applique les conditions
- [ ] VALIDATE : vérifie conformité
- [ ] RENDER : rapport de validation

4.2. **Intégrer dans GEVR**
- [ ] V = Validate utilise ce Scenario

4.3. **Route API**
- [ ] `/api/validation/execute/validate/<rule_id>`

### Livrables Phase 4
- `validation.s.gev`
- Serveur mis à jour
- Tests de validation sur règles existantes

---

## Phase 5 : Project

### Objectif
Gestion des projets dans le cockpit.

### Tâches

5.1. **Object:Project**
- [ ] Définir attributs : name, path, owner, description
- [ ] Attribut scenarioList
- [ ] Attribut instanceList

5.2. **Routes API**
- [ ] `/api/project/read/list`
- [ ] `/api/project/read/get/<id>`
- [ ] `/api/project/create/new/<vector>`
- [ ] `/api/project/update/switch/<id>`
- [ ] `/api/project/delete/remove/<id>`

5.3. **Cockpit**
- [ ] Sélecteur de projets (5 derniers)
- [ ] Liste exhaustive (ordre chrono inversé)
- [ ] Bouton Nouveau projet

### Livrables Phase 5
- `project.s.gev`
- Serveur mis à jour
- Cockpit HTML mis à jour
- Cockpit VSCode mis à jour

---

## Phase 6 : Pipeline Source

### Objectif
Implémenter le pipeline IdeaVector → ManifestVector.

### Tâches

6.1. **Object:Source et sous-types**
- [ ] Object:Source:IdeaSource
- [ ] Object:Source:BriefSource
- [ ] Object:Source:SpecSource
- [ ] Object:Source:ManifestSource

6.2. **Méthodes Create**
- [ ] IdeaSource.create
- [ ] BriefSource.create (GET récupère Idea)
- [ ] SpecSource.create (GET récupère Brief)
- [ ] ManifestSource.create (GET récupère Spec)

6.3. **Cascade**
- [ ] ManifestCreate depuis Idea → déclenche toute la chaîne

6.4. **Questions par Milestone**
- [ ] Définir QuestionList pour chaque étape

### Livrables Phase 6
- `source.s.gev` avec sous-types
- Serveur mis à jour
- Tests de pipeline complet Idea → Manifest

---

## Récapitulatif Livrables

| Phase | Livrables principaux |
|-------|---------------------|
| 1 | walker.s.gev, Walker dans serveur, logs, rapport validation |
| 2 | audit.s.gev, Audit dans serveur, rapport d'audit |
| 3 | scenario.s.gev, milestone.s.gev, question.s.gev, state.s.gev, pipeline.s.gev |
| 4 | validation.s.gev, intégration GEVR |
| 5 | project.s.gev, routes API, cockpits mis à jour |
| 6 | source.s.gev, pipeline Source complet |

---

## Ordre d'exécution

```
Phase 1 (Walker) ──► Phase 2 (Audit) ──► Phase 3 (Objets fondamentaux)
                                                      │
                                                      ▼
                         Phase 6 (Source) ◄── Phase 5 (Project) ◄── Phase 4 (Validation)
```

Phase 1 et 2 sont les fondations pour tester la MRG.
Phase 3 fournit les briques pour 4, 5, 6.
Phase 4, 5, 6 peuvent être parallélisées partiellement.
