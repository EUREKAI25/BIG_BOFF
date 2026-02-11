#!/usr/bin/env python3
"""
EURKAI - ERK to Rust Converter
================================
Génère du code Rust à partir d'objets ERK Method.

Usage:
    python erk_to_rust.py methods.s.gev -o methods.rs
    python erk_to_rust.py methods.s.gev --impl MyStruct
    python erk_to_rust.py methods.s.gev --trait MyTrait

Output:
    - Fonctions Rust avec documentation
    - Impl block ou trait si demandé
    - Types Rust idiomatiques avec Result
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → Rust
# =============================================================================

TYPE_MAP = {
    'string': 'String',
    'str': '&str',
    'number': 'f64',
    'int': 'i64',
    'float': 'f64',
    'boolean': 'bool',
    'bool': 'bool',
    'array': 'Vec<Value>',
    'list': 'Vec<Value>',
    'object': 'HashMap<String, Value>',
    'dict': 'HashMap<String, Value>',
    'any': 'Value',
    '*': 'Value',
    'function': 'fn()',
    'callable': 'fn()',
    'none': '()',
    'null': 'Option<Value>',
}


def erk_type_to_rust(erk_type: str) -> str:
    """Convertit un type ERK en type Rust"""
    return TYPE_MAP.get(erk_type.lower(), 'Value')


def to_snake_case(name: str) -> str:
    """Convertit en snake_case (Rust convention)"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# =============================================================================
# CODE GENERATOR
# =============================================================================

