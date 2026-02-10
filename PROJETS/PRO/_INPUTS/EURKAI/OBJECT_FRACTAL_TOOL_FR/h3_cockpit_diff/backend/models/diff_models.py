"""
H3 — Modèles de Diff Fractal
=============================

Dataclasses Pydantic pour représenter les diffs entre états fractals.
Strictement typés, sérialisables JSON, validés.

Périmètre: Uniquement les structures de données, pas de logique métier.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================

class Operation(str, Enum):
    """Type d'opération sur un objet fractal."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DISABLE = "disable"


class ChangeType(str, Enum):
    """Type de changement sur un champ."""
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


class Decision(str, Enum):
    """Décision utilisateur sur un changement."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


class DiffStatus(str, Enum):
    """Statut global d'un diff."""
    PENDING = "pending"           # En attente de validation
    PARTIAL = "partial"           # Partiellement validé
    VALIDATED = "validated"       # Toutes les décisions prises
    APPLIED = "applied"           # Appliqué avec succès
    REJECTED = "rejected"         # Entièrement rejeté
    ERROR = "error"               # Erreur lors de l'application


# =============================================================================
# MODÈLES DE BUNDLE DIFF
# =============================================================================

class FieldDiff(BaseModel):
    """Diff sur un champ individuel d'un bundle."""
    
    field_name: str = Field(..., description="Nom du champ")
    old_value: Optional[Any] = Field(None, description="Valeur avant modification")
    new_value: Optional[Any] = Field(None, description="Valeur après modification")
    change_type: ChangeType = Field(..., description="Type de changement")
    
    @model_validator(mode="after")
    def validate_change_type_consistency(self) -> "FieldDiff":
        """Vérifie la cohérence entre change_type et les valeurs."""
        if self.change_type == ChangeType.ADDED and self.old_value is not None:
            raise ValueError("ADDED change should have old_value=None")
        if self.change_type == ChangeType.REMOVED and self.new_value is not None:
            raise ValueError("REMOVED change should have new_value=None")
        if self.change_type == ChangeType.UNCHANGED and self.old_value != self.new_value:
            raise ValueError("UNCHANGED change should have identical values")
        return self

    model_config = {"extra": "forbid"}


class BundleDiff(BaseModel):
    """Diff sur un bundle complet (attributes, methods, rules, relations)."""
    
    bundle_type: str = Field(..., description="Type de bundle: attributes|methods|rules|relations")
    fields: List[FieldDiff] = Field(default_factory=list, description="Liste des champs modifiés")
    
    @property
    def has_changes(self) -> bool:
        """Indique si le bundle contient des changements effectifs."""
        return any(f.change_type != ChangeType.UNCHANGED for f in self.fields)
    
    @property
    def added_fields(self) -> List[FieldDiff]:
        return [f for f in self.fields if f.change_type == ChangeType.ADDED]
    
    @property
    def removed_fields(self) -> List[FieldDiff]:
        return [f for f in self.fields if f.change_type == ChangeType.REMOVED]
    
    @property
    def changed_fields(self) -> List[FieldDiff]:
        return [f for f in self.fields if f.change_type == ChangeType.CHANGED]

    model_config = {"extra": "forbid"}


class TagsDiff(BaseModel):
    """Diff spécifique pour les tags."""
    
    added: List[str] = Field(default_factory=list, description="Tags ajoutés")
    removed: List[str] = Field(default_factory=list, description="Tags supprimés")
    
    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    model_config = {"extra": "forbid"}


# =============================================================================
# MODÈLE OBJECT DIFF
# =============================================================================

