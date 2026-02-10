# SUPERREAD DSL — Features Futures v1.2
## À implémenter lors du déploiement des objets concernés

---

## 1. AGRÉGATIONS

```
read Facture.paid=false.sum(amount)
read Facture.group(client).sum(amount)
read Product.avg(price)
read Order.min(date)
read Order.max(total)
read Client.distinct(country)
```

---

## 2. JOINTURES

Inclure les objets liés dans les résultats.

```
read Facture.paid=false ++client ++product
```

Retourne :
```json
{
  "id": 123,
  "amount": 500,
  "client": { "name": "Acme", "country": "FR" },
  "product": { "name": "Website" }
}
```

Syntaxe :
```
++attr               Inclure l'objet lié par 'attr'
++attr.subattr       Inclure un sous-objet
++*                  Inclure toutes les relations
```

---

## 3. EXISTS / NOT EXISTS

```
read Client.exists(@facture)           # Clients avec au moins une facture
read Client.!exists(@facture)          # Clients sans factures
read Product.exists(@order.date>$today-30d)  # Produits commandés récemment
```

---

## 4. VARIABLES ET ALIAS

### Définir une variable

```
let premium = read Client.tier=premium
read Facture.@client=$premium
```

### Alias dans résultats

```
read Facture --fields=amount:total,client.name:client_name
```

---

## 5. TEMPLATES DE REQUÊTES

### Sauvegarder

```
save unpaid_invoices = read Facture.paid=false.date=[$today-30d..]
```

### Exécuter

```
run unpaid_invoices
```

### Avec paramètres

```
save invoices_by_client(client_id) = read Facture.@client=Client.id=$client_id
run invoices_by_client(128)
```

---

## 6. EXPORT

```
read Facture.paid=false --export=csv
read Facture.paid=false --export=json
read Agent --export=json --file=agents.json
read Client --export=xlsx
```

Formats supportés :
- csv
- json
- xlsx
- xml
- yaml

---

## 7. BATCH OPERATIONS

Plusieurs opérations atomiques en une transaction.

```
batch {
  update Facture.id=123 set paid=true,paid_at=$now
  create Payment:P123 amount=500 facture=Facture:123
  update Client.id=456 set balance={balance-500}
}
```

Rollback automatique si une opération échoue.

---

## 8. WATCHERS / TRIGGERS

### Watch (surveillance continue)

```
watch Facture.overdue=true -> notify(admin, "Facture en retard: {id}")
watch Stock.quantity<10 -> alert("Stock faible: {product.name}")
```

### Triggers (sur événements)

```
on create Facture -> set due_date=$today+30d
on update Client.tier=premium -> log("Client {name} devenu premium")
on delete Order -> archive(Order)
```

---

## 9. FONCTIONS DE TRANSFORMATION

### Sur les champs

```
read Client --fields=name.upper(),email.lower()
read Facture --fields=date.format("DD/MM/YYYY")
read Product --fields=price.format("€")
```

### Calculs avec formatage

```
read Product --fields=name,{price*1.2}.round(2):price_ttc
read Facture --fields=amount,{amount*0.2}.round(2):tva
```

### Fonctions disponibles

| Fonction | Description |
|----------|-------------|
| `.upper()` | Majuscules |
| `.lower()` | Minuscules |
| `.trim()` | Supprimer espaces |
| `.capitalize()` | Première lettre majuscule |
| `.format(pattern)` | Formatage (date, nombre) |
| `.round(n)` | Arrondir à n décimales |
| `.floor()` | Arrondi inférieur |
| `.ceil()` | Arrondi supérieur |
| `.abs()` | Valeur absolue |
| `.length()` | Longueur (string/array) |
| `.first()` | Premier élément |
| `.last()` | Dernier élément |
| `.slice(start,end)` | Sous-chaîne |
| `.replace(a,b)` | Remplacer |
| `.split(sep)` | Découper |
| `.join(sep)` | Joindre |

---

## 10. HISTORIQUE ET AUDIT

### Historique d'un objet

```
history Agent.name=ArchitectAgent
```

Retourne :
```
2024-12-12 10:30 - created by system
2024-12-12 11:45 - updated scope: core → global
2024-12-12 14:20 - updated priority: 5 → 10
```

### Diff entre versions

```
diff Agent.name=ArchitectAgent --from=$yesterday
diff Agent.name=ArchitectAgent --from=2024-12-01 --to=2024-12-10
```

### Restaurer une version

```
restore Agent.name=ArchitectAgent --to=$yesterday
```

---

## 11. STATS SYSTÈME

### Global

```
stats
```

Retourne :
```
Objets: 310
Types: 15
Relations: 28
Requêtes/min: 45
Uptime: 2h 34m
```

### Par type

```
stats Agent
```

Retourne :
```
Objets: 5
Attributs moyens: 12
Relations: 8
Dernière modification: il y a 2h
Taille mémoire: 2.4 KB
```

---

## 12. SOUS-REQUÊTES

```
read Facture.@client=@(read Client.country=ES)
read Product.id!@@(read OrderLine.distinct(product_id))
```

Équivalent SQL :
```sql
SELECT * FROM Facture 
WHERE client IN (SELECT id FROM Client WHERE country='ES')
```

---

## 13. BETWEEN (raccourci)

```
read Facture.amount.between(100,500)
```

Équivalent à :
```
read Facture.amount=[100..500]
```

---

## 14. PRIORITÉ D'IMPLÉMENTATION

| Priorité | Feature | Dépendance |
|----------|---------|------------|
| 🔴 Haute | Jointures `++` | Objets relationnels |
| 🔴 Haute | Agrégations | Objets avec montants |
| 🔴 Haute | Export | Intégration externe |
| 🟡 Moyenne | Templates | Workflows répétitifs |
| 🟡 Moyenne | Variables | Requêtes complexes |
| 🟡 Moyenne | Fonctions transform | Formatage rapports |
| 🟢 Basse | Watchers | Automatisation |
| 🟢 Basse | Triggers | Events système |
| 🟢 Basse | Historique | Audit/compliance |
| 🟢 Basse | Batch | Transactions |

---

## CHANGELOG

- **v1.2** (2024-12-12) : Document initial des features futures
