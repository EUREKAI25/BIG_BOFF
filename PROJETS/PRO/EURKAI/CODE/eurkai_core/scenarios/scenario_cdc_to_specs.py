"""
scenario_cdc_to_specs
Scénario autonome : cdc → specs techniques.

Usage direct :
    from scenarios.scenario_cdc_to_specs import run
    result = run({"cdc": {...}})

Futur usage via convert() :
    cdc.convert("specs")   →   appelle run() avec cdc.data

Étapes :
  1. validate_input  — vérifie présence et structure du cdc
  2. expand_cdc      — features → composants, flows → logique technique
  3. generate_specs  — construit toutes les sections
  4. normalize_output — garantit la structure des champs
  5. assemble_result — retour standardisé {from/to/data/meta}

Sections des specs :
  architecture      — pattern, layers, stack, déploiement
  components        — modules UI/service/API dérivés des features
  data_models       — modèles de données simplifiés avec champs
  api_endpoints     — endpoints REST dérivés des modèles
  tech_flows        — traduction technique des user_flows CDC
  tech_constraints  — contraintes techniques détaillées
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Templates d'architecture par type ────────────────────────────────────────

_ARCH_BY_TYPE = {
    "saas": {
        "pattern":    "Client-Server · REST API · SPA frontend",
        "layers": [
            "Frontend (SPA) — React / Vue / SvelteKit",
            "Backend API — REST (FastAPI / Express)",
            "Database — PostgreSQL (primary) + Redis (cache/sessions)",
            "Auth — JWT access token + refresh token rotation",
            "Background jobs — async tasks (Celery / BullMQ)",
        ],
        "stack_notes": "Containerized. Deploy on Railway / Fly.io / Vercel.",
    },
    "marketplace": {
        "pattern":    "Two-sided platform · transaction layer · webhooks",
        "layers": [
            "Frontend (SPA) — buyer view + seller view",
            "Backend API — REST + webhooks for payment events",
            "Database — PostgreSQL (multi-tenant schema)",
            "Payments — Stripe Connect (platform → seller payouts)",
            "Storage — S3 / Cloudinary (media uploads)",
            "Email — transactional (SendGrid / Brevo)",
        ],
        "stack_notes": "Horizontally scalable. Background workers for payout processing.",
    },
    "tool": {
        "pattern":    "Single-concern CLI or library · zero external deps default",
        "layers": [
            "CLI interface — Typer / Click / argparse",
            "Core logic — pure Python, no external I/O",
            "Config — ~/.toolrc or pyproject.toml",
            "Output formatter — plain text · JSON · table",
        ],
        "stack_notes": "Distributed as PyPI package or single binary (PyInstaller).",
    },
    "app": {
        "pattern":    "Client-Server · REST API · responsive frontend",
        "layers": [
            "Frontend — Next.js (SSR) or React (SPA)",
            "Backend API — REST (FastAPI / Express)",
            "Database — PostgreSQL",
            "Auth — OAuth2 social + email/password",
            "CDN — static assets (Cloudflare / Vercel Edge)",
        ],
        "stack_notes": "CI/CD via GitHub Actions. Preview deployments per PR.",
    },
    "dashboard": {
        "pattern":    "Data pipeline · aggregation layer · visualization frontend",
        "layers": [
            "Data sources — API integrations or direct DB read replicas",
            "Aggregation — scheduled jobs + Redis cache",
            "Backend API — REST (read-heavy, cached responses)",
            "Frontend — React + charting library (Recharts / Chart.js)",
            "Scheduler — cron for periodic data refresh",
        ],
        "stack_notes": "Read-replica DB for reporting queries. Export via background job.",
    },
    "api": {
        "pattern":    "Pure backend service · versioned REST · OpenAPI docs",
        "layers": [
            "API layer — versioned REST (/v1/…)",
            "Business logic — service/repository pattern",
            "Database — PostgreSQL + read replicas",
            "Auth — API key header + optional OAuth2",
            "Rate limiter — Redis-based sliding window",
            "Docs — OpenAPI 3.0 auto-generated (Swagger UI)",
        ],
        "stack_notes": "Containerized. SLA defined per pricing tier.",
    },
    "site": {
        "pattern":    "Static or CMS-driven · edge CDN · SSG/SSR",
        "layers": [
            "Frontend — Next.js / Astro (SSG or SSR)",
            "CMS — optional headless (Contentful / Sanity)",
            "Forms — serverless endpoint or Formspree",
            "Analytics — Plausible / GA4 (anonymized IPs)",
        ],
        "stack_notes": "Deploy on Vercel / Netlify. Edge CDN for global performance.",
    },
}

# ── Champs par type de modèle de données ─────────────────────────────────────

_MODEL_FIELDS = {
    "user": [
        {"name": "id",         "type": "uuid",      "notes": "primary key"},
        {"name": "email",      "type": "string",    "notes": "unique, indexed"},
        {"name": "password_hash", "type": "string", "notes": "bcrypt"},
        {"name": "role",       "type": "enum",      "notes": "user | admin"},
        {"name": "created_at", "type": "timestamp", "notes": "auto"},
    ],
    "invoice": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "user_id",     "type": "uuid",      "notes": "FK → User"},
        {"name": "amount",      "type": "decimal",   "notes": "2 decimal places"},
        {"name": "status",      "type": "enum",      "notes": "draft | sent | paid | overdue"},
        {"name": "due_date",    "type": "date",      "notes": ""},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "payment": [
        {"name": "id",             "type": "uuid",      "notes": "primary key"},
        {"name": "invoice_id",     "type": "uuid",      "notes": "FK → Invoice"},
        {"name": "amount",         "type": "decimal",   "notes": ""},
        {"name": "provider",       "type": "string",    "notes": "stripe | manual"},
        {"name": "transaction_id", "type": "string",    "notes": "external ref"},
        {"name": "paid_at",        "type": "timestamp", "notes": ""},
    ],
    "listing": [
        {"name": "id",          "type": "uuid",   "notes": "primary key"},
        {"name": "seller_id",   "type": "uuid",   "notes": "FK → User"},
        {"name": "title",       "type": "string", "notes": ""},
        {"name": "description", "type": "text",   "notes": ""},
        {"name": "price",       "type": "decimal","notes": ""},
        {"name": "status",      "type": "enum",   "notes": "active | paused | deleted"},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "order": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "buyer_id",    "type": "uuid",      "notes": "FK → User"},
        {"name": "listing_id",  "type": "uuid",      "notes": "FK → Listing"},
        {"name": "status",      "type": "enum",      "notes": "pending | confirmed | delivered | cancelled"},
        {"name": "total",       "type": "decimal",   "notes": ""},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "project": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "owner_id",    "type": "uuid",      "notes": "FK → User"},
        {"name": "name",        "type": "string",    "notes": ""},
        {"name": "status",      "type": "enum",      "notes": "active | archived"},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "course": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "author_id",   "type": "uuid",      "notes": "FK → User"},
        {"name": "title",       "type": "string",    "notes": ""},
        {"name": "description", "type": "text",      "notes": ""},
        {"name": "status",      "type": "enum",      "notes": "draft | published"},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "notification": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "user_id",     "type": "uuid",      "notes": "FK → User"},
        {"name": "type",        "type": "string",    "notes": ""},
        {"name": "payload",     "type": "json",      "notes": ""},
        {"name": "read_at",     "type": "timestamp", "notes": "nullable"},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
    "report": [
        {"name": "id",          "type": "uuid",      "notes": "primary key"},
        {"name": "owner_id",    "type": "uuid",      "notes": "FK → User"},
        {"name": "type",        "type": "string",    "notes": ""},
        {"name": "data",        "type": "json",      "notes": "snapshot"},
        {"name": "created_at",  "type": "timestamp", "notes": "auto"},
    ],
}

# ── Signaux pour inférer les modèles depuis les features ─────────────────────

_FEATURE_TO_MODEL = [
    (r"invoice",                "invoice"),
    (r"payment",                "payment"),
    (r"order",                  "order"),
    (r"listing|product|service","listing"),
    (r"course|lesson",          "course"),
    (r"project|task",           "project"),
    (r"notif|alert|reminder",   "notification"),
    (r"report|export|dashboard","report"),
]

# ── Contraintes techniques par type ──────────────────────────────────────────

_TECH_CONSTRAINTS_BY_TYPE = {
    "saas": [
        "Authentication: JWT with 15-min access tokens + 7-day refresh tokens",
        "Password: bcrypt, min 8 chars, breach check via HaveIBeenPwned API",
        "HTTPS enforced everywhere, HSTS preload",
        "DB: row-level security for multi-tenant data isolation",
        "API rate limiting: 100 req/min per authenticated user",
        "Logging: structured JSON logs, no PII in logs",
    ],
    "marketplace": [
        "Payments: Stripe Connect — escrow held until delivery confirmed",
        "KYC: seller identity verification before first payout",
        "Commission: computed server-side only, never client-supplied",
        "Dispute window: 7 days post-delivery before funds released",
        "Media: max 10 MB per file, image resizing on upload (S3 + Lambda)",
        "Webhooks: Stripe events processed idempotently",
    ],
    "tool": [
        "Zero side effects unless --write flag explicitly passed",
        "Stdin/stdout interface — composable with pipes",
        "Exit codes: 0 success, 1 user error, 2 internal error",
        "No network calls without explicit flag",
        "Config file validated on load (schema + type checking)",
        "Deterministic output for same input (no timestamps in default output)",
    ],
    "app": [
        "HTTPS enforced, HSTS header set",
        "CSP (Content Security Policy) configured",
        "Image optimization: WebP, lazy loading, srcset",
        "Bundle size budget: < 200 KB gzipped initial JS",
        "Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1",
        "Accessibility: all interactive elements keyboard-navigable",
    ],
    "dashboard": [
        "Read queries on read replica — no analytics on primary DB",
        "Cache TTL: metrics data cached 5 min (Redis), exports 1 hour",
        "Export jobs async — user notified by email when ready",
        "Date ranges capped at 12 months to prevent runaway queries",
        "Role-based visibility: users only see their own org data",
        "All chart data available as CSV export",
    ],
    "api": [
        "Versioning: URI versioning (/v1/, /v2/) with sunset headers",
        "Authentication: Bearer token (API key) in Authorization header",
        "Rate limiting: 1000 req/hour free tier, configurable paid tiers",
        "Idempotency: POST endpoints accept Idempotency-Key header",
        "Pagination: cursor-based for all list endpoints",
        "Errors: RFC 7807 problem+json format",
    ],
    "site": [
        "All forms: CSRF protection, honeypot field, server-side validation",
        "Images: next/image or equivalent for automatic optimization",
        "Fonts: self-hosted, no Google Fonts (GDPR)",
        "Analytics: IP anonymization, no cross-site tracking",
        "Meta: canonical tags, og:image, structured data (JSON-LD)",
        "No render-blocking resources above the fold",
    ],
}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_cdc_to_specs"):
    """
    Transforme un CDC en specs techniques structurées.

    input_data : dict — doit contenir la clé "cdc" (dict)
    verbose    : bool

    Retourne un dict standardisé {status, from, to, data, meta}.
    Compatible futur cdc.convert("specs").
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation ──────────────────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    cdc = val["cdc"]
    project_type = cdc.get("project_overview", {}).get("project_type", "tool")
    project_name = cdc.get("project_overview", {}).get("project_name", "")

    if verbose:
        print(f"  [agent]   {agent_ident} — cdc:{project_name} type:{project_type}")

    # ── Étape 2 — Expansion du CDC ────────────────────────────────────────────
    expanded = _expand_cdc(cdc, project_type)
    meta["steps"].append(_step_record("expand_cdc", True))

    # ── Étape 3 — Génération des specs ────────────────────────────────────────
    specs_raw = _generate_specs(cdc, expanded, project_type)
    meta["steps"].append(_step_record("generate_specs", True))

    # ── Étape 4 — Normalisation ───────────────────────────────────────────────
    norm = _normalize_output(specs_raw)
    meta["steps"].append(_step_record("normalize_output", norm["ok"]))

    if verbose:
        s = norm["specs"]
        print(f"  [OK]      {agent_ident} — "
              f"{len(s['components'])} components, "
              f"{len(s['data_models'])} models, "
              f"{len(s['api_endpoints'])} endpoints")

    # ── Étape 5 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))
    return _assemble_result("success", norm["specs"], meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}

    cdc = input_data.get("cdc")
    if not cdc or not isinstance(cdc, dict):
        return {"ok": False, "error": "cdc_missing_or_invalid"}

    if not cdc.get("project_overview") and not cdc.get("core_features"):
        return {"ok": False, "error": "cdc_has_no_usable_content"}

    return {"ok": True, "cdc": cdc}