class ObjectDiff(BaseModel):
    """Diff complet sur un objet fractal."""
    
    # Identification
    diff_item_id: str = Field(default_factory=lambda: str(uuid4()), description="ID unique de ce diff item")
    object_id: str = Field(..., description="ID de l'objet fractal")
    object_type: str = Field(..., description="Type catalog de l'objet")
    object_path: str = Field(..., description="Chemin fractal complet")
    object_label: Optional[str] = Field(None, description="Label lisible de l'objet")
    
    # Opération
    operation: Operation = Field(..., description="Type d'opération")
    
    # Bundles impactés
    attributes: Optional[BundleDiff] = Field(None, description="Diff sur les attributes")
    methods: Optional[BundleDiff] = Field(None, description="Diff sur les methods")
    rules: Optional[BundleDiff] = Field(None, description="Diff sur les rules")
    relations: Optional[BundleDiff] = Field(None, description="Diff sur les relations")
    tags: Optional[TagsDiff] = Field(None, description="Diff sur les tags")
    
    # État de décision
    decision: Decision = Field(default=Decision.PENDING, description="Décision utilisateur")
    user_override: Optional[Dict[str, Any]] = Field(None, description="Valeurs modifiées par l'utilisateur")
    decision_comment: Optional[str] = Field(None, description="Commentaire de la décision")
    decision_timestamp: Optional[datetime] = Field(None, description="Horodatage de la décision")
    decision_user_id: Optional[str] = Field(None, description="ID de l'utilisateur décideur")
    
    @property
    def has_bundle_changes(self) -> bool:
        """Indique si au moins un bundle a des changements."""
        bundles = [self.attributes, self.methods, self.rules, self.relations]
        return any(b and b.has_changes for b in bundles) or (self.tags and self.tags.has_changes)
    
    @property
    def is_decided(self) -> bool:
        """Indique si une décision a été prise."""
        return self.decision != Decision.PENDING
    
    def set_decision(
        self, 
        decision: Decision, 
        user_id: str,
        comment: Optional[str] = None,
        override: Optional[Dict[str, Any]] = None
    ) -> None:
        """Enregistre une décision utilisateur."""
        self.decision = decision
        self.decision_user_id = user_id
        self.decision_timestamp = datetime.utcnow()
        self.decision_comment = comment
        if decision == Decision.MODIFIED and override:
            self.user_override = override

    model_config = {"extra": "forbid"}


# =============================================================================
# MODÈLE DIFF GLOBAL
# =============================================================================

class DiffSummary(BaseModel):
    """Résumé statistique d'un diff."""
    
    total_changes: int = Field(0, description="Nombre total de changements")
    creates: int = Field(0, description="Nombre de créations")
    updates: int = Field(0, description="Nombre de modifications")
    deletes: int = Field(0, description="Nombre de suppressions")
    disables: int = Field(0, description="Nombre de désactivations")
    
    pending: int = Field(0, description="Décisions en attente")
    accepted: int = Field(0, description="Décisions acceptées")
    rejected: int = Field(0, description="Décisions rejetées")
    modified: int = Field(0, description="Décisions modifiées")
    
    @classmethod
    def from_object_diffs(cls, diffs: List[ObjectDiff]) -> "DiffSummary":
        """Calcule le résumé depuis une liste de diffs."""
        summary = cls()
        summary.total_changes = len(diffs)
        
        for d in diffs:
            # Par opération
            if d.operation == Operation.CREATE:
                summary.creates += 1
            elif d.operation == Operation.UPDATE:
                summary.updates += 1
            elif d.operation == Operation.DELETE:
                summary.deletes += 1
            elif d.operation == Operation.DISABLE:
                summary.disables += 1
            
            # Par décision
            if d.decision == Decision.PENDING:
                summary.pending += 1
            elif d.decision == Decision.ACCEPTED:
                summary.accepted += 1
            elif d.decision == Decision.REJECTED:
                summary.rejected += 1
            elif d.decision == Decision.MODIFIED:
                summary.modified += 1
        
        return summary

    model_config = {"extra": "forbid"}


