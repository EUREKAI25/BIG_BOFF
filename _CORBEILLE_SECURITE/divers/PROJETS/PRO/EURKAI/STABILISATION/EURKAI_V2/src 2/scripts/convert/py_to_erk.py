#!/usr/bin/env python3
"""
EURKAI - Python to ERK Converter
==================================
Convertit du code Python en objets ERK Method (.gev).

Usage:
    python py_to_erk.py module.py -o methods.s.gev
    python py_to_erk.py module.py --format json
    python py_to_erk.py module.py --stats

Utilise l'AST Python pour extraire:
- Fonctions (sync et async)
- Méthodes de classes
- Docstrings et type hints
- Dépendances
"""

import ast
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ERKParam:
    """Paramètre d'une fonction ERK"""
    name: str
    type: str = "any"
    required: bool = True
    default: Optional[str] = None


@dataclass
class ERKMethod:
    """Méthode ERK extraite du Python"""
    name: str
    lineage: str = ""
    description: str = ""
    params: List[ERKParam] = field(default_factory=list)
    return_type: str = "any"
    central_method: str = "Execute"
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    class_name: Optional[str] = None  # Si c'est une méthode de classe


# =============================================================================
# CENTRAL METHOD DETECTION
# =============================================================================

CENTRAL_METHOD_PATTERNS = {
    'Create': ['create', 'add', 'new', 'insert', 'generate', 'build', 'make'],
    'Read': ['get', 'read', 'fetch', 'load', 'find', 'query', 'list', 'retrieve', 'select'],
    'Update': ['update', 'set', 'modify', 'change', 'edit', 'replace', 'patch'],
    'Delete': ['delete', 'remove', 'destroy', 'clear', 'drop', 'purge'],
    'Render': ['render', 'display', 'show', 'draw', 'paint', 'format', 'to_html', 'to_string'],
    'Validate': ['validate', 'check', 'verify', 'is_', 'has_', 'can_', 'ensure'],
    'Transform': ['transform', 'convert', 'parse', 'serialize', 'deserialize', 'encode', 'decode'],
}


def detect_central_method(name: str) -> str:
    """Détecte le centralMethod basé sur le nom de la fonction"""
    name_lower = name.lower()
    
    for method, patterns in CENTRAL_METHOD_PATTERNS.items():
        for pattern in patterns:
            if name_lower.startswith(pattern):
                return method
    
    return "Execute"


# =============================================================================
# TYPE MAPPING Python → ERK
# =============================================================================

TYPE_MAP = {
    'str': 'string',
    'int': 'number',
    'float': 'number',
    'bool': 'boolean',
    'list': 'array',
    'dict': 'object',
    'List': 'array',
    'Dict': 'object',
    'Any': 'any',
    'None': 'none',
    'Optional': 'any',
    'Callable': 'function',
}


def py_type_to_erk(py_type: str) -> str:
    """Convertit un type Python en type ERK"""
    # Nettoyer les types génériques
    if '[' in py_type:
        base = py_type.split('[')[0]
        return TYPE_MAP.get(base, py_type.lower())
    return TYPE_MAP.get(py_type, py_type.lower())


def annotation_to_str(annotation) -> str:
    """Convertit une annotation AST en string"""
    if annotation is None:
        return "any"
    try:
        return ast.unparse(annotation)
    except:
        return "any"


# =============================================================================
# PYTHON PARSER
# =============================================================================

class PythonToERKParser:
    """Parse Python et extrait les méthodes ERK"""
    
    def __init__(self, source: str, filename: str = ""):
        self.source = source
        self.filename = filename
        self.methods: List[ERKMethod] = []
        
    def parse(self) -> List[ERKMethod]:
        """Parse le fichier Python"""
        tree = ast.parse(self.source, filename=self.filename)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.methods.append(self._parse_function(node))
            elif isinstance(node, ast.AsyncFunctionDef):
                self.methods.append(self._parse_function(node, is_async=True))
            elif isinstance(node, ast.ClassDef):
                self._parse_class(node)
        
        return self.methods
    
    def _parse_function(self, node: ast.FunctionDef, is_async: bool = False,
                       class_name: str = None) -> ERKMethod:
        """Parse une fonction Python"""
        name = node.name
        
        # Skip méthodes privées
        if name.startswith('_') and not name.startswith('__'):
            visibility = "protected"
        elif name.startswith('__') and not name.endswith('__'):
            visibility = "private"
        else:
            visibility = "public"
        
        # Docstring
        docstring = ast.get_docstring(node) or f"Python function {name}"
        
        # Paramètres
        params = []
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        
        for i, arg in enumerate(node.args.args):
            # Skip 'self' pour les méthodes
            if arg.arg == 'self':
                continue
            
            param_type = annotation_to_str(arg.annotation)
            
            # Default value
            default = None
            default_idx = i - defaults_offset
            if default_idx >= 0 and default_idx < len(node.args.defaults):
                try:
                    default = ast.unparse(node.args.defaults[default_idx])
                except:
                    default = "..."
            
            params.append(ERKParam(
                name=arg.arg,
                type=py_type_to_erk(param_type),
                required=default is None,
                default=default
            ))
        
        # Return type
        return_type = py_type_to_erk(annotation_to_str(node.returns))
        
        # Decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except:
                pass
        
        # Central method
        central_method = detect_central_method(name)
        
        # Lineage
        if class_name:
            lineage = f"Object:Method:PyMethod:{class_name}_{name}:"
        else:
            lineage = f"Object:Method:PyFunction:{name}:"
        
        return ERKMethod(
            name=name,
            lineage=lineage,
            description=docstring.split('\n')[0],  # Première ligne seulement
            params=params,
            return_type=return_type,
            central_method=central_method,
            is_async=is_async or isinstance(node, ast.AsyncFunctionDef),
            decorators=decorators,
            class_name=class_name
        )
    
    def _parse_class(self, node: ast.ClassDef):
        """Parse une classe et ses méthodes"""
        class_name = node.name
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self._parse_function(item, class_name=class_name)
                # Ne pas dupliquer si déjà parsé par ast.walk
                if not any(m.name == method.name and m.class_name == class_name 
                          for m in self.methods):
                    self.methods.append(method)
            elif isinstance(item, ast.AsyncFunctionDef):
                method = self._parse_function(item, is_async=True, class_name=class_name)
                if not any(m.name == method.name and m.class_name == class_name 
                          for m in self.methods):
                    self.methods.append(method)


