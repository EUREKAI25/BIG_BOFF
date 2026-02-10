#!/usr/bin/env python3
"""
EUREKAI Core - Moteur ERK
Parser + Resolver + Executor GEVR
"""

import re
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ============================================================================
# STORE - Stockage global des objets
# ============================================================================

class Store:
    """Stockage en mémoire de tous les objets"""
    
    def __init__(self):
        self.objects: Dict[str, Dict] = {}  # lineage -> object
        self.vectors: Dict[str, Dict] = {}  # V_name -> definition
        self.rules: List[Dict] = []          # rules triées par priorité
        self.config: Dict[str, Any] = {}     # config résolue
        
    def add(self, lineage: str, obj: Dict) -> None:
        self.objects[lineage] = obj
        # Index vectors
        if lineage.startswith("Object:Vector:"):
            name = obj.get("attributes", {}).get("name", "").strip('"')
            if name:
                self.vectors[name] = obj
        # Index rules
        if ":Rule:" in lineage:
            self.rules.append(obj)
            self.rules.sort(key=lambda r: int(r.get("attributes", {}).get("priority", 50)))
    
    def get(self, lineage: str) -> Optional[Dict]:
        return self.objects.get(lineage)
    
    def exists(self, lineage: str) -> bool:
        return lineage in self.objects
    
    def query(self, pattern: str) -> List[Dict]:
        """Recherche simple par pattern"""
        results = []
        for lineage, obj in self.objects.items():
            if pattern in lineage:
                results.append(obj)
        return results
    
    def get_children(self, lineage: str) -> List[str]:
        """Retourne les enfants directs d'un lineage"""
        prefix = lineage + ":"
        children = []
        for l in self.objects.keys():
            if l.startswith(prefix):
                rest = l[len(prefix):]
                if ":" not in rest:
                    children.append(l)
        return children
    
    def get_ancestors(self, lineage: str) -> List[str]:
        """Retourne les ancêtres d'un lineage"""
        parts = lineage.split(":")
        ancestors = []
        for i in range(1, len(parts)):
            ancestors.append(":".join(parts[:i]))
        return ancestors


# Instance globale
store = Store()


# ============================================================================
# PARSER - Parse les fichiers .gev / .erk
# ============================================================================

