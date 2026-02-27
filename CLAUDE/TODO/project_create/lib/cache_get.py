def cache_get(cache, key):
    if key not in cache["entries"]:
        return None

    entry = cache["entries"][key]

    if "expire_at" in entry and entry["expire_at"] < __import__('time').time():
        return None

    return entry.get("value")