# =============================================================================
# ERK GENERATOR
# =============================================================================

class ERKGenerator:
    """Génère la syntaxe ERK/GEV à partir des méthodes"""
    
    def __init__(self, methods: List[ERKMethod], source_file: str = ""):
        self.methods = methods
        self.source_file = source_file
    
    def to_gev(self) -> str:
        """Génère le format .gev"""
        lines = [
            f"# ============================================================",
            f"# EURKAI - Python Functions → ERK Methods",
            f"# Source: {self.source_file}",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Methods: {len(self.methods)}",
            f"# ============================================================",
            "",
        ]
        
        # Grouper par centralMethod
        by_method = {}
        for method in self.methods:
            cm = method.central_method
            by_method.setdefault(cm, []).append(method)
        
        for central_method, methods in sorted(by_method.items()):
            lines.append(f"# --- {central_method} Methods ({len(methods)}) ---")
            lines.append("")
            
            for method in methods:
                lines.extend(self._method_to_gev(method))
                lines.append("")
        
        return '\n'.join(lines)
    
    def _method_to_gev(self, method: ERKMethod) -> List[str]:
        """Convertit une méthode en syntaxe GEV"""
        lines = []
        
        # Lineage
        lines.append(method.lineage)
        
        # Description
        desc = method.description.replace('"', '\\"')
        lines.append(f'    .description = "{desc}"')
        
        # CentralMethod
        lines.append(f'    .centralMethod = {method.central_method}')
        
        # Class (si méthode)
        if method.class_name:
            lines.append(f'    .className = "{method.class_name}"')
        
        # Params
        if method.params:
            param_names = [f'"{p.name}"' for p in method.params]
            lines.append(f'    .params = [{", ".join(param_names)}]')
            
            for p in method.params:
                lines.append(f'    .param_{p.name}_type = "{p.type}"')
                if not p.required and p.default:
                    lines.append(f'    .param_{p.name}_default = {p.default}')
        
        # Return type
        lines.append(f'    .returnType = "{method.return_type}"')
        
        # Async
        if method.is_async:
            lines.append(f'    .isAsync = true')
        
        # Decorators
        if method.decorators:
            dec_list = [f'"{d}"' for d in method.decorators]
            lines.append(f'    .decorators = [{", ".join(dec_list)}]')
        
        lines.append(f'    .sourceLanguage = "python"')
        
        return lines
    
    def to_json(self) -> str:
        """Génère le format JSON"""
        data = {
            "source": self.source_file,
            "generated": datetime.now().isoformat(),
            "count": len(self.methods),
            "methods": []
        }
        
        for method in self.methods:
            method_data = {
                "name": method.name,
                "lineage": method.lineage,
                "description": method.description,
                "centralMethod": method.central_method,
                "returnType": method.return_type,
                "isAsync": method.is_async,
                "params": [asdict(p) for p in method.params],
                "decorators": method.decorators,
            }
            if method.class_name:
                method_data["className"] = method.class_name
            data["methods"].append(method_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - Python to ERK Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python py_to_erk.py module.py                    # Output GEV to stdout
  python py_to_erk.py module.py -o methods.s.gev   # Save to file
  python py_to_erk.py module.py --format json      # Output JSON
  python py_to_erk.py module.py --stats            # Show stats only
        """
    )
    
    parser.add_argument('file', help='Python file to parse')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-f', '--format', choices=['gev', 'json'], 
                       default='gev', help='Output format')
    parser.add_argument('--stats', action='store_true', help='Show stats only')
    parser.add_argument('--filter', help='Filter by centralMethod')
    
    args = parser.parse_args()
    
    # Lire le fichier
    source = Path(args.file).read_text(encoding='utf-8')
    
    # Parser
    parser_py = PythonToERKParser(source, args.file)
    methods = parser_py.parse()
    
    # Filtrer si demandé
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        methods = [m for m in methods if m.central_method in allowed]
    
    # Stats only
    if args.stats:
        print(f"📄 File: {args.file}")
        print(f"📦 Methods: {len(methods)}")
        print()
        
        # Par centralMethod
        by_method = {}
        for m in methods:
            by_method[m.central_method] = by_method.get(m.central_method, 0) + 1
        
        print("By CentralMethod:")
        for cm, count in sorted(by_method.items(), key=lambda x: -x[1]):
            print(f"  {cm}: {count}")
        
        print()
        print("Methods:")
        for m in methods:
            async_mark = "⚡" if m.is_async else ""
            class_mark = f"[{m.class_name}]" if m.class_name else ""
            params = ", ".join([p.name for p in m.params])
            print(f"  [{m.central_method:10}] {class_mark}{m.name}({params}) {async_mark}")
        
        return
    
    # Générer
    generator = ERKGenerator(methods, args.file)
    
    if args.format == 'gev':
        output = generator.to_gev()
    else:
        output = generator.to_json()
    
    # Output
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✅ Generated {args.output} ({len(methods)} methods)")
    else:
        print(output)


if __name__ == '__main__':
    main()
