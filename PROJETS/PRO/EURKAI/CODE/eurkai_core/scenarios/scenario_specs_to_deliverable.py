"""
scenario_specs_to_deliverable
Scénario de routage : specs → livrable du bon type.

Usage direct :
    from scenarios.scenario_specs_to_deliverable import run
    result = run({"specs": {...}})

Futur usage via convert() :
    specs.convert("deliverable")   →   appelle run() avec specs.data

Étapes :
  1. validate_input       — vérifie présence et structure des specs
  2. detect_type          — infère le type de livrable depuis le contenu des specs
  3. route_generation     — dispatch vers le bon générateur
  4. normalize_output     — garantit la structure du livrable retourné
  5. assemble_result      — retour standardisé {from/to/data/meta}

Types de livrables :
  code     → branché sur scenario_orchestrate (réel)
  page     → stub structuré : layout + sections + components
  document → stub structuré : outline + sections + contenu
  content  → stub structuré : brief contenu + plan éditorial
  media    → stub structuré : media pack spec + assets list

Règles de détection :
  architecture + components + data_models + api_endpoints → code
  layout / page / landing / interface                     → page
  posts / articles / newsletter / copy                    → content
  document / guide / report / specification               → document
  visuals / assets / image / media                        → media
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_specs_to_deliverable"):
    """
    Transforme des specs en livrable du bon type.

    input_data : dict — doit contenir la clé "specs" (dict)
    verbose    : bool

    Retourne {status, from, to, data: {deliverable_type, deliverable}, meta}.
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation ──────────────────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, None, meta)

    specs = val["specs"]

    # ── Étape 2 — Détection du type ───────────────────────────────────────────
    deliverable_type = _detect_type(specs)
    meta["steps"].append(_step_record("detect_type", True))
    meta["deliverable_type"] = deliverable_type

    if verbose:
        project_name = specs.get("architecture", {}).get("pattern", "") or ""
        print(f"  [agent]   {agent_ident} — type détecté : {deliverable_type} ({project_name[:40]})")

    # ── Étape 3 — Routage vers le générateur ─────────────────────────────────
    gen = _route_generation(deliverable_type, specs, verbose)
    meta["steps"].append(_step_record("route_generation", gen["ok"],
                                       gen.get("error") if not gen["ok"] else None))
    meta["generator_status"] = gen.get("generator_status", "ok")

    if not gen["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — route_generation : {gen['error']}")
        meta["errors"].append(gen["error"])
        return _assemble_result("partial", deliverable_type, gen.get("deliverable"), meta)

    # ── Étape 4 — Normalisation ───────────────────────────────────────────────
    norm = _normalize_output(deliverable_type, gen["deliverable"])
    meta["steps"].append(_step_record("normalize_output", norm["ok"]))

    if verbose:
        print(f"  [OK]      {agent_ident} — {deliverable_type} prêt")

    # ── Étape 5 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))

    # status = "success" si généré, "partial" si stub
    status = "success" if gen.get("is_real") else "partial"
    return _assemble_result(status, deliverable_type, norm["deliverable"], meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}
    specs = input_data.get("specs")
    if not specs or not isinstance(specs, dict):
        return {"ok": False, "error": "specs_missing_or_invalid"}
    if not any(k in specs for k in ("architecture", "components", "data_models",
                                     "api_endpoints", "tech_flows", "tech_constraints")):
        return {"ok": False, "error": "specs_has_no_usable_content"}
    return {"ok": True, "specs": specs}


