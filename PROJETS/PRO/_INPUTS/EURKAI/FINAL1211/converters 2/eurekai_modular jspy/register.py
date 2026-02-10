#!/usr/bin/env python3
"""
EUREKAI Modular - Register manifest to registry
Appelé via hookAfter après convert()
"""
import os
import json
from datetime import datetime


def register(manifest_path: str, registry_path: str = './catalog/registry.json') -> dict:
    """
    Enregistre un manifest dans le registry.
    
    Args:
        manifest_path: Chemin du manifest à enregistrer
        registry_path: Chemin du registry
    
    Returns:
        dict: Le registry mis à jour
    """
    # Charger le manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # Charger ou créer le registry
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'api_endpoint': '/api',
            'modules': {}
        }
    
    # Ajouter/mettre à jour le module
    module_name = manifest['module']
    registry['modules'][module_name] = {
        'type': manifest['type'],
        'object': manifest['object'],
        'manifest': manifest_path,
        'registered': datetime.now().isoformat(),
        'functions': list(manifest['functions'].keys())
    }
    
    registry['updated'] = datetime.now().isoformat()
    
    # Créer le répertoire si nécessaire
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    
    # Sauvegarder
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    return registry


def unregister(module_name: str, registry_path: str = './catalog/registry.json') -> dict:
    """
    Supprime un module du registry.
    
    Args:
        module_name: Nom du module à supprimer
        registry_path: Chemin du registry
    
    Returns:
        dict: Le registry mis à jour
    """
    if not os.path.exists(registry_path):
        return {}
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    if module_name in registry['modules']:
        del registry['modules'][module_name]
        registry['updated'] = datetime.now().isoformat()
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    
    return registry


def list_modules(registry_path: str = './catalog/registry.json') -> list:
    """Liste tous les modules enregistrés"""
    if not os.path.exists(registry_path):
        return []
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    return list(registry.get('modules', {}).keys())


if __name__ == '__main__':
    # Test
    print("Modules enregistrés:", list_modules())
