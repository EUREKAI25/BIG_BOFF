# ============================================================
# SUPERREAD DSL — SYNTAXE DÉFINITIVE v1.0
# EUREKAI Query Language
# ============================================================

## Vue d'ensemble

SuperRead est le langage de requête unifié d'EUREKAI. Il permet de lire, 
créer, modifier et supprimer des objets avec une syntaxe simple et puissante.

---

## 1. OPÉRATIONS CRUD

```bash
# LECTURE
read <Type>[.conditions]... [--options]

# CRÉATION
create <Type>:<Name> [attr=val]...

# MISE À JOUR  
update <Type>[.conditions]... set <attr>=<val>[,<attr>=<val>]... [--options]

# SUPPRESSION
delete <Type>[.conditions]... [--options]
```

---

## 2. OPÉRATEURS DE COMPARAISON

| Opérateur | Description | Exemple |
|-----------|-------------|---------|
| `=` | Égal | `.status=active` |
| `!=` | Différent | `.status!=deleted` |
| `>` | Supérieur | `.amount>1000` |
| `>=` | Supérieur ou égal | `.priority>=5` |
| `<` | Inférieur | `.stock<10` |
| `<=` | Inférieur ou égal | `.age<=65` |
| `~` | Contient (LIKE %val%) | `.name~martin` |
| `^` | Commence par (LIKE val%) | `.code^INV` |
| `$` | Finit par (LIKE %val) | `.email$@gmail.com` |
| `@` | Dans liste (IN) | `.country@FR,ES,IT` |
| `!@` | Pas dans liste (NOT IN) | `.status!@deleted,archived` |
| `?` | Existe (IS NOT NULL) | `.email?` |
| `!?` | N'existe pas (IS NULL) | `.deleted_at!?` |

---

## 3. OPÉRATEURS LOGIQUES

| Opérateur | Description | Exemple |
|-----------|-------------|---------|
| `.` | AND (entre attributs) | `.status=active.priority>5` |
| `\|` | OR (entre conditions) | `(.country=FR\|.country=ES)` |
| `()` | Groupement | `.status=active.(.country=FR\|.vip=true)` |
| `!()` | NOT (négation groupe) | `.!(status=deleted)` |

---

## 4. OPÉRATEURS ARITHMÉTIQUES

Utilisables dans les valeurs et expressions.

| Opérateur | Description | Exemple |
|-----------|-------------|---------|
| `+` | Addition | `{price+tax}` |
| `-` | Soustraction | `{price-discount}` |
| `*` | Multiplication | `{quantity*unit_price}` |
| `/` | Division | `{total/count}` |
| `%` | Modulo | `{id%2}` |

### Exemples de calculs

```bash
# Produits avec marge > 20%
read Product.{price-cost}>cost*0.2

# Commandes total > 500
read Order.{quantity*unit_price}>500
```

---

## 5. VARIABLES DE DATE

| Variable | Description | Exemple |
|----------|-------------|---------|
| `$now` | Date/heure courante | `.created_at>$now-1h` |
| `$today` | Aujourd'hui 00:00:00 | `.date=$today` |
| `$yesterday` | Hier 00:00:00 | `.date=$yesterday` |
| `$tomorrow` | Demain 00:00:00 | `.due_date<$tomorrow` |

### Arithmétique de dates

```bash
$now+7d          # Dans 7 jours
$now-1h          # Il y a 1 heure
$today-30d       # Il y a 30 jours
$now+2w          # Dans 2 semaines

# Unités: s (secondes), m (minutes), h (heures), d (jours), w (semaines)
```

### Exemples

```bash
# Factures des 7 derniers jours
read Facture.date>=$today-7d

# Sessions expirées
read Session.expires_at<$now

# Tâches dues demain
read Task.due_date<$tomorrow.due_date>=$today
```

---

## 6. RELATIONS (Attributs pointant vers d'autres objets)

### Syntaxe de base

```bash
@attr=Type                    # L'attribut 'attr' pointe vers un objet de Type
@attr=Type.conditions         # Avec conditions sur l'objet cible
```

### Exemples

```bash
# Factures d'un client spécifique
read Facture.@client=Client.id=128

# Factures de clients espagnols
read Facture.@client=Client.country=ES

# Factures de clients espagnols OU femmes
read Facture.(@client=Client.country=ES|@client=Client.gender=F)

# Tâches dépendant d'un scénario Bootstrap
read Task.@depends_on=Scenario:Bootstrap
```

### Récursivité

```bash
@@attr=Type                   # Récursif (tous les niveaux jusqu'à --depth)

# Tous les descendants d'un objet
read *.@@parent=Object:Entity --depth=5
```

---

## 7. OPTIONS DE LECTURE

### Pagination

