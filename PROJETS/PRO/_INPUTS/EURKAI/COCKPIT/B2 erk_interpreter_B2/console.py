"""
ERK Console Integration - Interface console pour l'interpréteur ERK.

Fournit l'API ERK.eval() et ERK.parse() pour la console du Cockpit.
"""

from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field

from .parser import parse, parse_expression
from .evaluator import evaluate, evaluate_rule, EvalResult, EvalContext
from .ast_nodes import RuleNode
from .errors import ERKError


@dataclass
class StoreAdapter:
    """
    Adaptateur pour le store du Cockpit.
    
    Permet de récupérer les objets et leurs règles depuis le store JSON.
    Cette classe doit être sous-classée ou configurée avec le store réel.
    """
    
    objects: Dict[str, dict] = field(default_factory=dict)
    lineages: Dict[str, list] = field(default_factory=dict)
    rules: Dict[str, Dict[str, str]] = field(default_factory=dict)  # {object_id: {rule_name: rule_text}}
    
    def get_object(self, object_id: str) -> Optional[dict]:
        """Récupère un objet par ID."""
        return self.objects.get(object_id)
    
    def get_rule(self, object_id: str, rule_name: str) -> Optional[str]:
        """Récupère le texte d'une règle."""
        obj_rules = self.rules.get(object_id, {})
        return obj_rules.get(rule_name)
    
    def get_all_rules(self, object_id: str) -> Dict[str, str]:
        """Récupère toutes les règles d'un objet."""
        return self.rules.get(object_id, {})
    
    def list_objects(self) -> list:
        """Liste tous les IDs d'objets."""
        return list(self.objects.keys())
    
    def get_lineage(self, lineage_name: str) -> list:
        """Récupère un lineage par nom."""
        return self.lineages.get(lineage_name, [])


class ERKConsole:
    """
    Interface console pour l'interpréteur ERK.
    
    Usage:
        ERK = ERKConsole(store)
        result = ERK.eval("agent_001", "can_execute")
        result = ERK.eval("agent_001", "can_execute", {"user_role": "admin"})
    """
    
    def __init__(self, store: StoreAdapter = None):
        self.store = store or StoreAdapter()
        self._cache = {}  # Cache des règles parsées
    
    def eval(
        self, 
        object_id: str, 
        rule_name: str, 
        context: Optional[dict] = None
    ) -> dict:
        """
        Évalue une règle ERK sur un objet.
        
        Args:
            object_id: ID de l'objet
            rule_name: Nom de la règle à évaluer
            context: Contexte additionnel (optionnel)
        
        Returns:
            dict avec {ok, rule, action, value, reason, details}
        """
        try:
            # Récupérer l'objet
            obj = self.store.get_object(object_id)
            if obj is None:
                return {
                    "ok": False,
                    "rule": rule_name,
                    "action": "unknown",
                    "reason": f"Object '{object_id}' not found",
                    "error": True
                }
            
            # Récupérer la règle
            rule_text = self.store.get_rule(object_id, rule_name)
            if rule_text is None:
                return {
                    "ok": False,
                    "rule": rule_name,
                    "action": "unknown",
                    "reason": f"Rule '{rule_name}' not found on object '{object_id}'",
                    "error": True
                }
            
            # Parser (avec cache)
            cache_key = f"{object_id}:{rule_name}"
            if cache_key not in self._cache:
                self._cache[cache_key] = parse(rule_text)
            
            rule_ast = self._cache[cache_key]
            
            # Construire le contexte d'évaluation
            eval_context = {
                "this": obj,
                "objects": self.store.objects,
                "lineages": self.store.lineages,
                "globals": context or {}
            }
            
            # Évaluer
            result = evaluate_rule(rule_ast, eval_context, rule_name)
            return result.to_dict()
        
        except ERKError as e:
            return e.to_dict()
        
        except Exception as e:
            return {
                "ok": False,
                "rule": rule_name,
                "action": "unknown",
                "reason": f"Unexpected error: {str(e)}",
                "error": True,
                "details": {"exception": type(e).__name__}
            }
    
    def parse(self, rule_text: str) -> dict:
        """
        Parse une règle et retourne l'AST (pour debug).
        
        Args:
            rule_text: Texte de la règle ERK
        
        Returns:
            dict représentant l'AST
        """
        try:
            ast = parse(rule_text)
            return {
                "ok": True,
                "ast": self._ast_to_dict(ast)
            }
        except ERKError as e:
            return e.to_dict()
    
    def validate(self, rule_text: str) -> dict:
        """
        Valide une règle sans l'évaluer.
        
        Args:
            rule_text: Texte de la règle ERK
        
        Returns:
            dict avec {valid: bool, error?: str}
        """
        try:
            parse(rule_text)
            return {"valid": True}
        except ERKError as e:
            return {"valid": False, "error": str(e)}
    
    def list_rules(self, object_id: str) -> dict:
        """Liste toutes les règles d'un objet."""
        rules = self.store.get_all_rules(object_id)
        return {
            "object_id": object_id,
            "rules": list(rules.keys()),
            "count": len(rules)
        }
    
    def eval_all(self, object_id: str, context: Optional[dict] = None) -> dict:
        """Évalue toutes les règles d'un objet."""
        rules = self.store.get_all_rules(object_id)
        results = {}
        
        for rule_name in rules:
            results[rule_name] = self.eval(object_id, rule_name, context)
        
        return {
            "object_id": object_id,
            "results": results,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results.values() if r.get("ok")),
                "failed": sum(1 for r in results.values() if not r.get("ok"))
            }
        }
    
    def clear_cache(self):
        """Vide le cache des règles parsées."""
        self._cache.clear()
    
    def _ast_to_dict(self, node) -> dict:
        """Convertit un nœud AST en dictionnaire."""
        if hasattr(node, '__dataclass_fields__'):
            result = {"type": node.node_type.name}
            for field_name in node.__dataclass_fields__:
                value = getattr(node, field_name)
                if field_name == 'node_type':
                    continue
                if hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self._ast_to_dict(value)
                elif isinstance(value, list):
                    result[field_name] = [
                        self._ast_to_dict(v) if hasattr(v, '__dataclass_fields__') else v
                        for v in value
                    ]
                else:
                    result[field_name] = value
            return result
        return str(node)


# Instance globale pour usage en console
_console_instance = None


def get_console(store: StoreAdapter = None) -> ERKConsole:
    """Obtient l'instance console (singleton pattern)."""
    global _console_instance
    if _console_instance is None or store is not None:
        _console_instance = ERKConsole(store)
    return _console_instance
