"""
EURKAI — MODEL_EXECUTOR
Point d'entrée unique pour tous les appels IA du système.
"""

from .src.executor import model_execute

__all__ = ["model_execute"]
__version__ = "1.0.0"
