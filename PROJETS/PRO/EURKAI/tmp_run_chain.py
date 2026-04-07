import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "CODE" / "eurkai_core"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scenarios.scenario_idea_to_brief       import run as scenario_idea_to_brief
from scenarios.scenario_brief_to_cdc        import run as scenario_brief_to_cdc
from scenarios.scenario_cdc_to_specs        import run as scenario_cdc_to_specs
from scenarios.scenario_specs_to_deliverable import run as scenario_specs_to_deliverable
from scenarios.scenario_deliverable_to_preprod import run as scenario_deliverable_to_preprod
from scenarios.scenario_preprod_to_prod     import run as scenario_preprod_to_prod
from scenarios.scenario_prod_to_backup      import run as scenario_prod_to_backup
from scenarios.scenario_prod_to_github      import run as scenario_prod_to_github


def run_step(func, data):
    try:
        result = func(data, verbose=False)
        return result
    except TypeError:
        try:
            result = func(data)
            return result
        except Exception as e:
            import traceback
            return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


input_data = {"idea": "Créer une API de gestion de factures avec authentification"}

print("=== EXECUTION EURKAI ===")

data = input_data

_tmpdir = tempfile.mkdtemp(prefix="eurkai_chain_")

# Étapes 1-6 : chaîne linéaire
linear_steps = [
    ("idea → brief",        scenario_idea_to_brief),
    ("brief → cdc",         scenario_brief_to_cdc),
    ("cdc → specs",         scenario_cdc_to_specs),
    ("specs → deliverable", scenario_specs_to_deliverable),
    ("deliverable → preprod", lambda d, verbose=False: scenario_deliverable_to_preprod(d, base_path=Path(_tmpdir), verbose=False)),
    ("preprod → prod",      scenario_preprod_to_prod),
]

prod_data = None
for i, (name, step) in enumerate(linear_steps, 1):
    print(f"\nSTEP {i} — {name}")
    print("input:", data)
    result = run_step(step, data)
    print("output:", result)
    if not isinstance(result, dict) or result.get("status") in ["error", "failure"]:
        print("STOP — FAILURE DETECTED")
        raise SystemExit(1)
    data = result.get("data", result)

# STEP 7 et 8 reçoivent toutes deux prod_env
prod_env_data = {"prod_env": data.get("prod_env", {})}

print(f"\nSTEP 7 — prod → backup")
print("input:", prod_env_data)
r7 = run_step(scenario_prod_to_backup, prod_env_data)
print("output:", r7)
if r7.get("status") in ["error", "failure"]:
    print("STOP — FAILURE DETECTED")
    raise SystemExit(1)

print(f"\nSTEP 8 — prod → github")
print("input:", prod_env_data)
r8 = run_step(scenario_prod_to_github, prod_env_data)
print("output:", r8)
if r8.get("status") in ["error", "failure"]:
    print("STOP — FAILURE DETECTED")

print("\n=== FIN ===")
