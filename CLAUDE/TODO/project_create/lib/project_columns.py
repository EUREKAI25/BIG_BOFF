def project_columns(rows, cols=None):
    if cols is None:
        return rows
    return [{col: row[col] for col in cols if col in row} for row in rows]