| Option | Description | Exemple |
|--------|-------------|---------|
| `--limit=N` | Limite à N résultats | `--limit=10` |
| `--offset=N` | Saute N résultats | `--offset=20` |
| `--page=N` | Page N (avec --per) | `--page=2` |
| `--per=N` | Résultats par page | `--per=20` |

```bash
# Page 2, 20 résultats par page
read Facture --page=2 --per=20

# Les 10 premiers résultats
read Agent --limit=10

# Résultats 21 à 30
read Agent --limit=10 --offset=20
```

### Tri

| Option | Description | Exemple |
|--------|-------------|---------|
| `--order=attr` | Tri ascendant | `--order=name` |
| `--order=-attr` | Tri descendant | `--order=-date` |
| `--order=a,-b` | Tri multiple | `--order=status,-priority` |

```bash
# Factures par montant décroissant
read Facture --order=-amount

# Tri multiple: par statut puis par date
read Task --order=status,-created_at
```

### Sélection de champs

```bash
--fields=a,b,c               # Champs à retourner
--fields=amount:total        # Renommer un champ (amount → total)

# Exemples
read Facture --fields=id,client,amount
read Agent --fields=name,status,priority:prio
```

### Profondeur de récursion

```bash
--depth=N                    # Profondeur pour relations récursives

# Défaut: valeur de config (superread.config.defaultDepth)
# Max: superread.config.maxDepth
```

---

## 8. OPTIONS D'AGRÉGATION

| Option | Description | Exemple |
|--------|-------------|---------|
| `--count` | Compte les résultats | `read Facture --count` |
| `--sum=attr` | Somme d'un attribut | `--sum=amount` |
| `--avg=attr` | Moyenne | `--avg=price` |
| `--min=attr` | Minimum | `--min=date` |
| `--max=attr` | Maximum | `--max=amount` |
| `--group=attr` | Grouper par | `--group=status` |
| `--distinct=attr` | Valeurs uniques | `--distinct=country` |

### Exemples

```bash
# Nombre de factures impayées
read Facture.paid=false --count

# Somme des factures par client
read Facture --group=client --sum=amount

# Moyenne des commandes par pays
read Order --group=country --avg=total

# Liste des pays distincts
read Client --distinct=country
```

---

## 9. EXPRESSIONS CONDITIONNELLES (CASE/WHEN)

### Syntaxe ternaire

```bash
{condition?valeurSiVrai:valeurSiFaux}
```

### Imbrication

```bash
{cond1?val1:{cond2?val2:valDefault}}
```

### Exemples

```bash
# Label de statut
read Facture --fields=id,amount,{paid=true?Payée:Impayée}:status_label

# Disponibilité produit
read Product --fields=name,{stock>100?En stock:{stock>0?Stock faible:Rupture}}:dispo

# Niveau de priorité
read Task --fields=name,{priority>8?Critique:{priority>5?Haute:{priority>2?Moyenne:Basse}}}:level
```

### Dans les updates

```bash
# Augmenter prix de 10%
update Product.category=electronics set price={price*1.1}

# Statut conditionnel
update Facture set status={paid=true?closed:{overdue=true?alert:pending}}

# Pénalité de retard (5%)
update Facture.overdue=true set penalty={amount*0.05}
```

---

## 10. OPTIONS UPDATE/DELETE

