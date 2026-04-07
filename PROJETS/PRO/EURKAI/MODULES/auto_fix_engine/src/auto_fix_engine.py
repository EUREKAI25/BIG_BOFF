"""
auto_fix_engine.py — Moteur de correction automatique de lisibilité.

Reçoit des AuditResult (vision_audit), détermine les corrections minimales nécessaires,
les applique comme patches CSS ciblés via data-audit selectors, et boucle jusqu'à convergence.

Principe : correction layer non-destructive — on injecte un <style> block dans le HTML
existant. Zéro re-génération, zéro touche aux renderers.

Usage :
    from auto_fix_engine import AutoFixEngine, run_correction_loop

    engine = AutoFixEngine()

    # Application simple (une passe)
    patch = engine.compute_patch(audit_results)
    fixed_html = engine.apply_patch(html, patch)

    # Loop complète (capture → audit → fix → re-audit)
    loop_result = engine.run_correction_loop(
        initial_html    = html,
        capture_fn      = my_capture_fn,
        audit_fn        = my_audit_fn,
        max_iterations  = 3,
    )
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MAX_ITERATIONS = 3
DEFAULT_TARGET_SCORE   = 70   # global_score minimum pour considérer passe

# Ordre de priorité des zones — les zones critiques sont fixées en premier
ZONE_PRIORITY = ["hero", "nav", "primary_cta", "final_cta", "first_section",
                 "section-1", "section-2", "section-3", "unknown"]

# Sélecteurs d'éléments texte dans une zone
_TEXT_SELECTORS = "h1, h2, h3, h4, p, span, a, label, li, button"


# ─────────────────────────────────────────────────────────────────────────────
# FIX TYPES
# ─────────────────────────────────────────────────────────────────────────────

class FixType(str, Enum):
    TEXT_CONTRAST       = "text_contrast"
    OVERLAY_INCREASE    = "overlay_increase"
    BACKGROUND_SIMPLIFY = "background_simplify"
    CTA_EMPHASIS        = "cta_emphasis"
    TYPOGRAPHY_SAFETY   = "typography_safety"
    TEXT_PLATE          = "text_plate"
    UNKNOWN             = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED TYPES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CorrectionEntry:
    """Une entrée dans le log de corrections."""
    iteration:   int
    zone:        str
    issue:       str        # problem text de l'AuditIssue
    severity:    str
    fix_type:    str        # FixType.value
    description: str        # description humaine de la correction appliquée
    before:      dict       # état du patch avant
    after:       dict       # état du patch après

    def to_dict(self) -> dict:
        return {
            "iteration":   self.iteration,
            "zone":        self.zone,
            "issue":       self.issue,
            "severity":    self.severity,
            "fix_type":    self.fix_type,
            "description": self.description,
        }


@dataclass
class ZonePatch:
    """Corrections CSS pour une zone donnée. Paramètres nommés, pas de CSS brut."""
    zone: str

    # Texte
    text_color:        str | None   = None   # ex: "#ffffff"
    text_shadow:       str | None   = None   # ex: "0 2px 8px rgba(0,0,0,0.8)"
    font_weight:       int | None   = None   # ex: 700
    font_size_scale:   float | None = None   # multiplicateur : 1.1 = +10%

    # Fond / overlay
    overlay_opacity:   float | None = None   # 0.0 → 1.0
    overlay_color:     str | None   = None   # ex: "#000000"
    overlay_gradient:  str | None   = None   # CSS gradient complet
    blur_px:           int | None   = None   # blur en pixels
    bg_color:          str | None   = None

    # CTA
    cta_bg:            str | None   = None
    cta_color:         str | None   = None
    cta_font_weight:   int | None   = None

    # Text plate (fond derrière le texte)
    text_plate_bg:     str | None   = None   # ex: "rgba(0,0,0,0.55)"
    text_plate_radius: str | None   = None   # ex: "4px"

    def is_empty(self) -> bool:
        fields = [
            self.text_color, self.text_shadow, self.font_weight, self.font_size_scale,
            self.overlay_opacity, self.overlay_color, self.overlay_gradient, self.blur_px,
            self.bg_color, self.cta_bg, self.cta_color, self.cta_font_weight,
            self.text_plate_bg, self.text_plate_radius,
        ]
        return all(f is None for f in fields)

    def merge(self, other: "ZonePatch") -> "ZonePatch":
        """Fusionne deux patches (other a la priorité sur les valeurs non-None)."""
        def pick(a, b):
            return b if b is not None else a
        return ZonePatch(
            zone=self.zone,
            text_color=pick(self.text_color, other.text_color),
            text_shadow=pick(self.text_shadow, other.text_shadow),
            font_weight=pick(self.font_weight, other.font_weight),
            font_size_scale=pick(self.font_size_scale, other.font_size_scale),
            overlay_opacity=pick(self.overlay_opacity, other.overlay_opacity),
            overlay_color=pick(self.overlay_color, other.overlay_color),
            overlay_gradient=pick(self.overlay_gradient, other.overlay_gradient),
            blur_px=pick(self.blur_px, other.blur_px),
            bg_color=pick(self.bg_color, other.bg_color),
            cta_bg=pick(self.cta_bg, other.cta_bg),
            cta_color=pick(self.cta_color, other.cta_color),
            cta_font_weight=pick(self.cta_font_weight, other.cta_font_weight),
            text_plate_bg=pick(self.text_plate_bg, other.text_plate_bg),
            text_plate_radius=pick(self.text_plate_radius, other.text_plate_radius),
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and k != "zone"}


@dataclass
class FullPatch:
    """Ensemble des corrections pour toutes les zones d'une page."""
    zones: dict[str, ZonePatch] = field(default_factory=dict)

    def get_or_create(self, zone: str) -> ZonePatch:
        if zone not in self.zones:
            self.zones[zone] = ZonePatch(zone=zone)
        return self.zones[zone]

    def set(self, zone: str, patch: ZonePatch) -> None:
        if zone in self.zones:
            self.zones[zone] = self.zones[zone].merge(patch)
        else:
            self.zones[zone] = patch

    def merge(self, other: "FullPatch") -> "FullPatch":
        result = FullPatch(zones=dict(self.zones))
        for zone, patch in other.zones.items():
            if zone in result.zones:
                result.zones[zone] = result.zones[zone].merge(patch)
            else:
                result.zones[zone] = patch
        return result

    def is_empty(self) -> bool:
        return not self.zones or all(p.is_empty() for p in self.zones.values())

    def to_dict(self) -> dict:
        return {z: p.to_dict() for z, p in self.zones.items() if not p.is_empty()}


