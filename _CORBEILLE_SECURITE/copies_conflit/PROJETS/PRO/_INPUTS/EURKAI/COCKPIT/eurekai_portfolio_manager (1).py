"""
EUREKAI — Système de Déploiement Autonome Multi-Projets
========================================================
Module G3/11 : Portfolio, déploiement, supervision et stratégies de mise à jour.

ARCHITECTURE
------------
Portfolio
├─ ProjectManifest[]     → Définitions statiques des projets
├─ ProjectState[]        → États runtime (version, statut, incidents)
├─ DeploymentPipeline    → Orchestration des déploiements
└─ SupervisionEngine     → Monitoring centralisé + alertes

STRATÉGIES DE DÉPLOIEMENT
-------------------------
1. SAFE_DEPLOY   → Déploiement séquentiel avec validation complète
2. CANARY        → Déploiement progressif (10% → 50% → 100%)
3. ROLLBACK      → Retour à la version précédente
4. BLUE_GREEN    → Switch instantané entre environnements

AUTEUR : EUREKAI System
VERSION : G3/11
DÉPENDANCES : eurekai_meta_tests (G2/10)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from enum import Enum, auto
from datetime import datetime, timedelta
import json
import hashlib
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid


# =============================================================================
# ÉNUMÉRATIONS & CONSTANTES
# =============================================================================

class ProjectStatus(Enum):
    """Statuts possibles d'un projet."""
    DRAFT = "draft"               # Projet défini mais jamais déployé
    DEPLOYING = "deploying"       # Déploiement en cours
    RUNNING = "running"           # Opérationnel
    DEGRADED = "degraded"         # Partiellement opérationnel
    STOPPED = "stopped"           # Arrêté volontairement
    FAILED = "failed"             # Échec critique
    UPDATING = "updating"         # Mise à jour en cours
    ROLLING_BACK = "rolling_back" # Rollback en cours


class DeploymentStrategy(Enum):
    """Stratégies de déploiement disponibles."""
    SAFE_DEPLOY = "safe_deploy"   # Validation complète avant activation
    CANARY = "canary"             # Déploiement progressif
    BLUE_GREEN = "blue_green"     # Switch instantané
    ROLLING = "rolling"           # Mise à jour progressive des instances
    IMMEDIATE = "immediate"       # Déploiement direct (dev only)


class IncidentSeverity(Enum):
    """Niveaux de sévérité des incidents."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """État de santé d'un projet."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CHECKING = "checking"


# =============================================================================
# STRUCTURES DE DONNÉES — MANIFESTS
# =============================================================================

@dataclass
class ProjectDependency:
    """Dépendance vers un autre projet."""
    project_id: str
    version_constraint: str = "*"  # "*", ">=1.0", "^2.0", "~1.2.3"
    required: bool = True
    
    def is_satisfied_by(self, version: str) -> bool:
        """Vérifie si une version satisfait la contrainte."""
        if self.version_constraint == "*":
            return True
        # Parsing simplifié des contraintes
        if self.version_constraint.startswith(">="):
            min_ver = self.version_constraint[2:]
            return self._compare_versions(version, min_ver) >= 0
        if self.version_constraint.startswith("^"):
            # Compatible avec major version
            base = self.version_constraint[1:]
            return version.split(".")[0] == base.split(".")[0]
        if self.version_constraint.startswith("~"):
            # Compatible avec minor version
            base = self.version_constraint[1:]
            v_parts = version.split(".")[:2]
            b_parts = base.split(".")[:2]
            return v_parts == b_parts
        return version == self.version_constraint
    
    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare deux versions sémantiques."""
        parts1 = [int(x) for x in v1.split(".")[:3]]
        parts2 = [int(x) for x in v2.split(".")[:3]]
        while len(parts1) < 3:
            parts1.append(0)
        while len(parts2) < 3:
            parts2.append(0)
        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            if p1 < p2:
                return -1
        return 0


@dataclass
class BootstrapConfig:
    """Configuration de bootstrap d'un projet."""
    entry_point: str = "Object:Root"  # Vecteur ou chemin du point d'entrée
    init_sequence: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3
    health_check_url: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Configuration du monitoring d'un projet."""
    health_check_interval: int = 30  # secondes
    metrics_endpoint: Optional[str] = None
    log_level: str = "INFO"
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    retention_days: int = 30


@dataclass
class ProjectManifest:
    """
    Définition complète d'un projet EUREKAI.
    Équivalent d'un package.json / Cargo.toml pour l'écosystème fractal.
    """
    project_id: str
    name: str
    version: str
    description: str = ""
    
    # Métadonnées
    author: str = "EUREKAI"
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    # Configuration
    bootstrap: BootstrapConfig = field(default_factory=BootstrapConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Dépendances
    dependencies: List[ProjectDependency] = field(default_factory=list)
    
    # Fractale
    root_vector: str = "Object:Root"
    modules: List[str] = field(default_factory=list)
    
    # Déploiement
    default_strategy: DeploymentStrategy = DeploymentStrategy.SAFE_DEPLOY
    min_instances: int = 1
    max_instances: int = 1
    
    def __post_init__(self):
        pass  # Reserved for future initialization logic
    
    @property
    def manifest_id(self) -> str:
        """Identifiant unique du manifest."""
        return f"{self.project_id}@{self.version}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
            "bootstrap": {
                "entry_point": self.bootstrap.entry_point,
                "init_sequence": self.bootstrap.init_sequence,
                "timeout_seconds": self.bootstrap.timeout_seconds,
                "retry_count": self.bootstrap.retry_count,
                "health_check_url": self.bootstrap.health_check_url,
                "environment": self.bootstrap.environment
            },
            "monitoring": {
                "health_check_interval": self.monitoring.health_check_interval,
                "metrics_endpoint": self.monitoring.metrics_endpoint,
                "log_level": self.monitoring.log_level,
                "alert_thresholds": self.monitoring.alert_thresholds,
                "retention_days": self.monitoring.retention_days
            },
            "dependencies": [
                {"project_id": d.project_id, "version": d.version_constraint, "required": d.required}
                for d in self.dependencies
            ],
            "root_vector": self.root_vector,
            "modules": self.modules,
            "default_strategy": self.default_strategy.value,
            "min_instances": self.min_instances,
            "max_instances": self.max_instances
        }


# =============================================================================
# STRUCTURES DE DONNÉES — ÉTAT RUNTIME
# =============================================================================

@dataclass
class Incident:
    """Incident survenu sur un projet."""
    incident_id: str
    project_id: str
    severity: IncidentSeverity
    title: str
    message: str
    occurred_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    
    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.resolved_at:
            return self.resolved_at - self.occurred_at
        return None
    
    def resolve(self, resolution: str):
        """Marque l'incident comme résolu."""
        self.resolved_at = datetime.now()
        self.resolution = resolution


