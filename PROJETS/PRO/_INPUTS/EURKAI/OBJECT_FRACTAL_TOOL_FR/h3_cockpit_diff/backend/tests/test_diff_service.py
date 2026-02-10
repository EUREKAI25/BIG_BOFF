"""
H3 — Tests DiffService
=======================

Tests unitaires pour le service de gestion des diffs fractals.
Couvre: calcul de diff, décisions, application, journalisation.
"""

import pytest
from datetime import datetime

import sys
sys.path.insert(0, str(__file__).replace('/tests/test_diff_service.py', ''))

from models.diff_models import (
    Operation,
    ChangeType,
    Decision,
    DiffStatus,
    DecisionRequest,
    BatchDecisionRequest,
    ApplyDiffRequest,
)
from services.diff_service import (
    DiffService,
    DiffComputationError,
    DiffValidationError,
    DiffApplicationError,
)
from interfaces.supertool_protocols import (
    StubSuperToolRegistry,
    StubFractalStateProvider,
    StubAuditLogProvider,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def service() -> DiffService:
    """Crée un DiffService avec des stubs."""
    return DiffService(
        supertools=StubSuperToolRegistry(),
        state_provider=StubFractalStateProvider(),
        audit_provider=StubAuditLogProvider()
    )


@pytest.fixture
def current_state() -> dict:
    """État actuel de test."""
    return {
        "obj-001": {
            "type": "User",
            "path": "/users/obj-001",
            "label": "John Doe",
            "attributes": {
                "name": "John",
                "email": "john@example.com",
                "age": 30
            },
            "methods": {},
            "rules": {},
            "relations": {},
            "tags": ["active", "verified"]
        },
        "obj-002": {
            "type": "Article",
            "path": "/articles/obj-002",
            "label": "My Article",
            "attributes": {
                "title": "Hello World",
                "status": "draft"
            },
            "tags": ["blog"]
        },
        "obj-003": {
            "type": "Config",
            "path": "/config/obj-003",
            "attributes": {
                "key": "value"
            }
        }
    }


@pytest.fixture
def proposed_state() -> dict:
    """État proposé de test."""
    return {
        # obj-001: MODIFIED (name, age changed, tag changed)
        "obj-001": {
            "type": "User",
            "path": "/users/obj-001",
            "label": "John Doe",
            "attributes": {
                "name": "Johnny",
                "email": "john@example.com",
                "age": 31,
                "phone": "+1234567890"  # Added
            },
            "methods": {},
            "rules": {},
            "relations": {},
            "tags": ["active", "premium"]  # "verified" removed, "premium" added
        },
        # obj-002: UNCHANGED
        "obj-002": {
            "type": "Article",
            "path": "/articles/obj-002",
            "label": "My Article",
            "attributes": {
                "title": "Hello World",
                "status": "draft"
            },
            "tags": ["blog"]
        },
        # obj-003: DELETED (not in proposed)
        # obj-004: CREATED
        "obj-004": {
            "type": "Product",
            "path": "/products/obj-004",
            "label": "New Product",
            "attributes": {
                "name": "Widget",
                "price": 99.99
            },
            "tags": ["new"]
        }
    }


# =============================================================================
# TESTS COMPUTE DIFF
# =============================================================================

class TestComputeDiff:
    """Tests pour le calcul de diff."""
    
    @pytest.mark.asyncio
    async def test_compute_simple_create(self, service: DiffService):
        """Test calcul diff avec création simple."""
        current = {}
        proposed = {
            "new-obj": {
                "type": "Item",
                "path": "/items/new-obj",
                "attributes": {"name": "Test"}
            }
        }
        
        diff = await service.compute_diff(
            scenario_id="test-scenario",
            current_state=current,
            proposed_state=proposed
        )
        
        assert diff.scenario_id == "test-scenario"
        assert len(diff.changes) == 1
        assert diff.changes[0].operation == Operation.CREATE
        assert diff.changes[0].object_id == "new-obj"
        assert diff.summary.creates == 1
    
    @pytest.mark.asyncio
    async def test_compute_simple_delete(self, service: DiffService):
        """Test calcul diff avec suppression simple."""
        current = {
            "old-obj": {
                "type": "Item",
                "path": "/items/old-obj",
                "attributes": {"name": "Old"}
            }
        }
        proposed = {}
        
        diff = await service.compute_diff(
            scenario_id="test-scenario",
            current_state=current,
            proposed_state=proposed
        )
        
        assert len(diff.changes) == 1
        assert diff.changes[0].operation == Operation.DELETE
        assert diff.summary.deletes == 1
    
    @pytest.mark.asyncio
    async def test_compute_update_with_bundle_changes(self, service: DiffService):
        """Test calcul diff avec modifications de bundles."""
        current = {
            "obj": {
                "type": "User",
                "path": "/users/obj",
                "attributes": {
                    "name": "Old Name",
                    "age": 25
                }
            }
        }
        proposed = {
            "obj": {
                "type": "User",
                "path": "/users/obj",
                "attributes": {
                    "name": "New Name",
                    "age": 25,
                    "email": "new@example.com"
                }
            }
        }
        
        diff = await service.compute_diff(
            scenario_id="test-scenario",
            current_state=current,
            proposed_state=proposed
        )
        
        assert len(diff.changes) == 1
        change = diff.changes[0]
        assert change.operation == Operation.UPDATE
        assert change.attributes is not None
        assert change.attributes.has_changes
        
        # Vérifier les champs
        field_names = {f.field_name for f in change.attributes.fields}
        assert "name" in field_names
        assert "email" in field_names
    
    @pytest.mark.asyncio
    async def test_compute_tag_changes(self, service: DiffService):
        """Test calcul diff avec modifications de tags."""
        current = {
            "obj": {
                "type": "Item",
                "path": "/items/obj",
                "tags": ["tag1", "tag2", "tag3"]
            }
        }
        proposed = {
            "obj": {
                "type": "Item",
                "path": "/items/obj",
                "tags": ["tag2", "tag4"]  # tag1, tag3 removed; tag4 added
            }
        }
        
        diff = await service.compute_diff(
            scenario_id="test-scenario",
            current_state=current,
            proposed_state=proposed
        )
        
        assert len(diff.changes) == 1
        change = diff.changes[0]
        assert change.tags is not None
        assert change.tags.has_changes
        assert set(change.tags.removed) == {"tag1", "tag3"}
        assert change.tags.added == ["tag4"]
    
    @pytest.mark.asyncio
    async def test_compute_complex_diff(
        self,
        service: DiffService,
        current_state: dict,
        proposed_state: dict
    ):
        """Test calcul diff complexe avec multiples opérations."""
        diff = await service.compute_diff(
            scenario_id="complex-scenario",
            scenario_label="Complex Test",
            current_state=current_state,
            proposed_state=proposed_state
        )
        
        assert diff.scenario_label == "Complex Test"
        
        # Doit avoir: 1 update (obj-001), 1 delete (obj-003), 1 create (obj-004)
        # obj-002 est inchangé donc pas inclus
        assert diff.summary.total_changes == 3
        assert diff.summary.creates == 1
        assert diff.summary.updates == 1
        assert diff.summary.deletes == 1
    
    @pytest.mark.asyncio
    async def test_compute_no_changes(self, service: DiffService):
        """Test calcul diff sans changements."""
        state = {
            "obj": {
                "type": "Item",
                "path": "/items/obj",
                "attributes": {"name": "Same"}
            }
        }
        
        diff = await service.compute_diff(
            scenario_id="no-changes",
            current_state=state,
            proposed_state=state
        )
        
        assert len(diff.changes) == 0
        assert diff.summary.total_changes == 0
    
    @pytest.mark.asyncio
    async def test_diff_stored_and_retrievable(self, service: DiffService):
        """Test que le diff est stocké et récupérable."""
        diff = await service.compute_diff(
            scenario_id="stored",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        retrieved = await service.get_diff(diff.diff_id)
        assert retrieved is not None
        assert retrieved.diff_id == diff.diff_id
    
    @pytest.mark.asyncio
    async def test_audit_log_created(self, service: DiffService):
        """Test que le log d'audit est créé."""
        diff = await service.compute_diff(
            scenario_id="audited",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        log = await service.get_audit_log(diff.diff_id)
        assert log is not None
        assert len(log.entries) == 1
        assert log.entries[0].action == "compute"


# =============================================================================
# TESTS DECISIONS
# =============================================================================

class TestDecisions:
    """Tests pour la soumission de décisions."""
    
    @pytest.mark.asyncio
    async def test_submit_accept_decision(self, service: DiffService):
        """Test soumission d'une décision d'acceptation."""
        diff = await service.compute_diff(
            scenario_id="decision-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        change_id = diff.changes[0].diff_item_id
        
        updated = await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_id,
                decision=Decision.ACCEPTED,
                comment="LGTM"
            )
        )
        
        assert updated.changes[0].decision == Decision.ACCEPTED
        assert updated.changes[0].decision_user_id == "user-001"
        assert updated.changes[0].decision_comment == "LGTM"
        assert updated.status == DiffStatus.VALIDATED
    
    @pytest.mark.asyncio
    async def test_submit_reject_decision(self, service: DiffService):
        """Test soumission d'une décision de rejet."""
        diff = await service.compute_diff(
            scenario_id="reject-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        change_id = diff.changes[0].diff_item_id
        
        updated = await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_id,
                decision=Decision.REJECTED
            )
        )
        
        assert updated.changes[0].decision == Decision.REJECTED
        assert updated.status == DiffStatus.REJECTED
    
    @pytest.mark.asyncio
    async def test_submit_modified_decision(self, service: DiffService):
        """Test soumission d'une décision MODIFIED avec override."""
        diff = await service.compute_diff(
            scenario_id="modify-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a", "attributes": {"x": 1}}}
        )
        
        change_id = diff.changes[0].diff_item_id
        override = {"attributes": {"x": 100}}
        
        updated = await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_id,
                decision=Decision.MODIFIED,
                override=override
            )
        )
        
        assert updated.changes[0].decision == Decision.MODIFIED
        assert updated.changes[0].user_override == override
    
    @pytest.mark.asyncio
    async def test_submit_batch_decisions(self, service: DiffService):
        """Test soumission de décisions en batch."""
        diff = await service.compute_diff(
            scenario_id="batch-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"},
                "obj3": {"type": "C", "path": "/c"}
            }
        )
        
        updated = await service.submit_batch_decisions(
            BatchDecisionRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                decisions=[
                    DecisionRequest(
                        diff_item_id=diff.changes[0].diff_item_id,
                        decision=Decision.ACCEPTED
                    ),
                    DecisionRequest(
                        diff_item_id=diff.changes[1].diff_item_id,
                        decision=Decision.REJECTED
                    ),
                    DecisionRequest(
                        diff_item_id=diff.changes[2].diff_item_id,
                        decision=Decision.ACCEPTED
                    )
                ]
            )
        )
        
        assert updated.summary.accepted == 2
        assert updated.summary.rejected == 1
        assert updated.status == DiffStatus.VALIDATED
    
    @pytest.mark.asyncio
    async def test_accept_all(self, service: DiffService):
        """Test acceptation de tous les changements."""
        diff = await service.compute_diff(
            scenario_id="accept-all-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"}
            }
        )
        
        updated = await service.accept_all(diff.diff_id, "user-001")
        
        assert updated.summary.accepted == 2
        assert updated.summary.pending == 0
        assert updated.status == DiffStatus.VALIDATED
    
    @pytest.mark.asyncio
    async def test_reject_all(self, service: DiffService):
        """Test rejet de tous les changements."""
        diff = await service.compute_diff(
            scenario_id="reject-all-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"}
            }
        )
        
        updated = await service.reject_all(diff.diff_id, "user-001")
        
        assert updated.summary.rejected == 2
        assert updated.summary.pending == 0
        assert updated.status == DiffStatus.REJECTED
    
    @pytest.mark.asyncio
    async def test_reset_decisions(self, service: DiffService):
        """Test réinitialisation des décisions."""
        diff = await service.compute_diff(
            scenario_id="reset-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        # D'abord accepter
        await service.accept_all(diff.diff_id, "user-001")
        
        # Puis reset
        updated = await service.reset_decisions(diff.diff_id, "user-002")
        
        assert updated.summary.pending == 1
        assert updated.summary.accepted == 0
        assert updated.status == DiffStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_decision_on_invalid_diff(self, service: DiffService):
        """Test erreur sur diff inexistant."""
        with pytest.raises(DiffValidationError) as exc:
            await service.submit_decision(
                diff_id="nonexistent",
                user_id="user-001",
                decision_request=DecisionRequest(
                    diff_item_id="item",
                    decision=Decision.ACCEPTED
                )
            )
        assert "not found" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_decision_on_invalid_item(self, service: DiffService):
        """Test erreur sur item inexistant."""
        diff = await service.compute_diff(
            scenario_id="invalid-item",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        with pytest.raises(DiffValidationError) as exc:
            await service.submit_decision(
                diff_id=diff.diff_id,
                user_id="user-001",
                decision_request=DecisionRequest(
                    diff_item_id="nonexistent-item",
                    decision=Decision.ACCEPTED
                )
            )
        assert "not found" in str(exc.value)


# =============================================================================
# TESTS APPLICATION
# =============================================================================

class TestApplication:
    """Tests pour l'application des diffs."""
    
    @pytest.mark.asyncio
    async def test_apply_accepted_changes(self, service: DiffService):
        """Test application des changements acceptés."""
        diff = await service.compute_diff(
            scenario_id="apply-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a", "attributes": {"x": 1}},
                "obj2": {"type": "B", "path": "/b", "attributes": {"y": 2}}
            }
        )
        
        # Trouver les changements par object_id (ordre non garanti)
        change_obj1 = next(c for c in diff.changes if c.object_id == "obj1")
        change_obj2 = next(c for c in diff.changes if c.object_id == "obj2")
        
        # Accepter uniquement obj1
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_obj1.diff_item_id,
                decision=Decision.ACCEPTED
            )
        )
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_obj2.diff_item_id,
                decision=Decision.REJECTED
            )
        )
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert result.success
        assert result.applied_count == 1
        assert result.skipped_count == 1
        
        # Vérifier que le SuperTool a été appelé pour obj1 uniquement
        registry = service._supertools
        assert len(registry.create.calls) == 1
        assert registry.create.calls[0]["object_type"] == "A"
        assert registry.create.calls[0]["object_path"] == "/a"
    
    @pytest.mark.asyncio
    async def test_apply_with_update_and_delete(self, service: DiffService):
        """Test application avec UPDATE et DELETE."""
        diff = await service.compute_diff(
            scenario_id="mixed-apply",
            current_state={
                "existing": {
                    "type": "X",
                    "path": "/x",
                    "attributes": {"old": "value"}
                },
                "to-delete": {
                    "type": "Y",
                    "path": "/y"
                }
            },
            proposed_state={
                "existing": {
                    "type": "X",
                    "path": "/x",
                    "attributes": {"new": "value"}
                }
            }
        )
        
        await service.accept_all(diff.diff_id, "user-001")
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert result.success
        assert result.applied_count == 2
        
        registry = service._supertools
        assert len(registry.update.calls) == 1
        assert len(registry.delete.calls) == 1
    
    @pytest.mark.asyncio
    async def test_apply_with_modified_override(self, service: DiffService):
        """Test application avec override MODIFIED."""
        diff = await service.compute_diff(
            scenario_id="override-apply",
            current_state={
                "obj": {"type": "A", "path": "/a", "attributes": {"x": 1}}
            },
            proposed_state={
                "obj": {"type": "A", "path": "/a", "attributes": {"x": 10}}
            }
        )
        
        # Modifier la proposition
        override = {"attributes": {"x": 999}}
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=diff.changes[0].diff_item_id,
                decision=Decision.MODIFIED,
                override=override
            )
        )
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert result.success
        
        # Vérifier que l'override a été utilisé
        registry = service._supertools
        assert registry.update.calls[0]["attributes"] == {"x": 999}
    
    @pytest.mark.asyncio
    async def test_cannot_apply_without_accepted(self, service: DiffService):
        """Test qu'on ne peut pas appliquer sans acceptations."""
        diff = await service.compute_diff(
            scenario_id="no-accept",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        # Rejeter tout
        await service.reject_all(diff.diff_id, "user-001")
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert not result.success
        # Le diff est REJECTED donc pas applicable
        assert "not applicable" in result.message.lower() or "no changes" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_cannot_apply_pending(self, service: DiffService):
        """Test qu'on ne peut pas appliquer avec pending."""
        diff = await service.compute_diff(
            scenario_id="pending-apply",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        # Pas de décision = PENDING = pas applicable
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_apply_handles_supertool_failure(self, service: DiffService):
        """Test gestion des erreurs SuperTool."""
        diff = await service.compute_diff(
            scenario_id="failure-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        await service.accept_all(diff.diff_id, "user-001")
        
        # Configurer le stub pour échouer
        service._supertools.create.should_fail = True
        service._supertools.create.fail_message = "Simulated failure"
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert not result.success
        assert result.failed_count == 1
        assert "Simulated failure" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_apply_updates_diff_status(self, service: DiffService):
        """Test que le statut du diff est mis à jour après application."""
        diff = await service.compute_diff(
            scenario_id="status-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        await service.accept_all(diff.diff_id, "user-001")
        
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        assert result.success
        assert result.updated_diff.status == DiffStatus.APPLIED


# =============================================================================
# TESTS PREVIEW
# =============================================================================

class TestPreview:
    """Tests pour l'aperçu d'application."""
    
    @pytest.mark.asyncio
    async def test_preview_shows_accepted_rejected(self, service: DiffService):
        """Test aperçu avec acceptés et rejetés."""
        diff = await service.compute_diff(
            scenario_id="preview-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"},
                "obj3": {"type": "C", "path": "/c"}
            }
        )
        
        # Accepter obj1, rejeter obj2, laisser obj3 pending
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=diff.changes[0].diff_item_id,
                decision=Decision.ACCEPTED
            )
        )
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=diff.changes[1].diff_item_id,
                decision=Decision.REJECTED
            )
        )
        
        preview = await service.get_application_preview(diff.diff_id)
        
        assert preview["to_apply"]["count"] == 1
        assert preview["rejected"]["count"] == 1
        assert preview["pending"]["count"] == 1
        assert preview["can_apply"] is True
    
    @pytest.mark.asyncio
    async def test_preview_warnings_for_pending(self, service: DiffService):
        """Test avertissements pour changements pending."""
        diff = await service.compute_diff(
            scenario_id="warning-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"}
            }
        )
        
        # Accepter seulement obj1
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=diff.changes[0].diff_item_id,
                decision=Decision.ACCEPTED
            )
        )
        
        preview = await service.get_application_preview(diff.diff_id)
        
        assert len(preview["warnings"]) > 0
        assert "pending" in preview["warnings"][0].lower()


