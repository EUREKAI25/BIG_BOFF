# EUREKAI — Système de Déploiement Autonome Multi-Projets

## Module G3/11 — Documentation Complète

---

## 1. Architecture du Portfolio

Le système implémente une **gestion centralisée de projets** avec supervision et déploiement automatisés.

### Vue d'ensemble

```
Portfolio EUREKAI
├─ ProjectManifest[]     → Définitions statiques (config, dépendances)
├─ ProjectState[]        → États runtime (version, santé, incidents)
├─ DeploymentPipeline[]  → Stratégies de déploiement
└─ SupervisionEngine     → Monitoring centralisé + alertes
```

### Modèle de Portfolio

| Composant | Description |
|-----------|-------------|
| `portfolio_id` | Identifiant unique du portfolio |
| `manifests` | Dict des définitions de projets |
| `states` | Dict des états runtime |
| `summary` | Résumé agrégé (projets actifs, incidents, santé) |

### États d'un Projet

```python
class ProjectStatus(Enum):
    DRAFT = "draft"               # Défini mais jamais déployé
    DEPLOYING = "deploying"       # Déploiement initial en cours
    RUNNING = "running"           # Opérationnel
    DEGRADED = "degraded"         # Partiellement opérationnel
    STOPPED = "stopped"           # Arrêté volontairement
    FAILED = "failed"             # Échec critique
    UPDATING = "updating"         # Mise à jour en cours
    ROLLING_BACK = "rolling_back" # Rollback en cours
```

---

## 2. API de Déploiement

### `deployProject(projectId, strategy?, version?)`

Déploie un projet avec la stratégie spécifiée.

```python
result = manager.deployProject(
    project_id="api-gateway",
    strategy=DeploymentStrategy.SAFE_DEPLOY,
    version="1.5.0"
)

# Retour:
{
    "success": True,
    "deployment_id": "DEP-A1B2C3D4",
    "version": "1.5.0",
    "strategy": "safe_deploy",
    "duration_ms": 1234,
    "logs": ["[HH:MM:SS] Phase 1: Validating...", ...]
}
```

### `updateProject(projectId, newManifest, strategy?)`

Met à jour un projet avec un nouveau manifest.

```python
new_manifest = ProjectManifest(
    project_id="api-gateway",
    name="API Gateway",
    version="1.6.0",  # Version supérieure requise
    ...
)

result = manager.updateProject("api-gateway", new_manifest)
```

### `getProjectStatus(projectId)`

Récupère le statut complet d'un projet.

```python
status = manager.getProjectStatus("api-gateway")

# Retour:
{
    "found": True,
    "project_id": "api-gateway",
    "name": "EUREKAI API Gateway",
    "version": "1.5.2",
    "status": "running",
    "health": "healthy",
    "uptime": "2:30:45",
    "active_incidents": 0,
    "last_deployment": {
        "id": "DEP-A1B2C3D4",
        "status": "success",
        "version": "1.5.2"
    },
    "metrics": {
        "success_rate": 0.95,
        "total_deployments": 20,
        "rollbacks": 1
    },
    "links": {
        "logs": "/logs/api-gateway",
        "metrics": "/metrics/api-gateway",
        "dashboard": "/dashboard/api-gateway"
    }
}
```

### `rollbackProject(projectId)`

Effectue un rollback vers la version précédente.

```python
result = manager.rollbackProject("api-gateway")

# Retour:
{
    "success": True,
    "from_version": "1.6.0",
    "to_version": "1.5.2"
}
```

### `stopProject(projectId)`

Arrête un projet en cours d'exécution.

```python
result = manager.stopProject("api-gateway")
```

### Autres API

| Méthode | Description |
|---------|-------------|
| `registerProject(manifest)` | Enregistre un nouveau projet |
| `unregisterProject(projectId)` | Retire un projet (doit être arrêté) |
| `listProjects(status?, tags?)` | Liste les projets avec filtres |
| `getPortfolioSummary()` | Résumé global du portfolio |
| `getDeploymentOrder()` | Ordre de déploiement (tri topologique) |
| `deployAll(strategy?)` | Déploie tous les projets en ordre |