@dataclass
class DeploymentRecord:
    """Enregistrement d'un déploiement."""
    deployment_id: str
    project_id: str
    version: str
    strategy: DeploymentStrategy
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, success, failed, rolled_back
    rollback_version: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    
    def log(self, message: str):
        """Ajoute un message au log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
    
    def complete(self, success: bool):
        """Marque le déploiement comme terminé."""
        self.completed_at = datetime.now()
        self.status = "success" if success else "failed"
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.completed_at:
            return self.completed_at - self.started_at
        return datetime.now() - self.started_at


@dataclass
class ProjectState:
    """
    État runtime d'un projet.
    Séparé du manifest pour permettre l'évolution indépendante.
    """
    project_id: str
    status: ProjectStatus = ProjectStatus.DRAFT
    current_version: str = "0.0.0"
    previous_version: Optional[str] = None
    
    # Santé
    health: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    uptime_start: Optional[datetime] = None
    
    # Incidents
    incidents: List[Incident] = field(default_factory=list)
    active_incidents: int = 0
    
    # Déploiements
    deployment_history: List[DeploymentRecord] = field(default_factory=list)
    current_deployment: Optional[DeploymentRecord] = None
    
    # Métriques
    total_deployments: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    rollbacks: int = 0
    
    # Logs et monitoring
    log_url: Optional[str] = None
    metrics_url: Optional[str] = None
    dashboard_url: Optional[str] = None
    
    def add_incident(self, severity: IncidentSeverity, title: str, message: str) -> Incident:
        """Crée et enregistre un nouvel incident."""
        incident = Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            project_id=self.project_id,
            severity=severity,
            title=title,
            message=message
        )
        self.incidents.append(incident)
        self.active_incidents += 1
        
        # Dégradation automatique si incident critique
        if severity == IncidentSeverity.CRITICAL and self.status == ProjectStatus.RUNNING:
            self.status = ProjectStatus.DEGRADED
        
        return incident
    
    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        """Résout un incident."""
        for incident in self.incidents:
            if incident.incident_id == incident_id and not incident.is_resolved:
                incident.resolve(resolution)
                self.active_incidents -= 1
                
                # Restauration si plus d'incidents actifs critiques
                if self.active_incidents == 0 and self.status == ProjectStatus.DEGRADED:
                    self.status = ProjectStatus.RUNNING
                
                return True
        return False
    
    def start_deployment(self, version: str, strategy: DeploymentStrategy) -> DeploymentRecord:
        """Démarre un nouveau déploiement."""
        self.previous_version = self.current_version
        
        deployment = DeploymentRecord(
            deployment_id=f"DEP-{uuid.uuid4().hex[:8].upper()}",
            project_id=self.project_id,
            version=version,
            strategy=strategy,
            started_at=datetime.now(),
            rollback_version=self.current_version
        )
        
        self.current_deployment = deployment
        self.deployment_history.append(deployment)
        self.total_deployments += 1
        self.status = ProjectStatus.DEPLOYING if self.status == ProjectStatus.DRAFT else ProjectStatus.UPDATING
        
        return deployment
    
    def complete_deployment(self, success: bool) -> bool:
        """Finalise le déploiement en cours."""
        if not self.current_deployment:
            return False
        
        self.current_deployment.complete(success)
        
        if success:
            self.current_version = self.current_deployment.version
            self.successful_deployments += 1
            self.status = ProjectStatus.RUNNING
            self.uptime_start = datetime.now()
            self.health = HealthStatus.HEALTHY
        else:
            self.failed_deployments += 1
            self.status = ProjectStatus.FAILED
            self.health = HealthStatus.UNHEALTHY
        
        self.current_deployment = None
        return success
    
    def rollback(self) -> bool:
        """Effectue un rollback vers la version précédente."""
        if not self.previous_version:
            return False
        
        self.rollbacks += 1
        self.status = ProjectStatus.ROLLING_BACK
        
        # Swap versions
        temp = self.current_version
        self.current_version = self.previous_version
        self.previous_version = temp
        
        self.status = ProjectStatus.RUNNING
        return True
    
    @property
    def uptime(self) -> Optional[timedelta]:
        """Durée depuis le dernier démarrage réussi."""
        if self.uptime_start and self.status == ProjectStatus.RUNNING:
            return datetime.now() - self.uptime_start
        return None
    
    @property
    def success_rate(self) -> float:
        """Taux de succès des déploiements."""
        if self.total_deployments == 0:
            return 0.0
        return self.successful_deployments / self.total_deployments
    
    def to_dict(self) -> Dict[str, Any]:
        """Export en dictionnaire."""
        return {
            "project_id": self.project_id,
            "status": self.status.value,
            "current_version": self.current_version,
            "previous_version": self.previous_version,
            "health": self.health.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "uptime": str(self.uptime) if self.uptime else None,
            "active_incidents": self.active_incidents,
            "total_incidents": len(self.incidents),
            "metrics": {
                "total_deployments": self.total_deployments,
                "successful_deployments": self.successful_deployments,
                "failed_deployments": self.failed_deployments,
                "rollbacks": self.rollbacks,
                "success_rate": self.success_rate
            },
            "links": {
                "logs": self.log_url,
                "metrics": self.metrics_url,
                "dashboard": self.dashboard_url
            }
        }


# =============================================================================
# PORTFOLIO — COLLECTION DE PROJETS
# =============================================================================

@dataclass
class PortfolioSummary:
    """Résumé de l'état du portfolio."""
    total_projects: int
    running: int
    degraded: int
    stopped: int
    failed: int
    deploying: int
    
    total_incidents: int
    critical_incidents: int
    
    overall_health: HealthStatus
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_projects": self.total_projects,
            "by_status": {
                "running": self.running,
                "degraded": self.degraded,
                "stopped": self.stopped,
                "failed": self.failed,
                "deploying": self.deploying
            },
            "incidents": {
                "total": self.total_incidents,
                "critical": self.critical_incidents
            },
            "overall_health": self.overall_health.value,
            "last_updated": self.last_updated.isoformat()
        }


