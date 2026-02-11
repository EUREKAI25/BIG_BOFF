"""
EUREKAI Convert - README Generator
Génère la documentation du module
"""
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from eurekai_audit import ParseResult, AnalysisResult
from .gen_python_client import js_to_py_name, js_to_py_type

class ReadmeGenerator:
    """Génère un README pour le module"""
    
    def __init__(self, parsed: ParseResult, analysis: AnalysisResult, 
                 filename: str = "", port: int = 3000):
        self.parsed = parsed
        self.analysis = analysis
        self.filename = filename
        self.port = port
        self.template_dir = Path(__file__).parent / 'templates'
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self) -> str:
        """Génère le README"""
        template = self.env.get_template('README.md.j2')
        
        functions = self._prepare_functions()
        
        return template.render(
            module_name=self._get_module_name(),
            filename=self.filename,
            timestamp=datetime.now().isoformat(),
            port=self.port,
            score=self.analysis.score,
            functions=functions,
            dependencies=list(self.parsed.globals_read),
            has_store='Store' in self.parsed.globals_read
        )
    
    def _prepare_functions(self) -> list[dict]:
        """Prépare les données des fonctions pour le template"""
        result = []
        
        for f in self.parsed.functions:
            if not f.is_exported:
                continue
            
            params = []
            example_args = []
            
            for p in f.params:
                params.append({
                    'name': p.name,
                    'py_type': js_to_py_type(p.type),
                    'description': '',
                    'required': p.required
                })
                
                # Générer exemple
                if p.type == 'Function':
                    continue
                elif p.type == 'string':
                    example_args.append(f'"{p.name}"')
                else:
                    example_args.append(p.name)
            
            result.append({
                'name': f.name,
                'py_name': js_to_py_name(f.name),
                'description': f.jsdoc.get('description', ''),
                'params': params,
                'has_callback': f.has_callback,
                'example_args': ', '.join(example_args)
            })
        
        return result
    
    def _get_module_name(self) -> str:
        if not self.filename:
            return "eurekai_module"
        return Path(self.filename).stem.replace('-', '_').replace('.', '_')


def generate_readme(parsed: ParseResult, analysis: AnalysisResult,
                   filename: str = "", port: int = 3000) -> str:
    """Point d'entrée principal"""
    return ReadmeGenerator(parsed, analysis, filename, port).generate()
