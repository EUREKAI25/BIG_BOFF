def cache_set(cache, key, value):
    import time
    cache["entries"][key] = {
        "value": value,
        "expire_at": time.time() + cache["ttl_seconds"]
    }