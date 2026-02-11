#!/usr/bin/env python3
"""
EURKAI - ERK to Go Converter
==============================
Génère du code Go à partir d'objets ERK Method.

Usage:
    python erk_to_go.py methods.s.gev -o methods.go
    python erk_to_go.py methods.s.gev --package mypackage
    python erk_to_go.py methods.s.gev --struct MyService

Output:
    - Fonctions Go avec documentation
    - Struct avec méthodes si demandé
    - Types Go idiomatiques
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → Go
# =============================================================================

TYPE_MAP = {
    'string': 'string',
    'str': 'string',
    'number': 'float64',
    'int': 'int',
    'float': 'float64',
    'boolean': 'bool',
    'bool': 'bool',
    'array': '[]interface{}',
    'list': '[]interface{}',
    'object': 'map[string]interface{}',
    'dict': 'map[string]interface{}',
    'any': 'interface{}',
    '*': 'interface{}',
    'function': 'func()',
    'callable': 'func()',
    'none': '',
    'null': 'nil',
}


def erk_type_to_go(erk_type: str) -> str:
    """Convertit un type ERK en type Go"""
    return TYPE_MAP.get(erk_type.lower(), 'interface{}')


def to_pascal_case(name: str) -> str:
    """Convertit en PascalCase (Go exported)"""
    if '_' in name:
        # snake_case → PascalCase
        return ''.join(word.capitalize() for word in name.split('_'))
    # camelCase → PascalCase
    return name[0].upper() + name[1:] if name else name


def to_camel_case(name: str) -> str:
    """Convertit en camelCase (Go unexported)"""
    pascal = to_pascal_case(name)
    return pascal[0].lower() + pascal[1:] if pascal else pascal


# =============================================================================
# CODE GENERATOR
# =============================================================================

class GoGenerator:
    """Génère du code Go à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code Go complet"""
        lines = []
        
        # Header comment
        lines.extend(self._generate_header())
        lines.append("")
        
        # Package
        package = self.options.get('package', 'main')
        lines.append(f"package {package}")
        lines.append("")
        
        # Imports
        lines.extend(self._generate_imports())
        lines.append("")
        
        # Types
        lines.extend(self._generate_types())
        lines.append("")
        
        # Struct ou fonctions
        if self.options.get('struct_name'):
            lines.extend(self._generate_struct())
        else:
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            "// EURKAI - Generated Go Code",
            f"// Source: {source}",
            f"// Generated: {datetime.now().isoformat()}",
            f"// Methods: {len(self.methods)}",
        ]
    
    def _generate_imports(self) -> List[str]:
        """Génère les imports Go"""
        imports = ['errors', 'fmt']
        
        # Ajouter context si async
        has_async = any(
            m.attributes.get('isAsync') or m.attributes.get('async')
            for m in self.methods
        )
        if has_async:
            imports.append('context')
        
        lines = ['import (']
        for imp in sorted(imports):
            lines.append(f'\t"{imp}"')
        lines.append(')')
        
        return lines
    
    def _generate_types(self) -> List[str]:
        """Génère les types Go"""
        return [
            "// CentralMethod represents GEVR operation types",
            "type CentralMethod string",
            "",
            "const (",
            '\tCreate    CentralMethod = "Create"',
            '\tRead      CentralMethod = "Read"',
            '\tUpdate    CentralMethod = "Update"',
            '\tDelete    CentralMethod = "Delete"',
            '\tRender    CentralMethod = "Render"',
            '\tValidate  CentralMethod = "Validate"',
            '\tTransform CentralMethod = "Transform"',
            '\tExecute   CentralMethod = "Execute"',
            ")",
            "",
            "// Context holds execution context",
            "type Context map[string]interface{}",
        ]
    
    def _generate_function(self, method: ERKObject, receiver: str = "") -> List[str]:
        """Génère une fonction Go"""
        lines = []
        attrs = method.attributes
        
        name = to_pascal_case(method.name)  # Go exported
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        central_method = attrs.get('centralMethod', 'Execute')
        return_type = erk_type_to_go(attrs.get('returnType', attrs.get('returns', 'any')))
        
        # Documentation
        lines.append(f"// {name} - {description}")
        lines.append(f"// CentralMethod: {central_method}")
        
        # Construire signature
        param_parts = []
        for param in (params if isinstance(params, list) else []):
            if isinstance(param, str):
                param_name = to_camel_case(param)
                param_type = attrs.get(f'param_{param}_type', 'any')
            else:
                param_name = to_camel_case(param.get('name', 'arg'))
                param_type = param.get('type', 'any')
            
            go_type = erk_type_to_go(param_type)
            param_parts.append(f"{param_name} {go_type}")
        
        params_str = ', '.join(param_parts)
        
        # Return type (Go idiom: return value + error)
        if return_type and return_type != '':
            return_sig = f"({return_type}, error)"
        else:
            return_sig = "error"
        
        # Fonction avec ou sans receiver
        if receiver:
            lines.append(f"func (s *{receiver}) {name}({params_str}) {return_sig} {{")
        else:
            lines.append(f"func {name}({params_str}) {return_sig} {{")
        
        # Body template
        if central_method == 'Create':
            lines.append(f"\t// Create logic")
            lines.append(f"\tresult := make(map[string]interface{{}})")
            lines.append(f"\t_ = result // TODO: implement")
            if return_type:
                lines.append(f"\treturn result, nil")
            else:
                lines.append(f"\treturn nil")
        elif central_method == 'Read':
            lines.append(f"\t// Read logic")
            if return_type:
                lines.append(f"\treturn nil, nil")
            else:
                lines.append(f"\treturn nil")
        elif central_method == 'Update':
            lines.append(f"\t// Update logic")
            if return_type:
                lines.append(f"\treturn true, nil")
            else:
                lines.append(f"\treturn nil")
        elif central_method == 'Delete':
            lines.append(f"\t// Delete logic")
            if return_type:
                lines.append(f"\treturn true, nil")
            else:
                lines.append(f"\treturn nil")
        elif central_method == 'Render':
            lines.append(f"\t// Render logic")
            lines.append(f'\thtml := ""')
            if return_type:
                lines.append(f"\treturn html, nil")
            else:
                lines.append(f"\treturn nil")
        elif central_method == 'Validate':
            lines.append(f"\t// Validation logic")
            if return_type:
                lines.append(f"\treturn true, nil")
            else:
                lines.append(f"\treturn nil")
        else:
            lines.append(f"\t// Execute logic")
            lines.append(f'\treturn nil, errors.New("not implemented: {name}")')
        
        lines.append("}")
        
        return lines
    
    def _generate_struct(self) -> List[str]:
        """Génère un struct avec méthodes"""
        lines = []
        struct_name = self.options.get('struct_name', 'Service')
        
        # Struct definition
        lines.append(f"// {struct_name} provides ERK method implementations")
        lines.append(f"type {struct_name} struct {{")
        lines.append("\tctx Context")
        lines.append("}")
        lines.append("")
        
        # Constructor
        lines.append(f"// New{struct_name} creates a new {struct_name} instance")
        lines.append(f"func New{struct_name}(ctx Context) *{struct_name} {{")
        lines.append(f"\tif ctx == nil {{")
        lines.append(f"\t\tctx = make(Context)")
        lines.append(f"\t}}")
        lines.append(f"\treturn &{struct_name}{{ctx: ctx}}")
        lines.append("}")
        lines.append("")
        
        # Methods
        for method in self.methods:
            lines.extend(self._generate_function(method, struct_name))
            lines.append("")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to Go Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_go.py methods.s.gev                    # Package main
  python erk_to_go.py methods.s.gev -o methods.go      # Save to file
  python erk_to_go.py methods.s.gev --package myapp    # Custom package
  python erk_to_go.py methods.s.gev --struct Service   # Struct with methods
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--package', default='main', help='Go package name')
    parser.add_argument('--struct', dest='struct_name', help='Generate struct with methods')
    parser.add_argument('--filter', help='Filter by centralMethod')
    
    args = parser.parse_args()
    
    objects = parse_gev_file(args.file)
    
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        objects = [o for o in objects 
                   if o.attributes.get('centralMethod', 'Execute') in allowed]
    
    options = {
        'package': args.package,
        'struct_name': args.struct_name,
    }
    
    generator = GoGenerator(objects, options)
    output = generator.generate()
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        methods = filter_by_type(objects, 'Method')
        print(f"✅ Generated {args.output} ({len(methods)} methods)")
    else:
        print(output)


if __name__ == '__main__':
    main()
