"""
agent_brief
Transforme une idée brute en BRIEF projet structuré.
Logique déterministe — LLM optionnel en fallback isolé.

Input  : {"idea": "create a SaaS that helps freelancers track invoices"}
Output : {"status": "success", "brief": {...}}

Champs du brief :
  project_name   — nom lisible du projet
  project_type   — SaaS | app | site | tool | api | unknown
  description    — phrase de présentation du projet
  target_users   — qui l'utilise
  core_features  — liste 3–5 fonctionnalités principales
  constraints    — contraintes tech/UX détectées ou par défaut
  monetization   — modèle économique inféré
  priority       — low | medium | high
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Signaux de détection ──────────────────────────────────────────────────────

_TYPE_SIGNALS = {
    "saas": [
        r"\bsaas\b", r"\bsubscription\b", r"\babonnement\b",
        r"\bmulti[- ]?tenant\b", r"\bcloud[- ]?based\b",
        r"\bplatform\b", r"\bplateforme\b", r"\bsuite\b",
    ],
    "app": [
        r"\bapp\b", r"\bapplication\b", r"\bmobile\b", r"\bios\b",
        r"\bandroid\b", r"\bpwa\b", r"\bweb app\b",
    ],
    "site": [
        r"\bwebsite\b", r"\bsite\b", r"\blanding\b", r"\bblog\b",
        r"\bportfolio\b", r"\bvitrine\b", r"\bshowcase\b",
    ],
    "tool": [
        r"\btool\b", r"\boutil\b", r"\bscript\b", r"\bautomation\b",
        r"\bautomatisation\b", r"\bcli\b", r"\bbot\b", r"\bplugin\b",
        r"\bextension\b", r"\bhelper\b",
    ],
    "api": [
        r"\bapi\b", r"\brest\b", r"\bwebhook\b", r"\bendpoint\b",
        r"\bservice\b", r"\bmicroservice\b",
    ],
    "marketplace": [
        r"\bmarketplace\b", r"\bplace de marché\b", r"\bcommission\b",
        r"\bbuyers?\b.*\bsellers?\b", r"\bconnect\b.*\bproviders?\b",
    ],
    "dashboard": [
        r"\bdashboard\b", r"\btableau de bord\b", r"\banalytics\b",
        r"\breporting\b", r"\bmonitoring\b", r"\bmetrics\b",
    ],
}

_DOMAIN_SIGNALS = {
    "finance": [
        r"invoices?", r"factures?", r"payments?", r"paiements?",
        r"\baccounting\b", r"comptabilit", r"\bbudget\b",
        r"expenses?", r"\brevenue\b", r"\btax\b", r"\btva\b",
    ],
    "productivity": [
        r"\btasks?\b", r"\btâches?\b", r"\bprojects?\b", r"\bprojets?\b",
        r"\bplanning\b", r"\bschedule\b", r"\bcalendar\b", r"\bagenda\b",
        r"time\s+track", r"track\s+time",
    ],
    "ecommerce": [
        r"\bshop\b", r"\bboutique\b", r"\bstore\b", r"\bmagasin\b",
        r"\bproducts?\b", r"\bproduits?\b", r"\bcart\b", r"\borders?\b",
    ],
    "hr": [
        r"\bhr\b", r"employees?", r"\bstaff\b", r"\bhiring\b",
        r"recruits?", r"\bpaie\b", r"onboarding",
    ],
    "education": [
        r"courses?\b", r"\blearn", r"\btraining\b", r"\blms\b",
        r"\bquiz\b", r"students?", r"teachers?", r"certif",
    ],
    "health": [
        r"\bhealth\b", r"\bsanté\b", r"\bmedical\b", r"patients?",
        r"\bfitness\b", r"\bwellness\b", r"\bdiet\b",
    ],
    "crm": [
        r"\bcrm\b", r"\bcustomer relationship\b", r"leads?\s+management",
        r"\bsales\s+pipeline\b", r"\bpipeline\b", r"deals?\s+track",
    ],
    "content": [
        r"\bcontent\b", r"\bcontenu\b", r"\bblog\b", r"\bcms\b",
        r"articles?", r"publish", r"\bnewsletter\b",
    ],
}

_USER_PROFILES = {
    "freelancers":       [r"freelancers?", r"indépendants?", r"consultants?"],
    "small businesses":  [r"\bsmb\b", r"small business", r"\bpme\b", r"startups?"],
    "developers":        [r"developers?", r"\bdevs?\b", r"programmers?", r"coders?", r"tech team"],
    "designers":         [r"designers?", r"\bcreatives?\b", r"agenc(y|ies)", r"\bagence\b"],
    "marketing teams":   [r"\bmarketing\b", r"\bgrowth\b", r"\bseo\b", r"content team"],
    "HR teams":          [r"\bhr\b", r"recruits?", r"hiring manager"],
    "teachers":          [r"teachers?", r"educators?", r"instructors?", r"trainers?"],
    "e-commerce sellers":[r"sellers?", r"vendors?", r"merchants?", r"shop owner"],
    "project managers":  [r"project managers?", r"\bpm\b", r"team leads?"],
    "students":          [r"students?", r"learners?", r"pupils?"],
}

_MONETIZATION_SIGNALS = {
    "freemium → paid tiers": [
        r"\bfreemium\b", r"\bfree.*premium\b", r"\btrial\b", r"\bfree plan\b",
    ],
    "subscription (monthly/yearly)": [
        r"\bsubscription\b", r"\babonnement\b", r"\brecurring\b", r"\bmonthly\b",
        r"\byearly\b", r"\bsaas\b",
    ],
    "commission / marketplace fee": [
        r"\bcommission\b", r"\bmarketplace\b", r"\bplace de marché\b", r"\btransaction fee\b",
    ],
    "one-time purchase": [
        r"\bone[- ]time\b", r"\blifetime\b", r"\bpay once\b",
    ],
    "usage-based pricing": [
        r"\bpay[- ]per[- ]use\b", r"\busage[- ]based\b", r"\bcredit\b", r"\bapi calls?\b",
    ],
    "advertising": [
        r"\bads\b", r"\badvertis\b", r"\bmonetize.*traffic\b",
    ],
}

_FEATURE_TEMPLATES = {
    "marketplace": [
        "Seller and buyer profile management",
        "Service / product listing and search",
        "Booking or order flow",
        "Review and rating system",
        "Commission and payment processing",
    ],
    "finance": [
        "Invoice creation and management",
        "Payment tracking and status updates",
        "Expense recording and categorization",
        "Financial dashboard and reporting",
        "Export to PDF / accounting formats",
    ],
    "productivity": [
        "Task and project management",
        "Time tracking per task",
        "Team collaboration and assignments",
        "Progress dashboard",
        "Notifications and reminders",
    ],
    "ecommerce": [
        "Product catalog management",
        "Shopping cart and checkout",
        "Order tracking",
        "Customer management",
        "Inventory alerts",
    ],
    "crm": [
        "Contact and lead management",
        "Sales pipeline visualization",
        "Activity log and follow-ups",
        "Email integration",
        "Reporting and conversion metrics",
    ],
    "hr": [
        "Employee directory and profiles",
        "Leave and absence management",
        "Onboarding workflow",
        "Performance reviews",
        "Payroll overview",
    ],
    "education": [
        "Course creation and publishing",
        "Student enrollment management",
        "Quiz and assessment engine",
        "Progress tracking",
        "Certification generation",
    ],
    "content": [
        "Content editor with rich text",
        "Media library",
        "Publishing schedule",
        "SEO metadata management",
        "Analytics per content piece",
    ],
}

_GENERIC_FEATURES = [
    "User authentication and account management",
    "Dashboard with key metrics",
    "Data import / export",
    "Notification system",
    "Settings and customization",
]

_CONSTRAINT_TEMPLATES = {
    "tech": {
        "saas":        ["Responsive web (desktop-first)", "API-first architecture", "Multi-tenant data isolation"],
        "app":         ["Mobile-first UI", "Offline support (PWA)", "Performance < 2s load"],
        "tool":        ["CLI-compatible", "Zero config default", "Single binary or pip install"],
        "api":         ["REST + JSON", "Auth via API key or OAuth2", "Rate limiting"],
        "dashboard":   ["Real-time data refresh", "Exportable charts", "Role-based access"],
        "marketplace": ["Two-sided user flows", "Secure payment processing", "Trust & review system"],
        "site":        ["SEO-optimized", "Fast load (< 1s)", "Accessibility WCAG 2.1"],
    },
    "ux": {
        "saas":        ["Onboarding in < 5 min", "Contextual help / tooltips", "Empty state guidance"],
        "app":         ["Gesture-friendly", "Clear error messages", "Progressive disclosure"],
        "tool":        ["Single command to start", "Clear output format", "Helpful error messages"],
        "dashboard":   ["Data readable at a glance", "Filter and search", "Printable view"],
        "site":        ["Clear CTA above fold", "Mobile-friendly navigation", "Readable typography"],
    },
}


# ── Entry point ───────────────────────────────────────────────────────────────

def run(input_data, model_type="deterministic", verbose=True, agent_ident="agent_brief"):
    """
    Transforme une idée en BRIEF structuré.

    input_data : dict avec clé "idea" (str)
    model_type : "deterministic" | "llm"

    Retourne :
        status — "success" | "failure"
        brief  — dict complet (ou None si failure)
    """
    idea = (input_data or {}).get("idea", "")
    if not idea or not idea.strip():
        return _failure("idea_empty")

    idea   = idea.strip()
    lower  = idea.lower()

    project_type  = _detect_type(lower)
    domain        = _detect_domain(lower)
    project_name  = _extract_name(lower, project_type, domain)
    description   = _build_description(idea, project_name, project_type, domain)
    target_users  = _detect_users(lower)
    core_features = _build_features(lower, domain, project_type)
    constraints   = _build_constraints(project_type)
    monetization  = _detect_monetization(lower, project_type)
    priority      = _score_priority(lower, project_type, domain)

    brief = {
        "project_name":  project_name,
        "project_type":  project_type,
        "description":   description,
        "target_users":  target_users,
        "core_features": core_features,
        "constraints":   constraints,
        "monetization":  monetization,
        "priority":      priority,
    }

    if verbose:
        print(f"  [agent]   {agent_ident} — {project_type}:{project_name}")
        print(f"  [OK]      domain:{domain} users:{target_users} priority:{priority}")

    return {"status": "success", "brief": brief}


# ── Détection du type ─────────────────────────────────────────────────────────

def _detect_type(lower):
    scores = {t: 0 for t in _TYPE_SIGNALS}
    for type_name, patterns in _TYPE_SIGNALS.items():
        for pat in patterns:
            if re.search(pat, lower):
                scores[type_name] += 1
    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else "tool"


# ── Détection du domaine ──────────────────────────────────────────────────────

def _detect_domain(lower):
    for domain, patterns in _DOMAIN_SIGNALS.items():
        for pat in patterns:
            if re.search(pat, lower):
                return domain
    return "generic"


# ── Extraction du nom ─────────────────────────────────────────────────────────

def _extract_name(lower, project_type, domain):
    """Extrait un nom de projet lisible depuis l'idée brute."""
    stopwords = {
        # articles / prépositions
        "a", "an", "the", "that", "this", "with", "for", "and", "or",
        "in", "on", "to", "of", "from", "is", "are", "be", "can", "will",
        "where", "which", "who", "how", "what", "looking",
        # verbes d'action (très courants dans les idées de projets)
        "create", "build", "make", "develop", "write", "add", "new", "simple",
        "help", "helps", "allow", "allows", "enable", "enables", "let", "lets",
        "manage", "manages", "track", "tracks", "connect", "connects",
        "automate", "automates", "publish", "publishes", "use", "using",
        "get", "set", "run", "find", "show", "send", "load", "save",
        # type de produit (déjà détectés)
        "saas", "app", "application", "website", "site", "tool", "platform",
        "service", "system", "solution", "api", "marketplace",
    }

    # Extraire tous les mots significatifs de l'idée complète
    words = re.findall(r"[a-zàâäéèêëîïôùûüç]+", lower)
    significant = [w for w in words if w not in stopwords and len(w) > 2]

    # Préférer les mots proches du début (après les verbes d'action)
    start = re.sub(
        r"^(create|build|make|develop|write|add|a|an|the|new|simple)\s+",
        "", lower
    ).strip()
    # Retirer la partie après "that/which/where" pour garder le sujet
    subject = re.sub(r"\s+(that|which|where|who)\s+.*", "", start).strip()
    subject_words = re.findall(r"[a-zàâäéèêëîïôùûüç]+", subject)
    subject_clean  = [w for w in subject_words if w not in stopwords and len(w) > 2]

    # Priorité : mots du sujet en premier, compléter avec mots du reste
    combined = subject_clean[:2]
    for w in significant:
        if w not in combined:
            combined.append(w)
        if len(combined) >= 3:
            break

    if combined:
        return " ".join(w.capitalize() for w in combined[:3])

    # Fallback : domain + type lisible
    _type_labels = {
        "saas": "Platform", "app": "App", "tool": "Tool",
        "api": "API", "marketplace": "Marketplace", "dashboard": "Dashboard", "site": "Site",
    }
    label = _type_labels.get(project_type, "Product")
    return f"{domain.capitalize()} {label}"


