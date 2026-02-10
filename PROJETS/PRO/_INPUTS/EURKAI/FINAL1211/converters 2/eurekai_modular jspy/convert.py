#!/usr/bin/env python3
"""
EUREKAI Modular - Convert JS to Manifest + Python Backend
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime


def parse_js(source: str) -> dict:
    """Parse JS et extrait fonctions, params, JSDoc"""
    
    functions = []
    
    # Pattern pour fonctions avec JSDoc
    pattern = re.compile(
        r'(?P<jsdoc>/\*\*[\s\S]*?\*/\s*)?'
        r'function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{',
        re.MULTILINE
    )
    
    # Pattern pour exports window.xxx = xxx
    exports = set(re.findall(r'window\.(\w+)\s*=\s*\w+', source))
    
    # Pattern pour détecter dépendances backend (Store, fetch, etc.)
    has_backend_deps = bool(re.search(r'\b(Store|fetch|require|process|fs)\b', source))
    
    for match in pattern.finditer(source):
        name = match.group('name')
        params_raw = match.group('params')
        jsdoc = match.group('jsdoc') or ''
        
        # Parser params
        params = []
        for p in params_raw.split(','):
            p = p.strip()
            if not p:
                continue
            # Gérer valeurs par défaut
            if '=' in p:
                p = p.split('=')[0].strip()
            params.append(p)
        
        # Extraire description du JSDoc
        desc_match = re.search(r'/\*\*\s*\n\s*\*\s*([^\n@]+)', jsdoc)
        description = desc_match.group(1).strip() if desc_match else ''
        
        # Extraire @returns
        returns_match = re.search(r'@returns?\s+\{([^}]+)\}', jsdoc)
        returns = returns_match.group(1) if returns_match else 'any'
        
        # Détecter si fonction utilise callback
        has_callback = 'callback' in params or 'cb' in params or 'fn' in params
        
        functions.append({
            'name': name,
            'params': params,
            'description': description,
            'returns': returns,
            'has_callback': has_callback,
            'exported': name in exports
        })
    
    return {
        'functions': functions,
        'exports': list(exports),
        'has_backend_deps': has_backend_deps,
        'source': source
    }


def detect_type(parsed: dict) -> str:
    """Détecte si module est frontend ou backend"""
    if parsed['has_backend_deps']:
        return 'backend'
    
    # Si toutes les fonctions sont pures (pas de callback, pas de dépendances)
    for f in parsed['functions']:
        if f['has_callback']:
            return 'backend'
    
    return 'frontend'


def generate_manifest(parsed: dict, module_name: str, module_type: str) -> dict:
    """Génère le manifest JSON"""
    
    functions = {}
    for f in parsed['functions']:
        if not f['exported']:
            continue
        
        # Déterminer centralMethod selon le nom
        name_lower = f['name'].lower()
        if name_lower.startswith('get') or name_lower.startswith('read') or name_lower.startswith('find'):
            central_method = 'Read'
        elif name_lower.startswith('set') or name_lower.startswith('create') or name_lower.startswith('add'):
            central_method = 'Create'
        elif name_lower.startswith('update') or name_lower.startswith('modify'):
            central_method = 'Update'
        elif name_lower.startswith('delete') or name_lower.startswith('remove'):
            central_method = 'Delete'
        else:
            central_method = 'Execute'
        
        func_def = {
            'methodAlias': f['name'],
            'centralMethod': central_method,
            'params': f['params'],
            'description': f['description'],
            'returns': f['returns']
        }
        
        # Pour frontend, inclure le code
        if module_type == 'frontend':
            # Extraire le corps de la fonction
            pattern = re.compile(
                rf'function\s+{f["name"]}\s*\([^)]*\)\s*\{{',
                re.MULTILINE
            )
            match = pattern.search(parsed['source'])
            if match:
                start = match.end()
                depth = 1
                i = start
                while i < len(parsed['source']) and depth > 0:
                    if parsed['source'][i] == '{':
                        depth += 1
                    elif parsed['source'][i] == '}':
                        depth -= 1
                    i += 1
                func_def['code'] = parsed['source'][start:i-1].strip()
        
        functions[f['name']] = func_def
    
    return {
        'module': module_name,
        'type': module_type,
        'object': module_name.capitalize(),
        'version': '1.0.0',
        'generated': datetime.now().isoformat(),
        'functions': functions
    }


def generate_python_backend(parsed: dict, module_name: str, manifest: dict) -> str:
    """Génère le module Python backend"""
    
    lines = [
        f'"""',
        f'EUREKAI Backend - {module_name}',
        f'Auto-generated from {module_name}.js',
        f'"""',
        '',
        'from catalog import store',
        '',
    ]
    
    for f in parsed['functions']:
        if not f['exported']:
            continue
        
        # Signature Python
        params_str = ', '.join(f['params'])
        lines.append(f'def {f["name"]}({params_str}):')
        lines.append(f'    """')
        lines.append(f'    {f["description"]}')
        lines.append(f'    """')
        lines.append(f'    # TODO: Implémenter la logique')
        lines.append(f'    # Code JS original à convertir:')
        
        # Extraire le corps JS comme commentaire
        pattern = re.compile(
            rf'function\s+{f["name"]}\s*\([^)]*\)\s*\{{',
            re.MULTILINE
        )
        match = pattern.search(parsed['source'])
        if match:
            start = match.end()
            depth = 1
            i = start
            while i < len(parsed['source']) and depth > 0:
                if parsed['source'][i] == '{':
                    depth += 1
                elif parsed['source'][i] == '}':
                    depth -= 1
                i += 1
            body = parsed['source'][start:i-1].strip()
            for line in body.split('\n'):
                lines.append(f'    # {line}')
        
        lines.append(f'    pass')
        lines.append('')
    
    # Export dict
    lines.append('')
    lines.append('# Export des fonctions')
    lines.append('FUNCTIONS = {')
    for f in parsed['functions']:
        if f['exported']:
            lines.append(f'    "{f["name"]}": {f["name"]},')
    lines.append('}')
    
    return '\n'.join(lines)


