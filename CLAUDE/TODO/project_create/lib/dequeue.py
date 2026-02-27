def dequeue(queue):
    if queue["items"]:
        return queue["items"].pop(0)
    return None