# =============================================================================
# TESTS SÉCURITÉ
# =============================================================================

class TestSecurity:
    """Tests de sécurité — rien n'est appliqué sans acceptation explicite."""
    
    @pytest.mark.asyncio
    async def test_nothing_applied_without_decision(self, service: DiffService):
        """Test que rien n'est appliqué sans décision."""
        diff = await service.compute_diff(
            scenario_id="security-test",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"}
            }
        )
        
        # Tenter d'appliquer sans décision
        result = await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        # Doit échouer
        assert not result.success
        
        # Aucun SuperTool ne doit avoir été appelé
        registry = service._supertools
        assert len(registry.create.calls) == 0
        assert len(registry.update.calls) == 0
        assert len(registry.delete.calls) == 0
    
    @pytest.mark.asyncio
    async def test_rejected_changes_not_applied(self, service: DiffService):
        """Test que les changements rejetés ne sont pas appliqués."""
        diff = await service.compute_diff(
            scenario_id="reject-security",
            current_state={},
            proposed_state={
                "obj1": {"type": "A", "path": "/a"},
                "obj2": {"type": "B", "path": "/b"}
            }
        )
        
        # Trouver les changements par object_id (ordre non garanti)
        change_obj1 = next(c for c in diff.changes if c.object_id == "obj1")
        change_obj2 = next(c for c in diff.changes if c.object_id == "obj2")
        
        # Accepter obj1, rejeter obj2
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_obj1.diff_item_id,
                decision=Decision.ACCEPTED
            )
        )
        await service.submit_decision(
            diff_id=diff.diff_id,
            user_id="user-001",
            decision_request=DecisionRequest(
                diff_item_id=change_obj2.diff_item_id,
                decision=Decision.REJECTED
            )
        )
        
        await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        # Seul obj1 doit être créé (type A, path /a)
        registry = service._supertools
        assert len(registry.create.calls) == 1
        assert registry.create.calls[0]["object_path"] == "/a"
        assert registry.create.calls[0]["object_type"] == "A"
    
    @pytest.mark.asyncio
    async def test_audit_trail_complete(self, service: DiffService):
        """Test que l'audit trail est complet."""
        diff = await service.compute_diff(
            scenario_id="audit-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        await service.accept_all(diff.diff_id, "user-001")
        await service.apply_diff(
            ApplyDiffRequest(
                diff_id=diff.diff_id,
                user_id="user-001",
                confirm=True
            )
        )
        
        log = await service.get_audit_log(diff.diff_id)
        
        # Doit contenir: compute, accept_all, apply
        actions = [e.action for e in log.entries]
        assert "compute" in actions
        assert "accept_all" in actions
        assert "apply" in actions


# =============================================================================
# TESTS UTILITAIRES
# =============================================================================

class TestUtilities:
    """Tests pour les méthodes utilitaires."""
    
    @pytest.mark.asyncio
    async def test_get_pending_diffs(self, service: DiffService):
        """Test récupération des diffs en attente."""
        # Créer plusieurs diffs
        await service.compute_diff("s1", {}, {"obj1": {"type": "A", "path": "/a"}})
        await service.compute_diff("s2", {}, {"obj2": {"type": "B", "path": "/b"}})
        diff3 = await service.compute_diff("s1", {}, {"obj3": {"type": "C", "path": "/c"}})
        
        # Appliquer le 3ème
        await service.accept_all(diff3.diff_id, "user")
        await service.apply_diff(ApplyDiffRequest(
            diff_id=diff3.diff_id,
            user_id="user",
            confirm=True
        ))
        
        # Récupérer les pending
        pending = await service.get_pending_diffs()
        assert len(pending) == 2
        
        # Filtrer par scénario
        s1_pending = await service.get_pending_diffs(scenario_id="s1")
        assert len(s1_pending) == 1
    
    @pytest.mark.asyncio
    async def test_delete_diff(self, service: DiffService):
        """Test suppression d'un diff."""
        diff = await service.compute_diff(
            scenario_id="delete-test",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        deleted = await service.delete_diff(diff.diff_id, "user-001")
        assert deleted
        
        # Ne doit plus exister
        retrieved = await service.get_diff(diff.diff_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_cannot_delete_applied_diff(self, service: DiffService):
        """Test qu'on ne peut pas supprimer un diff appliqué."""
        diff = await service.compute_diff(
            scenario_id="no-delete",
            current_state={},
            proposed_state={"obj": {"type": "A", "path": "/a"}}
        )
        
        await service.accept_all(diff.diff_id, "user-001")
        await service.apply_diff(ApplyDiffRequest(
            diff_id=diff.diff_id,
            user_id="user-001",
            confirm=True
        ))
        
        with pytest.raises(DiffValidationError) as exc:
            await service.delete_diff(diff.diff_id, "user-001")
        assert "applied" in str(exc.value).lower()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
