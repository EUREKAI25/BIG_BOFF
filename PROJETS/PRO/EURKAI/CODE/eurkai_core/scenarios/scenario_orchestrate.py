"""
scenario_orchestrate
Chaîne autonome : input → objet → code (→ fix si échec).

Étapes :
  0a. agent_brief      — si params["idea"] : idée → BRIEF structuré (name/type/features/monetization)
  0b. agent_intake     — si params["idea"] : idée brute → objet minimal
  1.  agent_architect  — enrichit l'objet (domain, inputs, outputs, structure)
  2.  agent_generate_object  — produit un objet EURKAI conforme (si schema catalog)
  3.  agent_generate_code    — produit le code correspondant
  4.  agent_debug_fix        — tentative de correction si code invalide/vide
  5.  agent_validator        — valide cohérence objet/code (score 0–100)
  6.  Output structuré final

Entrée minimale :
  schema_ident  — ident du schema cible
  params        — dict avec object_lineage, object_goal, object_type…
               — ou {"idea": "..."} pour démarrer depuis une idée brute

Sortie :
  status        — "success" | "partial" | "error"
  object        — objet généré (ou None)
  code          — code généré (ou "")
  filename      — fichier résolu
  brief         — BRIEF structuré (ou None si pas d'idea)
  validation    — {score, issues, warnings} depuis agent_validator
  meta          — trace d'exécution + usages
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from core.context import _context_to_dict
from agents.agent_generate_object import run as generate_object
from agents.agent_generate_code    import run as generate_code
from agents.agent_debug_fix        import run as debug_fix
from agents.agent_intake           import run as intake
from agents.agent_architect        import run as architect
from agents.agent_validator        import run as validate
from agents.agent_brief            import run as brief_agent


# ── Main entry point ──────────────────────────────────────────────────────────

def run(schema_ident, params=None, catalog=None, model_type="llm", verbose=True, context=None):
    """
    Orchestre la chaîne input → objet → code.

    schema_ident : ident du schema dans le catalog
    params       : dict libre — object_lineage, object_goal, object_type, target_language…
    catalog      : catalog EURKAI (chargé automatiquement si absent)
    model_type   : "llm" pour agent_generate_object, "deterministic" pour agent_generate_code
    context      : ProjectExecutionContext | dict | None — contexte transverse (transport only)
    """
    params  = params or {}
    catalog = catalog or load_catalog()

    meta  = {"steps": [], "usage": {}}
    brief = None

    ctx_dict = _context_to_dict(context)
    if ctx_dict is not None:
        meta["context"] = ctx_dict

    # ── Étape 0a — Brief : structurer l'idée ─────────────────────────────────
    if params.get("idea"):
        brief_step = _step_brief(params["idea"], verbose, ctx_dict)
        meta["steps"].append({"step": "brief", "status": brief_step["_step_status"]})
        if brief_step["_step_status"] == "ok":
            brief  = brief_step["brief"]
            params = _enrich_from_brief(params, brief)

    # ── Étape 0b — Intake : idée brute → objet structuré ─────────────────────
    if params.get("idea"):
        resolved = _resolve_from_idea(params["idea"], catalog, verbose)
        if resolved["status"] == "error":
            return _error(resolved["error"], meta)
        schema_ident = resolved["schema_ident"]
        params       = {**resolved["params"], **{k: v for k, v in params.items()
                                                  if k not in resolved["params"]}}

    # ── Étape 0b — Architect : enrichir l'objet ───────────────────────────────
    arch_result = _step_architect(params, verbose, ctx_dict)
    meta["steps"].append({"step": "architect", "status": arch_result["_step_status"]})
    if arch_result["_step_status"] == "ok":
        params       = arch_result["enriched"]
        schema_ident = params.get("ident") or schema_ident

    # ── Étape 1 — Générer l'objet ─────────────────────────────────────────────
    obj_result = _step_generate_object(schema_ident, params, catalog, model_type, verbose)
    meta["steps"].append({"step": "generate_object", "status": obj_result["_step_status"]})
    meta["usage"]["generate_object"] = obj_result.get("usage", {})

    if obj_result["_step_status"] == "error":
        return _error(obj_result["_step_error"], meta)

    generated_object = obj_result.get("generated_object")

    # ── Étape 2 — Générer le code ─────────────────────────────────────────────
    code_params = _build_code_params(params, generated_object)
    code_result = _step_generate_code(schema_ident, code_params, catalog, verbose, ctx_dict)
    meta["steps"].append({"step": "generate_code", "status": code_result["_step_status"],
                          "filename": code_result.get("filename", "")})

    if code_result["_step_status"] == "error":
        return _partial(generated_object, "", code_result["_step_error"], meta)

    # ── Étape 3 — Debug fix si code vide ou invalide ──────────────────────────
    code = code_result.get("code", "")
    if not code.strip():
        fix_result = _step_debug_fix(code, "code_empty", params, verbose)
        meta["steps"].append({"step": "debug_fix", "status": fix_result["_step_status"],
                              "fix_applied": fix_result.get("fix_applied", "")})
        if fix_result["_step_status"] == "success":
            code_result["code"] = fix_result["fixed_code"]
            code = code_result["code"]
        else:
            return _partial(generated_object, "", "generate_and_fix_both_failed", meta)

    # ── Étape 4 — Validation objet / code ────────────────────────────────────
    val_result = _step_validate(generated_object, code, params, verbose, ctx_dict)
    meta["steps"].append({"step": "validate", "status": val_result["_step_status"],
                          "score": val_result.get("score", 0)})
    meta["validation"] = {"score": val_result.get("score", 0),
                          "issues": val_result.get("issues", []),
                          "warnings": val_result.get("warnings", [])}

    # ── Output final ──────────────────────────────────────────────────────────
    status = "success"
    if obj_result["_step_status"] == "partial" or code_result["_step_status"] == "partial":
        status = "partial"
    if val_result["_step_status"] == "failure":
        status = "partial"   # validation failure → partial (code existe mais problèmes détectés)

    if verbose:
        score = val_result.get("score", 0)
        print(f"  [{'OK' if status == 'success' else 'WARN'}]   scenario_orchestrate — {status} (score:{score}/100)")

    return {
        "status":     status,
        "object":     generated_object,
        "code":       code,
        "filename":   code_result.get("filename", ""),
        "brief":      brief,
        "warnings":   obj_result.get("warnings", []) + code_result.get("warnings", []) + val_result.get("warnings", []),
        "validation": meta["validation"],
        "meta":       meta,
    }


# ── Steps ─────────────────────────────────────────────────────────────────────

def _step_generate_object(schema_ident, params, catalog, model_type, verbose):
    storage = catalog.get("_storage")
    schema  = storage.get("schema", schema_ident) if storage else None

    if schema is None:
        # Pas de schema dans le catalog — on saute generate_object
        if verbose:
            print(f"  [SKIP]    generate_object — schema '{schema_ident}' absent du catalog")
        return {"_step_status": "partial", "_step_error": None,
                "generated_object": _build_inline_object(schema_ident, params),
                "warnings": [f"schema_not_in_catalog:{schema_ident}"],
                "usage": {}}

    result = generate_object(schema_ident, params, catalog,
                             model_type=model_type, verbose=verbose)

    if not result.get("success"):
        return {"_step_status": "error",
                "_step_error":  result.get("error", "generate_object_failed"),
                "usage": result.get("usage", {})}

    return {"_step_status": "ok",
            "generated_object": result.get("generated_object"),
            "warnings": [],
            "usage": result.get("usage", {})}


def _step_brief(idea, verbose, ctx_dict=None):
    """Appelle agent_brief. Fallback propre si échec — n'est jamais bloquant."""
    result = brief_agent({"idea": idea}, verbose=verbose, context=ctx_dict)
    if result["status"] != "success":
        if verbose:
            print(f"  [SKIP]    brief — {result.get('reason')} — fallback sans brief")
        return {"_step_status": "skipped", "brief": None}
    return {"_step_status": "ok", "brief": result["brief"]}


