"""
ERK Evaluator - Évaluation de l'AST dans un contexte.

L'évaluateur traverse l'AST et calcule la valeur résultante
en utilisant le contexte fourni pour résoudre les références.

Contexte attendu:
{
    "this": <objet courant>,
    "objects": { id: object, ... },  # pour résolution par ID
    "lineages": { name: [ids], ... }, # pour résolution par lineage
    "globals": { ... }  # variables globales
}
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .ast_nodes import (
    ASTNode, NodeType, LiteralNode, IdentifierNode, ThisNode,
    MemberAccessNode, BinaryOpNode, UnaryOpNode, MethodCallNode,
    ArrayNode, RuleNode
)
from .errors import ERKEvalError, ERKReferenceError, ERKTypeError


@dataclass
class EvalResult:
    """Résultat d'évaluation d'une règle ERK."""
    ok: bool
    rule: str
    action: str
    value: Any = None
    reason: str = ""
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour la console."""
        return {
            "ok": self.ok,
            "rule": self.rule,
            "action": self.action,
            "value": self.value,
            "reason": self.reason,
            "details": self.details
        }


@dataclass
class EvalContext:
    """Contexte d'évaluation ERK."""
    this: Any = None  # L'objet courant
    objects: Dict[str, Any] = field(default_factory=dict)  # Objets par ID
    lineages: Dict[str, List[str]] = field(default_factory=dict)  # Lineages
    globals: Dict[str, Any] = field(default_factory=dict)  # Variables globales
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EvalContext':
        """Crée un contexte depuis un dictionnaire."""
        return cls(
            this=data.get('this'),
            objects=data.get('objects', {}),
            lineages=data.get('lineages', {}),
            globals=data.get('globals', {})
        )


