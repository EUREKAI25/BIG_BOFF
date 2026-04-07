# eurkai_bootstrap_minimal.py
# Bootstrap minimal :
# - 1 catalog
# - 1 object
# - 1 schema
# - 1 scenario
# - 4 SuperMethods
# - 1 règle / 1 méthode de validation
#
# Objectif :
# voir l'exécution réelle de la MRG avant d'enrichir le système.

from __future__ import annotations

from dataclasses import dataclass
from pprint import pprint
from typing import Any, Callable, Dict, Optional


Catalog = Dict[str, Any]
ObjectDict = Dict[str, Any]
ResultDict = Dict[str, Any]


# ============================================================
# FONCTIONS MÉTIER MINIMALES
# ============================================================

def filter_has_schema(obj: ObjectDict) -> bool:
    """Filtre minimal : l'objet possède un schema explicite."""
    return bool(obj.get("schema"))


def validate_object_against_schema(obj: ObjectDict, catalog: Catalog) -> ResultDict:
    """
    Validation minimale et agnostique :
    - récupère le schema de l'objet
    - vérifie les required_element_list du schema
    - exécute les validation_rule_list du schema
    """
    schema_ident = obj.get("schema")
    if not schema_ident:
        return {
            "success": False,
            "status": "failure",
            "object_ident": obj.get("ident"),
            "schema_ident": None,
            "tested_rule_count": 0,
            "success_count": 0,
            "failure_count": 1,
            "score": 0,
            "failure_list": ["missing_schema_reference"],
            "details": {},
        }

    schema = catalog["schema_list"].get(schema_ident)
    if not schema:
        return {
            "success": False,
            "status": "failure",
            "object_ident": obj.get("ident"),
            "schema_ident": schema_ident,
            "tested_rule_count": 0,
            "success_count": 0,
            "failure_count": 1,
            "score": 0,
            "failure_list": [f"unknown_schema:{schema_ident}"],
            "details": {},
        }

    failure_list: list[str] = []
    success_count = 0
    tested_rule_count = 0

    # 1) présence des éléments requis
    required_elements = schema.get("required_element_list", {})
    for element_name, element_spec in required_elements.items():
        tested_rule_count += 1

        exists = resolve_path_exists(obj, element_name)
        if not exists:
            failure_list.append(f"missing_required_element:{element_name}")
        else:
            success_count += 1

    # 2) règles de validation du schema
    validation_rule_list = schema.get("validation_rule_list", {})
    for rule_ident, rule in validation_rule_list.items():
        tested_rule_count += 1

        validation_method_name = rule.get("how")
        validation_method = catalog["function_list"].get(validation_method_name)
        if validation_method is None:
            failure_list.append(f"unknown_validation_method:{validation_method_name}")
            continue

        rule_result = validation_method(obj=obj, schema=schema, rule=rule, catalog=catalog)
        if rule_result.get("success"):
            success_count += 1
        else:
            failure_list.append(rule_ident)

    failure_count = tested_rule_count - success_count
    score = 100 if tested_rule_count == 0 else int((success_count / tested_rule_count) * 100)

    return {
        "success": failure_count == 0,
        "status": "success" if failure_count == 0 else "failure",
        "object_ident": obj.get("ident"),
        "schema_ident": schema_ident,
        "tested_rule_count": tested_rule_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "score": score,
        "failure_list": failure_list,
        "details": {
            "required_element_list": list(required_elements.keys()),
            "validation_rule_list": list(validation_rule_list.keys()),
        },
    }


def rule_has_schema_reference(
    obj: ObjectDict,
    schema: ObjectDict,
    rule: ObjectDict,
    catalog: Catalog,
) -> ResultDict:
    """
    Règle minimale :
    l'objet doit référencer exactement le schema attendu par ce test.
    """
    expected_schema = rule.get("params", {}).get("expected_schema_ident")
    actual_schema = obj.get("schema")

    ok = expected_schema == actual_schema
    return {
        "success": ok,
        "status": "success" if ok else "failure",
        "rule_ident": rule.get("ident"),
        "expected_schema_ident": expected_schema,
        "actual_schema_ident": actual_schema,
    }


