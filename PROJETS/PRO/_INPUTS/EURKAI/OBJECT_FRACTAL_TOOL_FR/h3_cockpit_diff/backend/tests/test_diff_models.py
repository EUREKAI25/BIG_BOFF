"""
H3 — Tests des Modèles Diff
============================

Tests unitaires pour les dataclasses Pydantic du système de diff.
Couvre: validation, sérialisation, cas d'erreurs.
"""

import json
import pytest
from datetime import datetime
from pydantic import ValidationError

import sys
sys.path.insert(0, str(__file__).replace('/tests/test_diff_models.py', ''))

from models.diff_models import (
    # Enums
    Operation,
    ChangeType,
    Decision,
    DiffStatus,
    # Models
    FieldDiff,
    BundleDiff,
    TagsDiff,
    ObjectDiff,
    DiffSummary,
    FractalDiff,
    DiffAuditEntry,
    DiffAuditLog,
    # API Models
    DecisionRequest,
    BatchDecisionRequest,
    ApplyDiffRequest,
    DiffOperationResult,
)


# =============================================================================
# TESTS FIELDDIFF
# =============================================================================

class TestFieldDiff:
    """Tests pour FieldDiff."""
    
    def test_valid_added_field(self):
        """Test création d'un champ ajouté."""
        field = FieldDiff(
            field_name="name",
            old_value=None,
            new_value="test",
            change_type=ChangeType.ADDED
        )
        assert field.field_name == "name"
        assert field.old_value is None
        assert field.new_value == "test"
        assert field.change_type == ChangeType.ADDED
    
    def test_valid_removed_field(self):
        """Test création d'un champ supprimé."""
        field = FieldDiff(
            field_name="obsolete",
            old_value="old_value",
            new_value=None,
            change_type=ChangeType.REMOVED
        )
        assert field.change_type == ChangeType.REMOVED
        assert field.new_value is None
    
    def test_valid_changed_field(self):
        """Test création d'un champ modifié."""
        field = FieldDiff(
            field_name="status",
            old_value="draft",
            new_value="published",
            change_type=ChangeType.CHANGED
        )
        assert field.change_type == ChangeType.CHANGED
    
    def test_valid_unchanged_field(self):
        """Test création d'un champ inchangé."""
        field = FieldDiff(
            field_name="id",
            old_value="123",
            new_value="123",
            change_type=ChangeType.UNCHANGED
        )
        assert field.change_type == ChangeType.UNCHANGED
    
    def test_invalid_added_with_old_value(self):
        """Test erreur: ADDED avec old_value non null."""
        with pytest.raises(ValidationError) as exc:
            FieldDiff(
                field_name="test",
                old_value="should_be_none",
                new_value="new",
                change_type=ChangeType.ADDED
            )
        assert "ADDED change should have old_value=None" in str(exc.value)
    
    def test_invalid_removed_with_new_value(self):
        """Test erreur: REMOVED avec new_value non null."""
        with pytest.raises(ValidationError) as exc:
            FieldDiff(
                field_name="test",
                old_value="old",
                new_value="should_be_none",
                change_type=ChangeType.REMOVED
            )
        assert "REMOVED change should have new_value=None" in str(exc.value)
    
    def test_invalid_unchanged_different_values(self):
        """Test erreur: UNCHANGED avec valeurs différentes."""
        with pytest.raises(ValidationError) as exc:
            FieldDiff(
                field_name="test",
                old_value="a",
                new_value="b",
                change_type=ChangeType.UNCHANGED
            )
        assert "UNCHANGED change should have identical values" in str(exc.value)
    
    def test_serialization_json(self):
        """Test sérialisation JSON."""
        field = FieldDiff(
            field_name="name",
            old_value=None,
            new_value="test",
            change_type=ChangeType.ADDED
        )
        json_str = field.model_dump_json()
        data = json.loads(json_str)
        
        assert data["field_name"] == "name"
        assert data["change_type"] == "added"
    
    def test_extra_fields_forbidden(self):
        """Test que les champs supplémentaires sont interdits."""
        with pytest.raises(ValidationError):
            FieldDiff(
                field_name="test",
                old_value=None,
                new_value="x",
                change_type=ChangeType.ADDED,
                extra_field="not_allowed"  # type: ignore
            )


