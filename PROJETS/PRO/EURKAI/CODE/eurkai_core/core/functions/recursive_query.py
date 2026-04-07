"""
recursive_query — moteur de requête récursif et composable sur le catalog EURKAI.

Principe :
  - Le catalog est un dict de listes (catalog_object_list, catalog_schema_list, etc.)
  - Les objets se référencent via des champs qui contiennent un ident ou un lineage
  - QueryCriteria est composable et récursif (N niveaux)

Usage simple (depuis une méthode métier) :
  from core.functions.recursive_query import recursive_query, QueryCriteria

  invoices = recursive_query(catalog,
      QueryCriteria("Object:Document:Invoice")
          .where("invoice_status", "=", "paid")
          .related_via("invoice_client", client_criteria, direction="outgoing")
  )

Directions :
  "outgoing" — self.field pointe vers un objet related   (ex: invoice.invoice_client → Client)
  "incoming" — related.field pointe vers self            (ex: Invoice.invoice_client → client)
"""

from core.storage.catalog_storage import get_storage


# ─── Critères ────────────────────────────────────────────────────────────────

class QueryCriteria:
    """
    Définit les critères d'une requête : lineage, filtres sur champs, relations.
    Chainable : .where(...).related_via(...).where(...)
    """

    def __init__(self, lineage_prefix=None):
        """
        lineage_prefix : filtre par préfixe de lineage.
            ex: "Object:Document:Invoice" → inclut Invoice et tous ses descendants.
            None → tous les objets.
        """
        self.lineage_prefix = lineage_prefix
        self.filters   = []   # [(field, operator, value), ...]
        self.relations = []   # [(field, subcriteria, direction), ...]
        self.type_name = "object"  # type dans CatalogStorage (ex: "object", "schema", "rule")

    def where(self, field, operator, value):
        """
        Ajoute un filtre sur un champ.

        Opérateurs supportés :
          =  !=  >  <  >=  <=  LIKE  IN  STARTS_WITH  EXISTS  NOT_EXISTS
        """
        self.filters.append((field, operator, value))
        return self

    def related_via(self, field, subcriteria, direction="outgoing"):
        """
        Ajoute une contrainte relationnelle récursive.

        field       : nom du champ qui porte la référence (ident ou lineage)
        subcriteria : QueryCriteria des objets liés
        direction   :
            "outgoing" — self[field] référence un objet des résultats de subcriteria
            "incoming" — subcriteria[field] référence cet objet
        """
        self.relations.append((field, subcriteria, direction))
        return self

    def from_type(self, type_name):
        """Cible un type catalog différent (ex: 'schema', 'rule')."""
        self.type_name = type_name
        return self


# ─── Moteur ──────────────────────────────────────────────────────────────────

def recursive_query(catalog, criteria, _storage=None):
    """
    Filtre le catalog selon les critères et retourne une liste d'objets (dicts).

    catalog  : dict catalog EURKAI
    criteria : QueryCriteria
    """
    if _storage is None:
        _storage = get_storage(catalog)

    # 1. Candidats : tous les objets du type cible (dict ident → objet)
    all_objects_dict = _storage.get_all(criteria.type_name)
    if not all_objects_dict:
        return []
    all_objects = list(all_objects_dict.values())

    # 2. Filtre lineage
    if criteria.lineage_prefix:
        prefix = criteria.lineage_prefix.rstrip(":")
        candidates = [
            o for o in all_objects
            if _lineage_matches(o.get("object_lineage", ""), prefix)
        ]
    else:
        candidates = list(all_objects)

    # 3. Filtres sur champs
    for (field, op, value) in criteria.filters:
        candidates = [o for o in candidates if _match(o, field, op, value)]

    # 4. Contraintes relationnelles (récursion)
    for (field, subcriteria, direction) in criteria.relations:
        related_objects = recursive_query(catalog, subcriteria, _storage)
        related_idents  = {r["object_ident"] for r in related_objects if "object_ident" in r}
        related_lineages = {r.get("object_lineage", "") for r in related_objects}

        if direction == "outgoing":
            # self[field] → objet related
            candidates = [
                o for o in candidates
                if _resolves_to(o.get(field), related_idents, related_lineages)
            ]
        else:  # incoming
            # related[field] → self
            matched_idents = set()
            for o in candidates:
                o_ident = o.get("object_ident", "")
                o_lineage = o.get("object_lineage", "")
                for r in related_objects:
                    if _resolves_to(r.get(field), {o_ident}, {o_lineage}):
                        matched_idents.add(o_ident)
                        break
            candidates = [o for o in candidates if o.get("object_ident") in matched_idents]

    return candidates


# ─── Helpers internes ────────────────────────────────────────────────────────

def _lineage_matches(lineage, prefix):
    """
    Vérifie si un lineage correspond au préfixe.
    "Object:Design:Palette" correspond à prefix "Object:Design" et "Object:Design:Palette".
    """
    return lineage == prefix or lineage.startswith(prefix + ":")


def _match(obj, field, operator, value):
    """Évalue un filtre (field, operator, value) sur un objet dict."""
    obj_val = obj.get(field)

    if operator == "NOT_EXISTS":
        return obj_val is None
    if operator == "EXISTS":
        return obj_val is not None

    if obj_val is None:
        return False

    op = operator.upper() if isinstance(operator, str) else operator

    if op in ("=", "=="):
        return str(obj_val) == str(value)
    if op == "!=":
        return str(obj_val) != str(value)
    if op == "LIKE":
        return str(value).lower() in str(obj_val).lower()
    if op == "STARTS_WITH":
        return str(obj_val).startswith(str(value))
    if op == "IN":
        return obj_val in value
    if op in (">", "<", ">=", "<="):
        try:
            return eval(f"{float(obj_val)} {op} {float(value)}")  # noqa: S307
        except (ValueError, TypeError):
            # Fallback : comparaison lexicale
            if op == ">":  return str(obj_val) > str(value)
            if op == "<":  return str(obj_val) < str(value)
            if op == ">=": return str(obj_val) >= str(value)
            if op == "<=": return str(obj_val) <= str(value)
    return False


def _resolves_to(field_value, idents, lineages):
    """
    Vérifie si une valeur de champ référence un objet parmi un ensemble de résultats.
    Supporte : ident direct, lineage complet, préfixe lineage.
    """
    if field_value is None:
        return False
    fv = str(field_value).strip()
    if fv in idents:
        return True
    for lin in lineages:
        if lin and (fv == lin or fv.startswith(lin + ":")):
            return True
    return False
