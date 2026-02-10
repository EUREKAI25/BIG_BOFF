"""
EUREKAI C1/1 — Lineages Assistés
================================
Système de suggestion de parents pour objets orphelins ou incomplets.

Architecture:
- SuggestionStrategy: Classe de base pour les stratégies de scoring
- LineageSuggester: Orchestrateur principal
- SuggestionResult: Structure de retour standardisée
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from enum import Enum
import re
from difflib import SequenceMatcher


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================

class ObjectType(Enum):
    """Types IVC×DRO pour cohérence de classification."""
    IDENTITY = "I"
    VIEW = "V"
    CONTEXT = "C"
    DEFINITION = "D"
    RULE = "R"
    OPTION = "O"
    UNKNOWN = "?"


@dataclass
class FractalObject:
    """Représentation d'un objet dans le store fractal."""
    id: str
    name: str
    lineage: str = ""
    parent_id: Optional[str] = None
    depth: int = 0
    object_type: ObjectType = ObjectType.UNKNOWN
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    @property
    def lineage_segments(self) -> List[str]:
        """Parse le lineage en segments."""
        if not self.lineage:
            return []
        return [s.strip() for s in self.lineage.split(":") if s.strip()]
    
    @property
    def is_orphan(self) -> bool:
        """L'objet n'a pas de parent déclaré."""
        return self.parent_id is None
    
    @property
    def has_incomplete_lineage(self) -> bool:
        """Le lineage semble tronqué ou incomplet."""
        segments = self.lineage_segments
        if not segments:
            return True
        # Heuristique: un lineage de moins de 2 segments est suspect
        return len(segments) < 2


@dataclass
class SuggestionResult:
    """
    Structure de retour pour une suggestion de parent.
    
    Attributes:
        parent_id: ID de l'objet parent suggéré
        score: Score de confiance (0.0 à 1.0)
        reason: Explication humaine de la suggestion
        strategy_scores: Détail des scores par stratégie
    """
    parent_id: str
    score: float
    reason: str
    strategy_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "parentId": self.parent_id,
            "score": round(self.score, 3),
            "scorePercent": round(self.score * 100, 1),
            "reason": self.reason,
            "details": self.strategy_scores
        }


# =============================================================================
# STRATÉGIES DE SCORING
# =============================================================================

class SuggestionStrategy(ABC):
    """Classe de base pour les stratégies de suggestion."""
    
    name: str = "base"
    weight: float = 1.0
    
    @abstractmethod
    def score(self, target: FractalObject, candidate: FractalObject) -> Tuple[float, str]:
        """
        Calcule le score de compatibilité entre target et candidate.
        
        Returns:
            Tuple (score 0-1, raison textuelle)
        """
        pass


class PatternMatchingStrategy(SuggestionStrategy):
    """
    Stratégie basée sur les patterns de lineage.
    
    Exemples de patterns reconnus:
    - Core:Agent:* → parent probable: Core:Agent
    - Agency:Project:Blog → parent probable: Agency:Project
    
    IMPORTANT: Le parent direct (1 niveau au-dessus avec tous segments matchant)
    reçoit un bonus significatif pour être priorisé.
    """
    
    name = "pattern"
    weight = 0.40
    
    def score(self, target: FractalObject, candidate: FractalObject) -> Tuple[float, str]:
        target_segments = target.lineage_segments
        candidate_segments = candidate.lineage_segments
        
        if not target_segments or not candidate_segments:
            return 0.0, "Lineage vide"
        
        # Le candidat doit être un préfixe du target
        # Ex: target = Core:Agent:LLM, candidate = Core:Agent
        if len(candidate_segments) >= len(target_segments):
            return 0.0, "Candidat trop profond"
        
        # Vérifier correspondance des segments
        matches = 0
        for i, seg in enumerate(candidate_segments):
            if i < len(target_segments) and seg.lower() == target_segments[i].lower():
                matches += 1
        
        if matches == 0:
            return 0.0, "Aucun segment commun"
        
        # Le candidat doit matcher TOUS ses segments pour être valide
        if matches < len(candidate_segments):
            # Match partiel: score réduit
            score = matches / len(candidate_segments) * 0.5
            return score, f"Match partiel: {matches}/{len(candidate_segments)} segments"
        
        # Match complet: calculer le score basé sur la proximité
        depth_diff = len(target_segments) - len(candidate_segments)
        
        if depth_diff == 1:
            # Parent direct: score maximal
            score = 1.0
            reason = f"Parent direct: {candidate.lineage} → {target.lineage}"
        elif depth_diff == 2:
            # Grand-parent: bon score
            score = 0.75
            reason = f"Grand-parent ({depth_diff} niveaux)"
        else:
            # Ancêtre plus distant: score décroissant
            score = max(0.3, 1.0 - (depth_diff * 0.15))
            reason = f"Ancêtre ({depth_diff} niveaux)"
        
        return score, reason


