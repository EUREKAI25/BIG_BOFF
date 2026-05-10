"""
scenario_debug_validate V2
Scan récursif du catalog EURKAI + validation par règles EURKAI.

V1 : Règle 1 (ident propre) + Règle 2 (validate_object_vs_schema)
V2 : +function_path résolvable, +doublons ident, +format lineage,
     +active flag, +schema coverage

Bypass MRG (trop lourd pour scan bulk — pas d'exécution, pas d'historique).
Validation directe via validate_object_vs_schema.

Usage :
    python scenarios/scenario_debug_validate.py
    python scenarios/scenario_debug_validate.py agent
    from scenarios.scenario_debug_validate import run
"""

import importlib
import json
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.functions.validate_object_vs_schema import validate_object_vs_schema


# ── Constantes ────────────────────────────────────────────────────────────────

# Format lineage attendu : Object suivi d'au moins un segment :Type ou :Type:Name
_LINEAGE_RE = re.compile(r'^Object(:[A-Za-z][A-Za-z0-9_]*){1,}$')

# ── Schéma minimal (fallback si object_schema absent ou schema non trouvé) ────
#
# Vérifie uniquement : ident propre au type + présence de object_schema.
# Les clés contenant "{type}" sont résolues dynamiquement.
#
_MINIMAL_RULES = {
    "schema_ident": "_debug_minimal",
    "schema_required_element_list": {
        "schema_field": {
            "rule_condition": "EXISTS('object_schema')",
            "rule_severity":  "warning",
        },
    },
    "schema_validation_rule_list": {},
}


