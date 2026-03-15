"""
logo_generator.arbitration
───────────────────────────
Sélectionne un concept parmi les N générés selon ArbitrationMode.

Mode NONE   → premier concept (index 0)
Mode AI     → scoring automatique (heuristiques + pénalités flags)
Mode HUMAN  → retourne tous les concepts sans sélection (LogoOutput.all_concepts)
"""

from __future__ import annotations
from typing import List, Optional

from .schemas import LogoConcept, ArbitrationConfig, ArbitrationMode


# ─── Scoring AI ───────────────────────────────────────────────────────────────

_FLAG_PENALTIES: dict[str, float] = {
    "FLAG_BG_RECT":        0.25,
    "FLAG_INVISIBLE_SHAPE": 0.10,
    "FLAG_FULL_SIZE_RECT":  0.20,
}


def _ai_score(concept: LogoConcept) -> float:
    """
    Score heuristique d'un concept.
    Base : 1.0
    Pénalités : par flag détecté par vector_optimizer
    Bonus : concepts courts (SVG léger ≈ moins de bruit)
    """
    score = 1.0

    # Pénalités par flag
    for flag in concept.flags:
        for key, penalty in _FLAG_PENALTIES.items():
            if flag.startswith(key):
                score -= penalty
                break

    # Légère préférence pour SVG compact (moins de shapes inutiles)
    svg_len = len(concept.svg_content)
    if svg_len < 3000:
        score += 0.05
    elif svg_len > 15000:
        score -= 0.05

    return max(0.0, min(1.0, score))


# ─── Sélection ────────────────────────────────────────────────────────────────

def select_concept(
    concepts: List[LogoConcept],
    config: ArbitrationConfig,
) -> Optional[LogoConcept]:
    """
    Sélectionne un concept selon le mode d'arbitrage.

    - NONE   : retourne concepts[0]
    - AI     : score tous, retourne le meilleur si score ≥ threshold
    - HUMAN  : retourne None (l'appelant doit présenter all_concepts)
    """
    if not concepts:
        return None

    if config.mode == ArbitrationMode.NONE:
        return concepts[0]

    if config.mode == ArbitrationMode.HUMAN:
        # Pas de sélection automatique — l'API retourne tous les concepts
        return None

    # Mode AI
    scored = []
    for concept in concepts:
        score = _ai_score(concept)
        concept.score = score
        scored.append((score, concept))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_concept = scored[0]

    if best_score >= config.ai_score_threshold:
        return best_concept

    # Aucun concept ne dépasse le seuil → retourner le meilleur quand même
    # mais logger un warning dans les flags
    best_concept.flags.append(
        f"FLAG_LOW_SCORE: best concept scored {best_score:.2f} "
        f"(threshold: {config.ai_score_threshold}). Manual review recommended."
    )
    return best_concept
