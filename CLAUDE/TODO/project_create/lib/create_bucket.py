import time

def create_bucket(capacity, refill_rate):
    return {
        "tokens": capacity,
        "capacity": capacity,
        "refill_rate": refill_rate,
        "last_refill": time.time()
    }