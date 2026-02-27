def count(table, filter_func=None):
    if filter_func is None:
        return len(table["rows"])
    return sum(1 for row in table["rows"] if filter_func(row))