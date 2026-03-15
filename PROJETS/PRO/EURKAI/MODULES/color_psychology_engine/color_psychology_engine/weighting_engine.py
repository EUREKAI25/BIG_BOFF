"""
color_psychology_engine.weighting_engine
──────────────────────────────────────────
Pondération et agrégation des signaux colorés.

Poids par source :
  industry       : 40%
  brand_values   : 30%
  tone           : 20%
  style_tags     : 7%
  exploration    : 3%  (diversité / évitement de la convergence)

L'audience modifie les poids (multiplicateur, pas source indépendante).

Algorithme :
  1. Collecter tous les signaux avec leur poids
  2. Comptabiliser les votes (nom_couleur → score_cumulé)
  3. Séparer preferred / accent / neutral / avoid
  4. Résoudre temperature et saturation par vote majoritaire pondéré
"""

from __future__ import annotations
from collections import defaultdict
from typing import List, Optional, Tuple

from .industry_color_map import get_industry_profile
from .emotion_color_map import (
    get_emotion_profile, get_tone_profile,
    get_audience_profile, get_style_profile,
)


# ─── Poids de base ────────────────────────────────────────────────────────────

_BASE_WEIGHTS = {
    "industry":     0.40,
    "brand_values": 0.30,
    "tone":         0.20,
    "style_tags":   0.07,
    "exploration":  0.03,
}

# Couleurs de diversité (exploration : évite la convergence totale)
_EXPLORATION_COLORS = ["teal", "coral", "warm_purple", "amber"]


# ─── Score aggregator ────────────────────────────────────────────────────────

class ColorScoreAggregator:
    def __init__(self):
        self._preferred: dict[str, float]    = defaultdict(float)
        self._accent:    dict[str, float]    = defaultdict(float)
        self._neutral:   dict[str, float]    = defaultdict(float)
        self._avoid:     dict[str, float]    = defaultdict(float)
        self._temperatures: list[tuple]      = []   # (temp, weight)
        self._saturations:  list[tuple]      = []   # (sat, weight)
        self._confidence:   float            = 0.0
        self._n_signals:    int              = 0

    def add_industry(self, industry: str, weight: float = 0.40):
        profile = get_industry_profile(industry)
        if not profile:
            return
        self._n_signals += 1
        for c in profile.preferred:
            self._preferred[c] += weight * 1.0
        for c in profile.accents:
            self._accent[c] += weight * 0.8
        for c in profile.neutrals:
            self._neutral[c] += weight * 0.6
        for c in profile.avoid:
            self._avoid[c] += weight * 1.0
        self._temperatures.append((profile.temperature, weight))
        self._saturations.append((profile.saturation, weight))
        self._confidence += weight

    def add_brand_value(self, value: str, weight: float = 0.10):
        profile = get_emotion_profile(value)
        if not profile:
            return
        self._n_signals += 1
        for c in profile.colors[:3]:
            self._preferred[c] += weight * profile.weight
        if len(profile.colors) > 3:
            for c in profile.colors[3:]:
                self._accent[c] += weight * 0.6
        self._temperatures.append((profile.temperature, weight * 0.5))
        self._saturations.append((profile.saturation, weight * 0.5))
        self._confidence += weight * 0.7

    def add_tone(self, tone: str, weight: float = 0.20):
        profile = get_tone_profile(tone)
        if not profile:
            return
        self._n_signals += 1
        for c in profile.colors[:2]:
            self._preferred[c] += weight * profile.weight
        for c in profile.colors[2:]:
            self._accent[c] += weight * 0.6
        self._temperatures.append((profile.temperature, weight))
        self._saturations.append((profile.saturation, weight))
        self._confidence += weight * 0.8

    def add_style_tags(self, tags: list[str], weight_per_tag: float = 0.035):
        for tag in tags:
            profile = get_style_profile(tag)
            if not profile:
                continue
            self._n_signals += 1
            for c in profile.colors[:2]:
                self._preferred[c] += weight_per_tag * profile.weight
            self._temperatures.append((profile.temperature, weight_per_tag * 0.4))
            self._saturations.append((profile.saturation, weight_per_tag * 0.4))

    def add_audience(self, audience: str, multiplier: float = 0.15):
        """L'audience ne vote pas directement mais amplifie certains signaux."""
        profile = get_audience_profile(audience)
        if not profile:
            return
        self._n_signals += 1
        for c in profile.colors[:2]:
            self._preferred[c] += multiplier * profile.weight
        self._temperatures.append((profile.temperature, multiplier * 0.3))
        self._saturations.append((profile.saturation, multiplier * 0.3))

    def add_exploration(self, weight: float = 0.03):
        """Ajoute une légère diversité pour éviter la convergence totale."""
        for c in _EXPLORATION_COLORS:
            self._accent[c] += weight * 0.3

    # ─── Résolution ─────────────────────────────────────────────────────────

    def resolve_temperature(self) -> str:
        return _majority_vote(self._temperatures, default="neutral")

    def resolve_saturation(self) -> str:
        return _majority_vote(self._saturations, default="medium")

    def top_preferred(self, n: int = 4) -> list[str]:
        return _top_n(self._preferred, n)

    def top_accents(self, n: int = 3) -> list[str]:
        # Exclure les couleurs déjà dans preferred
        filtered = {k: v for k, v in self._accent.items() if k not in self._preferred}
        return _top_n(filtered, n)

    def top_neutrals(self, n: int = 3) -> list[str]:
        return _top_n(self._neutral, n)

    def top_avoid(self, n: int = 4) -> list[str]:
        return _top_n(self._avoid, n)

    @property
    def confidence(self) -> float:
        return min(1.0, self._confidence)

    @property
    def score_breakdown(self) -> dict:
        return {
            "n_signals": self._n_signals,
            "preferred_scores": dict(sorted(self._preferred.items(), key=lambda x: -x[1])[:8]),
            "accent_scores":    dict(sorted(self._accent.items(), key=lambda x: -x[1])[:5]),
        }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _majority_vote(votes: list[tuple[str, float]], default: str) -> str:
    """Vote pondéré sur une liste de (valeur, poids)."""
    if not votes:
        return default
    tally: dict[str, float] = defaultdict(float)
    for val, w in votes:
        tally[val] += w
    return max(tally, key=lambda k: tally[k])


def _top_n(scores: dict[str, float], n: int) -> list[str]:
    return [k for k, _ in sorted(scores.items(), key=lambda x: -x[1])[:n]]
