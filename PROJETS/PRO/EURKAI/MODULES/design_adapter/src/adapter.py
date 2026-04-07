"""
adapter.py
EurkaiStyleAdapter — point d'entrée principal du module.

Prend un DOM HTML et/ou un CSS brut, retourne un EurkaiPatch
(CSS :root{} override + token_map documenté + métadonnées).

Usage:
    from design_adapter import adapt

    patch = adapt(html=page_html, css=page_css)
    print(patch.css_patch)          # injectez dans <style>
    print(patch.confidence)         # 0–1
    print(patch.warnings)           # tokens manquants, conflits
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from .css_extractor import extract as extract_css
from .dom_extractor import extract as extract_dom
from .models import CSSSignals, DOMSignals, EurkaiPatch, TokenMap
from .patch_generator import generate_patch
from .token_mapper import map_to_tokens


class EurkaiStyleAdapter:
    """
    Adaptateur de style : convertit le DOM/CSS d'un site existant
    en patch de tokens Eurkai.

    L'objectif est de produire une couche de compatibilité visuelle
    sans modifier le site d'origine.
    """

    def adapt(
        self,
        html: str = "",
        css: str = "",
        *,
        mood: Optional[str] = None,
        site_name: str = "",
    ) -> EurkaiPatch:
        """
        Analyse le style du site et génère le patch Eurkai.

        Args:
            html:      HTML complet de la page (peut être vide)
            css:       CSS concaténé du site (peut être vide)
            mood:      Hint de mood optionnel ("luxury", "bold", "minimal"…)
                       Influence uniquement les transitions si fourni.
            site_name: Nom du site (pour commentaires dans le patch)

        Returns:
            EurkaiPatch avec css_patch prêt à injecter
        """
        # ── Extraction ────────────────────────────────────────────────────────
        css_signals: CSSSignals = extract_css(css) if css.strip() else CSSSignals()
        dom_signals: DOMSignals = extract_dom(html) if html.strip() else DOMSignals()

        # ── Mapping tokens ────────────────────────────────────────────────────
        token_map, sources, warnings = map_to_tokens(css_signals, dom_signals)

        # ── Génération du patch ───────────────────────────────────────────────
        css_patch = generate_patch(token_map, sources, warnings, mood=mood)

        # ── Score de confiance ────────────────────────────────────────────────
        confidence = _compute_confidence(token_map, sources)

        # ── Stats d'extraction ────────────────────────────────────────────────
        stats = {
            "colors_found":    len(css_signals.colors),
            "fonts_found":     len(css_signals.fonts),
            "radii_found":     len(css_signals.radii),
            "spacings_found":  len(css_signals.spacings),
            "css_vars_found":  len(css_signals.css_vars),
            "dom_colors_found":len(dom_signals.color_hints),
            "dom_vars_found":  len(dom_signals.existing_css_vars),
            "tokens_resolved": len([v for v in sources.values() if "fallback" not in v.lower()]),
            "tokens_fallback": len([v for v in sources.values() if "fallback" in v.lower()]),
        }

        return EurkaiPatch(
            css_patch=css_patch,
            token_map=asdict(token_map),
            source_signals=sources,
            confidence=confidence,
            warnings=warnings,
            framework_detected=dom_signals.detected_framework,
            extraction_stats=stats,
        )


# ── Fonction standalone ────────────────────────────────────────────────────────

def adapt(
    html: str = "",
    css: str = "",
    *,
    mood: Optional[str] = None,
    site_name: str = "",
) -> EurkaiPatch:
    """
    Raccourci fonctionnel : `from design_adapter import adapt`.

    Args:
        html:      HTML complet de la page (optionnel)
        css:       CSS concaténé (optionnel)
        mood:      Hint de mood optionnel
        site_name: Nom du site (pour les commentaires du patch)

    Returns:
        EurkaiPatch
    """
    return EurkaiStyleAdapter().adapt(html=html, css=css, mood=mood, site_name=site_name)


# ── Helpers ───────────────────────────────────────────────────────────────────

_FALLBACK_MARKERS = ("fallback", "default", "dérivé")
_HIGH_VALUE_TOKENS = {
    "color_primary", "color_secondary", "color_text",
    "color_bg", "font_family_headings", "font_family_body",
}


def _compute_confidence(token_map: TokenMap, sources: dict[str, str]) -> float:
    """
    Score 0–1 représentant la fiabilité du patch.

    Basé sur :
    - Proportion de tokens haute importance résolus depuis des signaux réels
    - Pénalité pour chaque token restant en fallback
    """
    if not sources:
        return 0.0

    high_value_resolved = 0
    for token in _HIGH_VALUE_TOKENS:
        src = sources.get(token, "fallback")
        if not any(m in src.lower() for m in _FALLBACK_MARKERS):
            high_value_resolved += 1

    high_value_score = high_value_resolved / len(_HIGH_VALUE_TOKENS)

    # Proportion globale de tokens non-fallback
    real_count = sum(
        1 for v in sources.values()
        if not any(m in v.lower() for m in _FALLBACK_MARKERS)
    )
    global_score = real_count / len(sources) if sources else 0.0

    # Pondération : haute importance × 0.7, global × 0.3
    return round(high_value_score * 0.7 + global_score * 0.3, 3)
