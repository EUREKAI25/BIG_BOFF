"""
H3 — DiffService
=================

Service de gestion des diffs fractals selon le pattern GEVR.
- GET: Récupérer l'état actuel / proposé / diffs en attente
- EXECUTE: Calculer le diff, préparer les opérations
- VALIDATE: Appliquer seulement ce qui a été accepté
- RENDER: Retourner un résultat lisible pour le front

Périmètre: Orchestration uniquement, délègue aux SuperTools pour les mutations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from models.diff_models import (
    ApplyDiffRequest,
    BatchDecisionRequest,
    BundleDiff,
    ChangeType,
    Decision,
    DecisionRequest,
    DiffAuditEntry,
    DiffAuditLog,
    DiffOperationResult,
    DiffStatus,
    FieldDiff,
    FractalDiff,
    ObjectDiff,
    Operation,
    TagsDiff,
)
from interfaces.supertool_protocols import (
    IAuditLogProvider,
    IFractalStateProvider,
    ISuperToolRegistry,
    StubAuditLogProvider,
    StubFractalStateProvider,
    StubSuperToolRegistry,
)


class DiffComputationError(Exception):
    """Erreur lors du calcul d'un diff."""
    pass


class DiffValidationError(Exception):
    """Erreur lors de la validation d'un diff."""
    pass


class DiffApplicationError(Exception):
    """Erreur lors de l'application d'un diff."""
    pass


