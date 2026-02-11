#!/usr/bin/env python3
"""
EURKAI - ERK to Python Converter
==================================
Génère du code Python à partir d'objets ERK Method.

Usage:
    python erk_to_py.py methods.s.gev -o output.py
    python erk_to_py.py methods.s.gev --class MyClass   # Encapsulé dans une classe
    python erk_to_py.py methods.s.gev --async           # Fonctions async

Output:
    - Fonctions Python avec docstrings et type hints
    - Classes si demandé
    - Décorateurs GEVR
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import du parser ERK
from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → Python
# =============================================================================

TYPE_MAP = {
    'string': 'str',
    'str': 'str',
    'number': 'float',
    'int': 'int',
    'float': 'float',
    'boolean': 'bool',
    'bool': 'bool',
    'array': 'list',
    'list': 'list',
    'object': 'dict',
    'dict': 'dict',
    'any': 'Any',
    '*': 'Any',
    'function': 'Callable',
    'callable': 'Callable',
    'none': 'None',
    'null': 'None',
}


def erk_type_to_py(erk_type: str) -> str:
    """Convertit un type ERK en type Python"""
    return TYPE_MAP.get(erk_type.lower(), erk_type)


def to_snake_case(name: str) -> str:
    """Convertit camelCase en snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# =============================================================================
# CODE GENERATOR
# =============================================================================

