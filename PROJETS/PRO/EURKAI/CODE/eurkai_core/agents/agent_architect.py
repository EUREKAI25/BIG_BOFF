"""
agent_architect
Enrichit un objet issu de agent_intake avec :
- un goal plus précis
- des inputs/outputs typés
- une structure métier selon le type (function/class/module/scenario)

Déterministe — LLM optionnel en fallback isolé.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Enrichissements par type ───────────────────────────────────────────────────

_DEFAULT_OUTPUTS = {
    "function": {"result": "Any"},
    "class":    {"instance": "self"},
    "module":   {"success": "bool", "result": "Any"},
    "scenario": {"success": "bool", "outputs": "dict"},
    "page":     {"html": "str"},
}

_DEFAULT_METHODS = {
    "class":    ["__init__", "validate", "to_dict"],
    "module":   ["run"],
    "scenario": ["run", "test"],
}

_DOMAIN_HINTS = {
    # finance
    r"\bvat\b|\btax\b|\btva\b|\bimpôt\b|\bfacture\b|\binvoice\b|\bprice\b|\bprix\b": "finance",
    # auth
    r"\bauth\b|\blogin\b|\bpassword\b|\btoken\b|\bsession\b|\bjwt\b":                "auth",
    # email
    r"\bemail\b|\bmail\b|\bnewsletter\b|\bsmtp\b|\bbrevo\b|\bsendgrid\b":            "email",
    # data
    r"\bparse\b|\bcsv\b|\bjson\b|\bxml\b|\bimport\b|\bexport\b|\bconvert\b":         "data",
    # user
    r"\buser\b|\butilisateur\b|\bprofile\b|\baccount\b|\bcompte\b":                  "user",
    # payment
    r"\bpayment\b|\bpaiement\b|\bstripe\b|\bcheckout\b|\border\b|\bcommande\b":      "payment",
    # storage
    r"\bfile\b|\bfichier\b|\bstorage\b|\bdatabase\b|\bdb\b|\bsave\b|\bload\b":       "storage",
}


def run(obj, catalog=None, model_type="deterministic", verbose=True,
        agent_ident="agent_architect", context=None):
    """
    Enrichit un objet issu de agent_intake.

    obj        : dict avec type, ident, goal, attributes (sortie de agent_intake)
    catalog    : dict — non utilisé en mode déterministe
    model_type : "deterministic" | "llm"

    Retourne :
        status  — "success" | "failure"
        object  — objet enrichi
    """
    if not obj or not isinstance(obj, dict):
        return _failure("invalid_input")

    object_type = obj.get("type") or obj.get("object_type") or "function"
    ident       = obj.get("ident") or obj.get("object_ident") or ""
    goal        = obj.get("goal") or obj.get("object_goal") or ""
    attributes  = obj.get("attributes") or {}

    if not ident:
        return _failure("ident_missing")

    lower  = f"{ident} {goal}".lower()
    domain = _detect_domain(lower)

    inputs  = _build_inputs(attributes, object_type, lower)
    outputs = _build_outputs(object_type, lower, domain)
    struct  = _build_structure(object_type, ident, inputs, outputs, lower)
    goal_e  = _enrich_goal(goal, object_type, ident, domain, inputs, outputs)

    enriched = {
        # Champs originaux conservés
        **obj,
        # Enrichissements
        "goal":           goal_e,
        "object_goal":    goal_e,
        "domain":         domain,
        "inputs":         inputs,
        "outputs":        outputs,
        "structure":      struct,
        # Champs compatibles scenario_orchestrate
        "attributes":     inputs,
    }

    if verbose:
        print(f"  [agent]   {agent_ident} — {object_type}:{ident} domain:{domain}")
        print(f"  [OK]      inputs:{list(inputs.keys())} outputs:{list(outputs.keys())}")

    return {"status": "success", "object": enriched}


# ── Détection de domaine ───────────────────────────────────────────────────────

def _detect_domain(lower):
    for pattern, domain in _DOMAIN_HINTS.items():
        if re.search(pattern, lower):
            return domain
    return "generic"


# ── Construction des inputs ────────────────────────────────────────────────────

def _build_inputs(attributes, object_type, lower):
    """Part des attributs existants et enrichit par domaine."""
    inputs = dict(attributes)

    # Si déjà des attributs, compléter seulement si peu nombreux
    if len(inputs) >= 3:
        return inputs

    # Enrichissements par signaux dans goal/ident
    _hints = [
        (r"\bprice\b|\bprix\b|\bcost\b|\bcoût\b",          "price",      "float"),
        (r"\brate\b|\btaux\b|\bpercent\b",                  "rate",       "float"),
        (r"\bname\b|\bnom\b",                               "name",       "str"),
        (r"\bemail\b|\bmail\b",                             "email",      "str"),
        (r"\bdate\b",                                       "date",       "str"),
        (r"\bamount\b|\bmontant\b",                         "amount",     "float"),
        (r"\blist\b|\bliste\b|\bitems\b|\bvalues\b",        "items",      "list"),
        (r"\btext\b|\btexte\b|\bstring\b|\bmessage\b",      "text",       "str"),
        (r"\buser_id\b|\buser\b|\butilisateur\b",           "user_id",    "str"),
        (r"\bpath\b|\bfile\b|\bfichier\b",                  "path",       "str"),
        (r"\btemplate\b|\btemplate\b",                      "template",   "str"),
        (r"\btoken\b|\bapi_key\b|\bclé\b",                  "token",      "str"),
    ]
    for pattern, key, typ in _hints:
        if re.search(pattern, lower) and key not in inputs:
            inputs[key] = typ

    return inputs


# ── Construction des outputs ───────────────────────────────────────────────────

def _build_outputs(object_type, lower, domain):
    outputs = dict(_DEFAULT_OUTPUTS.get(object_type, {"result": "Any"}))

    # Surcharges par domaine
    if domain == "finance":
        outputs = {"amount_ht": "float", "amount_ttc": "float", "rate_applied": "float"}
    elif domain == "auth":
        outputs = {"success": "bool", "token": "str", "user_id": "str"}
    elif domain == "email":
        outputs = {"success": "bool", "message_id": "str"}
    elif domain == "data":
        outputs = {"success": "bool", "data": "Any", "errors": "list"}
    elif domain == "user":
        outputs = {"success": "bool", "user": "dict"}
    elif domain == "payment":
        outputs = {"success": "bool", "transaction_id": "str", "status": "str"}
    elif domain == "storage":
        outputs = {"success": "bool", "path": "str"}

    return outputs


# ── Construction de la structure ───────────────────────────────────────────────

def _build_structure(object_type, ident, inputs, outputs, lower):
    if object_type == "function":
        return {
            "signature": f"{ident}({', '.join(inputs.keys())})",
            "returns":   next(iter(outputs.keys()), "result"),
            "pure":      not re.search(r"\bsave\b|\bwrite\b|\bsend\b|\bdelete\b", lower),
        }

    if object_type == "class":
        methods = list(_DEFAULT_METHODS["class"])
        if re.search(r"\bsave\b|\bpersist\b|\bstore\b", lower):
            methods.append("save")
        if re.search(r"\bload\b|\bfetch\b|\bget\b", lower):
            methods.append("load")
        return {
            "attributes": inputs,
            "methods":    methods,
        }

    if object_type == "module":
        return {
            "entry_point": "run(params: dict) -> dict",
            "params":      inputs,
            "returns":     outputs,
        }

    if object_type == "scenario":
        steps = _infer_steps(lower, inputs)
        return {
            "steps":   steps,
            "context": list(inputs.keys()),
            "outputs": list(outputs.keys()),
        }

    if object_type == "page":
        return {
            "sections": ["header", "content", "footer"],
            "data":     inputs,
        }

    return {}


def _infer_steps(lower, inputs):
    """Infère des étapes simples depuis l'ident/goal pour un scenario."""
    steps = ["validate_inputs"]
    if re.search(r"\bauth\b|\blogin\b|\btoken\b", lower):
        steps.append("authenticate")
    if re.search(r"\bfetch\b|\bload\b|\bget\b|\bread\b", lower):
        steps.append("fetch_data")
    if re.search(r"\bpay\b|\bcharge\b|\bstripe\b|\bcheckout\b", lower):
        steps.append("process_payment")
    if re.search(r"\bsend\b|\bnotif\b|\bemail\b", lower):
        steps.append("send_notification")
    if re.search(r"\bsave\b|\bstore\b|\bpersist\b", lower):
        steps.append("save_result")
    steps.append("return_output")
    return steps


