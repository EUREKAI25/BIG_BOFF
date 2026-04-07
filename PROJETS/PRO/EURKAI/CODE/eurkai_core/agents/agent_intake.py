"""
agent_intake
Transforme une idée texte libre en objet structuré exploitable par scenario_orchestrate.
Logique déterministe — LLM optionnel en fallback isolé.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Signaux de détection de type ──────────────────────────────────────────────

_TYPE_SIGNALS = {
    "function": [
        "function", "def ", "func", "méthode", "method",
        "calcul", "calculate", "compute", "convert", "check",
        "parse", "format", "validate", "generate", "get", "fetch",
    ],
    "class": [
        "class", "objet", "object", "model", "entity",
        "représente", "represent", "profile", "user", "item",
        "document", "record", "instance",
    ],
    "module": [
        "module", "library", "bibliothèque", "package", "système",
        "system", "engine", "manager", "service", "handler",
        "gestionnaire", "moteur",
    ],
    "scenario": [
        "scenario", "scénario", "workflow", "pipeline", "orchestrat",
        "process", "processus", "flux", "flow", "chaîne", "chain",
        "séquence", "sequence",
    ],
    "page": [
        "page", "view", "vue", "interface", "ui", "screen", "dashboard",
        "formulaire", "form", "admin",
    ],
}

# Stopwords à exclure lors de la construction de l'ident
_STOPWORDS = {
    "a", "an", "the", "that", "this", "with", "for", "and", "or",
    "in", "on", "to", "of", "from", "by", "is", "are", "be",
    "create", "make", "build", "write", "add", "new", "simple",
    "python", "code", "which", "can", "une", "un", "qui", "que",
    "de", "du", "le", "la", "les", "en", "et", "ou", "pour",
    "dans", "sur", "avec", "est", "sont",
}


def run(idea, catalog=None, model_type="deterministic", verbose=True,
        agent_ident="agent_intake"):
    """
    Transforme une idée texte libre en objet structuré.

    idea       : str — idée en langage naturel
    catalog    : dict — non utilisé en mode déterministe, passé au LLM si fallback
    model_type : "deterministic" | "llm"

    Retourne :
        status  — "success" | "failure"
        object  — dict avec type/ident/goal/params (ou None si failure)
        raw     — idée originale
    """
    if not idea or not idea.strip():
        return _failure("idea_empty", idea)

    idea_clean = idea.strip()
    lower      = idea_clean.lower()

    object_type = _detect_type(lower)
    ident       = _build_ident(lower, object_type)
    goal        = _build_goal(idea_clean, object_type, ident)
    params      = _extract_params(lower)

    if not ident:
        if model_type != "deterministic":
            return _llm_fallback(idea_clean, model_type, catalog, verbose)
        return _failure("ident_unresolvable", idea_clean)

    obj = {
        "type":     object_type,
        "ident":    ident,
        "goal":     goal,
        "params":   params,
        # Champs compatibles avec scenario_orchestrate
        "object_type":    object_type,
        "object_lineage": f"Object:{_to_pascal(ident)}",
        "object_goal":    goal,
        "attributes":     params.get("attributes", {}),
    }

    if verbose:
        print(f"  [agent]   {agent_ident} — type:{object_type} ident:{ident}")
        print(f"  [OK]      goal: {goal[:60]}{'...' if len(goal) > 60 else ''}")

    return {"status": "success", "object": obj, "raw": idea_clean}


# ── Détection de type ─────────────────────────────────────────────────────────

def _detect_type(lower):
    scores = {t: 0 for t in _TYPE_SIGNALS}
    for type_name, signals in _TYPE_SIGNALS.items():
        for sig in signals:
            if sig in lower:
                scores[type_name] += 1
    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else "function"


# ── Construction de l'ident ───────────────────────────────────────────────────

def _build_ident(lower, object_type):
    # Nettoyer : supprimer ponctuation, garder mots
    words = re.findall(r"[a-zàâäéèêëîïôùûüç]+", lower)

    # Retirer stopwords + le nom du type lui-même
    type_words = set(re.findall(r"[a-z]+", object_type))
    filtered   = [w for w in words if w not in _STOPWORDS and w not in type_words]

    if not filtered:
        # Fallback : prendre les 3 premiers mots de l'idée
        filtered = [w for w in words if w not in _STOPWORDS][:3]

    if not filtered:
        return ""

    # Limiter à 4 mots max, construire snake_case
    slug = "_".join(filtered[:4])
    return re.sub(r"[^a-z0-9_]", "", slug).strip("_")


# ── Construction du goal ──────────────────────────────────────────────────────

def _build_goal(idea, object_type, ident):
    # Si l'idée ressemble déjà à une description, la retourner telle quelle
    if len(idea) > 20 and not idea.lower().startswith(("create", "make", "build", "write", "add")):
        return idea

    # Sinon, reformuler
    _type_labels = {
        "function": "Fonction",
        "class":    "Classe",
        "module":   "Module",
        "scenario": "Scénario",
        "page":     "Page",
    }
    label = _type_labels.get(object_type, "Objet")
    name  = ident.replace("_", " ")
    return f"{label} {name} — {idea.rstrip('.')}"


# ── Extraction de paramètres simples ──────────────────────────────────────────

def _extract_params(lower):
    params     = {}
    attributes = {}

    # Détecter des arguments typiques dans l'idée
    _type_hints = {
        r"\bprice\b|\bprix\b|\bcost\b|\bcost\b":             ("price",       "float"),
        r"\brate\b|\btaux\b|\bpercent\b|\bpourcentage\b":    ("rate",        "float"),
        r"\bname\b|\bnom\b":                                  ("name",        "str"),
        r"\bemail\b|\bmail\b":                                ("email",       "str"),
        r"\bdate\b":                                          ("date",        "str"),
        r"\bamount\b|\bmontant\b":                            ("amount",      "float"),
        r"\blist\b|\bliste\b|\bitems\b":                      ("items",       "list"),
        r"\bvalue\b|\bvaleur\b|\bval\b":                      ("value",       "float"),
        r"\btext\b|\btexte\b|\bstring\b|\bchaine\b":          ("text",        "str"),
        r"\buser\b|\butilisateur\b":                          ("user_id",     "str"),
        r"\bfile\b|\bfichier\b|\bpath\b|\bchemin\b":          ("path",        "str"),
    }

    for pattern, (attr_name, attr_type) in _type_hints.items():
        if re.search(pattern, lower):
            attributes[attr_name] = attr_type

    if attributes:
        params["attributes"] = attributes

    return params


# ── LLM fallback (isolé) ──────────────────────────────────────────────────────

def _llm_fallback(idea, model_type, catalog, verbose):
    try:
        from core.functions.prompt_execute import execute
    except ImportError:
        return _failure("llm_not_available", idea)

    prompt = (
        f"Tu es un agent EURKAI. Transforme cette idée en objet structuré JSON.\n"
        f"Idée : {idea}\n\n"
        f"Réponds uniquement avec un JSON valide de cette forme :\n"
        f'{{"type":"function|class|module|scenario","ident":"snake_case_name",'
        f'"goal":"description courte","attributes":{{}}}}\n'
    )

    result = execute(model_type, prompt, {"max_tokens": 256}, catalog or {})
    if not result.get("success"):
        return _failure(f"llm_failed:{result.get('error')}", idea)

    import json
    text = result.get("content", "")
    m    = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return _failure("llm_no_json", idea)
    try:
        data = json.loads(m.group(0))
    except Exception:
        return _failure("llm_invalid_json", idea)

    ident = data.get("ident", "")
    obj   = {
        "type":           data.get("type", "function"),
        "ident":          ident,
        "goal":           data.get("goal", idea),
        "params":         {"attributes": data.get("attributes", {})},
        "object_type":    data.get("type", "function"),
        "object_lineage": f"Object:{_to_pascal(ident)}",
        "object_goal":    data.get("goal", idea),
        "attributes":     data.get("attributes", {}),
    }
    if verbose:
        print(f"  [OK]      agent_intake (llm) — {ident}")
    return {"status": "success", "object": obj, "raw": idea}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_pascal(s):
    return "".join(w.capitalize() for w in re.split(r"[_\-\s]+", s or ""))


def _failure(reason, idea):
    return {"status": "failure", "object": None, "raw": idea, "reason": reason}


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    ideas = [
        "create a python function that calculates VAT from a price and a rate",
        "build a class to represent a user profile with name and email",
        "module for sending outbound emails with templates",
        "scenario that orchestrates the payment checkout flow",
        "admin dashboard page for managing projects",
        "calculate the average of a list of values",
        "une fonction qui convertit des degrés Celsius en Fahrenheit",
        "",
    ]

    print("=" * 60)
    print("  agent_intake — smoke test")
    print("=" * 60)

    passed = failed = 0
    for idea in ideas:
        r = run(idea, verbose=False)
        ok = r["status"] == "success"
        print(f"\n{'✓' if ok else '✗'} \"{idea[:50]}{'...' if len(idea) > 50 else ''}\"")
        if ok:
            o = r["object"]
            print(f"  type   : {o['type']}")
            print(f"  ident  : {o['ident']}")
            print(f"  goal   : {o['goal'][:70]}")
            if o.get("attributes"):
                print(f"  attrs  : {o['attributes']}")
            passed += 1
        else:
            print(f"  reason : {r.get('reason')}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  {passed}/{passed + failed} passed")
    print("=" * 60)
