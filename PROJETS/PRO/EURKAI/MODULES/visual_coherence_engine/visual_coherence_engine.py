# Shim — permet `from visual_coherence_engine import run` quand ce dossier est dans sys.path
import importlib.util as _util, sys as _sys
from pathlib import Path as _Path

_src = _Path(__file__).parent / "src" / "visual_coherence_engine.py"
_spec = _util.spec_from_file_location("_vce_src", _src)
_mod = _util.module_from_spec(_spec)   # type: ignore
_spec.loader.exec_module(_mod)          # type: ignore

run                        = _mod.run
analyze_image              = _mod.analyze_image
analyze_design_reference   = _mod.analyze_design_reference
generate_palette_from_image = _mod.generate_palette_from_image
compute_image_adjustments  = _mod.compute_image_adjustments
compute_readability_rules  = _mod.compute_readability_rules