class RustGenerator:
    """Génère du code Rust à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.methods = filter_by_type(objects, 'Method')
        
    def generate(self) -> str:
        """Génère le code Rust complet"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Imports
        lines.extend(self._generate_imports())
        lines.append("")
        
        # Types
        lines.extend(self._generate_types())
        lines.append("")
        
        # Trait, impl ou fonctions
        if self.options.get('trait_name'):
            lines.extend(self._generate_trait())
        elif self.options.get('impl_name'):
            lines.extend(self._generate_impl())
        else:
            for method in self.methods:
                lines.extend(self._generate_function(method))
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            "//! EURKAI - Generated Rust Code",
            f"//! Source: {source}",
            f"//! Generated: {datetime.now().isoformat()}",
            f"//! Methods: {len(self.methods)}",
        ]
    
    def _generate_imports(self) -> List[str]:
        """Génère les imports Rust"""
        return [
            "use std::collections::HashMap;",
            "use serde_json::Value;",
            "use thiserror::Error;",
        ]
    
    def _generate_types(self) -> List[str]:
        """Génère les types Rust"""
        return [
            "/// GEVR Central Method types",
            "#[derive(Debug, Clone, Copy, PartialEq, Eq)]",
            "pub enum CentralMethod {",
            "    Create,",
            "    Read,",
            "    Update,",
            "    Delete,",
            "    Render,",
            "    Validate,",
            "    Transform,",
            "    Execute,",
            "}",
            "",
            "/// ERK Error type",
            "#[derive(Error, Debug)]",
            "pub enum ErkError {",
            '    #[error("Not implemented: {0}")]',
            "    NotImplemented(String),",
            '    #[error("Execution error: {0}")]',
            "    ExecutionError(String),",
            "}",
            "",
            "/// Result type alias",
            "pub type ErkResult<T> = Result<T, ErkError>;",
            "",
            "/// Execution context",
            "pub type Context = HashMap<String, Value>;",
        ]
    
    def _generate_function(self, method: ERKObject, is_method: bool = False) -> List[str]:
        """Génère une fonction Rust"""
        lines = []
        attrs = method.attributes
        
        name = to_snake_case(method.name)
        description = attrs.get('description', f'Method {name}')
        params = attrs.get('params', [])
        central_method = attrs.get('centralMethod', 'Execute')
        return_type = erk_type_to_rust(attrs.get('returnType', attrs.get('returns', 'any')))
        is_async = attrs.get('isAsync', False) or attrs.get('async', False)
        
        # Documentation
        lines.append(f"/// {description}")
        lines.append(f"///")
        lines.append(f"/// # CentralMethod")
        lines.append(f"/// `{central_method}`")
        
        # Construire signature
        param_parts = []
        if is_method:
            param_parts.append("&self")
        
        for param in (params if isinstance(params, list) else []):
            if isinstance(param, str):
                param_name = to_snake_case(param)
                param_type = attrs.get(f'param_{param}_type', 'any')
            else:
                param_name = to_snake_case(param.get('name', 'arg'))
                param_type = param.get('type', 'any')
            
            rust_type = erk_type_to_rust(param_type)
            param_parts.append(f"{param_name}: {rust_type}")
        
        params_str = ', '.join(param_parts)
        
        # Async
        async_keyword = "async " if is_async else ""
        
        # Visibility
        pub_keyword = "pub " if not is_method else ""
        
        lines.append(f"{pub_keyword}{async_keyword}fn {name}({params_str}) -> ErkResult<{return_type}> {{")
        
        # Body template
        if central_method == 'Create':
            lines.append(f"    // Create logic")
            lines.append(f"    let result = HashMap::new();")
            lines.append(f"    Ok(Value::Object(result.into()))")
        elif central_method == 'Read':
            lines.append(f"    // Read logic")
            lines.append(f"    Ok(Value::Null)")
        elif central_method == 'Update':
            lines.append(f"    // Update logic")
            lines.append(f"    Ok(Value::Bool(true))")
        elif central_method == 'Delete':
            lines.append(f"    // Delete logic")
            lines.append(f"    Ok(Value::Bool(true))")
        elif central_method == 'Render':
            lines.append(f"    // Render logic")
            lines.append(f'    let html = String::new();')
            lines.append(f"    Ok(Value::String(html))")
        elif central_method == 'Validate':
            lines.append(f"    // Validation logic")
            lines.append(f"    Ok(Value::Bool(true))")
        else:
            lines.append(f'    Err(ErkError::NotImplemented("{name}".to_string()))')
        
        lines.append("}")
        
        return lines
    
    def _generate_trait(self) -> List[str]:
        """Génère un trait Rust"""
        lines = []
        trait_name = self.options.get('trait_name', 'ErkMethods')
        
        lines.append(f"/// ERK Methods trait")
        lines.append(f"pub trait {trait_name} {{")
        
        for method in self.methods:
            attrs = method.attributes
            name = to_snake_case(method.name)
            params = attrs.get('params', [])
            return_type = erk_type_to_rust(attrs.get('returnType', 'any'))
            is_async = attrs.get('isAsync', False)
            
            # Params
            param_parts = ["&self"]
            for param in (params if isinstance(params, list) else []):
                if isinstance(param, str):
                    param_name = to_snake_case(param)
                    param_type = attrs.get(f'param_{param}_type', 'any')
                else:
                    param_name = to_snake_case(param.get('name', 'arg'))
                    param_type = param.get('type', 'any')
                rust_type = erk_type_to_rust(param_type)
                param_parts.append(f"{param_name}: {rust_type}")
            
            params_str = ', '.join(param_parts)
            async_kw = "async " if is_async else ""
            
            lines.append(f"    {async_kw}fn {name}({params_str}) -> ErkResult<{return_type}>;")
        
        lines.append("}")
        
        return lines
    
    def _generate_impl(self) -> List[str]:
        """Génère un impl block"""
        lines = []
        impl_name = self.options.get('impl_name', 'ErkService')
        
        # Struct definition
        lines.append(f"/// ERK Service implementation")
        lines.append(f"pub struct {impl_name} {{")
        lines.append("    ctx: Context,")
        lines.append("}")
        lines.append("")
        
        # Impl block
        lines.append(f"impl {impl_name} {{")
        
        # Constructor
        lines.append("    /// Create new instance")
        lines.append("    pub fn new(ctx: Context) -> Self {")
        lines.append(f"        Self {{ ctx }}")
        lines.append("    }")
        lines.append("")
        
        # Methods
        for method in self.methods:
            method_lines = self._generate_function(method, is_method=True)
            for line in method_lines:
                lines.append(f"    {line}")
            lines.append("")
        
        lines.append("}")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to Rust Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_rust.py methods.s.gev                  # Functions
  python erk_to_rust.py methods.s.gev -o methods.rs    # Save to file
  python erk_to_rust.py methods.s.gev --impl Service   # Impl block
  python erk_to_rust.py methods.s.gev --trait Methods  # Trait definition
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--impl', dest='impl_name', help='Generate impl block')
    parser.add_argument('--trait', dest='trait_name', help='Generate trait')
    parser.add_argument('--filter', help='Filter by centralMethod')
    
    args = parser.parse_args()
    
    objects = parse_gev_file(args.file)
    
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        objects = [o for o in objects 
                   if o.attributes.get('centralMethod', 'Execute') in allowed]
    
    options = {
        'impl_name': args.impl_name,
        'trait_name': args.trait_name,
    }
    
    generator = RustGenerator(objects, options)
    output = generator.generate()
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        methods = filter_by_type(objects, 'Method')
        print(f"✅ Generated {args.output} ({len(methods)} methods)")
    else:
        print(output)


if __name__ == '__main__':
    main()
