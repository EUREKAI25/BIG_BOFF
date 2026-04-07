"""
EURKAI Design Adapter — couche d'adaptation de style.

Convertit le DOM/CSS d'un site existant en patch de tokens Eurkai.
Aucune modification du site d'origine requise.

Usage minimal:
    from design_adapter import adapt

    patch = adapt(html=page_html, css=page_css)
    # Injectez patch.css_patch dans un <style> sur la page cible

Usage complet:
    from design_adapter import EurkaiStyleAdapter

    adapter = EurkaiStyleAdapter()
    patch = adapter.adapt(html=html, css=css, mood="minimal", site_name="acme.com")

    print(f"Confiance : {patch.confidence:.0%}")
    print(f"Framework : {patch.framework_detected}")
    print(f"Stats     : {patch.extraction_stats}")
    for token, src in patch.source_signals.items():
        print(f"  {token} ← {src}")
"""
from .src import (
    adapt,
    EurkaiStyleAdapter,
    EurkaiPatch,
    TokenMap,
    ColorSignal,
    FontSignal,
    RadiusSignal,
    SpacingSignal,
    CSSSignals,
    DOMSignals,
    extract_css,
    extract_dom,
    map_to_tokens,
    generate_patch,
)

__version__ = "1.0.0"

__all__ = [
    "adapt",
    "EurkaiStyleAdapter",
    "EurkaiPatch",
    "TokenMap",
    "ColorSignal", "FontSignal", "RadiusSignal", "SpacingSignal",
    "CSSSignals", "DOMSignals",
    "extract_css", "extract_dom",
    "map_to_tokens", "generate_patch",
]
