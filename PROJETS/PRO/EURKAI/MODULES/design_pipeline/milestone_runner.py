"""
milestone_runner — moteur d'exécution de milestones design.

Règles :
- Chaque milestone résout ses options, sélectionne de façon déterministe, valide.
- Aucune logique métier ici : tout est injecté via les paramètres.
- Si options vides → MilestoneError. Si validation échoue → MilestoneError.
- JAMAIS de fallback silencieux.
"""

from __future__ import annotations
import random
import time
from typing import Any, Callable


# ─── Exception ────────────────────────────────────────────────────────────────

class MilestoneError(Exception):
    """Échec d'un milestone — pas de fallback, erreur remontée."""
    def __init__(self, milestone_ident: str, reason: str):
        self.milestone_ident = milestone_ident
        self.reason = reason
        super().__init__(f"[{milestone_ident}] {reason}")


# ─── Types ────────────────────────────────────────────────────────────────────

OptionResolver  = Callable[[Any, dict], list]
SelectionRule   = Callable[[list, Any, dict], Any]
Validator       = Callable[[Any, dict], tuple[bool, str]]
Hook            = Callable[[dict, Any], None]


# ─── Sélection déterministe standard ─────────────────────────────────────────

def seed_select(options: list, context: dict, milestone_ident: str) -> Any:
    """
    Sélection déterministe : seed du context + hash du milestone_ident.
    Même seed + même milestone + mêmes options → même résultat.
    """
    seed = context.get("seed", 42)
    salt = abs(hash(milestone_ident)) % 10_000
    return random.Random(seed + salt).choice(options)


# ─── Core ────────────────────────────────────────────────────────────────────

def standard_milestone_run(
    context:         dict,
    milestone_ident: str,
    input_object:    Any,
    option_resolver: OptionResolver,
    selection_rules: SelectionRule,
    output_schema:   dict,
    validators:      list[Validator],
    hooks:           dict[str, Hook] | None = None,
) -> tuple[dict, Any]:
    """
    Exécute un milestone design de façon contrôlée.

    Args:
        context          : contexte accumulé du pipeline (dict mutable)
        milestone_ident  : nom unique du milestone (ex: "choose_layout_strategy")
        input_object     : données d'entrée pour ce milestone
        option_resolver  : fn(input, context) → liste des options autorisées
        selection_rules  : fn(options, input, context) → option sélectionnée
        output_schema    : dict {field: type_or_None} — champs requis dans l'output
        validators       : liste de fn(output, context) → (bool, message)
        hooks            : {"before": fn, "after": fn} optionnel

    Returns:
        (updated_context, selected_output)

    Raises:
        MilestoneError si options vides, validation échoue, ou schema incomplet.
    """
    t0 = time.time()

    # ── Hook before ──────────────────────────────────────────────────────────
    if hooks and "before" in hooks:
        hooks["before"](context, input_object)

    # ── 1. Résoudre les options autorisées ───────────────────────────────────
    options = option_resolver(input_object, context)

    if not options:
        raise MilestoneError(milestone_ident, "option_resolver returned empty list — no valid options")

    _log(context, milestone_ident, f"options={len(options)} available={options[:5]}{'…' if len(options)>5 else ''}")

    # ── 2. Sélection déterministe ────────────────────────────────────────────
    selected = selection_rules(options, input_object, context)

    if selected is None:
        raise MilestoneError(milestone_ident, "selection_rules returned None")

    _log(context, milestone_ident, f"selected={selected!r}  seed={context.get('seed', 42)}")

    # ── 3. Valider le schéma de sortie ───────────────────────────────────────
    _check_schema(selected, output_schema, milestone_ident)

    # ── 4. Valider les règles métier ─────────────────────────────────────────
    for v in validators:
        ok, msg = v(selected, context)
        if not ok:
            raise MilestoneError(milestone_ident, f"validator failed: {msg}")

    # ── 5. Stocker dans le context ───────────────────────────────────────────
    context[milestone_ident] = selected
    context.setdefault("_milestone_log", []).append({
        "ident":    milestone_ident,
        "selected": selected if not isinstance(selected, dict) else list(selected.keys()),
        "options":  len(options),
        "seed":     context.get("seed", 42),
        "ms":       round((time.time() - t0) * 1000),
    })

    # ── Hook after ───────────────────────────────────────────────────────────
    if hooks and "after" in hooks:
        hooks["after"](context, selected)

    return context, selected


# ─── Helpers internes ────────────────────────────────────────────────────────

def _check_schema(output: Any, schema: dict, milestone_ident: str) -> None:
    """Vérifie que output contient tous les champs requis du schema."""
    if not schema:
        return
    if not isinstance(output, dict):
        return  # output scalaire (str, etc.) — schema s'applique pas
    missing = [k for k in schema if k not in output]
    if missing:
        raise MilestoneError(milestone_ident, f"output missing schema fields: {missing}")


def _log(context: dict, milestone_ident: str, msg: str) -> None:
    """Log milestone dans context._debug_log."""
    entry = f"[{milestone_ident}] {msg}"
    context.setdefault("_debug_log", []).append(entry)
    if context.get("verbose"):
        print(entry)