class DiffService:
    """
    Service de gestion des diffs fractals.
    
    Implémente le pattern GEVR pour la manipulation des diffs:
    - GET: get_diff, get_pending_diffs, get_audit_log
    - EXECUTE: compute_diff, prepare_application
    - VALIDATE: submit_decisions, validate_diff
    - RENDER: apply_diff, get_application_preview
    
    Ce service ne fait JAMAIS d'écriture directe sur la fractale.
    Toutes les mutations passent par les SuperTools.
    """
    
    def __init__(
        self,
        supertools: Optional[ISuperToolRegistry] = None,
        state_provider: Optional[IFractalStateProvider] = None,
        audit_provider: Optional[IAuditLogProvider] = None
    ) -> None:
        """
        Initialise le DiffService.
        
        Args:
            supertools: Registry des SuperTools (stub par défaut)
            state_provider: Provider d'état fractal (stub par défaut)
            audit_provider: Provider d'audit log (stub par défaut)
        """
        # TODO: Injecter les vraies implémentations
        self._supertools = supertools or StubSuperToolRegistry()
        self._state_provider = state_provider or StubFractalStateProvider()
        self._audit_provider = audit_provider or StubAuditLogProvider()
        
        # Storage en mémoire pour les diffs (TODO: persister)
        self._diffs: Dict[str, FractalDiff] = {}
        self._audit_logs: Dict[str, DiffAuditLog] = {}
    
    # =========================================================================
    # GET — Récupération
    # =========================================================================
    
    async def get_diff(self, diff_id: str) -> Optional[FractalDiff]:
        """
        Récupère un diff par son ID.
        
        Args:
            diff_id: ID du diff
            
        Returns:
            FractalDiff ou None si non trouvé
        """
        return self._diffs.get(diff_id)
    
    async def get_pending_diffs(
        self,
        scenario_id: Optional[str] = None,
        status: Optional[DiffStatus] = None
    ) -> List[FractalDiff]:
        """
        Récupère les diffs en attente.
        
        Args:
            scenario_id: Filtrer par scénario
            status: Filtrer par statut
            
        Returns:
            Liste des diffs correspondants
        """
        results = list(self._diffs.values())
        
        if scenario_id:
            results = [d for d in results if d.scenario_id == scenario_id]
        
        if status:
            results = [d for d in results if d.status == status]
        else:
            # Par défaut, exclure les diffs déjà appliqués ou en erreur
            results = [d for d in results if d.status not in (DiffStatus.APPLIED, DiffStatus.ERROR)]
        
        # Trier par date de création décroissante
        results.sort(key=lambda d: d.created_at, reverse=True)
        
        return results
    
    async def get_audit_log(self, diff_id: str) -> Optional[DiffAuditLog]:
        """
        Récupère le journal d'audit d'un diff.
        
        Args:
            diff_id: ID du diff
            
        Returns:
            DiffAuditLog ou None
        """
        return self._audit_logs.get(diff_id)
    
    # =========================================================================
    # EXECUTE — Calcul du diff
    # =========================================================================
    
    async def compute_diff(
        self,
        scenario_id: str,
        current_state: Dict[str, Dict[str, Any]],
        proposed_state: Dict[str, Dict[str, Any]],
        scenario_label: Optional[str] = None
    ) -> FractalDiff:
        """
        Calcule un diff entre l'état actuel et l'état proposé.
        
        Args:
            scenario_id: ID du scénario/SuperTool source
            current_state: État actuel (dict object_id -> object_data)
            proposed_state: État proposé (dict object_id -> object_data)
            scenario_label: Label lisible du scénario
            
        Returns:
            FractalDiff calculé
            
        Raises:
            DiffComputationError: En cas d'erreur de calcul
        """
        try:
            changes: List[ObjectDiff] = []
            
            all_ids = set(current_state.keys()) | set(proposed_state.keys())
            
            for object_id in all_ids:
                current = current_state.get(object_id)
                proposed = proposed_state.get(object_id)
                
                if current is None and proposed is not None:
                    # Création
                    change = self._compute_create_diff(object_id, proposed)
                    changes.append(change)
                
                elif current is not None and proposed is None:
                    # Suppression
                    change = self._compute_delete_diff(object_id, current)
                    changes.append(change)
                
                elif current is not None and proposed is not None:
                    # Modification potentielle
                    change = self._compute_update_diff(object_id, current, proposed)
                    if change.has_bundle_changes or change.tags and change.tags.has_changes:
                        changes.append(change)
            
            # Créer le diff global
            diff = FractalDiff(
                scenario_id=scenario_id,
                scenario_label=scenario_label,
                changes=changes
            )
            
            # Stocker le diff
            self._diffs[diff.diff_id] = diff
            
            # Initialiser le log d'audit
            self._audit_logs[diff.diff_id] = DiffAuditLog(diff_id=diff.diff_id)
            
            # Logger la création
            await self._log_action(
                diff_id=diff.diff_id,
                scenario_id=scenario_id,
                action="compute",
                user_id="system",
                context={"changes_count": len(changes)}
            )
            
            return diff
            
        except Exception as e:
            raise DiffComputationError(f"Failed to compute diff: {str(e)}") from e
    
    def _compute_create_diff(
        self,
        object_id: str,
        proposed: Dict[str, Any]
    ) -> ObjectDiff:
        """Calcule le diff pour une création."""
        return ObjectDiff(
            object_id=object_id,
            object_type=proposed.get("type", "unknown"),
            object_path=proposed.get("path", ""),
            object_label=proposed.get("label"),
            operation=Operation.CREATE,
            attributes=self._compute_bundle_diff("attributes", None, proposed.get("attributes")),
            methods=self._compute_bundle_diff("methods", None, proposed.get("methods")),
            rules=self._compute_bundle_diff("rules", None, proposed.get("rules")),
            relations=self._compute_bundle_diff("relations", None, proposed.get("relations")),
            tags=self._compute_tags_diff(None, proposed.get("tags", []))
        )
    
    def _compute_delete_diff(
        self,
        object_id: str,
        current: Dict[str, Any]
    ) -> ObjectDiff:
        """Calcule le diff pour une suppression."""
        return ObjectDiff(
            object_id=object_id,
            object_type=current.get("type", "unknown"),
            object_path=current.get("path", ""),
            object_label=current.get("label"),
            operation=Operation.DELETE,
            attributes=self._compute_bundle_diff("attributes", current.get("attributes"), None),
            methods=self._compute_bundle_diff("methods", current.get("methods"), None),
            rules=self._compute_bundle_diff("rules", current.get("rules"), None),
            relations=self._compute_bundle_diff("relations", current.get("relations"), None),
            tags=self._compute_tags_diff(current.get("tags", []), None)
        )
    
    def _compute_update_diff(
        self,
        object_id: str,
        current: Dict[str, Any],
        proposed: Dict[str, Any]
    ) -> ObjectDiff:
        """Calcule le diff pour une modification."""
        return ObjectDiff(
            object_id=object_id,
            object_type=current.get("type", "unknown"),
            object_path=current.get("path", ""),
            object_label=proposed.get("label") or current.get("label"),
            operation=Operation.UPDATE,
            attributes=self._compute_bundle_diff(
                "attributes",
                current.get("attributes"),
                proposed.get("attributes")
            ),
            methods=self._compute_bundle_diff(
                "methods",
                current.get("methods"),
                proposed.get("methods")
            ),
            rules=self._compute_bundle_diff(
                "rules",
                current.get("rules"),
                proposed.get("rules")
            ),
            relations=self._compute_bundle_diff(
                "relations",
                current.get("relations"),
                proposed.get("relations")
            ),
            tags=self._compute_tags_diff(
                current.get("tags", []),
                proposed.get("tags", [])
            )
        )
    
    def _compute_bundle_diff(
        self,
        bundle_type: str,
        current: Optional[Dict[str, Any]],
        proposed: Optional[Dict[str, Any]]
    ) -> Optional[BundleDiff]:
        """Calcule le diff sur un bundle."""
        if current is None and proposed is None:
            return None
        
        current = current or {}
        proposed = proposed or {}
        
        all_fields = set(current.keys()) | set(proposed.keys())
        fields: List[FieldDiff] = []
        
        for field_name in all_fields:
            old_value = current.get(field_name)
            new_value = proposed.get(field_name)
            
            if old_value is None and new_value is not None:
                change_type = ChangeType.ADDED
            elif old_value is not None and new_value is None:
                change_type = ChangeType.REMOVED
            elif old_value != new_value:
                change_type = ChangeType.CHANGED
            else:
                change_type = ChangeType.UNCHANGED
            
            fields.append(FieldDiff(
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                change_type=change_type
            ))
        
        return BundleDiff(bundle_type=bundle_type, fields=fields)
    
    def _compute_tags_diff(
        self,
        current: Optional[List[str]],
        proposed: Optional[List[str]]
    ) -> TagsDiff:
        """Calcule le diff sur les tags."""
        current_set = set(current or [])
        proposed_set = set(proposed or [])
        
        return TagsDiff(
            added=list(proposed_set - current_set),
            removed=list(current_set - proposed_set)
        )
    
    # =========================================================================
    # VALIDATE — Soumission des décisions
    # =========================================================================
    
    async def submit_decision(
        self,
        diff_id: str,
        user_id: str,
        decision_request: DecisionRequest
    ) -> FractalDiff:
        """
        Soumet une décision pour un changement.
        
        Args:
            diff_id: ID du diff
            user_id: ID de l'utilisateur
            decision_request: Détails de la décision
            
        Returns:
            FractalDiff mis à jour
            
        Raises:
            DiffValidationError: Si le diff ou l'item n'existe pas
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {diff_id} not found")
        
        change = diff.get_change_by_id(decision_request.diff_item_id)
        if not change:
            raise DiffValidationError(
                f"Change {decision_request.diff_item_id} not found in diff {diff_id}"
            )
        
        # Appliquer la décision
        change.set_decision(
            decision=decision_request.decision,
            user_id=user_id,
            comment=decision_request.comment,
            override=decision_request.override
        )
        
        # Mettre à jour le statut global
        diff.update_status()
        
        # Logger la décision
        await self._log_action(
            diff_id=diff_id,
            scenario_id=diff.scenario_id,
            action="decision",
            user_id=user_id,
            diff_item_id=decision_request.diff_item_id,
            object_id=change.object_id,
            operation=change.operation,
            decision=decision_request.decision,
            context={
                "comment": decision_request.comment,
                "has_override": decision_request.override is not None
            }
        )
        
        return diff
    
    async def submit_batch_decisions(
        self,
        request: BatchDecisionRequest
    ) -> FractalDiff:
        """
        Soumet plusieurs décisions en batch.
        
        Args:
            request: Requête batch avec toutes les décisions
            
        Returns:
            FractalDiff mis à jour
        """
        diff = await self.get_diff(request.diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {request.diff_id} not found")
        
        for decision_req in request.decisions:
            change = diff.get_change_by_id(decision_req.diff_item_id)
            if change:
                change.set_decision(
                    decision=decision_req.decision,
                    user_id=request.user_id,
                    comment=decision_req.comment,
                    override=decision_req.override
                )
                
                await self._log_action(
                    diff_id=request.diff_id,
                    scenario_id=diff.scenario_id,
                    action="decision",
                    user_id=request.user_id,
                    diff_item_id=decision_req.diff_item_id,
                    object_id=change.object_id,
                    operation=change.operation,
                    decision=decision_req.decision,
                    context={"batch": True}
                )
        
        diff.update_status()
        return diff
    
    async def accept_all(self, diff_id: str, user_id: str) -> FractalDiff:
        """
        Accepte tous les changements en attente.
        
        Args:
            diff_id: ID du diff
            user_id: ID de l'utilisateur
            
        Returns:
            FractalDiff mis à jour
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {diff_id} not found")
        
        for change in diff.pending_changes:
            change.set_decision(
                decision=Decision.ACCEPTED,
                user_id=user_id
            )
        
        diff.update_status()
        
        await self._log_action(
            diff_id=diff_id,
            scenario_id=diff.scenario_id,
            action="accept_all",
            user_id=user_id,
            context={"accepted_count": diff.summary.accepted if diff.summary else 0}
        )
        
        return diff
    
    async def reject_all(self, diff_id: str, user_id: str) -> FractalDiff:
        """
        Rejette tous les changements en attente.
        
        Args:
            diff_id: ID du diff
            user_id: ID de l'utilisateur
            
        Returns:
            FractalDiff mis à jour
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {diff_id} not found")
        
        for change in diff.pending_changes:
            change.set_decision(
                decision=Decision.REJECTED,
                user_id=user_id
            )
        
        diff.update_status()
        
        await self._log_action(
            diff_id=diff_id,
            scenario_id=diff.scenario_id,
            action="reject_all",
            user_id=user_id,
            context={"rejected_count": diff.summary.rejected if diff.summary else 0}
        )
        
        return diff
    
    async def reset_decisions(self, diff_id: str, user_id: str) -> FractalDiff:
        """
        Réinitialise toutes les décisions.
        
        Args:
            diff_id: ID du diff
            user_id: ID de l'utilisateur
            
        Returns:
            FractalDiff mis à jour
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {diff_id} not found")
        
        for change in diff.changes:
            change.decision = Decision.PENDING
            change.user_override = None
            change.decision_comment = None
            change.decision_timestamp = None
            change.decision_user_id = None
        
        diff.update_status()
        
        await self._log_action(
            diff_id=diff_id,
            scenario_id=diff.scenario_id,
            action="reset",
            user_id=user_id,
            context={"reset_count": len(diff.changes)}
        )
        
        return diff
    
    # =========================================================================
    # RENDER — Application du diff
    # =========================================================================
    
    async def get_application_preview(
        self,
        diff_id: str
    ) -> Dict[str, Any]:
        """
        Génère un aperçu de ce qui sera appliqué.
        
        Args:
            diff_id: ID du diff
            
        Returns:
            Dictionnaire avec les détails de l'application prévue
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            raise DiffValidationError(f"Diff {diff_id} not found")
        
        accepted = diff.accepted_changes
        rejected = [c for c in diff.changes if c.decision == Decision.REJECTED]
        pending = diff.pending_changes
        
        return {
            "diff_id": diff_id,
            "status": diff.status.value,
            "can_apply": diff.is_applicable,
            "to_apply": {
                "count": len(accepted),
                "creates": len([c for c in accepted if c.operation == Operation.CREATE]),
                "updates": len([c for c in accepted if c.operation == Operation.UPDATE]),
                "deletes": len([c for c in accepted if c.operation == Operation.DELETE]),
                "disables": len([c for c in accepted if c.operation == Operation.DISABLE]),
                "items": [
                    {
                        "object_id": c.object_id,
                        "operation": c.operation.value,
                        "label": c.object_label
                    }
                    for c in accepted
                ]
            },
            "rejected": {
                "count": len(rejected),
                "items": [c.object_id for c in rejected]
            },
            "pending": {
                "count": len(pending),
                "items": [c.object_id for c in pending]
            },
            "warnings": self._compute_application_warnings(diff)
        }
    
    def _compute_application_warnings(self, diff: FractalDiff) -> List[str]:
        """Calcule les avertissements pour l'application."""
        warnings = []
        
        if diff.pending_changes:
            warnings.append(
                f"{len(diff.pending_changes)} change(s) still pending - "
                "they will NOT be applied"
            )
        
        # Vérifier les dépendances (simplifié)
        deleted_ids = {c.object_id for c in diff.changes 
                      if c.operation == Operation.DELETE and c.decision == Decision.ACCEPTED}
        
        for change in diff.accepted_changes:
            if change.operation == Operation.UPDATE:
                # TODO: Vérifier si l'objet existe toujours
                pass
            elif change.relations:
                # Vérifier si les relations pointent vers des objets supprimés
                for field in change.relations.fields:
                    if field.new_value and field.new_value in deleted_ids:
                        warnings.append(
                            f"Object {change.object_id} has relation to "
                            f"{field.new_value} which is being deleted"
                        )
        
        return warnings
    
    async def apply_diff(
        self,
        request: ApplyDiffRequest
    ) -> DiffOperationResult:
        """
        Applique un diff validé via les SuperTools.
        
        GARDE-FOU: Cette méthode ne fait AUCUNE écriture directe.
        Toutes les mutations passent par SuperCreate/SuperUpdate/SuperDelete.
        
        Args:
            request: Requête d'application avec confirmation explicite
            
        Returns:
            DiffOperationResult avec le détail de l'application
            
        Raises:
            DiffApplicationError: Si le diff ne peut pas être appliqué
        """
        diff = await self.get_diff(request.diff_id)
        if not diff:
            raise DiffApplicationError(f"Diff {request.diff_id} not found")
        
        # Vérifier que le diff est applicable
        if not diff.is_applicable:
            return DiffOperationResult(
                success=False,
                diff_id=request.diff_id,
                message="Diff is not applicable - no accepted changes or invalid status",
                errors=["Cannot apply diff in current state"]
            )
        
        # Récupérer les changements à appliquer
        changes_to_apply = diff.accepted_changes
        if not changes_to_apply:
            return DiffOperationResult(
                success=False,
                diff_id=request.diff_id,
                message="No changes to apply",
                errors=["All changes were rejected or are still pending"]
            )
        
        # Appliquer chaque changement
        applied_count = 0
        failed_count = 0
        skipped_count = 0
        errors: List[str] = []
        
        for change in changes_to_apply:
            try:
                result = await self._apply_single_change(
                    change,
                    request.user_id,
                    diff.scenario_id
                )
                
                if result.success:
                    applied_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{change.object_id}: {result.error_details}")
                    
            except Exception as e:
                failed_count += 1
                errors.append(f"{change.object_id}: {str(e)}")
        
        # Compter les skipped (rejected + pending)
        skipped_count = len(diff.changes) - len(changes_to_apply)
        
        # Mettre à jour le statut du diff
        if failed_count == 0:
            diff.status = DiffStatus.APPLIED
            success = True
            message = f"Successfully applied {applied_count} change(s)"
        elif applied_count > 0:
            diff.status = DiffStatus.PARTIAL
            success = True
            message = f"Partially applied: {applied_count} success, {failed_count} failed"
        else:
            diff.status = DiffStatus.ERROR
            success = False
            message = f"Application failed: {failed_count} error(s)"
        
        diff.updated_at = datetime.utcnow()
        
        # Logger l'application
        await self._log_action(
            diff_id=request.diff_id,
            scenario_id=diff.scenario_id,
            action="apply",
            user_id=request.user_id,
            context={
                "applied": applied_count,
                "failed": failed_count,
                "skipped": skipped_count
            },
            success=success,
            error_message="; ".join(errors) if errors else None
        )
        
        return DiffOperationResult(
            success=success,
            diff_id=request.diff_id,
            message=message,
            applied_count=applied_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            errors=errors,
            updated_diff=diff
        )
    
    async def _apply_single_change(
        self,
        change: ObjectDiff,
        user_id: str,
        scenario_id: str
    ) -> Any:
        """
        Applique un changement unique via les SuperTools.
        
        Args:
            change: Changement à appliquer
            user_id: ID de l'utilisateur
            scenario_id: ID du scénario
            
        Returns:
            SuperToolResult
        """
        metadata = {
            "applied_by": user_id,
            "scenario_id": scenario_id,
            "diff_item_id": change.diff_item_id,
            "applied_at": datetime.utcnow().isoformat()
        }
        
        if change.operation == Operation.CREATE:
            return await self._supertools.create.execute(
                object_type=change.object_type,
                object_path=change.object_path,
                attributes=self._extract_new_values(change.attributes),
                methods=self._extract_new_values(change.methods),
                rules=self._extract_new_values(change.rules),
                relations=self._extract_new_values(change.relations),
                tags=change.tags.added if change.tags else None,
                metadata=metadata
            )
        
        elif change.operation == Operation.UPDATE:
            # Appliquer les overrides si présents
            attributes = change.user_override.get("attributes") if change.user_override else None
            methods = change.user_override.get("methods") if change.user_override else None
            rules = change.user_override.get("rules") if change.user_override else None
            relations = change.user_override.get("relations") if change.user_override else None
            
            # Sinon utiliser les nouvelles valeurs du diff
            if attributes is None:
                attributes = self._extract_new_values(change.attributes)
            if methods is None:
                methods = self._extract_new_values(change.methods)
            if rules is None:
                rules = self._extract_new_values(change.rules)
            if relations is None:
                relations = self._extract_new_values(change.relations)
            
            return await self._supertools.update.execute(
                object_id=change.object_id,
                attributes=attributes,
                methods=methods,
                rules=rules,
                relations=relations,
                tags_add=change.tags.added if change.tags else None,
                tags_remove=change.tags.removed if change.tags else None,
                metadata=metadata
            )
        
        elif change.operation == Operation.DELETE:
            return await self._supertools.delete.execute(
                object_id=change.object_id,
                hard_delete=True,
                metadata=metadata
            )
        
        elif change.operation == Operation.DISABLE:
            return await self._supertools.delete.execute(
                object_id=change.object_id,
                hard_delete=False,
                metadata=metadata
            )
        
        else:
            raise DiffApplicationError(f"Unknown operation: {change.operation}")
    
    def _extract_new_values(self, bundle: Optional[BundleDiff]) -> Optional[Dict[str, Any]]:
        """Extrait les nouvelles valeurs d'un bundle diff."""
        if not bundle:
            return None
        
        result = {}
        for field in bundle.fields:
            if field.change_type in (ChangeType.ADDED, ChangeType.CHANGED):
                result[field.field_name] = field.new_value
        
        return result if result else None
    
    # =========================================================================
    # LOGGING
    # =========================================================================
    
    async def _log_action(
        self,
        diff_id: str,
        scenario_id: str,
        action: str,
        user_id: str,
        diff_item_id: Optional[str] = None,
        object_id: Optional[str] = None,
        operation: Optional[Operation] = None,
        decision: Optional[Decision] = None,
        context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Journalise une action dans l'audit log."""
        entry = DiffAuditEntry(
            diff_id=diff_id,
            diff_item_id=diff_item_id,
            scenario_id=scenario_id,
            action=action,
            user_id=user_id,
            object_id=object_id,
            operation=operation,
            decision=decision,
            input_data=context,
            success=success,
            error_message=error_message
        )
        
        if diff_id in self._audit_logs:
            self._audit_logs[diff_id].add_entry(entry)
        
        # Également logger via le provider externe
        await self._audit_provider.log_action(
            action_type=f"diff.{action}",
            user_id=user_id,
            context={
                "diff_id": diff_id,
                "scenario_id": scenario_id,
                "diff_item_id": diff_item_id,
                "object_id": object_id,
                **(context or {})
            },
            success=success,
            error_message=error_message
        )
    
    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    
    async def delete_diff(self, diff_id: str, user_id: str) -> bool:
        """
        Supprime un diff (uniquement si non appliqué).
        
        Args:
            diff_id: ID du diff
            user_id: ID de l'utilisateur
            
        Returns:
            True si supprimé
        """
        diff = await self.get_diff(diff_id)
        if not diff:
            return False
        
        if diff.status == DiffStatus.APPLIED:
            raise DiffValidationError("Cannot delete an applied diff")
        
        await self._log_action(
            diff_id=diff_id,
            scenario_id=diff.scenario_id,
            action="delete",
            user_id=user_id
        )
        
        del self._diffs[diff_id]
        if diff_id in self._audit_logs:
            del self._audit_logs[diff_id]
        
        return True