---

## 3. Stratégies de Déploiement

### SAFE_DEPLOY (Déploiement sécurisé)

Validation complète avant activation. Recommandé pour la production.

```
Étapes:
1. VALIDATE  → Vérification dépendances et prérequis
2. PREPARE   → Configuration de l'environnement
3. DEPLOY    → Déploiement des composants
4. VERIFY    → Health checks et smoke tests
5. ACTIVATE  → Mise en service
```

### CANARY (Déploiement progressif)

Déploiement par étapes avec monitoring à chaque pallier.

```
Progression:
10% → monitoring → 30% → monitoring → 50% → monitoring → 100%

Rollback automatique si les métriques dégradent.
```

**Prérequis**: Le projet doit déjà être en cours d'exécution (pour mise à jour).

### BLUE_GREEN (Switch instantané)

Maintient deux environnements identiques, switch du trafic instantané.

```
1. Déployer sur environnement inactif (green)
2. Vérifier la santé de green
3. Switch du trafic blue → green
4. Conserver blue pour rollback rapide
```

### IMMEDIATE (Dev uniquement)

Déploiement direct sans validation. À utiliser uniquement en développement.

---

## 4. Gestion des Dépendances

### Définition des dépendances

```python
manifest = ProjectManifest(
    project_id="web-frontend",
    dependencies=[
        ProjectDependency("core-services", ">=1.0", required=True),
        ProjectDependency("api-gateway", "^1.5", required=True),
        ProjectDependency("analytics", "~0.9", required=False)
    ],
    ...
)
```

### Contraintes de version

| Syntaxe | Signification |
|---------|---------------|
| `*` | Toute version |
| `>=1.0` | Version 1.0 ou supérieure |
| `^2.0` | Compatible major (2.x.x) |
| `~1.2.3` | Compatible minor (1.2.x) |
| `1.5.2` | Version exacte |

### Ordre de déploiement

Le système calcule automatiquement l'ordre de déploiement par **tri topologique** :

```
core-services (aucune dépendance)
    ↓
api-gateway (→ core-services)
    ↓
web-frontend (→ core-services, api-gateway)
```

---

## 5. Scénarios d'Usage

### Scénario 1 : Ajout d'un nouveau projet

```python
# 1. Créer le manifest
manifest = ProjectManifest(
    project_id="notification-service",
    name="Notification Service",
    version="1.0.0",
    dependencies=[
        ProjectDependency("core-services", ">=1.0")
    ],
    bootstrap=BootstrapConfig(
        entry_point="Object:Notifications.Root",
        health_check_url="/health"
    ),
    default_strategy=DeploymentStrategy.SAFE_DEPLOY
)

# 2. Enregistrer dans le portfolio
manager.registerProject(manifest)

# 3. Déployer
result = manager.deployProject("notification-service")
```

### Scénario 2 : Mise à jour d'un projet existant

```python
# 1. Créer le nouveau manifest avec version supérieure
new_manifest = ProjectManifest(
    project_id="api-gateway",
    name="API Gateway",
    version="1.6.0",  # Bump de version
    modules=["routing", "auth", "tracing"],  # Nouveau module
    ...
)

# 2. Appliquer la mise à jour (Canary pour sécurité)
result = manager.updateProject(
    "api-gateway", 
    new_manifest,
    strategy=DeploymentStrategy.CANARY
)

# 3. Vérifier le statut
status = manager.getProjectStatus("api-gateway")
```

### Scénario 3 : Rollback après incident

```python
# 1. Détecter un problème
status = manager.getProjectStatus("api-gateway")
if status["health"] == "unhealthy":
    
    # 2. Rollback immédiat
    result = manager.rollbackProject("api-gateway")
    
    # 3. Vérifier la restauration
    status = manager.getProjectStatus("api-gateway")
    assert status["health"] == "healthy"
```