# ── Construction de la description ────────────────────────────────────────────

def _build_description(idea, project_name, project_type, domain):
    _prefixes = {
        "saas":        "A cloud platform",
        "app":         "A web application",
        "site":        "A website",
        "tool":        "A developer tool",
        "api":         "An API service",
        "marketplace": "A marketplace",
        "dashboard":   "A dashboard",
    }
    prefix = _prefixes.get(project_type, "A product")

    # Si l'idée est bien formée (> 25 chars et contient un verbe d'action), la réutiliser
    _action_verbs = r"\b(helps?|allows?|enables?|lets?|manages?|tracks?|automates?|connects?|provides?|offers?|gives?)\b"
    if len(idea) > 25 and re.search(_action_verbs, idea, re.I):
        trimmed = re.sub(r"^(create|build|make|develop|a|an)\s+", "", idea, flags=re.I).strip()
        return trimmed[0].upper() + trimmed[1:] if trimmed else f"{prefix} that handles {domain} workflows."

    # Fallback propre sans "generic"
    domain_part = f"{domain} " if domain != "generic" else ""
    return f"{prefix} that handles {domain_part}workflows."


# ── Détection des utilisateurs cibles ────────────────────────────────────────

def _detect_users(lower):
    found = []
    for profile, patterns in _USER_PROFILES.items():
        for pat in patterns:
            if re.search(pat, lower):
                found.append(profile)
                break
    if not found:
        return "professionals and teams"
    return ", ".join(found[:2])   # max 2 profils


