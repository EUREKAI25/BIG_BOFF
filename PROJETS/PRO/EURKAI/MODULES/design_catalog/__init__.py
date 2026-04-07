"""
design_catalog — EURKAI Design Catalog
v1.0.0

Catalogue des endpoints et scénarios design.
Expose design.explore() pour l'introspection.
"""

from __future__ import annotations

from pathlib import Path

from design_catalog.design_explore import explore

_HERE    = Path(__file__).parent
CATALOG  = _HERE / "design_catalog.json"
VERSION  = "1.0.0"

__all__ = ["explore"]
