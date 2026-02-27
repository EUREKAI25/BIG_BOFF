def peek(queue):
    if queue["items"]:
        return queue["items"][0]
    return None