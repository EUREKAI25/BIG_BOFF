# FORMAT GÉNÉRAL
read <Type>[.<attr><op><val>]... [<relation>=<Type>[.<attr><op><val>]...]... [OPTIONS]

# OPÉRATEURS DE COMPARAISON
=      égal
!=     différent
>      supérieur
>=     supérieur ou égal
<      inférieur
<=     inférieur ou égal
~      contient (LIKE %val%)
^      commence par (LIKE val%)
$      finit par (LIKE %val)
@      dans liste (IN)
!@     pas dans liste (NOT IN)
?      existe (IS NOT NULL)
!?     n'existe pas (IS NULL)

# OPÉRATEURS LOGIQUES
.      AND (entre attributs du même type)
|      OR (entre conditions alternatives)
()     groupement

# OPÉRATEURS ARITHMÉTIQUES (dans les valeurs)
+      addition
-      soustraction
*      multiplication
/      division
%      modulo
$now   date courante
$today date du jour (00:00)

# RELATIONS (attributs qui pointent vers d'autres objets)
@attr=Type[.conditions]    l'attribut 'attr' pointe vers Type

# OPTIONS
--limit=N          limite à N résultats
--offset=N         saute N résultats
--page=N           page N (avec --per=)
--per=N            résultats par page
--order=attr       tri par attribut (ASC par défaut)
--order=-attr      tri descendant
--count            retourne uniquement le compte
--fields=a,b,c     sélectionne les champs à retourner
--depth=N          profondeur de récursion pour relations

##############
# READ (déjà implémenté)
read Type.conditions... [--options]

# UPDATE
update Type.conditions... set attr=val,attr2=val2 [--dry]

# DELETE  
delete Type.conditions... [--dry] [--cascade]

# CREATE (déjà implémenté via 'create')
create Type:Name attr=val attr2=val2

conditionnelles
# Syntaxe: {condition?valeurSiVrai:valeurSiFaux}
# Imbriqué: {cond1?val1:{cond2?val2:valDefault}}

# Exemples:
read Facture --fields=id,amount,{paid=true?Payée:Impayée}:status_label

# Avec calcul
read Product --fields=name,{stock>100?En stock:{stock>0?Stock faible:Rupture}}:availability

# Dans un update
update Product.category=electronics set price={price*1.1}  # +10%
update Facture.overdue=true set penalty={amount*0.05}      # 5% pénalité

# Conditonnel dans update
update Facture set status={paid=true?closed:{overdue=true?alert:pending}}

agrégatins
# Comptage
read Facture.paid=false --count

# Groupement
read Facture --group=client --count
read Facture --group=status --sum=amount

# Agrégations disponibles
--count              # Nombre
--sum=field          # Somme
--avg=field          # Moyenne
--min=field          # Minimum
--max=field          # Maximum
--distinct=field     # Valeurs uniques

# SUPERREAD DSL — Complément v1.1
## Plages, Dates et Devises

---

## 17. PLAGES DE VALEURS


### Syntaxe

```
[min..max]                    Plage simple
[min..max].operation          Avec opération
[min..max].op1.op2.op3        Chaînage d'opérations
[..max]                       Sans borne min
[min..]                       Sans borne max
```

### Exemples

```
.date=[$today..20251212]
.date=[2024-12-07..12 décembre 25]
.amount=[100€..500€]
.amount=[100$..500 euros]
.priority=[1..5]
```

---

## 18. FORMATS DE DATE ACCEPTÉS

Tous les formats sont automatiquement normalisés en timestamp.

| Format | Exemple |
|--------|---------|
| ISO | 2025-12-12, 2025-12-12T10:30:00 |
| YYYYMMDD | 20251212 |
| Européen | 12/12/2025, 12-12-2025 |
| Français | 12 décembre 2025, 12 décembre 25, 1er janvier 2025 |
| Anglais | December 12, 2025, Dec 12 2025 |
| Variable | $now, $today, $yesterday, $tomorrow |
| Relatif | $today-7d, $now+30d, $today+2w |
| Expression | next week, last month, in 3 day |
| Jour | next monday, last friday |

### Unités de temps

| Unité | Code |
|-------|------|
| Seconde | s |
| Minute | m |
| Heure | h |
| Jour | d |
| Semaine | w |
| Mois | M |
| Année | y |

---

## 19. FORMATS MONÉTAIRES ACCEPTÉS

Tous les formats sont normalisés en centimes avec devise.

| Format | Exemple |
|--------|---------|
| Symbole | 100€, $500, £200 |
| Nom | 100 euros, 500 dollars, 200 pounds |
| Code | 100 EUR, 500 USD |
| Multiplicateur | 1.5k€, 2M$, 500K |
| Mixte | 1.5k euros, 2M dollars |

### Devises supportées

EUR, USD, GBP, CHF, JPY, et devises historiques (DEM, FRF, ESP...).

Les taux de conversion sont récupérés via API externe (configurable).
En cas d'indisponibilité, le dernier taux connu (historique) est utilisé.

---

## 20. OPÉRATIONS SUR PLAGES DE DATES

### Comptages