class LexicalSimilarityStrategy(SuggestionStrategy):
    """
    Stratégie basée sur la similarité des noms.
    Utilise SequenceMatcher pour une distance de type Levenshtein.
    """
    
    name = "lexical"
    weight = 0.25
    
    def score(self, target: FractalObject, candidate: FractalObject) -> Tuple[float, str]:
        # Similarité sur le nom
        name_sim = SequenceMatcher(
            None, 
            target.name.lower(), 
            candidate.name.lower()
        ).ratio()
        
        # Similarité sur le dernier segment de lineage
        target_last = target.lineage_segments[-1] if target.lineage_segments else ""
        candidate_last = candidate.lineage_segments[-1] if candidate.lineage_segments else ""
        
        segment_sim = SequenceMatcher(
            None,
            target_last.lower(),
            candidate_last.lower()
        ).ratio()
        
        # Combinaison pondérée
        score = (name_sim * 0.6 + segment_sim * 0.4)
        
        if score > 0.7:
            reason = f"Forte similarité lexicale ({score:.0%})"
        elif score > 0.4:
            reason = f"Similarité modérée ({score:.0%})"
        else:
            reason = f"Faible similarité ({score:.0%})"
        
        return score, reason


class StructuralProximityStrategy(SuggestionStrategy):
    """
    Stratégie basée sur la structure de l'arbre.
    Préfère les parents proches en termes de profondeur.
    """
    
    name = "structural"
    weight = 0.20
    
    def score(self, target: FractalObject, candidate: FractalObject) -> Tuple[float, str]:
        # Le parent idéal est exactement 1 niveau au-dessus
        depth_diff = target.depth - candidate.depth
        
        if depth_diff <= 0:
            return 0.0, "Candidat pas au-dessus dans l'arbre"
        
        if depth_diff == 1:
            return 1.0, "Parent direct (1 niveau au-dessus)"
        elif depth_diff == 2:
            return 0.7, "Grand-parent (2 niveaux)"
        elif depth_diff <= 4:
            return 0.4, f"Ancêtre ({depth_diff} niveaux)"
        else:
            return 0.1, f"Ancêtre distant ({depth_diff} niveaux)"


class TypeCoherenceStrategy(SuggestionStrategy):
    """
    Stratégie basée sur la cohérence des types IVC×DRO.
    Certaines combinaisons sont plus naturelles.
    """
    
    name = "type_coherence"
    weight = 0.15
    
    # Matrice de compatibilité des types
    COMPATIBILITY = {
        # (parent_type, child_type) → score
        (ObjectType.IDENTITY, ObjectType.VIEW): 0.9,
        (ObjectType.IDENTITY, ObjectType.CONTEXT): 0.8,
        (ObjectType.DEFINITION, ObjectType.RULE): 0.9,
        (ObjectType.DEFINITION, ObjectType.OPTION): 0.8,
        (ObjectType.RULE, ObjectType.OPTION): 0.7,
        (ObjectType.CONTEXT, ObjectType.CONTEXT): 0.6,
    }
    
    def score(self, target: FractalObject, candidate: FractalObject) -> Tuple[float, str]:
        key = (candidate.object_type, target.object_type)
        
        if key in self.COMPATIBILITY:
            score = self.COMPATIBILITY[key]
            reason = f"Cohérence {candidate.object_type.value}→{target.object_type.value}"
            return score, reason
        
        # Types identiques: score moyen
        if candidate.object_type == target.object_type:
            return 0.5, f"Types identiques ({target.object_type.value})"
        
        # Types inconnus: score neutre
        if ObjectType.UNKNOWN in (candidate.object_type, target.object_type):
            return 0.3, "Type non déterminé"
        
        return 0.2, f"Types différents ({candidate.object_type.value}≠{target.object_type.value})"


# =============================================================================
# ORCHESTRATEUR PRINCIPAL
# =============================================================================

