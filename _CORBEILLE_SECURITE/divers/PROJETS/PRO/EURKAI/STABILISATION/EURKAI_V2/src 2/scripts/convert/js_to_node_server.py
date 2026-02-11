"""
EURKAI Convert - Node.js Server Generator
Génère un serveur Express.js à partir d'un ParseResult
"""
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from EURKAI_audit import ParseResult, JsFunction

# Type mapping JS → JS (pour clarté dans les variantes)
JS_TYPE_MAP = {
    'string': 'string',
    'number': 'number',
    'boolean': 'boolean',
    'Object': 'Object',
    'Array': 'Array',
    'Function': 'Function',
    '*': 'any',
    'any': 'any'
}

class NodeServerGenerator:
    """Génère un serveur Node.js/Express"""
    
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
        """Génère le code du serveur"""
        template = self.env.get_template('server.js.j2')
        
        # Préparer les données pour le template
        functions = self._prepare_functions()
        callback_functions = self._prepare_callback_functions()
        dependencies = list(self.parsed.globals_read)
        
        # Nettoyer le source (enlever les window.xxx = xxx)
        source = self._clean_source()
        
        return template.render(
            filename=self.filename,
            timestamp=datetime.now().isoformat(),
            port=self.port,
            source=source,
            functions=functions,
            callback_functions=callback_functions,
            dependencies=dependencies
        )
    
    def _prepare_functions(self) -> list[dict]:
        """Prépare les métadonnées des fonctions"""
        return [
            {'name': f.name}
            for f in self.parsed.functions
            if f.is_exported
        ]
    
    def _prepare_callback_functions(self) -> list[dict]:
        """Prépare les fonctions avec callbacks pour générer les variantes"""
        result = []
        
        for f in self.parsed.functions:
            if not f.has_callback or not f.is_exported:
                continue
            
            # Identifier le paramètre callback
            callback_param = None
            other_params = []
            
            for p in f.params:
                if p.type == 'Function' or p.name in ('callback', 'cb', 'fn', 'handler'):
                    callback_param = p
                else:
                    other_params.append(p)
            
            if not callback_param:
                continue
            
            # Générer les signatures pour les variantes
            params_without_cb = ', '.join([
                f"{p.name}" + (f" = {p.default}" if p.default else "")
                for p in other_params
            ])
            
            # Arguments pour _collect: remplace callback par une fonction qui collecte
            call_args_collect = ', '.join([
                p.name if p != callback_param else "(obj, level) => { results.push({ obj, level }); }"
                for p in f.params
            ])
            
            # Arguments pour _find: remplace callback par une fonction qui cherche
            call_args_find = ', '.join([
                p.name if p != callback_param else "(obj, level) => { if (obj[field] === value) return { obj, level }; }"
                for p in f.params
            ])
            
            result.append({
                'name': f.name,
                'params_without_callback': params_without_cb,
                'call_args_collect': call_args_collect,
                'call_args_find': call_args_find
            })
        
        return result
    
    def _clean_source(self) -> str:
        """Nettoie le source pour Node.js"""
        source = self.parsed.raw_source
        
        # Supprimer les assignments window.xxx = xxx (on les expose via le dispatcher)
        source = re.sub(r'\n*//\s*Global access\n*', '', source)
        source = re.sub(r'window\.(\w+)\s*=\s*\1;?\n?', '', source)
        
        return source.strip()
    
    def generate_package_json(self) -> str:
        """Génère le package.json"""
        template = self.env.get_template('package.json.j2')
        module_name = self._get_module_name()
        
        return template.render(
            module_name=module_name,
            filename=self.filename,
            timestamp=datetime.now().isoformat()
        )
    
    def _get_module_name(self) -> str:
        """Extrait un nom de module depuis le filename"""
        if not self.filename:
            return "EURKAI_module"
        return Path(self.filename).stem.replace('-', '_').replace('.', '_')


def generate_node_server(parsed: ParseResult, filename: str = "", port: int = 3000) -> dict:
    """Point d'entrée - retourne dict avec server.js et package.json"""
    generator = NodeServerGenerator(parsed, filename, port)
    
    return {
        'server.js': generator.generate(),
        'package.json': generator.generate_package_json()
    }
