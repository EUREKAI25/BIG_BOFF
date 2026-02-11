# AUTO FUNCTION BUILDER - Exemples

Ce document présente des exemples concrets d'utilisation du système.

## Exemple 1 : Fonction simple de comptage

### Brief

```
Je veux une fonction qui lit un fichier texte à partir d'un chemin,
compte le nombre de lignes non vides, et retourne ce nombre.
La fonction doit lever une erreur claire si le fichier n'existe pas.
```

### Function_spec généré

```json
{
  "name": "count_non_empty_lines",
  "description": "Compte le nombre de lignes non vides dans un fichier texte.",
  "inputs": [
    {
      "name": "file_path",
      "type": "str",
      "description": "Chemin vers le fichier texte à analyser.",
      "required": true
    }
  ],
  "outputs": [
    {
      "name": "line_count",
      "type": "int",
      "description": "Nombre de lignes non vides."
    }
  ],
  "errors": [
    {
      "name": "FileNotFoundError",
      "description": "Levée si le fichier n'existe pas."
    }
  ],
  "acceptance_criteria": [
    "Retourne 0 pour un fichier vide.",
    "Ignore les lignes ne contenant que des espaces.",
    "Lève FileNotFoundError si le fichier est introuvable."
  ]
}
```

### Code généré

```python
"""Module généré automatiquement."""

import os
from report_actions import report_actions


def count_non_empty_lines(file_path: str) -> int:
    """Compte le nombre de lignes non vides dans un fichier texte.

    Args:
        file_path (str): Chemin vers le fichier texte à analyser.

    Returns:
        int: Nombre de lignes non vides.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
    """
    report_actions(
        event="COUNT_NON_EMPTY_LINES_START",
        level="info",
        message=f"Comptage des lignes dans {file_path}"
    )
    
    if not os.path.exists(file_path):
        report_actions(
            event="COUNT_NON_EMPTY_LINES_ERROR",
            level="error",
            message=f"Fichier introuvable: {file_path}"
        )
        raise FileNotFoundError(f"File not found: {file_path}")
    
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                count += 1
    
    report_actions(
        event="COUNT_NON_EMPTY_LINES_SUCCESS",
        level="info",
        message=f"Lignes comptées: {count}",
        context={"file": file_path, "count": count}
    )
    
    return count
```

### Tests générés

```python
"""Tests pour count_non_empty_lines."""

import pytest
from pathlib import Path
from count_non_empty_lines import count_non_empty_lines


def test_count_non_empty_lines_nominal(tmp_path):
    """Test nominal avec un fichier contenant des lignes."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("ligne 1\n\nligne 2\n  \nligne 3\n", encoding="utf-8")
    
    result = count_non_empty_lines(str(file_path))
    
    assert result == 3


def test_count_non_empty_lines_empty_file(tmp_path):
    """Test avec un fichier vide."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")
    
    result = count_non_empty_lines(str(file_path))
    
    assert result == 0


def test_count_non_empty_lines_only_spaces(tmp_path):
    """Test avec fichier contenant uniquement des espaces."""
    file_path = tmp_path / "spaces.txt"
    file_path.write_text("   \n  \n\t\t\n", encoding="utf-8")
    
    result = count_non_empty_lines(str(file_path))
    
    assert result == 0


def test_count_non_empty_lines_missing_file():
    """Test avec fichier inexistant."""
    with pytest.raises(FileNotFoundError):
        count_non_empty_lines("/chemin/inexistant.txt")
```

### Métadonnées générées

```json
{
  "name": "count_non_empty_lines",
  "description": "Compte le nombre de lignes non vides dans un fichier texte.",
  "version": "1.0.0",
  "author": "laNostrAI",
  "created_at": "2025-11-21T21:00:00Z",
  "updated_at": "2025-11-21T21:00:00Z",
  "language": "python",
  "object_type": "function",
  "module": "AUTO_FUNCTION_BUILDER_EXAMPLE",
  "tags": ["io", "text", "count"],
  "dependencies": ["report_actions"],
  "scenarios": ["example"],
  "inputs_schema": {
    "file_path": {
      "type": "str",
      "required": true
    }
  },
  "outputs_schema": {
    "line_count": {
      "type": "int"
    }
  }
}
```

## Exemple 2 : Fonction avec traitement de données

### Brief

```
Créer une fonction qui prend une liste de nombres et retourne :
- la somme
- la moyenne
- le minimum
- le maximum
Lever ValueError si la liste est vide.
```

### Utilisation du système

```python
builder_state = {
    "project": {
        "name": "data_processing",
        "root": "/home/user/projects/data"
    },
    "function_request": {
        "brief_raw": """
        Créer une fonction qui prend une liste de nombres et retourne :
        - la somme
        - la moyenne
        - le minimum
        - le maximum
        Lever ValueError si la liste est vide.
        """
    }
}

# Exécution complète
from auto_function_builder_get import auto_function_builder_get
from auto_function_builder_execute import auto_function_builder_execute
from auto_function_builder_finalize import auto_function_builder_finalize
from auto_function_builder_validate import auto_function_builder_validate
from auto_function_builder_render import auto_function_builder_render

builder_state = auto_function_builder_get(builder_state)
builder_state = auto_function_builder_execute(builder_state)

# Si tests échouent
if builder_state["tests"]["status"] == "failed":
    from auto_function_builder_fix import auto_function_builder_fix
    builder_state = auto_function_builder_fix(builder_state)

builder_state = auto_function_builder_finalize(builder_state)
builder_state = auto_function_builder_validate(builder_state)
builder_state = auto_function_builder_render(builder_state)

# Vérifier le résultat
print(f"Statut global: {builder_state['validation']['global_status']}")
print(f"Fonction générée: {builder_state['paths']['function_file']}")
print(f"Tests: {builder_state['paths']['tests_file']}")
print(f"Rapport: {builder_state['paths']['report_file']}")
```