### Scénario 4 : Déploiement complet du portfolio

```python
# Déploie tous les projets dans l'ordre des dépendances
result = manager.deployAll(strategy=DeploymentStrategy.SAFE_DEPLOY)

if result["success"]:
    print(f"✓ {result['completed']} projets déployés")
else:
    print(f"✗ Échec sur {result['failed_at']}")
```

---

## 6. Gestion des Incidents

### Création d'un incident

```python
state = manager.portfolio.get_state("api-gateway")

incident = state.add_incident(
    severity=IncidentSeverity.ERROR,
    title="High latency detected",
    message="P99 latency exceeded 500ms threshold"
)

# L'incident dégrade automatiquement le projet si CRITICAL
```

### Résolution d'un incident

```python
state.resolve_incident(
    incident.incident_id,
    resolution="Scaled up to 5 instances"
)

# Le projet revient automatiquement à RUNNING si plus d'incidents actifs
```

### Niveaux de sévérité

| Niveau | Impact |
|--------|--------|
| `INFO` | Notification, pas d'impact |
| `WARNING` | Attention requise |
| `ERROR` | Problème significatif |
| `CRITICAL` | Projet dégradé automatiquement |

---

## 7. Monitoring et Supervision

### Démarrer la supervision

```python
# Démarre les health checks automatiques toutes les 30 secondes
manager.startSupervision(interval_seconds=30)

# Arrêter la supervision
manager.stopSupervision()
```

### Événements émis

```python
def on_event(event_type: str, data: dict):
    if event_type == "critical_alert":
        send_pager_alert(data)
    elif event_type == "deployment_complete":
        log_deployment(data)

manager.onEvent(on_event)
```

| Événement | Déclencheur |
|-----------|-------------|
| `project_registered` | Nouveau projet ajouté |
| `project_unregistered` | Projet retiré |
| `deployment_complete` | Fin d'un déploiement |
| `project_stopped` | Projet arrêté |
| `project_rollback` | Rollback effectué |
| `critical_alert` | Incident critique détecté |

---

## 8. Cas de Test Fournis

### Tests unitaires

| Test | Description |
|------|-------------|
| TEST 1 | Création de ProjectManifest avec valeurs par défaut |
| TEST 2 | Validation des contraintes de dépendances (>=, ^, ~) |
| TEST 3 | Enregistrement et détection de doublons |
| TEST 4 | Tri topologique des dépendances |
| TEST 5 | API PortfolioManager complète |
| TEST 6 | Déploiement de projet |
| TEST 7 | Récupération du statut |
| TEST 8 | Mise à jour de projet |
| TEST 9 | Rollback |
| TEST 10 | Arrêt et suppression |
| TEST 11 | Gestion des incidents |
| TEST 12 | Résumé du portfolio |
| TEST 13 | Export JSON |
| TEST 14 | Stratégies de déploiement (Canary) |
| TEST 15 | Vérification des dépendances |

### Exécution

```bash
python eurekai_portfolio_manager.py --test
```

---

## 9. Checklist de Validation

- [x] **Portfolio multi-projets bien défini** : ProjectManifest + ProjectState
- [x] **API de déploiement claires** : deployProject, updateProject, getProjectStatus, rollback
- [x] **Stratégies de mise à jour** : Safe Deploy, Canary, Blue/Green, Immediate
- [x] **Gestion des dépendances** : Contraintes de version + tri topologique
- [x] **Supervision centralisée** : Health checks + incidents + événements
- [x] **Résilience aux erreurs** : Isolation par projet + rollback automatique
- [x] **Scénarios d'usage fournis** : 4 scénarios détaillés
- [x] **Cas de test complets** : 15 tests couvrant toutes les fonctionnalités

---

## 10. Fichiers Livrés

| Fichier | Description |
|---------|-------------|
| `eurekai_portfolio_manager.py` | Module Python complet (~1700 lignes) |
| `G3_11_Portfolio_Documentation.md` | Cette documentation |

---

*Module G3/11 — EUREKAI System*
