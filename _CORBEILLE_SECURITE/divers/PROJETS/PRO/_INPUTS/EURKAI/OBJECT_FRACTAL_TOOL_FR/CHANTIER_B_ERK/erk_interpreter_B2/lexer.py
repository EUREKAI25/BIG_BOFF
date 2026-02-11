"""
ERK Lexer - Tokenization des règles ERK.

Transforme une chaîne de caractères en liste de tokens typés.
Supporte:
- Mots-clés: AND, OR, NOT, true, false, null, this
- Mots-clés conditionnels (B2): IF, THEN, ELSE, WHEN, ctx
- Opérateurs: ==, !=, >, <, >=, <=, :
- Délimiteurs: (, ), [, ], ., ,
- Identifiants et littéraux (strings, numbers)

Version: B2/2 - Conditions étendues et contexte
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Generator

from .errors import ERKLexerError


class TokenType(Enum):
    """Types de tokens ERK."""
    # Keywords
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    THIS = auto()
    
    # B2: Conditional keywords
    IF = auto()
    THEN = auto()
    ELSE = auto()
    WHEN = auto()
    CTX = auto()      # Contexte d'évaluation
    
    # Rule actions
    ACTION = auto()  # enable, allow, deny, require, validate, etc.
    
    # Literals
    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()
    
    # Operators
    EQ = auto()       # ==
    NEQ = auto()      # !=
    GT = auto()       # >
    LT = auto()       # <
    GTE = auto()      # >=
    LTE = auto()      # <=
    COLON = auto()    # :
    
    # Delimiters
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    LBRACKET = auto() # [
    RBRACKET = auto() # ]
    DOT = auto()      # .
    COMMA = auto()    # ,
    
    # Special
    EOF = auto()
    NEWLINE = auto()


@dataclass
class Token:
    """Token ERK avec position."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"


# Mots-clés réservés
KEYWORDS = {
    'AND': TokenType.AND,
    'OR': TokenType.OR,
    'NOT': TokenType.NOT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'null': TokenType.NULL,
    'this': TokenType.THIS,
    # B2: Conditional keywords
    'IF': TokenType.IF,
    'THEN': TokenType.THEN,
    'ELSE': TokenType.ELSE,
    'WHEN': TokenType.WHEN,
    'ctx': TokenType.CTX,
}

# Actions de règles ERK reconnues
RULE_ACTIONS = {
    'enable', 'disable', 'allow', 'deny', 
    'require', 'validate', 'compute', 'trigger',
    'assert', 'check', 'guard', 'when'
}

# Opérateurs multi-caractères (ordre important: plus longs d'abord)
OPERATORS = [
    ('==', TokenType.EQ),
    ('!=', TokenType.NEQ),
    ('>=', TokenType.GTE),
    ('<=', TokenType.LTE),
    ('>', TokenType.GT),
    ('<', TokenType.LT),
    (':', TokenType.COLON),
    ('(', TokenType.LPAREN),
    (')', TokenType.RPAREN),
    ('[', TokenType.LBRACKET),
    (']', TokenType.RBRACKET),
    ('.', TokenType.DOT),
    (',', TokenType.COMMA),
]


class Lexer:
    """Lexer pour les règles ERK."""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    @property
    def current_char(self) -> Optional[str]:
        """Caractère courant ou None si fin."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[str]:
        """Regarde le caractère à offset positions."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> str:
        """Avance d'un caractère et le retourne."""
        char = self.current_char
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def skip_whitespace(self):
        """Ignore les espaces (sauf newlines qui sont des tokens)."""
        while self.current_char and self.current_char in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Ignore les commentaires # jusqu'à fin de ligne."""
        if self.current_char == '#':
            while self.current_char and self.current_char != '\n':
                self.advance()
    
    def read_string(self) -> Token:
        """Lit une chaîne entre guillemets."""
        quote = self.current_char  # " ou '
        start_line = self.line
        start_col = self.column
        self.advance()  # skip opening quote
        
        value = []
        while self.current_char and self.current_char != quote:
            if self.current_char == '\\':
                self.advance()
                escape_char = self.current_char
                if escape_char == 'n':
                    value.append('\n')
                elif escape_char == 't':
                    value.append('\t')
                elif escape_char == '\\':
                    value.append('\\')
                elif escape_char == quote:
                    value.append(quote)
                else:
                    value.append('\\')
                    value.append(escape_char or '')
                if self.current_char:
                    self.advance()
            else:
                value.append(self.current_char)
                self.advance()
        
        if self.current_char != quote:
            raise ERKLexerError(
                f"Unterminated string starting at line {start_line}, column {start_col}",
                line=start_line, column=start_col
            )
        
        self.advance()  # skip closing quote
        return Token(TokenType.STRING, ''.join(value), start_line, start_col)
    
    def read_number(self) -> Token:
        """Lit un nombre (entier ou flottant)."""
        start_line = self.line
        start_col = self.column
        value = []
        
        # Partie entière
        while self.current_char and self.current_char.isdigit():
            value.append(self.advance())
        
        # Partie décimale
        if self.current_char == '.' and self.peek() and self.peek().isdigit():
            value.append(self.advance())  # le point
            while self.current_char and self.current_char.isdigit():
                value.append(self.advance())
        
        return Token(TokenType.NUMBER, ''.join(value), start_line, start_col)
    
    def read_identifier(self) -> Token:
        """Lit un identifiant ou mot-clé."""
        start_line = self.line
        start_col = self.column
        value = []
        
        # Premier caractère: lettre ou _
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            value.append(self.advance())
        
        name = ''.join(value)
        
        # Vérifier si c'est un mot-clé
        if name in KEYWORDS:
            return Token(KEYWORDS[name], name, start_line, start_col)
        
        # Vérifier si c'est une action de règle (au début d'une ligne ou après newline)
        if name.lower() in RULE_ACTIONS:
            return Token(TokenType.ACTION, name.lower(), start_line, start_col)
        
        return Token(TokenType.IDENTIFIER, name, start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        """Tokenize la source complète."""
        self.tokens = []
        
        while self.current_char:
            # Espaces
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue
            
            # Commentaires
            if self.current_char == '#':
                self.skip_comment()
                continue
            
            # Newlines
            if self.current_char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self.advance()
                continue
            
            # Strings
            if self.current_char in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # Numbers
            if self.current_char.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Identifiers / Keywords
            if self.current_char.isalpha() or self.current_char == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Operators
            found = False
            for op, tok_type in OPERATORS:
                if self.source[self.pos:self.pos + len(op)] == op:
                    self.tokens.append(Token(tok_type, op, self.line, self.column))
                    for _ in range(len(op)):
                        self.advance()
                    found = True
                    break
            
            if found:
                continue
            
            # Caractère inconnu
            raise ERKLexerError(
                f"Unexpected character '{self.current_char}'",
                line=self.line, column=self.column
            )
        
        # Ajouter EOF
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        
        return self.tokens


def tokenize(source: str) -> List[Token]:
    """Fonction utilitaire pour tokenizer une source."""
    lexer = Lexer(source)
    return lexer.tokenize()
