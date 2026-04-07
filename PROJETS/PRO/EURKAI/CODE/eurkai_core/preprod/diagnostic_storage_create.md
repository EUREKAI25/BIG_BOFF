# Diagnostic — storage = [] 
Date : 2026-04-07

---

## A. storage_create — état réel

- existe ?        OUI  (modules/storage_create.py)
- implémenté ?    OUI  — itère data_models, appelle agent_generate_code, retourne des modules
- stub ?          NON

---

## B. Appel dans product_create

- appelé ?        OUI  (ligne 98-109 de product_create.py)
- conditionnel ?  NON  — appelé inconditionnellement

---

## C. Cause exacte

storage est vide parce que _SPECS_CODE ne contient pas de clé "data_models".
product_create lit `specs.get("data_models")` → obtient [] → storage_create n'a rien à générer.

---

## D. Correction minimale

Fichier à modifier : _SPECS_CODE (dans scenario_specs_to_deliverable.py ou dans le script d'appel)

Ajouter dans les specs passées à run() :

```python
"data_models": [
    {"name": "User",    "table": "users",    "fields": [{"name": "id", "type": "uuid"}, {"name": "email", "type": "string"}]},
    {"name": "Invoice", "table": "invoices", "fields": [{"name": "id", "type": "uuid"}, {"name": "amount", "type": "decimal"}]},
    {"name": "Payment", "table": "payments", "fields": [{"name": "id", "type": "uuid"}, {"name": "amount", "type": "decimal"}]},
]
```

---

## Fichiers lus

- CODE/eurkai_core/modules/storage_create.py
- CODE/eurkai_core/modules/product_create.py
