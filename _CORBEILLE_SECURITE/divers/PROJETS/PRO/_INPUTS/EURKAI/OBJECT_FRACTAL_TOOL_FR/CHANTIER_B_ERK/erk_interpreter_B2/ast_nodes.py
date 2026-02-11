"""
ERK AST Nodes - Définition des nœuds de l'arbre syntaxique abstrait.

Chaque nœud représente une construction syntaxique ERK:
- Literals: valeurs constantes (bool, string, number)
- Identifiers: références à des variables/propriétés
- Expressions: opérations (binaires, unaires, appels de méthodes)
- Conditionals (B2): IF/THEN/ELSE, WHEN

Version: B2/2 - Conditions étendues et contexte
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
    CTX = auto()  # B2: Référence au contexte (ctx)
    
    # Expressions
    BINARY_OP = auto()
    UNARY_OP = auto()
    METHOD_CALL = auto()
    
    # Rule structure
    RULE = auto()
    ARRAY = auto()
    
    # B2: Conditionals
    IF_THEN_ELSE = auto()
    WHEN_THEN = auto()


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
class CtxNode(ASTNode):
    """B2: Référence au contexte d'évaluation (ctx)."""
    node_type: NodeType = field(default=NodeType.CTX)
    
    def __repr__(self):
        return "Ctx"


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


# ============================================================================
# B2: Nœuds conditionnels
# ============================================================================

@dataclass
class IfThenElseNode(ASTNode):
    """
    B2: Expression conditionnelle IF/THEN/ELSE.
    
    Syntaxe: IF condition THEN consequence [ELSE alternative]
    
    Exemples:
      IF this.priority == "natural" THEN enable ELSE disable
      IF this.credits > 0 THEN allow
    """
    condition: ASTNode = None      # La condition à évaluer
    then_branch: ASTNode = None    # Résultat si condition vraie
    else_branch: ASTNode = None    # Résultat si condition fausse (optionnel)
    
    def __repr__(self):
        else_part = f" ELSE {self.else_branch}" if self.else_branch else ""
        return f"IfThenElse(IF {self.condition} THEN {self.then_branch}{else_part})"


@dataclass
class WhenThenNode(ASTNode):
    """
    B2: Condition contextuelle WHEN/THEN.
    
    Syntaxe: WHEN condition THEN result
    
    Utilisé pour les conditions basées sur le contexte d'exécution.
    
    Exemples:
      WHEN ctx.layer == "System" AND this.type == "Agent" THEN allow
      WHEN ctx.mode == "strict" THEN require
    """
    condition: ASTNode = None      # La condition (souvent implique ctx)
    then_result: ASTNode = None    # Résultat si condition vraie
    
    def __repr__(self):
        return f"WhenThen(WHEN {self.condition} THEN {self.then_result})"
