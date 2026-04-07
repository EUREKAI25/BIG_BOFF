from core.query.get_attribute import get_attribute

def query(objects, where=None):
    if where is None:
        where = {}

    result = []
    for obj in objects.values():
        ok = True
        for key, expected in where.items():
            actual = get_attribute(obj, key)
            if expected == "__exists__":
                if actual is None:
                    ok = False
                    break
            elif actual != expected:
                ok = False
                break
        if ok:
            result.append(obj)
    return result
