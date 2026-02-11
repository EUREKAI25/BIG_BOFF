"""
EUREKAI Convert - Python Client Generator
Génère un client Python à partir d'un ParseResult
"""
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from eurekai_audit import ParseResult, JsFunction, JsParam

# Type mapping JS → Python
PY_TYPE_MAP = {
    'string': 'str',
    'number': 'float',
    'boolean': 'bool',
    'Object': 'dict',
    'Array': 'list',
    'Function': 'callable',
    '*': 'Any',
    'any': 'Any',
    'undefined': 'None'
}

def js_to_py_type(js_type: str) -> str:
    """Convertit un type JS en type Python"""
    # Gérer les types composés comme {Object|undefined}
    js_type = js_type.strip('{}')
    if '|' in js_type:
        types = [js_to_py_type(t.strip()) for t in js_type.split('|')]
        types = [t for t in types if t != 'None']
        if len(types) == 1:
            return f"Optional[{types[0]}]"
        return f"Optional[Union[{', '.join(types)}]]"
    
    return PY_TYPE_MAP.get(js_type, 'Any')

def js_to_py_name(name: str) -> str:
    """Convertit un nom JS (camelCase) en Python (snake_case)"""
    # camelCase → snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def js_to_py_default(default: str) -> str:
    """Convertit une valeur par défaut JS en Python"""
    if default is None:
        return None
    
    default = default.strip()
    
    # Booléens
    if default == 'true':
        return 'True'
    if default == 'false':
        return 'False'
    
    # null/undefined
    if default in ('null', 'undefined'):
        return 'None'
    
    # Objets vides
    if default == '{}':
        return 'None'  # On utilisera {} dans le code mais None comme défaut pour signature
    if default == '[]':
        return 'None'
    
    # Strings
    if default.startswith("'"):
        return default.replace("'", '"')
    
    return default


class PythonClientGenerator:
    """Génère un client Python"""
    
    def __init__(self, parsed: ParseResult, filename: str = "", port: int = 3000):
        self.parsed = parsed
        self.filename = filename
        self.port = port
        self.template_dir = Path(__file__).parent / 'templates'
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self) -> str:
        """Génère le code du client Python"""
        template = self.env.get_template('client.py.j2')
        
        functions = self._prepare_functions()
        callback_functions = self._prepare_callback_functions()
        
        return template.render(
            filename=self.filename,
            timestamp=datetime.now().isoformat(),
            port=self.port,
            module_name=self._get_module_name(),
            functions=functions,
            callback_functions=callback_functions,
            has_store='Store' in self.parsed.globals_read
        )
    
    def _prepare_functions(self) -> list[dict]:
        """Prépare les métadonnées des fonctions pour le template"""
        result = []
        
        for f in self.parsed.functions:
            if not f.is_exported:
                continue
            
            params = self._prepare_params(f)
            
            # Construire la signature Python
            sig_parts = []
            call_parts = []
            
            for p in params:
                if p['required']:
                    sig_parts.append(f"{p['name']}: {p['py_type']}")
                else:
                    sig_parts.append(f"{p['name']}: {p['py_type']} = {p['py_default']}")
                call_parts.append(p['name'])
            
            result.append({
                'name': f.name,
                'py_name': js_to_py_name(f.name),
                'params': params,
                'py_signature': ', '.join(sig_parts),
                'py_call_args': ', '.join(call_parts),
                'py_return_type': js_to_py_type(f.jsdoc.get('returns', '*')),
                'description': f.jsdoc.get('description', f'Call {f.name}'),
                'return_description': f.jsdoc.get('returns_desc', 'Result from server'),
                'has_callback': f.has_callback,
                'example_args': self._generate_example_args(f)
            })
        
        return result
    
    def _prepare_callback_functions(self) -> list[dict]:
        """Prépare les fonctions avec callbacks"""
        result = []
        
        for f in self.parsed.functions:
            if not f.has_callback or not f.is_exported:
                continue
            
            # Paramètres sans le callback
            params_no_cb = [
                p for p in self._prepare_params(f)
                if p['type'] != 'Function' and p['name'] not in ('callback', 'cb', 'fn', 'handler')
            ]
            
            sig_parts = []
            call_parts = []
            
            for p in params_no_cb:
                if p['required']:
                    sig_parts.append(f"{p['name']}: {p['py_type']}")
                else:
                    sig_parts.append(f"{p['name']}: {p['py_type']} = {p['py_default']}")
                call_parts.append(p['name'])
            
            result.append({
                'name': f.name,
                'py_name': js_to_py_name(f.name),
                'py_signature_no_callback': ', '.join(sig_parts),
                'py_call_args_no_callback': ', '.join(call_parts)
            })
        
        return result
    
    def _prepare_params(self, func: JsFunction) -> list[dict]:
        """Prépare les paramètres d'une fonction"""
        result = []
        
        for p in func.params:
            py_default = js_to_py_default(p.default)
            
            result.append({
                'name': p.name,
                'type': p.type,
                'py_type': js_to_py_type(p.type),
                'required': p.required,
                'default': p.default,
                'py_default': py_default if py_default else 'None',
                'description': ''  # TODO: extraire depuis JSDoc
            })
        
        return result
    
    def _generate_example_args(self, func: JsFunction) -> str:
        """Génère des arguments d'exemple pour la doc"""
        examples = []
        
        for p in func.params:
            if p.type == 'Function':
                continue  # Skip callbacks
            elif p.type == 'string':
                examples.append(f'"{p.name}_value"')
            elif p.type == 'number':
                examples.append('0')
            elif p.type == 'boolean':
                examples.append('True')
            elif p.type == 'Object':
                examples.append('{}')
            elif p.type == 'Array':
                examples.append('[]')
            else:
                examples.append(f'"{p.name}"')
        
        return ', '.join(examples) if examples else ''
    
    def _get_module_name(self) -> str:
        """Extrait un nom de module depuis le filename"""
        if not self.filename:
            return "eurekai_module"
        return Path(self.filename).stem.replace('-', '_').replace('.', '_')


def generate_python_client(parsed: ParseResult, filename: str = "", port: int = 3000) -> str:
    """Point d'entrée principal"""
    generator = PythonClientGenerator(parsed, filename, port)
    return generator.generate()
