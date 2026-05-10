"""
brief_team_orchestrator v0.1.0
Module EURKAI — maturation d'une idée en brief structuré par consultation d'agents experts.

Principe :
  idea → orchestrateur → agents experts → synthèse → brief structuré v0

Mode :
  "stub" (défaut) — agents déterministes, analyse textuelle, aucun LLM, aucune dépendance externe
  "real"          — identique stub en v0 (LLM à brancher ultérieurement comme plugin)

Agents :
  product_agent              — vision produit, fonctionnalités core, périmètre v0
  architecture_agent         — composants techniques, patterns, objets clés
  ux_design_agent            — parcours utilisateur, workflows, interfaces
  security_agent             — secrets, validation, audit trail
  performance_agent          — scalabilité, cache, modes d'exécution
  business_agent             — modèle économique, adoption, valeur métier
  validation_contracts_agent — invariants, contrats, triple validation

Usage :
  from modules.brief_team_orchestrator import run
  result = run("mon idée", mode="stub")
  # result["status"] == "success"
  # result["brief"]   == {project_name, vision, objective, ...}
  # result["reports"] == {agent_name: {recommendations, questions, risks, brief_additions}, ...}

Contrat de sortie :
  {
    "status":  "success" | "failure",
    "brief":   { ... },   # 13 sections garanties
    "reports": { agent_name: agent_output, ... },
    "meta":    { "steps": [...], "mode": str, "agents_called": [...] }
  }
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MANIFEST = {
    "name":        "brief_team_orchestrator",
    "version":     "0.1.0",
    "type":        "module",
    "layer":       "maturation",
    "mode":        "deterministic",
    "description": "Maturation d'une idée en brief structuré par équipe d'agents experts.",
    "inputs":      ["idea", "context", "mode"],
    "outputs":     ["brief", "reports", "meta"],
}

AGENT_NAMES = [
    "product_agent",
    "architecture_agent",
    "ux_design_agent",
    "security_agent",
    "performance_agent",
    "business_agent",
    "validation_contracts_agent",
]

_BRIEF_REQUIRED_FIELDS = [
    "project_name", "vision", "objective", "target_users",
    "core_capabilities", "expected_workflows", "key_objects",
    "key_scenarios", "constraints", "success_criteria",
    "open_questions", "scope_v0", "out_of_scope_v0",
]


# ── Entry point ────────────────────────────────────────────────────────────────

def run(idea, context=None, mode="stub", verbose=True):
    """
    idea    : str  — idée de projet en langage naturel (fr ou en)
    context : dict — contexte additionnel (project_name, domain, target_users, constraints…)
    mode    : "stub" | "real"
              stub → agents déterministes, aucun LLM
              real → identique stub en v0 (LLM à brancher ultérieurement)
    verbose : bool — logs de progression

    Retourne :
      status  — "success" | "failure"
      brief   — dict structuré (13 sections)
      reports — dict {agent_name: agent_output}
      meta    — {steps, mode, agents_called}
    """
    if not idea or not str(idea).strip():
        return _failure("idea_empty")

    idea    = str(idea).strip()
    context = context or {}
    meta    = {"steps": [], "mode": mode, "agents_called": []}

    if verbose:
        print(f"  [orchestrator] brief_team — idea: {idea[:80]}{'...' if len(idea) > 80 else ''}")
        print(f"  [orchestrator] mode: {mode}")

    # ── Étape 1 — Sélection des agents (v0 : tous) ────────────────────────────
    agents_to_call = _select_agents(idea, context)
    meta["agents_called"] = agents_to_call
    meta["steps"].append({"step": "select_agents", "count": len(agents_to_call)})

    # ── Étape 2 — Consultation des agents experts ─────────────────────────────
    reports = {}
    for agent_name in agents_to_call:
        report = _dispatch_agent(agent_name, idea, context, mode)
        reports[agent_name] = report
        meta["steps"].append({"step": f"consult_{agent_name}", "status": "ok"})
        if verbose:
            n_recs  = len(report["recommendations"])
            n_qs    = len(report["questions"])
            n_risks = len(report["risks"])
            print(f"  [agent]       {agent_name} — {n_recs} rec, {n_qs} questions, {n_risks} risks")

    # ── Étape 3 — Synthèse ────────────────────────────────────────────────────
    brief = _synthesis_agent(idea, reports, context, mode)
    meta["steps"].append({"step": "synthesis", "status": "ok"})

    if verbose:
        print(f"  [synthesis]   brief — {len(brief['core_capabilities'])} capabilities, "
              f"{len(brief['scope_v0'])} scope_v0, {len(brief['out_of_scope_v0'])} out_of_scope")

    return {
        "status":  "success",
        "brief":   brief,
        "reports": reports,
        "meta":    meta,
    }


# ── Orchestration ──────────────────────────────────────────────────────────────

def _select_agents(idea, context):
    """v0 : tous les agents systématiquement."""
    return list(AGENT_NAMES)


def _dispatch_agent(agent_name, idea, context, mode):
    _registry = {
        "product_agent":              _product_agent,
        "architecture_agent":         _architecture_agent,
        "ux_design_agent":            _ux_design_agent,
        "security_agent":             _security_agent,
        "performance_agent":          _performance_agent,
        "business_agent":             _business_agent,
        "validation_contracts_agent": _validation_contracts_agent,
    }
    fn = _registry.get(agent_name)
    if fn is None:
        return _empty_report(agent_name)
    return fn(idea, context, mode)


# ── Agents experts ─────────────────────────────────────────────────────────────
# Chaque agent : fn(idea, context, mode) → {agent, focus, recommendations, questions, risks, brief_additions}
# Tous déterministes : analyse lexicale de l'idée, aucun LLM.

def _product_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Définir la valeur métier principale livrée à l'utilisateur final",
        "Prioriser le périmètre v0 : 20% des features couvrent 80% des usages",
    ]
    questions = [
        "Quel est le problème n°1 que le projet résout pour l'utilisateur ?",
        "Quels sont les 3 scénarios d'usage les plus critiques en v0 ?",
        "Quelle est la métrique principale de succès du produit ?",
    ]
    risks = [
        "Scope creep : ajout de fonctionnalités non essentielles en v0",
        "Persona utilisateur non défini ou trop large",
    ]

    caps      = []
    scenarios = []
    scope     = []
    outscope  = []

    if _has(low, ["orchestrat", "pipeline", "chaîne", "chain"]):
        recs.append("Concevoir le pipeline de bout-en-bout testable dès v0")
        caps    += ["Orchestration de pipeline multi-étapes", "Chaînage de scénarios"]
        scope   += ["Orchestration des étapes principales (stub/skeleton)"]
        outscope += ["Parallélisation et optimisation des étapes"]

    if _has(low, ["idée", "idea", "brief", "matur"]):
        caps   += ["Transformation idée → brief structuré", "Maturation progressive de projet"]
        scope  += ["Scénario idée → brief fonctionnel"]
        scenarios.append("Saisie d'une idée → brief structuré produit")

    if _has(low, ["génér", "generat", "produit", "artefact", "create", "créat"]):
        caps.append("Génération automatique d'artefacts depuis une spécification")
        scenarios.append("Génération d'un artefact depuis un schéma")

    if _has(low, ["valid", "test", "contrat", "contract"]):
        caps   += ["Validation de conformité des objets", "Tests automatisés de contrats"]
        scenarios.append("Validation d'un objet contre son schéma")

    if _has(low, ["catalog", "catalogue", "registre", "registry"]):
        caps.append("Catalogue centralisé avec recherche et filtrage")
        scope.append("Catalogue des objets essentiels")

    if _has(low, ["ecosyst", "plateforme", "platform", "system", "système"]):
        recs.append("Définir les acteurs et leurs rôles dans l'écosystème")
        questions.append("Qui sont les utilisateurs primaires vs secondaires ?")
        risks.append("Périmètre trop large pour une v0 viable")
        outscope += ["Multi-tenant", "API publique externe", "Marketplace tiers"]

    if _has(low, ["objet", "object", "schema", "fractal"]):
        caps.append("Modèle objet unifié (tout est objet)")
        scope.append("Objets essentiels et leurs schémas définis")

    if _has(low, ["deploy", "déploi", "prod", "livr"]):
        scenarios.append("Déploiement d'un livrable en pré-production")
        outscope.append("Infrastructure de déploiement automatisée (v1+)")

    if _has(low, ["plugin", "extend", "modular"]):
        recs.append("Prévoir un point d'extension (plugin) sans l'implémenter en v0")
        outscope.append("Système de plugins tiers")

    if not caps:
        caps = ["Traitement d'une entrée en artefact exploitable"]
    if not scenarios:
        scenarios = [
            "Création d'un projet depuis une idée",
            "Validation de conformité d'un objet",
            "Génération d'artefact depuis un schéma",
        ]
    if not scope:
        scope = ["Pipeline de base bout-en-bout fonctionnel"]
    if not outscope:
        outscope = ["Optimisation avancée", "Fonctionnalités secondaires non core"]

    return {
        "agent":           "product_agent",
        "focus":           "Vision produit, fonctionnalités core, périmètre v0",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "core_capabilities": caps,
            "key_scenarios":     scenarios,
            "scope_v0":          scope,
            "out_of_scope_v0":   outscope,
        },
    }


def _architecture_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Architecture modulaire avec interfaces claires entre composants",
        "Définir les objets de domaine avant l'architecture technique",
        "Chaque module expose un seul point d'entrée run() standardisé",
    ]
    questions = [
        "Quel est le modèle de persistance retenu (fichiers JSON, base de données, in-memory) ?",
        "Comment les modules communiquent-ils (appel direct, message bus, API REST) ?",
        "Quelle est la stratégie de déploiement cible (local, cloud, conteneur) ?",
    ]
    risks = [
        "Couplage fort entre runtime et catalog",
        "Dépendances circulaires entre modules",
    ]

    key_objects = ["Object", "Schema", "Rule", "History"]
    workflows   = []
    constraints = ["Architecture modulaire obligatoire", "Interfaces claires entre composants"]

    if _has(low, ["fractal", "hiérarchi", "hierarch", "objet père", "père"]):
        recs.append("Définir la hiérarchie d'objets (Object > Schema > Rule > History)")
        key_objects += ["Catalog", "Registry"]

    if _has(low, ["catalog", "catalogue"]):
        recs.append("Catalog comme source de vérité unique — lecture/écriture via CatalogStorage")
        key_objects.append("CatalogStorage")
        risks.append("Catalog monolithique difficile à maintenir à grande échelle")
        workflows.append("Chargement catalog → résolution des dépendances → exécution scénario")

    if _has(low, ["agent", "orchest"]):
        recs.append("Séparer orchestration (scénarios) de l'exécution (agents)")
        key_objects += ["Scenario", "Agent", "Orchestrator"]
        workflows.append("Orchestrateur reçoit input → dispatche aux agents → agrège résultats")

    if _has(low, ["mrg", "scan", "super_execute", "super_validate", "super_render"]):
        recs.append("MRG pattern : scan_and_do, super_execute, super_validate, super_render")
        key_objects += ["MRG", "ScanContext"]
        workflows.append("scan_and_do → super_execute → super_validate → super_render")

    if _has(low, ["skeleton", "stub", "mode"]):
        recs.append("Modes d'exécution distincts dès v0 : real / stub / skeleton")
        constraints.append("Mode skeleton : aucun appel LLM, sorties minimales garanties")

    if _has(low, ["plugin", "hook", "extend"]):
        recs.append("Hooks before/after sur les méthodes MRG pour extensibilité")
        key_objects.append("Hook")
        risks.append("Architecture hooks peut complexifier le débogage")

    if not workflows:
        workflows = ["Entrée → validation → traitement → assemblage résultat → retour standardisé"]

    return {
        "agent":           "architecture_agent",
        "focus":           "Architecture technique, composants, patterns",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "key_objects":       key_objects,
            "expected_workflows": workflows,
            "constraints":        constraints,
        },
    }


def _ux_design_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Identifier les parcours utilisateur principaux avant de designer les interfaces",
        "Priorité lisibilité des logs et messages d'erreur — utilisateurs techniques en v0",
    ]
    questions = [
        "Quel est le point d'entrée principal : CLI, API REST, interface web, SDK ?",
        "Comment l'utilisateur suit-il l'avancement d'un pipeline en cours ?",
        "Quels sont les cas d'erreur les plus fréquents et comment sont-ils présentés ?",
    ]
    risks = [
        "Interface trop technique pour les utilisateurs non-développeurs",
        "Absence de feedback visuel sur l'état du pipeline",
        "Développer une UI en v0 détourne des ressources du core fonctionnel",
    ]

    workflows    = []
    target_users = []

    if _has(low, ["idée", "idea", "brief"]):
        workflows.append("Utilisateur saisit une idée → système génère un brief → utilisateur valide/affine")

    if _has(low, ["cdc", "cahier", "specs", "spec"]):
        workflows.append("Utilisateur soumet un brief → système génère un CDC → itération")

    if _has(low, ["orchest", "pipeline", "chaîne", "chain", "étape"]):
        workflows.append("Vue progression : idea → brief → CDC → specs → MVP")
        recs.append("Visualiser clairement les étapes et leur statut (ok / partial / error)")

    if _has(low, ["cli", "terminal", "console", "script"]):
        recs.append("CLI comme interface primaire avec sortie structurée (JSON/YAML)")
        workflows.append("CLI : python run.py --idea '...' --mode stub → JSON résultat")
        target_users.append("Développeurs Python utilisant le CLI")

    if _has(low, ["web", "interface", "ui", "dashboard", "visualis"]):
        recs.append("Interface web comme surcouche optionnelle — hors scope v0")
        risks.append("UI web à ajouter en v1+ uniquement (plugin)")
        target_users.append("Utilisateurs non-techniques (v1+)")

    if _has(low, ["développeur", "developer", "dev", "code", "python"]):
        target_users.append("Développeurs Python")

    if _has(low, ["architect", "techni", "ingénieur", "engineer"]):
        target_users.append("Architectes logiciels")

    if _has(low, ["chef de projet", "product", "manager", "pm"]):
        target_users.append("Chefs de projet technique")

    if not target_users:
        target_users = ["Développeurs Python", "Architectes logiciels"]

    if not workflows:
        workflows = [
            "Utilisateur fournit une entrée → système produit un artefact → utilisateur valide",
            "CLI : python run.py <ident> <params> → résultat JSON ou fichier",
        ]

    return {
        "agent":           "ux_design_agent",
        "focus":           "Expérience utilisateur, parcours, interaction",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "expected_workflows": workflows,
            "target_users":       target_users,
        },
    }


def _security_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Ne jamais stocker de clés API en clair dans le code source",
        "Valider toutes les entrées externes avant traitement (schema-first)",
    ]
    questions = [
        "Qui peut écrire dans le catalog ? Quels contrôles d'accès en v0 ?",
        "Comment les clés API LLM sont-elles gérées (env vars, vault) ?",
        "Quel niveau d'audit trail est requis (lecture seule, mutations, tout) ?",
    ]
    risks = [
        "Absence de validation des objets avant persistence",
        "Injection via prompts LLM si le code généré est exécuté directement",
    ]

    constraints = [
        "Aucune clé API en dur dans le code source",
        "Validation obligatoire de tout objet avant persistence",
    ]

    if _has(low, ["génér", "generat", "code"]):
        risks.append("Code généré non sandboxé exécuté dans le processus principal")
        constraints.append("Code généré traité comme artefact — jamais exécuté automatiquement")
        recs.append("Sandboxer l'exécution du code généré (subprocess, restrictions AST)")

    if _has(low, ["llm", "ia", "ai", "claude", "gpt", "anthropic", "openai"]):
        recs.append("Clés API LLM gérées via variables d'environnement ou fichier .env non versionné")
        risks.append("Fuite de données sensibles dans les prompts LLM")
        constraints.append("Aucun envoi de données sensibles aux LLM sans consentement explicite")

    if _has(low, ["api", "rest", "endpoint", "http", "web"]):
        recs.append("Authentification sur tous les endpoints API dès v0 (même interne)")
        risks.append("API exposée sans authentification en mode développement")

    if _has(low, ["history", "audit", "log", "trace"]):
        recs.append("Audit trail complet sur les mutations de catalog et d'objets")
        constraints.append("History log immuable — pas de suppression sans marquage")

    if _has(low, ["multi", "collaborat", "partag", "shared"]):
        risks.append("Absence de contrôle d'accès en mode multi-utilisateurs")
        recs.append("Définir la politique d'isolation des namespaces en v0")

    return {
        "agent":           "security_agent",
        "focus":           "Gestion des secrets, validation, audit trail",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "constraints": constraints,
        },
    }


def _performance_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Lazy loading du catalog : charger uniquement les objets nécessaires à l'exécution",
        "Pas d'optimisation prématurée en v0 — mesurer avant d'optimiser",
    ]
    questions = [
        "Quel est le volume attendu d'objets dans le catalog (dizaines, milliers, millions) ?",
        "Combien d'utilisateurs ou processus simultanés en v0 ?",
        "Quelles sont les opérations les plus fréquentes (lecture catalog, génération, validation) ?",
    ]
    risks = [
        "Catalog chargé entièrement en mémoire à chaque appel",
        "Absence de cache sur les requêtes fréquentes",
    ]

    constraints = [
        "v0 : performance non prioritaire, mesure avant optimisation",
    ]

    if _has(low, ["skeleton", "stub", "mode", "mock"]):
        recs.append("Mode skeleton/stub pour tester sans overhead LLM dès v0")
        recs.append("Benchmark du pipeline en mode stub avant activation LLM")
        constraints.append("Mode skeleton obligatoire pour les tests unitaires et CI")

    if _has(low, ["cache", "memoize", "hash", "requête", "query"]):
        recs.append("Cache des résultats de requêtes catalog (hash criteria, invalidation after_write)")
        risks.append("Invalidation de cache manquée → résultats obsolètes")

    if _has(low, ["scale", "volume", "million", "concurrent", "parallèle", "distribué"]):
        recs.append("Définir les SLA de performance dès v0 (P50, P99 latence)")
        risks.append("Architecture single-process limitante à fort volume — prévoir migration")

    if _has(low, ["async", "asynchron", "worker", "queue"]):
        recs.append("Synchrone en v0, asynchrone uniquement si mesuré nécessaire")
        constraints.append("Pas d'async/await en v0 — simple, synchrone, testable")

    if _has(low, ["llm", "ia", "claude", "gpt"]):
        recs.append("Comptabiliser et logguer les tokens LLM utilisés (usage) dès v0")
        risks.append("Coût LLM non borné si aucun budget de tokens n'est défini")

    return {
        "agent":           "performance_agent",
        "focus":           "Performance, scalabilité, gestion mémoire",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "constraints": constraints,
        },
    }


def _business_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Définir le périmètre v0 avec une définition du succès claire et mesurable",
        "Identifier les early adopters et obtenir du feedback dès la première version fonctionnelle",
    ]
    questions = [
        "Quel est le modèle économique visé (outil interne, SaaS, open-source) ?",
        "Qui sont les parties prenantes clés et leur niveau d'implication ?",
        "Quel est l'horizon de temps pour une v0 utilisable par un utilisateur externe ?",
    ]
    risks = [
        "Développer trop de fonctionnalités avant le premier retour utilisateur réel",
        "Absence de définition du succès pour la v0",
    ]

    success_criteria = []

    if _has(low, ["interne", "internal", "outil", "tool", "studio"]):
        recs.append("Valider l'adoption interne avant d'envisager une commercialisation")
        risks.append("Outil interne non adopté par les utilisateurs cibles sans onboarding")
        success_criteria.append("Au moins 3 utilisateurs internes validant le pipeline de bout en bout")

    if _has(low, ["agency", "lab", "library", "bibliothèque", "blog"]):
        recs.append("Définir le rôle de chaque structure (Agency/Lab/Library/Blog) dans l'écosystème")
        questions.append("Comment Agency/Lab/Library/Blog interagissent-ils avec le pipeline core ?")
        success_criteria.append("Structures Agency/Lab/Library/Blog définies et navigables en v0")

    if _has(low, ["plugin", "extend", "marketplace", "tiers"]):
        risks.append("Écosystème de plugins complexe à gouverner sans standard établi")
        recs.append("Définir le contrat d'extension avant d'ouvrir aux plugins tiers")

    if _has(low, ["open", "open-source", "communauté", "community", "github"]):
        recs.append("Documentation externe suffisante pour onboarding sans support direct")
        questions.append("Licence open-source choisie (MIT, Apache, LGPL) ?")
        success_criteria.append("README et documentation permettant un onboarding autonome")

    if _has(low, ["autonome", "autonomous", "auto", "automat"]):
        recs.append("Démontrer l'autonomie du système sur au moins un scénario complet dès v0")
        success_criteria.append("Au moins un scénario end-to-end sans intervention humaine")

    if not success_criteria:
        success_criteria = [
            "Pipeline de base (idée → artefact) fonctionnel en mode stub",
            "Au moins 3 scénarios end-to-end testables",
        ]

    success_criteria.append("Documentation suffisante pour un onboarding externe sans support")

    return {
        "agent":           "business_agent",
        "focus":           "Modèle économique, adoption, valeur métier",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "success_criteria": success_criteria,
        },
    }


def _validation_contracts_agent(idea, context, mode):
    low = idea.lower()

    recs = [
        "Définir les invariants et contrats de chaque objet dès v0",
        "Triple validation : L1 (type/structure), L2 (règles métier), L3 (cohérence globale)",
        "Chaque scénario remplit 100% de ses contrats ou échoue explicitement — pas de demi-état",
    ]
    questions = [
        "Quels sont les invariants non négociables du système (champs obligatoires, unicité, etc.) ?",
        "Comment les erreurs de validation sont-elles communiquées à l'utilisateur ?",
        "Quelle est la politique de retry en cas d'échec de validation (0, 1, N fois) ?",
    ]
    risks = [
        "Validation trop stricte bloquant la progression en v0 (erreur sur champ optionnel)",
        "Validation insuffisante laissant persister des objets malformés",
        "Absence d'historique des validations (audit trail incomplet)",
    ]

    success_criteria = [
        "100% des contrats de scénarios remplis ou échec explicite documenté",
        "Validation L1+L2+L3 opérationnelle sur les objets essentiels",
    ]
    constraints = []

    if _has(low, ["schema", "rule", "règle", "contrat", "contract"]):
        recs.append("Schema-first : tout objet validé contre son schéma avant usage ou persistence")
        constraints.append("Schema-first : validation obligatoire avant toute écriture")

    if _has(low, ["history", "audit", "log", "trace"]):
        recs.append("Logger 100% des actions MRG dans History (action, déclencheur, résultat, justification)")
        success_criteria.append("History log complet sur toutes les actions MRG")
        constraints.append("History log immuable — mutations tracées systématiquement")

    if _has(low, ["100%", "complet", "pur", "pure", "minimal"]):
        recs.append("Marquer les contrats non implémentés NOT_IMPLEMENTED — jamais de silence")
        constraints.append("Aucun contrat ignoré silencieusement — NOT_IMPLEMENTED ou erreur explicite")

    if _has(low, ["skeleton", "stub", "mode"]):
        recs.append("Mode skeleton : contrats de structure respectés même sans logique métier")
        success_criteria.append("Mode skeleton/stub passe les tests de contrats de base")

    if not constraints:
        constraints = ["Triple validation obligatoire sur les objets persistés"]

    return {
        "agent":           "validation_contracts_agent",
        "focus":           "Invariants, contrats, triple validation, audit trail",
        "recommendations": recs,
        "questions":       questions,
        "risks":           risks,
        "brief_additions": {
            "success_criteria": success_criteria,
            "constraints":       constraints,
        },
    }


# ── Synthèse ───────────────────────────────────────────────────────────────────

def _synthesis_agent(idea, reports, context, mode):
    """
    Agrège les brief_additions de tous les agents et produit le brief structuré final.
    Garantit la présence de toutes les sections — aucun champ vide.
    """
    low     = idea.lower()
    merged  = _merge_additions(reports)
    sentences = [s.strip() for s in re.split(r'[.!?\n]', idea) if len(s.strip()) > 10]

    project_name = _extract_project_name(idea, context)
    vision       = _extract_vision(sentences, idea)
    objective    = _extract_objective(sentences, idea, low)

    target_users = _deduplicate(merged.get("target_users", []))
    if not target_users:
        target_users = _infer_target_users(low)

    core_capabilities = _deduplicate(merged.get("core_capabilities", []))
    if not core_capabilities:
        core_capabilities = ["Traitement d'une entrée en artefact exploitable"]

    expected_workflows = _deduplicate(merged.get("expected_workflows", []))
    if not expected_workflows:
        expected_workflows = ["Entrée → validation → traitement → assemblage → retour standardisé"]

    key_objects = _deduplicate(merged.get("key_objects", []))
    if not key_objects:
        key_objects = _infer_key_objects(low)

    key_scenarios = _deduplicate(merged.get("key_scenarios", []))
    if not key_scenarios:
        key_scenarios = ["Création de projet depuis une idée", "Validation de conformité d'un objet"]

    constraints = _deduplicate(merged.get("constraints", []))
    if not constraints:
        constraints = ["Architecture modulaire", "Aucune dépendance externe non justifiée"]

    success_criteria = _deduplicate(merged.get("success_criteria", []))
    if not success_criteria:
        success_criteria = ["Pipeline de base fonctionnel", "Tests unitaires verts"]

    # Open questions : agrégées de tous les agents, dédupliquées
    open_questions = []
    for report in reports.values():
        for q in report.get("questions", []):
            if q not in open_questions:
                open_questions.append(q)

    scope_v0 = _deduplicate(merged.get("scope_v0", []))
    if not scope_v0:
        scope_v0 = ["Pipeline de base fonctionnel", "Objets essentiels définis et validés"]

    out_of_scope_v0 = _deduplicate(merged.get("out_of_scope_v0", []))
    # Garanties de base toujours hors scope v0
    _standard_out = [
        "Optimisation avancée des performances",
        "Sécurité production (TLS, rate-limiting, RBAC complet)",
        "Interface graphique web (v1+)",
    ]
    for item in _standard_out:
        if item not in out_of_scope_v0:
            out_of_scope_v0.append(item)

    return {
        "project_name":      project_name,
        "vision":            vision,
        "objective":         objective,
        "target_users":      target_users,
        "core_capabilities": core_capabilities,
        "expected_workflows": expected_workflows,
        "key_objects":       key_objects,
        "key_scenarios":     key_scenarios,
        "constraints":       constraints,
        "success_criteria":  success_criteria,
        "open_questions":    open_questions,
        "scope_v0":          scope_v0,
        "out_of_scope_v0":   out_of_scope_v0,
    }


# ── Helpers extraction ─────────────────────────────────────────────────────────

def _extract_project_name(idea, context):
    if context.get("project_name"):
        return context["project_name"]
    # Identifiant ALL_CAPS (ex. EURKAI, MRG, GEV)
    caps = re.findall(r'\b[A-Z][A-Z0-9]{2,}\b', idea)
    if caps:
        return caps[0]
    # CamelCase (ex. EurkaiCore)
    camel = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', idea)
    if camel:
        return camel[0]
    # Premiers mots significatifs
    stopwords = {
        "est", "une", "son", "ses", "les", "des", "par", "qui", "que",
        "peut", "doit", "être", "elle", "lui", "nous", "vous", "ils",
        "the", "and", "for", "that", "this", "from", "with", "are", "its",
    }
    words = re.findall(r'\b[a-zA-Zàâéèêëîïôùûüç]{3,}\b', idea)
    meaningful = [w for w in words[:12] if w.lower() not in stopwords]
    if meaningful:
        return " ".join(meaningful[:2]).title()
    return "Projet"


def _extract_vision(sentences, idea):
    return sentences[0] if sentences else idea[:200]


def _extract_objective(sentences, idea, low):
    objective_kws = ["objectif", "but ", "vise", "permet", "transformer", "transform",
                     "aim", "goal", "purpose", "pour ", "afin"]
    for s in sentences:
        if any(kw in s.lower() for kw in objective_kws):
            return s.strip()
    return sentences[1].strip() if len(sentences) > 1 else sentences[0].strip() if sentences else idea[:200]


def _infer_target_users(low):
    users = []
    if _has(low, ["développeur", "developer", "dev", "python", "code"]):
        users.append("Développeurs Python")
    if _has(low, ["architect", "techni", "ingénieur", "engineer"]):
        users.append("Architectes logiciels")
    if _has(low, ["chef de projet", "product manager", "pm "]):
        users.append("Chefs de projet technique")
    if _has(low, ["équipe", "team", "entreprise", "company"]):
        users.append("Équipes de développement")
    return users or ["Développeurs", "Équipes techniques"]


def _infer_key_objects(low):
    objects = []
    kw_map = [
        (["objet", "object"],                  "Object (père de tous les objets)"),
        (["schema"],                            "Schema"),
        (["rule", "règle"],                     "Rule"),
        (["history", "historique"],             "History"),
        (["scenario", "scénario"],              "Scenario"),
        (["catalog", "catalogue"],              "Catalog"),
        (["agent"],                             "Agent"),
        (["placeholder", "format", "template"], "Format / Placeholder"),
    ]
    for terms, label in kw_map:
        if _has(low, terms):
            objects.append(label)
    return objects or ["Object", "Schema", "Rule"]


def _merge_additions(reports):
    merged = {}
    for report in reports.values():
        for key, value in report.get("brief_additions", {}).items():
            if isinstance(value, list):
                merged.setdefault(key, [])
                merged[key].extend(value)
            elif isinstance(value, str) and key not in merged:
                merged[key] = value
    return merged


def _deduplicate(lst):
    seen, result = set(), []
    for item in lst:
        key = item.lower() if isinstance(item, str) else str(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _has(text_lower, terms):
    return any(t in text_lower for t in terms)


def _empty_report(agent_name):
    return {
        "agent":           agent_name,
        "focus":           "unknown",
        "recommendations": [],
        "questions":       [],
        "risks":           [],
        "brief_additions": {},
    }


def _failure(reason):
    return {
        "status":  "failure",
        "brief":   None,
        "reports": {},
        "meta":    {"error": reason, "steps": [], "mode": None, "agents_called": []},
    }
