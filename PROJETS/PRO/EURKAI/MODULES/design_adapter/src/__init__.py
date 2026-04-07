"""
design_adapter.src — API publique de l'EurkaiStyleAdapter.
"""
from .adapter import EurkaiStyleAdapter, adapt
from .models import (
    ColorSignal,
    FontSignal,
    RadiusSignal,
    SpacingSignal,
    CSSSignals,
    DOMSignals,
    TokenMap,
    EurkaiPatch,
)
from .css_extractor import extract as extract_css
from .dom_extractor import extract as extract_dom
from .token_mapper import map_to_tokens
from .patch_generator import generate_patch

__all__ = [
    # Main API
    "adapt",
    "EurkaiStyleAdapter",
    # Output model
    "EurkaiPatch",
    # Token map
    "TokenMap",
    # Signals
    "ColorSignal", "FontSignal", "RadiusSignal", "SpacingSignal",
    "CSSSignals", "DOMSignals",
    # Low-level extractors (pour usage avancé)
    "extract_css",
    "extract_dom",
    "map_to_tokens",
    "generate_patch",
]