def _expand_cdc(cdc, project_type):
    """
    Transforme les features et flows du CDC en matière première pour les specs.
    """
    features    = cdc.get("core_features") or []
    user_flows  = cdc.get("user_flows") or []
    constraints = cdc.get("constraints") or {}

    # Features → composants
    components = _features_to_components(features, project_type)

    # Features → modèles de données
    model_names = _infer_model_names(features, project_type)

    # User flows → flows techniques
    tech_flows = _flows_to_tech(user_flows, components, project_type)

    return {
        "components":   components,
        "model_names":  model_names,
        "tech_flows":   tech_flows,
        "base_constraints": constraints,
    }


def _generate_specs(cdc, expanded, project_type):
    """Construit toutes les sections des specs."""
    arch        = _ARCH_BY_TYPE.get(project_type, _ARCH_BY_TYPE["app"])
    models      = _build_data_models(expanded["model_names"])
    endpoints   = _build_api_endpoints(expanded["model_names"], project_type)
    tech_constr = _TECH_CONSTRAINTS_BY_TYPE.get(project_type, [])

    # Fusionner contraintes CDC (tech + ux) avec contraintes specs
    base_tech = (expanded["base_constraints"].get("tech") or [])
    base_ux   = (expanded["base_constraints"].get("ux") or [])

    return {
        "architecture":     arch,
        "components":       expanded["components"],
        "data_models":      models,
        "api_endpoints":    endpoints,
        "tech_flows":       expanded["tech_flows"],
        "tech_constraints": {
            "security":     tech_constr[:3],
            "performance":  tech_constr[3:6] if len(tech_constr) > 3 else [],
            "from_cdc_tech": base_tech,
            "from_cdc_ux":   base_ux,
        },
    }


