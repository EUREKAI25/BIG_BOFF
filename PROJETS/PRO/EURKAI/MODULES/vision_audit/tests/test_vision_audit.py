"""
Tests unitaires — vision_audit.
Aucun appel API : teste structure, parsing, validation, prompt.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import tempfile
import base64
from vision_audit import (
    VisionAudit, AuditResult, AuditIssue,
    build_audit_prompt, summarize_results,
    _parse_response, _validate_structure, _extract_json,
    _build_result, _error_result,
    DEFAULT_MODEL, _HIGH_PRIORITY_ZONES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

_VALID_RESPONSE = {
    "readability_pass": False,
    "global_score": 52,
    "issues": [
        {
            "zone": "hero",
            "problem": "text contrast insufficient against background image",
            "severity": "high",
            "confidence": 0.92,
            "suggested_fix": "increase overlay opacity or add dark gradient behind text",
        },
        {
            "zone": "hero",
            "problem": "background too detailed and competes with text",
            "severity": "medium",
            "confidence": 0.85,
            "suggested_fix": "reduce image contrast or apply blur behind text area",
        },
    ],
    "quick_fixes": [
        "increase overlay opacity to at least 0.6",
        "force text color to high-contrast variant",
    ],
}

_PASS_RESPONSE = {
    "readability_pass": True,
    "global_score": 88,
    "issues": [],
    "quick_fixes": [],
}


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_imports():
    from vision_audit import VisionAudit, AuditResult, AuditIssue, audit_screenshot, audit_page
    assert VisionAudit is not None
    assert AuditResult is not None
    print("✓ imports OK")


def test_high_priority_zones():
    assert "hero"        in _HIGH_PRIORITY_ZONES
    assert "nav"         in _HIGH_PRIORITY_ZONES
    assert "primary_cta" in _HIGH_PRIORITY_ZONES
    assert "footer"      not in _HIGH_PRIORITY_ZONES
    print("✓ high_priority_zones OK")


def test_build_prompt_hero():
    prompt = build_audit_prompt(zone="hero", viewport="desktop")
    assert "hero"    in prompt
    assert "desktop" in prompt
    assert "HIGH"    in prompt  # zone prioritaire
    assert "JSON"    in prompt
    assert "readability_pass" in prompt
    print("✓ build_prompt hero OK")


def test_build_prompt_normal_zone():
    prompt = build_audit_prompt(zone="footer", viewport="mobile")
    assert "NORMAL" in prompt
    assert "HIGH"   not in prompt
    print("✓ build_prompt normal zone OK")


def test_extract_json_clean():
    raw = '{"readability_pass": true, "global_score": 90, "issues": [], "quick_fixes": []}'
    result = _extract_json(raw)
    assert result.startswith("{")
    print("✓ extract_json clean OK")


def test_extract_json_with_markdown():
    raw = 'Here is my analysis:\n```json\n{"readability_pass": true, "global_score": 80, "issues": [], "quick_fixes": []}\n```'
    result = _extract_json(raw)
    data = json.loads(result)
    assert data["readability_pass"] is True
    print("✓ extract_json markdown OK")


def test_extract_json_embedded():
    raw = 'Analysis complete. {"readability_pass": false, "global_score": 40, "issues": [], "quick_fixes": []} End.'
    result = _extract_json(raw)
    data = json.loads(result)
    assert data["global_score"] == 40
    print("✓ extract_json embedded OK")


def test_validate_structure_valid():
    errors = _validate_structure(_VALID_RESPONSE, "hero")
    assert errors == [], f"Erreurs inattendues : {errors}"
    print("✓ validate_structure valid OK")


def test_validate_structure_missing_key():
    bad = {k: v for k, v in _VALID_RESPONSE.items() if k != "global_score"}
    errors = _validate_structure(bad, "hero")
    assert any("global_score" in e for e in errors)
    print("✓ validate_structure missing_key OK")


def test_validate_structure_invalid_severity():
    data = json.loads(json.dumps(_VALID_RESPONSE))
    data["issues"][0]["severity"] = "critical"  # invalide
    errors = _validate_structure(data, "hero")
    assert any("severity" in e for e in errors)
    print("✓ validate_structure invalid_severity OK")


def test_validate_structure_score_out_of_range():
    data = {**_VALID_RESPONSE, "global_score": 150}
    errors = _validate_structure(data, "hero")
    assert any("global_score" in e for e in errors)
    print("✓ validate_structure score_out_of_range OK")


def test_validate_structure_confidence_invalid():
    data = json.loads(json.dumps(_VALID_RESPONSE))
    data["issues"][0]["confidence"] = 1.5  # > 1.0
    errors = _validate_structure(data, "hero")
    assert any("confidence" in e for e in errors)
    print("✓ validate_structure confidence_invalid OK")


def test_parse_response_valid():
    raw = json.dumps(_VALID_RESPONSE)
    data = _parse_response(raw, zone="hero")
    assert data["readability_pass"] is False
    assert data["global_score"]     == 52
    assert len(data["issues"])      == 2
    print("✓ parse_response valid OK")


def test_parse_response_invalid_json():
    try:
        _parse_response("not json at all", zone="hero")
        assert False, "Devrait lever ValueError"
    except ValueError:
        pass
    print("✓ parse_response invalid_json raises OK")


def test_build_result():
    result = _build_result(
        data=_VALID_RESPONSE,
        zone="hero", viewport="desktop",
        image_path="/tmp/hero.png",
        model=DEFAULT_MODEL,
        duration_ms=1500.0,
    )
    assert isinstance(result, AuditResult)
    assert result.readability_pass is False
    assert result.global_score     == 52
    assert len(result.issues)      == 2
    assert result.issues[0].severity   == "high"
    assert result.issues[0].confidence == 0.92
    assert result.ok                is True
    assert result.error             is None
    print("✓ build_result OK")


def test_error_result():
    result = _error_result(
        zone="nav", viewport="mobile",
        image_path="/tmp/nav.png",
        model=DEFAULT_MODEL,
        duration_ms=50.0,
        error="Image introuvable",
    )
    assert result.ok               is False
    assert result.readability_pass is False
    assert result.global_score     == 0
    assert "introuvable"           in result.error
    print("✓ error_result OK")


def test_audit_result_to_dict():
    result = _build_result(_VALID_RESPONSE, "hero", "desktop", "/tmp/hero.png", DEFAULT_MODEL, 1200.0)
    d = result.to_dict()
    assert "readability_pass" in d
    assert "global_score"     in d
    assert "issues"           in d
    assert "quick_fixes"      in d
    assert "_meta"            in d
    assert d["_meta"]["zone"]      == "hero"
    assert d["_meta"]["viewport"]  == "desktop"
    assert len(d["issues"])        == 2
    print("✓ AuditResult.to_dict OK")


def test_audit_result_repr():
    result = _build_result(_VALID_RESPONSE, "hero", "desktop", "/tmp/hero.png", DEFAULT_MODEL, 1200.0)
    r = repr(result)
    assert "FAIL"   in r
    assert "hero"   in r
    assert "score"  in r
    print(f"✓ AuditResult.__repr__ OK : {r}")


def test_audit_issue_to_dict():
    issue = AuditIssue(
        zone="hero", problem="low contrast",
        severity="high", confidence=0.9,
        suggested_fix="add dark overlay",
    )
    d = issue.to_dict()
    assert d["severity"]   == "high"
    assert d["confidence"] == 0.9
    print("✓ AuditIssue.to_dict OK")


def test_summarize_results():
    r1 = _build_result(_VALID_RESPONSE, "hero", "desktop", "/tmp/hero.png", DEFAULT_MODEL, 1000.0)
    r2 = _build_result(_PASS_RESPONSE,  "nav",  "desktop", "/tmp/nav.png",  DEFAULT_MODEL, 800.0)
    summary = summarize_results([r1, r2])
    assert summary["total"]       == 2
    assert summary["pass"]        == 1
    assert summary["fail"]        == 1
    assert summary["avg_score"]   == 70.0  # (52 + 88) / 2
    assert summary["high_issues"] == 1
    assert "hero" in summary["zones_failed"]
    print("✓ summarize_results OK")


def test_summarize_empty():
    summary = summarize_results([])
    assert summary["total"] == 0
    print("✓ summarize_results empty OK")


def test_visionaudit_requires_api_key():
    import os
    old = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        VisionAudit(api_key=None)
        assert False, "Devrait lever ValueError"
    except ValueError as e:
        assert "API" in str(e) or "api_key" in str(e).lower()
    finally:
        if old:
            os.environ["ANTHROPIC_API_KEY"] = old
    print("✓ VisionAudit requires api_key OK")


def test_visionaudit_missing_image():
    """Sans appel API : vérifie que audit_screenshot retourne error sur image inexistante."""
    auditor = VisionAudit(api_key="sk-ant-dummy-key-for-test")
    result  = auditor.audit_screenshot(
        image_path="/nonexistent/path/hero.png",
        zone="hero", viewport="desktop",
    )
    assert result.ok               is False
    assert result.error            is not None
    assert result.readability_pass is False
    print(f"✓ VisionAudit missing_image error OK : {result.error[:40]}")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_imports,
        test_high_priority_zones,
        test_build_prompt_hero,
        test_build_prompt_normal_zone,
        test_extract_json_clean,
        test_extract_json_with_markdown,
        test_extract_json_embedded,
        test_validate_structure_valid,
        test_validate_structure_missing_key,
        test_validate_structure_invalid_severity,
        test_validate_structure_score_out_of_range,
        test_validate_structure_confidence_invalid,
        test_parse_response_valid,
        test_parse_response_invalid_json,
        test_build_result,
        test_error_result,
        test_audit_result_to_dict,
        test_audit_result_repr,
        test_audit_issue_to_dict,
        test_summarize_results,
        test_summarize_empty,
        test_visionaudit_requires_api_key,
        test_visionaudit_missing_image,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"✗ {t.__name__} : {e}")
            failed += 1
    print(f"\n{'✅' if failed == 0 else '❌'} {len(tests) - failed}/{len(tests)} tests passent.")