class LineageSuggester:
    """
    Orchestrateur de suggestions de parents.
    
    Usage:
        store = {...}  # Dictionnaire id → FractalObject
        suggester = LineageSuggester(store)
        suggestions = suggester.suggest_parents("orphan_object_id")
    """
    
    DEFAULT_STRATEGIES = [
        PatternMatchingStrategy(),
        LexicalSimilarityStrategy(),
        StructuralProximityStrategy(),
        TypeCoherenceStrategy(),
    ]
    
    def __init__(
        self,
        store: Dict[str, FractalObject],
        strategies: Optional[List[SuggestionStrategy]] = None,
        min_score: float = 0.3,
        max_results: int = 5
    ):
        self.store = store
        self.strategies = strategies or self.DEFAULT_STRATEGIES
        self.min_score = min_score
        self.max_results = max_results
    
    def suggest_parents(self, object_id: str) -> List[SuggestionResult]:
        """
        Suggère des parents potentiels pour un objet.
        
        Args:
            object_id: ID de l'objet cible
            
        Returns:
            Liste de SuggestionResult triée par score décroissant
        """
        target = self.store.get(object_id)
        if not target:
            return []
        
        results = []
        
        for candidate_id, candidate in self.store.items():
            # Exclure l'objet lui-même
            if candidate_id == object_id:
                continue
            
            # Exclure les descendants (éviter cycles)
            if self._is_descendant(candidate_id, object_id):
                continue
            
            # Calculer le score combiné
            combined_score, strategy_scores, reasons = self._compute_combined_score(
                target, candidate
            )
            
            if combined_score >= self.min_score:
                # Construire la raison principale
                main_reason = self._build_main_reason(reasons, strategy_scores)
                
                results.append(SuggestionResult(
                    parent_id=candidate_id,
                    score=combined_score,
                    reason=main_reason,
                    strategy_scores=strategy_scores
                ))
        
        # Trier par score décroissant et limiter
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:self.max_results]
    
    def _compute_combined_score(
        self,
        target: FractalObject,
        candidate: FractalObject
    ) -> Tuple[float, Dict[str, float], Dict[str, str]]:
        """Calcule le score combiné de toutes les stratégies."""
        total_weight = sum(s.weight for s in self.strategies)
        weighted_sum = 0.0
        strategy_scores = {}
        reasons = {}
        
        for strategy in self.strategies:
            score, reason = strategy.score(target, candidate)
            weighted_sum += score * strategy.weight
            strategy_scores[strategy.name] = round(score, 3)
            reasons[strategy.name] = reason
        
        combined = weighted_sum / total_weight if total_weight > 0 else 0.0
        return combined, strategy_scores, reasons
    
    def _build_main_reason(
        self,
        reasons: Dict[str, str],
        scores: Dict[str, float]
    ) -> str:
        """Construit la raison principale à partir des meilleures stratégies."""
        # Trouver la stratégie avec le meilleur score
        if not scores:
            return "Aucune stratégie applicable"
        
        best_strategy = max(scores.items(), key=lambda x: x[1])
        return reasons.get(best_strategy[0], "Correspondance détectée")
    
    def _is_descendant(self, potential_ancestor: str, potential_descendant: str) -> bool:
        """Vérifie si potential_descendant est un descendant de potential_ancestor."""
        current = self.store.get(potential_descendant)
        visited = set()
        
        while current and current.parent_id and current.id not in visited:
            visited.add(current.id)
            if current.parent_id == potential_ancestor:
                return True
            current = self.store.get(current.parent_id)
        
        return False
    
    def find_orphans(self) -> List[FractalObject]:
        """Retourne tous les objets orphelins du store."""
        return [obj for obj in self.store.values() if obj.is_orphan]
    
    def find_incomplete(self) -> List[FractalObject]:
        """Retourne tous les objets avec lineage incomplet."""
        return [obj for obj in self.store.values() if obj.has_incomplete_lineage]
    
    def batch_suggest(self) -> Dict[str, List[SuggestionResult]]:
        """
        Génère des suggestions pour tous les objets orphelins/incomplets.
        
        Returns:
            Dictionnaire object_id → suggestions
        """
        results = {}
        
        # Utiliser un dict pour dédupliquer par ID
        targets_dict = {}
        for obj in self.find_orphans():
            targets_dict[obj.id] = obj
        for obj in self.find_incomplete():
            targets_dict[obj.id] = obj
        
        for obj_id, obj in targets_dict.items():
            suggestions = self.suggest_parents(obj_id)
            if suggestions:
                results[obj_id] = suggestions
        
        return results


# =============================================================================
# API SIMPLIFIÉE
# =============================================================================

def suggest_parents(
    object_id: str,
    store: Dict[str, FractalObject],
    **kwargs
) -> List[Dict]:
    """
    API simplifiée pour obtenir des suggestions.
    
    Args:
        object_id: ID de l'objet orphelin
        store: Store fractal (dict id → FractalObject)
        **kwargs: Options du suggester (min_score, max_results)
    
    Returns:
        Liste de suggestions au format dict
    """
    suggester = LineageSuggester(store, **kwargs)
    results = suggester.suggest_parents(object_id)
    return [r.to_dict() for r in results]


# =============================================================================
# UTILITAIRES
# =============================================================================

def parse_lineage(lineage_str: str) -> Tuple[List[str], int]:
    """
    Parse un lineage string en segments et profondeur.
    
    Returns:
        (segments, depth)
    """
    segments = [s.strip() for s in lineage_str.split(":") if s.strip()]
    return segments, len(segments)


def infer_type_from_name(name: str) -> ObjectType:
    """
    Infère le type IVC×DRO à partir du nom.
    Heuristique simple basée sur des patterns courants.
    """
    name_lower = name.lower()
    
    patterns = {
        ObjectType.IDENTITY: ["agent", "user", "system", "entity"],
        ObjectType.VIEW: ["view", "display", "render", "ui"],
        ObjectType.CONTEXT: ["context", "session", "state", "env"],
        ObjectType.DEFINITION: ["def", "schema", "model", "type"],
        ObjectType.RULE: ["rule", "policy", "constraint", "check"],
        ObjectType.OPTION: ["option", "config", "setting", "param"],
    }
    
    for obj_type, keywords in patterns.items():
        if any(kw in name_lower for kw in keywords):
            return obj_type
    
    return ObjectType.UNKNOWN
