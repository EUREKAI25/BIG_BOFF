"""
pipeline_v2 — Orchestrateur du pipeline design v2 à milestones stricts.

Interface identique à pipeline.run_pipeline() pour remplacement transparent :
    run_pipeline_v2(brief, project_name, seed, ...) → dict

Le pipeline exécute PIPELINE_MILESTONES dans l'ordre et renvoie un résultat
structuré compatible avec ce qu'attendait generate_ui.py.

Différences vs pipeline v1 :
- Aucun fallback silencieux
- DesignPlan strictement composé depuis les option_pools
- Rendu fidèle au plan, zéro override
- validate_render_contract() vérifie le contrat après rendu
- MilestoneError est remontée telle quelle (pas catchée)
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .milestones import PIPELINE_MILESTONES
from .milestone_runner import MilestoneError
from .render_validator import validate_render_contract


# ─── Output dir ───────────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
OUTPUT_DIR = _HERE.parent.parent / "output"


def run_pipeline_v2(
    brief:          str,
    project_name:   str       = "projet",
    seed:           int       = 42,
    palette:        dict      = None,
    harmony:        str       = "analogous",
    site_family:    str | None = None,
    enable_capture: bool      = False,
    enable_audit:   bool      = False,
    output_dir:     Path      = None,
    verbose:        bool      = False,
    **kwargs,
) -> dict:
    """
    Exécute le pipeline design v2 complet.

    Args:
        brief        : texte du brief
        project_name : nom du projet (utilisé dans le HTML)
        seed         : graine déterministe (reproduit le même output avec le même brief)
        palette      : palette déjà résolue (dict optionnel)
        harmony      : non utilisé en v2 (conservé pour compatibilité interface)
        site_family  : non utilisé en v2 (conservé pour compatibilité)
        enable_capture / enable_audit : non utilisés en v2 (conservé pour compatibilité)
        output_dir   : répertoire de sortie (défaut: output/)
        verbose      : active les logs console

    Returns:
        dict avec :
            html         : HTML rendu
            output_path  : Path du fichier sauvegardé
            plan         : DesignPlan dict
            milestone_log: liste des milestones exécutés
            seed         : seed utilisé
            duration_ms  : durée totale en ms
            validated    : bool — contrat de rendu validé
            errors       : list[str] — erreurs de validation (vide si ok)
    """
    t0 = time.time()

    out_dir = output_dir or OUTPUT_DIR
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Contexte initial ──────────────────────────────────────────────────────
    context: dict[str, Any] = {
        "brief":        brief,
        "project_name": project_name,
        "brand_name":   project_name,
        "seed":         seed,
        "palette":      palette or {},
        "verbose":      verbose,
        "_milestone_log": [],
        "_debug_log":   [],
    }

    # ── Exécution des milestones ──────────────────────────────────────────────
    for milestone_ident, run_fn in PIPELINE_MILESTONES:
        context, _ = run_fn(context)
        if verbose:
            print(f"  ✓ {milestone_ident}")

    # ── Résultats ─────────────────────────────────────────────────────────────
    html = context.get("render_from_plan", "")
    plan = context.get("validate_design_plan", context.get("compose_design_plan", {}))

    # ── Validation contrat ────────────────────────────────────────────────────
    validated, contract_errors = validate_render_contract(html, plan)

    # ── Sauvegarde ────────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    filename = f"{safe_name}_{seed}_{ts}.html"
    output_path = out_dir / filename

    output_path.write_text(html, encoding="utf-8")

    duration_ms = round((time.time() - t0) * 1000)

    if verbose:
        status = "✓ OK" if validated else f"⚠ {len(contract_errors)} erreurs contrat"
        print(f"\n[pipeline_v2] {project_name} — seed={seed} — {duration_ms}ms — {status}")
        if contract_errors:
            for e in contract_errors:
                print(f"  ⚠ {e}")
        print(f"  → {output_path}")

    return {
        "html":          html,
        "output_path":   output_path,
        "output_paths":  [output_path],
        "plan":          plan,
        "milestone_log": context.get("_milestone_log", []),
        "debug_log":     context.get("_debug_log", []),
        "seed":          seed,
        "duration_ms":   duration_ms,
        "validated":     validated,
        "errors":        contract_errors,
        # Compatibilité generate_ui.py
        "final_score":   1.0 if validated else 0.8,
        "charter_paths": [],
    }
