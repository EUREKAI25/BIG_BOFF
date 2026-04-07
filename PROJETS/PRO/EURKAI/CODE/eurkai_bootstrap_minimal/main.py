from catalog.catalog import load_catalog
from functions.schema_validate import schema_validate

if __name__ == "__main__":
    catalog = load_catalog()
    schema_validate(catalog)