def _detect_type(specs):
    """
    Infère le type de livrable depuis le contenu des specs.
    Signaux backend (models, endpoints non-vides) → code en priorité.
    Signaux page/content/doc/media → override si pas de backend réel.
    """
    has_arch       = bool(specs.get("architecture"))
    has_components = bool(specs.get("components"))
    has_models     = bool(specs.get("data_models"))          # liste non-vide
    has_endpoints  = bool([e for e in (specs.get("api_endpoints") or [])
                           if e.get("path")])                 # endpoints réels

    all_text = _specs_to_text(specs)

    # Signaux textuels
    is_page    = bool(re.search(r"\blanding\b|\bhome.?page\b|\bwireframe\b|\blayout\b", all_text))
    is_content = bool(re.search(r"\bposts?\b|\barticles?\b|\bnewsletter\b|\bcopy\b|\bedito\b", all_text))
    is_doc     = bool(re.search(r"\bdocument\b|\bguide\b|\breport\b|\boutline\b", all_text))
    is_media   = bool(re.search(r"\bvisuals?\b|\bassets?\b|\bmockup\b|\billustration\b", all_text))

    # Code : signaux backend explicites, ou architecture + composants sans override
    if has_models or has_endpoints:
        return "code"
    if has_arch and has_components and not (is_page or is_content or is_doc or is_media):
        return "code"

    # Autres types, par priorité de signal
    if is_page:    return "page"
    if is_content: return "content"
    if is_doc:     return "document"
    if is_media:   return "media"

    return "code"   # défaut


def _route_generation(deliverable_type, specs, verbose):
    """
    Dispatch vers le bon générateur selon le type.
    Seul `code` est réellement branché. Les autres retournent un stub structuré.
    """
    if deliverable_type == "code":
        return _generate_code(specs, verbose)
    if deliverable_type == "page":
        return _generate_page_stub(specs)
    if deliverable_type == "content":
        return _generate_content_stub(specs)
    if deliverable_type == "document":
        return _generate_document_stub(specs)
    if deliverable_type == "media":
        return _generate_media_stub(specs)
    return {"ok": False, "error": f"unknown_deliverable_type:{deliverable_type}"}


def _normalize_output(deliverable_type, deliverable):
    """Garantit les champs minimaux du livrable selon son type."""
    if not deliverable or not isinstance(deliverable, dict):
        return {"ok": False, "deliverable": {}}

    norm = dict(deliverable)
    norm.setdefault("type",   deliverable_type)
    norm.setdefault("status", "ready")

    return {"ok": True, "deliverable": norm}


# ── Générateurs ───────────────────────────────────────────────────────────────

def _generate_code(specs, verbose):
    """
    Branché sur scenario_orchestrate.
    Génère le module principal défini dans l'architecture.
    """
    try:
        from scenarios.scenario_orchestrate import run as orchestrate
    except ImportError as e:
        return {"ok": False, "error": f"orchestrate_import_failed:{e}"}

    # Extraire le composant P1 principal
    arch       = specs.get("architecture", {})
    components = specs.get("components", [])
    models     = specs.get("data_models", [])

    main_comp  = next((c for c in components if c.get("priority") == "P1"), None)
    comp_name  = main_comp["name"] if main_comp else "MainModule"
    feature    = main_comp.get("feature", comp_name) if main_comp else comp_name
    layer      = main_comp.get("layer", "backend") if main_comp else "backend"

    # Inférer object_type depuis le layer
    object_type = {
        "frontend": "class",
        "backend":  "module",
        "shared":   "class",
    }.get(layer, "module")

    # Construire le goal depuis l'architecture
    goal = (
        f"{feature}. Pattern : {arch.get('pattern', '')}. "
        f"Stack : {arch.get('stack_notes', '')}."
    )

    schema_ident = _to_snake(comp_name)
    params = {
        "object_type":    object_type,
        "object_goal":    goal,
        "object_lineage": f"Module:{comp_name}",
        "attributes":     {m["name"]: "model" for m in models[:3]},
    }

    result = orchestrate(
        schema_ident, params,
        catalog={"_storage": None},
        verbose=verbose,
    )

    if result.get("status") in ("success", "partial"):
        deliverable = {
            "type":           "code",
            "entry_point":    comp_name,
            "filename":       result.get("filename", ""),
            "code":           result.get("code", ""),
            "validation":     result.get("validation", {}),
            "components_all": [c["name"] for c in components],
            "note":           (
                f"Module principal généré. "
                f"{len(components)} composants identifiés dans les specs — "
                f"générer chacun individuellement via scenario_orchestrate."
            ),
        }
        return {"ok": True, "is_real": True, "generator_status": result["status"],
                "deliverable": deliverable}

    return {"ok": False, "error": f"orchestrate_failed:{result.get('status')}",
            "deliverable": None}


