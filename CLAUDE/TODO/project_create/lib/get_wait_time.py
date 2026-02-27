def get_wait_time(bucket, now, n):
    refill_bucket(bucket, now)
    
    if bucket["tokens"] >= n:
        return 0.0
    
    tokens_needed = n - bucket["tokens"]
    wait_time = tokens_needed / bucket["refill_rate"]
    return wait_time

def refill_bucket(bucket, now):
    elapsed = now - bucket["last_refill"]
    tokens_to_add = elapsed * bucket["refill_rate"]
    bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, bucket["capacity"])
    bucket["last_refill"] = now