class Parser:
    """Parse les fichiers ERK"""
    
    def __init__(self):
        self.current_lineage: Optional[str] = None
        
    def parse_file(self, filepath: str) -> List[Dict]:
        """Parse un fichier ERK et retourne les objets"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content, source=filepath)
    
    def parse(self, content: str, source: str = "memory") -> List[Dict]:
        """Parse du contenu ERK"""
        objects = []
        lines = content.split('\n')
        
        current_obj = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            
            # Lineage declaration: Object:Parent:Child:
            lineage_match = re.match(r'^([A-Z][A-Za-z0-9_]*(?::[A-Z][A-Za-z0-9_]*)*):$', stripped)
            if lineage_match:
                # Save previous object
                if current_obj:
                    objects.append(current_obj)
                    store.add(current_obj["lineage"], current_obj)
                
                lineage = lineage_match.group(1)
                # Auto-prefix Object: if needed
                if not lineage.startswith("Object:") and lineage != "Object":
                    lineage = "Object:" + lineage
                
                self.current_lineage = lineage
                parts = lineage.split(":")
                
                current_obj = {
                    "lineage": lineage,
                    "name": parts[-1],
                    "parent": ":".join(parts[:-1]) if len(parts) > 1 else "",
                    "attributes": {},
                    "relations": [],
                    "source": source,
                    "line": i + 1
                }
                continue
            
            # Attribute: .name = value
            attr_match = re.match(r'^\.([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*(.+)$', stripped)
            if attr_match and current_obj:
                attr_name = attr_match.group(1)
                attr_value = attr_match.group(2).strip()
                current_obj["attributes"][attr_name] = attr_value
                continue
            
            # Relation: Name relation_type Target
            rel_match = re.match(r'^([A-Z][A-Za-z0-9_]*)\s+(depends_on|related_to|inherits_from|IN)\s+(.+)$', stripped)
            if rel_match:
                source_name = rel_match.group(1)
                rel_type = rel_match.group(2)
                target = rel_match.group(3).strip()
                
                # IN est un alias de related_to
                if rel_type == "IN":
                    rel_type = "related_to"
                
                current_obj["relations"].append({
                    "source": source_name,
                    "type": rel_type,
                    "target": target
                })
                continue
        
        # Save last object
        if current_obj:
            objects.append(current_obj)
            store.add(current_obj["lineage"], current_obj)
        
        return objects


# ============================================================================
# RESOLVER - Résout les vecteurs V_xxx vers valeurs
# ============================================================================

class Resolver:
    """Résout les vecteurs et expressions"""
    
    def __init__(self, store: Store):
        self.store = store
        self.cache: Dict[str, Any] = {}
    
    def resolve(self, value: str, context: Dict = None) -> Any:
        """Résout une valeur (vecteur, expression, ou littéral)"""
        if context is None:
            context = {}
        
        # Déjà en cache?
        cache_key = f"{value}:{json.dumps(context, sort_keys=True, default=str)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self._resolve_internal(value, context)
        self.cache[cache_key] = result
        return result
    
    def _resolve_internal(self, value: str, context: Dict) -> Any:
        """Résolution interne"""
        
        # String littéral
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        
        # Nombre
        if re.match(r'^-?\d+(\.\d+)?$', value):
            return float(value) if '.' in value else int(value)
        
        # Booléen
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        
        # Null
        if value.lower() in ("null", "nil"):
            return None
        
        # Vecteur V_xxx
        if value.startswith("V_"):
            return self._resolve_vector(value, context)
        
        # Variable de date
        if value.startswith("$"):
            return self._resolve_date(value)
        
        # Expression conditionnelle {cond?a:b}
        if value.startswith("{") and value.endswith("}"):
            return self._resolve_expression(value[1:-1], context)
        
        # Enum/liste
        if "," in value and not value.startswith("read "):
            return [v.strip() for v in value.split(",")]
        
        # SuperRead query
        if value.startswith("read "):
            return self._resolve_query(value, context)
        
        # Identifiant simple (retourne tel quel)
        return value
    
    def _resolve_vector(self, name: str, context: Dict) -> Any:
        """Résout un vecteur V_xxx"""
        vector_def = self.store.vectors.get(name)
        
        if not vector_def:
            # Chercher dans config
            for lineage, obj in self.store.objects.items():
                if ":Config:" in lineage:
                    attrs = obj.get("attributes", {})
                    if name in attrs:
                        return self.resolve(attrs[name], context)
            return None
        
        attrs = vector_def.get("attributes", {})
        
        # Si formule, l'évaluer
        formula = attrs.get("formula")
        if formula:
            return self.resolve(formula, context)
        
        # Si source = context.xxx, chercher dans context
        source = attrs.get("source", "")
        if source.startswith("context."):
            key = source.split(".", 1)[1]
            if key in context:
                return context[key]
        
        # Sinon retourner default
        default = attrs.get("default")
        if default:
            return self.resolve(default, context)
        
        return None
    
    def _resolve_date(self, value: str) -> datetime:
        """Résout une variable de date"""
        now = datetime.now()
        
        if value == "$now":
            return now
        if value == "$today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if value == "$yesterday":
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        if value == "$tomorrow":
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # $now+7d, $today-1w, etc.
        match = re.match(r'\$(now|today|yesterday|tomorrow)([+-])(\d+)([smhdwMy])', value)
        if match:
            base_name, op, amount, unit = match.groups()
            base = self._resolve_date(f"${base_name}")
            amount = int(amount)
            
            if unit == 's':
                delta = timedelta(seconds=amount)
            elif unit == 'm':
                delta = timedelta(minutes=amount)
            elif unit == 'h':
                delta = timedelta(hours=amount)
            elif unit == 'd':
                delta = timedelta(days=amount)
            elif unit == 'w':
                delta = timedelta(weeks=amount)
            elif unit == 'M':
                delta = timedelta(days=amount * 30)  # Approximation
            elif unit == 'y':
                delta = timedelta(days=amount * 365)
            else:
                delta = timedelta()
            
            if op == '+':
                return base + delta
            else:
                return base - delta
        
        return now
    
    def _resolve_expression(self, expr: str, context: Dict) -> Any:
        """Résout une expression conditionnelle"""
        # {cond?valTrue:valFalse}
        # Simplification: on cherche le premier ? et le :
        q_pos = expr.find('?')
        if q_pos == -1:
            # Pas de condition, c'est un calcul
            return self._resolve_calc(expr, context)
        
        condition = expr[:q_pos]
        rest = expr[q_pos+1:]
        
        # Trouver le : (attention aux imbrications)
        depth = 0
        colon_pos = -1
        for i, c in enumerate(rest):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            elif c == ':' and depth == 0:
                colon_pos = i
                break
        
        if colon_pos == -1:
            return None
        
        val_true = rest[:colon_pos]
        val_false = rest[colon_pos+1:]
        
        if self._eval_condition(condition, context):
            return self.resolve(val_true, context)
        else:
            return self.resolve(val_false, context)
    
    def _resolve_calc(self, expr: str, context: Dict) -> Any:
        """Résout un calcul simple"""
        # Remplacer les références par leurs valeurs
        # Simplification: eval Python (dangereux en prod, OK pour proto)
        try:
            return eval(expr)
        except:
            return expr
    
    def _eval_condition(self, condition: str, context: Dict) -> bool:
        """Évalue une condition simple"""
        # .attr=value, .attr>value, etc.
        match = re.match(r'\.?(\w+)\s*(=|!=|>|>=|<|<=|\?|!\?)\s*(.+)?', condition)
        if not match:
            return False
        
        attr, op, value = match.groups()
        
        # Récupérer la valeur de l'attribut depuis context
        actual = context.get(attr)
        
        if op == '?':
            return actual is not None
        if op == '!?':
            return actual is None
        
        if value:
            expected = self.resolve(value, context)
        else:
            expected = None
        
        if op == '=':
            return actual == expected
        if op == '!=':
            return actual != expected
        if op == '>':
            return actual > expected
        if op == '>=':
            return actual >= expected
        if op == '<':
            return actual < expected
        if op == '<=':
            return actual <= expected
        
        return False
    
    def _resolve_query(self, query: str, context: Dict) -> List[Dict]:
        """Exécute une requête SuperRead simplifiée"""
        # read Type.conditions --options
        # Pour le proto, on fait une recherche simple
        match = re.match(r'read\s+(\S+)', query)
        if match:
            pattern = match.group(1).split('.')[0]
            return self.store.query(pattern)
        return []


# ============================================================================
# EXECUTOR - Exécute les scénarios GEVR
# ============================================================================

class Executor:
    """Exécute les scénarios GEVR"""
    
    def __init__(self, store: Store, resolver: Resolver):
        self.store = store
        self.resolver = resolver
    
    def execute(self, scenario_lineage: str, context: Dict = None) -> Dict:
        """Exécute un scénario complet"""
        if context is None:
            context = {}
        
        scenario = self.store.get(scenario_lineage)
        if not scenario:
            return {"status": "error", "message": f"Scenario not found: {scenario_lineage}"}
        
        result = {
            "scenario": scenario_lineage,
            "status": "pending",
            "steps": {},
            "output": None
        }
        
        # Get steps (enfants du scénario)
        steps = self.store.get_children(scenario_lineage)
        
        # Trier par order ou par type GEVR
        step_order = {"GetStep": 1, "ExecuteStep": 2, "ValidateStep": 3, "RenderStep": 4}
        steps.sort(key=lambda s: step_order.get(s.split(":")[-1], 99))
        
        # Exécuter chaque step
        for step_lineage in steps:
            step_result = self._execute_step(step_lineage, context)
            step_name = step_lineage.split(":")[-1]
            result["steps"][step_name] = step_result
            
            if step_result.get("status") == "failed":
                result["status"] = "failed"
                return result
            
            # Passer le résultat au contexte pour le step suivant
            if "output" in step_result:
                context["_previous"] = step_result["output"]
        
        result["status"] = "done"
        result["output"] = context.get("_previous")
        return result
    
    def _execute_step(self, step_lineage: str, context: Dict) -> Dict:
        """Exécute un step"""
        step = self.store.get(step_lineage)
        if not step:
            return {"status": "failed", "message": f"Step not found: {step_lineage}"}
        
        attrs = step.get("attributes", {})
        step_type = attrs.get("type", step_lineage.split(":")[-1])
        
        result = {"status": "pending", "type": step_type}
        
        try:
            if step_type == "GetStep":
                result["output"] = self._execute_get(attrs, context)
            elif step_type == "ExecuteStep":
                result["output"] = self._execute_execute(attrs, context)
            elif step_type == "ValidateStep":
                result["output"] = self._execute_validate(attrs, context)
            elif step_type == "RenderStep":
                result["output"] = self._execute_render(attrs, context)
            
            result["status"] = "done"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def _execute_get(self, attrs: Dict, context: Dict) -> Any:
        """Exécute un GetStep"""
        action = attrs.get("action", "")
        
        if action.startswith("read "):
            return self.resolver._resolve_query(action, context)
        
        source = attrs.get("source", "")
        query = attrs.get("query", "")
        
        if source == "file" and query:
            # Charger un fichier
            parser = Parser()
            return parser.parse_file(query)
        
        if source == "store":
            return self.store.query(query)
        
        return context.get("_previous")
    
    def _execute_execute(self, attrs: Dict, context: Dict) -> Any:
        """Exécute un ExecuteStep"""
        action = attrs.get("action", "")
        
        if action:
            return self.resolver.resolve(action, context)
        
        method = attrs.get("method", "")
        if method:
            # Appeler une méthode (simplifié)
            return {"method": method, "executed": True}
        
        return context.get("_previous")
    
    def _execute_validate(self, attrs: Dict, context: Dict) -> Any:
        """Exécute un ValidateStep"""
        assertion = attrs.get("assert", "")
        
        if assertion:
            if not self.resolver._eval_condition(assertion, context):
                raise Exception(f"Validation failed: {assertion}")
        
        return context.get("_previous")
    
    def _execute_render(self, attrs: Dict, context: Dict) -> Any:
        """Exécute un RenderStep"""
        output = attrs.get("output", "")
        format_type = attrs.get("format", "json")
        
        data = context.get("_previous")
        
        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        
        return data


# ============================================================================
# VALIDATOR - Applique les rules
# ============================================================================

class Validator:
    """Applique les règles de validation"""
    
    def __init__(self, store: Store, resolver: Resolver):
        self.store = store
        self.resolver = resolver
    
    def validate(self, obj: Dict) -> Tuple[bool, List[str]]:
        """Valide un objet contre toutes les rules applicables"""
        errors = []
        lineage = obj.get("lineage", "")
        attrs = obj.get("attributes", {})
        
        # Contexte pour la résolution
        context = dict(attrs)
        context["lineage"] = lineage
        context["name"] = obj.get("name", "")
        
        for rule in self.store.rules:
            rule_attrs = rule.get("attributes", {})
            target = rule_attrs.get("target", "")
            
            # Rule s'applique à cet objet?
            if target and not lineage.startswith(target):
                continue
            
            # Évaluer l'assertion
            assertion = rule_attrs.get("assert", "")
            if assertion:
                if not self.resolver._eval_condition(assertion, context):
                    on_failure = rule_attrs.get("onFailure", "WARN")
                    message = rule_attrs.get("message", f"Rule {rule.get('name', '')} failed")
                    
                    if on_failure == "REJECT":
                        errors.append(f"ERROR: {message}")
                    else:
                        errors.append(f"WARN: {message}")
        
        has_errors = any(e.startswith("ERROR:") for e in errors)
        return (not has_errors, errors)
    
    def apply_defaults(self, obj: Dict) -> Dict:
        """Applique les règles de default"""
        lineage = obj.get("lineage", "")
        attrs = obj.get("attributes", {})
        
        context = dict(attrs)
        
        for rule in self.store.rules:
            rule_attrs = rule.get("attributes", {})
            target = rule_attrs.get("target", "")
            
            if target and not lineage.startswith(target):
                continue
            
            condition = rule_attrs.get("condition", "")
            action = rule_attrs.get("action", "")
            
            if condition and action.startswith("set "):
                if self.resolver._eval_condition(condition, context):
                    # Parse "set attr=value"
                    set_match = re.match(r'set\s+(\w+)=(.+)', action)
                    if set_match:
                        attr_name, attr_value = set_match.groups()
                        resolved = self.resolver.resolve(attr_value, context)
                        obj["attributes"][attr_name] = resolved
                        context[attr_name] = resolved
        
        return obj


# ============================================================================
# MRG - Méthode Récursive Générique
# ============================================================================

class MRG:
    """Méthode Récursive Générique - Point d'entrée principal"""
    
    def __init__(self):
        self.store = store
        self.parser = Parser()
        self.resolver = Resolver(store)
        self.executor = Executor(store, self.resolver)
        self.validator = Validator(store, self.resolver)
    
    def load(self, path: str) -> int:
        """Charge un fichier ou dossier .gev"""
        count = 0
        
        if os.path.isfile(path):
            objects = self.parser.parse_file(path)
            count = len(objects)
            print(f"  Loaded {count} objects from {path}")
        
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(('.gev', '.erk')):
                        filepath = os.path.join(root, file)
                        objects = self.parser.parse_file(filepath)
                        count += len(objects)
                        print(f"  Loaded {len(objects)} objects from {filepath}")
        
        return count
    
    def get(self, lineage: str) -> Optional[Dict]:
        """Récupère un objet par lineage"""
        return self.store.get(lineage)
    
    def get_create(self, lineage: str, defaults: Dict = None) -> Dict:
        """Get or Create pattern"""
        obj = self.store.get(lineage)
        
        if obj:
            return obj
        
        # Create
        if not lineage.startswith("Object:") and lineage != "Object":
            lineage = "Object:" + lineage
        
        parts = lineage.split(":")
        obj = {
            "lineage": lineage,
            "name": parts[-1],
            "parent": ":".join(parts[:-1]) if len(parts) > 1 else "",
            "attributes": defaults or {},
            "relations": [],
            "source": "runtime",
            "auto_created": True
        }
        
        # Appliquer defaults depuis rules
        obj = self.validator.apply_defaults(obj)
        
        self.store.add(lineage, obj)
        return obj
    
    def resolve(self, value: str, context: Dict = None) -> Any:
        """Résout une valeur"""
        return self.resolver.resolve(value, context or {})
    
    def validate(self, lineage: str) -> Tuple[bool, List[str]]:
        """Valide un objet"""
        obj = self.store.get(lineage)
        if not obj:
            return (False, [f"Object not found: {lineage}"])
        return self.validator.validate(obj)
    
    def execute(self, scenario: str, context: Dict = None) -> Dict:
        """Exécute un scénario"""
        return self.executor.execute(scenario, context or {})
    
    def traverse(self, lineage: str, callback) -> List[Any]:
        """Traverse le lineage et applique callback à chaque ancêtre"""
        results = []
        ancestors = self.store.get_ancestors(lineage)
        
        for ancestor in ancestors:
            obj = self.store.get(ancestor)
            if obj:
                result = callback(obj)
                results.append(result)
        
        # L'objet lui-même
        obj = self.store.get(lineage)
        if obj:
            results.append(callback(obj))
        
        return results
    
    def query(self, pattern: str) -> List[Dict]:
        """Recherche des objets"""
        return self.store.query(pattern)
    
    def stats(self) -> Dict:
        """Statistiques du store"""
        return {
            "objects": len(self.store.objects),
            "vectors": len(self.store.vectors),
            "rules": len(self.store.rules),
            "config": len(self.store.config)
        }
    
    def tree(self, root: str = "Object", depth: int = 3, indent: int = 0) -> str:
        """Affiche l'arbre des objets"""
        lines = []
        obj = self.store.get(root)
        
        if obj:
            prefix = "  " * indent
            name = obj.get("name", root)
            lines.append(f"{prefix}├── {name}")
        
        if depth > 0:
            children = self.store.get_children(root)
            for child in children:
                lines.append(self.tree(child, depth - 1, indent + 1))
        
        return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def main():
    """Point d'entrée CLI"""
    import sys
    
    mrg = MRG()
    
    print("=" * 60)
    print("EUREKAI Core - ERK Engine v0.1")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"\nLoading: {path}")
        count = mrg.load(path)
        print(f"\nTotal: {count} objects loaded")
        print(f"\nStats: {mrg.stats()}")
        
        if len(sys.argv) > 2:
            cmd = sys.argv[2]
            
            if cmd == "tree":
                print(f"\nTree:")
                print(mrg.tree())
            
            elif cmd == "validate":
                lineage = sys.argv[3] if len(sys.argv) > 3 else "Object"
                for l in mrg.store.objects.keys():
                    if l.startswith(lineage):
                        valid, errors = mrg.validate(l)
                        status = "✓" if valid else "✗"
                        print(f"{status} {l}")
                        for e in errors:
                            print(f"    {e}")
            
            elif cmd == "get":
                lineage = sys.argv[3] if len(sys.argv) > 3 else "Object"
                obj = mrg.get(lineage)
                if obj:
                    print(json.dumps(obj, indent=2, default=str))
                else:
                    print(f"Not found: {lineage}")
            
            elif cmd == "resolve":
                value = sys.argv[3] if len(sys.argv) > 3 else "V_Temperature"
                result = mrg.resolve(value)
                print(f"{value} => {result}")
            
            elif cmd == "repl":
                repl(mrg)
            
            elif cmd == "cockpit":
                output = sys.argv[3] if len(sys.argv) > 3 else "cockpit.html"
                generate_cockpit(mrg, output)
                print(f"\nOpen in browser: file://{os.path.abspath(output)}")
    
    else:
        print("\nUsage:")
        print("  python eurekai_core.py <path>              Load files")
        print("  python eurekai_core.py <path> tree         Show tree")
        print("  python eurekai_core.py <path> validate     Validate all")
        print("  python eurekai_core.py <path> get <lineage>   Get object")
        print("  python eurekai_core.py <path> resolve <V_xxx> Resolve vector")
        print("  python eurekai_core.py <path> repl         Interactive mode")
        print("  python eurekai_core.py <path> cockpit      Generate HTML cockpit")
        print("\nExamples:")
        print("  python eurekai_core.py ./eurekai-test")
        print("  python eurekai_core.py ./eurekai-test tree")
        print("  python eurekai_core.py ./eurekai-test repl")
        print("  python eurekai_core.py ./eurekai-test cockpit")


    # Mode interactif REPL
    if len(sys.argv) > 2 and sys.argv[2] == "repl":
        repl(mrg)