def _normalize_output(specs):
    """Garantit que tous les champs sont présents et bien typés."""
    _list_fields = ("components", "data_models", "api_endpoints", "tech_flows")
    _dict_fields = ("architecture", "tech_constraints")

    normalized = dict(specs)

    for field in _list_fields:
        if not isinstance(normalized.get(field), list):
            normalized[field] = []

    for field in _dict_fields:
        if not isinstance(normalized.get(field), dict):
            normalized[field] = {}

    # Garantir les sous-clés de tech_constraints
    tc = normalized["tech_constraints"]
    tc.setdefault("security",      [])
    tc.setdefault("performance",   [])
    tc.setdefault("from_cdc_tech", [])
    tc.setdefault("from_cdc_ux",   [])

    # Garantir les sous-clés d'architecture
    a = normalized["architecture"]
    a.setdefault("pattern",     "")
    a.setdefault("layers",      [])
    a.setdefault("stack_notes", "")

    return {"ok": True, "specs": normalized}


# ── Helpers — composants ──────────────────────────────────────────────────────

def _features_to_components(features, project_type):
    """Chaque feature → un composant avec type et layer."""
    components = []

    _layer_hints = {
        r"dashboard|analytics|report|chart|graph":             "frontend",
        r"notif|alert|reminder|email":                        "backend",
        r"export|import|upload|download":                      "backend",
        r"auth|login|register|password|token":                 "shared",
        r"api|endpoint|webhook|integration":                   "backend",
        r"form|modal|page|view|screen|list|grid":             "frontend",
        r"payment|invoice|billing|subscription|charge":        "backend",
    }

    _type_hints = {
        r"form|editor|modal|input":     "UI component",
        r"list|table|grid|board":       "UI component",
        r"chart|graph|dashboard":       "UI component",
        r"service|manager|handler":     "Service",
        r"api|endpoint|webhook":        "API handler",
        r"export|import|upload":        "Utility service",
        r"notif|email|alert":           "Background service",
        r"auth|session|token":          "Auth module",
    }

    for feature in features:
        lower  = feature.lower() if isinstance(feature, str) else (feature.get("name","")).lower()
        name   = feature if isinstance(feature, str) else feature.get("name", "")
        prio   = feature.get("priority", "P2") if isinstance(feature, dict) else "P2"

        component_name = _to_pascal(name)

        # Inférer layer
        layer = "shared"
        for pattern, lyr in _layer_hints.items():
            if re.search(pattern, lower):
                layer = lyr
                break

        # Inférer type
        comp_type = "Module"
        for pattern, t in _type_hints.items():
            if re.search(pattern, lower):
                comp_type = t
                break

        components.append({
            "name":     component_name,
            "type":     comp_type,
            "layer":    layer,
            "feature":  name,
            "priority": prio,
        })

    # Ajouter composants systèmes selon le type de projet
    system_components = _get_system_components(project_type)
    components.extend(system_components)

    return components


