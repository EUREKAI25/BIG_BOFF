#!/usr/bin/env python3
"""
EUREKAI Modular - Serveur API agnostique
Route: GET /api/{object}/{centralMethod}/{methodAlias}?vector={id}&token={token}
"""
import os
import json
import importlib.util
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# Configuration
CATALOG_DIR = os.environ.get('EUREKAI_CATALOG', './catalog')
REGISTRY_PATH = os.path.join(CATALOG_DIR, 'registry.json')


def load_registry():
    """Charge le registry"""
    if not os.path.exists(REGISTRY_PATH):
        return {'modules': {}}
    with open(REGISTRY_PATH, 'r') as f:
        return json.load(f)


def load_manifest(module_name: str) -> dict:
    """Charge le manifest d'un module"""
    registry = load_registry()
    if module_name not in registry.get('modules', {}):
        return None
    
    manifest_path = registry['modules'][module_name]['manifest']
    with open(manifest_path, 'r') as f:
        return json.load(f)


def load_backend_function(module_name: str, func_name: str):
    """Charge dynamiquement une fonction backend"""
    backend_path = os.path.join(CATALOG_DIR, 'backend', f'{module_name}.py')
    
    if not os.path.exists(backend_path):
        return None
    
    spec = importlib.util.spec_from_file_location(module_name, backend_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if hasattr(module, 'FUNCTIONS') and func_name in module.FUNCTIONS:
        return module.FUNCTIONS[func_name]
    
    if hasattr(module, func_name):
        return getattr(module, func_name)
    
    return None


def get_vector_params(vector_id: str) -> dict:
    """Récupère les paramètres depuis un vecteur (Store)"""
    # TODO: Implémenter la récupération depuis le Store
    # Pour l'instant, on parse le vector_id comme JSON si possible
    try:
        return json.loads(vector_id)
    except:
        return {'vector': vector_id}


def validate_token(token: str) -> bool:
    """Valide le token d'authentification"""
    # TODO: Implémenter la validation réelle
    return token is not None and len(token) > 0


# Middleware d'authentification
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Token est la dernière clé du query string
        query_keys = list(request.args.keys())
        token = query_keys[-1] if len(query_keys) > 1 else None
        if not validate_token(token):
            return jsonify({'ok': False, 'error': 'Invalid or missing token'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/api/<object_name>/<central_method>/<method_alias>')
@require_token
def handle_api_call(object_name: str, central_method: str, method_alias: str):
    """
    Route principale API
    GET /api/{object}/{centralMethod}/{methodAlias}?{vector}&{token}
    """
    # Récupérer vector et token depuis les clés du query string
    args = list(request.args.keys())
    vector_id = args[0] if len(args) > 0 else None
    # token est déjà géré par le decorator
    
    # Trouver le module correspondant à l'objet
    registry = load_registry()
    module_name = None
    
    for name, info in registry.get('modules', {}).items():
        if info.get('object', '').lower() == object_name.lower():
            module_name = name
            break
    
    if not module_name:
        return jsonify({
            'ok': False,
            'error': f'Object "{object_name}" not found',
            'available': [m['object'] for m in registry.get('modules', {}).values()]
        }), 404
    
    # Charger le manifest
    manifest = load_manifest(module_name)
    if not manifest:
        return jsonify({'ok': False, 'error': 'Manifest not found'}), 404
    
    # Trouver la fonction
    func_def = None
    for fname, fdef in manifest.get('functions', {}).items():
        if fdef.get('methodAlias') == method_alias and fdef.get('centralMethod') == central_method:
            func_def = fdef
            func_name = fname
            break
    
    if not func_def:
        return jsonify({
            'ok': False,
            'error': f'Method "{method_alias}" with centralMethod "{central_method}" not found',
            'available': list(manifest.get('functions', {}).keys())
        }), 404
    
    # Récupérer les paramètres
    params = get_vector_params(vector_id)
    
    # Exécuter selon le type
    if manifest['type'] == 'frontend':
        # Frontend: retourner le code pour exécution côté client
        return jsonify({
            'ok': True,
            'type': 'frontend',
            'code': func_def.get('code'),
            'params': func_def.get('params')
        })
    
    else:
        # Backend: exécuter la fonction Python
        func = load_backend_function(module_name, func_name)
        
        if not func:
            return jsonify({
                'ok': False,
                'error': f'Backend function "{func_name}" not implemented'
            }), 501
        
        try:
            # Mapper les paramètres
            func_params = func_def.get('params', [])
            call_args = [params.get(p) for p in func_params]
            
            result = func(*call_args)
            
            return jsonify({
                'ok': True,
                'type': 'backend',
                'result': result
            })
        
        except Exception as e:
            return jsonify({
                'ok': False,
                'error': str(e)
            }), 500


@app.route('/api/registry')
def get_registry():
    """Retourne le registry complet"""
    return jsonify(load_registry())


@app.route('/api/manifest/<module_name>')
def get_manifest(module_name: str):
    """Retourne le manifest d'un module"""
    manifest = load_manifest(module_name)
    if not manifest:
        return jsonify({'ok': False, 'error': 'Module not found'}), 404
    return jsonify(manifest)


@app.route('/health')
def health():
    """Health check"""
    registry = load_registry()
    return jsonify({
        'status': 'ok',
        'modules': list(registry.get('modules', {}).keys())
    })


if __name__ == '__main__':
    print("🚀 EUREKAI API Server")
    print(f"📁 Catalog: {CATALOG_DIR}")
    print(f"📋 Registry: {REGISTRY_PATH}")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)
