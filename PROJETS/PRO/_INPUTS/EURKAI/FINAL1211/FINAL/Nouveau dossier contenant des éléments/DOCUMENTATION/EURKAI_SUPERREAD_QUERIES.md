# EURKAI SuperRead - Documentation Complète des Queries

> **Version**: 1.0.0  
> **Date**: 2025-12-18  
> **Auteur**: laNostr'AI / EURKAI

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Syntaxe Générale](#2-syntaxe-générale)
3. [Opérateurs de Comparaison](#3-opérateurs-de-comparaison)
4. [Opérateurs Logiques](#4-opérateurs-logiques)
5. [Relations et Jointures](#5-relations-et-jointures)
6. [Variables Temporelles](#6-variables-temporelles)
7. [Options de Query](#7-options-de-query)
8. [Agrégations](#8-agrégations)
9. [Requêtes Récursives](#9-requêtes-récursives)
10. [Formules et Calculs](#10-formules-et-calculs)
11. [Exemples Avancés](#11-exemples-avancés)
12. [Référence Rapide](#12-référence-rapide)

---

## 1. Introduction

**SuperRead** est le langage de requête d'EURKAI permettant d'interroger, filtrer et manipuler les objets du store. Il s'inspire de la syntaxe SQL tout en étant adapté à l'architecture fractale d'EURKAI.

### Principes fondamentaux

- **Tout est Object** : Chaque entité est un objet avec un lineage
- **Lineage = Chemin d'héritage** : `Object:Entity:User:AdminUser`
- **Séparateur `:` = héritage vertical** (ancêtres → descendants)
- **Séparateur `.` = accès attribut/méthode**
- **Préfixe `V_` = Vecteur** (variable résolue dynamiquement)

### Commandes principales

| Commande | Description |
|----------|-------------|
| `read` | Lire/rechercher des objets |
| `get` | Récupérer un objet par lineage exact |
| `resolve` | Résoudre un vecteur |
| `tree` | Afficher l'arbre d'objets |
| `stats` | Statistiques du store |
| `vectors` | Lister tous les vecteurs |
| `rules` | Lister toutes les règles |

---

## 2. Syntaxe Générale

### Format de base

```
read <Type>[.<attr><op><val>]... [@<relation>=<Type>]... [OPTIONS]
```

### Composants

| Élément | Description | Exemple |
|---------|-------------|---------|
| `<Type>` | Type d'objet à rechercher | `Agent`, `Facture`, `Template` |
| `.<attr>` | Attribut à filtrer | `.status`, `.name`, `.priority` |
| `<op>` | Opérateur de comparaison | `=`, `>`, `~`, etc. |
| `<val>` | Valeur de comparaison | `active`, `5`, `Main` |
| `@<relation>` | Relation vers autre objet | `@client=Client` |
| `[OPTIONS]` | Options de requête | `--limit=10`, `--order=-date` |

### Exemples simples

```bash
# Tous les objets de type Agent
read Agent

# Agents avec status = active
read Agent.status=active

# Agents avec priorité >= 5
read Agent.priority>=5

# Agents dont le nom contient "Main"
read Agent.name~Main
```

---

## 3. Opérateurs de Comparaison

### Opérateurs d'égalité

| Opérateur | Signification | Exemple | SQL équivalent |
|-----------|---------------|---------|----------------|
| `=` | Égal à | `.status=active` | `WHERE status = 'active'` |
| `!=` | Différent de | `.status!=deleted` | `WHERE status != 'deleted'` |

### Opérateurs numériques

| Opérateur | Signification | Exemple | SQL équivalent |
|-----------|---------------|---------|----------------|
| `>` | Supérieur à | `.priority>5` | `WHERE priority > 5` |
| `>=` | Supérieur ou égal | `.priority>=5` | `WHERE priority >= 5` |
| `<` | Inférieur à | `.priority<10` | `WHERE priority < 10` |
| `<=` | Inférieur ou égal | `.priority<=10` | `WHERE priority <= 10` |

### Opérateurs de texte

| Opérateur | Signification | Exemple | SQL équivalent |
|-----------|---------------|---------|----------------|
| `~` | Contient | `.name~Main` | `WHERE name LIKE '%Main%'` |
| `^` | Commence par | `.name^Obj` | `WHERE name LIKE 'Obj%'` |
| `$` | Finit par | `.name$Template` | `WHERE name LIKE '%Template'` |

### Opérateurs de liste

| Opérateur | Signification | Exemple | SQL équivalent |
|-----------|---------------|---------|----------------|
| `@` | Dans la liste (IN) | `.status@[active,pending]` | `WHERE status IN ('active','pending')` |
| `!@` | Pas dans la liste | `.status!@[deleted,archived]` | `WHERE status NOT IN (...)` |

### Opérateurs d'existence

| Opérateur | Signification | Exemple | SQL équivalent |
|-----------|---------------|---------|----------------|
| `?` | Existe (NOT NULL) | `.email?` | `WHERE email IS NOT NULL` |
| `!?` | N'existe pas (NULL) | `.deleted_at!?` | `WHERE deleted_at IS NULL` |

---

## 4. Opérateurs Logiques

### Chaînage de conditions

| Opérateur | Signification | Exemple |
|-----------|---------------|---------|
| `.` | AND (entre attributs) | `.status=active.priority>5` |
| `\|` | OR (alternatives) | `.status=active\|.status=pending` |
| `()` | Groupement | `(.status=active\|.status=pending).priority>5` |

### Exemples

```bash
# AND implicite : agents actifs ET priorité > 5
read Agent.status=active.priority>5

# OR : agents actifs OU en attente
read Agent.status=active|.status=pending

# Groupement : (actifs OU pending) ET priorité > 5
read Agent(.status=active|.status=pending).priority>5

# Négation via !=
read Agent.status!=deleted.status!=archived
```

---

## 5. Relations et Jointures

### Relation simple `@attr=Type`

Permet de filtrer sur un attribut qui référence un autre objet.

```bash
# Factures du client dont l'ID = 128
read Facture.@client=Client.id=128

# Factures des clients espagnols
read Facture.@client=Client.country=ES

# Factures impayées des clients espagnols
read Facture.paid=false.@client=Client.country=ES
```

### Relation récursive `@@attr=Type`

Pour les relations parent-enfant récursives.

```bash
# Tous les descendants de Object:Entity
read *.@@parent=Object:Entity --depth=5

# Catégories et sous-catégories
read Category.@@parent=Category:Root --depth=10
```

### Jointures (Include) `++`

| Syntaxe | Description |
|---------|-------------|
| `++attr` | Inclure l'objet lié par l'attribut |
| `++*` | Inclure toutes les relations |
| `--attr` | Exclure un attribut |
| `--*` | Exclure toutes les relations |

```bash
# Factures avec le client inclus
read Facture.paid=false ++client

# Factures avec toutes les relations
read Facture ++*

# Commandes avec client et produits
read Order ++client ++productList

# Template avec ses éléments HTML
read Template:PageTemplate ++HTMLElementList
```

---

## 6. Variables Temporelles

### Variables de base

| Variable | Description | Exemple de valeur |
|----------|-------------|-------------------|
| `$now` | Date/heure actuelle | `2025-12-18T15:30:00` |
| `$today` | Date du jour à 00:00 | `2025-12-18T00:00:00` |
| `$yesterday` | Hier à 00:00 | `2025-12-17T00:00:00` |
| `$tomorrow` | Demain à 00:00 | `2025-12-19T00:00:00` |

### Arithmétique temporelle

| Suffixe | Unité | Exemple |
|---------|-------|---------|
| `s` | Secondes | `$now-30s` |
| `m` | Minutes | `$now-5m` |
| `h` | Heures | `$now-1h` |
| `d` | Jours | `$today-7d` |
| `w` | Semaines | `$today-2w` |
| `M` | Mois | `$today-1M` |
| `y` | Années | `$today-1y` |

### Exemples temporels

```bash
# Factures des 7 derniers jours
read Facture.date>=$today-7d

# Sessions expirées
read Session.expires_at<$now

# Modifications de la dernière heure
read *.updated_at>$now-1h --order=-updated_at

# Factures du mois en cours
read Facture.date>=$today-30d.date<=$today

# Tâches dues demain
read Task.due_date=$tomorrow
```

### Fonctions de date

| Fonction | Description | Exemple |
|----------|-------------|---------|
| `DATE('YYYY-MM-DD')` | Date spécifique | `DATE('2025-12-31')` |
| `DATETIME('...')` | DateTime spécifique | `DATETIME('2025-12-31T23:59:59')` |
| `YEAR($date)` | Extraire l'année | `YEAR($today)` |
| `MONTH($date)` | Extraire le mois | `MONTH($today)` |
| `DAY($date)` | Extraire le jour | `DAY($today)` |
| `WEEKDAY($date)` | Jour de la semaine (0-6) | `WEEKDAY($today)` |
| `WORKDAYS(d1, d2)` | Jours ouvrés entre 2 dates | `WORKDAYS($today, DATE('2025-12-31'))` |

---

## 7. Options de Query

### Pagination

| Option | Description | Exemple |
|--------|-------------|---------|
| `--limit=N` | Limiter à N résultats | `--limit=10` |
| `--offset=N` | Sauter N résultats | `--offset=20` |
| `--page=N` | Page N (avec --per) | `--page=2` |
| `--per=N` | Résultats par page | `--per=20` |

```bash
# 10 premiers résultats
read Facture --limit=10

# Page 3, 25 par page
read Facture --page=3 --per=25

# Offset manuel
read Facture --limit=25 --offset=50
```

### Tri

| Option | Description | Exemple |
|--------|-------------|---------|
| `--order=attr` | Tri ascendant | `--order=name` |
| `--order=-attr` | Tri descendant | `--order=-date` |
| `--order=a,-b` | Tri multiple | `--order=status,-priority` |

```bash
# Par nom A-Z
read Agent --order=name

# Par date décroissante
read Facture --order=-created_at

# Par statut puis priorité décroissante
read Task --order=status,-priority
```

### Sélection de champs

| Option | Description | Exemple |
|--------|-------------|---------|
| `--fields=a,b,c` | Champs à retourner | `--fields=id,name,status` |
| `--fields=a:alias` | Avec alias | `--fields=amount:total` |

```bash
# Seulement id et nom
read Agent --fields=id,name

# Avec alias
read Facture --fields=id,client,amount:total
```

### Options spéciales

| Option | Description | Exemple |
|--------|-------------|---------|
| `--depth=N` | Profondeur récursion | `--depth=5` |
| `--dry` | Simulation (n'exécute pas) | `--dry` |
| `--cascade` | Suppression en cascade | `--cascade` |
| `--explain` | Afficher le plan d'exécution | `--explain` |

---

## 8. Agrégations

### Fonctions d'agrégation

| Option | Description | Exemple |
|--------|-------------|---------|
| `--count` | Compter les résultats | `--count` |
| `--sum=attr` | Somme d'un attribut | `--sum=amount` |
| `--avg=attr` | Moyenne | `--avg=price` |
| `--min=attr` | Minimum | `--min=priority` |
| `--max=attr` | Maximum | `--max=priority` |
| `--distinct=attr` | Valeurs uniques | `--distinct=country` |

### Groupement

```bash
# Compte par statut
read Facture --group=status --count

# Total par client
read Facture --group=client --sum=amount

# Moyenne par pays
read Order --group=country --avg=total

# Compte et somme
read Facture --group=status --count --sum=amount
```

### Exemples d'agrégation

```bash
# Nombre total de factures impayées
read Facture.paid=false --count

# Montant total des factures
read Facture --sum=amount

# Top 10 clients par montant
read Facture --group=client --sum=amount --order=-amount --limit=10

# Pays distincts des clients
read Client --distinct=country

# Stats complètes par statut
read Facture --group=status --count --sum=amount --avg=amount
```

---

## 9. Requêtes Récursives

### Syntaxe de descendance

| Syntaxe | Description |
|---------|-------------|
| `:Type` | Descendants de Type (lineage commence par Type) |
| `Type:` | Ancêtres de Type |
| `Type:*` | Enfants directs de Type |
| `Type:**` | Tous les descendants (récursif) |

### Exemples

```bash
# Tous les descendants de Template
read :Template

# Tous les descendants de Object:Element
read :Object:Element

# Enfants directs de PageTemplate
read Object:Template:PageTemplate:*

# Recherche récursive avec profondeur
read :Template --depth=10

# Template avec tous ses éléments récursifs
read :Template:PageTemplate ++* --depth=10
```

### Navigation dans le lineage

```bash
# Objets dont le parent est Entity
read *.parent=Object:Entity

# Objets au niveau 3 du lineage
read *.lineage~:*:*:*

# Tous les objets "List"
read *List
```

---

## 10. Formules et Calculs

### Opérateurs arithmétiques

| Opérateur | Description | Exemple |
|-----------|-------------|---------|
| `+` | Addition | `{price+tax}` |
| `-` | Soustraction | `{total-discount}` |
| `*` | Multiplication | `{quantity*price}` |
| `/` | Division | `{total/count}` |
| `%` | Modulo | `{index%2}` |

### Expressions dans les valeurs

```bash
# Produits avec marge > 20%
read Product.{(price-cost)/price*100}>20

# Mise à jour avec calcul (simulation)
update Product set price={price*1.1} --dry

# Factures avec montant HT calculé
read Facture --fields=id,amount,{amount/1.2}:amount_ht
```

### Expressions conditionnelles (ternaires)

```bash
# Syntaxe : {condition?valeurVrai:valeurFaux}

# Statut textuel
read Facture --fields=id,{paid=true?Payée:Impayée}:statut

# Ternaires imbriqués
read Product --fields=name,{stock>100?En stock:{stock>0?Stock faible:Rupture}}:disponibilite

# Priorité textuelle
read Task --fields=name,{priority>7?Urgent:{priority>4?Normal:Basse}}:niveau
```

---

## 11. Exemples Avancés

### Requêtes métier

```bash
# Factures en retard de paiement
read Facture.paid=false.due_date<$today

# Clients sans commande depuis 30 jours
read Client.@@orders=Order.date<$today-30d!?

# Produits populaires du mois
read Product.@@orders=Order.date>=$today-30d --group=id --count --order=-count --limit=10

# Agents disponibles avec compétence Python
read Agent.status=available.@skills=Skill.name=Python

# Tâches urgentes assignées à moi
read Task.priority>=8.@assignee=User.id=$currentUser
```

### Requêtes pour Templates (cas d'usage EURKAI)

```bash
# Template de page avec tous ses éléments
read Template:PageTemplate ++HeadElement ++BodyElement ++SectionList --depth=5

# Éléments HTML d'un template spécifique
read :HTMLElement.@template=Template:PageTemplate:HomePage

# Tous les composants utilisés dans les templates
read :Component.@@parent=Template --distinct=type

# Structure complète d'une page
read Template:PageTemplate:HomePage ++* --depth=10 --fields=lineage,tag,attrs,children
```

### Requêtes de maintenance

```bash
# Objets modifiés aujourd'hui
read *.updated_at>=$today --order=-updated_at

# Objets orphelins (sans parent valide)
read *.parent!?

# Doublons potentiels
read *.name --group=name --count --having=count>1

# Objets avec erreurs de validation
read *.@validation=ValidationResult.status=error
```

---

## 12. Référence Rapide

### Cheat Sheet

```
╔══════════════════════════════════════════════════════════════════╗
║                    SUPERREAD CHEAT SHEET                        ║
╠══════════════════════════════════════════════════════════════════╣
║ COMPARAISON                                                      ║
║   =  !=  >  >=  <  <=  ~  ^  $  @  !@  ?  !?                    ║
╠══════════════════════════════════════════════════════════════════╣
║ LOGIQUE                                                          ║
║   .    AND entre conditions                                      ║
║   |    OR entre conditions                                       ║
║   ()   Groupement                                                ║
╠══════════════════════════════════════════════════════════════════╣
║ RELATIONS                                                        ║
║   @attr=Type      Relation simple                                ║
║   @@attr=Type     Relation récursive                             ║
║   ++attr          Include relation                               ║
║   ++*             Include toutes relations                       ║
╠══════════════════════════════════════════════════════════════════╣
║ TEMPS                                                            ║
║   $now  $today  $yesterday  $tomorrow                            ║
║   $now-7d  $today+1M  $now-1h                                    ║
╠══════════════════════════════════════════════════════════════════╣
║ OPTIONS                                                          ║
║   --limit=N  --offset=N  --page=N  --per=N                       ║
║   --order=attr  --order=-attr                                    ║
║   --fields=a,b,c  --depth=N                                      ║
║   --count  --sum=  --avg=  --min=  --max=                        ║
║   --group=  --distinct=  --dry  --cascade                        ║
╠══════════════════════════════════════════════════════════════════╣
║ LINEAGE                                                          ║
║   :Type           Descendants de Type                            ║
║   Type:*          Enfants directs                                ║
║   Type:**         Tous descendants                               ║
╠══════════════════════════════════════════════════════════════════╣
║ CALCULS                                                          ║
║   {a+b}  {a-b}  {a*b}  {a/b}  {a%b}                              ║
║   {cond?vrai:faux}  Ternaire                                     ║
╚══════════════════════════════════════════════════════════════════╝
```

### Exemples par cas d'usage

| Cas d'usage | Query |
|-------------|-------|
| Liste simple | `read Agent` |
| Filtre égalité | `read Agent.status=active` |
| Filtre numérique | `read Agent.priority>=5` |
| Filtre texte | `read Agent.name~Main` |
| Multi-filtres | `read Agent.status=active.priority>5` |
| Avec relation | `read Facture.@client=Client.country=ES` |
| Avec jointure | `read Facture ++client` |
| Paginé | `read Facture --page=2 --per=20` |
| Trié | `read Facture --order=-date` |
| Agrégé | `read Facture --group=status --count` |
| Temporel | `read Facture.date>=$today-7d` |
| Récursif | `read :Template --depth=10` |

---

## Annexes

### A. Correspondance SQL

| SuperRead | SQL |
|-----------|-----|
| `read Type` | `SELECT * FROM Type` |
| `.attr=val` | `WHERE attr = 'val'` |
| `.attr>val` | `WHERE attr > val` |
| `.attr~val` | `WHERE attr LIKE '%val%'` |
| `--limit=10` | `LIMIT 10` |
| `--offset=20` | `OFFSET 20` |
| `--order=attr` | `ORDER BY attr ASC` |
| `--order=-attr` | `ORDER BY attr DESC` |
| `--count` | `SELECT COUNT(*)` |
| `--group=attr` | `GROUP BY attr` |
| `@rel=Type` | `JOIN Type ON ...` |

### B. Types de données supportés

| Type | Format | Exemple |
|------|--------|---------|
| String | `"texte"` ou `texte` | `status=active` |
| Number | entier ou décimal | `priority=5`, `price=19.99` |
| Boolean | `true` / `false` | `paid=true` |
| Date | ISO 8601 | `date=2025-12-18` |
| DateTime | ISO 8601 | `created_at=2025-12-18T15:30:00` |
| Array | `[a,b,c]` | `status@[active,pending]` |
| Null | `null` ou `!?` | `.deleted_at!?` |

### C. Codes d'erreur

| Code | Description |
|------|-------------|
| `E001` | Syntaxe invalide |
| `E002` | Type inconnu |
| `E003` | Attribut inexistant |
| `E004` | Opérateur non supporté |
| `E005` | Relation invalide |
| `E006` | Profondeur maximale atteinte |
| `E007` | Timeout de requête |

---

*Documentation générée pour EURKAI v1.0 - laNostr'AI*