def validate_attending_result(result: ResultDict, scenario: ObjectDict, catalog: Catalog) -> ResultDict:
    """
    Validation minimale du résultat de run.
    Pour ce bootstrap :
    - on attend simplement success == True
    - en cas d'échec, on déclenche failurehook (print)
    """
    attending_result = scenario.get("attending_result", {"success": True})
    expected_success = attending_result.get("success", True)
    actual_success = result.get("success", False)

    is_valid = actual_success == expected_success

    if not is_valid:
        failurehook_name = scenario.get("failurehook")
        if failurehook_name:
            failurehook = catalog["function_list"].get(failurehook_name)
            if failurehook:
                failurehook(result=result, scenario=scenario, catalog=catalog)

    return {
        "success": is_valid,
        "status": "success" if is_valid else "failure",
        "expected": attending_result,
        "actual": {"success": actual_success},
        "upstream_result": result,
    }


def schema_validate_failurehook_print(result: ResultDict, scenario: ObjectDict, catalog: Catalog) -> None:
    print("\n[FAILUREHOOK] schema_validate a échoué")
    pprint(result)


def render_validation_result(result: ResultDict, scenario: ObjectDict, catalog: Catalog) -> ResultDict:
    """
    Render minimal :
    retourne un dict lisible, sans créer d'objet spécial.
    """
    upstream = result.get("upstream_result", {})
    return {
        "scenario_ident": scenario.get("ident"),
        "status": result.get("status"),
        "expected": result.get("expected"),
        "actual": result.get("actual"),
        "object_ident": upstream.get("object_ident"),
        "schema_ident": upstream.get("schema_ident"),
        "score": upstream.get("score"),
        "tested_rule_count": upstream.get("tested_rule_count"),
        "success_count": upstream.get("success_count"),
        "failure_count": upstream.get("failure_count"),
        "failure_list": upstream.get("failure_list"),
    }


# ============================================================
# OUTILS GÉNÉRIQUES MINIMAUX
# ============================================================

def resolve_path_exists(obj: ObjectDict, dotted_path: str) -> bool:
    """
    Vérifie l'existence d'un chemin simple.
    Ex :
    - "schema"
    - "owned_element_list.base_list.name"
    """
    current: Any = obj
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def query(filter_name: str, catalog: Catalog) -> Optional[ObjectDict]:
    """
    SuperGet exécute simplement query(filter).
    Version ultra minimale :
    - retourne le premier objet conforme au filtre
    """
    filter_fn = catalog["filter_list"].get(filter_name)
    if filter_fn is None:
        raise ValueError(f"Unknown filter: {filter_name}")

    for obj in catalog["object_list"].values():
        if filter_fn(obj):
            return obj
    return None


def resolve_how(scenario: ObjectDict, what: ObjectDict, catalog: Catalog) -> Callable[..., ResultDict]:
    """
    Résolution minimale de how.
    Pour ce bootstrap :
    - scenario.how porte le nom de la fonction à exécuter
    """
    how_name = scenario.get("how")
    how_fn = catalog["function_list"].get(how_name)
    if how_fn is None:
        raise ValueError(f"Unknown how function: {how_name}")
    return how_fn


def run(what: ObjectDict, how: Callable[..., ResultDict], catalog: Catalog) -> ResultDict:
    """
    SuperExecute reste agnostique :
    - il ne connaît pas la logique métier
    - il applique juste how à what
    """
    return how(obj=what, catalog=catalog)


# ============================================================
# SUPERMETHODS
# ============================================================