class PythonGenerator:
    """Génère du code Python à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code Python complet"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Imports
        lines.extend(self._generate_imports())
        lines.append("")
        lines.append("")
        
        # Classe wrapper si demandé
        if self.options.get('class_name'):
            lines.extend(self._generate_class())
        else:
            # Fonctions standalone
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
                lines.append("")
            
            # __all__
            lines.extend(self._generate_all())
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header du fichier"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            '"""',
            'EURKAI - Generated Python Module',
            f'Source: {source}',
            f'Generated: {datetime.now().isoformat()}',
            f'Methods: {len(self.methods)}',
            '"""',
        ]
    
    def _generate_imports(self) -> List[str]:
        """Génère les imports"""
        lines = [
            "from typing import Any, Dict, List, Optional, Callable",
        ]
        
        # Ajouter asyncio si nécessaire
        has_async = any(
            m.attributes.get('isAsync') or m.attributes.get('async')
            for m in self.methods
        )
        if has_async or self.options.get('async'):
            lines.append("import asyncio")
        
        # Imports personnalisés
        custom_imports = self.options.get('imports', [])
        for imp in custom_imports:
            lines.append(imp)
        
        return lines
    
    def _generate_function(self, method: ERKObject, indent: str = "") -> List[str]:
        """Génère une fonction Python"""
        lines = []
        attrs = method.attributes
        
        name = method.name
        py_name = to_snake_case(name) if self.options.get('snake_case', True) else name
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        is_async = attrs.get('isAsync', False) or attrs.get('async', False)
        central_method = attrs.get('centralMethod', 'Execute')
        return_type = erk_type_to_py(attrs.get('returnType', attrs.get('returns', 'Any')))
        
        # Décorateur si demandé
        if self.options.get('decorators'):
            lines.append(f"{indent}@gevr_method('{central_method}')")
        
        # Construire la signature
        param_parts = []
        for param in (params if isinstance(params, list) else []):
            if isinstance(param, str):
                param_name = param
                param_type = attrs.get(f'param_{param}_type', 'Any')
                param_default = attrs.get(f'param_{param}_default')
            else:
                param_name = param.get('name', 'arg')
                param_type = param.get('type', 'Any')
                param_default = param.get('default')
            
            py_type = erk_type_to_py(param_type)
            
            if param_default is not None:
                # Convertir default JS → Python
                if param_default == 'null' or param_default == 'undefined':
                    param_default = 'None'
                elif param_default == 'true':
                    param_default = 'True'
                elif param_default == 'false':
                    param_default = 'False'
                param_parts.append(f"{param_name}: {py_type} = {param_default}")
            else:
                param_parts.append(f"{param_name}: {py_type}")
        
        params_str = ', '.join(param_parts)
        
        # Définition
        async_keyword = "async " if (is_async or self.options.get('async')) else ""
        lines.append(f"{indent}{async_keyword}def {py_name}({params_str}) -> {return_type}:")
        
        # Docstring
        lines.append(f'{indent}    """')
        lines.append(f'{indent}    {description}')
        lines.append(f'{indent}    ')
        lines.append(f'{indent}    CentralMethod: {central_method}')
        
        if params:
            lines.append(f'{indent}    ')
            lines.append(f'{indent}    Args:')
            for param in (params if isinstance(params, list) else []):
                if isinstance(param, str):
                    param_name = param
                    param_type = attrs.get(f'param_{param}_type', 'Any')
                else:
                    param_name = param.get('name', 'arg')
                    param_type = param.get('type', 'Any')
                lines.append(f'{indent}        {param_name}: {param_type}')
        
        lines.append(f'{indent}    ')
        lines.append(f'{indent}    Returns:')
        lines.append(f'{indent}        {return_type}')
        lines.append(f'{indent}    """')
        
        # Body
        if 'code' in attrs and self.options.get('include_code'):
            lines.append(f"{indent}    # Original JS code (needs conversion):")
            for code_line in attrs['code'].split('\n')[:10]:
                lines.append(f"{indent}    # {code_line}")
            lines.append(f"{indent}    pass  # TODO: Convert from JS")
        else:
            # Template basé sur centralMethod
            if central_method == 'Create':
                lines.append(f"{indent}    # Create logic")
                lines.append(f"{indent}    result = {{}}")
                lines.append(f"{indent}    return result")
            elif central_method == 'Read':
                lines.append(f"{indent}    # Read logic")
                lines.append(f"{indent}    return None")
            elif central_method == 'Update':
                lines.append(f"{indent}    # Update logic")
                lines.append(f"{indent}    return True")
            elif central_method == 'Delete':
                lines.append(f"{indent}    # Delete logic")
                lines.append(f"{indent}    return True")
            elif central_method == 'Render':
                lines.append(f"{indent}    # Render logic")
                lines.append(f"{indent}    html = ''")
                lines.append(f"{indent}    return html")
            elif central_method == 'Validate':
                lines.append(f"{indent}    # Validation logic")
                lines.append(f"{indent}    return True")
            elif central_method == 'Transform':
                lines.append(f"{indent}    # Transform logic")
                lines.append(f"{indent}    return None")
            else:
                lines.append(f"{indent}    # Execute logic")
                lines.append(f"{indent}    pass")
        
        return lines
    
    def _generate_class(self) -> List[str]:
        """Génère une classe englobante"""
        lines = []
        class_name = self.options.get('class_name', 'ERKMethods')
        
        lines.append(f"class {class_name}:")
        lines.append(f'    """')
        lines.append(f'    EURKAI Methods Container')
        lines.append(f'    Generated from ERK definitions')
        lines.append(f'    """')
        lines.append("")
        
        # Constructor
        lines.append("    def __init__(self, context: Dict[str, Any] = None):")
        lines.append('        """Initialize with optional context."""')
        lines.append("        self.context = context or {}")
        lines.append("")
        
        # Methods
        for method in self.methods:
            lines.extend(self._generate_function(method, "    "))
            lines.append("")
        
        return lines
    
    def _generate_all(self) -> List[str]:
        """Génère __all__"""
        lines = []
        method_names = [
            to_snake_case(m.name) if self.options.get('snake_case', True) else m.name
            for m in self.methods
        ]
        
        if not method_names:
            return lines
        
        lines.append("__all__ = [")
        for name in method_names:
            lines.append(f"    '{name}',")
        lines.append("]")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to Python Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_py.py methods.s.gev                    # Standard output
  python erk_to_py.py methods.s.gev -o methods.py      # Save to file
  python erk_to_py.py methods.s.gev --class MyClass    # Class wrapper
  python erk_to_py.py methods.s.gev --async            # All async
  python erk_to_py.py methods.s.gev --no-snake         # Keep camelCase
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--class', dest='class_name', help='Wrap in class with given name')
    parser.add_argument('--async', dest='force_async', action='store_true', 
                       help='Make all functions async')
    parser.add_argument('--no-snake', action='store_true', 
                       help='Keep camelCase names (no snake_case conversion)')
    parser.add_argument('--decorators', action='store_true',
                       help='Add @gevr_method decorators')
    parser.add_argument('--include-code', action='store_true',
                       help='Include original JS code as comments')
    parser.add_argument('--filter', help='Filter by centralMethod')
    
    args = parser.parse_args()
    
    # Parse ERK
    objects = parse_gev_file(args.file)
    
    # Filter si demandé
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        objects = [o for o in objects 
                   if o.attributes.get('centralMethod', 'Execute') in allowed]
    
    # Options
    options = {
        'class_name': args.class_name,
        'async': args.force_async,
        'snake_case': not args.no_snake,
        'decorators': args.decorators,
        'include_code': args.include_code,
    }
    
    # Generate
    generator = PythonGenerator(objects, options)
    output = generator.generate()
    
    # Output
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        methods = filter_by_type(objects, 'Method')
        print(f"✅ Generated {args.output} ({len(methods)} methods)")
    else:
        print(output)


if __name__ == '__main__':
    main()
