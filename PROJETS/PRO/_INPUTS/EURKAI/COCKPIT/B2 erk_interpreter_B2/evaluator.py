"""
ERK Evaluator - Évaluation de l'AST dans un contexte.

L'évaluateur traverse l'AST et calcule la valeur résultante
en utilisant le contexte fourni pour résoudre les références.

Contexte attendu B2/2:
{
    "this": <objet courant>,
    "ctx": {                    # B2: Variables de contexte
        "layer": "System",      # Couche courante
        "mode": "normal",       # Mode d'exécution
        "state": "active",      # État global
        ...
    },
    "objects": { id: object, ... },  # pour résolution par ID
    "lineages": { name: [ids], ... }, # pour résolution par lineage
    "globals": { ... }  # variables globales
}

Version: B2/2 - Conditions étendues, contexte et traçabilité
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from .ast_nodes import (
    ASTNode, NodeType, LiteralNode, IdentifierNode, ThisNode, CtxNode,
    MemberAccessNode, BinaryOpNode, UnaryOpNode, MethodCallNode,
    ArrayNode, RuleNode, IfThenElseNode, WhenThenNode
)
from .errors import ERKEvalError, ERKReferenceError, ERKTypeError


# ============================================================================
# B2: Système de traçabilité
# ============================================================================

class TraceEventType(Enum):
    """Types d'événements de trace."""
    EVAL_START = auto()
    EVAL_END = auto()
    CONDITION_CHECK = auto()
    BRANCH_TAKEN = auto()
    BRANCH_SKIPPED = auto()
    VALUE_RESOLVED = auto()
    METHOD_CALLED = auto()
    ERROR = auto()


@dataclass
class TraceEvent:
    """Événement de trace pour le debugging."""
    event_type: TraceEventType
    node_type: str
    description: str
    value: Any = None
    line: int = 0
    column: int = 0
    
    def to_dict(self) -> dict:
        return {
            "event": self.event_type.name,
            "node": self.node_type,
            "description": self.description,
            "value": repr(self.value) if self.value is not None else None,
            "location": f"L{self.line}:C{self.column}" if self.line else None
        }


@dataclass
class EvalTrace:
    """
    B2: Trace complète d'évaluation pour la traçabilité.
    
    Permet de savoir exactement:
    - Quelles branches ont été prises
    - Quelles conditions ont été évaluées
    - Pourquoi une règle a retourné ok/error
    """
    events: List[TraceEvent] = field(default_factory=list)
    depth: int = 0
    
    def add(self, event_type: TraceEventType, node_type: str, 
            description: str, value: Any = None, line: int = 0, column: int = 0):
        """Ajoute un événement à la trace."""
        self.events.append(TraceEvent(
            event_type=event_type,
            node_type=node_type,
            description=description,
            value=value,
            line=line,
            column=column
        ))
    
    def condition_checked(self, description: str, result: bool, node: ASTNode = None):
        """Enregistre une vérification de condition."""
        self.add(
            TraceEventType.CONDITION_CHECK,
            node.__class__.__name__ if node else "Unknown",
            description,
            result,
            node.line if node else 0,
            node.column if node else 0
        )
    
    def branch_taken(self, branch_name: str, node: ASTNode = None):
        """Enregistre une branche prise."""
        self.add(
            TraceEventType.BRANCH_TAKEN,
            node.__class__.__name__ if node else "Unknown",
            f"Branch taken: {branch_name}",
            None,
            node.line if node else 0,
            node.column if node else 0
        )
    
    def branch_skipped(self, branch_name: str, node: ASTNode = None):
        """Enregistre une branche sautée."""
        self.add(
            TraceEventType.BRANCH_SKIPPED,
            node.__class__.__name__ if node else "Unknown",
            f"Branch skipped: {branch_name}",
            None,
            node.line if node else 0,
            node.column if node else 0
        )
    
    def to_summary(self) -> dict:
        """Résumé de la trace pour affichage."""
        branches_taken = [e for e in self.events if e.event_type == TraceEventType.BRANCH_TAKEN]
        conditions = [e for e in self.events if e.event_type == TraceEventType.CONDITION_CHECK]
        
        return {
            "total_events": len(self.events),
            "branches_taken": [e.description for e in branches_taken],
            "conditions_evaluated": len(conditions),
            "conditions_true": sum(1 for e in conditions if e.value is True),
            "conditions_false": sum(1 for e in conditions if e.value is False),
        }
    
    def to_list(self) -> List[dict]:
        """Exporte tous les événements."""
        return [e.to_dict() for e in self.events]


# ============================================================================
# Résultat d'évaluation amélioré
# ============================================================================

