#!/usr/bin/env python3
"""
pipeline.py — EURKAI Design Pipeline Orchestrator

Moteur d'exécution central. Pas un script de démo. Pas une exécution linéaire.

Flow complet :
    brief
    → contexte de style (dna / palette / theme)
    → design plan (généré, validé, seedé)
    → boucle validation plan (max 5 tentatives, mutation seed)
    → rendu HTML (uniquement après plan valide)
    → capture screenshots
    → audit vision (readability)
    → boucle auto-fix (max 3 itérations)
    → apprentissage (enregistrement des patterns)
    → output

Usage :
    python pipeline.py --brief "Distillerie normande, calvados 1887" --name maison-calva
    python pipeline.py --brief "..." --name "..." --seed 42
    python pipeline.py --brief "..." --name "..." --no-capture --no-audit
    python pipeline.py --brief "..." --name "..." --json
"""

from __future__ import annotations

import argparse
import http.server
import json
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR / "MODULES"
OUTPUT_DIR  = SCRIPT_DIR / "output"

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(MODULES_DIR))          # packages: design_plan, design_validator, …
for _mod in sorted(MODULES_DIR.iterdir()):    # src/* importable directement depuis chaque module
    if _mod.is_dir() and not _mod.name.startswith(("_", ".")):
        sys.path.insert(0, str(_mod))


# ─────────────────────────────────────────────────────────────────────────────
# MODULE IMPORTS — graceful degradation par module
# ─────────────────────────────────────────────────────────────────────────────

_modules: dict[str, bool] = {}

# ── Renderer ──────────────────────────────────────────────────────────────────
try:
    from generate_brand_charter import (
        step_dna, step_psychology, step_palette, step_explore,
        step_build_style_dna, step_theme, generate_landing_page,
    )
    _modules["renderer"] = True
except ImportError as e:
    _modules["renderer"] = False
    _renderer_err = str(e)

# ── Design Plan ───────────────────────────────────────────────────────────────
try:
    from design_plan.src.design_plan import generate_design_plan, DesignPlan
    _modules["design_plan"] = True
except ImportError:
    try:
        from design_plan import generate_design_plan, DesignPlan  # type: ignore
        _modules["design_plan"] = True
    except ImportError:
        _modules["design_plan"] = False

# ── Design Validator ──────────────────────────────────────────────────────────
try:
    from design_validator.src.design_validator import validate_layout
    _modules["design_validator"] = True
except ImportError:
    try:
        from design_validator import validate_layout  # type: ignore
        _modules["design_validator"] = True
    except ImportError:
        _modules["design_validator"] = False

# ── Auto Fix Engine ───────────────────────────────────────────────────────────
try:
    from auto_fix_engine.src.auto_fix_engine import (
        AutoFixEngine, FullPatch, ZonePatch, apply_css_patch, LoopResult,
    )
    _modules["auto_fix_engine"] = True
except ImportError:
    try:
        from auto_fix_engine import AutoFixEngine, FullPatch, ZonePatch, apply_css_patch, LoopResult  # type: ignore
        _modules["auto_fix_engine"] = True
    except ImportError:
        _modules["auto_fix_engine"] = False

# ── Design Learning ───────────────────────────────────────────────────────────
try:
    from design_learning.src.design_learning import (
        DesignLearning, derive_context, derive_context_from_audit,
    )
    _modules["design_learning"] = True
except ImportError:
    try:
        from design_learning import DesignLearning, derive_context, derive_context_from_audit  # type: ignore
        _modules["design_learning"] = True
    except ImportError:
        _modules["design_learning"] = False

# ── Screenshot Capture (requires playwright) ──────────────────────────────────
try:
    from screenshot_capture.src.screenshot_capture import ScreenshotCapture, CaptureResult
    _modules["screenshot_capture"] = True
except ImportError:
    try:
        from screenshot_capture import ScreenshotCapture, CaptureResult  # type: ignore
        _modules["screenshot_capture"] = True
    except ImportError:
        _modules["screenshot_capture"] = False

# ── Vision Audit (requires anthropic) ────────────────────────────────────────
try:
    from vision_audit.src.vision_audit import VisionAudit, AuditResult, summarize_results
    _modules["vision_audit"] = True
except ImportError:
    try:
        from vision_audit import VisionAudit, AuditResult, summarize_results  # type: ignore
        _modules["vision_audit"] = True
    except ImportError:
        _modules["vision_audit"] = False


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