class FractalDiff(BaseModel):
    """
    Diff global entre deux états fractals.
    
    Structure principale consommée par le Cockpit pour la validation.
    """
    
    # Identification
    diff_id: str = Field(default_factory=lambda: str(uuid4()), description="ID unique du diff")
    scenario_id: str = Field(..., description="ID du scénario/SuperTool source")
    scenario_label: Optional[str] = Field(None, description="Label du scénario")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Dernière mise à jour")
    status: DiffStatus = Field(default=DiffStatus.PENDING, description="Statut global")
    
    # Contenu du diff
    changes: List[ObjectDiff] = Field(default_factory=list, description="Liste des changements")
    
    # Résumé (calculé)
    summary: Optional[DiffSummary] = Field(None, description="Résumé statistique")
    
    # Contexte
    source_snapshot_id: Optional[str] = Field(None, description="ID du snapshot source")
    target_snapshot_id: Optional[str] = Field(None, description="ID du snapshot cible proposé")
    
    @model_validator(mode="after")
    def compute_summary(self) -> "FractalDiff":
        """Calcule automatiquement le résumé."""
        self.summary = DiffSummary.from_object_diffs(self.changes)
        return self
    
    @property
    def created_objects(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.operation == Operation.CREATE]
    
    @property
    def updated_objects(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.operation == Operation.UPDATE]
    
    @property
    def deleted_objects(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.operation == Operation.DELETE]
    
    @property
    def disabled_objects(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.operation == Operation.DISABLE]
    
    @property
    def pending_changes(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.decision == Decision.PENDING]
    
    @property
    def accepted_changes(self) -> List[ObjectDiff]:
        return [c for c in self.changes if c.decision in (Decision.ACCEPTED, Decision.MODIFIED)]
    
    @property
    def is_fully_decided(self) -> bool:
        """Indique si toutes les décisions ont été prises."""
        return all(c.is_decided for c in self.changes)
    
    @property
    def is_applicable(self) -> bool:
        """Indique si le diff peut être appliqué (au moins une acceptation)."""
        return len(self.accepted_changes) > 0 and self.status in (DiffStatus.PENDING, DiffStatus.PARTIAL, DiffStatus.VALIDATED)
    
    def get_change_by_id(self, diff_item_id: str) -> Optional[ObjectDiff]:
        """Récupère un changement par son ID."""
        for c in self.changes:
            if c.diff_item_id == diff_item_id:
                return c
        return None
    
    def get_changes_by_object_id(self, object_id: str) -> List[ObjectDiff]:
        """Récupère tous les changements pour un objet donné."""
        return [c for c in self.changes if c.object_id == object_id]
    
    def update_status(self) -> None:
        """Met à jour le statut en fonction des décisions."""
        self.updated_at = datetime.utcnow()
        self.summary = DiffSummary.from_object_diffs(self.changes)
        
        if self.summary.pending == self.summary.total_changes:
            self.status = DiffStatus.PENDING
        elif self.summary.pending == 0:
            if self.summary.rejected == self.summary.total_changes:
                self.status = DiffStatus.REJECTED
            else:
                self.status = DiffStatus.VALIDATED
        else:
            self.status = DiffStatus.PARTIAL

    model_config = {"extra": "forbid"}


# =============================================================================
# MODÈLES D'AUDIT LOG
# =============================================================================

class DiffAuditEntry(BaseModel):
    """Entrée de journal d'audit pour une action sur un diff."""
    
    log_id: str = Field(default_factory=lambda: str(uuid4()), description="ID unique du log")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Horodatage")
    
    # Contexte
    diff_id: str = Field(..., description="ID du diff parent")
    diff_item_id: Optional[str] = Field(None, description="ID de l'item de diff concerné")
    scenario_id: str = Field(..., description="ID du scénario source")
    
    # Action
    action: str = Field(..., description="Type d'action: decision|apply|rollback")
    user_id: str = Field(..., description="ID de l'utilisateur")
    
    # Détails
    object_id: Optional[str] = Field(None, description="ID de l'objet concerné")
    operation: Optional[Operation] = Field(None, description="Opération concernée")
    decision: Optional[Decision] = Field(None, description="Décision prise")
    
    # Données
    input_data: Optional[Dict[str, Any]] = Field(None, description="Données d'entrée")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Données de sortie")
    
    # Résultat
    success: bool = Field(True, description="Succès de l'action")
    error_message: Optional[str] = Field(None, description="Message d'erreur si échec")
    
    # Commentaire
    comment: Optional[str] = Field(None, description="Commentaire utilisateur")

    model_config = {"extra": "forbid"}