def _get_system_components(project_type):
    """Composants système toujours présents selon le type."""
    shared = [
        {"name": "AuthModule",    "type": "Auth module",   "layer": "shared",   "feature": "Authentication", "priority": "P1"},
        {"name": "ApiClient",     "type": "Service",       "layer": "frontend", "feature": "API calls",       "priority": "P1"},
        {"name": "ErrorBoundary", "type": "UI component",  "layer": "frontend", "feature": "Error handling",  "priority": "P1"},
    ]
    extras = {
        "saas":        [{"name": "BillingService",  "type": "Service",  "layer": "backend",  "feature": "Subscription billing", "priority": "P1"}],
        "marketplace": [{"name": "PaymentGateway",  "type": "Service",  "layer": "backend",  "feature": "Payment processing",   "priority": "P1"},
                        {"name": "ReviewModule",    "type": "Module",   "layer": "shared",   "feature": "Reviews & ratings",    "priority": "P2"}],
        "dashboard":   [{"name": "ChartEngine",     "type": "UI component", "layer": "frontend", "feature": "Data visualization", "priority": "P1"}],
        "api":         [{"name": "RateLimiter",     "type": "Middleware","layer": "backend",  "feature": "Rate limiting",        "priority": "P1"},
                        {"name": "OpenApiDocs",     "type": "Service",  "layer": "backend",  "feature": "API documentation",    "priority": "P2"}],
    }
    return shared + extras.get(project_type, [])


