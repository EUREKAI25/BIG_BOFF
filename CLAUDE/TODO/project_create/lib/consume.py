def consume(bucket, now, n):
    elapsed = now - bucket["last_refill"]
    tokens_to_add = elapsed * bucket["refill_rate"]
    bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, bucket["capacity"])
    bucket["last_refill"] = now
    
    if bucket["tokens"] >= n:
        bucket["tokens"] -= n
        return True
    return False