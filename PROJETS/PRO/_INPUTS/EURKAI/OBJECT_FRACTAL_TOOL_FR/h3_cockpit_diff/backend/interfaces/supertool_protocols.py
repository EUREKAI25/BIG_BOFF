"""
H3 — Interfaces SuperTools
===========================

Protocols définissant les interfaces des SuperTools consommés par H3.
Ces interfaces permettent de mocker les SuperTools dans les tests.

Périmètre: Uniquement les définitions d'interface, pas d'implémentation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# =============================================================================
# RÉSULTATS D'OPÉRATION
# =============================================================================

@dataclass
class SuperToolResult:
    """Résultat standard d'une opération SuperTool."""
    
    success: bool
    object_id: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None


# =============================================================================
# PROTOCOLS SUPERTOOLS
# =============================================================================

@runtime_checkable
class ISuperCreate(Protocol):
    """Interface pour SuperCreate — création d'objets fractals."""
    
    async def execute(
        self,
        object_type: str,
        object_path: str,
        attributes: Optional[Dict[str, Any]] = None,
        methods: Optional[Dict[str, Any]] = None,
        rules: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        """
        Crée un nouvel objet fractal.
        
        Args:
            object_type: Type catalog de l'objet
            object_path: Chemin fractal de destination
            attributes: Bundle attributes
            methods: Bundle methods
            rules: Bundle rules
            relations: Bundle relations
            tags: Liste des tags
            metadata: Métadonnées additionnelles
            
        Returns:
            SuperToolResult avec l'ID de l'objet créé
        """
        ...


@runtime_checkable
class ISuperUpdate(Protocol):
    """Interface pour SuperUpdate — modification d'objets fractals."""
    
    async def execute(
        self,
        object_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        methods: Optional[Dict[str, Any]] = None,
        rules: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None,
        tags_add: Optional[List[str]] = None,
        tags_remove: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        """
        Met à jour un objet fractal existant.
        
        Args:
            object_id: ID de l'objet à modifier
            attributes: Modifications du bundle attributes
            methods: Modifications du bundle methods
            rules: Modifications du bundle rules
            relations: Modifications du bundle relations
            tags_add: Tags à ajouter
            tags_remove: Tags à supprimer
            metadata: Métadonnées additionnelles
            
        Returns:
            SuperToolResult
        """
        ...


@runtime_checkable
class ISuperDelete(Protocol):
    """Interface pour SuperDelete — suppression d'objets fractals."""
    
    async def execute(
        self,
        object_id: str,
        hard_delete: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        """
        Supprime un objet fractal.
        
        Args:
            object_id: ID de l'objet à supprimer
            hard_delete: Si True, suppression définitive. Si False, désactivation.
            metadata: Métadonnées additionnelles
            
        Returns:
            SuperToolResult
        """
        ...


@runtime_checkable
class ISuperRead(Protocol):
    """Interface pour SuperRead — lecture d'objets fractals."""
    
    async def execute(
        self,
        object_id: str,
        include_bundles: bool = True,
        include_relations: bool = False
    ) -> SuperToolResult:
        """
        Lit un objet fractal.
        
        Args:
            object_id: ID de l'objet à lire
            include_bundles: Inclure tous les bundles
            include_relations: Inclure les relations résolues
            
        Returns:
            SuperToolResult avec les données de l'objet
        """
        ...


# =============================================================================
# INTERFACE COMPOSITE
# =============================================================================

class ISuperToolRegistry(ABC):
    """
    Registry des SuperTools disponibles.
    
    Permet d'accéder aux SuperTools de manière centralisée
    et facilite l'injection de dépendances pour les tests.
    """
    
    @property
    @abstractmethod
    def create(self) -> ISuperCreate:
        """Retourne l'instance de SuperCreate."""
        ...
    
    @property
    @abstractmethod
    def update(self) -> ISuperUpdate:
        """Retourne l'instance de SuperUpdate."""
        ...
    
    @property
    @abstractmethod
    def delete(self) -> ISuperDelete:
        """Retourne l'instance de SuperDelete."""
        ...
    
    @property
    @abstractmethod
    def read(self) -> ISuperRead:
        """Retourne l'instance de SuperRead."""
        ...


# =============================================================================
# INTERFACE FRACTAL STATE
# =============================================================================

@runtime_checkable
class IFractalStateProvider(Protocol):
    """Interface pour accéder à l'état actuel de la fractale."""
    
    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère l'état actuel d'un objet.
        
        Args:
            object_id: ID de l'objet
            
        Returns:
            Dictionnaire représentant l'objet ou None si non trouvé
        """
        ...
    
    async def get_objects_by_path(self, path_prefix: str) -> List[Dict[str, Any]]:
        """
        Récupère les objets sous un chemin donné.
        
        Args:
            path_prefix: Préfixe de chemin fractal
            
        Returns:
            Liste des objets correspondants
        """
        ...
    
    async def object_exists(self, object_id: str) -> bool:
        """
        Vérifie si un objet existe.
        
        Args:
            object_id: ID de l'objet
            
        Returns:
            True si l'objet existe
        """
        ...


# =============================================================================
# INTERFACE AUDIT LOG
# =============================================================================

@runtime_checkable
class IAuditLogProvider(Protocol):
    """Interface pour la journalisation d'audit."""
    
    async def log_action(
        self,
        action_type: str,
        user_id: str,
        context: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """
        Journalise une action.
        
        Args:
            action_type: Type d'action
            user_id: ID de l'utilisateur
            context: Contexte de l'action
            success: Succès de l'action
            error_message: Message d'erreur si échec
            
        Returns:
            ID de l'entrée de log créée
        """
        ...
    
    async def get_logs(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs.
        
        Args:
            filter_by: Filtres à appliquer
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des entrées de log
        """
        ...


# =============================================================================
# STUBS POUR DÉVELOPPEMENT / TESTS
# =============================================================================

class StubSuperCreate:
    """Stub de SuperCreate pour les tests."""
    
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.next_id: int = 1
        self.should_fail: bool = False
        self.fail_message: str = "Stub failure"
    
    async def execute(
        self,
        object_type: str,
        object_path: str,
        attributes: Optional[Dict[str, Any]] = None,
        methods: Optional[Dict[str, Any]] = None,
        rules: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        self.calls.append({
            "object_type": object_type,
            "object_path": object_path,
            "attributes": attributes,
            "methods": methods,
            "rules": rules,
            "relations": relations,
            "tags": tags,
            "metadata": metadata
        })
        
        if self.should_fail:
            return SuperToolResult(
                success=False,
                error_code="STUB_ERROR",
                error_details=self.fail_message
            )
        
        object_id = f"obj-{self.next_id:04d}"
        self.next_id += 1
        
        return SuperToolResult(
            success=True,
            object_id=object_id,
            message=f"Created {object_type} at {object_path}"
        )


class StubSuperUpdate:
    """Stub de SuperUpdate pour les tests."""
    
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.should_fail: bool = False
        self.fail_message: str = "Stub failure"
    
    async def execute(
        self,
        object_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        methods: Optional[Dict[str, Any]] = None,
        rules: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None,
        tags_add: Optional[List[str]] = None,
        tags_remove: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        self.calls.append({
            "object_id": object_id,
            "attributes": attributes,
            "methods": methods,
            "rules": rules,
            "relations": relations,
            "tags_add": tags_add,
            "tags_remove": tags_remove,
            "metadata": metadata
        })
        
        if self.should_fail:
            return SuperToolResult(
                success=False,
                error_code="STUB_ERROR",
                error_details=self.fail_message
            )
        
        return SuperToolResult(
            success=True,
            object_id=object_id,
            message=f"Updated {object_id}"
        )


class StubSuperDelete:
    """Stub de SuperDelete pour les tests."""
    
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.should_fail: bool = False
        self.fail_message: str = "Stub failure"
    
    async def execute(
        self,
        object_id: str,
        hard_delete: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SuperToolResult:
        self.calls.append({
            "object_id": object_id,
            "hard_delete": hard_delete,
            "metadata": metadata
        })
        
        if self.should_fail:
            return SuperToolResult(
                success=False,
                error_code="STUB_ERROR",
                error_details=self.fail_message
            )
        
        action = "Deleted" if hard_delete else "Disabled"
        return SuperToolResult(
            success=True,
            object_id=object_id,
            message=f"{action} {object_id}"
        )


class StubSuperRead:
    """Stub de SuperRead pour les tests."""
    
    def __init__(self) -> None:
        self.objects: Dict[str, Dict[str, Any]] = {}
        self.calls: List[Dict[str, Any]] = []
    
    def add_object(self, object_id: str, data: Dict[str, Any]) -> None:
        """Ajoute un objet au stub."""
        self.objects[object_id] = data
    
    async def execute(
        self,
        object_id: str,
        include_bundles: bool = True,
        include_relations: bool = False
    ) -> SuperToolResult:
        self.calls.append({
            "object_id": object_id,
            "include_bundles": include_bundles,
            "include_relations": include_relations
        })
        
        if object_id not in self.objects:
            return SuperToolResult(
                success=False,
                error_code="NOT_FOUND",
                error_details=f"Object {object_id} not found"
            )
        
        return SuperToolResult(
            success=True,
            object_id=object_id,
            data=self.objects[object_id]
        )


class StubSuperToolRegistry(ISuperToolRegistry):
    """Registry de stubs pour les tests."""
    
    def __init__(self) -> None:
        self._create = StubSuperCreate()
        self._update = StubSuperUpdate()
        self._delete = StubSuperDelete()
        self._read = StubSuperRead()
    
    @property
    def create(self) -> StubSuperCreate:
        return self._create
    
    @property
    def update(self) -> StubSuperUpdate:
        return self._update
    
    @property
    def delete(self) -> StubSuperDelete:
        return self._delete
    
    @property
    def read(self) -> StubSuperRead:
        return self._read


class StubFractalStateProvider:
    """Stub du provider d'état fractal pour les tests."""
    
    def __init__(self) -> None:
        self.objects: Dict[str, Dict[str, Any]] = {}
    
    def add_object(self, object_id: str, data: Dict[str, Any]) -> None:
        """Ajoute un objet au stub."""
        self.objects[object_id] = data
    
    async def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.objects.get(object_id)
    
    async def get_objects_by_path(self, path_prefix: str) -> List[Dict[str, Any]]:
        return [
            obj for obj in self.objects.values()
            if obj.get("path", "").startswith(path_prefix)
        ]
    
    async def object_exists(self, object_id: str) -> bool:
        return object_id in self.objects


class StubAuditLogProvider:
    """Stub du provider d'audit log pour les tests."""
    
    def __init__(self) -> None:
        self.logs: List[Dict[str, Any]] = []
        self.next_id: int = 1
    
    async def log_action(
        self,
        action_type: str,
        user_id: str,
        context: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        log_id = f"log-{self.next_id:04d}"
        self.next_id += 1
        
        self.logs.append({
            "log_id": log_id,
            "action_type": action_type,
            "user_id": user_id,
            "context": context,
            "success": success,
            "error_message": error_message
        })
        
        return log_id
    
    async def get_logs(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        results = self.logs
        
        if filter_by:
            for key, value in filter_by.items():
                results = [log for log in results if log.get(key) == value]
        
        return results[:limit]