# ── Construction des features ─────────────────────────────────────────────────

def _build_features(lower, domain, project_type):
    # Features depuis domain template (domain prioritaire, puis project_type comme fallback)
    domain_features = list(_FEATURE_TEMPLATES.get(domain) or _FEATURE_TEMPLATES.get(project_type, []))

    # Enrichissement par mots-clés dans l'idée
    extra = []
    if re.search(r"\bnotif\b|\balert\b|\breminder\b", lower):
        extra.append("Smart notifications and reminders")
    if re.search(r"\bexport\b|\breport\b|\bpdf\b", lower):
        extra.append("Export and reporting (PDF, CSV)")
    if re.search(r"\bteam\b|\bcollabor\b|\bshare\b", lower):
        extra.append("Team collaboration and sharing")
    if re.search(r"\bautom\b|\bauto\b|\bschedul\b", lower):
        extra.append("Automated workflows and scheduling")
    if re.search(r"\bintegrat\b|\bconnect\b|\bapi\b", lower):
        extra.append("Third-party integrations (API)")
    if re.search(r"\bmobile\b|\bpwa\b", lower):
        extra.append("Mobile-friendly / PWA")

    # Fusionner : domain d'abord, extra ensuite, compléter avec generic si besoin
    features = domain_features[:3] + extra[:2]
    if len(features) < 3:
        features += [f for f in _GENERIC_FEATURES if f not in features]
    return features[:5]


