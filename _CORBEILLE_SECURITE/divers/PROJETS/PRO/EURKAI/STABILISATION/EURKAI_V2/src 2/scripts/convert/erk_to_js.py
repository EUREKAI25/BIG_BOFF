#!/usr/bin/env python3
"""
EURKAI - ERK to JavaScript Converter
======================================
Génère du code JavaScript à partir d'objets ERK Method.

Usage:
    python erk_to_js.py methods.s.gev -o output.js
    python erk_to_js.py methods.s.gev --module  # Format ES6 module
    python erk_to_js.py methods.s.gev --class   # Encapsulé dans une classe

Output:
    - Fonctions JS avec JSDoc
    - Exports (module.exports ou export)
    - Structure GEVR si spécifiée
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import du parser ERK
from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → JS
# =============================================================================

TYPE_MAP = {
    'string': 'string',
    'str': 'string',
    'number': 'number',
    'int': 'number',
    'float': 'number',
    'boolean': 'boolean',
    'bool': 'boolean',
    'array': 'Array',
    'list': 'Array',
    'object': 'Object',
    'dict': 'Object',
    'any': '*',
    'function': 'Function',
    'callable': 'Function',
}


def erk_type_to_js(erk_type: str) -> str:
    """Convertit un type ERK en type JSDoc"""
    return TYPE_MAP.get(erk_type.lower(), erk_type)


# =============================================================================
# CODE GENERATOR
# =============================================================================

class JSGenerator:
    """Génère du code JavaScript à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code JS complet"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Imports si nécessaire
        if self.options.get('imports'):
            lines.extend(self._generate_imports())
            lines.append("")
        
        # Classe wrapper si demandé
        if self.options.get('class_name'):
            lines.extend(self._generate_class())
        else:
            # Fonctions standalone
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
            
            # Exports
            lines.extend(self._generate_exports())
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header du fichier"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            "/**",
            " * EURKAI - Generated JavaScript",
            f" * Source: {source}",
            f" * Generated: {datetime.now().isoformat()}",
            f" * Methods: {len(self.methods)}",
            " */",
            "",
            "'use strict';",
        ]
    
    def _generate_imports(self) -> List[str]:
        """Génère les imports"""
        lines = []
        imports = self.options.get('imports', {})
        
        for module, items in imports.items():
            if isinstance(items, list):
                items_str = ', '.join(items)
                lines.append(f"const {{ {items_str} }} = require('{module}');")
            else:
                lines.append(f"const {items} = require('{module}');")
        
        return lines
    
    def _generate_function(self, method: ERKObject, indent: str = "") -> List[str]:
        """Génère une fonction JS"""
        lines = []
        attrs = method.attributes
        
        name = method.name
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        is_async = attrs.get('isAsync', False) or attrs.get('async', False)
        central_method = attrs.get('centralMethod', 'Execute')
        
        # JSDoc
        lines.append(f"{indent}/**")
        lines.append(f"{indent} * {description}")
        lines.append(f"{indent} * @centralMethod {central_method}")
        
        # Params dans JSDoc
        if isinstance(params, list):
            for param in params:
                if isinstance(param, str):
                    param_name = param
                    param_type = attrs.get(f'param_{param}_type', 'any')
                else:
                    param_name = param.get('name', 'arg')
                    param_type = param.get('type', 'any')
                
                js_type = erk_type_to_js(param_type)
                lines.append(f"{indent} * @param {{{js_type}}} {param_name}")
        
        # Return type
        return_type = attrs.get('returnType', attrs.get('returns', '*'))
        lines.append(f"{indent} * @returns {{{erk_type_to_js(return_type)}}}")
        lines.append(f"{indent} */")
        
        # Signature
        async_keyword = "async " if is_async else ""
        params_str = ', '.join(params) if isinstance(params, list) else ""
        lines.append(f"{indent}{async_keyword}function {name}({params_str}) {{")
        
        # Body
        if 'code' in attrs:
            # Code existant
            code_lines = attrs['code'].split('\n')
            for code_line in code_lines:
                lines.append(f"{indent}    {code_line}")
        else:
            # Placeholder
            lines.append(f"{indent}    // TODO: Implement {name}")
            lines.append(f"{indent}    // CentralMethod: {central_method}")
            
            # Générer un template basé sur centralMethod
            if central_method == 'Create':
                lines.append(f"{indent}    const newObj = {{}};")
                lines.append(f"{indent}    // Create logic here")
                lines.append(f"{indent}    return newObj;")
            elif central_method == 'Read':
                lines.append(f"{indent}    // Read logic here")
                lines.append(f"{indent}    return null;")
            elif central_method == 'Update':
                lines.append(f"{indent}    // Update logic here")
                lines.append(f"{indent}    return true;")
            elif central_method == 'Delete':
                lines.append(f"{indent}    // Delete logic here")
                lines.append(f"{indent}    return true;")
            elif central_method == 'Render':
                lines.append(f"{indent}    let html = '';")
                lines.append(f"{indent}    // Render logic here")
                lines.append(f"{indent}    return html;")
            elif central_method == 'Validate':
                lines.append(f"{indent}    // Validation logic here")
                lines.append(f"{indent}    return true;")
            elif central_method == 'Transform':
                lines.append(f"{indent}    // Transform logic here")
                lines.append(f"{indent}    return null;")
            else:
                lines.append(f"{indent}    // Execute logic here")
        
        lines.append(f"{indent}}}")
        
        return lines
    
    def _generate_class(self) -> List[str]:
        """Génère une classe englobante"""
        lines = []
        class_name = self.options.get('class_name', 'ERKMethods')
        
        lines.append(f"class {class_name} {{")
        lines.append("")
        
        # Constructor
        lines.append("    constructor(context = {}) {")
        lines.append("        this.context = context;")
        lines.append("    }")
        lines.append("")
        
        # Methods
        for method in self.methods:
            # Adapter pour méthode de classe
            method_lines = self._generate_function(method, "    ")
            # Remplacer "function name" par "name" pour syntaxe classe
            for i, line in enumerate(method_lines):
                if 'function ' in line:
                    method_lines[i] = line.replace('function ', '').replace('async ', 'async ')
            lines.extend(method_lines)
            lines.append("")
        
        lines.append("}")
        lines.append("")
        
        # Export
        if self.options.get('module'):
            lines.append(f"export default {class_name};")
        else:
            lines.append(f"module.exports = {class_name};")
        
        return lines
    
    def _generate_exports(self) -> List[str]:
        """Génère les exports"""
        lines = []
        method_names = [m.name for m in self.methods]
        
        if not method_names:
            return lines
        
        if self.options.get('module'):
            # ES6 exports
            lines.append("")
            lines.append("export {")
            for name in method_names:
                lines.append(f"    {name},")
            lines.append("};")
        else:
            # CommonJS exports
            lines.append("")
            lines.append("module.exports = {")
            for name in method_names:
                lines.append(f"    {name},")
            lines.append("};")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to JavaScript Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_js.py methods.s.gev                    # CommonJS output
  python erk_to_js.py methods.s.gev -o methods.js      # Save to file
  python erk_to_js.py methods.s.gev --module           # ES6 module
  python erk_to_js.py methods.s.gev --class MyClass    # Class wrapper
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--module', action='store_true', help='Generate ES6 module')
    parser.add_argument('--class', dest='class_name', help='Wrap in class with given name')
    parser.add_argument('--filter', help='Filter by centralMethod (e.g., Render,Execute)')
    
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
        'module': args.module,
        'class_name': args.class_name,
    }
    
    # Generate
    generator = JSGenerator(objects, options)
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