# =============================================================================
# TESTS BUNDLEDIFF
# =============================================================================

class TestBundleDiff:
    """Tests pour BundleDiff."""
    
    def test_empty_bundle(self):
        """Test bundle vide."""
        bundle = BundleDiff(bundle_type="attributes", fields=[])
        assert not bundle.has_changes
        assert bundle.added_fields == []
        assert bundle.removed_fields == []
        assert bundle.changed_fields == []
    
    def test_bundle_with_changes(self):
        """Test bundle avec changements."""
        bundle = BundleDiff(
            bundle_type="attributes",
            fields=[
                FieldDiff(field_name="a", old_value=None, new_value="x", change_type=ChangeType.ADDED),
                FieldDiff(field_name="b", old_value="y", new_value=None, change_type=ChangeType.REMOVED),
                FieldDiff(field_name="c", old_value="1", new_value="2", change_type=ChangeType.CHANGED),
                FieldDiff(field_name="d", old_value="z", new_value="z", change_type=ChangeType.UNCHANGED),
            ]
        )
        
        assert bundle.has_changes
        assert len(bundle.added_fields) == 1
        assert len(bundle.removed_fields) == 1
        assert len(bundle.changed_fields) == 1
    
    def test_bundle_only_unchanged(self):
        """Test bundle avec uniquement des champs inchangés."""
        bundle = BundleDiff(
            bundle_type="methods",
            fields=[
                FieldDiff(field_name="x", old_value="a", new_value="a", change_type=ChangeType.UNCHANGED),
            ]
        )
        assert not bundle.has_changes


# =============================================================================
# TESTS TAGSDIFF
# =============================================================================

class TestTagsDiff:
    """Tests pour TagsDiff."""
    
    def test_empty_tags(self):
        """Test diff tags vide."""
        tags = TagsDiff()
        assert not tags.has_changes
    
    def test_tags_added(self):
        """Test tags ajoutés."""
        tags = TagsDiff(added=["new_tag", "another_tag"])
        assert tags.has_changes
        assert len(tags.added) == 2
    
    def test_tags_removed(self):
        """Test tags supprimés."""
        tags = TagsDiff(removed=["old_tag"])
        assert tags.has_changes
    
    def test_tags_mixed(self):
        """Test tags ajoutés et supprimés."""
        tags = TagsDiff(added=["new"], removed=["old"])
        assert tags.has_changes


# =============================================================================
# TESTS OBJECTDIFF
# =============================================================================

class TestObjectDiff:
    """Tests pour ObjectDiff."""
    
    def test_create_operation(self):
        """Test diff de création."""
        diff = ObjectDiff(
            object_id="obj-001",
            object_type="User",
            object_path="/app/users/obj-001",
            operation=Operation.CREATE
        )
        
        assert diff.operation == Operation.CREATE
        assert diff.decision == Decision.PENDING
        assert not diff.is_decided
        assert diff.diff_item_id  # Auto-generated
    
    def test_update_operation_with_bundles(self):
        """Test diff de mise à jour avec bundles."""
        diff = ObjectDiff(
            object_id="obj-002",
            object_type="Article",
            object_path="/content/articles/obj-002",
            operation=Operation.UPDATE,
            attributes=BundleDiff(
                bundle_type="attributes",
                fields=[
                    FieldDiff(
                        field_name="title",
                        old_value="Old Title",
                        new_value="New Title",
                        change_type=ChangeType.CHANGED
                    )
                ]
            )
        )
        
        assert diff.has_bundle_changes
        assert diff.attributes is not None
        assert diff.attributes.has_changes
    
    def test_set_decision(self):
        """Test enregistrement d'une décision."""
        diff = ObjectDiff(
            object_id="obj-003",
            object_type="Item",
            object_path="/items/obj-003",
            operation=Operation.DELETE
        )
        
        diff.set_decision(
            decision=Decision.ACCEPTED,
            user_id="user-123",
            comment="Approved for deletion"
        )
        
        assert diff.is_decided
        assert diff.decision == Decision.ACCEPTED
        assert diff.decision_user_id == "user-123"
        assert diff.decision_comment == "Approved for deletion"
        assert diff.decision_timestamp is not None
    
    def test_set_decision_with_override(self):
        """Test décision MODIFIED avec override."""
        diff = ObjectDiff(
            object_id="obj-004",
            object_type="Config",
            object_path="/config/obj-004",
            operation=Operation.UPDATE
        )
        
        override = {"attributes": {"value": "custom_value"}}
        diff.set_decision(
            decision=Decision.MODIFIED,
            user_id="user-456",
            override=override
        )
        
        assert diff.decision == Decision.MODIFIED
        assert diff.user_override == override
    
    def test_no_bundle_changes(self):
        """Test diff sans changements dans les bundles."""
        diff = ObjectDiff(
            object_id="obj-005",
            object_type="Empty",
            object_path="/empty",
            operation=Operation.UPDATE
        )
        
        assert not diff.has_bundle_changes