def repl(mrg: MRG):
    """Mode interactif REPL"""
    print("\n" + "=" * 60)
    print("EUREKAI REPL - Type 'help' for commands, 'quit' to exit")
    print("=" * 60 + "\n")
    
    superread = SuperRead(mrg)
    
    while True:
        try:
            cmd = input("eurekai> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        
        if not cmd:
            continue
        
        if cmd in ("quit", "exit", "q"):
            print("Bye!")
            break
        
        if cmd == "help":
            print("""
Commands:
  tree [depth]              Show object tree
  get <lineage>             Get object by lineage
  resolve <V_xxx>           Resolve a vector
  validate [lineage]        Validate objects
  stats                     Show statistics
  
SuperRead:
  read <Type>[.conditions]  Read objects
  create <Type>:<Name>      Create object
  update <Type>.cond set k=v Update objects
  delete <Type>.cond        Delete objects
  
Examples:
  read Agent
  read Agent.role=architect
  read Agent.temperature>0.5
  create Agent:TestAgent name="Test" role=executor
  get Object:Entity:Agent
  resolve V_Temperature
""")
            continue
        
        if cmd == "stats":
            print(mrg.stats())
            continue
        
        if cmd.startswith("tree"):
            parts = cmd.split()
            depth = int(parts[1]) if len(parts) > 1 else 3
            print(mrg.tree(depth=depth))
            continue
        
        if cmd.startswith("get "):
            lineage = cmd[4:].strip()
            obj = mrg.get(lineage)
            if obj:
                print(json.dumps(obj, indent=2, default=str))
            else:
                # Essayer avec préfixe Object:
                obj = mrg.get("Object:" + lineage)
                if obj:
                    print(json.dumps(obj, indent=2, default=str))
                else:
                    print(f"Not found: {lineage}")
            continue
        
        if cmd.startswith("resolve "):
            value = cmd[8:].strip()
            result = mrg.resolve(value)
            print(f"{value} => {result}")
            continue
        
        if cmd.startswith("validate"):
            parts = cmd.split()
            prefix = parts[1] if len(parts) > 1 else "Object"
            for lineage in mrg.store.objects.keys():
                if lineage.startswith(prefix):
                    valid, errors = mrg.validate(lineage)
                    status = "✓" if valid else "✗"
                    print(f"{status} {lineage}")
                    for e in errors:
                        print(f"    {e}")
            continue
        
        # SuperRead commands
        if cmd.startswith(("read ", "create ", "update ", "delete ")):
            result = superread.execute(cmd)
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("lineage", ""))
                        lineage = item.get("lineage", "")
                        print(f"  {name} ({lineage})")
                    else:
                        print(f"  {item}")
                print(f"\n{len(result)} result(s)")
            else:
                print(result)
            continue
        
        print(f"Unknown command: {cmd}. Type 'help' for available commands.")


