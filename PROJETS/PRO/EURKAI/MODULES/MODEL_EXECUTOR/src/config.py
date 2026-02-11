"""
Configuration loader pour MODEL_EXECUTOR
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Charger .env depuis ~/.bigboff/secrets.env
ENV_PATH = Path.home() / ".bigboff" / "secrets.env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Charger config.yaml
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

class Config:
    def __init__(self):
        with open(CONFIG_PATH, "r") as f:
            self.data = yaml.safe_load(f)

    def get_active_provider(self, model_type: str) -> str:
        """Retourne le provider actif pour un type de modèle."""
        return self.data["model_types"].get(model_type, {}).get("active")

    def get_fallback_provider(self, model_type: str) -> str:
        """Retourne le provider fallback pour un type de modèle."""
        return self.data["model_types"].get(model_type, {}).get("fallback")

    def get_provider_config(self, provider_name: str) -> dict:
        """Retourne la config complète d'un provider."""
        return self.data["providers"].get(provider_name, {})

    def get_api_key(self, provider_name: str) -> str:
        """Récupère la clé API depuis les variables d'environnement."""
        provider_config = self.get_provider_config(provider_name)
        env_var = provider_config.get("api_key_env")
        if not env_var:
            raise ValueError(f"Provider {provider_name}: api_key_env non défini dans config.yaml")

        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"Provider {provider_name}: {env_var} non trouvé dans ~/.bigboff/secrets.env")

        return api_key

    def get_model_name(self, provider_name: str, model_type: str) -> str:
        """Retourne le nom du modèle à utiliser."""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.get("models", {}).get(model_type)

    def get_pricing(self, provider_name: str, model_type: str) -> dict:
        """Retourne les infos de pricing."""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.get("pricing", {}).get(model_type, {})

# Instance globale
config = Config()
