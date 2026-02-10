"""
ERK AST Nodes - Définition des nœuds de l'arbre syntaxique abstrait.

Chaque nœud représente une construction syntaxique ERK:
- Literals: valeurs constantes (bool, string, number)
- Identifiers: références à des variables/propriétés
- Expressions: opérations (binaires, unaires, appels de méthodes)
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from enum import Enum, auto


class NodeType(Enum):
    """Types de nœuds AST."""
    # Literals
    BOOLEAN = auto()
    STRING = auto()
    NUMBER = auto()
    NULL = auto()
    
    # References
    IDENTIFIER = auto()
    THIS = auto()
    MEMBER_ACCESS = auto()
    
    # Expressions
    BINARY_OP = auto()
    UNARY_OP = auto()
    METHOD_CALL = auto()
    
    # Rule structure
    RULE = auto()
    ARRAY = auto()


@dataclass
class ASTNode:
    """Nœud de base de l'AST."""
    node_type: NodeType
    line: int = 0
    column: int = 0


@dataclass
class LiteralNode(ASTNode):
    """Valeur littérale: bool, string, number, null."""
    value: Any = None
    
    def __repr__(self):
        return f"Literal({self.value!r})"


@dataclass
class IdentifierNode(ASTNode):
    """Référence à un identifiant (variable, propriété)."""
    name: str = ""
    
    def __repr__(self):
        return f"Identifier({self.name})"


@dataclass
class ThisNode(ASTNode):
    """Référence à l'objet courant (this)."""
    node_type: NodeType = field(default=NodeType.THIS)
    
    def __repr__(self):
        return "This"


@dataclass
class MemberAccessNode(ASTNode):
    """Accès à un membre: obj.property."""
    object: ASTNode = None
    member: str = ""
    
    def __repr__(self):
        return f"MemberAccess({self.object}.{self.member})"


@dataclass
class BinaryOpNode(ASTNode):
    """Opération binaire: a OP b."""
    operator: str = ""
    left: ASTNode = None
    right: ASTNode = None
    
    def __repr__(self):
        return f"BinaryOp({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOpNode(ASTNode):
    """Opération unaire: NOT a."""
    operator: str = ""
    operand: ASTNode = None
    
    def __repr__(self):
        return f"UnaryOp({self.operator} {self.operand})"


@dataclass
class MethodCallNode(ASTNode):
    """Appel de méthode: obj.method(args)."""
    object: ASTNode = None
    method: str = ""
    arguments: List[ASTNode] = field(default_factory=list)
    
    def __repr__(self):
        args = ", ".join(str(a) for a in self.arguments)
        return f"MethodCall({self.object}.{self.method}({args}))"


@dataclass
class ArrayNode(ASTNode):
    """Tableau littéral: [a, b, c]."""
    elements: List[ASTNode] = field(default_factory=list)
    
    def __repr__(self):
        return f"Array([{', '.join(str(e) for e in self.elements)}])"


@dataclass
class RuleNode(ASTNode):
    """Règle ERK complète: action: expression."""
    action: str = ""           # enable, allow, deny, require, etc.
    expression: ASTNode = None
    metadata: dict = field(default_factory=dict)
    
    def __repr__(self):
        return f"Rule({self.action}: {self.expression})"
