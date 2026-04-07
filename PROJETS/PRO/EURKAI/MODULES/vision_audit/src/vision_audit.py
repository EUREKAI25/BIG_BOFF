"""
vision_audit.py — Audit visuel de lisibilité via modèle vision.

Analyse des screenshots PNG et retourne des diagnostics structurés
sur la lisibilité, le contraste perçu, la hiérarchie visuelle et la visibilité des CTAs.

Usage programmatique :
    from vision_audit import VisionAudit

    auditor = VisionAudit()  # lit ANTHROPIC_API_KEY depuis l'env
    result  = auditor.audit_screenshot("hero.png", zone="hero", viewport="desktop")
    results = auditor.audit_page([
        {"image_path": "hero.png",  "zone": "hero",  "viewport": "desktop"},
        {"image_path": "nav.png",   "zone": "nav",   "viewport": "desktop"},
        {"image_path": "cta.png",   "zone": "primary_cta", "viewport": "mobile"},
    ])

Usage CLI :
    python vision_audit.py --image hero.png --zone hero --viewport desktop
    python vision_audit.py --batch captures.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent.parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute


# ─────────────────────────────────────────────────────────────────────────────
# TYPES
# ─────────────────────────────────────────────────────────────────────────────

Severity  = Literal["low", "medium", "high"]
Viewport  = Literal["desktop", "tablet", "mobile"]

# Zones critiques → audit plus strict
_HIGH_PRIORITY_ZONES = {"hero", "nav", "primary_cta"}

# Modèle par défaut — Haiku (vision, coût minimal)
DEFAULT_MODEL      = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1024


# ─────────────────────────────────────────────────────────────────────────────
# RESULT OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AuditIssue:
    zone:          str
    problem:       str
    severity:      Severity
    confidence:    float        # 0.0 → 1.0
    suggested_fix: str

    def to_dict(self) -> dict:
        return {
            "zone":          self.zone,
            "problem":       self.problem,
            "severity":      self.severity,
            "confidence":    round(self.confidence, 2),
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class AuditResult:
    # Champs résultat
    readability_pass: bool
    global_score:     int              # 0–100
    issues:           list[AuditIssue] = field(default_factory=list)
    quick_fixes:      list[str]        = field(default_factory=list)

    # Métadonnées
    zone:       str  = ""
    viewport:   str  = "desktop"
    image_path: str  = ""

    # Traçabilité
    model:       str   = DEFAULT_MODEL
    duration_ms: float = 0.0
    error:       str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        return {
            "readability_pass": self.readability_pass,
            "global_score":     self.global_score,
            "issues":           [i.to_dict() for i in self.issues],
            "quick_fixes":      self.quick_fixes,
            "_meta": {
                "zone":        self.zone,
                "viewport":    self.viewport,
                "image_path":  self.image_path,
                "model":       self.model,
                "duration_ms": round(self.duration_ms, 1),
                "error":       self.error,
            },
        }

    def __repr__(self) -> str:
        status = "✓ PASS" if self.readability_pass else "✗ FAIL"
        n      = len(self.issues)
        highs  = sum(1 for i in self.issues if i.severity == "high")
        return (f"[{status}] {self.zone}@{self.viewport} "
                f"score={self.global_score} issues={n}(high={highs})")


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """\
You are a UI readability auditor. Analyze this screenshot and return ONLY valid JSON.

ZONE: {zone}
VIEWPORT: {viewport}
STRICTNESS: {strictness}

EVALUATION CRITERIA — evaluate ALL of these:
1. TEXT CONTRAST (perceived) — is text clearly readable at first glance against its background?
2. BACKGROUND INTERFERENCE — does the background image/texture/pattern compete with text legibility?
3. TEXT HIERARCHY — is the main message readable instantly? Is there visual confusion between heading/body/label?
4. CTA VISIBILITY — is any call-to-action button/link clearly identifiable and distinct?
5. GLOBAL CLARITY — can a user understand this section in under 2 seconds?

FAIL CONDITIONS (set readability_pass = false if ANY of these):
- text contrast is clearly poor (hard to read at normal viewing distance)
- background detail competes with text
- CTA is not visually distinct
- main message takes more than 2 seconds to grasp