# =============================================================================
# TESTS DIFFSUMMARY
# =============================================================================

class TestDiffSummary:
    """Tests pour DiffSummary."""
    
    def test_empty_summary(self):
        """Test résumé vide."""
        summary = DiffSummary.from_object_diffs([])
        
        assert summary.total_changes == 0
        assert summary.creates == 0
        assert summary.pending == 0
    
    def test_summary_from_diffs(self):
        """Test calcul du résumé depuis une liste de diffs."""
        diffs = [
            ObjectDiff(object_id="1", object_type="A", object_path="/a", operation=Operation.CREATE),
            ObjectDiff(object_id="2", object_type="B", object_path="/b", operation=Operation.CREATE),
            ObjectDiff(object_id="3", object_type="C", object_path="/c", operation=Operation.UPDATE),
            ObjectDiff(object_id="4", object_type="D", object_path="/d", operation=Operation.DELETE),
        ]
        
        # Simuler des décisions
        diffs[0].decision = Decision.ACCEPTED
        diffs[1].decision = Decision.REJECTED
        
        summary = DiffSummary.from_object_diffs(diffs)
        
        assert summary.total_changes == 4
        assert summary.creates == 2
        assert summary.updates == 1
        assert summary.deletes == 1
        assert summary.accepted == 1
        assert summary.rejected == 1
        assert summary.pending == 2


# =============================================================================
# TESTS FRACTALDIFF
# =============================================================================

