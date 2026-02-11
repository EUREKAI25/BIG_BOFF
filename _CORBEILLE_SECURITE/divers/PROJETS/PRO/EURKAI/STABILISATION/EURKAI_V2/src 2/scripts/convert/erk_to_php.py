#!/usr/bin/env python3
"""
EURKAI - ERK to PHP Converter
===============================
Génère du code PHP à partir d'objets ERK Method.

Usage:
    python erk_to_php.py methods.s.gev -o output.php
    python erk_to_php.py methods.s.gev --class MyClass   # Classe PHP
    python erk_to_php.py methods.s.gev --namespace App   # Avec namespace

Output:
    - Fonctions PHP avec PHPDoc
    - Classes PSR-4 compatible
    - Type hints PHP 8+
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import du parser ERK
from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → PHP
# =============================================================================

TYPE_MAP = {
    'string': 'string',
    'str': 'string',
    'number': 'float',
    'int': 'int',
    'float': 'float',
    'boolean': 'bool',
    'bool': 'bool',
    'array': 'array',
    'list': 'array',
    'object': 'object',
    'dict': 'array',
    'any': 'mixed',
    '*': 'mixed',
    'function': 'callable',
    'callable': 'callable',
    'none': 'void',
    'null': 'null',
}


def erk_type_to_php(erk_type: str) -> str:
    """Convertit un type ERK en type PHP"""
    return TYPE_MAP.get(erk_type.lower(), erk_type)


def to_camel_case(name: str) -> str:
    """S'assure que le nom est en camelCase"""
    # Si déjà camelCase, retourner tel quel
    if '_' not in name:
        return name
    # snake_case → camelCase
    parts = name.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


# =============================================================================
# CODE GENERATOR
# =============================================================================