class DiffAuditLog(BaseModel):
    """Journal d'audit complet pour un diff."""
    
    diff_id: str = Field(..., description="ID du diff")
    entries: List[DiffAuditEntry] = Field(default_factory=list, description="Entrées du journal")
    
    def add_entry(self, entry: DiffAuditEntry) -> None:
        """Ajoute une entrée au journal."""
        self.entries.append(entry)
    
    def get_entries_by_action(self, action: str) -> List[DiffAuditEntry]:
        """Récupère les entrées par type d'action."""
        return [e for e in self.entries if e.action == action]
    
    def get_entries_by_object(self, object_id: str) -> List[DiffAuditEntry]:
        """Récupère les entrées pour un objet donné."""
        return [e for e in self.entries if e.object_id == object_id]

    model_config = {"extra": "forbid"}


# =============================================================================
# MODÈLES DE REQUÊTE/RÉPONSE API
# =============================================================================

class DecisionRequest(BaseModel):
    """Requête pour soumettre une décision sur un changement."""
    
    diff_item_id: str = Field(..., description="ID de l'item de diff")
    decision: Decision = Field(..., description="Décision")
    comment: Optional[str] = Field(None, description="Commentaire optionnel")
    override: Optional[Dict[str, Any]] = Field(None, description="Valeurs modifiées si decision=MODIFIED")
    
    @model_validator(mode="after")
    def validate_override(self) -> "DecisionRequest":
        """Vérifie que override est fourni si decision=MODIFIED."""
        if self.decision == Decision.MODIFIED and not self.override:
            raise ValueError("override is required when decision is MODIFIED")
        return self

    model_config = {"extra": "forbid"}


class BatchDecisionRequest(BaseModel):
    """Requête pour soumettre plusieurs décisions."""
    
    diff_id: str = Field(..., description="ID du diff")
    user_id: str = Field(..., description="ID de l'utilisateur")
    decisions: List[DecisionRequest] = Field(..., description="Liste des décisions")
    
    @field_validator("decisions")
    @classmethod
    def validate_not_empty(cls, v: List[DecisionRequest]) -> List[DecisionRequest]:
        if not v:
            raise ValueError("decisions list cannot be empty")
        return v

    model_config = {"extra": "forbid"}


class ApplyDiffRequest(BaseModel):
    """Requête pour appliquer un diff validé."""
    
    diff_id: str = Field(..., description="ID du diff")
    user_id: str = Field(..., description="ID de l'utilisateur")
    confirm: bool = Field(..., description="Confirmation explicite")
    apply_only_accepted: bool = Field(default=True, description="N'appliquer que les changements acceptés")
    
    @field_validator("confirm")
    @classmethod
    def validate_confirm(cls, v: bool) -> bool:
        if not v:
            raise ValueError("confirm must be True to apply diff")
        return v

    model_config = {"extra": "forbid"}


class DiffOperationResult(BaseModel):
    """Résultat d'une opération sur un diff."""
    
    success: bool = Field(..., description="Succès global")
    diff_id: str = Field(..., description="ID du diff")
    message: str = Field(..., description="Message descriptif")
    
    applied_count: int = Field(0, description="Nombre de changements appliqués")
    failed_count: int = Field(0, description="Nombre d'échecs")
    skipped_count: int = Field(0, description="Nombre de changements ignorés")
    
    errors: List[str] = Field(default_factory=list, description="Liste des erreurs")
    warnings: List[str] = Field(default_factory=list, description="Liste des avertissements")
    
    updated_diff: Optional[FractalDiff] = Field(None, description="Diff mis à jour")

    model_config = {"extra": "forbid"}
