"""EURKAI Seed Builder — Génère des seeds de pages depuis des maquettes."""
from .schemas import PageSeed, SeedSection, SeedField, ResponsiveConfig
from .analyzer import MockupAnalyzer
from .watcher import process_pending_mockups, load_seed, list_seeds

__version__ = "0.1.0"
__all__ = [
    "PageSeed", "SeedSection", "SeedField", "ResponsiveConfig",
    "MockupAnalyzer",
    "process_pending_mockups", "load_seed", "list_seeds",
]
