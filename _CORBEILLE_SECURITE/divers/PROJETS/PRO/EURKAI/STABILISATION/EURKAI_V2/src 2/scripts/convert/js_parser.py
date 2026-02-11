"""
EURKAI Audit - JavaScript Parser
Extrait les fonctions, signatures, JSDoc et dépendances d'un fichier JS
"""
import re
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class JsParam:
    name: str
    type: str = "any"
    required: bool = True
    default: Optional[str] = None

@dataclass 
class JsFunction:
    name: str
    params: list[JsParam] = field(default_factory=list)
    jsdoc: dict = field(default_factory=dict)
    body: str = ""
    is_exported: bool = False
    has_callback: bool = False
    options_schema: dict = field(default_factory=dict)
    body_refs: list[str] = field(default_factory=list)

@dataclass
class ParseResult:
    functions: list[JsFunction] = field(default_factory=list)
    globals_read: set = field(default_factory=set)
    globals_written: set = field(default_factory=set)
    raw_source: str = ""

class JsParser:
    """Parse JavaScript pour extraire structure et métadonnées"""
    
    # Patterns de détection
    FUNCTION_PATTERN = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'  # JSDoc optionnel
        r'function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*{'
    )
    
    JSDOC_PARAM = re.compile(r'@param\s+{([^}]+)}\s+(\w+)(?:\s*-\s*(.*))?')
    JSDOC_RETURNS = re.compile(r'@returns?\s+{([^}]+)}(?:\s*-\s*(.*))?')
    JSDOC_DESC = re.compile(r'/\*\*\s*\n\s*\*\s*([^\n@]+)')
    JSDOC_EXAMPLE = re.compile(r'@example\s*([\s\S]*?)(?=\s*\*\s*@|\s*\*/)')
    
    WINDOW_EXPORT = re.compile(r'window\.(\w+)\s*=\s*(\w+)')
    MODULE_EXPORT = re.compile(r'module\.exports\s*=|exports\.(\w+)\s*=')
    
    DESTRUCTURE_OPTIONS = re.compile(
        r'const\s*{\s*([^}]+)\s*}\s*=\s*(\w+)'
    )
    
    GLOBAL_ACCESS = re.compile(r'\b([A-Z][a-zA-Z0-9]*)\.(get|set|call|apply|getAllLineages|\w+)\s*\(')
    
    def __init__(self, source: str):
        self.source = source
        self.result = ParseResult(raw_source=source)
        
    def parse(self) -> ParseResult:
        """Parse complet du fichier JS"""
        self._extract_functions()
        self._extract_exports()
        self._extract_globals()
        self._analyze_callbacks()
        self._extract_options_schemas()
        return self.result
    
    def _extract_functions(self):
        """Extrait toutes les fonctions avec leur JSDoc"""
        for match in self.FUNCTION_PATTERN.finditer(self.source):
            jsdoc_raw = match.group('jsdoc') or ""
            name = match.group('name')
            params_raw = match.group('params')
            
            # Extraire le corps de la fonction
            body = self._extract_function_body(match.end() - 1)
            
            # Parser les paramètres
            params = self._parse_params(params_raw, jsdoc_raw)
            
            # Parser JSDoc
            jsdoc = self._parse_jsdoc(jsdoc_raw)
            
            # Extraire les références dans le body
            body_refs = list(set(self.GLOBAL_ACCESS.findall(body)))
            body_refs = [f"{cls}.{method}" for cls, method in body_refs]
            
            func = JsFunction(
                name=name,
                params=params,
                jsdoc=jsdoc,
                body=body,
                body_refs=body_refs
            )
            self.result.functions.append(func)
    
    def _extract_function_body(self, start_brace: int) -> str:
        """Extrait le corps d'une fonction en comptant les accolades"""
        depth = 1
        i = start_brace + 1
        while i < len(self.source) and depth > 0:
            if self.source[i] == '{':
                depth += 1
            elif self.source[i] == '}':
                depth -= 1
            i += 1
        return self.source[start_brace:i]
    
    def _parse_params(self, params_raw: str, jsdoc: str) -> list[JsParam]:
        """Parse les paramètres avec types depuis JSDoc"""
        params = []
        jsdoc_types = {}
        
        # Extraire types depuis JSDoc
        for match in self.JSDOC_PARAM.finditer(jsdoc):
            ptype, pname = match.group(1), match.group(2)
            jsdoc_types[pname] = ptype
        
        # Parser les paramètres
        for param in params_raw.split(','):
            param = param.strip()
            if not param:
                continue
                
            default = None
            if '=' in param:
                param, default = param.split('=', 1)
                param = param.strip()
                default = default.strip()
            
            name = param
            ptype = jsdoc_types.get(name, "any")
            
            params.append(JsParam(
                name=name,
                type=ptype,
                required=default is None,
                default=default
            ))
        
        return params
    
    def _parse_jsdoc(self, jsdoc_raw: str) -> dict:
        """Parse le bloc JSDoc"""
        if not jsdoc_raw:
            return {}
        
        result = {}
        
        # Description
        desc_match = self.JSDOC_DESC.search(jsdoc_raw)
        if desc_match:
            result['description'] = desc_match.group(1).strip()
        
        # Returns
        returns_match = self.JSDOC_RETURNS.search(jsdoc_raw)
        if returns_match:
            result['returns'] = returns_match.group(1)
        
        # Examples
        examples = self.JSDOC_EXAMPLE.findall(jsdoc_raw)
        if examples:
            result['examples'] = [e.strip().replace('*', '').strip() for e in examples]
        
        return result
    
    def _extract_exports(self):
        """Détecte les exports (window.x ou module.exports)"""
        exported_names = set()
        
        for match in self.WINDOW_EXPORT.finditer(self.source):
            global_name, func_name = match.groups()
            exported_names.add(func_name)
            self.result.globals_written.add(f"window.{global_name}")
        
        for match in self.MODULE_EXPORT.finditer(self.source):
            if match.group(1):
                exported_names.add(match.group(1))
        
        # Marquer les fonctions exportées
        for func in self.result.functions:
            if func.name in exported_names:
                func.is_exported = True
    
    def _extract_globals(self):
        """Extrait les globales lues (Store, etc.)"""
        for match in self.GLOBAL_ACCESS.finditer(self.source):
            cls = match.group(1)
            if cls not in ('window', 'document', 'console', 'JSON', 'Array', 'Object', 'Map', 'Set'):
                self.result.globals_read.add(cls)
    
    def _analyze_callbacks(self):
        """Détecte les fonctions avec callbacks"""
        for func in self.result.functions:
            for param in func.params:
                if param.type == 'Function' or param.name in ('callback', 'cb', 'fn', 'handler'):
                    func.has_callback = True
                    break
    
    def _extract_options_schemas(self):
        """Extrait les schémas d'options destructurées"""
        for func in self.result.functions:
            # Chercher destructuring dans le body
            for match in self.DESTRUCTURE_OPTIONS.finditer(func.body):
                destructured = match.group(1)
                source_var = match.group(2)
                
                # Vérifier si c'est un paramètre de la fonction
                if source_var in [p.name for p in func.params]:
                    schema = {}
                    for item in destructured.split(','):
                        item = item.strip()
                        if '=' in item:
                            name, default = item.split('=', 1)
                            name = name.strip()
                            default = default.strip()
                            schema[name] = {
                                'default': default,
                                'type': self._infer_type(default)
                            }
                        else:
                            schema[item] = {'type': 'any'}
                    func.options_schema = schema

    def _infer_type(self, value: str) -> str:
        """Infère le type depuis une valeur par défaut"""
        value = value.strip()
        if value in ('true', 'false'):
            return 'boolean'
        if value.startswith("'") or value.startswith('"'):
            return 'string'
        if value.replace('.', '').replace('-', '').isdigit():
            return 'number'
        if value == '{}':
            return 'object'
        if value == '[]':
            return 'array'
        return 'any'


def parse_js(source: str) -> ParseResult:
    """Point d'entrée principal"""
    return JsParser(source).parse()


def parse_js_file(filepath: str) -> ParseResult:
    """Parse un fichier JS"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return parse_js(f.read())