RETURN THIS JSON STRUCTURE ONLY — no preamble, no explanation, no markdown:
{{
  "readability_pass": <boolean>,
  "global_score": <integer 0-100, 100=perfect readability, 0=completely unreadable>,
  "issues": [
    {{
      "zone": "{zone}",
      "problem": "<specific problem description, max 15 words>",
      "severity": "<low|medium|high>",
      "confidence": <float 0.0-1.0>,
      "suggested_fix": "<specific actionable fix, max 20 words>"
    }}
  ],
  "quick_fixes": ["<actionable fix 1>", "<actionable fix 2>"]
}}

RULES:
- No aesthetic opinions or image descriptions
- Only usability and readability issues
- Be decisive — no vague or conditional answers
- If nothing is wrong: return empty issues array, readability_pass true, score 85-100
- quick_fixes: only include if there are issues; list the 1-3 most impactful fixes
- severity high = blocks readability, medium = degrades usability, low = minor improvement
"""


def build_audit_prompt(zone: str, viewport: str) -> str:
    strictness = "HIGH — be strict, minor issues should be reported" \
        if zone in _HIGH_PRIORITY_ZONES else \
        "NORMAL — only report significant readability problems"
    return _PROMPT_TEMPLATE.format(
        zone=zone,
        viewport=viewport,
        strictness=strictness,
    )


# ─────────────────────────────────────────────────────────────────────────────
# JSON VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

_REQUIRED_KEYS      = {"readability_pass", "global_score", "issues", "quick_fixes"}
_VALID_SEVERITIES   = {"low", "medium", "high"}
_ISSUE_REQUIRED     = {"zone", "problem", "severity", "confidence", "suggested_fix"}


def _extract_json(text: str) -> str:
    """Extrait le bloc JSON de la réponse (en cas de texte parasite autour)."""
    text = text.strip()
    # Cas idéal : réponse entièrement JSON
    if text.startswith("{"):
        return text
    # Cherche un bloc ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    # Cherche le premier { ... } dans le texte
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1)
    raise ValueError(f"Impossible d'extraire un JSON valide de la réponse : {text[:200]!r}")


def _validate_structure(data: dict, zone: str) -> list[str]:
    """Retourne la liste des erreurs de structure. Vide = valide."""
    errors = []
    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"Clés manquantes : {missing}")
        return errors  # impossible de continuer

    if not isinstance(data["readability_pass"], bool):
        errors.append("readability_pass doit être un booléen")
    if not isinstance(data["global_score"], int) or not (0 <= data["global_score"] <= 100):
        errors.append(f"global_score invalide : {data['global_score']!r}")
    if not isinstance(data["issues"], list):
        errors.append("issues doit être une liste")
    else:
        for i, issue in enumerate(data["issues"]):
            missing_i = _ISSUE_REQUIRED - set(issue.keys())
            if missing_i:
                errors.append(f"Issue[{i}] champs manquants : {missing_i}")
            if issue.get("severity") not in _VALID_SEVERITIES:
                errors.append(f"Issue[{i}] severity invalide : {issue.get('severity')!r}")
            conf = issue.get("confidence")
            if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                errors.append(f"Issue[{i}] confidence invalide : {conf!r}")
    if not isinstance(data.get("quick_fixes"), list):
        errors.append("quick_fixes doit être une liste")
    return errors


def _parse_response(raw: str, zone: str) -> dict:
    """Parse + valide la réponse JSON du modèle. Lève ValueError si invalide."""
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON invalide : {e} — extrait : {json_str[:300]!r}") from e

    errors = _validate_structure(data, zone)
    if errors:
        raise ValueError(f"Structure invalide : {errors}")

    return data


def _build_result(data: dict, zone: str, viewport: str,
                  image_path: str, model: str, duration_ms: float) -> AuditResult:
    """Construit un AuditResult depuis le dict validé."""
    issues = [
        AuditIssue(
            zone=iss.get("zone", zone),
            problem=iss["problem"],
            severity=iss["severity"],
            confidence=float(iss["confidence"]),
            suggested_fix=iss["suggested_fix"],
        )
        for iss in data["issues"]
    ]
    return AuditResult(
        readability_pass=data["readability_pass"],
        global_score=int(data["global_score"]),
        issues=issues,
        quick_fixes=data.get("quick_fixes") or [],
        zone=zone,
        viewport=viewport,
        image_path=str(image_path),
        model=model,
        duration_ms=duration_ms,
        error=None,
    )


def _error_result(zone: str, viewport: str, image_path: str,
                  model: str, duration_ms: float, error: str) -> AuditResult:
    return AuditResult(
        readability_pass=False,
        global_score=0,
        zone=zone,
        viewport=viewport,
        image_path=str(image_path),
        model=model,
        duration_ms=duration_ms,
        error=error,
    )


# ─────────────────────────────────────────────────────────────────────────────
# VISION AUDIT SERVICE
# ─────────────────────────────────────────────────────────────────────────────

class VisionAudit:
    """
    Service d'audit visuel de lisibilité.

    Charge les images en base64, les envoie au modèle vision,
    parse et valide la réponse structurée.
    """

    def __init__(
        self,
        api_key:    str | None = None,
        model:      str        = DEFAULT_MODEL,
        max_tokens: int        = DEFAULT_MAX_TOKENS,
    ):
        self.model      = model
        self.max_tokens = max_tokens
        # api_key conservé pour compatibilité mais les clés sont gérées par MODEL_EXECUTOR
        if api_key:
            os.environ.setdefault("ANTHROPIC_API_KEY", api_key)

    # ── Public API ─────────────────────────────────────────────────────────

    def audit_screenshot(
        self,
        image_path: str | Path,
        zone:       str  = "unknown",
        viewport:   str  = "desktop",
        page:       str  = "",
    ) -> AuditResult:
        """Audite un screenshot PNG unique. Retourne un AuditResult structuré."""
        image_path = Path(image_path)
        t0 = time.perf_counter()

        try:
            b64 = _load_image_b64(image_path)
        except (FileNotFoundError, OSError) as e:
            return _error_result(zone, viewport, image_path, self.model, 0.0, str(e))

        prompt = build_audit_prompt(zone=zone, viewport=viewport)
        try:
            raw = self._call_model(b64, prompt)
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000
            return _error_result(zone, viewport, image_path, self.model, duration_ms, str(e))

        duration_ms = (time.perf_counter() - t0) * 1000

        try:
            data = _parse_response(raw, zone)
        except ValueError as e:
            return _error_result(zone, viewport, image_path, self.model, duration_ms, str(e))

        return _build_result(data, zone, viewport, image_path, self.model, duration_ms)

    def audit_page(
        self,
        captures: list[dict],
    ) -> list[AuditResult]:
        """
        Audite une liste de captures.

        Chaque entrée :
            {"image_path": "...", "zone": "hero", "viewport": "desktop"}
            page et autres champs sont optionnels.
        """
        results = []
        for cap in captures:
            result = self.audit_screenshot(
                image_path=cap["image_path"],
                zone=cap.get("zone", "unknown"),
                viewport=cap.get("viewport", "desktop"),
                page=cap.get("page", ""),
            )
            results.append(result)
        return results

    def audit_from_capture_results(
        self,
        capture_results: list,
    ) -> list[AuditResult]:
        """
        Intégration directe avec screenshot_capture.CaptureResult.
        capture_results : liste de CaptureResult (ok=True uniquement).
        """
        captures = [
            {
                "image_path": cr.path,
                "zone":       cr.zone,
                "viewport":   cr.viewport,
                "page":       cr.page,
            }
            for cr in capture_results
            if cr.ok and cr.path
        ]
        return self.audit_page(captures)

    # ── Internal ───────────────────────────────────────────────────────────

    def _call_model(self, image_b64: str, prompt: str) -> str:
        """Appel vision via MODEL_EXECUTOR. Retourne la réponse texte brute."""
        result = model_execute(
            "img2text",
            prompt,
            data={
                "image_base64":  image_b64,
                "media_type":    "image/png",
                "max_tokens":    self.max_tokens,
                "model_override": self.model,
            },
            provider="anthropic",
        )
        return result["result"]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _load_image_b64(path: Path) -> str:
    """Charge une image PNG et la retourne en base64 UTF-8."""
    if not path.exists():
        raise FileNotFoundError(f"Image introuvable : {path}")
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def summarize_results(results: list[AuditResult]) -> dict:
    """
    Résumé agrégé d'une liste de résultats.
    Utile pour logger l'état global d'une page après audit.
    """
    if not results:
        return {"total": 0, "pass": 0, "fail": 0, "avg_score": 0, "high_issues": 0}

    passing    = [r for r in results if r.readability_pass]
    failing    = [r for r in results if not r.readability_pass]
    avg_score  = sum(r.global_score for r in results) / len(results)
    high_count = sum(
        1 for r in results for i in r.issues if i.severity == "high"
    )
    return {
        "total":       len(results),
        "pass":        len(passing),
        "fail":        len(failing),
        "avg_score":   round(avg_score, 1),
        "high_issues": high_count,
        "zones_failed": [r.zone for r in failing],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS (module-level shortcuts)
# ─────────────────────────────────────────────────────────────────────────────

def audit_screenshot(
    image_path: str | Path,
    zone:       str = "unknown",
    viewport:   str = "desktop",
    api_key:    str | None = None,
    model:      str = DEFAULT_MODEL,
) -> AuditResult:
    """Raccourci fonctionnel — instancie VisionAudit et audite une image."""
    return VisionAudit(api_key=api_key, model=model).audit_screenshot(
        image_path=image_path, zone=zone, viewport=viewport,
    )


def audit_page(
    captures:  list[dict],
    api_key:   str | None = None,
    model:     str = DEFAULT_MODEL,
) -> list[AuditResult]:
    """Raccourci fonctionnel — audite une liste de captures."""
    return VisionAudit(api_key=api_key, model=model).audit_page(captures)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    ap = argparse.ArgumentParser(description="Vision audit de lisibilité")
    ap.add_argument("--image",    help="Chemin vers le PNG à auditer")
    ap.add_argument("--zone",     default="unknown",
                    help="Zone audit (hero, nav, primary_cta, etc.)")
    ap.add_argument("--viewport", default="desktop",
                    choices=["desktop", "tablet", "mobile"])
    ap.add_argument("--batch",    help="Fichier JSON avec liste de captures")
    ap.add_argument("--model",    default=DEFAULT_MODEL,
                    help="Modèle vision à utiliser")
    ap.add_argument("--output",   help="Fichier de sortie JSON (optionnel)")
    args = ap.parse_args()

    if not args.image and not args.batch:
        ap.error("--image ou --batch requis")

    auditor = VisionAudit(model=args.model)

    if args.batch:
        with open(args.batch) as f:
            captures = json.load(f)
        results = auditor.audit_page(captures)
        summary = summarize_results(results)
        output  = {
            "summary": summary,
            "results": [r.to_dict() for r in results],
        }
        _print_batch(results, summary)
    else:
        result = auditor.audit_screenshot(
            image_path=args.image, zone=args.zone, viewport=args.viewport,
        )
        output = result.to_dict()
        _print_single(result)

    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\n→ Résultat sauvegardé : {args.output}")


def _print_single(r: AuditResult) -> None:
    status = "✓ PASS" if r.readability_pass else "✗ FAIL"
    print(f"\n── Audit {r.zone}@{r.viewport} ───────────────────")
    print(f"  {status}  score={r.global_score}/100  ({r.duration_ms:.0f}ms)")
    if r.error:
        print(f"  ⚠ Erreur : {r.error}")
        return
    for iss in r.issues:
        sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(iss.severity, "●")
        print(f"  {sev_icon} [{iss.severity}] {iss.problem}")
        print(f"       → {iss.suggested_fix}")
    if r.quick_fixes:
        print(f"\n  Quick fixes :")
        for fix in r.quick_fixes:
            print(f"    · {fix}")


def _print_batch(results: list[AuditResult], summary: dict) -> None:
    for r in results:
        _print_single(r)
    print(f"\n── Résumé ─────────────────────────────────────")
    print(f"  Total : {summary['total']} | Pass : {summary['pass']} | Fail : {summary['fail']}")
    print(f"  Score moyen : {summary['avg_score']}/100")
    print(f"  Issues high : {summary['high_issues']}")
    if summary["zones_failed"]:
        print(f"  Zones KO : {summary['zones_failed']}")


if __name__ == "__main__":
    _cli()
