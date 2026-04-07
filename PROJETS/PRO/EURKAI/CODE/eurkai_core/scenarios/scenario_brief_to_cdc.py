"""
scenario_brief_to_cdc
Scénario autonome : brief → CDC (Cahier des Charges).

Usage direct :
    from scenarios.scenario_brief_to_cdc import run
    result = run({"brief": {...}})

Futur usage via convert() :
    brief.convert("cdc")   →   appelle run() avec brief.data

Étapes :
  1. validate_input   — vérifie présence et structure du brief
  2. expand_brief     — enrichit les champs avant structuration
  3. generate_cdc     — construit toutes les sections du CDC
  4. normalize_output — garantit la structure des champs
  5. assemble_result  — retour standardisé {from/to/data/meta}

Sections du CDC :
  project_overview  — nom, type, résumé, contexte
  objectives        — 3–5 objectifs métier
  target_users      — profils + cas d'usage
  core_features     — features détaillées avec user story + priorité
  user_flows        — parcours simplifiés
  constraints       — tech + UX + business
  success_metrics   — KPIs selon le type de projet
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Templates par type de projet ──────────────────────────────────────────────

_OBJECTIVES_BY_TYPE = {
    "saas": [
        "Provide a scalable, subscription-based solution accessible from any browser",
        "Reduce manual effort through automation of key workflows",
        "Enable teams to collaborate and track progress in real time",
        "Offer clear onboarding to reach activation in under 5 minutes",
        "Generate predictable recurring revenue through tiered pricing",
    ],
    "app": [
        "Deliver a fast and intuitive user experience on web and mobile",
        "Solve a specific user problem with minimal friction",
        "Enable offline-first usage where applicable",
        "Grow a loyal user base through strong core value delivery",
        "Collect actionable usage data to iterate quickly",
    ],
    "marketplace": [
        "Connect supply and demand efficiently in the target vertical",
        "Build trust between buyers and sellers through ratings and reviews",
        "Generate revenue through commissions on completed transactions",
        "Ensure a seamless booking or ordering experience",
        "Scale the supply side to meet growing demand",
    ],
    "tool": [
        "Solve a single, well-defined developer or power-user problem",
        "Minimize configuration — work out of the box",
        "Integrate with existing workflows and toolchains",
        "Provide clear documentation and examples",
        "Offer a free tier to drive adoption",
    ],
    "dashboard": [
        "Aggregate and visualize key business metrics in one place",
        "Enable data-driven decision making at a glance",
        "Support role-based access with appropriate data visibility",
        "Provide exportable and shareable reports",
        "Update in real time or near real time",
    ],
    "api": [
        "Expose a clean, versioned REST API with predictable behavior",
        "Handle authentication, rate limiting, and error responses correctly",
        "Provide sandbox environment and interactive documentation",
        "Support usage-based billing with transparent metering",
        "Guarantee high availability and fast response times",
    ],
    "site": [
        "Communicate the product value proposition clearly above the fold",
        "Convert visitors into leads or sign-ups",
        "Load in under 1 second and score well on Core Web Vitals",
        "Be accessible (WCAG 2.1 AA) and mobile-friendly",
        "Support SEO with proper metadata and structured content",
    ],
}

_METRICS_BY_TYPE = {
    "saas": [
        {"name": "Activation rate", "target": "> 40% of signups complete onboarding"},
        {"name": "MRR growth",       "target": "Month-over-month revenue growth"},
        {"name": "Churn rate",        "target": "< 5% monthly churn"},
        {"name": "Time to value",     "target": "< 5 min from signup to first success"},
    ],
    "marketplace": [
        {"name": "Match rate",        "target": "> 60% of requests matched within 24h"},
        {"name": "GMV",               "target": "Gross Merchandise Value (tracked monthly)"},
        {"name": "Repeat usage",      "target": "> 30% users return within 30 days"},
        {"name": "Seller satisfaction","target": "NPS > 40"},
    ],
    "tool": [
        {"name": "DAU / MAU ratio",   "target": "> 20% (stickiness)"},
        {"name": "Task success rate",  "target": "> 90% of initiated tasks completed"},
        {"name": "Time to first use",  "target": "< 2 min from install to first output"},
        {"name": "Retention D7",       "target": "> 50% of users return after 7 days"},
    ],
    "app": [
        {"name": "D1 retention",      "target": "> 40% return next day"},
        {"name": "Session length",    "target": "> 3 min average"},
        {"name": "Feature adoption",  "target": "> 60% use core feature within first session"},
        {"name": "App store rating",  "target": "> 4.2 / 5"},
    ],
    "dashboard": [
        {"name": "Daily active users", "target": "Target defined post-launch"},
        {"name": "Report exports",     "target": "Tracked per user per week"},
        {"name": "Data freshness",     "target": "< 5 min lag on live data"},
        {"name": "User satisfaction",  "target": "NPS > 35"},
    ],
    "api": [
        {"name": "Uptime",            "target": "> 99.9%"},
        {"name": "P99 latency",       "target": "< 200ms"},
        {"name": "API adoption",      "target": "Number of active API keys"},
        {"name": "Error rate",        "target": "< 0.1% of requests"},
    ],
    "site": [
        {"name": "Conversion rate",   "target": "> 3% visitors → leads"},
        {"name": "Bounce rate",       "target": "< 50%"},
        {"name": "Core Web Vitals",   "target": "LCP < 2.5s, CLS < 0.1"},
        {"name": "Organic traffic",   "target": "Month-over-month SEO growth"},
    ],
}

_BUSINESS_CONSTRAINTS_BY_TYPE = {
    "saas": [
        "GDPR compliance — user data handling and deletion",
        "Subscription billing integration (Stripe or equivalent)",
        "Multi-tenant data isolation",
    ],
    "marketplace": [
        "KYC / identity verification for sellers",
        "Escrow or secure payment flow",
        "Dispute resolution mechanism",
    ],
    "tool": [
        "Open source license or clearly defined EULA",
        "Versioning and backward compatibility policy",
        "Documentation published alongside releases",
    ],
    "app": [
        "GDPR compliance — cookie consent and data policy",
        "Accessibility (WCAG 2.1 AA minimum)",
        "Performance budget defined before build",
    ],
    "api": [
        "API versioning policy (v1, v2…)",
        "Rate limiting and quota management",
        "SLA defined per pricing tier",
    ],
    "site": [
        "Legal pages (mentions légales, CGU, politique de confidentialité)",
        "Cookie consent compliant with GDPR",
        "Analytics with anonymized IPs",
    ],
    "dashboard": [
        "Role-based access control (RBAC)",
        "Data retention policy",
        "Export formats defined (PDF, CSV)",
    ],
}

_USER_FLOW_TEMPLATES = {
    "saas": [
        "Sign up → email verification → onboarding wizard → first action",
        "Daily use: log in → dashboard → perform core action → review results",
        "Admin: manage team members → assign roles → track usage",
    ],
    "marketplace": [
        "Buyer: browse listings → contact seller → book/order → review",
        "Seller: create profile → list service → receive request → deliver → get paid",
        "Admin: moderate listings → resolve disputes → manage payouts",
    ],
    "tool": [
        "Install → run first command → see output → adjust config",
        "Repeat use: open project → run tool → review output → iterate",
    ],
    "app": [
        "Onboarding: install → sign up → complete profile → use core feature",
        "Returning: open app → see personalized view → take action → share/export",
    ],
    "dashboard": [
        "Log in → select date range → read key metrics → drill into detail → export",
        "Admin: configure data sources → set alerts → invite team members",
    ],
    "api": [
        "Get API key → read docs → make first call → handle response → go live",
        "Monitor: check usage dashboard → set rate limit alerts → review error logs",
    ],
    "site": [
        "Landing: arrive → read value prop → click CTA → sign up / contact",
        "Returning visitor: land on blog → read article → discover product → convert",
    ],
}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, verbose=True, agent_ident="scenario_brief_to_cdc"):
    """
    Transforme un brief en CDC structuré.

    input_data : dict — doit contenir la clé "brief" (dict)
    verbose    : bool — affiche les logs de progression

    Retourne un dict standardisé {status, from, to, data, meta}.
    Compatible avec le futur mécanisme brief.convert("cdc").
    """
    meta = {"steps": [], "errors": []}

    # ── Étape 1 — Validation de l'input ──────────────────────────────────────
    val = _validate_input(input_data)
    meta["steps"].append(_step_record("validate_input", val["ok"], val.get("error")))

    if not val["ok"]:
        if verbose:
            print(f"  [FAIL]    {agent_ident} — validate_input : {val['error']}")
        meta["errors"].append(val["error"])
        return _assemble_result("failure", None, meta)

    brief = val["brief"]
    if verbose:
        print(f"  [agent]   {agent_ident} — brief:{brief.get('project_name')} type:{brief.get('project_type')}")

    # ── Étape 2 — Expansion du brief ─────────────────────────────────────────
    expanded = _expand_brief(brief)
    meta["steps"].append(_step_record("expand_brief", True))

    # ── Étape 3 — Génération du CDC ───────────────────────────────────────────
    cdc_raw = _generate_cdc(brief, expanded)
    meta["steps"].append(_step_record("generate_cdc", True))

    # ── Étape 4 — Normalisation ───────────────────────────────────────────────
    norm = _normalize_output(cdc_raw)
    meta["steps"].append(_step_record("normalize_output", norm["ok"]))

    if verbose:
        n = norm["cdc"]
        print(f"  [OK]      {agent_ident} — {len(n['core_features'])} features, "
              f"{len(n['user_flows'])} flows, {len(n['success_metrics'])} metrics")

    # ── Étape 5 — Assemblage ──────────────────────────────────────────────────
    meta["steps"].append(_step_record("assemble_result", True))
    return _assemble_result("success", norm["cdc"], meta)


# ── Étapes ────────────────────────────────────────────────────────────────────

def _validate_input(input_data):
    """
    Vérifie que input_data contient un brief dict avec les champs minimaux.
    Retourne : {ok, brief, error}
    """
    if not isinstance(input_data, dict):
        return {"ok": False, "error": "input_not_a_dict"}

    brief = input_data.get("brief")
    if not brief or not isinstance(brief, dict):
        return {"ok": False, "error": "brief_missing_or_invalid"}

    if not brief.get("project_name") and not brief.get("description"):
        return {"ok": False, "error": "brief_has_no_usable_content"}

    return {"ok": True, "brief": brief}


def _expand_brief(brief):
    """
    Enrichit les champs du brief avant structuration du CDC.
    Retourne un dict de données enrichies (ne modifie pas le brief original).
    """
    project_type = brief.get("project_type", "tool")
    features     = brief.get("core_features") or []
    users        = brief.get("target_users", "general users")
    monetization = brief.get("monetization", "freemium → paid tiers")

    # Features détaillées : chaque feature devient un objet
    detailed_features = []
    priorities = ["P1", "P1", "P2", "P2", "P3"]   # les 2 premières sont critiques
    for i, feature in enumerate(features):
        prio = priorities[i] if i < len(priorities) else "P3"
        detailed_features.append({
            "name":       feature,
            "priority":   prio,
            "user_story": _make_user_story(feature, users),
        })

    # Profils utilisateurs étendus
    user_profiles = _expand_users(users, project_type)

    # Contraintes business selon le type
    business_constraints = _BUSINESS_CONSTRAINTS_BY_TYPE.get(project_type, [
        "GDPR compliance — user data handling",
        "Clear terms of service and privacy policy",
    ])

    return {
        "detailed_features":    detailed_features,
        "user_profiles":        user_profiles,
        "business_constraints": business_constraints,
        "monetization_note":    _expand_monetization(monetization),
    }


def _generate_cdc(brief, expanded):
    """
    Construit toutes les sections du CDC depuis brief + données enrichies.
    """
    project_type = brief.get("project_type", "tool")
    project_name = brief.get("project_name", "Unnamed Project")
    description  = brief.get("description", "")
    constraints  = brief.get("constraints") or {}

    return {
        "project_overview": {
            "project_name": project_name,
            "project_type": project_type,
            "summary":      description,
            "context":      _build_context(project_type, project_name),
            "monetization": expanded["monetization_note"],
        },
        "objectives": _OBJECTIVES_BY_TYPE.get(project_type,
                       _OBJECTIVES_BY_TYPE["tool"])[:4],
        "target_users": {
            "primary":    brief.get("target_users", "general users"),
            "profiles":   expanded["user_profiles"],
        },
        "core_features":   expanded["detailed_features"],
        "user_flows":      _USER_FLOW_TEMPLATES.get(project_type, [
                               "Sign in → explore → perform action → get result",
                           ]),
        "constraints": {
            "tech":     (constraints.get("tech") or []) + [
                            "Responsive design (mobile + desktop)",
                            "Secure HTTPS, authentication required",
                        ],
            "ux":       (constraints.get("ux") or []) + [
                            "Accessible (WCAG 2.1 AA)",
                            "Loading state on all async actions",
                        ],
            "business": expanded["business_constraints"],
        },
        "success_metrics": _METRICS_BY_TYPE.get(project_type,
                            _METRICS_BY_TYPE["app"])[:3],
    }


def _normalize_output(cdc):
    """
    Garantit que tous les champs CDC sont présents et bien typés.
    """
    _list_fields   = ("objectives", "user_flows", "success_metrics", "core_features")
    _dict_fields   = ("project_overview", "target_users", "constraints")

    normalized = dict(cdc)

    for field in _list_fields:
        if not isinstance(normalized.get(field), list):
            normalized[field] = []

    for field in _dict_fields:
        if not isinstance(normalized.get(field), dict):
            normalized[field] = {}

    # Garantir les sous-clés de constraints
    c = normalized["constraints"]
    c.setdefault("tech",     [])
    c.setdefault("ux",       [])
    c.setdefault("business", [])

    return {"ok": True, "cdc": normalized}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_user_story(feature, users):
    """Génère une user story basique depuis le nom de la feature."""
    # Extraire le verbe d'action et le complément
    lower   = feature.lower()
    subject = users.split(",")[0].strip() if "," in users else users

    _verb_map = [
        (r"creat|add|new",      "create"),
        (r"track|monitor",      "track"),
        (r"manag|edit|updat",   "manage"),
        (r"send|notif",         "send"),
        (r"view|see|read|list", "view"),
        (r"export|download",    "export"),
        (r"search|find|filter", "search"),
        (r"connect|integrat",   "connect"),
        (r"book|order|purchas", "book"),
        (r"review|rate",        "review"),
    ]

    verb = "use"
    for pattern, v in _verb_map:
        if re.search(pattern, lower):
            verb = v
            break

    return f"As a {subject}, I want to {verb} {feature.lower()} so that I can achieve my goal efficiently."


def _expand_users(users_str, project_type):
    """Construit des profils utilisateurs depuis la chaîne cible."""
    profiles = []
    raw_profiles = [u.strip() for u in users_str.split(",")]

    _profile_details = {
        "freelancers":       "Independent workers managing their own clients and projects",
        "small businesses":  "Teams of 2–50 managing operations without enterprise tooling",
        "developers":        "Technical users who value API access and CLI tools",
        "designers":         "Creative professionals focused on visual output and client delivery",
        "marketing teams":   "Growth-focused teams managing campaigns and content",
        "hr teams":          "People ops teams handling recruitment and employee lifecycle",
        "teachers":          "Educators creating and delivering instructional content",
        "students":          "Learners consuming structured educational content",
        "e-commerce sellers":"Online merchants managing products, orders, and inventory",
        "project managers":  "Professionals overseeing timelines, tasks, and resources",
    }

    for profile in raw_profiles:
        key   = profile.lower()
        descr = _profile_details.get(key, f"{profile.capitalize()} looking for a better workflow")
        profiles.append({"type": profile, "description": descr})

    # Ajouter admin si produit multi-utilisateurs
    if project_type in ("saas", "marketplace", "dashboard") and len(profiles) < 3:
        profiles.append({
            "type":        "admin",
            "description": "Platform administrator managing users, settings, and monitoring"
        })

    return profiles


def _expand_monetization(monetization):
    """Explicite la stratégie de monétisation."""
    _notes = {
        "subscription (monthly/yearly)": "Monthly and yearly plans. Yearly discount (~20%). Free trial recommended.",
        "freemium → paid tiers":         "Free tier with limited usage. Paid plans unlock advanced features.",
        "commission / marketplace fee":  "Commission on each transaction (typically 5–15%). No subscription needed.",
        "usage-based pricing":           "Pay per use (API calls, credits, seats). Scales with customer growth.",
        "one-time purchase":             "Single payment, lifetime access. Optional paid upgrades.",
        "advertising":                   "Free product monetized through contextually relevant advertising.",
    }
    return _notes.get(monetization, monetization)


def _build_context(project_type, project_name):
    """Génère une phrase de contexte selon le type de projet."""
    _contexts = {
        "saas":        f"{project_name} addresses a recurring workflow pain point and is delivered as a cloud-based subscription service.",
        "app":         f"{project_name} is a web application designed to solve a specific problem for its target users.",
        "marketplace": f"{project_name} creates value by connecting two sides of a market and facilitating transactions.",
        "tool":        f"{project_name} is a focused utility designed to be integrated into existing developer or power-user workflows.",
        "dashboard":   f"{project_name} centralizes data visibility and supports decision-making through clear metrics.",
        "api":         f"{project_name} exposes a programmable interface allowing third-party integration and automation.",
        "site":        f"{project_name} serves as the primary web presence and conversion surface for the product or brand.",
    }
    return _contexts.get(project_type, f"{project_name} is designed to serve its target users effectively.")


# ── Assemblage du résultat standardisé ───────────────────────────────────────

def _assemble_result(status, cdc, meta):
    """Construit le retour standardisé. Compatible futur brief.convert("cdc")."""
    return {
        "status": status,
        "from":   "brief",
        "to":     "cdc",
        "data":   {"cdc": cdc} if cdc else {},
        "meta":   meta,
    }


def _step_record(name, ok, error=None):
    """Trace d'une étape pour meta["steps"]."""
    record = {"step": name, "status": "ok" if ok else "failure"}
    if error:
        record["error"] = error
    return record


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    cases = [
        {
            "label": "✓ SaaS freelance invoicing",
            "input": {
                "brief": {
                    "project_name":  "Freelancers Invoices Payments",
                    "project_type":  "saas",
                    "description":   "A SaaS that helps freelancers track invoices and payments",
                    "target_users":  "freelancers",
                    "core_features": [
                        "Invoice creation and management",
                        "Payment tracking and status updates",
                        "Expense recording and categorization",
                        "Financial dashboard and reporting",
                        "Export to PDF / accounting formats",
                    ],
                    "constraints":   {
                        "tech": ["Responsive web (desktop-first)", "API-first architecture"],
                        "ux":   ["Onboarding in < 5 min", "Contextual help / tooltips"],
                    },
                    "monetization":  "subscription (monthly/yearly)",
                    "priority":      "high",
                },
            },
        },
        {
            "label": "✓ Marketplace designers",
            "input": {
                "brief": {
                    "project_name":  "Designers Clients Branding",
                    "project_type":  "marketplace",
                    "description":   "A marketplace that connects designers with clients",
                    "target_users":  "designers, small businesses",
                    "core_features": [
                        "Seller and buyer profile management",
                        "Service listing and search",
                        "Booking or order flow",
                        "Review and rating system",
                        "Commission and payment processing",
                    ],
                    "constraints":   {"tech": [], "ux": []},
                    "monetization":  "commission / marketplace fee",
                    "priority":      "medium",
                },
            },
        },
        {
            "label": "✗ brief manquant",
            "input": {"brief": None},
        },
        {
            "label": "✗ input invalide",
            "input": "not a dict",
        },
    ]

    print("=" * 65)
    print("  scenario_brief_to_cdc — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{case['label']}")
        print(f"  status   : {r['status']}")
        print(f"  from→to  : {r['from']} → {r['to']}")
        print(f"  steps    : {[s['step'] + ':' + s['status'] for s in r['meta']['steps']]}")
        if ok:
            cdc = r["data"]["cdc"]
            print(f"  overview : {cdc['project_overview']['project_name']} ({cdc['project_overview']['project_type']})")
            print(f"  context  : {cdc['project_overview']['context'][:80]}")
            print(f"  objectives ({len(cdc['objectives'])}) : {cdc['objectives'][0][:60]}")
            print(f"  features  ({len(cdc['core_features'])}) : {cdc['core_features'][0]['name']} [{cdc['core_features'][0]['priority']}]")
            print(f"  flows     ({len(cdc['user_flows'])}) : {cdc['user_flows'][0][:60]}")
            print(f"  metrics   ({len(cdc['success_metrics'])}) : {cdc['success_metrics'][0]['name']}")
            print(f"  constraints tech:{len(cdc['constraints']['tech'])} ux:{len(cdc['constraints']['ux'])} business:{len(cdc['constraints']['business'])}")
            passed += 1
        else:
            print(f"  errors   : {r['meta']['errors']}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed ({failed} failures intentionnelles)")
    print("=" * 65)
