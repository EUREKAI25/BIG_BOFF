def refill_bucket(bucket, now):
    elapsed = now - bucket["last_refill"]
    tokens_to_add = elapsed * bucket["refill_rate"]
    bucket["tokens"] = min(bucket["tokens"] + tokens_to_add, bucket["capacity"])
    bucket["last_refill"] = now