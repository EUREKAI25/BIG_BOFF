"""
Classe abstraite BaseProvider
Tous les providers doivent hériter de cette classe
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProvider(ABC):
    """Classe abstraite pour tous les providers."""

    def __init__(self, name: str, api_key: str):
        self.name = name
        self.api_key = api_key

    @abstractmethod
    def execute(self, model_type: str, model: str, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute l'appel au modèle.

        Args:
            model_type: Type (text2text, text2img, etc.)
            model: Nom du modèle (gpt-4o, flux-1-pro, etc.)
            prompt: Prompt/instruction
            data: Données complémentaires

        Returns:
            {
                "result": ...,
                "metadata": {
                    "provider": "...",
                    "model": "...",
                    "cost_usd": 0.0,
                    "tokens_input": 0,
                    "tokens_output": 0
                }
            }
        """
        pass

    def _build_metadata(self, model: str, cost: float = 0.0, tokens_in: int = 0, tokens_out: int = 0) -> Dict[str, Any]:
        """Construit les métadonnées standard."""
        return {
            "provider": self.name,
            "model": model,
            "cost_usd": round(cost, 4),
            "tokens_input": tokens_in,
            "tokens_output": tokens_out
        }
