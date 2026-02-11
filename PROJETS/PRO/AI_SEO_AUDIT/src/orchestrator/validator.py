"""Validator - Validates data coherence and EURKAI conformity."""
from typing import Any, Dict, List, Optional
from ..core.object import Object, TestResult
from ..core.domain.audit_session import AuditResult
from ..core.domain.competitor_analysis import CompetitorAnalysis
from ..core.domain.optimization_recommendation import OptimizationRecommendation


class ValidationResult:
    """Result of validation."""
    def __init__(self, ok: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.ok = ok
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self):
        return self.ok

    def __repr__(self):
        status = "✅" if self.ok else "❌"
        msg = f"{status} {len(self.errors)} errors, {len(self.warnings)} warnings"
        return f"<ValidationResult {msg}>"


class Validator(Object):
    """
    Validator for EURKAI architecture.

    Extends: Object → flow.validator.Validator

    Validates data coherence, EURKAI conformity, and business rules.
    """

    def __init__(self, strict: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.strict = strict  # If True, warnings are treated as errors

    def validate(self) -> bool:
        """Validate validator configuration."""
        return True

    def test(self) -> TestResult:
        """Test validator functionality."""
        # Test with valid data
        mock_results = [
            AuditResult("test query", "chatgpt", True, position=1, competitors=[])
        ]
        result = self.validate_audit_results(mock_results)
        if not result.ok:
            return TestResult(False, "Validator failed on valid data")

        return TestResult(True, "Validator is operational")

    def validate_audit_results(self, results: List[AuditResult]) -> ValidationResult:
        """
        Validate audit results.

        Checks:
        - Results list is not empty
        - Each result has required fields
        - Position values are valid (>= 1)
        - Competitors list is valid
        """
        errors = []
        warnings = []

        if not results:
            errors.append("Results list is empty")
            return ValidationResult(False, errors, warnings)

        for i, result in enumerate(results):
            # Check required fields
            if not result.query:
                errors.append(f"Result {i}: query is empty")
            if not result.ai_provider:
                errors.append(f"Result {i}: ai_provider is empty")

            # Check position validity
            if result.company_mentioned and result.position is not None:
                if result.position < 1:
                    errors.append(f"Result {i}: position must be >= 1, got {result.position}")
                if result.position > 20:
                    warnings.append(f"Result {i}: position {result.position} is very low (>20)")

            # Check competitors
            if result.competitors and not isinstance(result.competitors, list):
                errors.append(f"Result {i}: competitors must be a list")

        ok = len(errors) == 0 and (not self.strict or len(warnings) == 0)
        return ValidationResult(ok, errors, warnings)

    def validate_analysis(self, analysis: CompetitorAnalysis) -> ValidationResult:
        """
        Validate competitor analysis.

        Checks:
        - Target company is set
        - Competitors have valid data
        - Gaps are properly defined
        """
        errors = []
        warnings = []

        if not analysis.target_company:
            errors.append("Target company is not set")

        # Validate competitors
        for i, comp in enumerate(analysis.competitors):
            if not comp.name:
                errors.append(f"Competitor {i}: name is empty")
            if comp.mention_count < 0:
                errors.append(f"Competitor {i}: mention_count cannot be negative")
            if comp.avg_position is not None and comp.avg_position < 1:
                errors.append(f"Competitor {i}: avg_position must be >= 1")

        # Validate gaps
        for i, gap in enumerate(analysis.visibility_gaps):
            if not gap.type:
                errors.append(f"Gap {i}: type is empty")
            if gap.type not in ["content", "structured_data", "editorial", "authority"]:
                errors.append(f"Gap {i}: invalid type '{gap.type}'")
            if gap.severity not in ["low", "medium", "high"]:
                errors.append(f"Gap {i}: invalid severity '{gap.severity}'")

        if not analysis.competitors and not warnings:
            warnings.append("No competitors identified")

        ok = len(errors) == 0 and (not self.strict or len(warnings) == 0)
        return ValidationResult(ok, errors, warnings)

    def validate_recommendations(
        self, recommendations: List[OptimizationRecommendation]
    ) -> ValidationResult:
        """
        Validate optimization recommendations.

        Checks:
        - Recommendations list is not empty
        - Each recommendation has required fields
        - Priority and impact values are valid
        - Content is present
        """
        errors = []
        warnings = []

        if not recommendations:
            errors.append("Recommendations list is empty")
            return ValidationResult(False, errors, warnings)

        for i, rec in enumerate(recommendations):
            # Check required fields
            if not rec.title:
                errors.append(f"Recommendation {i}: title is empty")
            if not rec.type:
                errors.append(f"Recommendation {i}: type is empty")

            # Validate type
            if rec.type not in ["content", "structured_data", "editorial"]:
                errors.append(f"Recommendation {i}: invalid type '{rec.type}'")

            # Validate priority
            if not (1 <= rec.priority <= 5):
                errors.append(f"Recommendation {i}: priority must be 1-5, got {rec.priority}")

            # Validate impact
            if rec.estimated_impact not in ["low", "medium", "high"]:
                errors.append(f"Recommendation {i}: invalid impact '{rec.estimated_impact}'")

            # Check content
            if not rec.content:
                warnings.append(f"Recommendation {i}: content is empty")

            # Check integration guide
            if not rec.integration_guide:
                warnings.append(f"Recommendation {i}: integration_guide is empty")

        # Check priority distribution (at least one P1 or P2)
        high_priority_count = sum(1 for r in recommendations if r.priority <= 2)
        if high_priority_count == 0:
            warnings.append("No high-priority recommendations (P1-P2)")

        ok = len(errors) == 0 and (not self.strict or len(warnings) == 0)
        return ValidationResult(ok, errors, warnings)

    def validate_manifest_conformity(self, obj: Object) -> ValidationResult:
        """
        Validate EURKAI MANIFEST conformity.

        Checks:
        - Object inherits from Object base
        - Has required methods (validate, test)
        - Has required attributes (ident, created_at, version)
        """
        errors = []
        warnings = []

        # Check inheritance
        if not isinstance(obj, Object):
            errors.append(f"{type(obj).__name__} does not inherit from Object")

        # Check required methods
        if not hasattr(obj, 'validate') or not callable(obj.validate):
            errors.append(f"{type(obj).__name__} missing validate() method")
        if not hasattr(obj, 'test') or not callable(obj.test):
            errors.append(f"{type(obj).__name__} missing test() method")

        # Check required attributes
        if not hasattr(obj, 'ident'):
            errors.append(f"{type(obj).__name__} missing ident attribute")
        if not hasattr(obj, 'created_at'):
            errors.append(f"{type(obj).__name__} missing created_at attribute")
        if not hasattr(obj, 'version'):
            errors.append(f"{type(obj).__name__} missing version attribute")

        # Try to call validate and test
        try:
            if hasattr(obj, 'validate'):
                obj.validate()
        except Exception as e:
            errors.append(f"{type(obj).__name__}.validate() raised exception: {e}")

        try:
            if hasattr(obj, 'test'):
                result = obj.test()
                if not result.success:
                    warnings.append(f"{type(obj).__name__}.test() returned failure: {result.message}")
        except Exception as e:
            errors.append(f"{type(obj).__name__}.test() raised exception: {e}")

        ok = len(errors) == 0 and (not self.strict or len(warnings) == 0)
        return ValidationResult(ok, errors, warnings)
