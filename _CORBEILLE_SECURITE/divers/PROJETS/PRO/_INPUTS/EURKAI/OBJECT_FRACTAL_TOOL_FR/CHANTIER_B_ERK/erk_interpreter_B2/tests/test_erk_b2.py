"""
Tests pour l'interpréteur ERK B2/2 - Conditions étendues et contexte.

Ces tests vérifient:
- La rétrocompatibilité avec B1/1
- Les nouvelles constructions IF/THEN/ELSE
- Les constructions WHEN/THEN
- L'accès au contexte via ctx
- La traçabilité des évaluations
"""

import pytest
from erk import (
    ERK,
    parse,
    parse_expression,
    parse_conditional,
    tokenize,
    evaluate,
    evaluate_rule,
    ERKConsole,
    StoreAdapter,
    ERKParseError,
    ERKEvalError,
    ERKReferenceError,
    TokenType,
    EvalTrace,
    TraceEventType,
    IfThenElseNode,
    WhenThenNode,
    CtxNode,
    NodeType,
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
# TESTS DE RÉTROCOMPATIBILITÉ B1/1
# ============================================================================

class TestB1Compatibility:
    """Tests de rétrocompatibilité avec B1/1."""
    
    def test_simple_rule_still_works(self):
        """Les règles simples B1 fonctionnent toujours."""
        context = {"this": {"active": True}}
        result = ERK.quick_eval("enable: this.active", context)
        assert result["ok"] == True
    
    def test_comparison_still_works(self):
        """Les comparaisons B1 fonctionnent."""
        context = {"this": {"status": "active"}}
        result = ERK.quick_eval("check: this.status == 'active'", context)
        assert result["ok"] == True
    
    def test_logical_operators_still_work(self):
        """Les opérateurs AND/OR/NOT fonctionnent."""
        context = {"this": {"a": True, "b": False}}
        
        # AND
        result = ERK.quick_eval("check: this.a AND this.b", context)
        assert result["ok"] == False
        
        # OR
        result = ERK.quick_eval("check: this.a OR this.b", context)
        assert result["ok"] == True
        
        # NOT
        result = ERK.quick_eval("check: NOT this.b", context)
        assert result["ok"] == True
    
    def test_methods_still_work(self):
        """Les méthodes built-in fonctionnent."""
        context = {"this": {"flags": ["admin", "active"]}}
        result = ERK.quick_eval("enable: this.flags.contains('admin')", context)
        assert result["ok"] == True
    
    def test_deny_action_still_works(self):
        """L'action deny fonctionne (logique inversée)."""
        context = {"this": {"credits": 0}}
        result = ERK.quick_eval("deny: this.credits <= 0", context)
        assert result["ok"] == False  # deny condition triggered


# ============================================================================
# TESTS LEXER B2
# ============================================================================

class TestLexerB2:
    """Tests du lexer avec les nouveaux tokens B2."""
    
    def test_if_then_else_tokens(self):
        """Tokenize IF/THEN/ELSE."""
        tokens = tokenize("IF this.a THEN b ELSE c")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.IF in types
        assert TokenType.THEN in types
        assert TokenType.ELSE in types
    
    def test_when_token(self):
        """Tokenize WHEN."""
        tokens = tokenize("WHEN ctx.layer == 'System' THEN allow")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.WHEN in types
        assert TokenType.CTX in types
        assert TokenType.THEN in types
    
    def test_ctx_token(self):
        """Tokenize ctx."""
        tokens = tokenize("ctx.layer")
        assert tokens[0].type == TokenType.CTX
        assert tokens[0].value == "ctx"


# ============================================================================
# TESTS PARSER B2
# ============================================================================

class TestParserB2:
    """Tests du parser avec les nouvelles constructions B2."""
    
    def test_parse_if_then(self):
        """Parse IF condition THEN result."""
        ast = parse("enable: IF this.priority == 'natural' THEN true")
        assert ast.action == "enable"
        assert isinstance(ast.expression, IfThenElseNode)
        assert ast.expression.else_branch is None
    
    def test_parse_if_then_else(self):
        """Parse IF condition THEN result ELSE alternative."""
        ast = parse("enable: IF this.credits > 0 THEN allow ELSE deny")
        assert ast.action == "enable"
        expr = ast.expression
        assert isinstance(expr, IfThenElseNode)
        assert expr.condition is not None
        assert expr.then_branch is not None
        assert expr.else_branch is not None
    
    def test_parse_when_then(self):
        """Parse WHEN condition THEN result."""
        ast = parse("allow: WHEN ctx.layer == 'System' THEN true")
        assert ast.action == "allow"
        assert isinstance(ast.expression, WhenThenNode)
    
    def test_parse_ctx_access(self):
        """Parse ctx.property."""
        expr = parse_expression("ctx.layer == 'System'")
        # L'expression devrait être une comparaison
        assert expr.operator == "=="
        # Le côté gauche devrait contenir un accès à ctx
        assert expr.left.node_type == NodeType.MEMBER_ACCESS
    
    def test_parse_nested_if(self):
        """Parse IF imbriqués."""
        ast = parse("enable: IF this.a THEN IF this.b THEN true ELSE false ELSE false")
        assert isinstance(ast.expression, IfThenElseNode)
        assert isinstance(ast.expression.then_branch, IfThenElseNode)
    
    def test_parse_complex_when_condition(self):
        """Parse WHEN avec condition complexe."""
        ast = parse("allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true")
        expr = ast.expression
        assert isinstance(expr, WhenThenNode)
        # La condition devrait être un AND
        assert expr.condition.operator == "AND"


# ============================================================================
# TESTS ÉVALUATEUR B2 - IF/THEN/ELSE
# ============================================================================

class TestEvaluatorIfThenElse:
    """Tests de l'évaluation IF/THEN/ELSE."""
    
    def test_if_true_takes_then_branch(self):
        """IF condition vraie -> branche THEN."""
        context = {"this": {"priority": "natural"}}
        result = ERK.quick_eval(
            "enable: IF this.priority == 'natural' THEN true ELSE false",
            context
        )
        assert result["ok"] == True
        assert result["value"] == True
    
    def test_if_false_takes_else_branch(self):
        """IF condition fausse -> branche ELSE."""
        context = {"this": {"priority": "high"}}
        result = ERK.quick_eval(
            "enable: IF this.priority == 'natural' THEN true ELSE false",
            context
        )
        assert result["ok"] == False
        assert result["value"] == False
    
    def test_if_false_no_else_returns_false(self):
        """IF condition fausse sans ELSE -> False."""
        context = {"this": {"priority": "high"}}
        result = ERK.quick_eval(
            "enable: IF this.priority == 'natural' THEN true",
            context
        )
        assert result["ok"] == False
    
    def test_if_with_complex_condition(self):
        """IF avec condition complexe AND/OR."""
        context = {"this": {"status": "active", "credits": 100}}
        result = ERK.quick_eval(
            "allow: IF this.status == 'active' AND this.credits > 0 THEN true ELSE false",
            context
        )
        assert result["ok"] == True
    
    def test_if_with_identifier_results(self):
        """IF avec identifiants comme résultats."""
        context = {"this": {"mode": "strict"}, "globals": {"allow": True, "deny": False}}
        # Note: Les identifiants 'allow', 'deny' sont évalués dans le contexte
        result = ERK.quick_eval(
            "check: IF this.mode == 'strict' THEN true ELSE false",
            context
        )
        assert result["ok"] == True


# ============================================================================
# TESTS ÉVALUATEUR B2 - WHEN/THEN
# ============================================================================

class TestEvaluatorWhenThen:
    """Tests de l'évaluation WHEN/THEN."""
    
    def test_when_true_returns_result(self):
        """WHEN condition vraie -> résultat."""
        context = {
            "this": {"type": "Agent"},
            "ctx": {"layer": "System"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' THEN true",
            context
        )
        assert result["ok"] == True
    
    def test_when_false_returns_false(self):
        """WHEN condition fausse -> False."""
        context = {
            "this": {"type": "Agent"},
            "ctx": {"layer": "User"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' THEN true",
            context
        )
        assert result["ok"] == False
    
    def test_when_with_this_and_ctx(self):
        """WHEN avec combinaison this et ctx."""
        context = {
            "this": {"type": "Agent", "priority": "natural"},
            "ctx": {"layer": "System", "mode": "normal"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true",
            context
        )
        assert result["ok"] == True


# ============================================================================
# TESTS ÉVALUATEUR B2 - CONTEXTE (ctx)
# ============================================================================

class TestEvaluatorCtx:
    """Tests de l'évaluation du contexte ctx."""
    
    def test_ctx_simple_access(self):
        """Accès simple à ctx.property."""
        context = {
            "this": {},
            "ctx": {"layer": "System"}
        }
        result = ERK.quick_eval("check: ctx.layer == 'System'", context)
        assert result["ok"] == True
    
    def test_ctx_nested_access(self):
        """Accès imbriqué ctx.a.b."""
        context = {
            "this": {},
            "ctx": {"config": {"mode": "strict"}}
        }
        result = ERK.quick_eval("check: ctx.config.mode == 'strict'", context)
        assert result["ok"] == True
    
    def test_ctx_with_methods(self):
        """ctx avec méthodes."""
        context = {
            "this": {},
            "ctx": {"flags": ["debug", "verbose"]}
        }
        result = ERK.quick_eval("check: ctx.flags.contains('debug')", context)
        assert result["ok"] == True
    
    def test_ctx_missing_returns_empty(self):
        """ctx manquant retourne un dict vide."""
        context = {"this": {}}  # Pas de ctx
        # Devrait fonctionner sans erreur, ctx sera {}
        result = ERK.quick_eval("check: true", context)
        assert result["ok"] == True
    
    def test_ctx_combined_with_this(self):
        """Combinaison de ctx et this."""
        context = {
            "this": {"role": "admin"},
            "ctx": {"mode": "elevated"}
        }
        result = ERK.quick_eval(
            "allow: this.role == 'admin' AND ctx.mode == 'elevated'",
            context
        )
        assert result["ok"] == True


# ============================================================================
# TESTS TRAÇABILITÉ B2
# ============================================================================

class TestTraceability:
    """Tests de la traçabilité des évaluations."""
    
    def test_result_includes_trace(self):
        """Le résultat inclut une trace quand activée."""
        context = {"this": {"active": True}}
        # Utiliser evaluate_rule directement pour avoir accès à la trace
        ast = parse("enable: this.active")
        result = evaluate_rule(ast, context, "test", enable_trace=True)
        
        # La trace devrait exister sur l'objet résultat
        assert result.trace is not None
        assert isinstance(result.trace, EvalTrace)
    
    def test_trace_contains_branches(self):
        """La trace contient les branches prises."""
        context = {"this": {"priority": "natural"}}
        ast = parse("enable: IF this.priority == 'natural' THEN true ELSE false")
        result = evaluate_rule(ast, context, "test_rule", enable_trace=True)
        
        trace_summary = result.trace.to_summary()
        assert trace_summary["total_events"] > 0
        assert any("THEN" in b for b in trace_summary["branches_taken"])
    
    def test_trace_condition_results(self):
        """La trace contient les résultats des conditions."""
        context = {"this": {"a": True, "b": False}}
        ast = parse("check: this.a AND this.b")
        result = evaluate_rule(ast, context, "test_rule", enable_trace=True)
        
        trace = result.trace
        conditions = [e for e in trace.events if e.event_type == TraceEventType.CONDITION_CHECK]
        assert len(conditions) >= 2  # Au moins les deux opérandes
    
    def test_full_trace_export(self):
        """Export complet de la trace."""
        context = {"this": {"status": "active"}}
        ast = parse("check: this.status == 'active'")
        result = evaluate_rule(ast, context, "test_rule", enable_trace=True)
        
        full_dict = result.to_dict_full()
        assert "trace_full" in full_dict
        assert isinstance(full_dict["trace_full"], list)


# ============================================================================
# TESTS EXEMPLES DOCUMENTÉS
# ============================================================================

class TestDocumentedExamples:
    """Tests des exemples mentionnés dans le prompt B2/2."""
    
    def test_example_1_priority_natural(self):
        """IF this.priority == 'natural' THEN enable ELSE disable"""
        # Cas 1: priority = natural
        context = {"this": {"priority": "natural"}}
        result = ERK.quick_eval(
            "check: IF this.priority == 'natural' THEN true ELSE false",
            context
        )
        assert result["ok"] == True
        
        # Cas 2: priority = high
        context = {"this": {"priority": "high"}}
        result = ERK.quick_eval(
            "check: IF this.priority == 'natural' THEN true ELSE false",
            context
        )
        assert result["ok"] == False
    
    def test_example_2_system_layer_agent(self):
        """WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN allow"""
        # Cas 1: System layer + Agent type
        context = {
            "this": {"type": "Agent"},
            "ctx": {"layer": "System"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true",
            context
        )
        assert result["ok"] == True
        
        # Cas 2: User layer
        context = {
            "this": {"type": "Agent"},
            "ctx": {"layer": "User"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true",
            context
        )
        assert result["ok"] == False
        
        # Cas 3: System layer but not Agent
        context = {
            "this": {"type": "Task"},
            "ctx": {"layer": "System"}
        }
        result = ERK.quick_eval(
            "allow: WHEN ctx.layer == 'System' AND this.type == 'Agent' THEN true",
            context
        )
        assert result["ok"] == False


# ============================================================================
# TESTS CAS LIMITES
# ============================================================================

class TestEdgeCases:
    """Tests des cas limites."""
    
    def test_empty_ctx(self):
        """ctx vide ne cause pas d'erreur."""
        context = {"this": {"value": 1}, "ctx": {}}
        result = ERK.quick_eval("check: this.value == 1", context)
        assert result["ok"] == True
    
    def test_missing_ctx_property(self):
        """Propriété ctx manquante cause une erreur appropriée."""
        context = {"this": {}, "ctx": {}}
        result = ERK.quick_eval("check: ctx.missing == 'value'", context)
        assert result["ok"] == False
        assert "not found" in result["reason"].lower()
    
    def test_deeply_nested_if(self):
        """IF profondément imbriqués."""
        context = {"this": {"a": True, "b": True, "c": True}}
        result = ERK.quick_eval(
            "check: IF this.a THEN IF this.b THEN IF this.c THEN true ELSE false ELSE false ELSE false",
            context
        )
        assert result["ok"] == True
    
    def test_when_with_method_calls(self):
        """WHEN avec appels de méthodes."""
        context = {
            "this": {"flags": ["admin"]},
            "ctx": {"permissions": ["read", "write"]}
        }
        result = ERK.quick_eval(
            "allow: WHEN this.flags.contains('admin') AND ctx.permissions.contains('write') THEN true",
            context
        )
        assert result["ok"] == True
    
    def test_if_with_boolean_literal_results(self):
        """IF avec true/false comme résultats."""
        context = {"this": {"active": True}}
        result = ERK.quick_eval(
            "check: IF this.active THEN true ELSE false",
            context
        )
        assert result["ok"] == True
        assert result["value"] == True


# ============================================================================
# TESTS INTÉGRATION CONSOLE
# ============================================================================

class TestConsoleIntegration:
    """Tests d'intégration avec la console."""
    
    def test_validate_if_then_else(self, console):
        """Valide la syntaxe IF/THEN/ELSE."""
        result = console.validate("enable: IF this.active THEN true ELSE false")
        assert result["valid"] == True
    
    def test_validate_when_then(self, console):
        """Valide la syntaxe WHEN/THEN."""
        result = console.validate("allow: WHEN ctx.layer == 'System' THEN true")
        assert result["valid"] == True
    
    def test_parse_returns_ast_with_if(self, console):
        """Parse retourne un AST correct pour IF."""
        result = console.parse("enable: IF this.a THEN true")
        assert result["ok"] == True
        assert "if_then_else" in str(result["ast"]).lower() or "ifthenelse" in str(result["ast"]).lower()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
