#!/usr/bin/env python3
"""
ERK Interpreter - Démonstration Interactive

Ce script démontre les capacités de l'interpréteur ERK minimal.
Il peut être utilisé comme référence pour l'intégration avec le Cockpit.
"""

from erk import ERK, ERKConsole, StoreAdapter


def create_demo_store() -> StoreAdapter:
    """Crée un store de démonstration avec des objets et règles réalistes."""
    store = StoreAdapter()
    
    # === OBJETS ===
    store.objects = {
        # Agent principal actif
        "agent_claude": {
            "id": "agent_claude",
            "type": "Agent",
            "priority": "natural",
            "status": "active",
            "flags": ["prompt_enabled", "can_execute", "verified"],
            "config": {
                "api_key": "sk-ant-xxxxx",
                "max_tokens": 4096,
                "temperature": 0.7
            },
            "credits": 1000,
            "role": "assistant"
        },
        
        # Agent suspendu
        "agent_suspended": {
            "id": "agent_suspended",
            "type": "Agent",
            "priority": "low",
            "status": "suspended",
            "flags": [],
            "config": {},
            "credits": 0,
            "role": "worker"
        },
        
        # Tâche en attente
        "task_analysis": {
            "id": "task_analysis",
            "type": "Task",
            "owner": "agent_claude",
            "status": "pending",
            "priority": 8,
            "requires": ["data_access", "compute"]
        },
        
        # Prompt template
        "prompt_greeting": {
            "id": "prompt_greeting",
            "type": "Prompt",
            "category": "interaction",
            "flags": ["public", "cached"],
            "version": "1.0"
        }
    }
    
    # === LINEAGES ===
    store.lineages = {
        "active_agents": ["agent_claude"],
        "all_agents": ["agent_claude", "agent_suspended"],
        "pending_tasks": ["task_analysis"]
    }
    
    # === RÈGLES ERK ===
    store.rules = {
        "agent_claude": {
            # Vérifie si le prompt est activé
            "can_prompt": "enable: this.flags.contains('prompt_enabled')",
            
            # Vérifie si l'agent peut exécuter (actif + crédits)
            "can_execute": "allow: this.status == 'active' AND this.credits > 0",
            
            # Vérifie la priorité naturelle
            "is_natural_priority": "check: this.priority == 'natural'",
            
            # Vérifie la configuration API
            "has_valid_config": "require: this.config.has('api_key') AND this.config.api_key.isNotEmpty()",
            
            # Règle complexe multi-conditions
            "full_access": "allow: this.flags.contains('verified') AND this.status == 'active' AND this.role == 'assistant'"
        },
        
        "agent_suspended": {
            # L'agent suspendu ne peut pas exécuter
            "can_execute": "allow: this.status == 'active' AND this.credits > 0",
            
            # Vérifie si la suspension est active
            "is_suspended": "check: this.status == 'suspended'",
            
            # Refus si suspendu ou sans crédits
            "deny_access": "deny: this.status == 'suspended' OR this.credits <= 0"
        },
        
        "task_analysis": {
            # Vérifie si la tâche peut démarrer
            "can_start": "enable: this.status == 'pending' AND this.priority >= 5",
            
            # Vérifie les prérequis
            "has_requirements": "require: this.requires.isNotEmpty()"
        },
        
        "prompt_greeting": {
            # Vérifie si le prompt est public
            "is_public": "check: this.flags.contains('public')",
            
            # Vérifie si le cache est activé
            "use_cache": "enable: this.flags.contains('cached')"
        }
    }
    
    return store


def demo_basic_evaluation():
    """Démontre l'évaluation basique de règles."""
    print("=" * 60)
    print("1. ÉVALUATION BASIQUE")
    print("=" * 60)
    
    store = create_demo_store()
    console = ERKConsole(store)
    
    # Test 1: Agent actif
    print("\n▶ Évaluation: agent_claude.can_prompt")
    result = console.eval("agent_claude", "can_prompt")
    print(f"  Règle: enable: this.flags.contains('prompt_enabled')")
    print(f"  Résultat: {result}")
    
    # Test 2: Agent suspendu
    print("\n▶ Évaluation: agent_suspended.can_execute")
    result = console.eval("agent_suspended", "can_execute")
    print(f"  Règle: allow: this.status == 'active' AND this.credits > 0")
    print(f"  Résultat: {result}")
    
    # Test 3: Tâche
    print("\n▶ Évaluation: task_analysis.can_start")
    result = console.eval("task_analysis", "can_start")
    print(f"  Règle: enable: this.status == 'pending' AND this.priority >= 5")
    print(f"  Résultat: {result}")