| Option | Description | Exemple |
|--------|-------------|---------|
| `--dry` | Simulation (n'exécute pas) | `update ... --dry` |
| `--cascade` | Supprime les dépendants | `delete ... --cascade` |
| `--limit=N` | Limite le nombre d'opérations | `--limit=100` |
| `--confirm` | Demande confirmation | `delete ... --confirm` |

### Exemples

```bash
# Simulation d'update
update Product.category=books set price={price*0.9} --dry

# Supprimer avec cascade
delete Client.id=123 --cascade

# Supprimer les 100 plus anciennes sessions
delete Session.expires_at<$now --order=expires_at --limit=100
```

---

## 11. JOINTURES (Inclusion d'objets liés)

### Syntaxe

```bash
++attr               # Inclure l'objet lié par 'attr'
++attr.subattr       # Inclure un sous-objet
++*                  # Inclure toutes les relations
```

### Exemples

```bash
# Factures avec données client
read Facture.paid=false ++client

# Retourne:
# { id, amount, paid, client: { id, name, country } }

# Factures avec client et produit
read Facture ++client ++product --fields=id,amount,client.name,product.name

# Tout inclure
read Order ++* --limit=10
```

---

## 12. SOUS-REQUÊTES

### Syntaxe

```bash
@(read ...)          # Utilise le résultat d'une sous-requête
```

### Exemples

```bash
# Factures de clients premium
read Facture.@client=@(read Client.tier=premium --fields=id)

# Équivalent SQL:
# SELECT * FROM Facture WHERE client IN (SELECT id FROM Client WHERE tier='premium')

# Produits jamais commandés
read Product.id!@@(read OrderLine --distinct=product_id)
```

---

## 13. ALIAS ET RENOMMAGE

```bash
--as:attr=newname              # Renommer dans le résultat
--fields=attr:alias            # Renommer inline
```

### Exemples

```bash
# Renommer amount en total
read Facture --fields=id,amount:total,client

# Plusieurs renommages
read Product --fields=name:product_name,price:unit_price,stock:quantity
```

---

## 14. CONFIGURATION

La configuration SuperRead est éditable via la commande `config`.

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `defaultDepth` | 2 | Profondeur récursion par défaut |
| `maxDepth` | 10 | Profondeur max autorisée |
| `defaultLimit` | 100 | Limite par défaut |
| `maxLimit` | 1000 | Limite max autorisée |
| `defaultPerPage` | 20 | Résultats par page par défaut |
| `timeout` | 5000 | Timeout en ms |
| `cacheEnabled` | true | Cache activé |
| `cacheTTL` | 60000 | TTL cache en ms |

### Commandes config

```bash
config                        # Voir toute la config
config defaultDepth           # Voir une valeur
config defaultDepth 5         # Modifier une valeur
```

---

## 15. EXEMPLES COMPLETS

### Lecture simple

```bash
# Tous les agents
read Agent

# Agents actifs
read Agent.status=active

# Agents actifs avec priorité >= 5
read Agent.status=active.priority>=5
```

### Lecture avec options

```bash
# Top 10 agents par priorité
read Agent.status=active --order=-priority --limit=10

# Page 2 des scénarios
read Scenario --page=2 --per=20 --order=name

# Compter les tâches en cours
read Task.status=pending --count
```

### Requêtes avec relations

```bash
# Factures de clients espagnols
read Facture.@client=Client.country=ES

# Factures impayées de décembre pour clients ES ou femmes
read Facture.paid=false.date>=2024-12-07.date<=2024-12-24.(@client=Client.country=ES|@client=Client.gender=F)

# Tâches dépendant d'un scénario Bootstrap
read Task.@depends_on=Scenario:Bootstrap.priority<10
```

### Updates

```bash
# Marquer factures comme payées
update Facture.id@123,456,789 set paid=true,paid_at=$now

# +10% sur électronique
update Product.category=electronics set price={price*1.1}

# Statut conditionnel
update Facture set status={paid=true?closed:{date<$today-30d?overdue:pending}}

# Simulation
update Client.country=FR set vat_rate=0.20 --dry
```

### Deletes

```bash
# Supprimer sessions expirées
delete Session.expires_at<$now

# Supprimer avec cascade (supprime aussi les factures liées)
delete Client.id=123 --cascade

# Supprimer les logs > 90 jours (avec confirmation)
delete Log.date<$today-90d --confirm
```

### Agrégations

```bash
# Total factures par client
read Facture --group=client --sum=amount

# Moyenne et count par pays
read Client --group=country --count --avg=revenue

# Valeurs distinctes
read Product --distinct=category
```

### Jointures et sous-requêtes

```bash
# Factures avec détails client
read Facture.paid=false ++client --fields=id,amount,client.name,client.email

# Clients sans factures
read Client.id!@@(read Facture --distinct=client)

# Produits du même fournisseur que le produit 123
read Product.@supplier=@(read Product.id=123 --fields=supplier)
```

---

## 16. RÉSUMÉ RAPIDE

```
read   Type.cond... [--options]           # Lire
create Type:Name attr=val...              # Créer
update Type.cond... set attr=val...       # Modifier
delete Type.cond...                       # Supprimer

Conditions:  .attr=val  .attr>val  .attr~val  .attr?
Logique:     .cond1.cond2 (AND)    (cond1|cond2) (OR)
Relations:   .@attr=Type.cond
Calculs:     {attr+val}  {attr*1.1}  {cond?a:b}
Dates:       $now  $today  $now-7d  $today+1w
Options:     --limit  --page  --order  --fields  --count  --group
Jointures:   ++attr
Sous-req:    @(read ...)
```

---

## Changelog

- **v1.0** (2024-12-12) : Version initiale complète
  - Opérations CRUD (read, create, update, delete)
  - Opérateurs de comparaison complets
  - Opérateurs logiques (AND, OR, NOT)
  - Arithmétique et dates relatives
  - Relations et récursivité
  - Expressions conditionnelles (ternaires)
  - Agrégations (count, sum, avg, group)
  - Jointures (++)
  - Sous-requêtes @()
  - Configuration éditable
