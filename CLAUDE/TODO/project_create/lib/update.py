def update(table, where_fn, updates_dict):
    for row in table["rows"]:
        if where_fn(row):
            row.update(updates_dict)