def demo_quick_eval():
    """Démontre l'évaluation rapide sans store."""
    print("\n" + "=" * 60)
    print("2. ÉVALUATION RAPIDE (sans store)")
    print("=" * 60)
    
    # Contexte inline
    context = {
        "this": {
            "user": "alice",
            "role": "admin",
            "permissions": ["read", "write", "delete"],
            "verified": True,
            "login_attempts": 2
        }
    }
    
    rules = [
        ("Vérifie admin", "check: this.role == 'admin'"),
        ("Vérifie écriture", "allow: this.permissions.contains('write')"),
        ("Vérifie vérifié", "require: this.verified == true"),
        ("Vérifie tentatives", "deny: this.login_attempts > 5"),
        ("Accès complet", "allow: (this.role == 'admin' OR this.permissions.contains('delete')) AND this.verified")
    ]
    
    for name, rule in rules:
        result = ERK.quick_eval(rule, context)
        status = "✓" if result["ok"] else "✗"
        print(f"\n▶ {name}")
        print(f"  Règle: {rule}")
        print(f"  {status} ok={result['ok']}, raison: {result['reason']}")


def demo_error_handling():
    """Démontre la gestion des erreurs."""
    print("\n" + "=" * 60)
    print("3. GESTION DES ERREURS")
    print("=" * 60)
    
    # Erreur de syntaxe
    print("\n▶ Erreur de syntaxe:")
    result = ERK.validate("enable: this.value ==")
    print(f"  Règle: enable: this.value ==")
    print(f"  Validation: {result}")
    
    # Référence manquante
    print("\n▶ Référence manquante:")
    result = ERK.quick_eval("check: this.missing.property", {"this": {}})
    print(f"  Règle: check: this.missing.property")
    print(f"  Résultat: {result}")
    
    # Objet manquant dans store
    print("\n▶ Objet manquant:")
    store = create_demo_store()
    console = ERKConsole(store)
    result = console.eval("nonexistent_object", "some_rule")
    print(f"  Résultat: {result}")


def demo_all_rules():
    """Démontre l'évaluation de toutes les règles d'un objet."""
    print("\n" + "=" * 60)
    print("4. ÉVALUATION COMPLÈTE D'UN OBJET")
    print("=" * 60)
    
    store = create_demo_store()
    console = ERKConsole(store)
    
    print("\n▶ Toutes les règles de agent_claude:")
    result = console.eval_all("agent_claude")
    
    print(f"\n  Résumé: {result['summary']}")
    print("\n  Détails:")
    for rule_name, rule_result in result["results"].items():
        status = "✓" if rule_result["ok"] else "✗"
        print(f"    {status} {rule_name}: {rule_result['reason']}")


def demo_parse_ast():
    """Démontre le parsing et l'affichage de l'AST."""
    print("\n" + "=" * 60)
    print("5. PARSING ET AST")
    print("=" * 60)
    
    rule = "allow: (this.role == 'admin' OR this.level >= 5) AND this.verified == true"
    print(f"\n▶ Règle: {rule}")
    
    result = ERK.parse(rule)
    print(f"\n  AST: {result['ast']}")


def demo_methods():
    """Démontre les méthodes built-in disponibles."""
    print("\n" + "=" * 60)
    print("6. MÉTHODES BUILT-IN")
    print("=" * 60)
    
    context = {
        "this": {
            "name": "hello world",
            "items": ["a", "b", "c"],
            "config": {"key": "value"},
            "flags": ["active", "premium"],
            "count": 0
        }
    }
    
    methods = [
        ("contains", 'check: this.name.contains("world")'),
        ("startsWith", 'check: this.name.startsWith("hello")'),
        ("endsWith", 'check: this.name.endsWith("world")'),
        ("isEmpty (false)", "check: this.items.isEmpty()"),
        ("isNotEmpty (true)", "check: this.items.isNotEmpty()"),
        ("length", "check: this.items.length() == 3"),
        ("has (key)", 'check: this.config.has("key")'),
        ("has (missing)", 'check: this.config.has("missing")'),
    ]
    
    for name, rule in methods:
        result = ERK.quick_eval(rule, context)
        status = "✓" if result["ok"] else "✗"
        print(f"\n▶ {name}")
        print(f"  Règle: {rule}")
        print(f"  {status} Résultat: {result['value']}")


def main():
    """Point d'entrée principal."""
    print("\n" + "=" * 60)
    print("    ERK INTERPRETER - DÉMONSTRATION")
    print("    Version 1.0.0 - EUREKAI B1/1")
    print("=" * 60)
    
    demo_basic_evaluation()
    demo_quick_eval()
    demo_error_handling()
    demo_all_rules()
    demo_parse_ast()
    demo_methods()
    
    print("\n" + "=" * 60)
    print("    FIN DE LA DÉMONSTRATION")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
