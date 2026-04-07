"""
Tests minimaux du module screenshot_capture.
Vérifie la structure, les helpers et le CLI sans lancer de browser.
"""

import sys
from pathlib import Path

# Chemin vers le module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))  # EURKAI root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    from screenshot_capture import ScreenshotCapture, CaptureResult, VIEWPORT_PRESETS, AUDIT_ZONES
    assert ScreenshotCapture is not None
    assert CaptureResult is not None
    assert "desktop" in VIEWPORT_PRESETS
    assert "tablet"  in VIEWPORT_PRESETS
    assert "mobile"  in VIEWPORT_PRESETS
    assert "hero"    in AUDIT_ZONES
    assert "nav"     in AUDIT_ZONES
    print("✓ imports OK")


def test_viewport_presets():
    from screenshot_capture import VIEWPORT_PRESETS
    for name, vp in VIEWPORT_PRESETS.items():
        assert "width"  in vp, f"{name}: champ width manquant"
        assert "height" in vp, f"{name}: champ height manquant"
        assert vp["width"]  > 0
        assert vp["height"] > 0
    print("✓ viewport presets OK")


def test_audit_zones_selectors():
    from screenshot_capture import AUDIT_ZONES
    for name, selector in AUDIT_ZONES.items():
        assert selector.startswith("[data-audit="), f"{name}: sélecteur invalide: {selector}"
        assert name in selector, f"{name}: nom absent du sélecteur {selector}"
    print("✓ audit zones selectors OK")


def test_capture_result_dataclass():
    from screenshot_capture import CaptureResult
    r = CaptureResult(ok=True, path="/tmp/out.png", site="test", page="landing",
                      viewport="desktop", zone="hero", selector="[data-audit='hero']",
                      error=None, duration_ms=1234.5)
    d = r.to_dict()
    assert d["ok"]           is True
    assert d["site"]         == "test"
    assert d["zone"]         == "hero"
    assert d["duration_ms"]  == 1234.5
    assert "hero" in repr(r)  # zone name in repr
    print("✓ CaptureResult dataclass OK")


def test_output_path_structure(tmp_path):
    import tempfile
    from pathlib import Path
    from screenshot_capture import ScreenshotCapture
    with tempfile.TemporaryDirectory() as tmpdir:
        cap = ScreenshotCapture(output_root=tmpdir)
        p = cap._output_path(site="mysite", page="landing", viewport="desktop", zone="hero")
        assert p.name == "hero.png"
        assert "mysite" in str(p)
        assert "landing" in str(p)
        assert "desktop" in str(p)
        print(f"✓ output path OK : {p}")


def test_resolve_viewport():
    from screenshot_capture import VIEWPORT_PRESETS
    import screenshot_capture as _sc
    vp = _sc._resolve_viewport("tablet")
    assert vp == VIEWPORT_PRESETS["tablet"]
    # Viewport inconnu → lève ValueError
    try:
        _sc._resolve_viewport("unknown")
        assert False, "Devrait lever ValueError"
    except ValueError:
        pass
    print("✓ resolve viewport OK")


if __name__ == "__main__":
    import tempfile, os

    test_imports()
    test_viewport_presets()
    test_audit_zones_selectors()
    test_capture_result_dataclass()

    test_output_path_structure(None)

    test_resolve_viewport()

    print("\n✅ Tous les tests passent.")
