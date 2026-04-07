"""
design_learning.py — Couche d'apprentissage heuristique du système de design.

Observe les corrections appliquées par auto_fix_engine, stocke les patterns
efficaces, et les réutilise en amont pour améliorer les générations futures.

PRINCIPE : mémoire structurée + réutilisation déterministe.
Pas de ML. Pas de probabilités. Scoring par correspondance de contexte.

Usage :
    from design_learning import DesignLearning, derive_context

    db = DesignLearning("data/design_patterns.json")

    # Après une boucle de correction réussie
    db.record_from_loop_result(loop_result, initial_scores, theme_context=rc)

    # Avant le premier render
    ctx  = derive_context(zone="hero", rc=rc)
    patch = db.suggest_preemptive_adjustments([ctx])

    # Statistiques
    print(db.stats())
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

_DB_VERSION     = 1
_MAX_PATTERNS   = 500       # anti-surcharge : au-delà, les moins utilisés sont purgés
_MIN_MATCH_SCORE = 2        # score minimum pour qu'un pattern soit utilisé
_MAX_SUGGESTIONS = 3        # jamais plus de 3 patterns appliqués à la fois
_MIN_IMPROVEMENT = 5        # amélioration minimale (points de score) pour enregistrer

# Dimensions de contexte et leurs poids dans le matching
_CONTEXT_WEIGHTS = {
    "zone":             2,    # la zone est la dimension la plus discriminante
    "background_type":  1,
    "text_color_class": 1,
    "theme_type":       1,
}
_MAX_SCORE = sum(_CONTEXT_WEIGHTS.values())   # = 5


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN OBJECT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Pattern:
    """Un pattern de correction enregistré."""
    id:                str
    recorded_at:       str          # ISO datetime
    context: dict = field(default_factory=dict)
    # {zone, background_type, text_color_class, theme_type}

    problem:           str  = ""    # FixType.value : text_contrast, overlay_increase, etc.
    fix:    dict = field(default_factory=dict)
    # {overlay_opacity, text_color, text_shadow, blur_px, ...}
    # Correspond aux champs d'un ZonePatch

    score_improvement: int   = 0    # delta global_score avant/après correction
    iterations_needed: int   = 1    # nb d'itérations pour converger
    use_count:         int   = 0    # fois où ce pattern a été utilisé en mode proactif
    success_count:     int   = 0    # fois où l'usage proactif a évité une correction
    failure_count:     int   = 0    # fois où le pattern n'a pas suffi
    last_used:         str | None = None

    # Champ transient : score de matching courant (non persisté)
    match_score:       int   = field(default=0, compare=False, repr=False)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

    @property
    def is_reliable(self) -> bool:
        """Pattern fiable si utilisé ≥ 3 fois avec taux de succès ≥ 0.6."""
        if self.use_count < 3:
            return True   # nouveau pattern → bénéfice du doute
        return self.success_rate >= 0.6

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("match_score", None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Pattern":
        d = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**d)


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT DERIVATION
# ─────────────────────────────────────────────────────────────────────────────

def derive_context(zone: str, rc: dict) -> dict:
    """
    Dérive les dimensions de contexte depuis un rendering contract (rc).

    zone          : identifiant de zone (hero, nav, primary_cta, ...)
    rc            : rendering contract — doit contenir bg, fg, bg_art, hero_pattern, etc.

    Retourne un dict {zone, background_type, text_color_class, theme_type}.
    """
    bg          = rc.get("bg",           "#ffffff")
    fg          = rc.get("fg",           "#000000")
    bg_art      = rc.get("bg_art",       "")
    hero_pattern = rc.get("hero_pattern", "")

    # background_type
    image_patterns = {"split", "asymmetric", "layered", "fullbleed", "overlay"}
    if "url(" in str(bg_art) or hero_pattern in image_patterns:
        bg_type = "image"
    elif "gradient" in str(bg_art).lower():
        bg_type = "gradient"
    else:
        bg_type = "color"

    # text_color_class : light = texte clair sur fond sombre, dark = inverse
    text_lum = _hex_luminance(fg)
    text_color_class = "light" if text_lum > 0.4 else "dark"

    # theme_type : dark si fond sombre
    bg_lum = _hex_luminance(bg)
    theme_type = "dark" if bg_lum < 0.35 else "light"

    return {
        "zone":             zone,
        "background_type":  bg_type,
        "text_color_class": text_color_class,
        "theme_type":       theme_type,
    }


def derive_context_from_audit(zone: str, audit_result) -> dict:
    """
    Dérive un contexte minimal depuis un AuditResult quand le RC n'est pas dispo.
    Retourne un contexte partiel (background_type/text_color_class inconnus).
    """
    return {
        "zone":             zone,
        "background_type":  None,
        "text_color_class": None,
        "theme_type":       None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MATCHING / SCORING
# ─────────────────────────────────────────────────────────────────────────────

def score_match(pattern_ctx: dict, query_ctx: dict) -> int:
    """
    Score de correspondance entre le contexte d'un pattern et une query.
    Plus élevé = plus pertinent.
    Max = 5 (zone×2 + 3 dimensions×1).
    None dans le query = ignoré (pas de pénalité).
    """
    score = 0
    for dim, weight in _CONTEXT_WEIGHTS.items():
        q_val = query_ctx.get(dim)
        p_val = pattern_ctx.get(dim)
        if q_val is None:
            continue             # dimension inconnue dans la query → ignorer
        if p_val == q_val:
            score += weight
    return score


def _deduplicate_fix(existing: dict, new_fix: dict) -> dict:
    """
    Si deux patterns ont le même contexte + problème, on moyenne les valeurs
    numériques plutôt que d'en stocker deux copies.
    """
    merged = {}
    all_keys = set(existing) | set(new_fix)
    for k in all_keys:
        a = existing.get(k)
        b = new_fix.get(k)
        if a is None:
            merged[k] = b
        elif b is None:
            merged[k] = a
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            merged[k] = round((a + b) / 2, 3)
        else:
            merged[k] = b   # string → prendre le nouveau
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN LEARNING
# ─────────────────────────────────────────────────────────────────────────────

class DesignLearning:
    """
    Mémoire heuristique des patterns de correction design.

    Enregistre les corrections efficaces, les retrouve par contexte,
    et propose des ajustements proactifs avant le premier rendu.
    """

    def __init__(self, db_path: str | Path = "data/design_patterns.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._patterns: list[Pattern] = []
        self._loaded = False
        self._load()

    # ── Public API ─────────────────────────────────────────────────────────

    def record_fix(
        self,
        context:           dict,
        problem:           str,
        fix_params:        dict,
        score_improvement: int = 0,
        iterations_needed: int = 1,
    ) -> str | None:
        """
        Enregistre un pattern de correction réussi.
        Retourne l'ID du pattern créé ou mis à jour, ou None si ignoré.

        fix_params : dict correspondant aux champs d'un ZonePatch
                     (ex: {"overlay_opacity": 0.5, "text_color": "#ffffff"})
        """
        if score_improvement < _MIN_IMPROVEMENT:
            return None   # amélioration insuffisante — ne pas apprendre

        fix_params = {k: v for k, v in fix_params.items() if v is not None}
        if not fix_params:
            return None

        # Chercher un pattern quasi-identique (même contexte + même problème)
        for existing in self._patterns:
            if (existing.context == context
                    and existing.problem == problem
                    and _context_fully_known(context)):
                # Mettre à jour plutôt que dupliquer
                existing.fix               = _deduplicate_fix(existing.fix, fix_params)
                existing.score_improvement = max(existing.score_improvement, score_improvement)
                existing.iterations_needed = min(existing.iterations_needed, iterations_needed)
                self._save()
                return existing.id

        # Nouveau pattern
        now = _iso_now()
        p = Pattern(
            id=str(uuid.uuid4()),
            recorded_at=now,
            context=dict(context),
            problem=problem,
            fix=fix_params,
            score_improvement=score_improvement,
            iterations_needed=iterations_needed,
        )
        self._patterns.append(p)
        self._enforce_max_patterns()
        self._save()
        return p.id

    def record_from_loop_result(
        self,
        loop_result,               # auto_fix_engine.LoopResult
        initial_scores: dict,      # {zone: global_score} AVANT corrections
        rc:             dict,      # rendering contract pour dériver le contexte
    ) -> list[str]:
        """
        Enregistre les patterns depuis un LoopResult complet.
        N'enregistre que les zones améliorées + boucle convergée.
        Retourne la liste des pattern IDs créés/mis à jour.
        """
        if not loop_result.converged and loop_result.iterations_run >= 1:
            # On enregistre quand même si le score a progressé même sans convergence
            pass   # continuer — on filtre par score_improvement plus bas

        # Grouper les CorrectionEntry par zone
        by_zone: dict[str, list] = {}
        for entry in loop_result.log:
            by_zone.setdefault(entry.zone, []).append(entry)

        recorded = []
        for zone, entries in by_zone.items():
            final_score   = loop_result.final_scores.get(zone, 0)
            initial_score = initial_scores.get(zone, 0)
            improvement   = final_score - initial_score
            if improvement < _MIN_IMPROVEMENT:
                continue

            context    = derive_context(zone, rc)
            fix_params = {}
            zone_patch = loop_result.final_patch.zones.get(zone)
            if zone_patch:
                fix_params = zone_patch.to_dict()

            # Problème principal : le fix type le plus sévère
            severity_rank = {"high": 3, "medium": 2, "low": 1}
            main_entry = max(entries, key=lambda e: severity_rank.get(e.severity, 0))
            problem    = main_entry.fix_type

            pid = self.record_fix(
                context=context,
                problem=problem,
                fix_params=fix_params,
                score_improvement=improvement,
                iterations_needed=loop_result.iterations_run,
            )
            if pid:
                recorded.append(pid)

        return recorded

    def retrieve_relevant_patterns(
        self,
        context: dict,
        top_k:   int = _MAX_SUGGESTIONS,
    ) -> list[Pattern]:
        """
        Retrouve les patterns pertinents pour un contexte donné.
        Retourne au maximum top_k patterns, triés par score décroissant.
        Les patterns non fiables (success_rate < 0.6 après 3+ usages) sont exclus.
        """
        scored: list[tuple[int, Pattern]] = []
        for p in self._patterns:
            s = score_match(p.context, context)
            if s >= _MIN_MATCH_SCORE and p.is_reliable:
                p_copy = Pattern(**{k: v for k, v in p.to_dict().items()})
                p_copy.match_score = s
                scored.append((s, p_copy))

        # Trier : score desc, puis score_improvement desc pour départager
        scored.sort(key=lambda x: (x[0], x[1].score_improvement), reverse=True)
        return [p for _, p in scored[:top_k]]

    def suggest_preemptive_adjustments(
        self,
        zone_contexts: list[dict],
    ):
        """
        Propose un FullPatch proactif à appliquer AVANT le premier rendu.

        zone_contexts : liste de {zone, background_type, text_color_class, theme_type}
        Retourne un FullPatch (auto_fix_engine) ou None si aucun pattern pertinent.
        """
        # Import ici pour éviter un couplage circulaire au niveau module
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).parent.parent.parent / "auto_fix_engine" / "src"))
            from auto_fix_engine import FullPatch, ZonePatch
        except ImportError:
            # Fallback : retourner un dict si auto_fix_engine pas dispo
            return self._suggest_as_dict(zone_contexts)

        full_patch    = FullPatch()
        applied_count = 0

        for zone_ctx in zone_contexts:
            if applied_count >= _MAX_SUGGESTIONS:
                break

            zone     = zone_ctx.get("zone", "unknown")
            patterns = self.retrieve_relevant_patterns(zone_ctx, top_k=1)
            if not patterns:
                continue

            best = patterns[0]
            if best.match_score < _MIN_MATCH_SCORE:
                continue

            # Construire le ZonePatch depuis les fix params
            valid_fields = {f for f in ZonePatch.__dataclass_fields__ if f != "zone"}
            safe_fix = {k: v for k, v in best.fix.items() if k in valid_fields}
            if not safe_fix:
                continue

            zone_patch = ZonePatch(zone=zone, **safe_fix)
            full_patch.set(zone, zone_patch)
            applied_count += 1

        return full_patch if not full_patch.is_empty() else None

    def mark_preemptive_result(self, pattern_id: str, success: bool) -> None:
        """
        Feedback sur l'utilisation proactive d'un pattern.
        success=True  → le rendu était lisible sans correction supplémentaire
        success=False → la correction n'a pas suffi
        """
        for p in self._patterns:
            if p.id == pattern_id:
                p.use_count   += 1
                p.last_used    = _iso_now()
                if success:
                    p.success_count += 1
                else:
                    p.failure_count += 1
                self._save()
                return

    def stats(self) -> dict:
        """Statistiques globales de la base de patterns."""
        total = len(self._patterns)
        if not total:
            return {
                "total_patterns": 0,
                "reliable_patterns": 0,
                "avg_score_improvement": 0,
                "avg_success_rate": 0,
                "most_common_problems": [],
                "coverage": {},
            }

        reliable  = sum(1 for p in self._patterns if p.is_reliable)
        avg_imp   = sum(p.score_improvement for p in self._patterns) / total
        avg_sr    = sum(p.success_rate for p in self._patterns) / total

        # Problèmes les plus fréquents
        problem_counts: dict[str, int] = {}
        for p in self._patterns:
            problem_counts[p.problem] = problem_counts.get(p.problem, 0) + 1
        top_problems = sorted(problem_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Couverture par zone
        zone_counts: dict[str, int] = {}
        for p in self._patterns:
            z = p.context.get("zone", "unknown")
            zone_counts[z] = zone_counts.get(z, 0) + 1

        return {
            "total_patterns":       total,
            "reliable_patterns":    reliable,
            "avg_score_improvement": round(avg_imp, 1),
            "avg_success_rate":     round(avg_sr, 2),
            "most_common_problems": [{"problem": k, "count": v} for k, v in top_problems],
            "coverage":             zone_counts,
        }

    def all_patterns(self) -> list[Pattern]:
        return list(self._patterns)

    def clear(self) -> None:
        """Vide la base (utile pour les tests)."""
        self._patterns = []
        self._save()

    # ── Storage ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self.db_path.exists():
            self._patterns = []
            return
        try:
            data = json.loads(self.db_path.read_text("utf-8"))
            if isinstance(data, dict) and "patterns" in data:
                self._patterns = [Pattern.from_dict(d) for d in data["patterns"]]
            else:
                self._patterns = []
        except (json.JSONDecodeError, KeyError, TypeError):
            self._patterns = []

    def _save(self) -> None:
        """Écriture atomique — évite la corruption en cas de crash."""
        data = {
            "version":  _DB_VERSION,
            "saved_at": _iso_now(),
            "patterns": [p.to_dict() for p in self._patterns],
        }
        tmp = self.db_path.parent / f".{self.db_path.name}.tmp"
        try:
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
            os.replace(str(tmp), str(self.db_path))
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    def _enforce_max_patterns(self) -> None:
        """Si on dépasse _MAX_PATTERNS, purger les patterns les moins utilisés."""
        if len(self._patterns) <= _MAX_PATTERNS:
            return
        # Trier : garder les plus utilisés + les plus récents
        self._patterns.sort(
            key=lambda p: (p.use_count, p.score_improvement),
            reverse=True,
        )
        self._patterns = self._patterns[:_MAX_PATTERNS]

    def _suggest_as_dict(self, zone_contexts: list[dict]) -> dict | None:
        """Fallback quand auto_fix_engine n'est pas disponible : retourne un dict."""
        result = {}
        for zone_ctx in zone_contexts:
            zone     = zone_ctx.get("zone", "unknown")
            patterns = self.retrieve_relevant_patterns(zone_ctx, top_k=1)
            if patterns and patterns[0].match_score >= _MIN_MATCH_SCORE:
                result[zone] = patterns[0].fix
        return result if result else None


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _hex_luminance(hex_color: str) -> float:
    """
    Luminance relative d'une couleur hex (0 = noir absolu, 1 = blanc absolu).
    Formule sRGB WCAG.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return 0.5   # fallback
    try:
        r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return 0.5

    def _lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _context_fully_known(context: dict) -> bool:
    return all(context.get(dim) is not None for dim in _CONTEXT_WEIGHTS)