class TestFractalDiff:
    """Tests pour FractalDiff."""
    
    def test_create_simple_diff(self):
        """Test création d'un diff simple."""
        diff = FractalDiff(
            scenario_id="scenario-001",
            scenario_label="Test Scenario",
            changes=[
                ObjectDiff(
                    object_id="obj-1",
                    object_type="User",
                    object_path="/users/obj-1",
                    operation=Operation.CREATE
                )
            ]
        )
        
        assert diff.diff_id  # Auto-generated
        assert diff.scenario_id == "scenario-001"
        assert diff.status == DiffStatus.PENDING
        assert len(diff.changes) == 1
        assert diff.summary is not None
        assert diff.summary.creates == 1
    
    def test_categorized_changes(self):
        """Test accès aux changements catégorisés."""
        diff = FractalDiff(
            scenario_id="scenario-002",
            changes=[
                ObjectDiff(object_id="1", object_type="A", object_path="/a", operation=Operation.CREATE),
                ObjectDiff(object_id="2", object_type="B", object_path="/b", operation=Operation.UPDATE),
                ObjectDiff(object_id="3", object_type="C", object_path="/c", operation=Operation.DELETE),
                ObjectDiff(object_id="4", object_type="D", object_path="/d", operation=Operation.DISABLE),
            ]
        )
        
        assert len(diff.created_objects) == 1
        assert len(diff.updated_objects) == 1
        assert len(diff.deleted_objects) == 1
        assert len(diff.disabled_objects) == 1
    
    def test_get_change_by_id(self):
        """Test récupération d'un changement par ID."""
        change = ObjectDiff(
            object_id="target",
            object_type="X",
            object_path="/x",
            operation=Operation.CREATE
        )
        
        diff = FractalDiff(
            scenario_id="scenario-003",
            changes=[change]
        )
        
        found = diff.get_change_by_id(change.diff_item_id)
        assert found is not None
        assert found.object_id == "target"
        
        not_found = diff.get_change_by_id("nonexistent")
        assert not_found is None
    
    def test_update_status(self):
        """Test mise à jour du statut."""
        diff = FractalDiff(
            scenario_id="scenario-004",
            changes=[
                ObjectDiff(object_id="1", object_type="A", object_path="/a", operation=Operation.CREATE),
                ObjectDiff(object_id="2", object_type="B", object_path="/b", operation=Operation.UPDATE),
            ]
        )
        
        # Initial: PENDING
        assert diff.status == DiffStatus.PENDING
        
        # Une décision: PARTIAL
        diff.changes[0].decision = Decision.ACCEPTED
        diff.update_status()
        assert diff.status == DiffStatus.PARTIAL
        
        # Toutes décidées: VALIDATED
        diff.changes[1].decision = Decision.REJECTED
        diff.update_status()
        assert diff.status == DiffStatus.VALIDATED
    
    def test_is_fully_decided(self):
        """Test vérification toutes décisions prises."""
        diff = FractalDiff(
            scenario_id="scenario-005",
            changes=[
                ObjectDiff(object_id="1", object_type="A", object_path="/a", operation=Operation.CREATE),
            ]
        )
        
        assert not diff.is_fully_decided
        
        diff.changes[0].decision = Decision.ACCEPTED
        assert diff.is_fully_decided
    
    def test_is_applicable(self):
        """Test vérification applicabilité."""
        diff = FractalDiff(
            scenario_id="scenario-006",
            changes=[
                ObjectDiff(object_id="1", object_type="A", object_path="/a", operation=Operation.CREATE),
            ]
        )
        
        # Pas encore décidé
        assert not diff.is_applicable
        
        # Accepté
        diff.changes[0].decision = Decision.ACCEPTED
        diff.update_status()
        assert diff.is_applicable
    
    def test_serialization_json(self):
        """Test sérialisation JSON complète."""
        diff = FractalDiff(
            scenario_id="scenario-007",
            changes=[
                ObjectDiff(
                    object_id="obj-1",
                    object_type="User",
                    object_path="/users/obj-1",
                    operation=Operation.CREATE,
                    attributes=BundleDiff(
                        bundle_type="attributes",
                        fields=[
                            FieldDiff(
                                field_name="name",
                                old_value=None,
                                new_value="John",
                                change_type=ChangeType.ADDED
                            )
                        ]
                    )
                )
            ]
        )
        
        json_str = diff.model_dump_json()
        data = json.loads(json_str)
        
        assert "diff_id" in data
        assert data["scenario_id"] == "scenario-007"
        assert len(data["changes"]) == 1
        assert data["changes"][0]["operation"] == "create"


# =============================================================================
# TESTS API MODELS
# =============================================================================

class TestDecisionRequest:
    """Tests pour DecisionRequest."""
    
    def test_valid_accept_decision(self):
        """Test décision d'acceptation valide."""
        req = DecisionRequest(
            diff_item_id="item-001",
            decision=Decision.ACCEPTED,
            comment="Looks good"
        )
        assert req.decision == Decision.ACCEPTED
    
    def test_valid_reject_decision(self):
        """Test décision de rejet valide."""
        req = DecisionRequest(
            diff_item_id="item-002",
            decision=Decision.REJECTED
        )
        assert req.decision == Decision.REJECTED
    
    def test_modified_requires_override(self):
        """Test que MODIFIED requiert un override."""
        with pytest.raises(ValidationError) as exc:
            DecisionRequest(
                diff_item_id="item-003",
                decision=Decision.MODIFIED
            )
        assert "override is required when decision is MODIFIED" in str(exc.value)
    
    def test_valid_modified_with_override(self):
        """Test décision MODIFIED valide avec override."""
        req = DecisionRequest(
            diff_item_id="item-004",
            decision=Decision.MODIFIED,
            override={"attributes": {"value": "custom"}}
        )
        assert req.override is not None


