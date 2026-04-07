from core.query.query import query

def get_object_by_attribute(objects, attr_name, attr_value="__exists__"):
    results = query(objects, {attr_name: attr_value})
    return results[0] if results else None
