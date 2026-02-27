def filter_rows(rows, where_fn=None):
    if where_fn is None:
        return rows
    return [row for row in rows if where_fn(row)]