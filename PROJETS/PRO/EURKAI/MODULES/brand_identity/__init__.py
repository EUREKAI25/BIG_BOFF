"""
brand_identity — EURKAI Brand Identity Engine
v1.0.0

Génère un système d'identité visuelle complet depuis brief + visual_intent + palette.
Déterministe. Aucun appel externe. Aucune image générée ici.

Exports :
    generate_brand_identity(brief, visual_intent, palette, context, reference=None) -> dict
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).parent
_SRC  = _HERE / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("_brand_identity_core", _SRC / "brand_identity.py")
_mod  = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
generate_brand_identity = _mod.generate_brand_identity

VERSION = "1.0.0"

__all__ = ["generate_brand_identity"]