# ── Construction des contraintes ──────────────────────────────────────────────

def _build_constraints(project_type):
    tech = _CONSTRAINT_TEMPLATES["tech"].get(
        project_type,
        ["Web-based (responsive)", "Secure authentication", "REST API"]
    )
    ux = _CONSTRAINT_TEMPLATES["ux"].get(
        project_type,
        ["Intuitive onboarding", "Clear error messages", "Accessible UI"]
    )
    return {"tech": tech[:2], "ux": ux[:2]}


# ── Détection de la monétisation ──────────────────────────────────────────────

def _detect_monetization(lower, project_type):
    for model, patterns in _MONETIZATION_SIGNALS.items():
        for pat in patterns:
            if re.search(pat, lower):
                return model

    # Fallback par type
    _defaults = {
        "saas":        "subscription (monthly/yearly)",
        "marketplace": "commission / marketplace fee",
        "tool":        "freemium → paid tiers",
        "api":         "usage-based pricing",
        "site":        "advertising or sponsorship",
        "app":         "freemium → paid tiers",
        "dashboard":   "subscription (monthly/yearly)",
    }
    return _defaults.get(project_type, "freemium → paid tiers")


# ── Score de priorité ─────────────────────────────────────────────────────────

def _score_priority(lower, project_type, domain):
    score = 0

    # Type à forte valeur commerciale
    if project_type in ("saas", "marketplace"):
        score += 2
    elif project_type in ("app", "dashboard"):
        score += 1

    # Domaines à forte demande
    if domain in ("finance", "crm", "ecommerce"):
        score += 2
    elif domain in ("productivity", "hr", "education"):
        score += 1

    # Signaux d'urgence dans l'idée
    if re.search(r"\burgent\b|\basap\b|\bquickly\b|\bfast\b|\bcritical\b", lower):
        score += 2

    # Monétisation claire
    if re.search(r"\bsubscription\b|\bpay\b|\bcharge\b|\bmonetiz\b", lower):
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _failure(reason):
    return {"status": "failure", "brief": None, "reason": reason}