@dataclass
class EvalResult:
    """Résultat d'évaluation d'une règle ERK avec traçabilité B2."""
    ok: bool
    rule: str
    action: str
    value: Any = None
    reason: str = ""
    details: dict = field(default_factory=dict)
    trace: EvalTrace = field(default_factory=EvalTrace)
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour la console."""
        result = {
            "ok": self.ok,
            "rule": self.rule,
            "action": self.action,
            "value": self.value,
            "reason": self.reason,
            "details": self.details
        }
        
        # B2: Ajouter la trace si disponible
        if self.trace and self.trace.events:
            result["trace"] = self.trace.to_summary()
        
        return result
    
    def to_dict_full(self) -> dict:
        """Convertit avec trace complète."""
        result = self.to_dict()
        if self.trace:
            result["trace_full"] = self.trace.to_list()
        return result


# ============================================================================
# Contexte d'évaluation B2
# ============================================================================

@dataclass
class EvalContext:
    """
    Contexte d'évaluation ERK B2.
    
    Inclut maintenant le contexte 'ctx' pour les variables d'exécution.
    """
    this: Any = None  # L'objet courant
    ctx: Dict[str, Any] = field(default_factory=dict)  # B2: Contexte d'exécution
    objects: Dict[str, Any] = field(default_factory=dict)  # Objets par ID
    lineages: Dict[str, List[str]] = field(default_factory=dict)  # Lineages
    globals: Dict[str, Any] = field(default_factory=dict)  # Variables globales
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EvalContext':
        """Crée un contexte depuis un dictionnaire."""
        return cls(
            this=data.get('this'),
            ctx=data.get('ctx', {}),
            objects=data.get('objects', {}),
            lineages=data.get('lineages', {}),
            globals=data.get('globals', {})
        )


# ============================================================================
# Évaluateur principal
# ============================================================================

class Evaluator:
    """Évaluateur pour les expressions ERK avec traçabilité B2."""
    
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
    
    def __init__(self, context: EvalContext, enable_trace: bool = True):
        self.context = context
        self.enable_trace = enable_trace
        self.trace = EvalTrace() if enable_trace else None
    
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
        """Évalue une règle complète et retourne un résultat structuré avec trace."""
        # Reset trace pour cette évaluation
        if self.enable_trace:
            self.trace = EvalTrace()
        
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
                details={"expression_value": value},
                trace=self.trace
            )
        
        except (ERKEvalError, ERKReferenceError, ERKTypeError) as e:
            if self.trace:
                self.trace.add(
                    TraceEventType.ERROR,
                    "Error",
                    str(e),
                    line=e.line or 0,
                    column=e.column or 0
                )
            
            return EvalResult(
                ok=False,
                rule=rule_name,
                action=rule.action,
                reason=str(e),
                details={"error": e.to_dict()},
                trace=self.trace
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
    
    def _eval_ctx(self, node: CtxNode) -> Any:
        """B2: Évalue la référence au contexte 'ctx'."""
        if self.trace:
            self.trace.add(
                TraceEventType.VALUE_RESOLVED,
                "Ctx",
                "Accessed execution context",
                self.context.ctx,
                node.line,
                node.column
            )
        return self.context.ctx
    
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
            message=f"Attribute '{member}' not found",
            line=node.line,
            column=node.column,
            reference=member
        )
    
    def _eval_binary_op(self, node: BinaryOpNode) -> Any:
        op = node.operator
        
        # Short-circuit pour AND et OR
        if op == 'AND':
            left = self.evaluate(node.left)
            left_bool = self._to_bool(left)
            
            if self.trace:
                self.trace.condition_checked(
                    f"AND left operand: {repr(left)}", 
                    left_bool, 
                    node.left
                )
            
            if not left_bool:
                if self.trace:
                    self.trace.branch_skipped("AND right (short-circuit)", node)
                return False
            
            right = self.evaluate(node.right)
            right_bool = self._to_bool(right)
            
            if self.trace:
                self.trace.condition_checked(
                    f"AND right operand: {repr(right)}", 
                    right_bool, 
                    node.right
                )
            
            return right_bool
        
        if op == 'OR':
            left = self.evaluate(node.left)
            left_bool = self._to_bool(left)
            
            if self.trace:
                self.trace.condition_checked(
                    f"OR left operand: {repr(left)}", 
                    left_bool, 
                    node.left
                )
            
            if left_bool:
                if self.trace:
                    self.trace.branch_skipped("OR right (short-circuit)", node)
                return True
            
            right = self.evaluate(node.right)
            right_bool = self._to_bool(right)
            
            if self.trace:
                self.trace.condition_checked(
                    f"OR right operand: {repr(right)}", 
                    right_bool, 
                    node.right
                )
            
            return right_bool
        
        # Autres opérateurs (comparaisons)
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        
        if op == '==':
            result = left == right
        elif op == '!=':
            result = left != right
        elif op == '>':
            result = left > right
        elif op == '<':
            result = left < right
        elif op == '>=':
            result = left >= right
        elif op == '<=':
            result = left <= right
        else:
            raise ERKEvalError(
                message=f"Unknown operator: {op}",
                line=node.line,
                column=node.column
            )
        
        if self.trace:
            self.trace.condition_checked(
                f"{repr(left)} {op} {repr(right)}",
                result,
                node
            )
        
        return result
    
    def _eval_unary_op(self, node: UnaryOpNode) -> Any:
        if node.operator == 'NOT':
            value = self.evaluate(node.operand)
            result = not self._to_bool(value)
            
            if self.trace:
                self.trace.condition_checked(
                    f"NOT {repr(value)}",
                    result,
                    node
                )
            
            return result
        
        raise ERKEvalError(
            message=f"Unknown unary operator: {node.operator}",
            line=node.line,
            column=node.column
        )
    
    def _eval_method_call(self, node: MethodCallNode) -> Any:
        obj = self.evaluate(node.object)
        method_name = node.method
        args = [self.evaluate(arg) for arg in node.arguments]
        
        if self.trace:
            self.trace.add(
                TraceEventType.METHOD_CALLED,
                "MethodCall",
                f"Calling {method_name}({', '.join(repr(a) for a in args)})",
                line=node.line,
                column=node.column
            )
        
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
    
    # ========================================================================
    # B2: Évaluation des nœuds conditionnels
    # ========================================================================
    
    def _eval_if_then_else(self, node: IfThenElseNode) -> Any:
        """
        B2: Évalue IF condition THEN consequence [ELSE alternative]
        
        Retourne:
          - then_branch si condition est vraie
          - else_branch si condition est fausse et ELSE existe
          - False si condition est fausse et pas de ELSE
        """
        # Évaluer la condition
        condition_value = self.evaluate(node.condition)
        condition_bool = self._to_bool(condition_value)
        
        if self.trace:
            self.trace.condition_checked(
                f"IF condition: {repr(condition_value)}",
                condition_bool,
                node.condition
            )
        
        if condition_bool:
            # Condition vraie -> évaluer THEN
            if self.trace:
                self.trace.branch_taken("THEN", node)
            
            result = self.evaluate(node.then_branch)
            return result
        else:
            # Condition fausse
            if node.else_branch is not None:
                # ELSE existe -> évaluer ELSE
                if self.trace:
                    self.trace.branch_taken("ELSE", node)
                
                result = self.evaluate(node.else_branch)
                return result
            else:
                # Pas de ELSE -> retourner False
                if self.trace:
                    self.trace.branch_skipped("ELSE (not defined)", node)
                
                return False
    
    def _eval_when_then(self, node: WhenThenNode) -> Any:
        """
        B2: Évalue WHEN condition THEN result
        
        Similaire à IF mais sans ELSE.
        Retourne:
          - then_result si condition est vraie
          - False si condition est fausse
        """
        # Évaluer la condition
        condition_value = self.evaluate(node.condition)
        condition_bool = self._to_bool(condition_value)
        
        if self.trace:
            self.trace.condition_checked(
                f"WHEN condition: {repr(condition_value)}",
                condition_bool,
                node.condition
            )
        
        if condition_bool:
            if self.trace:
                self.trace.branch_taken("THEN (WHEN)", node)
            
            result = self.evaluate(node.then_result)
            return result
        else:
            if self.trace:
                self.trace.branch_skipped("WHEN condition not met", node)
            
            return False
    
    # ========================================================================
    # Méthodes built-in
    # ========================================================================
    
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


# ============================================================================
# Fonctions utilitaires
# ============================================================================

def evaluate(ast: ASTNode, context: dict, enable_trace: bool = False) -> Any:
    """Fonction utilitaire pour évaluer un AST."""
    ctx = EvalContext.from_dict(context) if isinstance(context, dict) else context
    evaluator = Evaluator(ctx, enable_trace=enable_trace)
    return evaluator.evaluate(ast)


def evaluate_rule(rule: RuleNode, context: dict, rule_name: str = "", 
                  enable_trace: bool = True) -> EvalResult:
    """Fonction utilitaire pour évaluer une règle complète."""
    ctx = EvalContext.from_dict(context) if isinstance(context, dict) else context
    evaluator = Evaluator(ctx, enable_trace=enable_trace)
    return evaluator.evaluate_rule(rule, rule_name)
