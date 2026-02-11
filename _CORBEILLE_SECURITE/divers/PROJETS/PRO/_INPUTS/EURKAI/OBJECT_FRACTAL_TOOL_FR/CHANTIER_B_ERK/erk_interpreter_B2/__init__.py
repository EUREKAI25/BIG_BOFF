"""
ERK - Interpréteur de Règles EUREKAI (V2 - Conditions étendues)

Ce module fournit un interpréteur pour les règles ERK utilisées
dans le système EUREKAI pour définir des autorisations, validations,
et comportements conditionnels.

Usage basique:
    from erk import ERK
    
    # Avec un store configuré
    ERK.eval("object_id", "rule_name")
    ERK.eval("object_id", "rule_name", {"extra_context": "value"})
    
    # Validation de syntaxe
    ERK.validate("enable: this.flags.contains('active')")
    
    # Parsing pour debug
    ERK.parse("allow: this.type == 'Agent' AND this.priority > 5")

Syntaxe ERK supportée (V2):
    - Actions: enable, disable, allow, deny, require, validate, etc.
    - Références: this, ctx (B2), identifiants, accès membres
    - Opérateurs: ==, !=, >, <, >=, <=, AND, OR, NOT
    - Littéraux: true, false, null, strings, numbers
    - Méthodes: contains(), startsWith(), isEmpty(), has(), hasFlag(), etc.
    - Arrays: [a, b, c]
    - B2: IF condition THEN result [ELSE alternative]
    - B2: WHEN condition THEN result
    - B2: ctx.variable pour accès au contexte d'exécution

Exemple de règles:
    enable: this.flags.contains("prompt_enabled")
    allow: this.type == "Agent" AND this.priority == "natural"
    deny: this.status == "suspended" OR this.credits <= 0
    require: this.config.has("api_key") AND this.config.api_key.isNotEmpty()
    
    # B2: Conditions étendues
    enable: IF this.priority == "natural" THEN enable ELSE disable
    allow: WHEN ctx.layer == "System" AND this.type == "Agent" THEN allow

Version: B2/2 - Conditions étendues et contexte
"""

__version__ = "2.0.0"
__author__ = "EUREKAI"

# Imports publics
from .ast_nodes import (
    ASTNode,
    NodeType,
    LiteralNode,
    IdentifierNode,
    ThisNode,
    CtxNode,  # B2
    MemberAccessNode,
    BinaryOpNode,
    UnaryOpNode,
    MethodCallNode,
    ArrayNode,
    RuleNode,
    IfThenElseNode,  # B2
    WhenThenNode,    # B2
)

from .errors import (
    ERKError,
    ERKLexerError,
    ERKParseError,
    ERKEvalError,
    ERKReferenceError,
    ERKTypeError
)

from .lexer import tokenize, Token, TokenType

from .parser import parse, parse_expression, parse_conditional  # B2: parse_conditional

from .evaluator import (
    evaluate,
    evaluate_rule,
    EvalResult,
    EvalContext,
    Evaluator,
    EvalTrace,       # B2
    TraceEvent,      # B2
    TraceEventType,  # B2
)

from .console import (
    ERKConsole,
    StoreAdapter,
    get_console
)


# API de façade simplifiée
class _ERKFacade:
    """
    Façade simplifiée pour l'API ERK.
    
    Permet d'utiliser ERK.eval(), ERK.parse(), etc. directement.
    """
    
    def __init__(self):
        self._console = None
    
    def configure(self, store: StoreAdapter = None):
        """Configure l'interpréteur avec un store."""
        self._console = ERKConsole(store)
        return self
    
    @property
    def console(self) -> ERKConsole:
        """Obtient la console (crée une instance par défaut si nécessaire)."""
        if self._console is None:
            self._console = ERKConsole()
        return self._console
    
    def eval(self, object_id: str, rule_name: str, context: dict = None) -> dict:
        """Évalue une règle sur un objet."""
        return self.console.eval(object_id, rule_name, context)
    
    def parse(self, rule_text: str) -> dict:
        """Parse une règle et retourne l'AST."""
        return self.console.parse(rule_text)
    
    def validate(self, rule_text: str) -> dict:
        """Valide la syntaxe d'une règle."""
        return self.console.validate(rule_text)
    
    def list_rules(self, object_id: str) -> dict:
        """Liste les règles d'un objet."""
        return self.console.list_rules(object_id)
    
    def eval_all(self, object_id: str, context: dict = None) -> dict:
        """Évalue toutes les règles d'un objet."""
        return self.console.eval_all(object_id, context)
    
    def quick_eval(self, rule_text: str, context: dict) -> dict:
        """
        Évalue une règle directement sans passer par le store.
        
        Utile pour les tests rapides.
        
        Args:
            rule_text: Texte de la règle ERK
            context: Contexte avec au minimum {"this": {...}}
        
        Returns:
            Résultat de l'évaluation
        """
        try:
            rule_ast = parse(rule_text)
            result = evaluate_rule(rule_ast, context, "inline")
            return result.to_dict()
        except ERKError as e:
            return e.to_dict()


# Instance globale
ERK = _ERKFacade()


# Exports
__all__ = [
    # Façade principale
    'ERK',
    
    # Classes AST
    'ASTNode',
    'NodeType',
    'LiteralNode',
    'IdentifierNode',
    'ThisNode',
    'CtxNode',           # B2
    'MemberAccessNode',
    'BinaryOpNode',
    'UnaryOpNode',
    'MethodCallNode',
    'ArrayNode',
    'RuleNode',
    'IfThenElseNode',    # B2
    'WhenThenNode',      # B2
    
    # Erreurs
    'ERKError',
    'ERKLexerError',
    'ERKParseError',
    'ERKEvalError',
    'ERKReferenceError',
    'ERKTypeError',
    
    # Lexer
    'tokenize',
    'Token',
    'TokenType',
    
    # Parser
    'parse',
    'parse_expression',
    'parse_conditional',  # B2
    
    # Evaluator
    'evaluate',
    'evaluate_rule',
    'EvalResult',
    'EvalContext',
    'Evaluator',
    'EvalTrace',          # B2
    'TraceEvent',         # B2
    'TraceEventType',     # B2
    
    # Console
    'ERKConsole',
    'StoreAdapter',
    'get_console',
]