MAX_PLAN_ATTEMPTS      = 5     # tentatives avant régénération complète du plan
MAX_FIX_ITERATIONS     = 3     # itérations auto-fix après rendu
PLAN_REGEN_SEED_OFFSET = 1000  # offset seed pour régénération complète
_SEED_MUTATION_PRIME   = 97    # multiplicateur premier pour mutation seed


# ─────────────────────────────────────────────────────────────────────────────
# DATA OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LogEntry:
    phase:   str
    message: str
    ts:      str  = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data:    dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d: dict = {"phase": self.phase, "message": self.message, "ts": self.ts}
        if self.data:
            d["data"] = self.data
        return d


@dataclass
class PipelineResult:
    status:         str           # "success" | "failure"
    project:        str
    brief:          str
    seed:           int
    attempts:       int           # tentatives de validation du plan
    fix_iterations: int           # itérations auto-fix réalisées
    final_score:    int           # score de lisibilité final (0 si pas d'audit)
    output_path:    str | None    # chemin du HTML final sauvegardé
    log:            list[LogEntry] = field(default_factory=list)
    error:          str | None    = None
    duration_ms:    float         = 0.0

    def to_dict(self) -> dict:
        return {
            "status":         self.status,
            "project":        self.project,
            "seed":           self.seed,
            "attempts":       self.attempts,
            "fix_iterations": self.fix_iterations,
            "final_score":    self.final_score,
            "output_path":    self.output_path,
            "error":          self.error,
            "duration_ms":    round(self.duration_ms, 1),
            "log":            [e.to_dict() for e in self.log],
        }


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL HTTP SERVER — HTML en mémoire, port aléatoire
# ─────────────────────────────────────────────────────────────────────────────

class _InMemoryServer:
    """
    Sert un document HTML depuis la mémoire sur un port local aléatoire.
    Thread-safe. Lifecycle : start() → url → update(html) → stop().
    """

    def __init__(self, html: str):
        self._html_bytes = html.encode("utf-8")
        self._server: http.server.HTTPServer | None = None
        self._thread:  threading.Thread      | None = None
        self._lock = threading.Lock()

    def start(self) -> str:
        """Démarre le serveur et retourne l'URL."""
        server_ref = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                with server_ref._lock:
                    body = server_ref._html_bytes
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache, no-store")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                pass  # silence

        self._server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return f"http://127.0.0.1:{port}/"

    def update(self, html: str) -> None:
        """Mise à jour atomique du contenu HTML servi."""
        new_bytes = html.encode("utf-8")
        with self._lock:
            self._html_bytes = new_bytes

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT EXTRACTION — DesignPlan → layout dict pour design_validator
# ─────────────────────────────────────────────────────────────────────────────

