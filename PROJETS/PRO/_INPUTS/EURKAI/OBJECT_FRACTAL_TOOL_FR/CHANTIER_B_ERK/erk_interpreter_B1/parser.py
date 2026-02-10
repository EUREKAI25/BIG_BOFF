"""
ERK Parser - Construction de l'AST à partir des tokens.

Grammaire ERK (simplifiée):
    rule       := action ':' expression
    expression := or_expr
    or_expr    := and_expr ('OR' and_expr)*
    and_expr   := not_expr ('AND' not_expr)*
    not_expr   := 'NOT' not_expr | comparison
    comparison := term (('==' | '!=' | '>' | '<' | '>=' | '<=') term)?
    term       := primary (('.' IDENTIFIER) | ('.' IDENTIFIER '(' args ')'))*
    primary    := 'this' | IDENTIFIER | literal | '(' expression ')' | array
    literal    := STRING | NUMBER | 'true' | 'false' | 'null'
    array      := '[' (expression (',' expression)*)? ']'
    args       := (expression (',' expression)*)?
"""

from typing import List, Optional
from .lexer import Token, TokenType, tokenize
from .ast_nodes import (
    ASTNode, NodeType, LiteralNode, IdentifierNode, ThisNode,
    MemberAccessNode, BinaryOpNode, UnaryOpNode, MethodCallNode,
    ArrayNode, RuleNode
)
from .errors import ERKParseError