def _step_architect(params, verbose, ctx_dict=None):
    """Enrichit l'objet via agent_architect. Fallback propre si échec."""
    result = architect(params, verbose=verbose, context=ctx_dict)
    if result["status"] != "success":
        if verbose:
            print(f"  [SKIP]    architect — {result.get('reason')} — fallback params originaux")
        return {"_step_status": "skipped"}
    return {"_step_status": "ok", "enriched": result["object"]}


def _resolve_from_idea(idea, catalog, verbose):
    """Appelle agent_intake et retourne schema_ident + params compatibles."""
    result = intake(idea, catalog=catalog, model_type="deterministic", verbose=verbose)
    if result["status"] != "success":
        return {"status": "error", "error": f"intake_failed:{result.get('reason')}"}
    obj = result["object"]
    return {
        "status":       "ok",
        "schema_ident": obj["ident"],
        "params":       obj,            # contient object_type, object_goal, attributes…
    }


def _step_debug_fix(code, error, params, verbose):
    result = debug_fix(code, error, context=params, verbose=verbose)
    status = "success" if result.get("status") == "success" else "failure"
    return {"_step_status": status,
            "fixed_code":   result.get("fixed_code", code),
            "fix_applied":  result.get("fix_applied", "")}


def _step_validate(obj, code, params, verbose, ctx_dict=None):
    """Valide la cohérence objet/code via agent_validator."""
    obj_for_val = obj or params
    val_context = dict(params) if params else {}
    if ctx_dict is not None:
        val_context["_execution_context"] = ctx_dict
    result = validate(obj_for_val, code, context=val_context, verbose=verbose)
    step_status = "ok" if result.get("status") == "success" else "failure"
    return {"_step_status": step_status,
            "score":        result.get("score", 0),
            "issues":       result.get("issues", []),
            "warnings":     result.get("warnings", [])}