### Code généré attendu

```python
"""Module généré automatiquement."""

from typing import Dict
from report_actions import report_actions


def calculate_stats(numbers: list) -> Dict[str, float]:
    """Calcule les statistiques d'une liste de nombres.

    Args:
        numbers (list): Liste de nombres à analyser.

    Returns:
        Dict[str, float]: Dictionnaire contenant sum, mean, min, max.

    Raises:
        ValueError: Si la liste est vide.
    """
    report_actions(
        event="CALCULATE_STATS_START",
        level="info",
        message="Calcul des statistiques"
    )
    
    if not numbers:
        report_actions(
            event="CALCULATE_STATS_ERROR",
            level="error",
            message="Liste vide fournie"
        )
        raise ValueError("La liste ne peut pas être vide.")
    
    total = sum(numbers)
    count = len(numbers)
    mean = total / count
    minimum = min(numbers)
    maximum = max(numbers)
    
    stats = {
        "sum": total,
        "mean": mean,
        "min": minimum,
        "max": maximum
    }
    
    report_actions(
        event="CALCULATE_STATS_SUCCESS",
        level="info",
        message="Statistiques calculées",
        context=stats
    )
    
    return stats
```

## Exemple 3 : Script d'utilisation complet

Voir le fichier `example_usage.py` pour un script complet d'utilisation du système.

```python
#!/usr/bin/env python3
"""Exemple d'utilisation complète de AUTO FUNCTION BUILDER."""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

# Imports des modules
from auto_function_builder_get import auto_function_builder_get
from auto_function_builder_execute import auto_function_builder_execute
from auto_function_builder_fix import auto_function_builder_fix
from auto_function_builder_finalize import auto_function_builder_finalize
from auto_function_builder_validate import auto_function_builder_validate
from auto_function_builder_render import auto_function_builder_render


def main():
    """Point d'entrée principal."""
    
    # Configuration
    brief = """
    Je veux une fonction qui valide une adresse email.
    La fonction doit vérifier :
    - présence d'un @
    - présence d'un domaine
    - format général valide
    Retourner True si valide, False sinon.
    """
    
    # Initialisation
    builder_state = {
        "project": {
            "name": "email_validator",
            "root": os.getcwd()
        },
        "function_request": {
            "brief_raw": brief
        }
    }
    
    print("🚀 Démarrage de AUTO FUNCTION BUILDER\n")
    
    # Phase GET
    print("📥 Phase GET...")
    builder_state = auto_function_builder_get(builder_state)
    print(f"✅ Fonction: {builder_state['function_request']['function_name']}\n")
    
    # Phase EXECUTE
    print("⚙️  Phase EXECUTE...")
    builder_state = auto_function_builder_execute(builder_state)
    
    tests_status = builder_state['tests']['status']
    print(f"✅ Tests: {tests_status}\n")
    
    # Phase FIX si nécessaire
    if tests_status == "failed":
        print("🔧 Phase FIX...")
        builder_state = auto_function_builder_fix(builder_state)
        final_status = builder_state['fix']['status']
        print(f"✅ Fix: {final_status}\n")
    
    # Phase FINALIZE
    print("🎯 Phase FINALIZE...")
    builder_state = auto_function_builder_finalize(builder_state)
    print("✅ Métadonnées générées\n")
    
    # Phase VALIDATE
    print("✔️  Phase VALIDATE...")
    builder_state = auto_function_builder_validate(builder_state)
    validation_status = builder_state['validation']['global_status']
    print(f"✅ Validation: {validation_status}\n")
    
    # Phase RENDER
    print("📄 Phase RENDER...")
    builder_state = auto_function_builder_render(builder_state)
    print("✅ Rapport généré\n")
    
    # Résumé
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Statut global: {validation_status}")
    print(f"\nFichiers générés:")
    for output in builder_state['outputs_index']:
        print(f"  - {output['type']}: {output['path']}")
    print("=" * 60)
    
    return 0 if validation_status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Exemples de builder_state

### État initial minimal

```json
{
  "project": {
    "name": "mon_projet",
    "root": "/chemin/projet"
  },
  "function_request": {
    "brief_raw": "Brief de la fonction ici"
  }
}
```

### État après GET

```json
{
  "project": {...},
  "function_request": {
    "brief_raw": "...",
    "brief_normalized": "...",
    "function_name": "ma_fonction",
    "language": "python"
  },
  "constraints": {...},
  "paths": {...},
  "code_context": {...}
}
```

### État final complet

```json
{
  "project": {...},
  "function_request": {...},
  "constraints": {...},
  "paths": {...},
  "code_context": {...},
  "function_spec": {...},
  "artifacts": {
    "function_skeleton": "...",
    "function_code": "...",
    "tests_code": "...",
    "validation_notes": [],
    "readme_notes": []
  },
  "tests": {
    "status": "success",
    "report": {...}
  },
  "fix": {
    "attempts": 0,
    "status": "not_started"
  },
  "metadata": {...},
  "validation": {
    "spec_validation": "ok",
    "conventions_validation": "ok",
    "tests_validation": "ok",
    "metadata_validation": "ok",
    "global_status": "success"
  },
  "outputs_index": [...]
}
```

---

**Pour plus d'informations, consulter `README.md` et `ARCHITECTURE.md`**
