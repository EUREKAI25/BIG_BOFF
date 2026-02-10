"""
H3 — Configuration Pytest
=========================

Fixtures et configuration globales pour les tests.
"""

import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset l'état entre chaque test."""
    yield
    # Cleanup si nécessaire


# Marqueur pour les tests async
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