class TestBatchDecisionRequest:
    """Tests pour BatchDecisionRequest."""
    
    def test_valid_batch(self):
        """Test batch valide."""
        req = BatchDecisionRequest(
            diff_id="diff-001",
            user_id="user-001",
            decisions=[
                DecisionRequest(diff_item_id="a", decision=Decision.ACCEPTED),
                DecisionRequest(diff_item_id="b", decision=Decision.REJECTED),
            ]
        )
        assert len(req.decisions) == 2
    
    def test_empty_decisions_invalid(self):
        """Test que decisions vide est invalide."""
        with pytest.raises(ValidationError) as exc:
            BatchDecisionRequest(
                diff_id="diff-002",
                user_id="user-002",
                decisions=[]
            )
        assert "decisions list cannot be empty" in str(exc.value)


class TestApplyDiffRequest:
    """Tests pour ApplyDiffRequest."""
    
    def test_valid_apply_request(self):
        """Test requête d'application valide."""
        req = ApplyDiffRequest(
            diff_id="diff-001",
            user_id="user-001",
            confirm=True
        )
        assert req.confirm
    
    def test_confirm_must_be_true(self):
        """Test que confirm=False est invalide."""
        with pytest.raises(ValidationError) as exc:
            ApplyDiffRequest(
                diff_id="diff-002",
                user_id="user-002",
                confirm=False
            )
        assert "confirm must be True" in str(exc.value)


class TestDiffOperationResult:
    """Tests pour DiffOperationResult."""
    
    def test_success_result(self):
        """Test résultat de succès."""
        result = DiffOperationResult(
            success=True,
            diff_id="diff-001",
            message="Applied successfully",
            applied_count=5
        )
        assert result.success
        assert result.applied_count == 5
    
    def test_failure_result(self):
        """Test résultat d'échec."""
        result = DiffOperationResult(
            success=False,
            diff_id="diff-002",
            message="Application failed",
            failed_count=3,
            errors=["Error 1", "Error 2", "Error 3"]
        )
        assert not result.success
        assert len(result.errors) == 3


# =============================================================================
# TESTS AUDIT LOG
# =============================================================================

class TestDiffAuditEntry:
    """Tests pour DiffAuditEntry."""
    
    def test_create_entry(self):
        """Test création d'une entrée d'audit."""
        entry = DiffAuditEntry(
            diff_id="diff-001",
            scenario_id="scenario-001",
            action="decision",
            user_id="user-001",
            object_id="obj-001",
            operation=Operation.CREATE,
            decision=Decision.ACCEPTED
        )
        
        assert entry.log_id  # Auto-generated
        assert entry.timestamp  # Auto-generated
        assert entry.success


class TestDiffAuditLog:
    """Tests pour DiffAuditLog."""
    
    def test_add_and_query_entries(self):
        """Test ajout et requête d'entrées."""
        log = DiffAuditLog(diff_id="diff-001")
        
        log.add_entry(DiffAuditEntry(
            diff_id="diff-001",
            scenario_id="s1",
            action="decision",
            user_id="u1",
            object_id="obj-1"
        ))
        log.add_entry(DiffAuditEntry(
            diff_id="diff-001",
            scenario_id="s1",
            action="apply",
            user_id="u1",
            object_id="obj-1"
        ))
        log.add_entry(DiffAuditEntry(
            diff_id="diff-001",
            scenario_id="s1",
            action="decision",
            user_id="u1",
            object_id="obj-2"
        ))
        
        assert len(log.entries) == 3
        
        decision_entries = log.get_entries_by_action("decision")
        assert len(decision_entries) == 2
        
        obj1_entries = log.get_entries_by_object("obj-1")
        assert len(obj1_entries) == 2


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
