"""
ERK Errors - Exceptions typées pour l'interpréteur ERK.

Hiérarchie:
- ERKError (base)
  - ERKLexerError (tokenization)
  - ERKParseError (parsing)
  - ERKEvalError (evaluation)
  - ERKReferenceError (résolution de références)
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ERKError(Exception):
    """Erreur de base ERK avec contexte."""
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule_name: Optional[str] = None
    details: dict = field(default_factory=dict)
    
    def __str__(self):
        loc = ""
        if self.line is not None:
            loc = f" at line {self.line}"
            if self.column is not None:
                loc += f", column {self.column}"
        
        rule = ""
        if self.rule_name:
            rule = f" [rule: {self.rule_name}]"
        
        return f"{self.__class__.__name__}: {self.message}{loc}{rule}"
    
    def to_dict(self) -> dict:
        """Convertit l'erreur en dictionnaire pour la console."""
        return {
            "error": True,
            "type": self.__class__.__name__,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "rule": self.rule_name,
            "details": self.details
        }


@dataclass
class ERKLexerError(ERKError):
    """Erreur de tokenization."""
    pass


@dataclass
class ERKParseError(ERKError):
    """Erreur de parsing."""
    expected: Optional[str] = None
    found: Optional[str] = None
    
    def __str__(self):
        base = super().__str__()
        if self.expected and self.found:
            return f"{base} (expected {self.expected}, found {self.found})"
        return base


@dataclass
class ERKEvalError(ERKError):
    """Erreur d'évaluation."""
    expression: Optional[str] = None
    context_key: Optional[str] = None
    
    def __str__(self):
        base = super().__str__()
        if self.expression:
            return f"{base} in expression: {self.expression}"
        return base


@dataclass
class ERKReferenceError(ERKError):
    """Erreur de résolution de référence."""
    reference: Optional[str] = None
    available: list = field(default_factory=list)
    
    def __str__(self):
        base = super().__str__()
        if self.reference:
            hint = ""
            if self.available:
                hint = f" (available: {', '.join(self.available[:5])})"
            return f"{base} - reference '{self.reference}' not found{hint}"
        return base


@dataclass
class ERKTypeError(ERKError):
    """Erreur de type lors de l'évaluation."""
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None
    value: Any = None
    
    def __str__(self):
        base = super().__str__()
        if self.expected_type and self.actual_type:
            return f"{base} (expected {self.expected_type}, got {self.actual_type})"
        return base