def run(catalog=None, type_filter=None, verbose=True):
    """
    Scanne le catalog EURKAI et valide chaque objet.

    catalog     : catalog EURKAI (chargé automatiquement si absent)
    type_filter : str — limiter à un type ("agent", "module", ...) — None = tout
    verbose     : bool

    Retourne un dict standardisé {status, from, to, data, meta}.
    """
    meta = {"steps": [], "errors": []}
    cat  = catalog or load_catalog()
    storage = cat.get("_storage")
    if storage is None:
        from core.storage.catalog_storage import get_storage
        storage = get_storage(cat)

    # ── Étape 1 — Construire la liste des cibles ──────────────────────────────
    types  = [type_filter] if type_filter else storage.list_types()
    targets = []
    for type_name in types:
        for ident, obj in storage.get_all(type_name).items():
            if obj is not None:
                targets.append((type_name, ident, obj))

    meta["steps"].append({"step": "scan", "status": "ok", "count": len(targets)})

    # ── Étape 2 — Doublons ident (cross-objets par type) ─────────────────────
    # Compte les valeurs {type}_ident pour détecter les doublons
    ident_counts = {}   # (type_name, ident_value) → count
    for type_name, ident, obj in targets:
        ident_key = f"{type_name}_ident"
        val = obj.get(ident_key) or ident
        key = (type_name, val)
        ident_counts[key] = ident_counts.get(key, 0) + 1
    duplicate_keys = {k for k, v in ident_counts.items() if v > 1}

    # ── Étape 3 — Schema coverage (warning par type sans schema) ─────────────
    schema_coverage = {}   # type_name → True/False
    for type_name in types:
        # Heuristique : cherche {Type}Schema dans le catalog
        candidate = f"{type_name.capitalize()}Schema"
        schema_coverage[type_name] = storage.get("schema", candidate) is not None

    if verbose:
        print("=" * 65)
        print(f"  scenario_debug_validate V2 — {len(targets)} objet(s) scannés")
        print("=" * 65)

    # ── Étape 4 — Validation par objet ───────────────────────────────────────
    ok_list      = []
    invalid_list = []
    missing_list = []
    errors_by_type = {}

    for type_name, ident, obj in targets:
        is_duplicate = (type_name, obj.get(f"{type_name}_ident") or ident) in duplicate_keys
        has_schema   = schema_coverage.get(type_name, False)
        result = _validate_one(type_name, ident, obj, storage,
                               is_duplicate=is_duplicate, has_schema=has_schema)

        if result["status"] == "ok":
            ok_list.append({"type": type_name, "ident": ident, "score": result["score"]})
        elif result["status"] == "missing":
            missing_list.append({"type": type_name, "ident": ident, "reason": result["reason"]})
            errors_by_type[type_name] = errors_by_type.get(type_name, 0) + 1
        else:
            invalid_list.append({
                "type":   type_name,
                "ident":  ident,
                "errors": result["errors"],
                "warnings": result.get("warnings", []),
                "score":  result["score"],
            })
            errors_by_type[type_name] = errors_by_type.get(type_name, 0) + 1

        if verbose:
            icon = "✓" if result["status"] == "ok" else ("?" if result["status"] == "missing" else "✗")
            score_str = f" score:{result['score']}" if "score" in result else ""
            print(f"  {icon} [{type_name}] {ident}{score_str}")
            if result["status"] == "invalid" and result.get("errors"):
                for e in result["errors"][:3]:
                    print(f"      → {e['field']}: {e['detail']}")

    # ── Étape 5 — Assemblage du rapport ──────────────────────────────────────
    total = len(ok_list) + len(invalid_list) + len(missing_list)
    score = round(100 * len(ok_list) / total) if total else 0

    report = {
        "summary": {
            "total":   total,
            "ok":      len(ok_list),
            "invalid": len(invalid_list),
            "missing": len(missing_list),
            "score":   score,
        },
        "ok_list":       ok_list,
        "invalid_list":  invalid_list,
        "missing_list":  missing_list,
        "errors_by_type": errors_by_type,
    }

    meta["steps"].append({"step": "report", "status": "ok"})

    if verbose:
        print()
        print(f"  RÉSULTAT : {len(ok_list)} OK  /  {len(invalid_list)} invalides  /  {len(missing_list)} manquants")
        print(f"  SCORE    : {score}%")
        print("=" * 65)

    # ── Étape 6 — Output sur disque ───────────────────────────────────────────
    out_dir  = Path(__file__).parent.parent / "preprod"
    out_dir.mkdir(exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"output_debug_validate_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    if verbose:
        print(f"\n  → output : {out_file}")

    status = "ok" if (len(invalid_list) + len(missing_list)) == 0 else "partial"

    return {
        "status": status,
        "from":   "catalog",
        "to":     "debug_report",
        "data":   {"report": report},
        "meta":   meta,
    }


# ── Validation d'un objet ─────────────────────────────────────────────────────

def _validate_one(type_name, ident, obj, storage, is_duplicate=False, has_schema=True):
    """
    Valide un objet contre toutes les règles V2 :
      Règle 1 : ident propre au type présent
      Règle 2 : validate_object_vs_schema contre le schema déclaré
      Règle 3 : function_path résolvable (importlib)
      Règle 4 : duplicate_ident détecté
      Règle 5 : format lineage Object:Type:Name
      Warn  A : active flag présent
      Warn  B : schema coverage du type

    Retourne : {status: "ok"|"invalid"|"missing", score, errors, warnings}
    """
    errors   = []
    warnings = []

    # ── Règle 1 — "tout est objet" ────────────────────────────────────────────
    ident_key = f"{type_name}_ident"
    if not obj.get(ident_key):
        generic_keys = ["ident", "object_ident", "schema_ident", "model_ident",
                        "delimiter_ident", "env_ident", "query_ident"]
        found_ident = any(obj.get(k) for k in generic_keys)
        if not found_ident:
            return {
                "status": "missing",
                "reason": f"no_{type_name}_ident_and_no_generic_ident",
            }

    # ── Règle 2 — validate_object_vs_schema ──────────────────────────────────
    schema_ident = obj.get("object_schema")
    schema = None
    if schema_ident:
        schema = storage.get("schema", schema_ident)
    if schema is None:
        schema = _build_minimal_schema(type_name)

    val = validate_object_vs_schema(obj, schema)
    errors.extend(val.get("failures", []))
    warnings.extend(val.get("warnings", []))
    base_tested = val.get("tested", 0)

    # ── Règle 3 — function_path résolvable ───────────────────────────────────
    fp_error = _check_function_path(type_name, obj)
    if fp_error:
        errors.append(fp_error)

    # ── Règle 4 — duplicate_ident ────────────────────────────────────────────
    if is_duplicate:
        errors.append({
            "field":  f"{type_name}_ident",
            "detail": f"duplicate_ident: '{ident}' apparaît plusieurs fois dans catalog_{type_name}_list",
            "type":   "duplicate_ident",
        })

    # ── Règle 5 — format lineage ─────────────────────────────────────────────
    lineage = obj.get("object_lineage", "")
    if lineage and not _LINEAGE_RE.match(lineage):
        errors.append({
            "field":  "object_lineage",
            "detail": f"invalid_lineage: '{lineage}' — attendu Object:Type[:Name]",
            "type":   "invalid_lineage",
        })

    # ── Warning A — active flag ───────────────────────────────────────────────
    active_key = f"{type_name}_active"
    if active_key not in obj:
        warnings.append({
            "rule":     "active_flag",
            "detail":   f"'{active_key}' absent",
            "severity": "warning",
        })

    # ── Warning B — schema coverage ──────────────────────────────────────────
    if not has_schema:
        warnings.append({
            "rule":     "schema_coverage",
            "detail":   f"aucun schema trouvé pour le type '{type_name}'",
            "severity": "warning",
        })

    # ── Score ─────────────────────────────────────────────────────────────────
    extra_checks = sum(1 for x in [fp_error, is_duplicate or None,
                                    lineage and not _LINEAGE_RE.match(lineage) or None]
                       if x)
    total_checks  = base_tested + extra_checks
    total_failures = len(errors)
    score = round(100 * (total_checks - total_failures) / total_checks) if total_checks else (100 if not errors else 0)

    if not errors:
        return {"status": "ok", "score": score, "warnings": warnings}

    return {
        "status":   "invalid",
        "score":    score,
        "errors":   errors,
        "warnings": warnings,
    }


def _check_function_path(type_name, obj):
    """
    Règle 3 — vérifie que function_path est importable.
    Cherche : {type}_contract.{type}_function puis function_path direct.
    Retourne un dict erreur ou None.
    """
    contract = obj.get(f"{type_name}_contract", {}) or {}
    function_path = contract.get(f"{type_name}_function") or obj.get("function_path", "")

    if not function_path:
        return None  # Pas de function_path → pas de check

    parts = function_path.rsplit(".", 1)
    if len(parts) != 2:
        return {
            "field":  "function_path",
            "detail": f"function_not_resolvable: format invalide '{function_path}'",
            "type":   "function_not_resolvable",
        }

    module_path, fn_name = parts
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return {
            "field":  "function_path",
            "detail": f"function_not_resolvable: module introuvable '{module_path}'",
            "type":   "function_not_resolvable",
        }
    except Exception as e:
        return {
            "field":  "function_path",
            "detail": f"function_not_resolvable: erreur import '{module_path}' — {e}",
            "type":   "function_not_resolvable",
        }

    if getattr(mod, fn_name, None) is None:
        return {
            "field":  "function_path",
            "detail": f"function_not_resolvable: '{fn_name}' absent dans '{module_path}'",
            "type":   "function_not_resolvable",
        }

    return None  # OK


def _build_minimal_schema(type_name):
    """Construit un schéma minimal dynamique pour un type donné."""
    return {
        "schema_ident": f"_debug_{type_name}",
        "schema_required_element_list": {
            "object_schema": {
                "rule_condition": "EXISTS('object_schema')",
                "rule_severity":  "warning",
            },
        },
        "schema_validation_rule_list": {},
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    type_filter = sys.argv[1] if len(sys.argv) > 1 else None

    result = run(type_filter=type_filter, verbose=True)
    r = result["data"]["report"]["summary"]
    sys.exit(0 if r["score"] == 100 else 1)