def _infer_model_names(features, project_type):
    """Infers model names from feature list. Always includes User."""
    models = ["user"]

    for feature in features:
        name = feature if isinstance(feature, str) else feature.get("name", "")
        lower = name.lower()
        for pattern, model in _FEATURE_TO_MODEL:
            if re.search(pattern, lower) and model not in models:
                models.append(model)
                break

    # Toujours ajouter notification pour SaaS/marketplace (UX essentiel)
    if project_type in ("saas", "marketplace") and "notification" not in models:
        models.append("notification")

    return models


def _build_data_models(model_names):
    """Construit les data models depuis les noms inférés."""
    models = []
    for name in model_names:
        fields = _MODEL_FIELDS.get(name)
        if fields:
            models.append({
                "name":   _to_pascal(name),
                "table":  f"{name}s",
                "fields": fields,
            })
        else:
            # Modèle générique pour les noms non couverts
            models.append({
                "name":   _to_pascal(name),
                "table":  f"{name}s",
                "fields": [
                    {"name": "id",         "type": "uuid",      "notes": "primary key"},
                    {"name": "user_id",    "type": "uuid",      "notes": "FK → User"},
                    {"name": "name",       "type": "string",    "notes": ""},
                    {"name": "created_at", "type": "timestamp", "notes": "auto"},
                ],
            })
    return models


