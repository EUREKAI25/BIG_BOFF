"""
test_full_chain_e2e.py
Tests e2e de la chaîne complète EURKAI :

  idea → brief → cdc → specs → deliverable → preprod → prod → backup → github

3 cas testés :
  CAS 1 — SaaS/code  : API factures, deliverable_type=code
  CAS 2 — content    : série d'articles, deliverable_type=content
  CAS 3 — invalid    : échec propre sans crash global

Invariants vérifiés sur chaque scénario :
  - champs minimums {status, from, to, data, meta}
  - transitions from→to correctes
  - champs data principaux non vides

Usage :
  python tests/test_full_chain_e2e.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.scenario_idea_to_brief        import run as idea_to_brief
from scenarios.scenario_brief_to_cdc         import run as brief_to_cdc
from scenarios.scenario_cdc_to_specs         import run as cdc_to_specs
from scenarios.scenario_specs_to_deliverable import run as specs_to_deliverable
from scenarios.scenario_deliverable_to_preprod import run as deliverable_to_preprod
from scenarios.scenario_preprod_to_prod      import run as preprod_to_prod
from scenarios.scenario_prod_to_backup       import run as prod_to_backup
from scenarios.scenario_prod_to_github       import run as prod_to_github

VALID_STATUSES = {"success", "partial", "failure"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _assert(condition, label, details=""):
    if not condition:
        raise AssertionError(f"FAIL — {label}" + (f" : {details}" if details else ""))


def _check_envelope(result, expected_from, expected_to, label):
    _assert(isinstance(result, dict),                       f"{label} — result is dict")
    _assert("status" in result,                             f"{label} — has 'status'")
    _assert(result["status"] in VALID_STATUSES,             f"{label} — status valid", result["status"])
    _assert("from" in result,                               f"{label} — has 'from'")
    _assert("to"   in result,                               f"{label} — has 'to'")
    _assert("data" in result,                               f"{label} — has 'data'")
    _assert("meta" in result,                               f"{label} — has 'meta'")
    _assert(result["from"] == expected_from,                f"{label} — from={expected_from}", result.get("from"))
    _assert(result["to"]   == expected_to,                  f"{label} — to={expected_to}",   result.get("to"))
    _assert(isinstance(result["meta"].get("steps"), list),  f"{label} — meta.steps is list")
    _assert(isinstance(result["meta"].get("errors"), list), f"{label} — meta.errors is list")


def _run_full_chain(idea_text, tmpdir, verbose=False):
    results = {}

    r1 = idea_to_brief({"idea": idea_text}, verbose=verbose)
    results["idea_to_brief"] = r1
    brief = r1.get("data", {}).get("brief", {})

    r2 = brief_to_cdc({"brief": brief}, verbose=verbose)
    results["brief_to_cdc"] = r2
    cdc = r2.get("data", {}).get("cdc", {})

    r3 = cdc_to_specs({"cdc": cdc}, verbose=verbose)
    results["cdc_to_specs"] = r3
    specs = r3.get("data", {}).get("specs", {})

    r4 = specs_to_deliverable({"specs": specs}, verbose=verbose)
    results["specs_to_deliverable"] = r4
    dtype       = r4.get("data", {}).get("deliverable_type", "code")
    deliverable = r4.get("data", {}).get("deliverable", {})

    r5 = deliverable_to_preprod(
        {"deliverable_type": dtype, "deliverable": deliverable},
        base_path=Path(tmpdir), verbose=verbose,
    )
    results["deliverable_to_preprod"] = r5
    preprod = r5.get("data", {}).get("preprod_env", {})

    r6 = preprod_to_prod({"preprod_env": preprod}, verbose=verbose)
    results["preprod_to_prod"] = r6
    prod = r6.get("data", {}).get("prod_env", {})

    r7 = prod_to_backup({"prod_env": prod}, verbose=verbose)
    results["prod_to_backup"] = r7

    r8 = prod_to_github({"prod_env": prod}, verbose=verbose)
    results["prod_to_github"] = r8

    return results


# ── CAS 1 — SaaS / code ───────────────────────────────────────────────────────

def test_case_1_saas_code():
    idea = "Créer une API de gestion de factures avec authentification"

    with tempfile.TemporaryDirectory(prefix="eurkai_e2e_") as tmp:
        results = _run_full_chain(idea, tmp)

    _check_envelope(results["idea_to_brief"],        "idea",        "brief",      "CAS1/idea_to_brief")
    _check_envelope(results["brief_to_cdc"],         "brief",       "cdc",        "CAS1/brief_to_cdc")
    _check_envelope(results["cdc_to_specs"],         "cdc",         "specs",      "CAS1/cdc_to_specs")
    _check_envelope(results["specs_to_deliverable"], "specs",       "deliverable","CAS1/specs_to_deliverable")
    _check_envelope(results["deliverable_to_preprod"],"deliverable","preprod",    "CAS1/deliverable_to_preprod")
    _check_envelope(results["preprod_to_prod"],      "preprod",     "prod",       "CAS1/preprod_to_prod")
    _check_envelope(results["prod_to_backup"],       "prod",        "backup",     "CAS1/prod_to_backup")
    _check_envelope(results["prod_to_github"],       "prod",        "github",     "CAS1/prod_to_github")

    for step, r in results.items():
        _assert(r["status"] in ("success", "partial"),
                f"CAS1/{step} — not failure", r["status"])

    _assert(results["idea_to_brief"]["data"].get("brief"),  "CAS1 — brief not empty")
    _assert(results["brief_to_cdc"]["data"].get("cdc"),     "CAS1 — cdc not empty")
    _assert(results["cdc_to_specs"]["data"].get("specs"),   "CAS1 — specs not empty")

    dtype = results["specs_to_deliverable"]["data"].get("deliverable_type")
    _assert(dtype == "code", "CAS1 — deliverable_type=code", dtype)

    preprod = results["deliverable_to_preprod"]["data"].get("preprod_env", {})
    _assert(preprod.get("files"), "CAS1 — preprod has files")

    prod = results["preprod_to_prod"]["data"].get("prod_env", {})
    _assert(prod.get("prod_path"),        "CAS1 — prod_path set")
    _assert(prod.get("release_manifest"), "CAS1 — release_manifest set")
    _assert(prod.get("deployment_plan"),  "CAS1 — deployment_plan set")

    backup = results["prod_to_backup"]["data"].get("backup_env", {})
    _assert(backup.get("backup_path"),  "CAS1 — backup_path set")
    _assert(backup.get("restore_plan"), "CAS1 — restore_plan set")

    github = results["prod_to_github"]["data"].get("github_env", {})
    _assert(github.get("repo_name"),      "CAS1 — repo_name set")
    _assert(github.get("commit_message"), "CAS1 — commit_message set")
    _assert(github.get("ready") is True,  "CAS1 — github ready=True")


# ── CAS 2 — Content ───────────────────────────────────────────────────────────

def test_case_2_content():
    idea = "Créer une série de 5 articles de blog sur la productivité"

    with tempfile.TemporaryDirectory(prefix="eurkai_e2e_content_") as tmp:
        results = _run_full_chain(idea, tmp)

    _check_envelope(results["idea_to_brief"],        "idea",        "brief",      "CAS2/idea_to_brief")
    _check_envelope(results["brief_to_cdc"],         "brief",       "cdc",        "CAS2/brief_to_cdc")
    _check_envelope(results["cdc_to_specs"],         "cdc",         "specs",      "CAS2/cdc_to_specs")
    _check_envelope(results["specs_to_deliverable"], "specs",       "deliverable","CAS2/specs_to_deliverable")
    _check_envelope(results["deliverable_to_preprod"],"deliverable","preprod",    "CAS2/deliverable_to_preprod")
    _check_envelope(results["preprod_to_prod"],      "preprod",     "prod",       "CAS2/preprod_to_prod")
    _check_envelope(results["prod_to_backup"],       "prod",        "backup",     "CAS2/prod_to_backup")
    _check_envelope(results["prod_to_github"],       "prod",        "github",     "CAS2/prod_to_github")

    for step, r in results.items():
        _assert(r["status"] in VALID_STATUSES,
                f"CAS2/{step} — status valid", r["status"])

    dtype = results["specs_to_deliverable"]["data"].get("deliverable_type")
    _assert(dtype == "content", "CAS2 — deliverable_type=content", dtype)

    _assert(results["idea_to_brief"]["data"].get("brief", {}).get("project_name"),
            "CAS2 — project_name set")


# ── CAS 3 — Input invalide ────────────────────────────────────────────────────

def test_case_3_invalid_input():
    r = idea_to_brief("not a dict", verbose=False)
    _check_envelope(r, "idea", "brief", "CAS3/idea_to_brief invalid")
    _assert(r["status"] == "failure", "CAS3/idea_to_brief — failure")

    r = brief_to_cdc({}, verbose=False)
    _check_envelope(r, "brief", "cdc", "CAS3/brief_to_cdc empty")
    _assert(r["status"] in ("failure", "partial"), "CAS3/brief_to_cdc")

    r = specs_to_deliverable({"specs": {}}, verbose=False)
    _check_envelope(r, "specs", "deliverable", "CAS3/specs_to_deliverable empty")
    _assert(r["status"] in VALID_STATUSES, "CAS3/specs_to_deliverable")

    r = deliverable_to_preprod({"deliverable": {}}, verbose=False)
    _check_envelope(r, "deliverable", "preprod", "CAS3/deliverable_to_preprod")
    _assert(r["status"] == "failure", "CAS3/deliverable_to_preprod — failure")

    r = preprod_to_prod({}, verbose=False)
    _check_envelope(r, "preprod", "prod", "CAS3/preprod_to_prod")
    _assert(r["status"] == "failure", "CAS3/preprod_to_prod — failure")

    r = prod_to_backup({}, verbose=False)
    _check_envelope(r, "prod", "backup", "CAS3/prod_to_backup")
    _assert(r["status"] == "failure", "CAS3/prod_to_backup — failure")

    r = prod_to_github({}, verbose=False)
    _check_envelope(r, "prod", "github", "CAS3/prod_to_github")
    _assert(r["status"] == "failure", "CAS3/prod_to_github — failure")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    passed = []
    failed = []

    print("=" * 65)
    print("  EURKAI — test_full_chain_e2e")
    print("=" * 65)

    print("\n[ CAS 1 ] API factures / code — chaîne complète")
    try:
        test_case_1_saas_code()
        print("  ✓ 8/8 étapes — tous invariants OK — deliverable_type=code")
        passed.append("CAS1 API/code")
    except AssertionError as e:
        print(f"  ✗ {e}")
        failed.append(f"CAS1 : {e}")

    print("\n[ CAS 2 ] Série d'articles / content")
    try:
        test_case_2_content()
        print("  ✓ 8/8 étapes — deliverable_type=content")
        passed.append("CAS2 content (dtype=content)")
    except AssertionError as e:
        print(f"  ✗ {e}")
        failed.append(f"CAS2 : {e}")

    print("\n[ CAS 3 ] Input invalide — échec propre")
    try:
        test_case_3_invalid_input()
        print("  ✓ 7 scénarios — tous échouent proprement")
        passed.append("CAS3 invalid input")
    except AssertionError as e:
        print(f"  ✗ {e}")
        failed.append(f"CAS3 : {e}")

    print(f"\n{'=' * 65}")
    print(f"  {len(passed)}/{len(passed)+len(failed)} passed")
    for p in passed:
        print(f"  ✓ {p}")
    for f in failed:
        print(f"  ✗ {f}")
    print("=" * 65)

    sys.exit(0 if not failed else 1)