def _extract_layout_from_plan(plan: "DesignPlan") -> dict:
    """
    Construit le layout dict attendu par design_validator depuis un DesignPlan.

    Représente l'INTENTION STRUCTURELLE du plan — pas le HTML rendu.
    La validation détecte les plans auto-contradictoires AVANT tout rendu.

    Règle d'or : si le plan est valide ici, le renderer peut partir de bases saines.
    """
    sections = [
        {
            "type":              s,
            "layout_variant":    s,
            "symmetric":         False,
            "visually_isolated": s == "cta_block",
        }
        for s in plan.section_types
    ]

    global_symmetry = (
        "center" in plan.hero.positioning.lower()
        or "centered" in plan.hero.type.lower()
    )

    return {
        "hero": {
            "type":           plan.hero.type,
            "positioning":    plan.hero.positioning,
            "text_placement": plan.hero.text_placement,
            "media_role":     plan.hero.media_role,
        },
        "sections": sections,
        "structure": {
            "global_symmetry":       global_symmetry,
            "equal_section_heights": False,
            "varying_heights":       True,
            "has_typographic_break": True,
            "density":               plan.composition.density,
            "repeated_layouts":      {},
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# SEED MUTATION
# ─────────────────────────────────────────────────────────────────────────────

def _mutate_seed(base_seed: int, attempt: int) -> int:
    """
    Génère un seed différent pour chaque tentative de validation.
    Utilise un multiplicateur premier pour éviter les collisions entre bases proches.
    attempt=0 → base_seed intact (première tentative = seed demandé par l'utilisateur).
    """
    return base_seed + attempt * _SEED_MUTATION_PRIME


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

class PipelineOrchestrator:
    """
    Moteur d'exécution central du pipeline EURKAI.

    Responsabilités :
    - Contrôle le flow d'exécution de bout en bout
    - Impose la validation avant tout rendu
    - Gère les retries avec mutation de seed
    - Coordonne tous les modules sans couplage direct entre eux
    - Log chaque étape de façon structurée
    - Ne silence jamais les erreurs
    """

    def __init__(
        self,
        output_dir:         Path | str = OUTPUT_DIR,
        learning_db:        Path | str | None = None,
        max_plan_attempts:  int = MAX_PLAN_ATTEMPTS,
        max_fix_iterations: int = MAX_FIX_ITERATIONS,
        enable_capture:     bool = True,
        enable_audit:       bool = True,
        enable_learning:    bool = True,
        verbose:            bool = True,
    ):
        self.output_dir         = Path(output_dir)
        self.max_plan_attempts  = max_plan_attempts
        self.max_fix_iterations = max_fix_iterations
        self.enable_capture     = enable_capture and _modules.get("screenshot_capture", False)
        self.enable_audit       = enable_audit   and _modules.get("vision_audit", False)
        self.enable_learning    = enable_learning and _modules.get("design_learning", False)
        self.verbose            = verbose

        self._learning: DesignLearning | None = None
        if self.enable_learning:
            db_path = learning_db or (self.output_dir / "design_patterns.json")
            try:
                self._learning = DesignLearning(db_path)
            except Exception as e:
                self._print(f"⚠️  design_learning init failed: {e} — learning disabled")
                self.enable_learning = False

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC ENTRYPOINT
    # ──────────────────────────────────────────────────────────────────────────

    def run(
        self,
        brief:        str,
        project_name: str,
        seed:         int = 42,
        style_dna:    dict | None = None,
        theme_hints:  dict | None = None,
        harmony:      str = "complementary",
        site_family:  str = "",
    ) -> PipelineResult:
        """
        Exécute le pipeline complet.

        Args:
            brief        : texte libre du brief projet
            project_name : identifiant unique du projet
            seed         : seed déterministe de départ
            style_dna    : dict optionnel pour influencer design_plan
            theme_hints  : dict optionnel {archetype, layout} pour forcer des choix
            harmony      : harmonie de palette
            site_family  : famille de site ("ecommerce_catalog", "editorial_magazine", ...)

        Returns:
            PipelineResult — statut, métriques, log complet
        """
        t0  = time.time()
        log: list[LogEntry] = []

        result = PipelineResult(
            status="failure",
            project=project_name,
            brief=brief,
            seed=seed,
            attempts=0,
            fix_iterations=0,
            final_score=0,
            output_path=None,
            log=log,
        )

        def _log(phase: str, msg: str, **data) -> None:
            entry = LogEntry(phase=phase, message=msg, data=data)
            log.append(entry)
            if self.verbose:
                ts = entry.ts[11:19]
                print(f"  [{ts}] [{phase:14s}] {msg}")
                for k, v in data.items():
                    v_str = str(v)
                    if len(v_str) > 120:
                        v_str = v_str[:117] + "…"
                    print(f"                         {k}: {v_str}")

        try:
            # ── PHASE 1 : Contexte de style ───────────────────────────────────
            _log("context", "Building style context")
            dna, exploration, palette_output, preset, css = \
                self._phase_build_context(brief, project_name, _log)

            # ── PHASE 2 : Design Plan — boucle de validation ──────────────────
            _log("design_plan", "Starting plan generation + validation loop",
                 max_attempts=self.max_plan_attempts)

            plan, attempts = self._phase_validate_plan_loop(
                brief=brief, seed=seed,
                style_dna=style_dna, theme_hints=theme_hints, log_fn=_log,
            )
            result.attempts = attempts

            if plan is None:
                # Régénération complète avec seed décalé
                regen_seed = seed + PLAN_REGEN_SEED_OFFSET
                _log("design_plan",
                     "All attempts failed — full plan regeneration with new seed",
                     regen_seed=regen_seed)

                plan, regen_attempts = self._phase_validate_plan_loop(
                    brief=brief, seed=regen_seed,
                    style_dna=style_dna, theme_hints=theme_hints, log_fn=_log,
                )
                result.attempts += regen_attempts

                if plan is None:
                    raise RuntimeError(
                        f"Design plan validation failed after {result.attempts} total attempts. "
                        "Cannot render — invalid layout structure."
                    )

            _log("design_plan", "Plan validated ✓",
                 layout_strategy=plan.layout_strategy,
                 profile=plan.brief_profile,
                 seed=plan.seed,
                 sections=plan.section_types)

            # ── PHASE 3 : Apprentissage proactif (avant rendu) ────────────────
            preemptive_patch: FullPatch | None = None
            if self.enable_learning and self._learning:
                preemptive_patch = self._phase_preemptive_learning(plan, _log)

            # ── PHASE 4 : Rendu (uniquement après plan valide) ────────────────
            _log("render", "Generating layout HTML",
                 seed=plan.seed,
                 layout=plan.layout_strategy,
                 hero=plan.hero.type,
                 sections=plan.section_types)
            html = self._phase_render(
                brief=brief, project_name=project_name,
                dna=dna, exploration=exploration,
                preset=preset, css=css,
                palette_output=palette_output,
                render_seed=plan.seed,
                harmony=harmony, site_family=site_family,
                plan=plan,
            )

            # Appliquer le patch proactif si disponible
            if (preemptive_patch and not preemptive_patch.is_empty()
                    and _modules.get("auto_fix_engine")):
                html = apply_css_patch(html, preemptive_patch)
                _log("render", "Preemptive learning patch applied",
                     zones=list(preemptive_patch.zones.keys()))

            _log("render", "HTML generated",
                 size_kb=round(len(html) / 1024, 1))

            # ── PHASE 5 : Capture + Audit + Auto-fix ─────────────────────────
            final_html, fix_iterations, final_score, loop_result, initial_scores = \
                self._phase_fix_loop(html=html, project_name=project_name, log_fn=_log)

            result.fix_iterations = fix_iterations
            result.final_score    = final_score

            # ── PHASE 6 : Apprentissage (après fix) ───────────────────────────
            if (self.enable_learning and self._learning
                    and loop_result is not None
                    and loop_result.iterations_run > 0):
                self._phase_record_learning(loop_result, initial_scores, _log)

            # ── PHASE 7 : Sauvegarde des outputs ─────────────────────────────
            out_path = self._phase_save_output(
                html=final_html, project_name=project_name,
                plan=plan, result=result, log_fn=_log,
            )
            result.output_path = str(out_path)
            result.status      = "success"

            _log("output", "Pipeline complete ✓", path=str(out_path))

        except Exception as exc:
            result.error  = str(exc)
            result.status = "failure"
            _log("error", f"Pipeline failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        result.duration_ms = (time.time() - t0) * 1000
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 1 — Contexte de style
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_build_context(
        self,
        brief:        str,
        project_name: str,
        log_fn:       Callable,
    ) -> tuple:
        """
        Construit le contexte de style : dna, exploration, palette, preset, css.
        Retourne des None si les modules sont indisponibles (graceful degradation).
        Le pipeline continue même sans contexte de style — le renderer a ses propres fallbacks.
        """
        if not _modules.get("renderer"):
            log_fn("context", "Renderer unavailable — context skipped",
                   error=_renderer_err if "_renderer_err" in dir() else "unknown")
            return None, None, None, None, None

        try:
            dna         = step_dna(brief, project_name)
            rec         = step_psychology(dna)
            palette_out = step_palette(dna, rec)
            exploration = step_explore(dna)
            style_dna   = step_build_style_dna(dna, palette_out, rec)
            preset, css = step_theme(style_dna)

            log_fn("context", "Style context ready",
                   dna=dna is not None,
                   palette=palette_out is not None,
                   theme=preset is not None)

            return dna, exploration, palette_out, preset, css

        except Exception as e:
            log_fn("context", f"Context build failed — pipeline continues: {e}")
            return None, None, None, None, None

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 2 — Validation du design plan (boucle avec mutation seed)
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_validate_plan_loop(
        self,
        brief:       str,
        seed:        int,
        style_dna:   dict | None,
        theme_hints: dict | None,
        log_fn:      Callable,
    ) -> tuple["DesignPlan | None", int]:
        """
        Génère et valide un design plan. Mute le seed à chaque échec.

        Checks par ordre :
        1. generate_design_plan() réussit sans exception
        2. plan.validate() → aucune erreur interne
        3. validate_layout(plan, layout) → PASS (contraintes structurelles)

        Returns:
            (DesignPlan, attempts_count) — plan=None si toutes tentatives échouent
        """
        if not _modules.get("design_plan"):
            log_fn("design_plan",
                   "design_plan module unavailable — validation loop skipped")
            return None, 0

        for attempt in range(1, self.max_plan_attempts + 1):
            current_seed = _mutate_seed(seed, attempt - 1)

            # ── 1. Génération ──────────────────────────────────────────────
            try:
                plan = generate_design_plan(
                    brief=brief,
                    seed=current_seed,
                    style_dna=style_dna,
                    theme_hints=theme_hints,
                )
            except Exception as e:
                log_fn("design_plan",
                       f"Generation error (attempt {attempt}/{self.max_plan_attempts})",
                       seed=current_seed, error=str(e))
                continue

            # ── 2. Validation interne (plan.validate()) ────────────────────
            plan_errors = plan.validate()
            if plan_errors:
                log_fn("design_plan",
                       f"Internal validation FAIL (attempt {attempt}/{self.max_plan_attempts})",
                       seed=current_seed, errors=plan_errors)
                continue

            # ── 3. Validation structurelle (design_validator) ──────────────
            if _modules.get("design_validator"):
                layout  = _extract_layout_from_plan(plan)
                vresult = validate_layout(plan.to_dict(), layout)

                if not vresult.valid:
                    log_fn("design_plan",
                           f"Structural validation FAIL (attempt {attempt}/{self.max_plan_attempts})",
                           seed=current_seed,
                           score=vresult.score,
                           fail_reasons=vresult.fail_reasons)
                    continue

                log_fn("design_plan",
                       f"Structural validation PASS (attempt {attempt}/{self.max_plan_attempts})",
                       seed=current_seed, score=vresult.score)
            else:
                log_fn("design_plan",
                       f"design_validator unavailable — using plan.validate() only "
                       f"(attempt {attempt}/{self.max_plan_attempts})",
                       seed=current_seed)

            # Succès
            return plan, attempt

        # Toutes les tentatives ont échoué
        log_fn("design_plan",
               f"All {self.max_plan_attempts} attempts failed",
               base_seed=seed)
        return None, self.max_plan_attempts

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 3 — Apprentissage proactif (avant rendu)
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_preemptive_learning(
        self,
        plan:   "DesignPlan",
        log_fn: Callable,
    ) -> "FullPatch | None":
        """
        Interroge la base de patterns pour suggérer des corrections proactives
        avant le premier rendu. Basé sur les zones critiques du plan.
        """
        if not self._learning:
            return None

        try:
            # Contextes partiels pour les zones critiques
            zone_contexts = [
                derive_context_from_audit("hero",        None),
                derive_context_from_audit("nav",         None),
                derive_context_from_audit("final_cta",   None),
            ]

            patch = self._learning.suggest_preemptive_adjustments(zone_contexts)

            if patch and not patch.is_empty():
                log_fn("learning",
                       "Preemptive patch suggested from stored patterns",
                       zones=list(patch.zones.keys()))
                return patch

            log_fn("learning", "No relevant patterns found — no preemptive patch")

        except Exception as e:
            log_fn("learning", f"Preemptive learning failed (non-blocking): {e}")

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 4 — Rendu HTML
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_render(
        self,
        brief:          str,
        project_name:   str,
        dna,
        exploration,
        preset:         dict | None,
        css:            str  | None,
        palette_output,
        render_seed:    int,
        harmony:        str,
        site_family:    str,
        plan=None,
    ) -> str:
        """
        Génère le HTML de la landing page via le renderer.
        Lève RuntimeError si le renderer est indisponible ou retourne du HTML vide.
        Le rendu ne se produit QUE si le plan a validé.
        plan (DesignPlan) est passé au renderer comme source de vérité structurelle.
        """
        if not _modules.get("renderer"):
            raise RuntimeError(
                "Renderer (generate_brand_charter) is unavailable. "
                "Cannot generate HTML."
            )

        html = generate_landing_page(
            project_name=project_name,
            brief_text=brief,
            dna=dna,
            exploration=exploration,
            preset=preset,
            css=css or "",
            render_seed=render_seed,
            palette_output=palette_output,
            harmony=harmony,
            site_family=site_family,
            plan=plan,
        )

        if not html or not html.strip():
            raise RuntimeError("Renderer returned empty HTML.")

        return html

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 5 — Boucle capture + audit + auto-fix
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_fix_loop(
        self,
        html:         str,
        project_name: str,
        log_fn:       Callable,
    ) -> tuple[str, int, int, "LoopResult | None", dict]:
        """
        Boucle de correction visuelle :
        capture → audit → si pass: break → patch → re-render → repeat

        Returns:
            (final_html, iterations_run, final_score, loop_result, initial_scores)
        """
        if not self.enable_capture or not self.enable_audit:
            log_fn("fix_loop", "Capture/audit disabled — skipping fix loop",
                   capture=self.enable_capture,
                   audit=self.enable_audit)
            return html, 0, 0, None, {}

        if not _modules.get("auto_fix_engine"):
            log_fn("fix_loop", "auto_fix_engine unavailable — skipping fix loop")
            return html, 0, 0, None, {}

        capturer = ScreenshotCapture(
            output_root=str(self.output_dir / project_name / "captures")
        )
        auditor = VisionAudit()
        engine  = AutoFixEngine(
            max_iterations=self.max_fix_iterations,
            target_score=70,
        )

        server = _InMemoryServer(html)
        url    = server.start()
        log_fn("fix_loop", "Local HTTP server started", url=url)

        current_html   = html
        current_patch  = FullPatch()
        correction_log: list = []
        initial_scores: dict[str, int] = {}
        final_scores:   dict[str, int] = {}
        iterations_run = 0
        converged      = False

        try:
            for iteration in range(1, self.max_fix_iterations + 1):
                iterations_run = iteration

                log_fn("fix_loop", f"Iteration {iteration}/{self.max_fix_iterations}")

                # ── Mise à jour du serveur avec le HTML courant ───────────────
                server.update(current_html)
                time.sleep(0.4)  # délai stabilisation

                # ── Capture ───────────────────────────────────────────────────
                try:
                    capture_results = capturer.capture_all_zones(
                        url=url,
                        site=project_name,
                        page=f"iter_{iteration}",
                    )
                except Exception as e:
                    log_fn("fix_loop", f"Capture failed (iteration {iteration}): {e}")
                    break

                ok_captures = [c for c in capture_results if c.ok]
                if not ok_captures:
                    log_fn("fix_loop", "No successful captures — stopping loop")
                    break

                log_fn("fix_loop", "Zones captured",
                       total=len(capture_results), ok=len(ok_captures))

                # ── Audit vision ──────────────────────────────────────────────
                try:
                    audit_results = auditor.audit_from_capture_results(ok_captures)
                except Exception as e:
                    log_fn("fix_loop", f"Vision audit failed (iteration {iteration}): {e}")
                    break

                summary = summarize_results(audit_results)

                # Scores initiaux enregistrés à la première itération
                if iteration == 1:
                    initial_scores = {r.zone: r.global_score for r in audit_results}

                final_scores = {r.zone: r.global_score for r in audit_results}

                log_fn("fix_loop", "Audit complete",
                       pass_count=summary.get("pass", 0),
                       fail_count=summary.get("fail", 0),
                       avg_score=summary.get("avg_score", 0),
                       high_issues=summary.get("high_issues", 0))

                # ── Vérification convergence ──────────────────────────────────
                all_pass = all(r.readability_pass for r in audit_results)
                if all_pass:
                    log_fn("fix_loop",
                           f"All zones pass readability — converged at iteration {iteration}")
                    converged = True
                    break

                # ── Calcul et application du patch ────────────────────────────
                try:
                    new_patch, iter_log = engine.compute_patch(
                        audit_results=audit_results,
                        current_patch=current_patch,
                        iteration=iteration,
                    )
                except Exception as e:
                    log_fn("fix_loop", f"Patch computation failed: {e}")
                    break

                if new_patch.is_empty():
                    log_fn("fix_loop", "Patch is empty — no further corrections possible")
                    converged = True
                    break

                try:
                    current_html  = engine.apply_patch(current_html, new_patch)
                    current_patch = new_patch
                    correction_log.extend(iter_log)
                except Exception as e:
                    log_fn("fix_loop", f"Patch application failed: {e}")
                    break

                log_fn("fix_loop",
                       f"Patch applied ({len(iter_log)} corrections)",
                       zones=list(new_patch.zones.keys()))

        finally:
            server.stop()
            log_fn("fix_loop", "Local HTTP server stopped")

        # ── Résultat consolidé ───────────────────────────────────────────────
        loop_result = LoopResult(
            converged=converged,
            iterations_run=iterations_run,
            final_html=current_html,
            final_patch=current_patch,
            log=correction_log,
            final_scores=final_scores,
            duration_ms=0.0,
        )

        avg_final = (
            round(sum(final_scores.values()) / len(final_scores))
            if final_scores else 0
        )

        log_fn("fix_loop", "Fix loop complete",
               converged=converged,
               iterations=iterations_run,
               avg_final_score=avg_final)

        return current_html, iterations_run, avg_final, loop_result, initial_scores

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 6 — Apprentissage post-fix
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_record_learning(
        self,
        loop_result:    "LoopResult",
        initial_scores: dict,
        log_fn:         Callable,
    ) -> None:
        """
        Enregistre les patterns de correction efficaces dans la base d'apprentissage.
        Filtrage : uniquement les corrections avec amélioration ≥ seuil minimal.
        """
        if not self._learning:
            return

        # RC proxy minimal — derive_context a besoin d'un RC pour les couleurs
        # On passe un RC neutre ; l'important est que les zones correspondent
        rc_proxy: dict = {
            "bg":           "#ffffff",
            "fg":           "#111111",
            "bg_art":       "",
            "hero_pattern": "asymmetric",
        }

        try:
            pattern_ids = self._learning.record_from_loop_result(
                loop_result=loop_result,
                initial_scores=initial_scores,
                rc=rc_proxy,
            )
            if pattern_ids:
                log_fn("learning",
                       f"Recorded {len(pattern_ids)} correction pattern(s)",
                       pattern_ids=pattern_ids)
            else:
                log_fn("learning",
                       "No patterns recorded (improvement below threshold)")
        except Exception as e:
            log_fn("learning", f"Pattern recording failed (non-blocking): {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 7 — Sauvegarde des outputs
    # ──────────────────────────────────────────────────────────────────────────

    def _phase_save_output(
        self,
        html:         str,
        project_name: str,
        plan:         "DesignPlan | None",
        result:       PipelineResult,
        log_fn:       Callable,
    ) -> Path:
        """
        Sauvegarde les artefacts du pipeline :
        - landing_<ts>.html  : HTML final (post fix-loop)
        - design_plan_<ts>.json : le plan validé
        - pipeline_result_<ts>.json : métriques du pipeline
        """
        slug    = project_name.lower().replace(" ", "_").replace("-", "_")
        out_dir = self.output_dir / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # HTML final
        html_path = out_dir / f"landing_{ts}.html"
        html_path.write_text(html, encoding="utf-8")

        # Design plan
        if plan is not None:
            plan_path = out_dir / f"design_plan_{ts}.json"
            plan_path.write_text(plan.to_json(indent=2, include_meta=True),
                                  encoding="utf-8")
        else:
            plan_path = None

        # Pipeline result (sans le log complet pour garder le JSON léger)
        result_data = {k: v for k, v in result.to_dict().items() if k != "log"}
        result_data["log_entries"] = len(result.log)
        result_path = out_dir / f"pipeline_result_{ts}.json"
        result_path.write_text(json.dumps(result_data, indent=2), encoding="utf-8")

        log_fn("output", "Artefacts saved",
               html=str(html_path),
               plan=str(plan_path) if plan_path else None,
               result=str(result_path))

        return html_path

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers internes
    # ──────────────────────────────────────────────────────────────────────────

    def _print(self, msg: str) -> None:
        if self.verbose:
            print(f"  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    brief:            str,
    project_name:     str,
    seed:             int = 42,
    output_dir:       str | Path = OUTPUT_DIR,
    harmony:          str = "complementary",
    site_family:      str = "",
    enable_capture:   bool = True,
    enable_audit:     bool = True,
    enable_learning:  bool = True,
    verbose:          bool = True,
    generate_charter: bool = False,
) -> PipelineResult:
    """
    Convenience function — crée un PipelineOrchestrator et exécute run().

    Pour les use-cases programmatiques simples.
    Pour un contrôle fin, instancier PipelineOrchestrator directement.
    """
    orchestrator = PipelineOrchestrator(
        output_dir=output_dir,
        enable_capture=enable_capture,
        enable_audit=enable_audit,
        enable_learning=enable_learning,
        verbose=verbose,
    )
    result = orchestrator.run(
        brief=brief,
        project_name=project_name,
        seed=seed,
        harmony=harmony,
        site_family=site_family,
    )

    if generate_charter and result.output_path:
        try:
            import generate_brand_charter as _gbc
            charter_dir = Path(result.output_path).parent / "charter"
            charter_dir.mkdir(parents=True, exist_ok=True)
            dna        = _gbc.step_dna(brief, project_name)
            rec        = _gbc.step_psychology(dna)
            palette    = _gbc.step_palette(dna, rec)
            style_dna  = _gbc.step_build_style_dna(dna, palette, rec)
            preset, css = _gbc.step_theme(style_dna)
            html       = _gbc.generate_html(dna, rec, palette, _gbc.step_explore(dna), style_dna, preset)
            (charter_dir / "brand_charter.html").write_text(html, encoding="utf-8")
            (charter_dir / "theme.css").write_text(css, encoding="utf-8")
            if verbose:
                print(f"[charter] Charte générée → {charter_dir}")
        except Exception as _e:
            if verbose:
                print(f"[charter] Erreur : {_e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _print_module_status() -> None:
    """Affiche le statut de chaque module du pipeline."""
    print("\n  Modules disponibles :")
    for mod, ok in sorted(_modules.items()):
        icon = "✓" if ok else "✗"
        print(f"    [{icon}] {mod}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EURKAI Design Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python pipeline.py --brief "Distillerie normande, calvados artisanal" --name maison-calva
  python pipeline.py --brief "..." --name "..." --seed 42 --harmony analogous
  python pipeline.py --brief "..." --name "..." --no-capture --no-audit
  python pipeline.py --brief "..." --name "..." --json
        """,
    )

    parser.add_argument("--brief",      required=False, default="",
                        help="Brief texte libre du projet")
    parser.add_argument("--name",       required=False, default="",
                        help="Identifiant unique du projet (slug)")
    parser.add_argument("--seed",       type=int, default=42,
                        help="Seed déterministe de départ (défaut: 42)")
    parser.add_argument("--output",     default=str(OUTPUT_DIR),
                        help=f"Dossier de sortie (défaut: {OUTPUT_DIR})")
    parser.add_argument("--harmony",    default="complementary",
                        choices=["complementary", "analogous", "triadic", "monochromatic"],
                        help="Harmonie de palette (défaut: complementary)")
    parser.add_argument("--site-family", default="",
                        help="Famille de site (ex: ecommerce_catalog, editorial_magazine)")
    parser.add_argument("--no-capture",  action="store_true",
                        help="Désactiver la capture de screenshots")
    parser.add_argument("--no-audit",    action="store_true",
                        help="Désactiver l'audit vision")
    parser.add_argument("--no-learning", action="store_true",
                        help="Désactiver l'apprentissage des patterns")
    parser.add_argument("--modules",     action="store_true",
                        help="Afficher le statut des modules et quitter")
    parser.add_argument("--quiet",       action="store_true",
                        help="Supprimer les logs intermédiaires")
    parser.add_argument("--json",        action="store_true",
                        help="Sortie JSON uniquement (implique --quiet)")

    args = parser.parse_args()

    if args.modules:
        _print_module_status()
        sys.exit(0)

    if not args.brief or not args.name:
        parser.error("--brief and --name are required (unless --modules is used)")

    quiet   = args.quiet or args.json
    verbose = not quiet

    if not quiet:
        print(f"\n{'═' * 62}")
        print(f"  EURKAI Pipeline Orchestrator")
        print(f"{'═' * 62}")
        print(f"  Project : {args.name}")
        print(f"  Brief   : {args.brief[:72]}{'…' if len(args.brief) > 72 else ''}")
        print(f"  Seed    : {args.seed}")
        print(f"  Output  : {args.output}")
        print(f"  Capture : {'yes' if not args.no_capture else 'no'}")
        print(f"  Audit   : {'yes' if not args.no_audit else 'no'}")
        print()

    result = run_pipeline(
        brief=args.brief,
        project_name=args.name,
        seed=args.seed,
        output_dir=args.output,
        harmony=args.harmony,
        site_family=args.site_family,
        enable_capture=not args.no_capture,
        enable_audit=not args.no_audit,
        enable_learning=not args.no_learning,
        verbose=verbose,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    elif not quiet:
        icon = "✅" if result.status == "success" else "❌"
        print(f"\n{icon} {result.status.upper()}")
        print(f"   Attempts      : {result.attempts}")
        print(f"   Fix iterations: {result.fix_iterations}")
        print(f"   Final score   : {result.final_score}")
        if result.output_path:
            print(f"   Output        : {result.output_path}")
        if result.error:
            print(f"   Error         : {result.error}")
        print(f"   Duration      : {result.duration_ms:.0f}ms")

    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