def _build_api_endpoints(model_names, project_type):
    """Génère les endpoints REST CRUD depuis les modèles."""
    endpoints = [
        # Auth — toujours présent
        {"method": "POST",   "path": "/auth/register",  "description": "Create account",       "auth": False},
        {"method": "POST",   "path": "/auth/login",     "description": "Get access token",      "auth": False},
        {"method": "POST",   "path": "/auth/refresh",   "description": "Refresh access token",  "auth": True},
        {"method": "DELETE", "path": "/auth/logout",    "description": "Revoke refresh token",  "auth": True},
    ]

    # CRUD par modèle (sauf User — géré via /auth + /users/me)
    skip  = {"user"}
    for name in model_names:
        if name in skip:
            continue
        plural = f"{name}s"
        endpoints += [
            {"method": "GET",    "path": f"/{plural}",        "description": f"List {plural}",         "auth": True},
            {"method": "POST",   "path": f"/{plural}",        "description": f"Create {name}",         "auth": True},
            {"method": "GET",    "path": f"/{plural}/{{id}}", "description": f"Get {name} by id",      "auth": True},
            {"method": "PATCH",  "path": f"/{plural}/{{id}}", "description": f"Update {name}",         "auth": True},
            {"method": "DELETE", "path": f"/{plural}/{{id}}", "description": f"Delete {name}",         "auth": True},
        ]

    # Endpoints spéciaux selon le type
    if project_type == "marketplace":
        endpoints.append(
            {"method": "POST", "path": "/orders/{id}/confirm", "description": "Confirm delivery, trigger payout", "auth": True}
        )
    if project_type in ("saas", "marketplace"):
        endpoints.append(
            {"method": "POST", "path": "/webhooks/stripe", "description": "Handle Stripe events", "auth": False}
        )

    return endpoints


def _flows_to_tech(user_flows, components, project_type):
    """Traduit les user flows CDC en flows techniques avec composants impliqués."""
    tech_flows = []

    for flow in user_flows:
        # Inférer les composants impliqués depuis les mots du flow
        lower     = flow.lower()
        involved  = []
        for comp in components:
            if any(word in lower for word in comp["feature"].lower().split()[:2]):
                involved.append(comp["name"])
        if "AuthModule" not in involved and re.search(r"log|sign|register|auth", lower):
            involved.insert(0, "AuthModule")

        # Construire étapes techniques minimales
        steps = _flow_to_steps(lower, project_type)

        tech_flows.append({
            "flow":       flow,
            "steps":      steps,
            "components": involved[:4] or ["ApiClient"],  # au moins un composant
        })

    return tech_flows


def _flow_to_steps(lower, project_type):
    """Génère des étapes techniques depuis le texte d'un flow."""
    steps = []

    if re.search(r"sign.?up|register|creat.*account", lower):
        steps += ["POST /auth/register", "Send verification email", "Redirect to onboarding"]
    elif re.search(r"log.?in|sign.?in", lower):
        steps += ["POST /auth/login", "Store JWT in httpOnly cookie", "Redirect to dashboard"]

    if re.search(r"creat|add|new|publish|list", lower):
        steps.append("POST /[resource] → validate → persist → return 201")
    if re.search(r"edit|updat|modif", lower):
        steps.append("PATCH /[resource]/{id} → validate → persist → return 200")
    if re.search(r"delet|remov|cancel|archiv", lower):
        steps.append("DELETE /[resource]/{id} → soft delete → return 204")
    if re.search(r"pay|checkout|order|book", lower):
        steps += ["POST /orders", "Initiate Stripe PaymentIntent", "Webhook confirms → update status"]
    if re.search(r"export|download|report", lower):
        steps += ["POST /exports → queue background job", "Poll GET /exports/{id}/status", "Download signed S3 URL"]
    if re.search(r"notif|alert|remind", lower):
        steps.append("Background worker → evaluate triggers → POST /notifications")

    return steps or ["GET /[resource] → fetch → render"]