def _step_generate_code(schema_ident, code_params, catalog, verbose, ctx_dict=None):
    result = generate_code(schema_ident, code_params, catalog,
                           model_type="deterministic", verbose=verbose, context=ctx_dict)

    step_status = {"ok": "ok", "partial": "partial", "error": "error"}.get(
        result.get("status", "error"), "error"
    )

    return {"_step_status": step_status,
            "_step_error":  result.get("warnings", []),
            "code":         result.get("code", ""),
            "filename":     result.get("filename", ""),
            "warnings":     result.get("warnings", [])}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _enrich_from_brief(params, brief):
    """Injecte le contexte du brief dans params avant intake + architect."""
    cp = dict(params)
    # Description du brief → goal si pas déjà défini
    cp.setdefault("object_goal", brief.get("description", ""))
    # Conserver le brief pour référence dans la chaîne
    cp["_brief"] = brief
    return cp


def _build_code_params(params, generated_object):
    """Enrichit les params pour agent_generate_code depuis l'objet généré."""
    cp = dict(params)

    if generated_object and isinstance(generated_object, dict):
        # Récupérer les attributs depuis l'objet si présents
        for key in ("object_fields", "schema_fields", "attributes", "fields"):
            if key in generated_object:
                cp.setdefault("attributes", generated_object[key])
                break
        # Récupérer le goal
        cp.setdefault("goal",
                      generated_object.get("object_goal") or
                      generated_object.get("object_description") or "")

    return cp


def _build_inline_object(schema_ident, params):
    """Objet minimal si le schema n'est pas dans le catalog.
    Préserve tous les champs de params (inclut les enrichissements architect)."""
    base = {
        "object_ident":    schema_ident,
        "object_lineage":  params.get("object_lineage", f"Object:{schema_ident}"),
        "object_goal":     params.get("object_goal", ""),
        "object_type":     params.get("object_type", "class"),
        "_inline":         True,
    }
    # Propager les champs architect si présents
    for key in ("domain", "inputs", "outputs", "structure", "goal"):
        if key in params:
            base[key] = params[key]
    return base


def _error(error, meta):
    return {"status": "error", "object": None, "code": "", "filename": "",
            "warnings": [str(error)], "meta": meta}


def _partial(obj, code, warning, meta):
    return {"status": "partial", "object": obj, "code": code, "filename": "",
            "warnings": [str(warning)] if warning else [], "meta": meta}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="scenario_orchestrate — input → objet → code")
    parser.add_argument("schema_ident",   help="Ident du schema (ex: ObjectSchema, UserProfile)")
    parser.add_argument("--lineage",      default="", help="object_lineage (ex: Object:User)")
    parser.add_argument("--goal",         default="", help="Objectif de l'objet")
    parser.add_argument("--type",         default="class", dest="object_type",
                        help="Type de code : function | class | module | scenario | page")
    parser.add_argument("--model",        default="llm", dest="model_type",
                        help="Modèle pour generate_object : llm | mock (défaut: llm)")
    parser.add_argument("--dry",          action="store_true",
                        help="Dry run : catalog minimal, pas d'appel LLM")
    args = parser.parse_args()

    params = {
        "object_lineage": args.lineage or f"Object:{args.schema_ident}",
        "object_goal":    args.goal,
        "object_type":    args.object_type,
    }

    if args.dry:
        # Mode sans catalog réel — utile pour tester la chaîne sans LLM
        _catalog = {"_storage": None}
        model    = "deterministic"
    else:
        _catalog = None          # chargé automatiquement
        model    = args.model_type

    result = run(args.schema_ident, params, catalog=_catalog, model_type=model)

    # Affichage compact
    summary = {
        "status":   result["status"],
        "filename": result["filename"],
        "object":   result["object"],
        "warnings": result["warnings"],
        "steps":    result["meta"]["steps"],
    }
    print("\n" + "=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if result["code"]:
        print("\n--- code ---")
        print(result["code"])

    sys.exit(0 if result["status"] in ("success", "partial") else 1)