def _generate_page_stub(specs):
    """Prépare un stub de livrable page depuis les specs."""
    arch       = specs.get("architecture", {})
    components = specs.get("components", [])
    tech_c     = specs.get("tech_constraints", {})

    ui_components = [c for c in components if c.get("layer") == "frontend"]

    deliverable = {
        "type":   "page",
        "status": "stub",
        "layout": {
            "pattern":  arch.get("pattern", ""),
            "sections": ["header", "hero", "features", "cta", "footer"],
        },
        "components": [c["name"] for c in ui_components[:6]],
        "ux_constraints": tech_c.get("from_cdc_ux", []),
        "tech_constraints": tech_c.get("from_cdc_tech", []),
        "next_step": "Brancher sur scenario_orchestrate avec object_type='page' pour générer le HTML.",
    }
    return {"ok": True, "is_real": False, "generator_status": "stub", "deliverable": deliverable}


def _generate_document_stub(specs):
    """Prépare un stub de livrable document depuis les specs."""
    arch    = specs.get("architecture", {})
    tech_c  = specs.get("tech_constraints", {})

    deliverable = {
        "type":   "document",
        "status": "stub",
        "outline": [
            "1. Introduction et contexte",
            "2. Architecture technique",
            "3. Composants et modules",
            "4. Modèles de données",
            "5. API et intégrations",
            "6. Contraintes techniques et sécurité",
            "7. Déploiement et infrastructure",
        ],
        "architecture_summary": arch.get("pattern", ""),
        "security_highlights":  tech_c.get("security", [])[:3],
        "next_step": "Générer le document complet via agent dédié ou export Markdown/HTML.",
    }
    return {"ok": True, "is_real": False, "generator_status": "stub", "deliverable": deliverable}


def _generate_content_stub(specs):
    """Prépare un stub de livrable contenu éditorial depuis les specs."""
    arch       = specs.get("architecture", {})
    components = specs.get("components", [])

    deliverable = {
        "type":   "content",
        "status": "stub",
        "editorial_plan": [
            {"format": "landing page copy",    "status": "à générer"},
            {"format": "onboarding emails (3)","status": "à générer"},
            {"format": "FAQ (5 questions)",    "status": "à générer"},
            {"format": "feature highlights",   "status": "à générer"},
        ],
        "tone":       "professionnel, clair, orienté bénéfice",
        "key_topics": [c["feature"] for c in components[:5]],
        "next_step":  "Générer chaque pièce de contenu via agent_brief + LLM copy.",
    }
    return {"ok": True, "is_real": False, "generator_status": "stub", "deliverable": deliverable}


def _generate_media_stub(specs):
    """Prépare un stub de media pack depuis les specs."""
    arch       = specs.get("architecture", {})
    components = specs.get("components", [])
    ui_comps   = [c for c in components if c.get("layer") == "frontend"]

    deliverable = {
        "type":   "media",
        "status": "stub",
        "assets_required": [
            {"name": "Logo",            "format": "SVG + PNG 2x",  "status": "à créer"},
            {"name": "Favicon",         "format": "ICO + SVG",     "status": "à créer"},
            {"name": "OG image",        "format": "PNG 1200×630",  "status": "à créer"},
            {"name": "UI screenshots",  "format": "PNG 1440w",     "status": "à créer"},
            {"name": "Icon set",        "format": "SVG sprite",    "status": "à créer"},
        ],
        "screens": [c["name"] for c in ui_comps[:4]],
        "style_direction": "Clean, professional, modern sans-serif",
        "next_step": "Générer les assets via pipeline design (design_catalog + ToolPage).",
    }
    return {"ok": True, "is_real": False, "generator_status": "stub", "deliverable": deliverable}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _specs_to_text(specs):
    """Concatène récursivement les valeurs string des specs pour la détection."""
    parts = []
    def _walk(obj):
        if isinstance(obj, str):
            parts.append(obj.lower())
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
    _walk(specs)
    return " ".join(parts)


def _to_snake(s):
    s = re.sub(r"([A-Z])", r"_\1", str(s)).lower().strip("_")
    return re.sub(r"[^a-z0-9_]", "_", s)


