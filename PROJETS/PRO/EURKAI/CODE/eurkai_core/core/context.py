"""
ProjectExecutionContext
Objet transverse transporté à travers tout le pipeline de création projet EURKAI.
Aucune logique d'interprétation ici — juste transport et exposition.

Usage :
    from core.context import ProjectExecutionContext
    ctx = ProjectExecutionContext(
        rules={"max_files": 10},
        resources={"budget": "low"},
        mode="skeleton",
        validation_level="core",
    )
    result = scenario_orchestrate.run(schema_ident, params, context=ctx)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProjectExecutionContext:
    """
    Context transverse du pipeline projet EURKAI.

    rules            : règles d'exécution (ex. contraintes métier, limites)
    resources        : ressources disponibles (ex. budget, providers, tokens)
    mode             : "real" | "stub" | "skeleton"
                       real     → comportement normal, appels LLM actifs
                       stub     → sorties simplifiées, LLM optionnel
                       skeleton → squelette minimal, aucun appel LLM
    validation_level : "none" | "core" | "full"
                       none  → pas de validation
                       core  → vérifications essentielles (défaut)
                       full  → toutes les vérifications
    meta             : dict libre pour annotations ou données de contexte
    """

    rules:            Dict[str, Any] = field(default_factory=dict)
    resources:        Dict[str, Any] = field(default_factory=dict)
    mode:             str            = "real"
    validation_level: str            = "core"
    meta:             Dict[str, Any] = field(default_factory=dict)

    VALID_MODES             = ("real", "stub", "skeleton")
    VALID_VALIDATION_LEVELS = ("none", "core", "full")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rules":            self.rules,
            "resources":        self.resources,
            "mode":             self.mode,
            "validation_level": self.validation_level,
            "meta":             self.meta,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProjectExecutionContext":
        return cls(
            rules=d.get("rules", {}),
            resources=d.get("resources", {}),
            mode=d.get("mode", "real"),
            validation_level=d.get("validation_level", "core"),
            meta=d.get("meta", {}),
        )


def _context_to_dict(context) -> Optional[Dict[str, Any]]:
    """Normalise un context (ProjectExecutionContext ou dict) en dict, ou None."""
    if context is None:
        return None
    if hasattr(context, "to_dict"):
        return context.to_dict()
    if isinstance(context, dict):
        return context
    return None
