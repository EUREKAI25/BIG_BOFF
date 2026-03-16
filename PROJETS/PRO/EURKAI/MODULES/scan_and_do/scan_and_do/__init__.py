"""
scan_and_do
───────────
MVP de la Méthode Récursive Globale (MRG).

Moteur d'exécution générique : itère sur un dictionnaire d'objets
et délègue chaque entrée à un scénario.

    scan_and_do(objects_dict, scenario)  ≡  mrg(what, how)

Le module est agnostique : aucune logique métier, aucune validation,
aucune agrégation. Tout appartient au scénario.
"""

from .engine import scan_and_do, Scenario

__version__ = "0.1.0"

__all__ = ["scan_and_do", "Scenario"]
