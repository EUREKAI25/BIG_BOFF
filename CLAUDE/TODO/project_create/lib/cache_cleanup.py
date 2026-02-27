import time
from identify_expired_entries import identify_expired_entries
from remove_expired_entries import remove_expired_entries


def cache_cleanup(cache):
    expired_keys = identify_expired_entries(cache, time.time())
    return remove_expired_entries(cache, expired_keys)
