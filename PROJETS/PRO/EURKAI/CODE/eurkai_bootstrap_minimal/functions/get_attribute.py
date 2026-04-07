def get_attribute(obj, attr_name):
    if not isinstance(obj, dict):
        return None
    return obj.get(attr_name)