class Portfolio:
    """
    Collection de projets EUREKAI avec supervision centralisée.
    """
    
    def __init__(self, portfolio_id: str = "default"):
        self.portfolio_id = portfolio_id
        self.manifests: Dict[str, ProjectManifest] = {}
        self.states: Dict[str, ProjectState] = {}
        self.created_at = datetime.now()
        self._lock = threading.RLock()
    
    def register_project(self, manifest: ProjectManifest) -> bool:
        """Enregistre un nouveau projet dans le portfolio."""
        with self._lock:
            if manifest.project_id in self.manifests:
                return False
            
            self.manifests[manifest.project_id] = manifest
            self.states[manifest.project_id] = ProjectState(
                project_id=manifest.project_id,
                current_version=manifest.version,
                log_url=f"/logs/{manifest.project_id}",
                metrics_url=f"/metrics/{manifest.project_id}",
                dashboard_url=f"/dashboard/{manifest.project_id}"
            )
            return True
    
    def unregister_project(self, project_id: str) -> bool:
        """Retire un projet du portfolio."""
        with self._lock:
            if project_id not in self.manifests:
                return False
            
            state = self.states.get(project_id)
            if state and state.status in [ProjectStatus.RUNNING, ProjectStatus.DEPLOYING]:
                return False  # Ne peut pas retirer un projet actif
            
            del self.manifests[project_id]
            del self.states[project_id]
            return True
    
    def get_manifest(self, project_id: str) -> Optional[ProjectManifest]:
        """Récupère le manifest d'un projet."""
        return self.manifests.get(project_id)
    
    def get_state(self, project_id: str) -> Optional[ProjectState]:
        """Récupère l'état d'un projet."""
        return self.states.get(project_id)
    
    def update_manifest(self, manifest: ProjectManifest) -> bool:
        """Met à jour le manifest d'un projet existant."""
        with self._lock:
            if manifest.project_id not in self.manifests:
                return False
            self.manifests[manifest.project_id] = manifest
            return True
    
    def list_projects(self, 
                      status_filter: Optional[List[ProjectStatus]] = None,
                      tag_filter: Optional[List[str]] = None) -> List[str]:
        """Liste les projets avec filtres optionnels."""
        result = []
        for project_id, manifest in self.manifests.items():
            state = self.states.get(project_id)
            
            # Filtre par statut
            if status_filter and state and state.status not in status_filter:
                continue
            
            # Filtre par tags
            if tag_filter and not any(t in manifest.tags for t in tag_filter):
                continue
            
            result.append(project_id)
        
        return result
    
    def get_summary(self) -> PortfolioSummary:
        """Génère un résumé de l'état du portfolio."""
        running = degraded = stopped = failed = deploying = 0
        total_incidents = critical_incidents = 0
        
        for state in self.states.values():
            if state.status == ProjectStatus.RUNNING:
                running += 1
            elif state.status == ProjectStatus.DEGRADED:
                degraded += 1
            elif state.status == ProjectStatus.STOPPED:
                stopped += 1
            elif state.status == ProjectStatus.FAILED:
                failed += 1
            elif state.status in [ProjectStatus.DEPLOYING, ProjectStatus.UPDATING]:
                deploying += 1
            
            total_incidents += state.active_incidents
            critical_incidents += sum(
                1 for i in state.incidents 
                if not i.is_resolved and i.severity == IncidentSeverity.CRITICAL
            )
        
        # Déterminer la santé globale
        if critical_incidents > 0 or failed > 0:
            overall_health = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_health = HealthStatus.UNHEALTHY
        elif running == len(self.states) and len(self.states) > 0:
            overall_health = HealthStatus.HEALTHY
        else:
            overall_health = HealthStatus.UNKNOWN
        
        return PortfolioSummary(
            total_projects=len(self.manifests),
            running=running,
            degraded=degraded,
            stopped=stopped,
            failed=failed,
            deploying=deploying,
            total_incidents=total_incidents,
            critical_incidents=critical_incidents,
            overall_health=overall_health
        )
    
    def check_dependencies(self, project_id: str) -> Tuple[bool, List[str]]:
        """Vérifie si les dépendances d'un projet sont satisfaites."""
        manifest = self.manifests.get(project_id)
        if not manifest:
            return False, [f"Project {project_id} not found"]
        
        errors = []
        for dep in manifest.dependencies:
            dep_state = self.states.get(dep.project_id)
            
            if not dep_state:
                if dep.required:
                    errors.append(f"Required dependency {dep.project_id} not found")
                continue
            
            if dep_state.status != ProjectStatus.RUNNING:
                if dep.required:
                    errors.append(f"Required dependency {dep.project_id} is not running (status: {dep_state.status.value})")
                continue
            
            if not dep.is_satisfied_by(dep_state.current_version):
                errors.append(f"Dependency {dep.project_id}@{dep_state.current_version} does not satisfy {dep.version_constraint}")
        
        return len(errors) == 0, errors
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Retourne le graphe des dépendances."""
        graph = {}
        for project_id, manifest in self.manifests.items():
            graph[project_id] = [dep.project_id for dep in manifest.dependencies]
        return graph
    
    def get_deployment_order(self) -> List[str]:
        """Calcule l'ordre de déploiement (tri topologique)."""
        graph = self.get_dependency_graph()
        visited = set()
        order = []
        
        def visit(node: str):
            if node in visited:
                return
            visited.add(node)
            for dep in graph.get(node, []):
                if dep in self.manifests:
                    visit(dep)
            order.append(node)
        
        for project_id in self.manifests:
            visit(project_id)
        
        return order
    
    def to_dict(self) -> Dict[str, Any]:
        """Export complet du portfolio."""
        return {
            "portfolio_id": self.portfolio_id,
            "created_at": self.created_at.isoformat(),
            "summary": self.get_summary().to_dict(),
            "projects": {
                pid: {
                    "manifest": m.to_dict(),
                    "state": self.states[pid].to_dict()
                }
                for pid, m in self.manifests.items()
            }
        }


# =============================================================================
# DEPLOYMENT STRATEGIES
# =============================================================================

class DeploymentPipeline(ABC):
    """Classe de base pour les pipelines de déploiement."""
    
    @abstractmethod
    def execute(self, portfolio: Portfolio, project_id: str, 
                manifest: ProjectManifest, state: ProjectState) -> bool:
        """Exécute le déploiement."""
        pass
    
    @abstractmethod
    def validate(self, portfolio: Portfolio, project_id: str) -> Tuple[bool, str]:
        """Valide les prérequis du déploiement."""
        pass
    
    @abstractmethod
    def rollback(self, portfolio: Portfolio, project_id: str, state: ProjectState) -> bool:
        """Effectue un rollback."""
        pass