@dataclass
class LoopResult:
    """Résultat complet d'une boucle de correction."""
    converged:      bool
    iterations_run: int
    final_html:     str
    final_patch:    FullPatch
    log:            list[CorrectionEntry]
    final_scores:   dict[str, int]   # zone → global_score de la dernière passe
    duration_ms:    float

    def to_dict(self) -> dict:
        return {
            "converged":      self.converged,
            "iterations_run": self.iterations_run,
            "final_patch":    self.final_patch.to_dict(),
            "log":            [e.to_dict() for e in self.log],
            "final_scores":   self.final_scores,
            "duration_ms":    round(self.duration_ms, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ISSUE CLASSIFIER (keyword-based, deterministic)
# ─────────────────────────────────────────────────────────────────────────────

# Règles : liste de (mots-clés requis, FixType)
# Un issue matche la première règle dont TOUS les mots-clés sont présents
_CLASSIFICATION_RULES: list[tuple[list[str], FixType]] = [
    # Overlay / gradient / scrim
    (["overlay"],                                   FixType.OVERLAY_INCREASE),
    (["gradient", "behind"],                        FixType.OVERLAY_INCREASE),
    (["scrim"],                                     FixType.OVERLAY_INCREASE),
    # CTA
    (["cta"],                                       FixType.CTA_EMPHASIS),
    (["call-to-action"],                            FixType.CTA_EMPHASIS),
    (["button", "visible"],                         FixType.CTA_EMPHASIS),
    (["button", "identif"],                         FixType.CTA_EMPHASIS),
    # Background
    (["background", "busy"],                        FixType.BACKGROUND_SIMPLIFY),
    (["background", "complex"],                     FixType.BACKGROUND_SIMPLIFY),
    (["background", "detail"],                      FixType.BACKGROUND_SIMPLIFY),
    (["background", "compet"],                      FixType.BACKGROUND_SIMPLIFY),
    (["image", "compet"],                           FixType.BACKGROUND_SIMPLIFY),
    (["image", "busy"],                             FixType.BACKGROUND_SIMPLIFY),
    # Text plate (règles explicites — pas de match trop large)
    (["text", "background", "plate"],               FixType.TEXT_PLATE),
    (["text", "backdrop"],                          FixType.TEXT_PLATE),
    (["text", "background plate"],                  FixType.TEXT_PLATE),
    # Typography
    (["font", "weight"],                            FixType.TYPOGRAPHY_SAFETY),
    (["font", "size"],                              FixType.TYPOGRAPHY_SAFETY),
    (["too thin"],                                  FixType.TYPOGRAPHY_SAFETY),
    (["too small"],                                 FixType.TYPOGRAPHY_SAFETY),
    # Text contrast (broad — must come after more specific rules)
    (["contrast"],                                  FixType.TEXT_CONTRAST),
    (["readable"],                                  FixType.TEXT_CONTRAST),
    (["legib"],                                     FixType.TEXT_CONTRAST),
    (["visibility"],                                FixType.TEXT_CONTRAST),
    (["hard to read"],                              FixType.TEXT_CONTRAST),
    (["low contrast"],                              FixType.TEXT_CONTRAST),
    (["insufficient"],                              FixType.TEXT_CONTRAST),
]


def classify_issue(problem: str) -> FixType:
    """Classifie un problème texte (AuditIssue.problem) en FixType via keyword matching."""
    lower = problem.lower()
    for keywords, fix_type in _CLASSIFICATION_RULES:
        if all(kw in lower for kw in keywords):
            return fix_type
    return FixType.UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# FIX COMPUTATION (paramétrique, basé sur severity)
# ─────────────────────────────────────────────────────────────────────────────

def compute_fix(fix_type: FixType, severity: str, zone: str,
                current: ZonePatch | None = None) -> ZonePatch:
    """
    Calcule le ZonePatch correspondant à un fix_type + severity.
    Si current est fourni, les valeurs sont incrémentées (pas remplacées).
    Progressive : high → corrections plus agressives.
    """
    cur = current or ZonePatch(zone=zone)
    patch = ZonePatch(zone=zone)

    if fix_type == FixType.TEXT_CONTRAST:
        # Augmenter progressivement : text-shadow d'abord, puis couleur forcée
        if severity == "high":
            patch.text_color  = "#ffffff"
            patch.text_shadow = "0 2px 12px rgba(0,0,0,0.95), 0 1px 4px rgba(0,0,0,0.8)"
        elif severity == "medium":
            patch.text_shadow = "0 1px 8px rgba(0,0,0,0.75)"
        else:
            patch.text_shadow = "0 1px 4px rgba(0,0,0,0.5)"

    elif fix_type == FixType.OVERLAY_INCREASE:
        # Monter l'opacité de l'overlay
        current_opacity = cur.overlay_opacity or 0.0
        if severity == "high":
            patch.overlay_opacity = min(current_opacity + 0.35, 0.75)
            patch.overlay_color   = cur.overlay_color or "#000000"
        elif severity == "medium":
            patch.overlay_opacity = min(current_opacity + 0.20, 0.65)
            patch.overlay_color   = cur.overlay_color or "#000000"
        else:
            patch.overlay_opacity = min(current_opacity + 0.10, 0.50)
            patch.overlay_color   = cur.overlay_color or "#000000"

    elif fix_type == FixType.BACKGROUND_SIMPLIFY:
        # Ajouter blur + overlay léger
        current_blur = cur.blur_px or 0
        if severity == "high":
            patch.blur_px         = min(current_blur + 6, 16)
            patch.overlay_opacity = min((cur.overlay_opacity or 0.0) + 0.20, 0.55)
            patch.overlay_color   = cur.overlay_color or "#000000"
        elif severity == "medium":
            patch.blur_px         = min(current_blur + 3, 10)
            patch.overlay_opacity = min((cur.overlay_opacity or 0.0) + 0.10, 0.40)
            patch.overlay_color   = cur.overlay_color or "#000000"
        else:
            patch.blur_px         = min(current_blur + 2, 6)

    elif fix_type == FixType.CTA_EMPHASIS:
        # Renforcer le CTA : poids + ombre
        if severity == "high":
            patch.cta_font_weight = 800
            patch.text_shadow     = "0 2px 8px rgba(0,0,0,0.7)"
        elif severity == "medium":
            patch.cta_font_weight = 700
        else:
            patch.cta_font_weight = 600

    elif fix_type == FixType.TYPOGRAPHY_SAFETY:
        current_weight = cur.font_weight or 400
        if severity == "high":
            patch.font_weight     = min(current_weight + 300, 800)
            patch.font_size_scale = min((cur.font_size_scale or 1.0) + 0.10, 1.25)
        elif severity == "medium":
            patch.font_weight     = min(current_weight + 200, 700)
            patch.font_size_scale = min((cur.font_size_scale or 1.0) + 0.05, 1.15)
        else:
            patch.font_weight     = min(current_weight + 100, 600)

    elif fix_type == FixType.TEXT_PLATE:
        # Fond derrière le texte
        if severity == "high":
            patch.text_plate_bg     = "rgba(0,0,0,0.65)"
            patch.text_plate_radius = "6px"
        elif severity == "medium":
            patch.text_plate_bg     = "rgba(0,0,0,0.45)"
            patch.text_plate_radius = "4px"
        else:
            patch.text_plate_bg     = "rgba(0,0,0,0.25)"
            patch.text_plate_radius = "4px"

    return patch


# ─────────────────────────────────────────────────────────────────────────────
# CSS GENERATION (ZonePatch → CSS string)
# ─────────────────────────────────────────────────────────────────────────────

def patch_to_css(patch: ZonePatch) -> str:
    """Convertit un ZonePatch en bloc CSS ciblé sur [data-audit="{zone}"]."""
    zone = patch.zone
    sel  = f'[data-audit="{zone}"]'
    rules: list[str] = []

    # ── Texte ────────────────────────────────────────────────────────────────
    text_props: list[str] = []
    if patch.text_color:
        text_props.append(f"color:{patch.text_color}!important")
    if patch.text_shadow:
        text_props.append(f"text-shadow:{patch.text_shadow}!important")
    if patch.font_weight:
        text_props.append(f"font-weight:{patch.font_weight}!important")
    if patch.font_size_scale and patch.font_size_scale != 1.0:
        scale = patch.font_size_scale
        text_props.append(f"font-size:calc(1em * {scale:.2f})!important")

    if text_props:
        rules.append(
            f'{sel} {_TEXT_SELECTORS} {{{";".join(text_props)}}}'
        )

    # ── Overlay (::before pseudo-element sur la zone) ─────────────────────
    if patch.overlay_opacity is not None and patch.overlay_opacity > 0:
        color    = patch.overlay_color or "#000000"
        opacity  = patch.overlay_opacity
        gradient = patch.overlay_gradient or \
            f"linear-gradient(to bottom,{color}00 0%,{color}{_opacity_to_hex(opacity)} 100%)"
        rules.append(f'{sel}{{position:relative!important;isolation:isolate}}')
        rules.append(
            f'{sel}::before{{'
            f'content:"";position:absolute;inset:0;'
            f'background:{gradient};'
            f'z-index:0;pointer-events:none}}'
        )
        # Les enfants directs passent au-dessus de l'overlay
        rules.append(f'{sel}>*{{position:relative;z-index:1}}')

    # ── Blur (sur les images dans la zone) ──────────────────────────────────
    if patch.blur_px:
        rules.append(
            f'{sel} img, {sel} [style*="url("]'
            f'{{filter:blur({patch.blur_px}px)!important}}'
        )

    # ── Background color ────────────────────────────────────────────────────
    if patch.bg_color:
        rules.append(f'{sel}{{background:{patch.bg_color}!important}}')

    # ── CTA ────────────────────────────────────────────────────────────────
    cta_props: list[str] = []
    if patch.cta_bg:
        cta_props.append(f"background:{patch.cta_bg}!important")
    if patch.cta_color:
        cta_props.append(f"color:{patch.cta_color}!important")
    if patch.cta_font_weight:
        cta_props.append(f"font-weight:{patch.cta_font_weight}!important")
    if cta_props:
        rules.append(f'{sel} button, {sel} a[href] {{{";".join(cta_props)}}}')

    # ── Text plate ──────────────────────────────────────────────────────────
    if patch.text_plate_bg:
        radius = patch.text_plate_radius or "4px"
        rules.append(
            f'{sel} h1, {sel} h2, {sel} h3, {sel} p'
            f'{{background:{patch.text_plate_bg};'
            f'border-radius:{radius};'
            f'padding:0.1em 0.3em!important;'
            f'display:inline-block!important}}'
        )

    return "\n".join(rules)


def full_patch_to_css(full_patch: FullPatch) -> str:
    """Convertit un FullPatch complet en bloc CSS injectable."""
    blocks = [patch_to_css(p) for p in full_patch.zones.values() if not p.is_empty()]
    if not blocks:
        return ""
    return "\n/* auto_fix_engine corrections */\n" + "\n".join(blocks) + "\n"


def _opacity_to_hex(opacity: float) -> str:
    """Convertit une opacité (0–1) en hex à 2 chiffres pour CSS color."""
    return format(int(round(opacity * 255)), "02x").upper()


# ─────────────────────────────────────────────────────────────────────────────
# HTML PATCH APPLICATION
# ─────────────────────────────────────────────────────────────────────────────

_PATCH_TAG_OPEN  = "/* [auto_fix_engine] */"
_PATCH_TAG_CLOSE = "/* [/auto_fix_engine] */"


def apply_css_patch(html: str, full_patch: FullPatch) -> str:
    """
    Injecte les corrections CSS dans le HTML existant.
    Remplace un bloc précédent si présent (idempotent entre itérations).
    Injecte juste avant </head>.
    """
    css = full_patch_to_css(full_patch)
    if not css:
        return html

    style_block = (
        f'<style id="auto-fix-engine">'
        f'{_PATCH_TAG_OPEN}{css}{_PATCH_TAG_CLOSE}'
        f'</style>'
    )

    # Supprimer le bloc précédent si présent
    html = re.sub(
        r'<style id="auto-fix-engine">.*?</style>',
        "",
        html,
        flags=re.DOTALL,
    )

    # Injecter avant </head>
    if "</head>" in html:
        html = html.replace("</head>", f"{style_block}</head>", 1)
    else:
        html += style_block

    return html


# ─────────────────────────────────────────────────────────────────────────────
# AUTO FIX ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class AutoFixEngine:
    """
    Moteur de correction automatique de lisibilité.

    Prend des AuditResult (vision_audit), calcule les corrections minimales
    nécessaires, les applique comme CSS patches non-destructifs via data-audit selectors.
    """

    def __init__(
        self,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        target_score:   int = DEFAULT_TARGET_SCORE,
    ):
        self.max_iterations = max_iterations
        self.target_score   = target_score

    # ── Public API ─────────────────────────────────────────────────────────

    def compute_patch(
        self,
        audit_results: list,           # list[AuditResult]
        current_patch: FullPatch | None = None,
        iteration:     int = 1,
    ) -> tuple[FullPatch, list[CorrectionEntry]]:
        """
        Calcule le FullPatch et le log pour une passe d'audit.
        Prend en compte le patch courant pour l'incrément (ne pas réinitialiser).
        """
        # Copier le patch courant pour éviter la mutation de l'objet original
        if current_patch is not None:
            patch = FullPatch(zones={z: p.merge(ZonePatch(zone=z)) for z, p in current_patch.zones.items()})
        else:
            patch = FullPatch()
        log:  list[CorrectionEntry] = []

        # Trier les audits par priorité de zone
        sorted_audits = sorted(
            audit_results,
            key=lambda r: _zone_priority(r.zone),
        )

        for audit_result in sorted_audits:
            if audit_result.readability_pass:
                continue   # cette zone est OK, on ne touche à rien

            zone        = audit_result.zone
            cur_zone_patch = patch.zones.get(zone)

            for issue in audit_result.issues:
                fix_type = classify_issue(issue.problem)
                if fix_type == FixType.UNKNOWN:
                    continue

                before = cur_zone_patch.to_dict() if cur_zone_patch else {}
                new_patch = compute_fix(
                    fix_type=fix_type,
                    severity=issue.severity,
                    zone=zone,
                    current=cur_zone_patch,
                )
                patch.set(zone, new_patch)
                cur_zone_patch = patch.zones[zone]
                after = cur_zone_patch.to_dict()

                if before != after:
                    log.append(CorrectionEntry(
                        iteration=iteration,
                        zone=zone,
                        issue=issue.problem,
                        severity=issue.severity,
                        fix_type=fix_type.value,
                        description=_describe_fix(fix_type, issue.severity, before, after),
                        before=before,
                        after=after,
                    ))

        return patch, log

    def apply_patch(self, html: str, patch: FullPatch) -> str:
        """Applique un FullPatch sur un HTML. Retourne le HTML corrigé."""
        return apply_css_patch(html, patch)

    def run_correction_loop(
        self,
        initial_html:  str,
        capture_fn:    Callable[[str], list],   # html → list[CaptureResult]
        audit_fn:      Callable[[list], list],  # list[CaptureResult] → list[AuditResult]
        max_iterations: int | None = None,
        target_score:   int | None = None,
    ) -> LoopResult:
        """
        Boucle de correction complète : render → capture → audit → fix → repeat.

        capture_fn : prend le HTML (string), retourne list[CaptureResult]
        audit_fn   : prend list[CaptureResult], retourne list[AuditResult]

        Injections de dépendances : pas de couplage direct aux modules screenshot/vision.
        """
        max_iter  = max_iterations or self.max_iterations
        target    = target_score   or self.target_score
        t0        = time.perf_counter()

        current_html  = initial_html
        full_patch    = FullPatch()   # accumulateur — copié à chaque itération
        full_log:     list[CorrectionEntry] = []
        final_scores: dict[str, int] = {}
        converged     = False

        for iteration in range(1, max_iter + 1):
            # ── 1. Capturer ───────────────────────────────────────────────
            captures = capture_fn(current_html)

            # ── 2. Auditer ────────────────────────────────────────────────
            audit_results = audit_fn(captures)

            # Enregistrer les scores courants
            final_scores = {r.zone: r.global_score for r in audit_results}

            # ── 3. Vérifier convergence ───────────────────────────────────
            all_pass = all(r.readability_pass for r in audit_results)
            avg_score = (
                sum(r.global_score for r in audit_results) / len(audit_results)
                if audit_results else 0
            )
            if all_pass or avg_score >= target:
                converged = True
                break

            # ── 4. Calculer + appliquer corrections ───────────────────────
            full_patch, iter_log = self.compute_patch(
                audit_results=audit_results,
                current_patch=full_patch,
                iteration=iteration,
            )
            full_log.extend(iter_log)

            if full_patch.is_empty():
                # Aucune correction possible — arrêt propre
                break

            current_html = apply_css_patch(current_html, full_patch)

        duration_ms = (time.perf_counter() - t0) * 1000
        return LoopResult(
            converged=converged,
            iterations_run=iteration,
            final_html=current_html,
            final_patch=full_patch,
            log=full_log,
            final_scores=final_scores,
            duration_ms=duration_ms,
        )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _zone_priority(zone: str) -> int:
    try:
        return ZONE_PRIORITY.index(zone)
    except ValueError:
        return len(ZONE_PRIORITY)


def _describe_fix(fix_type: FixType, severity: str, before: dict, after: dict) -> str:
    """Génère une description humaine concise de la correction appliquée."""
    if fix_type == FixType.TEXT_CONTRAST:
        if "text_color" in after and "text_color" not in before:
            return f"forced text color to {after['text_color']}"
        if "text_shadow" in after:
            return f"added text shadow (severity={severity})"
    elif fix_type == FixType.OVERLAY_INCREASE:
        prev = before.get("overlay_opacity", 0.0)
        curr = after.get("overlay_opacity", 0.0)
        return f"overlay opacity {prev:.2f} → {curr:.2f}"
    elif fix_type == FixType.BACKGROUND_SIMPLIFY:
        prev_blur = before.get("blur_px", 0)
        curr_blur = after.get("blur_px", 0)
        return f"background blur {prev_blur}px → {curr_blur}px"
    elif fix_type == FixType.CTA_EMPHASIS:
        return f"CTA font-weight → {after.get('cta_font_weight', 700)}"
    elif fix_type == FixType.TYPOGRAPHY_SAFETY:
        prev_w = before.get("font_weight", 400)
        curr_w = after.get("font_weight", 400)
        return f"font-weight {prev_w} → {curr_w}"
    elif fix_type == FixType.TEXT_PLATE:
        return f"added text background plate ({after.get('text_plate_bg', 'rgba(0,0,0,0.5)')})"
    return f"{fix_type.value} fix applied (severity={severity})"


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_correction_loop(
    initial_html:  str,
    capture_fn:    Callable[[str], list],
    audit_fn:      Callable[[list], list],
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    target_score:   int = DEFAULT_TARGET_SCORE,
) -> LoopResult:
    """Raccourci fonctionnel — instancie AutoFixEngine et lance la boucle."""
    return AutoFixEngine(
        max_iterations=max_iterations,
        target_score=target_score,
    ).run_correction_loop(
        initial_html=initial_html,
        capture_fn=capture_fn,
        audit_fn=audit_fn,
    )