class Parser:
    """Parser pour les règles ERK."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]  # Ignore newlines
        self.pos = 0
    
    @property
    def current(self) -> Token:
        """Token courant."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Token:
        """Regarde le token à offset positions."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Avance et retourne le token précédent."""
        token = self.current
        self.pos += 1
        return token
    
    def expect(self, tok_type: TokenType, message: str = None) -> Token:
        """Attend un type de token spécifique."""
        if self.current.type != tok_type:
            msg = message or f"Expected {tok_type.name}"
            raise ERKParseError(
                message=msg,
                line=self.current.line,
                column=self.current.column,
                expected=tok_type.name,
                found=self.current.type.name
            )
        return self.advance()
    
    def match(self, *types: TokenType) -> bool:
        """Vérifie si le token courant est l'un des types."""
        return self.current.type in types
    
    def parse_rule(self) -> RuleNode:
        """Parse une règle complète: action: expression."""
        # Action (enable, allow, etc.)
        if self.current.type == TokenType.ACTION:
            action_token = self.advance()
            action = action_token.value
        elif self.current.type == TokenType.IDENTIFIER:
            # Permet aussi des actions comme identifiants
            action_token = self.advance()
            action = action_token.value
        else:
            raise ERKParseError(
                message="Expected rule action (enable, allow, deny, etc.)",
                line=self.current.line,
                column=self.current.column,
                found=self.current.type.name
            )
        
        # Deux-points
        self.expect(TokenType.COLON, "Expected ':' after rule action")
        
        # Expression
        expr = self.parse_expression()
        
        return RuleNode(
            node_type=NodeType.RULE,
            action=action,
            expression=expr,
            line=action_token.line,
            column=action_token.column
        )
    
    def parse_expression(self) -> ASTNode:
        """Parse une expression (point d'entrée)."""
        return self.parse_or_expr()
    
    def parse_or_expr(self) -> ASTNode:
        """Parse: and_expr ('OR' and_expr)*"""
        left = self.parse_and_expr()
        
        while self.current.type == TokenType.OR:
            op_token = self.advance()
            right = self.parse_and_expr()
            left = BinaryOpNode(
                node_type=NodeType.BINARY_OP,
                operator='OR',
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_and_expr(self) -> ASTNode:
        """Parse: not_expr ('AND' not_expr)*"""
        left = self.parse_not_expr()
        
        while self.current.type == TokenType.AND:
            op_token = self.advance()
            right = self.parse_not_expr()
            left = BinaryOpNode(
                node_type=NodeType.BINARY_OP,
                operator='AND',
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_not_expr(self) -> ASTNode:
        """Parse: 'NOT' not_expr | comparison"""
        if self.current.type == TokenType.NOT:
            op_token = self.advance()
            operand = self.parse_not_expr()
            return UnaryOpNode(
                node_type=NodeType.UNARY_OP,
                operator='NOT',
                operand=operand,
                line=op_token.line,
                column=op_token.column
            )
        
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        """Parse: term (('==' | '!=' | '>' | '<' | '>=' | '<=') term)?"""
        left = self.parse_term()
        
        comparison_ops = {
            TokenType.EQ: '==',
            TokenType.NEQ: '!=',
            TokenType.GT: '>',
            TokenType.LT: '<',
            TokenType.GTE: '>=',
            TokenType.LTE: '<=',
        }
        
        if self.current.type in comparison_ops:
            op_token = self.advance()
            op = comparison_ops[op_token.type]
            right = self.parse_term()
            return BinaryOpNode(
                node_type=NodeType.BINARY_OP,
                operator=op,
                left=left,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_term(self) -> ASTNode:
        """Parse: primary (('.' IDENTIFIER) | ('.' IDENTIFIER '(' args ')'))*"""
        node = self.parse_primary()
        
        while self.current.type == TokenType.DOT:
            self.advance()  # consume '.'
            
            if self.current.type != TokenType.IDENTIFIER:
                raise ERKParseError(
                    message="Expected identifier after '.'",
                    line=self.current.line,
                    column=self.current.column
                )
            
            member_token = self.advance()
            member_name = member_token.value
            
            # Check for method call
            if self.current.type == TokenType.LPAREN:
                self.advance()  # consume '('
                args = self.parse_arguments()
                self.expect(TokenType.RPAREN, "Expected ')' after method arguments")
                
                node = MethodCallNode(
                    node_type=NodeType.METHOD_CALL,
                    object=node,
                    method=member_name,
                    arguments=args,
                    line=member_token.line,
                    column=member_token.column
                )
            else:
                node = MemberAccessNode(
                    node_type=NodeType.MEMBER_ACCESS,
                    object=node,
                    member=member_name,
                    line=member_token.line,
                    column=member_token.column
                )
        
        return node
    
    def parse_arguments(self) -> List[ASTNode]:
        """Parse: (expression (',' expression)*)?"""
        args = []
        
        if self.current.type == TokenType.RPAREN:
            return args
        
        args.append(self.parse_expression())
        
        while self.current.type == TokenType.COMMA:
            self.advance()
            args.append(self.parse_expression())
        
        return args
    
    def parse_primary(self) -> ASTNode:
        """Parse: 'this' | IDENTIFIER | literal | '(' expression ')' | array"""
        token = self.current
        
        # this
        if token.type == TokenType.THIS:
            self.advance()
            return ThisNode(line=token.line, column=token.column)
        
        # true / false
        if token.type == TokenType.TRUE:
            self.advance()
            return LiteralNode(
                node_type=NodeType.BOOLEAN,
                value=True,
                line=token.line,
                column=token.column
            )
        
        if token.type == TokenType.FALSE:
            self.advance()
            return LiteralNode(
                node_type=NodeType.BOOLEAN,
                value=False,
                line=token.line,
                column=token.column
            )
        
        # null
        if token.type == TokenType.NULL:
            self.advance()
            return LiteralNode(
                node_type=NodeType.NULL,
                value=None,
                line=token.line,
                column=token.column
            )
        
        # string
        if token.type == TokenType.STRING:
            self.advance()
            return LiteralNode(
                node_type=NodeType.STRING,
                value=token.value,
                line=token.line,
                column=token.column
            )
        
        # number
        if token.type == TokenType.NUMBER:
            self.advance()
            value = float(token.value) if '.' in token.value else int(token.value)
            return LiteralNode(
                node_type=NodeType.NUMBER,
                value=value,
                line=token.line,
                column=token.column
            )
        
        # identifier
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return IdentifierNode(
                node_type=NodeType.IDENTIFIER,
                name=token.value,
                line=token.line,
                column=token.column
            )
        
        # parenthesized expression
        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')'")
            return expr
        
        # array
        if token.type == TokenType.LBRACKET:
            return self.parse_array()
        
        raise ERKParseError(
            message="Unexpected token",
            line=token.line,
            column=token.column,
            found=token.type.name
        )
    
    def parse_array(self) -> ArrayNode:
        """Parse: '[' (expression (',' expression)*)? ']'"""
        start_token = self.expect(TokenType.LBRACKET)
        elements = []
        
        if self.current.type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            
            while self.current.type == TokenType.COMMA:
                self.advance()
                elements.append(self.parse_expression())
        
        self.expect(TokenType.RBRACKET, "Expected ']'")
        
        return ArrayNode(
            node_type=NodeType.ARRAY,
            elements=elements,
            line=start_token.line,
            column=start_token.column
        )


def parse(source: str) -> RuleNode:
    """Parse une règle ERK depuis une chaîne."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse_rule()


def parse_expression(source: str) -> ASTNode:
    """Parse une expression ERK seule (sans action:)."""
    tokens = tokenize(source)
    parser = Parser(tokens)
    return parser.parse_expression()