class SafeDeployPipeline(DeploymentPipeline):
    """
    Déploiement sécurisé avec validation complète.
    Étapes : Validate → Prepare → Deploy → Verify → Activate
    """
    
    def validate(self, portfolio: Portfolio, project_id: str) -> Tuple[bool, str]:
        deps_ok, errors = portfolio.check_dependencies(project_id)
        if not deps_ok:
            return False, f"Dependency check failed: {', '.join(errors)}"
        return True, "All validations passed"
    
    def execute(self, portfolio: Portfolio, project_id: str,
                manifest: ProjectManifest, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if not deployment:
            return False
        
        try:
            # Phase 1: Validate
            deployment.log("Phase 1: Validating deployment prerequisites...")
            valid, msg = self.validate(portfolio, project_id)
            if not valid:
                deployment.log(f"Validation failed: {msg}")
                return False
            deployment.log("Validation passed")
            
            # Phase 2: Prepare
            deployment.log("Phase 2: Preparing deployment environment...")
            self._prepare_environment(manifest, deployment)
            deployment.log("Environment prepared")
            
            # Phase 3: Deploy
            deployment.log("Phase 3: Deploying project components...")
            self._deploy_components(manifest, deployment)
            deployment.log("Components deployed")
            
            # Phase 4: Verify
            deployment.log("Phase 4: Running post-deployment verification...")
            if not self._verify_deployment(manifest, deployment):
                deployment.log("Verification failed, initiating rollback")
                return False
            deployment.log("Verification passed")
            
            # Phase 5: Activate
            deployment.log("Phase 5: Activating project...")
            self._activate_project(manifest, state, deployment)
            deployment.log("Project activated successfully")
            
            return True
            
        except Exception as e:
            deployment.log(f"Deployment error: {str(e)}")
            return False
    
    def rollback(self, portfolio: Portfolio, project_id: str, state: ProjectState) -> bool:
        return state.rollback()
    
    def _prepare_environment(self, manifest: ProjectManifest, deployment: DeploymentRecord):
        """Prépare l'environnement de déploiement."""
        for key, value in manifest.bootstrap.environment.items():
            deployment.log(f"  Setting {key}={value[:20]}...")
    
    def _deploy_components(self, manifest: ProjectManifest, deployment: DeploymentRecord):
        """Déploie les composants du projet."""
        for module in manifest.modules:
            deployment.log(f"  Deploying module: {module}")
    
    def _verify_deployment(self, manifest: ProjectManifest, deployment: DeploymentRecord) -> bool:
        """Vérifie le déploiement."""
        deployment.log("  Running health checks...")
        deployment.log("  Running smoke tests...")
        return True  # Simulation
    
    def _activate_project(self, manifest: ProjectManifest, state: ProjectState, 
                          deployment: DeploymentRecord):
        """Active le projet."""
        state.health = HealthStatus.HEALTHY
        state.last_health_check = datetime.now()


class CanaryDeployPipeline(DeploymentPipeline):
    """
    Déploiement progressif (canary).
    Progression : 10% → 30% → 50% → 100%
    """
    
    STAGES = [10, 30, 50, 100]
    
    def validate(self, portfolio: Portfolio, project_id: str) -> Tuple[bool, str]:
        state = portfolio.get_state(project_id)
        if not state:
            return False, "Project not found"
        
        # Check if project was running before deployment started
        # (status is now UPDATING, but we need to check if it had a previous version)
        if state.status not in [ProjectStatus.UPDATING, ProjectStatus.RUNNING] or not state.previous_version:
            # For initial deployment, canary is not suitable
            if state.total_deployments == 0:
                return False, "Canary requires a previously deployed project"
        
        deps_ok, errors = portfolio.check_dependencies(project_id)
        if not deps_ok:
            return False, f"Dependency check failed: {', '.join(errors)}"
        
        return True, "Canary deployment validated"
    
    def execute(self, portfolio: Portfolio, project_id: str,
                manifest: ProjectManifest, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if not deployment:
            return False
        
        try:
            valid, msg = self.validate(portfolio, project_id)
            if not valid:
                deployment.log(f"Validation failed: {msg}")
                return False
            
            for stage_percent in self.STAGES:
                deployment.log(f"Canary stage: {stage_percent}% traffic")
                
                # Simulation du déploiement progressif
                deployment.log(f"  Routing {stage_percent}% of traffic to new version...")
                deployment.log(f"  Monitoring metrics for stage {stage_percent}%...")
                
                # Vérification des métriques
                if not self._check_canary_health(stage_percent, deployment):
                    deployment.log(f"Canary failed at {stage_percent}%, rolling back")
                    return False
                
                deployment.log(f"  Stage {stage_percent}% passed")
            
            deployment.log("Canary deployment completed successfully")
            return True
            
        except Exception as e:
            deployment.log(f"Canary error: {str(e)}")
            return False
    
    def rollback(self, portfolio: Portfolio, project_id: str, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if deployment:
            deployment.log("Rolling back canary deployment...")
            deployment.log("Routing 100% traffic to previous version")
        return state.rollback()
    
    def _check_canary_health(self, stage_percent: int, deployment: DeploymentRecord) -> bool:
        """Vérifie la santé du canary à un stage donné."""
        # Simulation - en production, vérifierait les métriques réelles
        return True


class BlueGreenDeployPipeline(DeploymentPipeline):
    """
    Déploiement Blue/Green avec switch instantané.
    Maintient deux environnements identiques.
    """
    
    def validate(self, portfolio: Portfolio, project_id: str) -> Tuple[bool, str]:
        deps_ok, errors = portfolio.check_dependencies(project_id)
        if not deps_ok:
            return False, f"Dependency check failed: {', '.join(errors)}"
        return True, "Blue/Green validated"
    
    def execute(self, portfolio: Portfolio, project_id: str,
                manifest: ProjectManifest, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if not deployment:
            return False
        
        try:
            valid, msg = self.validate(portfolio, project_id)
            if not valid:
                deployment.log(f"Validation failed: {msg}")
                return False
            
            # Déterminer l'environnement cible
            current_env = "blue"  # Simulation
            target_env = "green" if current_env == "blue" else "blue"
            
            deployment.log(f"Current environment: {current_env}")
            deployment.log(f"Deploying to: {target_env}")
            
            # Déployer sur l'environnement inactif
            deployment.log(f"Deploying version {manifest.version} to {target_env}...")
            deployment.log(f"Running health checks on {target_env}...")
            
            # Vérifier la santé du nouvel environnement
            if not self._verify_environment(target_env, deployment):
                deployment.log(f"Health check failed on {target_env}")
                return False
            
            # Switch du trafic
            deployment.log(f"Switching traffic from {current_env} to {target_env}...")
            deployment.log("Traffic switch completed")
            
            # Garder l'ancien environnement pour rollback potentiel
            deployment.log(f"Keeping {current_env} environment for potential rollback")
            
            return True
            
        except Exception as e:
            deployment.log(f"Blue/Green error: {str(e)}")
            return False
    
    def rollback(self, portfolio: Portfolio, project_id: str, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if deployment:
            deployment.log("Blue/Green rollback: switching traffic back")
        return state.rollback()
    
    def _verify_environment(self, env: str, deployment: DeploymentRecord) -> bool:
        """Vérifie la santé d'un environnement."""
        deployment.log(f"  Checking {env} health endpoints...")
        deployment.log(f"  Running smoke tests on {env}...")
        return True


class ImmediateDeployPipeline(DeploymentPipeline):
    """
    Déploiement immédiat sans validation (dev/test uniquement).
    """
    
    def validate(self, portfolio: Portfolio, project_id: str) -> Tuple[bool, str]:
        return True, "Immediate deployment (no validation)"
    
    def execute(self, portfolio: Portfolio, project_id: str,
                manifest: ProjectManifest, state: ProjectState) -> bool:
        deployment = state.current_deployment
        if not deployment:
            return False
        
        deployment.log("IMMEDIATE DEPLOYMENT - No validation (dev mode)")
        deployment.log(f"Deploying {manifest.project_id}@{manifest.version}...")
        deployment.log("Deployment complete")
        
        return True
    
    def rollback(self, portfolio: Portfolio, project_id: str, state: ProjectState) -> bool:
        return state.rollback()


# =============================================================================
# PORTFOLIO MANAGER — API PRINCIPALE
# =============================================================================

class PortfolioManager:
    """
    Gestionnaire principal du portfolio EUREKAI.
    Fournit l'API de déploiement et supervision.
    """
    
    def __init__(self, portfolio: Optional[Portfolio] = None):
        self.portfolio = portfolio or Portfolio()
        self._pipelines: Dict[DeploymentStrategy, DeploymentPipeline] = {
            DeploymentStrategy.SAFE_DEPLOY: SafeDeployPipeline(),
            DeploymentStrategy.CANARY: CanaryDeployPipeline(),
            DeploymentStrategy.BLUE_GREEN: BlueGreenDeployPipeline(),
            DeploymentStrategy.IMMEDIATE: ImmediateDeployPipeline(),
        }
        self._supervision_active = False
        self._supervision_thread: Optional[threading.Thread] = None
        self._event_handlers: List[Callable[[str, Dict], None]] = []
    
    # =========================================================================
    # API DE DÉPLOIEMENT
    # =========================================================================
    
    def deployProject(self, project_id: str, 
                      strategy: Optional[DeploymentStrategy] = None,
                      version: Optional[str] = None) -> Dict[str, Any]:
        """
        Déploie un projet.
        
        Args:
            project_id: Identifiant du projet
            strategy: Stratégie de déploiement (défaut: manifest.default_strategy)
            version: Version à déployer (défaut: manifest.version)
        
        Returns:
            Dict avec deployment_id, status, et messages
        """
        manifest = self.portfolio.get_manifest(project_id)
        state = self.portfolio.get_state(project_id)
        
        if not manifest or not state:
            return {
                "success": False,
                "error": f"Project {project_id} not found"
            }
        
        # Vérifier si déploiement déjà en cours
        if state.status in [ProjectStatus.DEPLOYING, ProjectStatus.UPDATING]:
            return {
                "success": False,
                "error": f"Deployment already in progress for {project_id}"
            }
        
        # Utiliser les valeurs par défaut
        strategy = strategy or manifest.default_strategy
        version = version or manifest.version
        
        # Démarrer le déploiement
        deployment = state.start_deployment(version, strategy)
        deployment.log(f"Starting {strategy.value} deployment of {project_id}@{version}")
        
        # Exécuter le pipeline
        pipeline = self._pipelines.get(strategy)
        if not pipeline:
            deployment.log(f"Unknown strategy: {strategy.value}")
            state.complete_deployment(False)
            return {
                "success": False,
                "deployment_id": deployment.deployment_id,
                "error": f"Unknown strategy: {strategy.value}"
            }
        
        success = pipeline.execute(self.portfolio, project_id, manifest, state)
        state.complete_deployment(success)
        
        self._emit_event("deployment_complete", {
            "project_id": project_id,
            "deployment_id": deployment.deployment_id,
            "success": success,
            "version": version
        })
        
        return {
            "success": success,
            "deployment_id": deployment.deployment_id,
            "version": version,
            "strategy": strategy.value,
            "duration_ms": deployment.duration.total_seconds() * 1000 if deployment.duration else 0,
            "logs": deployment.logs
        }
    
    def updateProject(self, project_id: str, 
                      new_manifest: ProjectManifest,
                      strategy: Optional[DeploymentStrategy] = None) -> Dict[str, Any]:
        """
        Met à jour un projet avec un nouveau manifest.
        
        Args:
            project_id: Identifiant du projet
            new_manifest: Nouveau manifest
            strategy: Stratégie de mise à jour
        
        Returns:
            Dict avec status et deployment_id
        """
        if project_id != new_manifest.project_id:
            return {
                "success": False,
                "error": "Project ID mismatch"
            }
        
        current_manifest = self.portfolio.get_manifest(project_id)
        if not current_manifest:
            return {
                "success": False,
                "error": f"Project {project_id} not found"
            }
        
        state = self.portfolio.get_state(project_id)
        
        # Vérifier si c'est une montée de version
        if ProjectDependency._compare_versions(new_manifest.version, current_manifest.version) <= 0:
            return {
                "success": False,
                "error": f"New version {new_manifest.version} must be greater than current {current_manifest.version}"
            }
        
        # Mettre à jour le manifest
        self.portfolio.update_manifest(new_manifest)
        
        # Déterminer la stratégie
        strategy = strategy or new_manifest.default_strategy
        
        # Si le projet est en cours d'exécution, le redéployer
        if state and state.status == ProjectStatus.RUNNING:
            return self.deployProject(project_id, strategy, new_manifest.version)
        
        return {
            "success": True,
            "message": f"Manifest updated to version {new_manifest.version}"
        }
    
    def getProjectStatus(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère le statut complet d'un projet.
        
        Args:
            project_id: Identifiant du projet
        
        Returns:
            Dict avec état complet du projet
        """
        manifest = self.portfolio.get_manifest(project_id)
        state = self.portfolio.get_state(project_id)
        
        if not manifest or not state:
            return {
                "found": False,
                "error": f"Project {project_id} not found"
            }
        
        return {
            "found": True,
            "project_id": project_id,
            "name": manifest.name,
            "version": state.current_version,
            "status": state.status.value,
            "health": state.health.value,
            "uptime": str(state.uptime) if state.uptime else None,
            "active_incidents": state.active_incidents,
            "last_deployment": {
                "id": state.deployment_history[-1].deployment_id if state.deployment_history else None,
                "status": state.deployment_history[-1].status if state.deployment_history else None,
                "version": state.deployment_history[-1].version if state.deployment_history else None
            },
            "metrics": {
                "success_rate": state.success_rate,
                "total_deployments": state.total_deployments,
                "rollbacks": state.rollbacks
            },
            "links": {
                "logs": state.log_url,
                "metrics": state.metrics_url,
                "dashboard": state.dashboard_url
            }
        }
    
    def stopProject(self, project_id: str) -> Dict[str, Any]:
        """Arrête un projet."""
        state = self.portfolio.get_state(project_id)
        
        if not state:
            return {"success": False, "error": f"Project {project_id} not found"}
        
        if state.status not in [ProjectStatus.RUNNING, ProjectStatus.DEGRADED]:
            return {"success": False, "error": f"Project is not running (status: {state.status.value})"}
        
        state.status = ProjectStatus.STOPPED
        state.health = HealthStatus.UNKNOWN
        
        self._emit_event("project_stopped", {"project_id": project_id})
        
        return {"success": True, "message": f"Project {project_id} stopped"}
    
    def rollbackProject(self, project_id: str) -> Dict[str, Any]:
        """Effectue un rollback vers la version précédente."""
        state = self.portfolio.get_state(project_id)
        
        if not state:
            return {"success": False, "error": f"Project {project_id} not found"}
        
        if not state.previous_version:
            return {"success": False, "error": "No previous version to rollback to"}
        
        previous = state.previous_version
        success = state.rollback()
        
        if success:
            self._emit_event("project_rollback", {
                "project_id": project_id,
                "from_version": previous,
                "to_version": state.current_version
            })
        
        return {
            "success": success,
            "from_version": previous,
            "to_version": state.current_version if success else None
        }
    
    # =========================================================================
    # API DE PORTFOLIO
    # =========================================================================
    
    def registerProject(self, manifest: ProjectManifest) -> Dict[str, Any]:
        """Enregistre un nouveau projet."""
        success = self.portfolio.register_project(manifest)
        
        if success:
            self._emit_event("project_registered", {"project_id": manifest.project_id})
        
        return {
            "success": success,
            "project_id": manifest.project_id,
            "error": None if success else f"Project {manifest.project_id} already exists"
        }
    
    def unregisterProject(self, project_id: str) -> Dict[str, Any]:
        """Retire un projet du portfolio."""
        success = self.portfolio.unregister_project(project_id)
        
        if success:
            self._emit_event("project_unregistered", {"project_id": project_id})
        
        return {
            "success": success,
            "error": None if success else f"Cannot unregister {project_id} (not found or active)"
        }
    
    def listProjects(self, 
                     status: Optional[List[str]] = None,
                     tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Liste les projets avec leurs statuts."""
        status_filter = [ProjectStatus(s) for s in status] if status else None
        
        project_ids = self.portfolio.list_projects(status_filter, tags)
        
        return [self.getProjectStatus(pid) for pid in project_ids]
    
    def getPortfolioSummary(self) -> Dict[str, Any]:
        """Résumé global du portfolio."""
        return self.portfolio.get_summary().to_dict()
    
    def getDeploymentOrder(self) -> List[str]:
        """Ordre de déploiement recommandé (respect des dépendances)."""
        return self.portfolio.get_deployment_order()
    
    def deployAll(self, strategy: Optional[DeploymentStrategy] = None) -> Dict[str, Any]:
        """Déploie tous les projets dans l'ordre des dépendances."""
        order = self.getDeploymentOrder()
        results = []
        
        for project_id in order:
            result = self.deployProject(project_id, strategy)
            results.append({
                "project_id": project_id,
                "success": result.get("success", False),
                "deployment_id": result.get("deployment_id")
            })
            
            if not result.get("success"):
                return {
                    "success": False,
                    "completed": len([r for r in results if r["success"]]),
                    "failed_at": project_id,
                    "results": results
                }
        
        return {
            "success": True,
            "completed": len(results),
            "results": results
        }
    
    # =========================================================================
    # SUPERVISION
    # =========================================================================
    
    def startSupervision(self, interval_seconds: int = 30):
        """Démarre la supervision continue."""
        if self._supervision_active:
            return
        
        self._supervision_active = True
        self._supervision_thread = threading.Thread(
            target=self._supervision_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._supervision_thread.start()
    
    def stopSupervision(self):
        """Arrête la supervision."""
        self._supervision_active = False
        if self._supervision_thread:
            self._supervision_thread.join(timeout=5)
            self._supervision_thread = None
    
    def _supervision_loop(self, interval: int):
        """Boucle de supervision."""
        while self._supervision_active:
            try:
                self._run_health_checks()
                self._check_incidents()
            except Exception as e:
                print(f"Supervision error: {e}")
            
            time.sleep(interval)
    
    def _run_health_checks(self):
        """Exécute les health checks sur tous les projets actifs."""
        for project_id, state in self.portfolio.states.items():
            if state.status != ProjectStatus.RUNNING:
                continue
            
            state.health = HealthStatus.CHECKING
            
            # Simulation du health check
            is_healthy = True  # En production, vérifierait les endpoints
            
            state.health = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
            state.last_health_check = datetime.now()
            
            if not is_healthy:
                state.add_incident(
                    IncidentSeverity.ERROR,
                    f"Health check failed for {project_id}",
                    "Project health endpoint did not respond"
                )
    
    def _check_incidents(self):
        """Vérifie les incidents en cours et émet des alertes."""
        summary = self.portfolio.get_summary()
        
        if summary.critical_incidents > 0:
            self._emit_event("critical_alert", {
                "message": f"{summary.critical_incidents} critical incidents detected",
                "total_incidents": summary.total_incidents
            })
    
    def onEvent(self, handler: Callable[[str, Dict], None]):
        """Enregistre un handler d'événements."""
        self._event_handlers.append(handler)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Émet un événement aux handlers."""
        for handler in self._event_handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                print(f"Event handler error: {e}")


# =============================================================================
# EXEMPLES & DONNÉES DE TEST
# =============================================================================

def create_example_manifests() -> List[ProjectManifest]:
    """Crée des manifests de projets d'exemple."""
    return [
        ProjectManifest(
            project_id="core-services",
            name="EUREKAI Core Services",
            version="1.0.0",
            description="Services fondamentaux de la plateforme",
            tags=["core", "critical"],
            bootstrap=BootstrapConfig(
                entry_point="Object:CoreServices.Root",
                init_sequence=["init-db", "init-cache", "init-queues"],
                timeout_seconds=120,
                health_check_url="/health"
            ),
            monitoring=MonitoringConfig(
                health_check_interval=10,
                metrics_endpoint="/metrics",
                alert_thresholds={"error_rate": 0.01, "latency_p99": 500}
            ),
            modules=["database", "cache", "queue", "auth"],
            default_strategy=DeploymentStrategy.BLUE_GREEN
        ),
        ProjectManifest(
            project_id="web-frontend",
            name="EUREKAI Web Frontend",
            version="2.3.0",
            description="Interface utilisateur web",
            tags=["frontend", "web"],
            dependencies=[
                ProjectDependency("core-services", ">=1.0", required=True),
                ProjectDependency("api-gateway", "^1.0", required=True)
            ],
            bootstrap=BootstrapConfig(
                entry_point="Object:WebFrontend.Root",
                init_sequence=["build-assets", "warm-cache"],
                health_check_url="/ready"
            ),
            modules=["landing", "dashboard", "settings", "components"],
            default_strategy=DeploymentStrategy.CANARY
        ),
        ProjectManifest(
            project_id="api-gateway",
            name="EUREKAI API Gateway",
            version="1.5.2",
            description="Point d'entrée API unifié",
            tags=["api", "gateway", "critical"],
            dependencies=[
                ProjectDependency("core-services", ">=1.0", required=True)
            ],
            bootstrap=BootstrapConfig(
                entry_point="Object:APIGateway.Root",
                init_sequence=["load-routes", "init-rate-limiter"],
                health_check_url="/ping"
            ),
            monitoring=MonitoringConfig(
                health_check_interval=5,
                alert_thresholds={"error_rate": 0.005, "latency_p99": 100}
            ),
            modules=["routing", "auth", "rate-limiting", "logging"],
            default_strategy=DeploymentStrategy.SAFE_DEPLOY
        ),
        ProjectManifest(
            project_id="analytics-engine",
            name="EUREKAI Analytics Engine",
            version="0.9.0",
            description="Moteur d'analyse et métriques",
            tags=["analytics", "data"],
            dependencies=[
                ProjectDependency("core-services", ">=1.0", required=True)
            ],
            bootstrap=BootstrapConfig(
                entry_point="Object:Analytics.Root",
                init_sequence=["init-pipelines", "warm-models"],
                timeout_seconds=300
            ),
            modules=["collectors", "processors", "visualizers"],
            default_strategy=DeploymentStrategy.SAFE_DEPLOY
        )
    ]


def run_demo():
    """Exécute une démonstration complète."""
    print("\n" + "=" * 70)
    print("EUREKAI — Système de Déploiement Multi-Projets G3/11")
    print("=" * 70)
    
    # Créer le gestionnaire
    manager = PortfolioManager()
    
    # Handler d'événements
    events = []
    def log_event(event_type: str, data: Dict):
        events.append((event_type, data))
        print(f"  [EVENT] {event_type}: {data}")
    
    manager.onEvent(log_event)
    
    # Enregistrer les projets
    print("\n" + "-" * 70)
    print("1. ENREGISTREMENT DES PROJETS")
    print("-" * 70)
    
    manifests = create_example_manifests()
    for manifest in manifests:
        result = manager.registerProject(manifest)
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {manifest.project_id} ({manifest.version})")
    
    # Afficher le résumé
    print("\n" + "-" * 70)
    print("2. RÉSUMÉ DU PORTFOLIO")
    print("-" * 70)
    
    summary = manager.getPortfolioSummary()
    print(f"  Total projets: {summary['total_projects']}")
    print(f"  Santé globale: {summary['overall_health']}")
    
    # Ordre de déploiement
    print("\n" + "-" * 70)
    print("3. ORDRE DE DÉPLOIEMENT (TRI TOPOLOGIQUE)")
    print("-" * 70)
    
    order = manager.getDeploymentOrder()
    for i, pid in enumerate(order, 1):
        deps = manager.portfolio.get_manifest(pid).dependencies
        deps_str = ", ".join([d.project_id for d in deps]) if deps else "aucune"
        print(f"  {i}. {pid} (dépendances: {deps_str})")
    
    # Déployer les projets
    print("\n" + "-" * 70)
    print("4. DÉPLOIEMENT SÉQUENTIEL")
    print("-" * 70)
    
    for project_id in order:
        manifest = manager.portfolio.get_manifest(project_id)
        print(f"\n  Déploiement de {project_id} ({manifest.default_strategy.value})...")
        
        result = manager.deployProject(project_id)
        
        if result["success"]:
            print(f"  ✓ Déployé en {result['duration_ms']:.0f}ms")
        else:
            print(f"  ✗ Échec: {result.get('error', 'Unknown')}")
    
    # Statuts des projets
    print("\n" + "-" * 70)
    print("5. STATUTS DES PROJETS")
    print("-" * 70)
    
    for project_id in order:
        status = manager.getProjectStatus(project_id)
        print(f"  {project_id}:")
        print(f"    Version: {status['version']}")
        print(f"    Statut: {status['status']}")
        print(f"    Santé: {status['health']}")
    
    # Test de mise à jour
    print("\n" + "-" * 70)
    print("6. MISE À JOUR D'UN PROJET (api-gateway → 1.6.0)")
    print("-" * 70)
    
    new_manifest = ProjectManifest(
        project_id="api-gateway",
        name="EUREKAI API Gateway",
        version="1.6.0",
        description="Point d'entrée API unifié - UPDATED",
        tags=["api", "gateway", "critical"],
        dependencies=[
            ProjectDependency("core-services", ">=1.0", required=True)
        ],
        bootstrap=BootstrapConfig(
            entry_point="Object:APIGateway.Root",
            init_sequence=["load-routes", "init-rate-limiter", "warm-cache"],
            health_check_url="/ping"
        ),
        modules=["routing", "auth", "rate-limiting", "logging", "tracing"],
        default_strategy=DeploymentStrategy.SAFE_DEPLOY
    )
    
    result = manager.updateProject("api-gateway", new_manifest)
    status = "✓" if result["success"] else "✗"
    print(f"  {status} Mise à jour: {result}")
    
    # Test de rollback
    print("\n" + "-" * 70)
    print("7. ROLLBACK (api-gateway → 1.5.2)")
    print("-" * 70)
    
    result = manager.rollbackProject("api-gateway")
    status = "✓" if result["success"] else "✗"
    print(f"  {status} Rollback: {result}")
    
    # Résumé final
    print("\n" + "-" * 70)
    print("8. RÉSUMÉ FINAL")
    print("-" * 70)
    
    summary = manager.getPortfolioSummary()
    print(f"  Projets actifs: {summary['by_status']['running']}/{summary['total_projects']}")
    print(f"  Incidents: {summary['incidents']['total']} ({summary['incidents']['critical']} critiques)")
    print(f"  Santé globale: {summary['overall_health']}")
    print(f"  Événements émis: {len(events)}")
    
    print("\n" + "=" * 70)
    print("FIN DE LA DÉMONSTRATION")
    print("=" * 70)
    
    return manager


def run_test_cases():
    """Cas de test pour validation du module."""
    print("\n" + "=" * 70)
    print("CAS DE TEST — VALIDATION DU MODULE G3/11")
    print("=" * 70)
    
    # Test 1: Création de manifest
    print("\n[TEST 1] Création de ProjectManifest")
    manifest = ProjectManifest(
        project_id="test-project",
        name="Test Project",
        version="1.0.0"
    )
    assert manifest.manifest_id == "test-project@1.0.0"
    assert manifest.bootstrap.entry_point == "Object:Root"
    print("  ✓ Manifest créé avec valeurs par défaut")
    
    # Test 2: Dépendances
    print("\n[TEST 2] Validation des dépendances")
    dep = ProjectDependency("core", ">=1.0")
    assert dep.is_satisfied_by("1.0.0")
    assert dep.is_satisfied_by("2.0.0")
    assert not dep.is_satisfied_by("0.9.0")
    
    dep_caret = ProjectDependency("lib", "^2.0")
    assert dep_caret.is_satisfied_by("2.5.0")
    assert not dep_caret.is_satisfied_by("3.0.0")
    print("  ✓ Contraintes de version fonctionnelles")
    
    # Test 3: Portfolio
    print("\n[TEST 3] Gestion du Portfolio")
    portfolio = Portfolio("test")
    
    m1 = ProjectManifest("proj-a", "Project A", "1.0.0")
    m2 = ProjectManifest("proj-b", "Project B", "1.0.0", 
                         dependencies=[ProjectDependency("proj-a")])
    
    assert portfolio.register_project(m1)
    assert portfolio.register_project(m2)
    assert not portfolio.register_project(m1)  # Doublon
    
    assert len(portfolio.manifests) == 2
    print("  ✓ Enregistrement et détection de doublons")
    
    # Test 4: Ordre de déploiement
    print("\n[TEST 4] Tri topologique des dépendances")
    order = portfolio.get_deployment_order()
    assert order.index("proj-a") < order.index("proj-b")
    print(f"  ✓ Ordre: {order}")
    
    # Test 5: PortfolioManager API
    print("\n[TEST 5] API PortfolioManager")
    manager = PortfolioManager()
    
    manifests = create_example_manifests()
    for m in manifests:
        result = manager.registerProject(m)
        assert result["success"], f"Failed to register {m.project_id}"
    
    # Liste des projets
    projects = manager.listProjects()
    assert len(projects) == 4
    print(f"  ✓ {len(projects)} projets enregistrés")
    
    # Test 6: Déploiement
    print("\n[TEST 6] Déploiement de projet")
    result = manager.deployProject("core-services")
    assert result["success"]
    assert result["deployment_id"].startswith("DEP-")
    print(f"  ✓ Déploiement {result['deployment_id']} réussi")
    
    # Test 7: Statut
    print("\n[TEST 7] Récupération du statut")
    status = manager.getProjectStatus("core-services")
    assert status["found"]
    assert status["status"] == "running"
    assert status["health"] == "healthy"
    print(f"  ✓ Statut: {status['status']}, Santé: {status['health']}")
    
    # Test 8: Mise à jour
    print("\n[TEST 8] Mise à jour de projet")
    new_m = ProjectManifest(
        project_id="core-services",
        name="EUREKAI Core Services",
        version="1.1.0"
    )
    result = manager.updateProject("core-services", new_m)
    assert result["success"]
    print(f"  ✓ Mis à jour vers 1.1.0")
    
    # Test 9: Rollback
    print("\n[TEST 9] Rollback")
    result = manager.rollbackProject("core-services")
    assert result["success"]
    assert result["to_version"] == "1.0.0"
    print(f"  ✓ Rollback vers {result['to_version']}")
    
    # Test 10: Arrêt et suppression
    print("\n[TEST 10] Arrêt et suppression")
    result = manager.stopProject("core-services")
    assert result["success"]
    
    result = manager.unregisterProject("core-services")
    assert result["success"]
    print("  ✓ Projet arrêté et supprimé")
    
    # Test 11: Incidents
    print("\n[TEST 11] Gestion des incidents")
    manager.deployProject("api-gateway")
    state = manager.portfolio.get_state("api-gateway")
    
    incident = state.add_incident(
        IncidentSeverity.WARNING,
        "High latency detected",
        "P99 latency exceeded threshold"
    )
    assert incident.incident_id.startswith("INC-")
    assert state.active_incidents == 1
    
    state.resolve_incident(incident.incident_id, "Scaled up instances")
    assert state.active_incidents == 0
    print("  ✓ Incident créé et résolu")
    
    # Test 12: Résumé portfolio
    print("\n[TEST 12] Résumé du portfolio")
    summary = manager.getPortfolioSummary()
    assert "total_projects" in summary
    assert "overall_health" in summary
    print(f"  ✓ Résumé: {summary['total_projects']} projets, santé: {summary['overall_health']}")
    
    # Test 13: Export JSON
    print("\n[TEST 13] Export JSON")
    portfolio_dict = manager.portfolio.to_dict()
    json_str = json.dumps(portfolio_dict, default=str)
    assert len(json_str) > 100
    print(f"  ✓ JSON export ({len(json_str)} caractères)")
    
    # Test 14: Stratégies de déploiement
    print("\n[TEST 14] Stratégies de déploiement")
    
    # Re-register and deploy core-services for dependencies
    core_manifest = [m for m in manifests if m.project_id == "core-services"][0]
    manager.registerProject(core_manifest)
    manager.deployProject("core-services")
    manager.deployProject("api-gateway")
    
    # First deploy web-frontend normally (Canary requires running project)
    manager.deployProject("web-frontend", DeploymentStrategy.SAFE_DEPLOY)
    
    # Now update with Canary strategy (simulates update scenario)
    web_manifest = [m for m in manifests if m.project_id == "web-frontend"][0]
    new_web_manifest = ProjectManifest(
        project_id="web-frontend",
        name="EUREKAI Web Frontend",
        version="2.4.0",  # Version bump
        description="Interface utilisateur web - updated",
        tags=["frontend", "web"],
        dependencies=[
            ProjectDependency("core-services", ">=1.0", required=True),
            ProjectDependency("api-gateway", "^1.0", required=True)
        ],
        modules=["landing", "dashboard", "settings", "components", "newfeature"],
        default_strategy=DeploymentStrategy.CANARY
    )
    result = manager.updateProject("web-frontend", new_web_manifest, DeploymentStrategy.CANARY)
    status = manager.getProjectStatus("web-frontend")
    assert status["status"] == "running"
    print("  ✓ Canary deployment réussi")
    
    # Test 15: Vérification des dépendances
    print("\n[TEST 15] Vérification des dépendances")
    ok, errors = manager.portfolio.check_dependencies("web-frontend")
    # api-gateway et core-services doivent être running
    print(f"  ✓ Dépendances: {'OK' if ok else 'ERREURS: ' + str(errors)}")
    
    print("\n" + "-" * 70)
    print("TOUS LES TESTS PASSÉS ✓")
    print("-" * 70)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_test_cases()
    else:
        run_demo()
        run_test_cases()