| Opération | Description |
|-----------|-------------|
| `.day` | Nombre de jours |
| `.hour` | Nombre d'heures (jours × 24) |
| `.minute` | Nombre de minutes |
| `.hourExact` | Heures exactes (pour $now vers minuit) |
| `.minuteExact` | Minutes exactes |

### Jours ouvrés et fériés

| Opération | Description |
|-----------|-------------|
| `.businessDay` | Jours ouvrés (excl. weekend + fériés) |
| `.businessHour` | Heures ouvrées (selon pays, source officielle) |
| `.weekend` | Jours de weekend |
| `.holiday` | Jours fériés (via API par pays) |

### Filtres par jour

| Opération | Description |
|-----------|-------------|
| `.monday` | Tous les lundis |
| `.tuesday` | Tous les mardis |
| `.wednesday` | Tous les mercredis |
| `.thursday` | Tous les jeudis |
| `.friday` | Tous les vendredis |
| `.saturday` | Tous les samedis |
| `.sunday` | Tous les dimanches |
| `.filter(mon,wed,fri)` | Jours spécifiques |

### Filtres avancés

| Opération | Description |
|-----------|-------------|
| `.oddDay` | Jours impairs (1, 3, 5...) |
| `.evenDay` | Jours pairs (2, 4, 6...) |
| `.nthWeekday(2,monday)` | 2ème lundi de chaque mois |
| `.dayOfMonth(12)` | Tous les 12 du mois |
| `.leapYear` | Années bissextiles uniquement |

### Finalisation

| Opération | Description |
|-----------|-------------|
| `.count` | Nombre de résultats |
| `.list` | Liste des dates |
| `.first` | Première date |
| `.last` | Dernière date |

---

## 21. OPÉRATIONS SUR PLAGES MONÉTAIRES

| Opération | Description |
|-----------|-------------|
| `.inEUR` | Convertir en EUR |
| `.inUSD` | Convertir en USD |
| `.inGBP` | Convertir en GBP |
| `.in{CODE}` | Convertir en devise CODE |

---

## 22. EXEMPLES DE PLAGES

### Dates

```
# Factures de décembre
.date=[2024-12-01..2024-12-31]

# 7 derniers jours
.date=[$today-7d..$today]

# Jusqu'à la semaine prochaine
.date=[..next week]

# À partir d'aujourd'hui
.date=[$today..]

# Nombre de jours ouvrés en 2025
[$today..2025-12-31].businessDay.count

# Tous les 2ème mardis du mois en 2025
[2025-01-01..2025-12-31].nthWeekday(2,tuesday)

# Tous les 15 du mois
[2025-01-01..2025-12-31].dayOfMonth(15)

# Heures exactes de maintenant à minuit
[$now..$tomorrow].hourExact

# Jours fériés en France cette année
[$today..$today+1y].holiday

# Heures ouvrées (selon pays du projet)
[$today..$today+30d].businessHour
```

### Montants

```
# Entre 100€ et 500€
.amount=[100€..500€]

# Plus de 1000$ converti en EUR
.amount=[1000$..].inEUR

# Entre 100 et 500 (devise projet)
.amount=[100..500]
```

### Combinaisons

```
# Factures impayées des 30 derniers jours > 500€
read Facture.paid=false.date=[$today-30d..$today].amount=[500€..]

# RDV les lundis et mercredis du mois prochain
read RDV.date=[next month].filter(monday,wednesday)

# Tous les 2 mars des années bissextiles
[2000-01-01..2100-12-31].leapYear.dayOfMonth(2).filter(march)

# 23. CONFIGURATION PROJET

La configuration définit le contexte du projet client (pas d'EUREKAI).

### Paramètres

| Clé | Description | Exemple |
|-----|-------------|---------|
| `locale` | Langue du projet | fr-FR, es-ES |
| `country` | Pays du projet | FR, ES, US |
| `currency` | Devise de référence | EUR, USD |
| `timezone` | Fuseau horaire | Europe/Paris |

### APIs externes

| API | Usage |
|-----|-------|
| `currency` | Taux de change (exchangerate-api, fixer...) |
| `holiday` | Jours fériés par pays (nager.date) |
| `businessHour` | Heures ouvrées officielles (OCDE) |

### Heures ouvrées par pays (source OCDE/Eurostat)

| Pays | Annuelles | Hebdo | Journalières |
|------|-----------|-------|--------------|
| FR | 1607 | 35 | 7 |
| ES | 1691 | 40 | 8 |
| DE | 1349 | 34.2 | 6.84 |
| US | 1791 | 38.7 | 7.74 |
| UK | 1538 | 36.4 | 7.28 |

### Commande

```
config project.locale es-ES
config project.country ES
config project.currency USD
```

---

## 24. CHANGELOG

- **v1.1** (2024-12-12)
  - Plages de valeurs [min..max]
  - Normalisation universelle des dates (tous formats)
  - Normalisation des devises avec conversion
  - Opérations sur plages (.businessDay, .nthWeekday, .leapYear...)
  - Heures exactes (.hourExact, .minuteExact)
  - Configuration projet (locale, country, currency)
  - APIs externes configurables (currency, holiday, businessHour)
  - Fallback sur historique des taux si API down
