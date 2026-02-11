#!/usr/bin/env python3
"""
EURKAI - JS → ERK Function Generator
======================================
Génère des objets ERK Method à partir de fonctions JavaScript.

Usage:
    python gen_erk_functions.py extension.js -o functions.s.gev
    python gen_erk_functions.py extension.js --format json

Le script produit des objets ERK de type:
    Object:Method:JSScript:FunctionName:
    .description = "..."
    .params = ["param1", "param2"]
    .code = "function body..."
    .centralMethod = Render|Execute|Create|Update|Delete|Read
"""

import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ERKParam:
    """Paramètre d'une fonction ERK"""
    name: str
    type: str = "any"
    required: bool = True
    default: Optional[str] = None

@dataclass
class ERKFunction:
    """Fonction ERK extraite du JS"""
    name: str
    lineage: str = ""
    description: str = ""
    params: List[ERKParam] = field(default_factory=list)
    code: str = ""
    centralMethod: str = "Execute"
    isAsync: bool = False
    dependencies: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)

# ============================================================================
# JS PARSER (simplifié)
# ============================================================================

class JSParser:
    """Parse JavaScript pour extraire les fonctions"""
    
    # Patterns de détection
    PATTERNS = {
        # function name(params) {
        'function_decl': re.compile(
            r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'
            r'(?P<async>async\s+)?function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{',
            re.MULTILINE
        ),
        # const name = (params) => {
        'arrow_func': re.compile(
            r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'
            r'(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s*)?\((?P<params>[^)]*)\)\s*=>\s*\{',
            re.MULTILINE
        ),
        # const name = function(params) {
        'func_expr': re.compile(
            r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'
            r'(?:const|let|var)\s+(?P<name>\w+)\s*=\s*(?P<async>async\s*)?function\s*\((?P<params>[^)]*)\)\s*\{',
            re.MULTILINE
        ),
        # JSDoc patterns
        'jsdoc_desc': re.compile(r'/\*\*\s*\n?\s*\*?\s*([^@\n*][^\n]*)', re.MULTILINE),
        'jsdoc_param': re.compile(r'@param\s+(?:{([^}]+)}\s+)?(\w+)(?:\s*-\s*(.*))?'),
        'jsdoc_returns': re.compile(r'@returns?\s+{([^}]+)}'),
        # Exports
        'window_export': re.compile(r'window\.(\w+)\s*=\s*(\w+)'),
        'module_export': re.compile(r'module\.exports(?:\.(\w+))?\s*='),
        'named_export': re.compile(r'export\s+(?:const|let|var|function|async\s+function)\s+(\w+)'),
        'export_list': re.compile(r'export\s*\{\s*([^}]+)\s*\}'),
        # Dependencies
        'global_call': re.compile(r'\b([A-Z][a-zA-Z0-9]*)\.\w+\s*\('),
        'require': re.compile(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'),
        'import': re.compile(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'),
    }
    
    # Mapping centralMethod basé sur le nom
    CENTRAL_METHOD_PATTERNS = {
        'Create': [r'^create', r'^add', r'^new', r'^insert', r'^generate'],
        'Read': [r'^get', r'^read', r'^fetch', r'^load', r'^find', r'^query', r'^list'],
        'Update': [r'^update', r'^set', r'^modify', r'^change', r'^edit', r'^replace'],
        'Delete': [r'^delete', r'^remove', r'^destroy', r'^clear'],
        'Render': [r'^render', r'^display', r'^show', r'^draw', r'^paint', r'^build.*html'],
        'Validate': [r'^validate', r'^check', r'^verify', r'^is[A-Z]', r'^has[A-Z]'],
        'Transform': [r'^transform', r'^convert', r'^parse', r'^format', r'^serialize'],
    }
    
    def __init__(self, source: str):
        self.source = source
        self.functions: List[ERKFunction] = []
        self.exports: set = set()
        self.dependencies: set = set()
        
    def parse(self) -> List[ERKFunction]:
        """Parse complet du fichier JS"""
        self._extract_exports()
        self._extract_dependencies()
        self._extract_functions()
        return self.functions
    
    def _extract_exports(self):
        """Extrait les exports"""
        # window.xxx = yyy
        for m in self.PATTERNS['window_export'].finditer(self.source):
            self.exports.add(m.group(2))
        
        # module.exports.xxx = 
        for m in self.PATTERNS['module_export'].finditer(self.source):
            if m.group(1):
                self.exports.add(m.group(1))
        
        # export function xxx / export const xxx
        for m in self.PATTERNS['named_export'].finditer(self.source):
            self.exports.add(m.group(1))
        
        # export { a, b, c }
        for m in self.PATTERNS['export_list'].finditer(self.source):
            for name in m.group(1).split(','):
                name = name.strip().split(' as ')[0].strip()
                if name:
                    self.exports.add(name)
    
    def _extract_dependencies(self):
        """Extrait les dépendances globales"""
        # Appels de type Store.xxx(), vscode.xxx()
        for m in self.PATTERNS['global_call'].finditer(self.source):
            cls = m.group(1)
            if cls not in ('Array', 'Object', 'JSON', 'Math', 'Date', 'String', 'Number', 
                          'Boolean', 'Map', 'Set', 'Promise', 'RegExp', 'Error'):
                self.dependencies.add(cls)
        
        # require('xxx')
        for m in self.PATTERNS['require'].finditer(self.source):
            self.dependencies.add(m.group(1))
        
        # import xxx from 'yyy'
        for m in self.PATTERNS['import'].finditer(self.source):
            self.dependencies.add(m.group(1))
    
    def _extract_functions(self):
        """Extrait toutes les fonctions"""
        # Collecter toutes les fonctions depuis tous les patterns
        all_matches = []
        
        for pattern_name in ['function_decl', 'arrow_func', 'func_expr']:
            pattern = self.PATTERNS[pattern_name]
            for m in pattern.finditer(self.source):
                all_matches.append((m.start(), m, pattern_name))
        
        # Trier par position
        all_matches.sort(key=lambda x: x[0])
        
        for _, match, pattern_name in all_matches:
            func = self._parse_function(match)
            if func:
                self.functions.append(func)
    
    def _parse_function(self, match) -> Optional[ERKFunction]:
        """Parse une fonction depuis un match regex"""
        name = match.group('name')
        params_raw = match.group('params')
        jsdoc_raw = match.group('jsdoc') or ""
        is_async = bool(match.group('async'))
        
        # Extraire le corps
        body_start = match.end() - 1
        body = self._extract_body(body_start)
        
        # Parser les paramètres
        params = self._parse_params(params_raw, jsdoc_raw)
        
        # Parser JSDoc
        description = self._extract_description(jsdoc_raw)
        
        # Déterminer le centralMethod
        central_method = self._detect_central_method(name)
        
        # Construire le lineage ERK
        lineage = f"Object:Method:JSScript:{name}:"
        
        # Est-ce exporté?
        is_exported = name in self.exports
        
        return ERKFunction(
            name=name,
            lineage=lineage,
            description=description or f"JavaScript function {name}",
            params=params,
            code=body,
            centralMethod=central_method,
            isAsync=is_async,
            dependencies=list(self.dependencies),
            exports=[name] if is_exported else []
        )
    
    def _extract_body(self, start_brace: int) -> str:
        """Extrait le corps en comptant les accolades"""
        depth = 1
        i = start_brace + 1
        while i < len(self.source) and depth > 0:
            char = self.source[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            # Ignorer les strings
            elif char in ('"', "'", '`'):
                quote = char
                i += 1
                while i < len(self.source):
                    if self.source[i] == '\\':
                        i += 2
                        continue
                    if self.source[i] == quote:
                        break
                    i += 1
            i += 1
        return self.source[start_brace:i]
    
    def _parse_params(self, params_raw: str, jsdoc: str) -> List[ERKParam]:
        """Parse les paramètres avec types depuis JSDoc"""
        params = []
        jsdoc_types = {}
        
        # Extraire types depuis JSDoc
        for m in self.PATTERNS['jsdoc_param'].finditer(jsdoc):
            ptype = m.group(1) or 'any'
            pname = m.group(2)
            jsdoc_types[pname] = ptype
        
        # Parser les paramètres
        for param in params_raw.split(','):
            param = param.strip()
            if not param:
                continue
            
            # Gérer les valeurs par défaut
            default = None
            if '=' in param:
                param, default = param.split('=', 1)
                param = param.strip()
                default = default.strip()
            
            # Gérer le destructuring { a, b }
            if param.startswith('{'):
                param = 'options'  # Simplifier
            
            name = param
            ptype = jsdoc_types.get(name, 'any')
            
            params.append(ERKParam(
                name=name,
                type=ptype,
                required=default is None,
                default=default
            ))
        
        return params
    
    def _extract_description(self, jsdoc: str) -> str:
        """Extrait la description depuis JSDoc"""
        if not jsdoc:
            return ""
        m = self.PATTERNS['jsdoc_desc'].search(jsdoc)
        return m.group(1).strip() if m else ""
    
    def _detect_central_method(self, name: str) -> str:
        """Détecte le centralMethod basé sur le nom"""
        name_lower = name.lower()
        for method, patterns in self.CENTRAL_METHOD_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, name_lower):
                    return method
        return "Execute"  # Défaut

# ============================================================================
# ERK GENERATOR
# ============================================================================

class ERKGenerator:
    """Génère la syntaxe ERK/GEV à partir des fonctions"""
    
    def __init__(self, functions: List[ERKFunction], source_file: str = ""):
        self.functions = functions
        self.source_file = source_file
    
    def to_gev(self) -> str:
        """Génère le format .gev (ERK natif)"""
        lines = [
            f"# ============================================================",
            f"# EURKAI - JS Functions → ERK Methods",
            f"# Source: {self.source_file}",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Functions: {len(self.functions)}",
            f"# ============================================================",
            "",
        ]
        
        # Grouper par centralMethod
        by_method = {}
        for func in self.functions:
            cm = func.centralMethod
            if cm not in by_method:
                by_method[cm] = []
            by_method[cm].append(func)
        
        for central_method, funcs in sorted(by_method.items()):
            lines.append(f"# --- {central_method} Methods ({len(funcs)}) ---")
            lines.append("")
            
            for func in funcs:
                lines.extend(self._func_to_gev(func))
                lines.append("")
        
        return "\n".join(lines)
    
    def _func_to_gev(self, func: ERKFunction) -> List[str]:
        """Convertit une fonction en syntaxe GEV"""
        lines = []
        
        # Lineage
        lines.append(f"Object:Method:JSScript:{func.name}:")
        
        # Description
        desc = func.description.replace('"', '\\"')
        lines.append(f'    .description = "{desc}"')
        
        # CentralMethod
        lines.append(f'    .centralMethod = {func.centralMethod}')
        
        # Params
        if func.params:
            param_list = ", ".join([f'"{p.name}"' for p in func.params])
            lines.append(f'    .params = [{param_list}]')
            
            # Param details
            for p in func.params:
                lines.append(f'    .param_{p.name}_type = "{p.type}"')
                if not p.required and p.default:
                    lines.append(f'    .param_{p.name}_default = {p.default}')
        
        # Async
        if func.isAsync:
            lines.append(f'    .isAsync = true')
        
        # Dependencies
        if func.dependencies:
            dep_list = ", ".join([f'"{d}"' for d in func.dependencies[:5]])  # Max 5
            lines.append(f'    .dependencies = [{dep_list}]')
        
        # Code (en commentaire ou référence)
        code_lines = len(func.code.split('\n'))
        lines.append(f'    .codeLines = {code_lines}')
        lines.append(f'    .codeType = "javascript"')
        
        # Le code complet serait trop long, on le met en référence
        # Pour le stocker vraiment, on utiliserait un fichier séparé
        # lines.append(f'    .codeRef = "methods/{func.name}.js"')
        
        return lines
    
    def to_json(self) -> str:
        """Génère le format JSON"""
        data = {
            "source": self.source_file,
            "generated": datetime.now().isoformat(),
            "count": len(self.functions),
            "functions": []
        }
        
        for func in self.functions:
            func_data = {
                "name": func.name,
                "lineage": func.lineage,
                "description": func.description,
                "centralMethod": func.centralMethod,
                "isAsync": func.isAsync,
                "params": [asdict(p) for p in func.params],
                "dependencies": func.dependencies,
                "code": func.code,
            }
            data["functions"].append(func_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def to_manifest(self) -> str:
        """Génère un manifest ERK (pour l'extension)"""
        manifest = {
            "type": "ERKMethodManifest",
            "version": "1.0",
            "source": self.source_file,
            "generated": datetime.now().isoformat(),
            "methods": {}
        }
        
        for func in self.functions:
            manifest["methods"][func.name] = {
                "lineage": func.lineage,
                "centralMethod": func.centralMethod,
                "description": func.description,
                "params": [p.name for p in func.params],
                "async": func.isAsync,
            }
        
        return json.dumps(manifest, indent=2, ensure_ascii=False)

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - JS → ERK Function Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gen_erk_functions.py extension.js                    # Output GEV to stdout
  python gen_erk_functions.py extension.js -o methods.s.gev   # Save to file
  python gen_erk_functions.py extension.js --format json      # Output JSON
  python gen_erk_functions.py extension.js --format manifest  # Output manifest
  python gen_erk_functions.py extension.js --stats            # Show stats only
        """
    )
    
    parser.add_argument('file', help='JavaScript file to parse')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-f', '--format', choices=['gev', 'json', 'manifest'], 
                       default='gev', help='Output format')
    parser.add_argument('--stats', action='store_true', help='Show stats only')
    parser.add_argument('--filter', help='Filter by centralMethod (e.g., Render,Execute)')
    
    args = parser.parse_args()
    
    # Lire le fichier
    with open(args.file, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Parser
    parser_js = JSParser(source)
    functions = parser_js.parse()
    
    # Filtrer si demandé
    if args.filter:
        allowed = [m.strip() for m in args.filter.split(',')]
        functions = [f for f in functions if f.centralMethod in allowed]
    
    # Stats only
    if args.stats:
        print(f"📄 File: {args.file}")
        print(f"📦 Functions: {len(functions)}")
        print(f"📤 Exports: {len(parser_js.exports)}")
        print(f"🔗 Dependencies: {', '.join(parser_js.dependencies) or 'none'}")
        print()
        
        # Par centralMethod
        by_method = {}
        for f in functions:
            cm = f.centralMethod
            by_method[cm] = by_method.get(cm, 0) + 1
        
        print("By CentralMethod:")
        for cm, count in sorted(by_method.items(), key=lambda x: -x[1]):
            print(f"  {cm}: {count}")
        
        print()
        print("Functions:")
        for f in functions:
            async_mark = "⚡" if f.isAsync else ""
            export_mark = "✓" if f.exports else ""
            params = ", ".join([p.name for p in f.params])
            print(f"  [{f.centralMethod:10}] {f.name}({params}) {async_mark} {export_mark}")
        
        return
    
    # Générer
    generator = ERKGenerator(functions, args.file)
    
    if args.format == 'gev':
        output = generator.to_gev()
    elif args.format == 'json':
        output = generator.to_json()
    elif args.format == 'manifest':
        output = generator.to_manifest()
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Generated {args.output} ({len(functions)} functions)")
    else:
        print(output)

if __name__ == '__main__':
    main()
