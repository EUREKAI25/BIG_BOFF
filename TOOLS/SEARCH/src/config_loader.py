#!/usr/bin/env python3
"""
BIG_BOFF Search — Configuration Loader
Charge la configuration depuis ~/.bigboff/config.json ou config.default.json
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


# Chemins des fichiers de config
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = Path.home() / '.bigboff'
USER_CONFIG_FILE = CONFIG_DIR / 'config.json'
DEFAULT_CONFIG_FILE = PROJECT_ROOT / 'config.default.json'


def ensure_config_dir():
    """Crée le dossier ~/.bigboff s'il n'existe pas."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Charge la configuration.

    Priorité :
    1. ~/.bigboff/config.json (config utilisateur)
    2. config.default.json (config par défaut du projet)

    Returns:
        dict: Configuration complète avec chemins expandés
    """
    # Charger config par défaut
    if DEFAULT_CONFIG_FILE.exists():
        with open(DEFAULT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        raise FileNotFoundError(f"Config par défaut manquante : {DEFAULT_CONFIG_FILE}")

    # Override avec config utilisateur si existe
    if USER_CONFIG_FILE.exists():
        with open(USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config = merge_configs(config, user_config)

    # Expand tous les chemins (~ et variables d'environnement)
    config = expand_paths(config)

    return config


def merge_configs(base: Dict, override: Dict) -> Dict:
    """Merge récursif de deux dicts (override écrase base)."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def expand_paths(obj: Any) -> Any:
    """Expand récursif des chemins (~ et $VAR) dans une structure."""
    if isinstance(obj, dict):
        return {k: expand_paths(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_paths(item) for item in obj]
    elif isinstance(obj, str):
        # Expand ~ et variables d'env
        expanded = os.path.expanduser(obj)
        expanded = os.path.expandvars(expanded)
        return expanded
    else:
        return obj


def get_db_path() -> str:
    """Raccourci : retourne le chemin de la base de données."""
    config = load_config()
    return config['paths']['db_path']


def get_dropbox_root() -> str:
    """Raccourci : retourne le chemin racine Dropbox."""
    config = load_config()
    return config['paths']['dropbox_root']


def get_server_config() -> Dict[str, Any]:
    """Raccourci : retourne la config serveur."""
    config = load_config()
    return config['server']


def init_user_config():
    """Initialise la config utilisateur si elle n'existe pas.

    Copie config.default.json vers ~/.bigboff/config.json
    """
    ensure_config_dir()

    if USER_CONFIG_FILE.exists():
        print(f"✓ Config utilisateur existe déjà : {USER_CONFIG_FILE}")
        return

    if not DEFAULT_CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config par défaut manquante : {DEFAULT_CONFIG_FILE}")

    # Copier config par défaut
    with open(DEFAULT_CONFIG_FILE, 'r', encoding='utf-8') as f:
        default_config = json.load(f)

    with open(USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)

    print(f"✓ Config utilisateur créée : {USER_CONFIG_FILE}")
    print(f"   Éditez ce fichier pour personnaliser les chemins.")


def show_config():
    """Affiche la configuration actuelle."""
    config = load_config()
    print("=== Configuration BIG_BOFF Search ===\n")
    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        init_user_config()
    elif len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_config()
    else:
        print("Usage:")
        print("  python config_loader.py --init   # Créer ~/.bigboff/config.json")
        print("  python config_loader.py --show   # Afficher config actuelle")