def convert(jsfilepath: str, output_dir: str = './catalog') -> list:
    """
    Convertit un fichier JS en manifest + backend Python.
    
    Args:
        jsfilepath: Chemin du fichier JS source
        output_dir: Répertoire du catalogue
    
    Returns:
        list: [manifest_path, backend_path]
    """
    # Lire le source
    with open(jsfilepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Parser
    parsed = parse_js(source)
    module_name = Path(jsfilepath).stem.replace('-', '_')
    
    # Détecter type
    module_type = detect_type(parsed)
    
    # Générer manifest
    manifest = generate_manifest(parsed, module_name, module_type)
    
    # Créer répertoires
    manifests_dir = os.path.join(output_dir, 'manifests')
    backend_dir = os.path.join(output_dir, 'backend')
    os.makedirs(manifests_dir, exist_ok=True)
    os.makedirs(backend_dir, exist_ok=True)
    
    # Écrire manifest
    manifest_path = os.path.join(manifests_dir, f'{module_name}.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Écrire backend Python (seulement si backend)
    backend_path = None
    if module_type == 'backend':
        backend_code = generate_python_backend(parsed, module_name, manifest)
        backend_path = os.path.join(backend_dir, f'{module_name}.py')
        with open(backend_path, 'w', encoding='utf-8') as f:
            f.write(backend_code)
    
    return [manifest_path, backend_path]


if __name__ == '__main__':
    # Demo
    demo_js = '''
/**
 * Calcule la somme
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function add(a, b) {
    return a + b;
}

/**
 * Trouve les ancêtres d'un lineage
 * @param {string} lineage
 * @returns {Array}
 */
function getAncestors(lineage) {
    const result = [];
    Store.get(lineage).parents.forEach(p => result.push(p));
    return result;
}

window.add = add;
window.getAncestors = getAncestors;
'''
    
    with open('./demo.js', 'w') as f:
        f.write(demo_js)
    
    result = convert('./demo.js')
    print(f"Manifest: {result[0]}")
    print(f"Backend:  {result[1]}")
