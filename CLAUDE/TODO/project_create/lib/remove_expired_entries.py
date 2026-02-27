def remove_expired_entries(cache, expired_keys):
    count = 0
    for key in expired_keys:
        if key in cache["entries"]:
            del cache["entries"][key]
            count += 1
    return count