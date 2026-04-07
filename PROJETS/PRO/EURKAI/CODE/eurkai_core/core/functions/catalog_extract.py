"""
catalog_extract — extrait un sous-catalog depuis le catalog complet.
Filtre par lineage prefix, par type_name (nom de liste), ou par liste explicite.
Le sous-catalog extrait est un catalog valide et autonome.
"""


def catalog_extract(catalog, lineage_prefix=None, type_list=None, list_name_list=None):
    """
    Extrait un sous-catalog depuis le catalog complet.

    Paramètres (au moins un requis) :
      lineage_prefix  — str : filtre les objets dont object_lineage commence par ce préfixe
                        ex: "Object:Design" → tous les objets Design + leurs schemas associés
      type_list       — list[str] : liste de type_names à inclure intégralement
                        ex: ["object", "schema"] → catalog_object_list + catalog_schema_list
      list_name_list  — list[str] : liste de clés catalog exactes à inclure
                        ex: ["catalog_object_list", "catalog_role_list"]

    Retourne un dict catalog extrait (sans _storage — à recharger si nécessaire).
    """
    from core.storage.catalog_storage import get_storage

    storage = catalog.get("_storage") or get_storage(catalog)

    extracted = {}

    if list_name_list:
        # Inclusion directe par nom de liste
        for list_name in list_name_list:
            if list_name in catalog:
                extracted[list_name] = dict(catalog[list_name])

    if type_list:
        # Inclusion par type_name → catalog_{type}_list
        for type_name in type_list:
            all_items = storage.get_all(type_name)
            list_key  = f"catalog_{type_name}_list"
            extracted.setdefault(list_key, {}).update(all_items)

    if lineage_prefix:
        # Filtrage par lineage dans toutes les listes
        for type_name in storage.list_types():
            matching = storage.get_all_by_filter(
                type_name,
                lambda obj: _matches_lineage(obj, lineage_prefix)
            )
            if matching:
                list_key = f"catalog_{type_name}_list"
                extracted.setdefault(list_key, {}).update(matching)

    return extracted


def _matches_lineage(obj, prefix):
    """Vérifie si un objet a un lineage qui commence par le prefix donné."""
    lineage = obj.get("object_lineage") or obj.get("schema_ident") or ""
    return lineage.startswith(prefix)