class PHPGenerator:
    """Génère du code PHP à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code PHP complet"""
        lines = []
        
        # PHP opening
        lines.append("<?php")
        lines.append("")
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Namespace
        namespace = self.options.get('namespace')
        if namespace:
            lines.append(f"namespace {namespace};")
            lines.append("")
        
        # Declare strict
        if self.options.get('strict', True):
            lines.append("declare(strict_types=1);")
            lines.append("")
        
        # Classe ou fonctions
        if self.options.get('class_name'):
            lines.extend(self._generate_class())
        else:
            # Fonctions standalone
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header du fichier"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            "/**",
            " * EURKAI - Generated PHP",
            f" * Source: {source}",
            f" * Generated: {datetime.now().isoformat()}",
            f" * Methods: {len(self.methods)}",
            " */",
        ]
    
    def _generate_function(self, method: ERKObject, indent: str = "", 
                          visibility: str = "") -> List[str]:
        """Génère une fonction PHP"""
        lines = []
        attrs = method.attributes
        
        name = to_camel_case(method.name)
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        central_method = attrs.get('centralMethod', 'Execute')
        return_type = erk_type_to_php(attrs.get('returnType', attrs.get('returns', 'mixed')))
        
        # PHPDoc
        lines.append(f"{indent}/**")
        lines.append(f"{indent} * {description}")
        lines.append(f"{indent} *")
        lines.append(f"{indent} * @centralMethod {central_method}")
        
        # Params dans PHPDoc
        if isinstance(params, list):
            for param in params:
                if isinstance(param, str):
                    param_name = param
                    param_type = attrs.get(f'param_{param}_type', 'mixed')
                else:
                    param_name = param.get('name', 'arg')
                    param_type = param.get('type', 'mixed')
                
                php_type = erk_type_to_php(param_type)
                lines.append(f"{indent} * @param {php_type} ${param_name}")
        
        lines.append(f"{indent} * @return {return_type}")
        lines.append(f"{indent} */")
        
        # Construire la signature
        param_parts = []
        for param in (params if isinstance(params, list) else []):
            if isinstance(param, str):
                param_name = param
                param_type = attrs.get(f'param_{param}_type', 'mixed')
                param_default = attrs.get(f'param_{param}_default')
            else:
                param_name = param.get('name', 'arg')
                param_type = param.get('type', 'mixed')
                param_default = param.get('default')
            
            php_type = erk_type_to_php(param_type)
            
            if param_default is not None:
                # Convertir default JS → PHP
                if param_default in ('null', 'undefined'):
                    param_default = 'null'
                elif param_default == 'true':
                    param_default = 'true'
                elif param_default == 'false':
                    param_default = 'false'
                elif param_default == '{}':
                    param_default = '[]'
                elif param_default == '[]':
                    param_default = '[]'
                param_parts.append(f"{php_type} ${param_name} = {param_default}")
            else:
                param_parts.append(f"{php_type} ${param_name}")
        
        params_str = ', '.join(param_parts)
        
        # Définition
        func_keyword = f"{visibility} function" if visibility else "function"
        lines.append(f"{indent}{func_keyword} {name}({params_str}): {return_type}")
        lines.append(f"{indent}{{")
        
        # Body - template basé sur centralMethod
        if central_method == 'Create':
            lines.append(f"{indent}    // Create logic")
            lines.append(f"{indent}    $result = [];")
            lines.append(f"{indent}    return $result;")
        elif central_method == 'Read':
            lines.append(f"{indent}    // Read logic")
            lines.append(f"{indent}    return null;")
        elif central_method == 'Update':
            lines.append(f"{indent}    // Update logic")
            lines.append(f"{indent}    return true;")
        elif central_method == 'Delete':
            lines.append(f"{indent}    // Delete logic")
            lines.append(f"{indent}    return true;")
        elif central_method == 'Render':
            lines.append(f"{indent}    // Render logic")
            lines.append(f"{indent}    $html = '';")
            lines.append(f"{indent}    return $html;")
        elif central_method == 'Validate':
            lines.append(f"{indent}    // Validation logic")
            lines.append(f"{indent}    return true;")
        elif central_method == 'Transform':
            lines.append(f"{indent}    // Transform logic")
            lines.append(f"{indent}    return null;")
        else:
            lines.append(f"{indent}    // Execute logic")
            lines.append(f"{indent}    // TODO: Implement {name}")
        
        lines.append(f"{indent}}}")
        
        return lines
    
    def _generate_class(self) -> List[str]:
        """Génère une classe PHP"""
        lines = []
        class_name = self.options.get('class_name', 'ERKMethods')
        
        lines.append(f"class {class_name}")
        lines.append("{")
        
        # Propriété context
        lines.append("    /**")
        lines.append("     * @var array Context data")
        lines.append("     */")
        lines.append("    private array $context;")
        lines.append("")
        
        # Constructor
        lines.append("    /**")
        lines.append("     * Constructor")
        lines.append("     *")
        lines.append("     * @param array $context Initial context")
        lines.append("     */")
        lines.append("    public function __construct(array $context = [])")
        lines.append("    {")
        lines.append("        $this->context = $context;")
        lines.append("    }")
        lines.append("")
        
        # Methods
        for method in self.methods:
            lines.extend(self._generate_function(method, "    ", "public"))
            lines.append("")
        
        lines.append("}")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to PHP Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_php.py methods.s.gev                    # Functions output
  python erk_to_php.py methods.s.gev -o Methods.php     # Save to file
  python erk_to_php.py methods.s.gev --class MyClass    # Class wrapper
  python erk_to_php.py methods.s.gev --namespace App\\Services
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--class', dest='class_name', help='Generate class with given name')
    parser.add_argument('--namespace', help='PHP namespace')
    parser.add_argument('--no-strict', action='store_true', 
                       help='Disable strict_types declaration')
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
        'namespace': args.namespace,
        'strict': not args.no_strict,
    }
    
    # Generate
    generator = PHPGenerator(objects, options)
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
