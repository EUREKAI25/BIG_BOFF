from .src.design_validator import (
    DesignValidator,
    ValidationResult,
    validate_layout,
    PASS_THRESHOLD,
    MAX_SECTION_REPETITION,
    SEVERITY_MAJOR,
    SEVERITY_MEDIUM,
    SEVERITY_MINOR,
)

__all__ = [
    "DesignValidator",
    "ValidationResult",
    "validate_layout",
    "PASS_THRESHOLD",
    "MAX_SECTION_REPETITION",
    "SEVERITY_MAJOR",
    "SEVERITY_MEDIUM",
    "SEVERITY_MINOR",
]
