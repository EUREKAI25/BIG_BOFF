"""
scan_and_do.engine
───────────────────
Implémentation MVP du moteur d'exécution.

scan_and_do(objects_dict, scenario)

Pour chaque entrée du dictionnaire :
  1. récupérer l'objet courant
  2. passer l'objet à scenario.execute(key, obj)
  3. laisser le scénario décider

Le moteur n'agrège rien, ne valide rien, n'interprète rien.

Evolution future (hors MVP) :
  before_hook.execute(key, obj)
  scenario.execute(key, obj)
  after_hook.execute(key, obj)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class Scenario(ABC):
    """Interface que tout scénario doit implémenter."""

    @abstractmethod
    def execute(self, key: str, obj: Dict[str, Any]) -> None:
        """
        Traite un objet du dictionnaire.

        Parameters
        ----------
        key : str
            Clé de l'entrée dans objects_dict.
        obj : dict
            L'objet à traiter.

        Note : les outputs sont gérés en interne par le scénario.
        """
        ...


def scan_and_do(objects_dict: Dict[str, Any], scenario: Scenario) -> None:
    """
    Itère sur objects_dict et exécute scenario.execute(key, obj)
    pour chaque entrée.

    mrg(what=objects_dict, how=scenario)

    Parameters
    ----------
    objects_dict : dict
        Dictionnaire d'objets à traiter. Peut contenir n'importe quel type.
    scenario : Scenario
        Instance implémentant execute(key, obj).
    """
    for key, obj in objects_dict.items():
        scenario.execute(key, obj)
