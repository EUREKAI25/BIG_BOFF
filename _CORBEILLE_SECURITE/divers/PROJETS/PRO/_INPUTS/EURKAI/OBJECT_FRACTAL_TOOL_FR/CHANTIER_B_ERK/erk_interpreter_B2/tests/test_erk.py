"""
Tests pour l'interpréteur ERK minimal.

Ces tests vérifient:
- Le lexer (tokenization)
- Le parser (construction AST)
- L'évaluateur (évaluation dans un contexte)
- L'intégration console
- Les cas d'erreur
"""

import pytest
from erk import (
    ERK,
    parse,
    parse_expression,
    tokenize,
    evaluate,
    evaluate_rule,
    ERKConsole,
    StoreAdapter,
    ERKParseError,
    ERKEvalError,
    ERKReferenceError,
    TokenType
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_store():
    """Store de test avec des objets et règles."""
    store = StoreAdapter()
    
    # Objets de test
    store.objects = {
        "agent_001": {
            "id": "agent_001",
            "type": "Agent",
            "priority": "natural",
            "status": "active",
            "flags": ["prompt_enabled", "can_execute"],
            "config": {
                "api_key": "sk-xxx",
                "max_tokens": 1000
            },
            "credits": 100
        },
        "agent_002": {
            "id": "agent_002",
            "type": "Agent",
            "priority": "high",
            "status": "suspended",
            "flags": [],
            "config": {},
            "credits": 0
        },
        "task_001": {
            "id": "task_001",
            "type": "Task",
            "owner": "agent_001",
            "status": "pending",
            "priority": 5
        }
    }
    
    # Lineages
    store.lineages = {
        "active_agents": ["agent_001"],
        "all_agents": ["agent_001", "agent_002"]
    }
    
    # Règles
    store.rules = {
        "agent_001": {
            "can_prompt": "enable: this.flags.contains('prompt_enabled')",
            "can_execute": "allow: this.status == 'active' AND this.credits > 0",
            "is_natural": "check: this.priority == 'natural'",
            "has_config": "require: this.config.has('api_key')"
        },
        "agent_002": {
            "can_execute": "allow: this.status == 'active' AND this.credits > 0",
            "is_suspended": "check: this.status == 'suspended'"
        },
        "task_001": {
            "can_start": "enable: this.status == 'pending' AND this.priority >= 3"
        }
    }
    
    return store


@pytest.fixture
def console(sample_store):
    """Console configurée avec le store de test."""
    return ERKConsole(sample_store)


# ============================================================================
# TESTS LEXER
# ============================================================================

class TestLexer:
    """Tests du lexer."""
    
    def test_simple_tokens(self):
        """Tokenize des éléments simples."""
        tokens = tokenize("this.flags")
        assert tokens[0].type == TokenType.THIS
        assert tokens[1].type == TokenType.DOT
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "flags"
    
    def test_operators(self):
        """Tokenize des opérateurs."""
        tokens = tokenize("a == b != c >= d <= e > f < g")
        ops = [t for t in tokens if t.type in (TokenType.EQ, TokenType.NEQ, 
               TokenType.GTE, TokenType.LTE, TokenType.GT, TokenType.LT)]
        assert len(ops) == 6
    
    def test_keywords(self):
        """Tokenize des mots-clés."""
        tokens = tokenize("true AND false OR NOT null")
        assert tokens[0].type == TokenType.TRUE
        assert tokens[1].type == TokenType.AND
        assert tokens[2].type == TokenType.FALSE
        assert tokens[3].type == TokenType.OR
        assert tokens[4].type == TokenType.NOT
        assert tokens[5].type == TokenType.NULL
    
    def test_strings(self):
        """Tokenize des chaînes."""
        tokens = tokenize('"hello" \'world\'')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"
        assert tokens[1].type == TokenType.STRING
        assert tokens[1].value == "world"
    
    def test_numbers(self):
        """Tokenize des nombres."""
        tokens = tokenize("42 3.14 0")
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "3.14"
    
    def test_action(self):
        """Tokenize une action de règle."""
        tokens = tokenize("enable: this.active")
        assert tokens[0].type == TokenType.ACTION
        assert tokens[0].value == "enable"
        assert tokens[1].type == TokenType.COLON


# ============================================================================
# TESTS PARSER
# ============================================================================

class TestParser:
    """Tests du parser."""
    
    def test_simple_rule(self):
        """Parse une règle simple."""
        ast = parse("enable: true")
        assert ast.action == "enable"
        assert ast.expression.value == True
    
    def test_comparison(self):
        """Parse une comparaison."""
        ast = parse("check: this.status == 'active'")
        assert ast.action == "check"
        expr = ast.expression
        assert expr.operator == "=="
    
    def test_logical_and(self):
        """Parse un AND logique."""
        ast = parse("allow: this.a == 1 AND this.b == 2")
        expr = ast.expression
        assert expr.operator == "AND"
    
    def test_logical_or(self):
        """Parse un OR logique."""
        ast = parse("allow: this.a == 1 OR this.b == 2")
        expr = ast.expression
        assert expr.operator == "OR"
    
    def test_not(self):
        """Parse un NOT."""
        ast = parse("deny: NOT this.active")
        expr = ast.expression
        assert expr.operator == "NOT"
    
    def test_method_call(self):
        """Parse un appel de méthode."""
        ast = parse("enable: this.flags.contains('active')")
        expr = ast.expression
        assert expr.method == "contains"
        assert len(expr.arguments) == 1
    
    def test_member_access_chain(self):
        """Parse une chaîne d'accès aux membres."""
        ast = parse("check: this.config.nested.value == 42")
        # L'expression devrait être une comparaison
        assert ast.expression.operator == "=="
    
    def test_array_literal(self):
        """Parse un tableau littéral."""
        expr = parse_expression("[1, 2, 'three']")
        assert len(expr.elements) == 3
    
    def test_parentheses(self):
        """Parse des parenthèses."""
        ast = parse("allow: (this.a OR this.b) AND this.c")
        # Le AND devrait être à la racine
        assert ast.expression.operator == "AND"
    
    def test_complex_expression(self):
        """Parse une expression complexe."""
        rule = "allow: this.status == 'active' AND (this.credits > 0 OR this.premium == true)"
        ast = parse(rule)
        assert ast.action == "allow"
    
    def test_invalid_syntax(self):
        """Gère une syntaxe invalide."""
        with pytest.raises(ERKParseError):
            parse("enable:")  # Expression manquante
    
    def test_unterminated_string(self):
        """Gère une chaîne non terminée."""
        with pytest.raises(Exception):  # ERKLexerError
            parse('check: this.name == "unterminated')


# ============================================================================
# TESTS EVALUATOR
# ============================================================================

class TestEvaluator:
    """Tests de l'évaluateur."""
    
    def test_literal_true(self):
        """Évalue un littéral true."""
        result = ERK.quick_eval("enable: true", {"this": {}})
        assert result["ok"] == True
    
    def test_literal_false(self):
        """Évalue un littéral false."""
        result = ERK.quick_eval("enable: false", {"this": {}})
        assert result["ok"] == False
    
    def test_this_member_access(self):
        """Évalue un accès membre sur this."""
        context = {"this": {"status": "active"}}
        result = ERK.quick_eval("check: this.status == 'active'", context)
        assert result["ok"] == True
    
    def test_nested_member_access(self):
        """Évalue un accès membre imbriqué."""
        context = {"this": {"config": {"enabled": True}}}
        result = ERK.quick_eval("check: this.config.enabled == true", context)
        assert result["ok"] == True
    
    def test_and_operator(self):
        """Évalue un AND."""
        context = {"this": {"a": True, "b": True}}
        result = ERK.quick_eval("check: this.a AND this.b", context)
        assert result["ok"] == True
        
        context = {"this": {"a": True, "b": False}}
        result = ERK.quick_eval("check: this.a AND this.b", context)
        assert result["ok"] == False
    
    def test_or_operator(self):
        """Évalue un OR."""
        context = {"this": {"a": False, "b": True}}
        result = ERK.quick_eval("check: this.a OR this.b", context)
        assert result["ok"] == True
    
    def test_not_operator(self):
        """Évalue un NOT."""
        context = {"this": {"active": False}}
        result = ERK.quick_eval("check: NOT this.active", context)
        assert result["ok"] == True
    
    def test_contains_method(self):
        """Évalue la méthode contains."""
        context = {"this": {"flags": ["a", "b", "c"]}}
        result = ERK.quick_eval("check: this.flags.contains('b')", context)
        assert result["ok"] == True
        
        result = ERK.quick_eval("check: this.flags.contains('x')", context)
        assert result["ok"] == False
    
    def test_has_method(self):
        """Évalue la méthode has."""
        context = {"this": {"config": {"key": "value"}}}
        result = ERK.quick_eval("check: this.config.has('key')", context)
        assert result["ok"] == True
        
        result = ERK.quick_eval("check: this.config.has('missing')", context)
        assert result["ok"] == False
    
    def test_isEmpty_method(self):
        """Évalue la méthode isEmpty."""
        context = {"this": {"list": []}}
        result = ERK.quick_eval("check: this.list.isEmpty()", context)
        assert result["ok"] == True
        
        context = {"this": {"list": [1, 2]}}
        result = ERK.quick_eval("check: this.list.isEmpty()", context)
        assert result["ok"] == False
    
    def test_numeric_comparison(self):
        """Évalue des comparaisons numériques."""
        context = {"this": {"value": 10}}
        
        result = ERK.quick_eval("check: this.value > 5", context)
        assert result["ok"] == True
        
        result = ERK.quick_eval("check: this.value >= 10", context)
        assert result["ok"] == True
        
        result = ERK.quick_eval("check: this.value < 20", context)
        assert result["ok"] == True
    
    def test_deny_inverts_result(self):
        """Vérifie que deny inverse le résultat."""
        context = {"this": {"blocked": True}}
        result = ERK.quick_eval("deny: this.blocked", context)
        # deny: true -> ok: false (la condition de refus est satisfaite)
        assert result["ok"] == False
        
        context = {"this": {"blocked": False}}
        result = ERK.quick_eval("deny: this.blocked", context)
        # deny: false -> ok: true (pas de refus)
        assert result["ok"] == True
    
    def test_undefined_reference(self):
        """Gère une référence indéfinie."""
        context = {"this": {}}
        result = ERK.quick_eval("check: this.missing == true", context)
        # Devrait retourner une erreur
        assert result.get("error") or result["ok"] == False
    
    def test_hasFlag_method(self):
        """Évalue la méthode hasFlag."""
        context = {"this": {"flags": ["admin", "verified"]}}
        result = ERK.quick_eval("check: this.hasFlag('admin')", context)
        assert result["ok"] == True


# ============================================================================
# TESTS CONSOLE
# ============================================================================

class TestConsole:
    """Tests de l'intégration console."""
    
    def test_eval_existing_rule(self, console):
        """Évalue une règle existante."""
        result = console.eval("agent_001", "can_prompt")
        assert result["ok"] == True
        assert result["action"] == "enable"
    
    def test_eval_with_context(self, console):
        """Évalue avec un contexte additionnel."""
        result = console.eval("agent_001", "can_execute")
        assert result["ok"] == True
    
    def test_eval_suspended_agent(self, console):
        """Évalue un agent suspendu."""
        result = console.eval("agent_002", "can_execute")
        assert result["ok"] == False
    
    def test_eval_missing_object(self, console):
        """Gère un objet manquant."""
        result = console.eval("nonexistent", "rule")
        assert result["ok"] == False
        assert "not found" in result["reason"].lower()
    
    def test_eval_missing_rule(self, console):
        """Gère une règle manquante."""
        result = console.eval("agent_001", "nonexistent_rule")
        assert result["ok"] == False
        assert "not found" in result["reason"].lower()
    
    def test_list_rules(self, console):
        """Liste les règles d'un objet."""
        result = console.list_rules("agent_001")
        assert result["count"] == 4
        assert "can_prompt" in result["rules"]
    
    def test_eval_all(self, console):
        """Évalue toutes les règles."""
        result = console.eval_all("agent_001")
        assert result["summary"]["total"] == 4
        assert result["summary"]["passed"] >= 3
    
    def test_validate_valid_rule(self, console):
        """Valide une règle correcte."""
        result = console.validate("enable: this.active == true")
        assert result["valid"] == True
    
    def test_validate_invalid_rule(self, console):
        """Valide une règle incorrecte."""
        result = console.validate("enable:")
        assert result["valid"] == False
    
    def test_parse_returns_ast(self, console):
        """Parse retourne l'AST."""
        result = console.parse("check: this.value > 10")
        assert result["ok"] == True
        assert "ast" in result


# ============================================================================
# TESTS EXEMPLES DE RÈGLES ERK
# ============================================================================

class TestERKExamples:
    """Tests des exemples de règles ERK documentées."""
    
    def test_flag_check(self):
        """enable: this.flags.contains('prompt_enabled')"""
        context = {"this": {"flags": ["prompt_enabled", "active"]}}
        result = ERK.quick_eval("enable: this.flags.contains('prompt_enabled')", context)
        assert result["ok"] == True
    
    def test_type_and_priority(self):
        """allow: this.type == 'Agent' AND this.priority == 'natural'"""
        context = {"this": {"type": "Agent", "priority": "natural"}}
        result = ERK.quick_eval(
            "allow: this.type == 'Agent' AND this.priority == 'natural'",
            context
        )
        assert result["ok"] == True
    
    def test_credit_check(self):
        """deny: this.credits <= 0"""
        context = {"this": {"credits": 0}}
        result = ERK.quick_eval("deny: this.credits <= 0", context)
        assert result["ok"] == False  # deny condition met -> not ok
        
        context = {"this": {"credits": 100}}
        result = ERK.quick_eval("deny: this.credits <= 0", context)
        assert result["ok"] == True  # deny condition not met -> ok
    
    def test_config_validation(self):
        """require: this.config.has('api_key') AND this.config.api_key.isNotEmpty()"""
        context = {"this": {"config": {"api_key": "sk-xxx"}}}
        result = ERK.quick_eval(
            "require: this.config.has('api_key') AND this.config.api_key.isNotEmpty()",
            context
        )
        assert result["ok"] == True
    
    def test_suspended_or_no_credits(self):
        """deny: this.status == 'suspended' OR this.credits <= 0"""
        # Case 1: suspended
        context = {"this": {"status": "suspended", "credits": 100}}
        result = ERK.quick_eval(
            "deny: this.status == 'suspended' OR this.credits <= 0",
            context
        )
        assert result["ok"] == False
        
        # Case 2: no credits
        context = {"this": {"status": "active", "credits": 0}}
        result = ERK.quick_eval(
            "deny: this.status == 'suspended' OR this.credits <= 0",
            context
        )
        assert result["ok"] == False
        
        # Case 3: all good
        context = {"this": {"status": "active", "credits": 100}}
        result = ERK.quick_eval(
            "deny: this.status == 'suspended' OR this.credits <= 0",
            context
        )
        assert result["ok"] == True
    
    def test_complex_authorization(self):
        """allow: (this.role == 'admin' OR this.permissions.contains('write')) AND this.verified == true"""
        # Admin verified
        context = {"this": {"role": "admin", "permissions": [], "verified": True}}
        result = ERK.quick_eval(
            "allow: (this.role == 'admin' OR this.permissions.contains('write')) AND this.verified == true",
            context
        )
        assert result["ok"] == True
        
        # Has write permission, verified
        context = {"this": {"role": "user", "permissions": ["write", "read"], "verified": True}}
        result = ERK.quick_eval(
            "allow: (this.role == 'admin' OR this.permissions.contains('write')) AND this.verified == true",
            context
        )
        assert result["ok"] == True
        
        # Not verified
        context = {"this": {"role": "admin", "permissions": [], "verified": False}}
        result = ERK.quick_eval(
            "allow: (this.role == 'admin' OR this.permissions.contains('write')) AND this.verified == true",
            context
        )
        assert result["ok"] == False


# ============================================================================
# TESTS DE ROBUSTESSE
# ============================================================================

class TestRobustness:
    """Tests de robustesse et cas limites."""
    
    def test_empty_string_comparison(self):
        """Compare avec une chaîne vide."""
        context = {"this": {"name": ""}}
        result = ERK.quick_eval("check: this.name == ''", context)
        assert result["ok"] == True
    
    def test_null_handling(self):
        """Gère les valeurs null."""
        context = {"this": {"value": None}}
        result = ERK.quick_eval("check: this.value == null", context)
        assert result["ok"] == True
    
    def test_deep_nesting(self):
        """Accès profondément imbriqué."""
        context = {"this": {"a": {"b": {"c": {"d": 42}}}}}
        result = ERK.quick_eval("check: this.a.b.c.d == 42", context)
        assert result["ok"] == True
    
    def test_special_characters_in_string(self):
        """Chaînes avec caractères spéciaux."""
        context = {"this": {"msg": "Hello\nWorld"}}
        result = ERK.quick_eval('check: this.msg.contains("Hello")', context)
        assert result["ok"] == True
    
    def test_zero_is_falsy_for_boolean(self):
        """Zero est falsy en contexte booléen."""
        context = {"this": {"count": 0}}
        result = ERK.quick_eval("check: this.count", context)
        assert result["ok"] == False
    
    def test_empty_list_is_falsy(self):
        """Liste vide est falsy."""
        context = {"this": {"items": []}}
        result = ERK.quick_eval("check: this.items", context)
        assert result["ok"] == False
    
    def test_short_circuit_and(self):
        """Short-circuit sur AND."""
        # Si le premier est false, le second n'est pas évalué
        context = {"this": {"a": False}}
        result = ERK.quick_eval("check: this.a AND this.missing.path", context)
        assert result["ok"] == False  # Pas d'erreur sur missing.path
    
    def test_short_circuit_or(self):
        """Short-circuit sur OR."""
        # Si le premier est true, le second n'est pas évalué
        context = {"this": {"a": True}}
        result = ERK.quick_eval("check: this.a OR this.missing.path", context)
        assert result["ok"] == True  # Pas d'erreur sur missing.path


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