def SuperGet(scenario: ObjectDict, catalog: Catalog) -> Dict[str, Any]:
    """
    SuperGet = query(scenario.what.filter)
    retourne un dict unique {what, how}
    """
    filter_name = scenario["what"]["filter"]
    what = query(filter_name, catalog)
    if what is None:
        raise ValueError(f"No object found for filter: {filter_name}")

    how = resolve_how(scenario, what, catalog)

    # how est un attribut de l'objet ; il n'est défini qu'au gré des opérations
    what["how"] = {
        "value": scenario.get("how"),
        "status": "ready",
    }

    return {
        "what": what,
        "how": how,
    }


def SuperExecute(input_pair: Dict[str, Any], scenario: ObjectDict, catalog: Catalog) -> ResultDict:
    return run(input_pair["what"], input_pair["how"], catalog)


def SuperValidate(execute_result: ResultDict, scenario: ObjectDict, catalog: Catalog) -> ResultDict:
    validate_name = scenario.get("validate")
    validate_fn = catalog["function_list"].get(validate_name)
    if validate_fn is None:
        raise ValueError(f"Unknown validate function: {validate_name}")
    return validate_fn(result=execute_result, scenario=scenario, catalog=catalog)


def SuperRender(validate_result: ResultDict, scenario: ObjectDict, catalog: Catalog) -> ResultDict:
    render_name = scenario.get("render")
    render_fn = catalog["function_list"].get(render_name)
    if render_fn is None:
        raise ValueError(f"Unknown render function: {render_name}")
    return render_fn(result=validate_result, scenario=scenario, catalog=catalog)


# ============================================================
# MRG MINIMALE
# ============================================================

def mrg(scenario_ident: str, catalog: Catalog) -> ResultDict:
    """
    MRG minimale en 4 lignes GEVR :
    SuperGet
    SuperExecute
    SuperValidate
    SuperRender
    """
    scenario = catalog["scenario_list"].get(scenario_ident)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_ident}")

    gevr_input = SuperGet(scenario, catalog)
    execute_result = SuperExecute(gevr_input, scenario, catalog)
    validate_result = SuperValidate(execute_result, scenario, catalog)
    render_result = SuperRender(validate_result, scenario, catalog)
    return render_result


# ============================================================
# CATALOGUE MINIMAL
# ============================================================

def build_catalog() -> Catalog:
    return {
        "filter_list": {
            "has_schema": filter_has_schema,
        },
        "function_list": {
            "validate_object_against_schema": validate_object_against_schema,
            "rule_has_schema_reference": rule_has_schema_reference,
            "validate_attending_result": validate_attending_result,
            "render_validation_result": render_validation_result,
            "schema_validate_failurehook_print": schema_validate_failurehook_print,
        },
        "object_list": {
            "Page": {
                "ident": "Page",
                "name": "Page",
                "schema": "PageSchema",
                "how": None,
                "owned_element_list": {
                    "base_list": {
                        "name": {"value": "Page"},
                        "ident": {"value": "Page"},
                    }
                },
            }
        },
        "schema_list": {
            "PageSchema": {
                "ident": "PageSchema",
                "required_element_list": {
                    "schema": {},
                    "owned_element_list.base_list.name": {},
                    "owned_element_list.base_list.ident": {},
                },
                "validation_rule_list": {
                    "has_schema_rule": {
                        "ident": "has_schema_rule",
                        "how": "rule_has_schema_reference",
                        "params": {
                            "expected_schema_ident": "PageSchema",
                        },
                    }
                },
            }
        },
        "scenario_list": {
            "schema_validate": {
                "ident": "schema_validate",
                "what": {
                    "filter": "has_schema",
                },
                "how": "validate_object_against_schema",
                "validate": "validate_attending_result",
                "render": "render_validation_result",
                "failurehook": "schema_validate_failurehook_print",
                "attending_result": {
                    "success": True,
                },
            }
        },
    }


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    catalog = build_catalog()
    result = mrg("schema_validate", catalog)

    print("\n=== RESULTAT FINAL ===")
    pprint(result)

    print("\n=== OBJECT APRES EXECUTION ===")
    pprint(catalog["object_list"]["Page"])