# ============================================================================
# SUPERREAD - Query Language
# ============================================================================

class SuperRead:
    """Implémentation du langage SuperRead"""
    
    def __init__(self, mrg: MRG):
        self.mrg = mrg
    
    def execute(self, query: str) -> Any:
        """Exécute une requête SuperRead"""
        query = query.strip()
        
        if query.startswith("read "):
            return self._read(query[5:])
        elif query.startswith("create "):
            return self._create(query[7:])
        elif query.startswith("update "):
            return self._update(query[7:])
        elif query.startswith("delete "):
            return self._delete(query[7:])
        else:
            return f"Unknown command: {query}"
    
    def _read(self, query: str) -> List[Dict]:
        """read Type.conditions --options"""
        # Parse query
        parts = query.split()
        type_and_conditions = parts[0] if parts else ""
        options = self._parse_options(parts[1:])
        
        # Séparer type et conditions
        if "." in type_and_conditions:
            type_name, conditions_str = type_and_conditions.split(".", 1)
        else:
            type_name = type_and_conditions
            conditions_str = ""
        
        # Trouver les objets du type
        results = []
        search_pattern = f":{type_name}" if not type_name.startswith("Object:") else type_name
        
        for lineage, obj in self.mrg.store.objects.items():
            # Match le type (dans le lineage)
            if search_pattern in lineage or lineage.endswith(f":{type_name}"):
                # Appliquer les conditions
                if self._match_conditions(obj, conditions_str):
                    results.append(obj)
        
        # Appliquer options
        results = self._apply_options(results, options)
        
        return results
    
    def _create(self, query: str) -> Dict:
        """create Type:Name attr=val attr2=val2"""
        parts = query.split()
        if not parts:
            return {"error": "Missing type:name"}
        
        type_name = parts[0]
        attrs = {}
        
        # Parser les attributs
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                attrs[key] = value
        
        # Créer l'objet
        if not type_name.startswith("Object:"):
            type_name = "Object:" + type_name
        
        obj = self.mrg.get_create(type_name, attrs)
        return obj
    
    def _update(self, query: str) -> List[Dict]:
        """update Type.conditions set attr=val,attr2=val2"""
        # Trouver "set"
        if " set " not in query:
            return {"error": "Missing 'set' clause"}
        
        target_part, set_part = query.split(" set ", 1)
        
        # Récupérer les objets à modifier
        objects = self._read(target_part)
        
        # Parser les modifications
        updates = {}
        for item in set_part.split(","):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                updates[key.strip()] = value.strip()
        
        # Appliquer les modifications
        updated = []
        for obj in objects:
            for key, value in updates.items():
                # Résoudre la valeur si c'est une expression
                resolved = self.mrg.resolve(value, obj.get("attributes", {}))
                obj["attributes"][key] = resolved
            updated.append(obj)
        
        return updated
    
    def _delete(self, query: str) -> Dict:
        """delete Type.conditions"""
        objects = self._read(query)
        
        deleted = 0
        for obj in objects:
            lineage = obj.get("lineage")
            if lineage and lineage in self.mrg.store.objects:
                del self.mrg.store.objects[lineage]
                deleted += 1
        
        return {"deleted": deleted}
    
    def _parse_options(self, parts: List[str]) -> Dict:
        """Parse les options --xxx=yyy"""
        options = {}
        for part in parts:
            if part.startswith("--"):
                if "=" in part:
                    key, value = part[2:].split("=", 1)
                    options[key] = value
                else:
                    options[part[2:]] = True
        return options
    
    def _match_conditions(self, obj: Dict, conditions_str: str) -> bool:
        """Vérifie si un objet match les conditions"""
        if not conditions_str:
            return True
        
        attrs = obj.get("attributes", {})
        
        # Split par . (AND)
        conditions = conditions_str.split(".")
        
        for cond in conditions:
            if not cond:
                continue
            
            # Parser la condition: attr op value
            match = re.match(r'(\w+)(=|!=|>|>=|<|<=|~|\^|\$|\?|!\?)(.+)?', cond)
            if not match:
                continue
            
            attr, op, value = match.groups()
            actual = attrs.get(attr)
            
            # Nettoyer les guillemets
            if actual and isinstance(actual, str):
                actual = actual.strip('"')
            if value:
                value = value.strip('"')
            
            # Convertir en nombre si possible
            try:
                if actual:
                    actual_num = float(actual)
                else:
                    actual_num = None
                if value:
                    value_num = float(value)
                else:
                    value_num = None
            except (ValueError, TypeError):
                actual_num = None
                value_num = None
            
            # Évaluer
            if op == "=":
                if actual != value:
                    return False
            elif op == "!=":
                if actual == value:
                    return False
            elif op == ">":
                if actual_num is None or value_num is None or actual_num <= value_num:
                    return False
            elif op == ">=":
                if actual_num is None or value_num is None or actual_num < value_num:
                    return False
            elif op == "<":
                if actual_num is None or value_num is None or actual_num >= value_num:
                    return False
            elif op == "<=":
                if actual_num is None or value_num is None or actual_num > value_num:
                    return False
            elif op == "~":
                if not actual or value not in actual:
                    return False
            elif op == "^":
                if not actual or not actual.startswith(value):
                    return False
            elif op == "$":
                if not actual or not actual.endswith(value):
                    return False
            elif op == "?":
                if actual is None:
                    return False
            elif op == "!?":
                if actual is not None:
                    return False
        
        return True
    
    def _apply_options(self, results: List[Dict], options: Dict) -> List[Dict]:
        """Applique les options de tri, limite, etc."""
        
        # Order
        if "order" in options:
            order_field = options["order"]
            reverse = order_field.startswith("-")
            if reverse:
                order_field = order_field[1:]
            
            results.sort(
                key=lambda x: x.get("attributes", {}).get(order_field, ""),
                reverse=reverse
            )
        
        # Limit
        if "limit" in options:
            limit = int(options["limit"])
            results = results[:limit]
        
        # Offset
        if "offset" in options:
            offset = int(options["offset"])
            results = results[offset:]
        
        # Fields (projection)
        if "fields" in options:
            fields = options["fields"].split(",")
            projected = []
            for obj in results:
                proj = {"lineage": obj.get("lineage")}
                for f in fields:
                    if f in obj:
                        proj[f] = obj[f]
                    elif f in obj.get("attributes", {}):
                        proj[f] = obj["attributes"][f]
                projected.append(proj)
            results = projected
        
        # Count
        if options.get("count"):
            return [{"count": len(results)}]
        
        return results