# ── Enrichissement du goal ─────────────────────────────────────────────────────

def _enrich_goal(goal, object_type, ident, domain, inputs, outputs):
    name   = ident.replace("_", " ")
    in_str = ", ".join(f"{k} ({v})" for k, v in list(inputs.items())[:3])
    out_str = ", ".join(f"{k} ({v})" for k, v in list(outputs.items())[:2])

    _verbs = {
        "function": "Calcule",
        "class":    "Représente",
        "module":   "Gère",
        "scenario": "Orchestre",
        "page":     "Affiche",
    }
    verb = _verbs.get(object_type, "Traite")

    if domain != "generic":
        domain_label = f"[{domain}] "
    else:
        domain_label = ""

    base = goal if len(goal) > 15 else f"{verb} {name}"

    if in_str and out_str:
        return f"{domain_label}{base}. Entrées : {in_str}. Sorties : {out_str}."
    if in_str:
        return f"{domain_label}{base}. Entrées : {in_str}."
    return f"{domain_label}{base}."


# ── Helpers ────────────────────────────────────────────────────────────────────

def _failure(reason):
    return {"status": "failure", "object": None, "reason": reason}


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    cases = [
        {
            "label": "Function VAT",
            "obj": {
                "type": "function", "ident": "calculate_vat",
                "goal": "calculates VAT from price and rate",
                "attributes": {"price": "float", "rate": "float"},
            },
        },
        {
            "label": "Class UserProfile",
            "obj": {
                "type": "class", "ident": "UserProfile",
                "goal": "represents a user profile",
                "attributes": {"name": "str", "email": "str"},
            },
        },
        {
            "label": "Module email",
            "obj": {
                "type": "module", "ident": "email_sender",
                "goal": "module for sending outbound emails",
                "attributes": {},
            },
        },
        {
            "label": "Scenario checkout",
            "obj": {
                "type": "scenario", "ident": "checkout_flow",
                "goal": "orchestrates the payment checkout flow",
                "attributes": {},
            },
        },
    ]

    print("=" * 60)
    print("  agent_architect — smoke test")
    print("=" * 60)

    passed = failed = 0
    for case in cases:
        r = run(case["obj"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{'✓' if ok else '✗'} {case['label']}")
        if ok:
            o = r["object"]
            print(f"  domain   : {o['domain']}")
            print(f"  goal     : {o['goal']}")
            print(f"  inputs   : {o['inputs']}")
            print(f"  outputs  : {o['outputs']}")
            print(f"  struct   : {json.dumps(o['structure'], ensure_ascii=False)}")
            passed += 1
        else:
            print(f"  reason   : {r.get('reason')}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  {passed}/{passed + failed} passed")
    print("=" * 60)
