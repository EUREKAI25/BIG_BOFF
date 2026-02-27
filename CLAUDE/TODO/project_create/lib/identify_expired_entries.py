def identify_expired_entries(cache, current_time):
    expired_keys = []
    for key, entry in cache["entries"].items():
        if entry["expire_at"] < current_time:
            expired_keys.append(key)
    return expired_keys