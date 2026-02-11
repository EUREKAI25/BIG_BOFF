"""
EUREKAI Convert - Module de conversion JS → JS Server + Python Client
"""
import os
from pathlib import Path

from eurekai_audit import parse_js, parse_js_file, analyze, ParseResult, AnalysisResult
from .gen_node_server import generate_node_server
from .gen_python_client import generate_python_client
from .gen_readme import generate_readme

__all__ = [
    'generate_node_server',
    'generate_python_client', 
    'generate_readme',
    'convert_file',
    'convert_source'
]


def convert_file(filepath: str, output_dir: str = None, port: int = 3000) -> dict:
    """
    Convertit un fichier JS en module EUREKAI complet
    
    Args:
        filepath: Chemin du fichier JS source
        output_dir: Répertoire de sortie (défaut: ./generated/<module_name>/)
        port: Port du serveur Node.js
        
    Returns:
        dict avec les chemins des fichiers générés
    """
    # Parser et analyser
    parsed = parse_js_file(filepath)
    analysis = analyze(parsed)
    
    filename = os.path.basename(filepath)
    module_name = Path(filepath).stem.replace('-', '_').replace('.', '_')
    
    # Répertoire de sortie
    if output_dir is None:
        output_dir = f"./generated/{module_name}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer les fichiers
    files = {}
    
    # Server Node.js
    server_files = generate_node_server(parsed, filename, port)
    for name, content in server_files.items():
        path = os.path.join(output_dir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        files[name] = path
    
    # Client Python
    client_content = generate_python_client(parsed, filename, port)
    client_path = os.path.join(output_dir, f"{module_name}_client.py")
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(client_content)
    files['client.py'] = client_path
    
    # README
    readme_content = generate_readme(parsed, analysis, filename, port)
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    files['README.md'] = readme_path
    
    return {
        'module_name': module_name,
        'output_dir': output_dir,
        'files': files,
        'parsed': parsed,
        'analysis': analysis
    }


def convert_source(source: str, module_name: str = "module", 
                  output_dir: str = None, port: int = 3000) -> dict:
    """
    Convertit du code JS en module EUREKAI
    
    Args:
        source: Code JS source
        module_name: Nom du module
        output_dir: Répertoire de sortie
        port: Port du serveur
        
    Returns:
        dict avec les contenus générés (pas écrits sur disque si output_dir=None)
    """
    parsed = parse_js(source)
    analysis = analyze(parsed)
    filename = f"{module_name}.js"
    
    result = {
        'module_name': module_name,
        'parsed': parsed,
        'analysis': analysis,
        'files': {}
    }
    
    # Générer les contenus
    server_files = generate_node_server(parsed, filename, port)
    result['files']['server.js'] = server_files['server.js']
    result['files']['package.json'] = server_files['package.json']
    result['files']['client.py'] = generate_python_client(parsed, filename, port)
    result['files']['README.md'] = generate_readme(parsed, analysis, filename, port)
    
    # Écrire si output_dir spécifié
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for name, content in result['files'].items():
            path = os.path.join(output_dir, name)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        result['output_dir'] = output_dir
    
    return result
