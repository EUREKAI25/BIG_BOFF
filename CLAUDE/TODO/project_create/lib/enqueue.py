def enqueue(queue, item):
    if len(queue["items"]) < queue["max_size"]:
        queue["items"].append(item)
    return queue