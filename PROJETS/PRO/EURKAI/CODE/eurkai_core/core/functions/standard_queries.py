"""
standard_queries — 13 queries standard EURKAI.
Chaque fonction wraps recursive_query avec extraction ciblée d'une sous-liste.

Signature uniforme : (catalog, object_ident, criteria=None)
  - criteria optionnel : QueryCriteria enrichissant la recherche de base
  - Le filtre object_ident est toujours appliqué en premier

Source de vérité : EURKAI — CADRE STABLE v0 (owned_element_list structure)
Instances catalog : catalog_standard_query_list
"""

from core.functions.recursive_query import recursive_query, QueryCriteria


# ─── Helper interne ───────────────────────────────────────────────────────────

def _get_object(catalog, object_ident, criteria):
    q = (criteria or QueryCriteria()).where("object_ident", "=", object_ident)
    result = recursive_query(catalog, q)
    return result[0] if result else None

def _el(obj, *keys):
    """Descend dans object_elementlist via une suite de clés."""
    node = obj.get("object_elementlist", {}) if obj else {}
    for k in keys:
        node = node.get(k, {}) if isinstance(node, dict) else {}
    return node


# ─── Queries par type d'élément ───────────────────────────────────────────────

def get_attributes_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_attribute_list")

def get_methods_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_method_list")

def get_rules_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_rule_list")

def get_options_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_option_list")

def get_relations_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_relation_list")

def get_tags_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_base_list", "tag_list")


# ─── Queries owned / inherited / injected ────────────────────────────────────

def get_owned_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return obj.get("object_elementlist", {}) if obj else {}

def get_inherited_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    if not obj:
        return {}
    lineage = obj.get("object_lineage", "")
    parts = [p for p in lineage.split(":") if p]
    parent_ident = parts[-2] if len(parts) >= 2 else "Object"
    parent = _get_object(catalog, parent_ident, None)
    return parent.get("object_elementlist", {}) if parent else {}

def get_injected_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    return _el(obj, "object_transversal_parameter_list")


# ─── Queries tree ─────────────────────────────────────────────────────────────

def get_children_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    if not obj:
        return []
    lineage = obj.get("object_lineage", "")
    q = (criteria or QueryCriteria(lineage))
    all_desc = recursive_query(catalog, q)
    depth = len([p for p in lineage.split(":") if p])
    return [o for o in all_desc
            if o.get("object_lineage") != lineage
            and len([p for p in o.get("object_lineage","").split(":") if p]) == depth + 1]

def get_parents_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    if not obj:
        return []
    lineage = obj.get("object_lineage", "")
    parts = [p for p in lineage.split(":") if p]
    parents = []
    for i in range(1, len(parts)):
        ancestor_lineage = ":".join(parts[:i])
        ancestor_ident = parts[i - 1]
        parent = _get_object(catalog, ancestor_ident, None)
        if parent and parent.get("object_lineage") == ancestor_lineage:
            parents.append(parent)
    return parents

def get_siblings_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    if not obj:
        return []
    lineage = obj.get("object_lineage", "")
    parts = [p for p in lineage.split(":") if p]
    if len(parts) < 2:
        return []
    parent_lineage = ":".join(parts[:-1])
    q = QueryCriteria(parent_lineage)
    if criteria:
        q.filters += criteria.filters
    all_children = recursive_query(catalog, q)
    depth = len(parts)
    return [o for o in all_children
            if o.get("object_lineage") != lineage
            and len([p for p in o.get("object_lineage","").split(":") if p]) == depth]

def get_tree_by_object(catalog, object_ident, criteria=None):
    obj = _get_object(catalog, object_ident, criteria)
    if not obj:
        return []
    lineage = obj.get("object_lineage", "")
    q = (criteria or QueryCriteria(lineage))
    return [o for o in recursive_query(catalog, q) if o.get("object_lineage") != lineage]


# ─── Registre ─────────────────────────────────────────────────────────────────

STANDARD_QUERIES = {
    "get_attributes_by_object":  get_attributes_by_object,
    "get_methods_by_object":     get_methods_by_object,
    "get_rules_by_object":       get_rules_by_object,
    "get_options_by_object":     get_options_by_object,
    "get_relations_by_object":   get_relations_by_object,
    "get_tags_by_object":        get_tags_by_object,
    "get_owned_by_object":       get_owned_by_object,
    "get_inherited_by_object":   get_inherited_by_object,
    "get_injected_by_object":    get_injected_by_object,
    "get_children_by_object":    get_children_by_object,
    "get_parents_by_object":     get_parents_by_object,
    "get_siblings_by_object":    get_siblings_by_object,
    "get_tree_by_object":        get_tree_by_object,
}

def run_standard_query(query_ident, catalog, object_ident, criteria=None):
    """Point d'entrée générique : run_standard_query('get_rules_by_object', catalog, 'Rule')"""
    fn = STANDARD_QUERIES.get(query_ident)
    if fn is None:
        raise ValueError(f"StandardQuery inconnue : {query_ident}")
    return fn(catalog, object_ident, criteria)