# ============================================================================
# HTML COCKPIT GENERATOR
# ============================================================================

def generate_cockpit(mrg: MRG, output_path: str = "cockpit.html"):
    """Génère un cockpit HTML interactif"""
    
    # Construire l'arbre JSON
    def build_tree(lineage: str, depth: int = 5) -> Dict:
        obj = mrg.store.get(lineage)
        node = {
            "name": obj.get("name", lineage.split(":")[-1]) if obj else lineage.split(":")[-1],
            "lineage": lineage,
            "attributes": obj.get("attributes", {}) if obj else {},
            "children": []
        }
        
        if depth > 0:
            children = mrg.store.get_children(lineage)
            for child in children:
                node["children"].append(build_tree(child, depth - 1))
        
        return node
    
    tree_data = build_tree("Object", depth=10)
    
    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EUREKAI Cockpit</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e; 
            color: #eee; 
            display: flex;
            height: 100vh;
        }}
        
        /* Sidebar - Arbre */
        .sidebar {{
            width: 350px;
            background: #16213e;
            border-right: 1px solid #0f3460;
            overflow-y: auto;
            padding: 20px;
        }}
        .sidebar h2 {{
            color: #e94560;
            margin-bottom: 20px;
            font-size: 1.2em;
        }}
        
        /* Tree */
        .tree ul {{
            list-style: none;
            padding-left: 20px;
        }}
        .tree > ul {{ padding-left: 0; }}
        .tree li {{
            position: relative;
            padding: 5px 0;
        }}
        .tree li::before {{
            content: "";
            position: absolute;
            left: -15px;
            top: 0;
            border-left: 1px solid #0f3460;
            height: 100%;
        }}
        .tree li::after {{
            content: "";
            position: absolute;
            left: -15px;
            top: 15px;
            border-top: 1px solid #0f3460;
            width: 10px;
        }}
        .tree li:last-child::before {{ height: 15px; }}
        
        .node {{
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
            transition: all 0.2s;
        }}
        .node:hover {{ background: #0f3460; }}
        .node.selected {{ background: #e94560; }}
        .node .name {{ font-weight: 600; }}
        .node .count {{ 
            color: #888; 
            font-size: 0.8em; 
            margin-left: 5px;
        }}
        
        .toggle {{
            cursor: pointer;
            margin-right: 5px;
            color: #e94560;
        }}
        
        /* Main content */
        .main {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        
        /* Header */
        .header {{
            background: #16213e;
            padding: 15px 20px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .header h1 {{
            color: #e94560;
            font-size: 1.5em;
        }}
        .search {{
            flex: 1;
            max-width: 400px;
        }}
        .search input {{
            width: 100%;
            padding: 10px 15px;
            border: 1px solid #0f3460;
            border-radius: 20px;
            background: #1a1a2e;
            color: #eee;
            outline: none;
        }}
        .search input:focus {{ border-color: #e94560; }}
        
        /* Content area */
        .content {{
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }}
        
        /* Object detail */
        .object-detail {{
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .object-detail h3 {{
            color: #e94560;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .lineage {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 15px;
            font-family: monospace;
        }}
        
        /* Attributes table */
        .attrs-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .attrs-table th, .attrs-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #0f3460;
        }}
        .attrs-table th {{
            color: #e94560;
            font-weight: 600;
            width: 200px;
        }}
        .attrs-table td {{
            font-family: monospace;
        }}
        .attrs-table tr:hover {{ background: #1a1a2e; }}
        
        /* Stats */
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            min-width: 120px;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #e94560;
        }}
        .stat-card .label {{
            color: #888;
            font-size: 0.9em;
        }}
        
        /* Console */
        .console {{
            background: #0d0d1a;
            border-top: 1px solid #0f3460;
            padding: 15px;
        }}
        .console-input {{
            display: flex;
            gap: 10px;
        }}
        .console-input input {{
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #0f3460;
            border-radius: 4px;
            background: #1a1a2e;
            color: #eee;
            font-family: monospace;
            outline: none;
        }}
        .console-input button {{
            padding: 10px 20px;
            background: #e94560;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .console-input button:hover {{ background: #c73e54; }}
        .console-output {{
            margin-top: 10px;
            padding: 10px;
            background: #1a1a2e;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🌳 Fractale</h2>
        <div class="tree" id="tree"></div>
    </div>
    
    <div class="main">
        <div class="header">
            <h1>EUREKAI Cockpit</h1>
            <div class="search">
                <input type="text" id="search" placeholder="Rechercher un objet...">
            </div>
        </div>
        
        <div class="content" id="content">
            <div class="stats">
                <div class="stat-card">
                    <div class="value" id="stat-objects">0</div>
                    <div class="label">Objets</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-vectors">0</div>
                    <div class="label">Vecteurs</div>
                </div>
                <div class="stat-card">
                    <div class="value" id="stat-rules">0</div>
                    <div class="label">Rules</div>
                </div>
            </div>
            
            <div class="object-detail" id="detail">
                <h3>Sélectionnez un objet</h3>
                <p>Cliquez sur un élément dans l'arbre pour voir ses détails.</p>
            </div>
        </div>
        
        <div class="console">
            <div class="console-input">
                <input type="text" id="cmd" placeholder="SuperRead: read Agent.role=architect">
                <button onclick="executeCmd()">Exécuter</button>
            </div>
            <div class="console-output" id="output"></div>
        </div>
    </div>
    
    <script>
        // Data
        const treeData = {json.dumps(tree_data, ensure_ascii=False)};
        const stats = {json.dumps(mrg.stats())};
        
        // Update stats
        document.getElementById('stat-objects').textContent = stats.objects;
        document.getElementById('stat-vectors').textContent = stats.vectors;
        document.getElementById('stat-rules').textContent = stats.rules;
        
        // Render tree
        function renderTree(node, container) {{
            const li = document.createElement('li');
            
            const hasChildren = node.children && node.children.length > 0;
            
            const nodeEl = document.createElement('span');
            nodeEl.className = 'node';
            nodeEl.innerHTML = `
                ${{hasChildren ? '<span class="toggle">▼</span>' : '<span class="toggle" style="visibility:hidden">▼</span>'}}
                <span class="name">${{node.name}}</span>
                ${{hasChildren ? `<span class="count">(${{node.children.length}})</span>` : ''}}
            `;
            nodeEl.onclick = (e) => {{
                e.stopPropagation();
                selectNode(node);
                
                // Toggle children
                if (hasChildren) {{
                    const ul = li.querySelector('ul');
                    const toggle = nodeEl.querySelector('.toggle');
                    if (ul) {{
                        ul.style.display = ul.style.display === 'none' ? 'block' : 'none';
                        toggle.textContent = ul.style.display === 'none' ? '▶' : '▼';
                    }}
                }}
            }};
            
            li.appendChild(nodeEl);
            
            if (hasChildren) {{
                const ul = document.createElement('ul');
                node.children.forEach(child => renderTree(child, ul));
                li.appendChild(ul);
            }}
            
            container.appendChild(li);
        }}
        
        function selectNode(node) {{
            // Remove previous selection
            document.querySelectorAll('.node.selected').forEach(el => el.classList.remove('selected'));
            event.currentTarget.classList.add('selected');
            
            // Show detail
            const detail = document.getElementById('detail');
            
            let attrsHtml = '';
            const attrs = node.attributes || {{}};
            for (const [key, value] of Object.entries(attrs)) {{
                attrsHtml += `<tr><th>${{key}}</th><td>${{value}}</td></tr>`;
            }}
            
            detail.innerHTML = `
                <h3>${{node.name}}</h3>
                <div class="lineage">${{node.lineage}}</div>
                ${{Object.keys(attrs).length > 0 ? `
                    <table class="attrs-table">
                        <tbody>${{attrsHtml}}</tbody>
                    </table>
                ` : '<p>Aucun attribut</p>'}}
            `;
        }}
        
        function executeCmd() {{
            const cmd = document.getElementById('cmd').value;
            const output = document.getElementById('output');
            output.textContent = `> ${{cmd}}\\n\\n(Exécution côté serveur requise)`;
        }}
        
        // Search
        document.getElementById('search').addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.tree .node').forEach(node => {{
                const text = node.textContent.toLowerCase();
                node.parentElement.style.display = text.includes(query) ? 'block' : 'none';
            }});
        }});
        
        // Init
        const treeContainer = document.getElementById('tree');
        const ul = document.createElement('ul');
        renderTree(treeData, ul);
        treeContainer.appendChild(ul);
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Cockpit generated: {output_path}")
    return output_path


if __name__ == "__main__":
    main()