# ── Helpers généraux ──────────────────────────────────────────────────────────

def _to_pascal(s):
    s = str(s)
    words = re.split(r"[\s_\-/&]+", s)
    return "".join(w.capitalize() for w in words if w)


def _assemble_result(status, specs, meta):
    """Retour standardisé. Compatible futur cdc.convert('specs')."""
    return {
        "status": status,
        "from":   "cdc",
        "to":     "specs",
        "data":   {"specs": specs} if specs else {},
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

    _CDC_SAAS = {
        "project_overview": {
            "project_name": "Freelancers Invoices Payments",
            "project_type": "saas",
            "summary": "A SaaS that helps freelancers track invoices and payments",
        },
        "core_features": [
            {"name": "Invoice creation and management",     "priority": "P1"},
            {"name": "Payment tracking and status updates", "priority": "P1"},
            {"name": "Expense recording and categorization","priority": "P2"},
            {"name": "Financial dashboard and reporting",   "priority": "P2"},
            {"name": "Export to PDF / accounting formats",  "priority": "P3"},
        ],
        "user_flows": [
            "Sign up → email verification → onboarding wizard → first action",
            "Daily use: log in → dashboard → create invoice → send to client",
        ],
        "constraints": {
            "tech": ["Responsive web (desktop-first)", "API-first architecture"],
            "ux":   ["Onboarding in < 5 min", "Contextual help / tooltips"],
        },
    }

    _CDC_MARKETPLACE = {
        "project_overview": {
            "project_name": "Designers Clients Marketplace",
            "project_type": "marketplace",
        },
        "core_features": [
            {"name": "Seller and buyer profile management", "priority": "P1"},
            {"name": "Service listing and search",          "priority": "P1"},
            {"name": "Booking or order flow",               "priority": "P1"},
            {"name": "Review and rating system",            "priority": "P2"},
        ],
        "user_flows": [
            "Buyer: browse listings → contact seller → book/order → review",
            "Seller: create profile → list service → receive order → get paid",
        ],
        "constraints": {"tech": [], "ux": []},
    }

    cases = [
        {"label": "✓ SaaS invoicing",    "input": {"cdc": _CDC_SAAS}},
        {"label": "✓ Marketplace",        "input": {"cdc": _CDC_MARKETPLACE}},
        {"label": "✗ cdc manquant",       "input": {"cdc": None}},
        {"label": "✗ input invalide",     "input": "not a dict"},
    ]

    print("=" * 65)
    print("  scenario_cdc_to_specs — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{case['label']}")
        print(f"  status    : {r['status']}")
        print(f"  from→to   : {r['from']} → {r['to']}")
        print(f"  steps     : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if ok:
            s = r["data"]["specs"]
            print(f"  arch      : {s['architecture']['pattern']}")
            print(f"  layers    : {len(s['architecture']['layers'])} layers")
            print(f"  components: {len(s['components'])} ({', '.join(c['name'] for c in s['components'][:3])}…)")
            print(f"  models    : {len(s['data_models'])} ({', '.join(m['name'] for m in s['data_models'])})")
            print(f"  endpoints : {len(s['api_endpoints'])} (auth + CRUD)")
            print(f"  flows     : {len(s['tech_flows'])} tech flows")
            print(f"  security  : {s['tech_constraints']['security'][0][:60]}")
            passed += 1
        else:
            print(f"  errors    : {r['meta']['errors']}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
