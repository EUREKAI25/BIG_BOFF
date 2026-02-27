def delete(table, where_fn):
    table['rows'] = [row for row in table['rows'] if not where_fn(row)]