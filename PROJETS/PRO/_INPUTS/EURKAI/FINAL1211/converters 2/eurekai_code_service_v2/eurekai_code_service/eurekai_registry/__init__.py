"""
EUREKAI Registry - Catalogue des modules convertis
(À développer dans une phase ultérieure)
"""

class Registry:
    """Catalogue central des modules EUREKAI"""
    
    def __init__(self, base_dir: str = "./modules"):
        self.base_dir = base_dir
        self._modules = {}
    
    def register(self, module_name: str, path: str, tags: list = None):
        """Enregistre un module dans le catalogue"""
        self._modules[module_name] = {
            'path': path,
            'tags': tags or []
        }
    
    def get(self, module_name: str) -> dict:
        """Récupère les infos d'un module"""
        return self._modules.get(module_name)
    
    def search(self, tag: str) -> list:
        """Recherche par tag"""
        return [
            name for name, info in self._modules.items()
            if tag in info.get('tags', [])
        ]
    
    def list_all(self) -> list:
        """Liste tous les modules"""
        return list(self._modules.keys())


# Instance globale
_registry = None

def get_registry(base_dir: str = None) -> Registry:
    """Obtient l'instance du registre"""
    global _registry
    if _registry is None:
        _registry = Registry(base_dir or "./modules")
    return _registry
