def insert(table, row):
    # Valider que toutes les clés de row sont dans columns
    for key in row.keys():
        if key not in table["columns"]:
            raise ValueError(f"Column '{key}' not declared in table")
    
    # Ajouter la row aux rows
    table["rows"].append(row)