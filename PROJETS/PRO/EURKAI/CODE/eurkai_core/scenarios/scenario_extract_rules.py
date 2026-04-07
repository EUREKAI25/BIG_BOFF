"""
scenario_extract_rules
Extrait les règles et méthodes depuis un document de cadrage.
Persiste le résultat dans output/rule_list_cadre.json.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from catalog.load_catalog import load_catalog
from agents.agent_extract_rules import run as agent_extract


def run(document_path, model_type="llm", verbose=True):
    """
    document_path : chemin vers le document à analyser (str ou Path).
    Retourne : dict avec rule_list, method_list, success.
    """
    doc_path = Path(document_path)
    if not doc_path.exists():
        return {"success": False, "error": f"document_not_found:{document_path}"}

    source_document = doc_path.read_text(encoding="utf-8")

    catalog = load_catalog()

    if verbose:
        print("=" * 60)
        print(f"scenario_extract_rules — {doc_path.name}")
        print("=" * 60)

    result = agent_extract(source_document, catalog, model_type=model_type, verbose=verbose)

    if not result.get("success"):
        if verbose:
            print(f"  [FAIL]  {result.get('error')}")
        return result

    # Persister
    output_path = Path(__file__).parent.parent / "output" / "rule_list_cadre.json"
    output_path.parent.mkdir(exist_ok=True)

    existing = {"rule_list": [], "method_list": []}
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text())
        except Exception:
            pass

    # Merge : déduplique par ident
    existing_rule_ids   = {r.get("rule_ident") for r in existing.get("rule_list", [])}
    existing_method_ids = {m.get("method_ident") for m in existing.get("method_list", [])}

    new_rules   = [r for r in result["rule_list"]   if r.get("rule_ident")   not in existing_rule_ids]
    new_methods = [m for m in result["method_list"] if m.get("method_ident") not in existing_method_ids]

    merged = {
        "rule_list":   existing.get("rule_list", [])   + new_rules,
        "method_list": existing.get("method_list", []) + new_methods,
    }

    output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))

    if verbose:
        print(f"\n  Ajoutés : {len(new_rules)} règles + {len(new_methods)} méthodes")
        print(f"  Total   : {len(merged['rule_list'])} règles + {len(merged['method_list'])} méthodes")
        print(f"  Fichier : {output_path}")
        print("=" * 60)

    return {
        "success":      True,
        "rule_list":    result["rule_list"],
        "method_list":  result["method_list"],
        "new_rules":    len(new_rules),
        "new_methods":  len(new_methods),
        "output_path":  str(output_path),
        "usage":        result.get("usage", {}),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scenario_extract_rules.py <chemin_document> [model_type]")
        sys.exit(1)
    doc   = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "llm"
    res   = run(doc, model_type=model)
    sys.exit(0 if res.get("success") else 1)
