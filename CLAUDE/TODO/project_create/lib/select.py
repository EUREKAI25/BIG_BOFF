from filter_rows import filter_rows
from project_columns import project_columns


def select(table, where_fn=None, cols=None):
    rows = filter_rows(table["rows"], where_fn)
    return project_columns(rows, cols)