def _assemble_result(status, deliverable_type, deliverable, meta):
    return {
        "status": status,
        "from":   "specs",
        "to":     "deliverable",
        "data":   {"deliverable_type": deliverable_type, "deliverable": deliverable}
                  if deliverable_type else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    _SPECS_CODE = {
        "architecture": {
            "pattern":    "Client-Server · REST API · SPA frontend",
            "layers":     ["Frontend (SPA)", "Backend API", "Database — PostgreSQL", "Auth — JWT"],
            "stack_notes":"Containerized. Deploy on Railway.",
        },
        "components": [
            {"name": "InvoiceModule",   "type": "Module",      "layer": "backend",  "feature": "Invoice creation", "priority": "P1"},
            {"name": "PaymentService",  "type": "Service",     "layer": "backend",  "feature": "Payment tracking", "priority": "P1"},
            {"name": "AuthModule",      "type": "Auth module", "layer": "shared",   "feature": "Authentication",  "priority": "P1"},
            {"name": "DashboardView",   "type": "UI component","layer": "frontend", "feature": "Dashboard",       "priority": "P2"},
            {"name": "BillingService",  "type": "Service",     "layer": "backend",  "feature": "Billing",         "priority": "P1"},
        ],
        "data_models": [
            {"name": "User",    "table": "users",    "fields": [{"name": "id", "type": "uuid"}]},
            {"name": "Invoice", "table": "invoices", "fields": [{"name": "id", "type": "uuid"}]},
        ],
        "api_endpoints": [
            {"method": "POST", "path": "/auth/login",    "auth": False},
            {"method": "GET",  "path": "/invoices",      "auth": True},
        ],
        "tech_constraints": {
            "security":      ["JWT 15-min tokens", "bcrypt passwords"],
            "from_cdc_tech": ["Responsive web", "API-first"],
            "from_cdc_ux":   ["Onboarding < 5 min"],
        },
    }

    _SPECS_PAGE = {
        "architecture": {"pattern": "landing page wireframe"},
        "components": [
            {"name": "HeroSection",  "type": "UI component", "layer": "frontend", "feature": "Hero CTA",   "priority": "P1"},
            {"name": "FeatureGrid",  "type": "UI component", "layer": "frontend", "feature": "Features",   "priority": "P1"},
            {"name": "PricingTable", "type": "UI component", "layer": "frontend", "feature": "Pricing",    "priority": "P2"},
        ],
        "tech_constraints": {"from_cdc_ux": ["CTA visible above fold", "Mobile first"]},
        "api_endpoints": [],
        "data_models":   [],
    }

    cases = [
        {"label": "✓ Code (SaaS invoicing)",        "input": {"specs": _SPECS_CODE}},
        {"label": "✓ Page (landing page)",           "input": {"specs": _SPECS_PAGE}},
        {"label": "✓ Code forcé (architecture seule)",
         "input": {"specs": {"architecture": {"pattern": "REST API service"},
                              "components": [{"name": "ApiHandler", "priority": "P1",
                                              "layer": "backend", "feature": "API handling",
                                              "type": "Service"}],
                              "data_models": [], "api_endpoints": [], "tech_constraints": {}}}},
        {"label": "✗ specs manquantes",              "input": {"specs": None}},
        {"label": "✗ input invalide",               "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_specs_to_deliverable — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] in ("success", "partial")
        print(f"\n{case['label']}")
        print(f"  status     : {r['status']}")
        print(f"  from→to    : {r['from']} → {r['to']}")
        print(f"  steps      : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if r.get("data"):
            dtype = r["data"].get("deliverable_type")
            deliv = r["data"].get("deliverable") or {}
            print(f"  type       : {dtype}")
            print(f"  gen_status : {r['meta'].get('generator_status', '—')}")
            if dtype == "code":
                print(f"  filename   : {deliv.get('filename', '—')}")
                print(f"  entry      : {deliv.get('entry_point', '—')}")
                print(f"  all_comps  : {deliv.get('components_all', [])}")
                print(f"  validation : {deliv.get('validation', {}).get('score', '—')}/100")
            else:
                first_key = next((k for k in deliv if k not in ("type", "status")), None)
                if first_key:
                    print(f"  {first_key:<12}: {str(deliv[first_key])[:60]}")
                print(f"  next_step  : {deliv.get('next_step', '')[:60]}")
        if r.get("meta", {}).get("errors"):
            print(f"  errors     : {r['meta']['errors']}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