# ── Smoke test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    cases = [
        {
            "label": "SaaS freelance invoicing",
            "input": {"idea": "create a SaaS that helps freelancers track invoices and payments"},
        },
        {
            "label": "Marketplace designers / clients",
            "input": {"idea": "build a marketplace that connects designers with clients looking for branding services"},
        },
        {
            "label": "HR onboarding tool",
            "input": {"idea": "a tool for HR teams to automate employee onboarding workflows"},
        },
        {
            "label": "E-learning platform",
            "input": {"idea": "an e-learning platform where teachers can publish courses and track student progress"},
        },
        {
            "label": "Developer CLI tool",
            "input": {"idea": "cli tool to scaffold new Python projects with EURKAI structure"},
        },
        {
            "label": "Idée vide",
            "input": {"idea": ""},
        },
    ]

    print("=" * 65)
    print("  agent_brief — smoke test")
    print("=" * 65)

    passed = failed = 0
    for case in cases:
        r = run(case["input"], verbose=False)
        ok = r["status"] == "success"
        print(f"\n{'✓' if ok else '✗'} {case['label']}")
        if ok:
            b = r["brief"]
            print(f"  name         : {b['project_name']}")
            print(f"  type         : {b['project_type']}")
            print(f"  description  : {b['description'][:80]}")
            print(f"  users        : {b['target_users']}")
            print(f"  features     : {b['core_features'][:3]}")
            print(f"  monetization : {b['monetization']}")
            print(f"  priority     : {b['priority']}")
            passed += 1
        else:
            print(f"  reason       : {r.get('reason')}")
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  {passed}/{passed + failed} passed")
    print("=" * 65)
