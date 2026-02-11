#!/usr/bin/env python3
"""
EURKAI - ERK to TypeScript Converter
======================================
Génère du code TypeScript à partir d'objets ERK Method.

Usage:
    python erk_to_ts.py methods.s.gev -o output.ts
    python erk_to_ts.py methods.s.gev --interface      # Génère aussi les interfaces
    python erk_to_ts.py methods.s.gev --class MyClass  # Encapsulé dans une classe

Output:
    - Fonctions TypeScript avec types stricts
    - Interfaces pour les paramètres complexes
    - Support async/await
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → TypeScript
# =============================================================================

TYPE_MAP = {
    'string': 'string',
    'str': 'string',
    'number': 'number',
    'int': 'number',
    'float': 'number',
    'boolean': 'boolean',
    'bool': 'boolean',
    'array': 'any[]',
    'list': 'any[]',
    'object': 'Record<string, any>',
    'dict': 'Record<string, any>',
    'any': 'any',
    '*': 'any',
    'function': 'Function',
    'callable': 'Function',
    'none': 'void',
    'null': 'null',
    'undefined': 'undefined',
}


def erk_type_to_ts(erk_type: str) -> str:
    """Convertit un type ERK en type TypeScript"""
    return TYPE_MAP.get(erk_type.lower(), erk_type)


# =============================================================================
# CODE GENERATOR
# =============================================================================

class TypeScriptGenerator:
    """Génère du code TypeScript à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code TypeScript complet"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Interfaces si demandé
        if self.options.get('interfaces'):
            lines.extend(self._generate_interfaces())
            lines.append("")
        
        # Types pour CentralMethod
        lines.extend(self._generate_central_method_type())
        lines.append("")
        
        # Classe ou fonctions
        if self.options.get('class_name'):
            lines.extend(self._generate_class())
        else:
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
            
            lines.extend(self._generate_exports())
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            "/**",
            " * EURKAI - Generated TypeScript",
            f" * Source: {source}",
            f" * Generated: {datetime.now().isoformat()}",
            f" * Methods: {len(self.methods)}",
            " */",
            "",
        ]
    
    def _generate_central_method_type(self) -> List[str]:
        """Génère le type enum pour CentralMethod"""
        return [
            "/** GEVR Central Methods */",
            "export type CentralMethod = 'Create' | 'Read' | 'Update' | 'Delete' | 'Render' | 'Validate' | 'Transform' | 'Execute';",
        ]
    
    def _generate_interfaces(self) -> List[str]:
        """Génère les interfaces pour les contextes"""
        return [
            "/** Execution context */",
            "export interface ERKContext {",
            "    store?: Record<string, any>;",
            "    currentObject?: Record<string, any>;",
            "    parentObject?: Record<string, any>;",
            "    [key: string]: any;",
            "}",
            "",
            "/** Method metadata */",
            "export interface ERKMethodMeta {",
            "    name: string;",
            "    centralMethod: CentralMethod;",
            "    params: string[];",
            "    async: boolean;",
            "}",
        ]
    
    def _generate_function(self, method: ERKObject, indent: str = "") -> List[str]:
        """Génère une fonction TypeScript"""
        lines = []
        attrs = method.attributes
        
        name = method.name
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        is_async = attrs.get('isAsync', False) or attrs.get('async', False)
        central_method = attrs.get('centralMethod', 'Execute')
        return_type = erk_type_to_ts(attrs.get('returnType', attrs.get('returns', 'any')))
        
        # JSDoc
        lines.append(f"{indent}/**")
        lines.append(f"{indent} * {description}")
        lines.append(f"{indent} * @centralMethod {central_method}")
        
        if isinstance(params, list):
            for param in params:
                if isinstance(param, str):
                    param_name = param
                    param_type = attrs.get(f'param_{param}_type', 'any')
                else:
                    param_name = param.get('name', 'arg')
                    param_type = param.get('type', 'any')
                
                ts_type = erk_type_to_ts(param_type)
                lines.append(f"{indent} * @param {param_name} - {ts_type}")
        
        lines.append(f"{indent} * @returns {return_type}")
        lines.append(f"{indent} */")
        
        # Construire signature
        param_parts = []
        for param in (params if isinstance(params, list) else []):
            if isinstance(param, str):
                param_name = param
                param_type = attrs.get(f'param_{param}_type', 'any')
                param_default = attrs.get(f'param_{param}_default')
            else:
                param_name = param.get('name', 'arg')
                param_type = param.get('type', 'any')
                param_default = param.get('default')
            
            ts_type = erk_type_to_ts(param_type)
            
            if param_default is not None:
                param_parts.append(f"{param_name}: {ts_type} = {param_default}")
            else:
                param_parts.append(f"{param_name}: {ts_type}")
        
        params_str = ', '.join(param_parts)
        
        # Fonction
        async_keyword = "async " if is_async else ""
        promise_wrap = f"Promise<{return_type}>" if is_async else return_type
        
        export_keyword = "export " if not self.options.get('class_name') else ""
        lines.append(f"{indent}{export_keyword}{async_keyword}function {name}({params_str}): {promise_wrap} {{")
        
        # Body template
        lines.append(f"{indent}    // CentralMethod: {central_method}")
        
        if central_method == 'Create':
            lines.append(f"{indent}    const result: Record<string, any> = {{}};")
            lines.append(f"{indent}    // Create logic")
            lines.append(f"{indent}    return result as {return_type};")
        elif central_method == 'Read':
            lines.append(f"{indent}    // Read logic")
            lines.append(f"{indent}    return null as {return_type};")
        elif central_method == 'Update':
            lines.append(f"{indent}    // Update logic")
            lines.append(f"{indent}    return true as unknown as {return_type};")
        elif central_method == 'Delete':
            lines.append(f"{indent}    // Delete logic")
            lines.append(f"{indent}    return true as unknown as {return_type};")
        elif central_method == 'Render':
            lines.append(f"{indent}    let html = '';")
            lines.append(f"{indent}    // Render logic")
            lines.append(f"{indent}    return html as {return_type};")
        elif central_method == 'Validate':
            lines.append(f"{indent}    // Validation logic")
            lines.append(f"{indent}    return true as unknown as {return_type};")
        else:
            lines.append(f"{indent}    // Execute logic")
            lines.append(f"{indent}    throw new Error('Not implemented: {name}');")
        
        lines.append(f"{indent}}}")
        
        return lines
    
    def _generate_class(self) -> List[str]:
        """Génère une classe TypeScript"""
        lines = []
        class_name = self.options.get('class_name', 'ERKMethods')
        
        lines.append(f"export class {class_name} {{")
        lines.append("    private context: ERKContext;")
        lines.append("")
        lines.append("    constructor(context: ERKContext = {}) {")
        lines.append("        this.context = context;")
        lines.append("    }")
        lines.append("")
        
        for method in self.methods:
            # Adapter pour méthode de classe (public, sans function keyword)
            func_lines = self._generate_function(method, "    ")
            for i, line in enumerate(func_lines):
                # Remplacer "export function" par "public"
                if 'export function' in line:
                    func_lines[i] = line.replace('export function', 'public')
                elif 'export async function' in line:
                    func_lines[i] = line.replace('export async function', 'public async')
            lines.extend(func_lines)
            lines.append("")
        
        lines.append("}")
        
        return lines
    
    def _generate_exports(self) -> List[str]:
        """Génère la liste des exports (déjà inline avec export keyword)"""
        return []  # Les fonctions sont déjà exportées individuellement


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to TypeScript Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_ts.py methods.s.gev                    # Standard output
  python erk_to_ts.py methods.s.gev -o methods.ts      # Save to file
  python erk_to_ts.py methods.s.gev --class MyClass    # Class wrapper
  python erk_to_ts.py methods.s.gev --interfaces       # Include interfaces
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--class', dest='class_name', help='Wrap in class')
    parser.add_argument('--interfaces', action='store_true', help='Generate interfaces')
    parser.add_argument('--filter', help='Filter by centralMethod')
    
    args = parser.parse_args()
    
    objects = parse_gev_file(args.file)
    
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        objects = [o for o in objects 
                   if o.attributes.get('centralMethod', 'Execute') in allowed]
    
    options = {
        'class_name': args.class_name,
        'interfaces': args.interfaces or args.class_name,
    }
    
    generator = TypeScriptGenerator(objects, options)
    output = generator.generate()
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        methods = filter_by_type(objects, 'Method')
        print(f"✅ Generated {args.output} ({len(methods)} methods)")
    else:
        print(output)


if __name__ == '__main__':
    main()
