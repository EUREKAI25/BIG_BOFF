"""
conversational_brief
─────────────────────
Module EURKAI standalone — conversation guidée pour produire un JSON structuré.

Agnostique : le prompt, la checklist et le schéma de sortie sont injectés
par le projet consommateur. Réutilisable pour n'importe quel type de brief
(projet tech, brief design, brief marketing, etc.).

Usage minimal :
    from conversational_brief import run_brief
    from pathlib import Path

    spec = run_brief(
        system_prompt=Path("prompts/agent_brief.md"),
        checklist=["REFORMULATION", "UTILISATEURS", "PRODUIT", "FEATURES_MVP",
                   "STACK", "CONTRAINTES", "VALIDATION"],
        initial_brief="une marketplace de recettes cosmétiques",
        outdir=Path("outputs"),
        logdir=Path("logs"),
        registry_path=Path("product_registry.json"),
    )
"""

from .agent import run_brief

__version__ = "0.1.0"

__all__ = ["run_brief"]