class Evaluator:
    """Évaluateur pour les expressions ERK."""
    
    # Méthodes built-in disponibles sur les objets
    BUILTIN_METHODS = {
        'contains': '_method_contains',
        'startsWith': '_method_starts_with',
        'endsWith': '_method_ends_with',
        'isEmpty': '_method_is_empty',
        'isNotEmpty': '_method_is_not_empty',
        'length': '_method_length',
        'get': '_method_get',
        'has': '_method_has',
        'keys': '_method_keys',
        'values': '_method_values',
        'includes': '_method_contains',  # alias
        'hasFlag': '_method_has_flag',
        'inLineage': '_method_in_lineage',
    }
    
    def __init__(self, context: EvalContext):
        self.context = context
    
    def evaluate(self, node: ASTNode) -> Any:
        """Évalue un nœud AST et retourne sa valeur."""
        method_name = f'_eval_{node.node_type.name.lower()}'
        method = getattr(self, method_name, None)
        
        if method is None:
            raise ERKEvalError(
                message=f"Unknown node type: {node.node_type.name}",
                line=node.line,
                column=node.column
            )
        
        return method(node)
    
    def evaluate_rule(self, rule: RuleNode, rule_name: str = "") -> EvalResult:
        """Évalue une règle complète et retourne un résultat structuré."""
        try:
            value = self.evaluate(rule.expression)
            
            # Interpréter le résultat selon l'action
            ok = self._interpret_result(rule.action, value)
            
            return EvalResult(
                ok=ok,
                rule=rule_name,
                action=rule.action,
                value=value,
                reason=self._build_reason(rule.action, value, ok),
                details={"expression_value": value}
            )
        
        except (ERKEvalError, ERKReferenceError, ERKTypeError) as e:
            return EvalResult(
                ok=False,
                rule=rule_name,
                action=rule.action,
                reason=str(e),
                details={"error": e.to_dict()}
            )
    
    def _interpret_result(self, action: str, value: Any) -> bool:
        """Interprète la valeur selon l'action de la règle."""
        # Pour enable/allow/require/validate: True = ok
        # Pour deny/disable: True = NOT ok (inversé)
        bool_value = self._to_bool(value)
        
        if action in ('deny', 'disable'):
            return not bool_value
        
        return bool_value
    
    def _to_bool(self, value: Any) -> bool:
        """Convertit une valeur en booléen."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True
    
    def _build_reason(self, action: str, value: Any, ok: bool) -> str:
        """Construit une raison lisible pour le résultat."""
        if action in ('enable', 'allow'):
            return "condition met" if ok else "condition not met"
        if action in ('deny', 'disable'):
            return "denial condition not triggered" if ok else "denial condition triggered"
        if action == 'require':
            return "requirement satisfied" if ok else "requirement not satisfied"
        if action == 'validate':
            return "validation passed" if ok else "validation failed"
        return f"evaluated to {value}"
    
    # === Évaluation des différents types de nœuds ===
    
    def _eval_boolean(self, node: LiteralNode) -> bool:
        return node.value
    
    def _eval_string(self, node: LiteralNode) -> str:
        return node.value
    
    def _eval_number(self, node: LiteralNode) -> float:
        return node.value
    
    def _eval_null(self, node: LiteralNode) -> None:
        return None
    
    def _eval_this(self, node: ThisNode) -> Any:
        if self.context.this is None:
            raise ERKReferenceError(
                message="'this' is not defined in context",
                line=node.line,
                column=node.column,
                reference="this"
            )
        return self.context.this
    
    def _eval_identifier(self, node: IdentifierNode) -> Any:
        name = node.name
        
        # Chercher dans les globals
        if name in self.context.globals:
            return self.context.globals[name]
        
        # Chercher dans les objets par ID
        if name in self.context.objects:
            return self.context.objects[name]
        
        # Chercher dans les lineages
        if name in self.context.lineages:
            return self.context.lineages[name]
        
        raise ERKReferenceError(
            message=f"Undefined identifier: {name}",
            line=node.line,
            column=node.column,
            reference=name,
            available=list(self.context.globals.keys())[:10]
        )
    
    def _eval_member_access(self, node: MemberAccessNode) -> Any:
        obj = self.evaluate(node.object)
        member = node.member
        
        if obj is None:
            raise ERKReferenceError(
                message=f"Cannot access '{member}' of null",
                line=node.line,
                column=node.column,
                reference=member
            )
        
        # Accès dictionnaire
        if isinstance(obj, dict):
            if member in obj:
                return obj[member]
            raise ERKReferenceError(
                message=f"Key '{member}' not found",
                line=node.line,
                column=node.column,
                reference=member,
                available=list(obj.keys())[:10]
            )
        
        # Accès attribut
        if hasattr(obj, member):
            return getattr(obj, member)
        
        raise ERKReferenceError(
            message=f"Object has no attribute '{member}'",
            line=node.line,
            column=node.column,
            reference=member
        )
    
    def _eval_binary_op(self, node: BinaryOpNode) -> Any:
        op = node.operator
        
        # Short-circuit pour AND/OR
        if op == 'AND':
            left = self.evaluate(node.left)
            if not self._to_bool(left):
                return False
            return self._to_bool(self.evaluate(node.right))
        
        if op == 'OR':
            left = self.evaluate(node.left)
            if self._to_bool(left):
                return True
            return self._to_bool(self.evaluate(node.right))
        
        # Évaluer les deux côtés
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        
        # Comparaisons
        if op == '==':
            return left == right
        if op == '!=':
            return left != right
        if op == '>':
            return left > right
        if op == '<':
            return left < right
        if op == '>=':
            return left >= right
        if op == '<=':
            return left <= right
        
        raise ERKEvalError(
            message=f"Unknown operator: {op}",
            line=node.line,
            column=node.column
        )
    
    def _eval_unary_op(self, node: UnaryOpNode) -> Any:
        if node.operator == 'NOT':
            value = self.evaluate(node.operand)
            return not self._to_bool(value)
        
        raise ERKEvalError(
            message=f"Unknown unary operator: {node.operator}",
            line=node.line,
            column=node.column
        )
    
    def _eval_method_call(self, node: MethodCallNode) -> Any:
        obj = self.evaluate(node.object)
        method_name = node.method
        args = [self.evaluate(arg) for arg in node.arguments]
        
        # Vérifier si c'est une méthode built-in
        if method_name in self.BUILTIN_METHODS:
            handler_name = self.BUILTIN_METHODS[method_name]
            handler = getattr(self, handler_name)
            return handler(obj, args, node)
        
        # Sinon, essayer d'appeler la méthode sur l'objet
        if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
            return getattr(obj, method_name)(*args)
        
        raise ERKEvalError(
            message=f"Unknown method: {method_name}",
            line=node.line,
            column=node.column
        )
    
    def _eval_array(self, node: ArrayNode) -> list:
        return [self.evaluate(elem) for elem in node.elements]
    
    def _eval_rule(self, node: RuleNode) -> Any:
        return self.evaluate(node.expression)
    
    # === Méthodes built-in ===
    
    def _method_contains(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.contains(value) - vérifie si obj contient value."""
        if len(args) != 1:
            raise ERKEvalError(
                message="contains() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        
        value = args[0]
        
        if isinstance(obj, str):
            return str(value) in obj
        if isinstance(obj, (list, tuple, set)):
            return value in obj
        if isinstance(obj, dict):
            return value in obj.values()
        
        return False
    
    def _method_starts_with(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.startsWith(prefix)"""
        if len(args) != 1:
            raise ERKEvalError(
                message="startsWith() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        return str(obj).startswith(str(args[0]))
    
    def _method_ends_with(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.endsWith(suffix)"""
        if len(args) != 1:
            raise ERKEvalError(
                message="endsWith() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        return str(obj).endswith(str(args[0]))
    
    def _method_is_empty(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.isEmpty()"""
        if obj is None:
            return True
        if isinstance(obj, (str, list, dict, tuple, set)):
            return len(obj) == 0
        return False
    
    def _method_is_not_empty(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.isNotEmpty()"""
        return not self._method_is_empty(obj, args, node)
    
    def _method_length(self, obj: Any, args: List[Any], node: ASTNode) -> int:
        """obj.length()"""
        if obj is None:
            return 0
        if isinstance(obj, (str, list, dict, tuple, set)):
            return len(obj)
        raise ERKTypeError(
            message="length() requires a string, list, or dict",
            line=node.line, column=node.column,
            expected_type="iterable",
            actual_type=type(obj).__name__
        )
    
    def _method_get(self, obj: Any, args: List[Any], node: ASTNode) -> Any:
        """obj.get(key, default?)"""
        if len(args) < 1:
            raise ERKEvalError(
                message="get() requires at least 1 argument",
                line=node.line, column=node.column
            )
        
        key = args[0]
        default = args[1] if len(args) > 1 else None
        
        if isinstance(obj, dict):
            return obj.get(key, default)
        if isinstance(obj, list) and isinstance(key, int):
            return obj[key] if 0 <= key < len(obj) else default
        
        return default
    
    def _method_has(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.has(key) - vérifie si la clé existe."""
        if len(args) != 1:
            raise ERKEvalError(
                message="has() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        
        key = args[0]
        
        if isinstance(obj, dict):
            return key in obj
        if isinstance(obj, (list, tuple)):
            return key in obj
        if hasattr(obj, key):
            return True
        
        return False
    
    def _method_keys(self, obj: Any, args: List[Any], node: ASTNode) -> list:
        """obj.keys()"""
        if isinstance(obj, dict):
            return list(obj.keys())
        raise ERKTypeError(
            message="keys() requires a dict",
            line=node.line, column=node.column,
            expected_type="dict",
            actual_type=type(obj).__name__
        )
    
    def _method_values(self, obj: Any, args: List[Any], node: ASTNode) -> list:
        """obj.values()"""
        if isinstance(obj, dict):
            return list(obj.values())
        raise ERKTypeError(
            message="values() requires a dict",
            line=node.line, column=node.column,
            expected_type="dict",
            actual_type=type(obj).__name__
        )
    
    def _method_has_flag(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.hasFlag(flag_name) - vérifie un flag dans l'objet."""
        if len(args) != 1:
            raise ERKEvalError(
                message="hasFlag() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        
        flag_name = args[0]
        
        # Chercher dans obj.flags
        if isinstance(obj, dict):
            flags = obj.get('flags', [])
            if isinstance(flags, list):
                return flag_name in flags
            if isinstance(flags, dict):
                return flags.get(flag_name, False)
        
        return False
    
    def _method_in_lineage(self, obj: Any, args: List[Any], node: ASTNode) -> bool:
        """obj.inLineage(lineage_name) - vérifie si l'objet est dans un lineage."""
        if len(args) != 1:
            raise ERKEvalError(
                message="inLineage() requires exactly 1 argument",
                line=node.line, column=node.column
            )
        
        lineage_name = args[0]
        
        # Obtenir l'ID de l'objet
        obj_id = None
        if isinstance(obj, dict):
            obj_id = obj.get('id') or obj.get('_id')
        elif hasattr(obj, 'id'):
            obj_id = obj.id
        
        if obj_id is None:
            return False
        
        # Vérifier dans le contexte
        lineage = self.context.lineages.get(lineage_name, [])
        return obj_id in lineage


def evaluate(ast: ASTNode, context: dict) -> Any:
    """Fonction utilitaire pour évaluer un AST."""
    ctx = EvalContext.from_dict(context) if isinstance(context, dict) else context
    evaluator = Evaluator(ctx)
    return evaluator.evaluate(ast)


def evaluate_rule(rule: RuleNode, context: dict, rule_name: str = "") -> EvalResult:
    """Fonction utilitaire pour évaluer une règle complète."""
    ctx = EvalContext.from_dict(context) if isinstance(context, dict) else context
    evaluator = Evaluator(ctx)
    return evaluator.evaluate_rule(rule, rule_name)
