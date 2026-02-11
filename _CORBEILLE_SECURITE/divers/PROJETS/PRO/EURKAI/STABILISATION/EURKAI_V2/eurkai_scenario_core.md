# EURKAI – Cœur du scénario (V2)

## Objectif du document

Ce document formalise le **fonctionnement réel, validé et opérationnel** du moteur de scénario EURKAI V2, tel qu’il a été implémenté et testé.

Il constitue une **documentation de référence** destinée à être :
- archivée
- liée dans le suivi des tâches
- utilisée comme socle conceptuel pour les évolutions futures (ObjectStore, persistance, replay, etc.)

---

## 1. Positionnement du scénario dans EURKAI

Le scénario EURKAI n’est **ni** un script linéaire, **ni** un workflow figé.

Il est :
> un **moteur d’orchestration générique**, piloté par des hooks, capable de traiter des cibles hétérogènes (Objects, GEVLines, etc.), avec validation, rendu et gestion contrôlée de l’échec.

Il constitue :
- le cœur d’exécution du système
- la colonne vertébrale de propagation
- le point de convergence entre données, règles et actions

---

## 2. Architecture générale du scénario

### Séquence invariante

Un scénario EURKAI suit **toujours** la séquence suivante :

```
scenario.start
  └─ hookbefore
      └─ hookget
          └─ hookexecute
              └─ hookvalidate
                  ├─ hookrender (si valid)
                  └─ hookfailure (si invalid)
  └─ hookafter
scenario.end
```

Cette séquence est **structurellement invariante**.

- Les hooks sont optionnels
- L’ordre ne l’est jamais
- Aucun scénario ne peut court-circuiter une phase

---

## 3. Les hooks – rôles et responsabilités

### 3.1 hookbefore

- Initialisation
- Log de démarrage
- Injection de contexte éventuelle
- Aucun effet métier obligatoire

---

### 3.2 hookget – Résolution des cibles

Responsabilité centrale :
> produire une **targetlist normalisée**

Sources possibles :
- requête vectorielle
- walker relationnel
- lecture GEV (`gev_read_minimal`)
- combinaison de sources

Garanties :
- chaque target possède `id`, `type`
- `state.defined = True`

---

### 3.3 hookexecute – Action

Responsabilité :
> appliquer une action à chaque cible

Caractéristiques :
- itératif
- sans état au niveau du scénario
- chaque target retourne :
  - `success`
  - `state.resolved`
  - `state.executed`

Le scénario orchestre l’exécution mais ne porte **aucune logique métier**.

---

### 3.4 hookvalidate – Décision

Responsabilité critique :
> décider si le scénario est valide ou invalide

- retourne `valid = True | False`
- peut être forcé (`force_fail`)
- aucun effet secondaire autorisé

C’est **l’unique point de bifurcation** du scénario.

---

### 3.5 hookrender – Succès

- exécuté uniquement si `valid=True`
- produit un output structuré
- ne modifie pas l’état métier

---

### 3.6 hookfailure – Échec contrôlé

- exécuté uniquement si `valid=False`
- produit une structure de failure
- le process Python ne crash jamais

Échec métier ≠ erreur technique.

---

### 3.7 hookafter

- nettoyage
- log final
- aucune logique métier

---

## 4. Walker & parcours relationnel

Le walker permet un parcours :
- déclaratif
- borné (`depth`, `area`, `limit`)
- traçable (`expanded_count`)

Garanties validées :
- pas de boucle infinie
- expansion contrôlée

Le walker est **consommé** par le scénario, jamais implémenté par lui.

---

## 5. Mode GEV (Graph Execution Vocabulary)

Le mode GEV introduit :
- une source textuelle structurée
- une lecture minimaliste
- une transformation directe en targetlist

Chaque ligne GEV devient une cible standard.

GEV est une **source**, pas un moteur distinct.

---

## 6. Logging – séparation stricte

### Logs process
- stdout / stderr
- vides en cas de succès
- réservés aux erreurs techniques

### Logs applicatifs
- `run.log`
- traçage métier
- séquentiel, stable, lisible

Invariant validé par les tests.

---

## 7. Validation par les tests

Les tests `chaintest_*` démontrent que :
- le scénario est exécutable en module
- SUCCESS et FAILURE sont stables
- aucun test ne pollue stderr
- le moteur ne crash jamais sur un échec métier

Ce socle est **définitivement validé**.

---

## 8. Invariants à ne jamais casser

1. Le scénario orchestre, il ne décide pas
2. La targetlist est l’unité centrale
3. `hookvalidate` est l’unique point de décision
4. Échec ≠ exception
5. La séquence est invariante
6. Le scénario est indépendant du storage

---

## 9. Conséquence directe

Ce socle permet l’introduction d’un ObjectStore **sans refonte du scénario**.

L’ObjectStore deviendra une implémentation branchée sur :
- hookget
- hookexecute
- hookrender

Le cœur du scénario est prêt.

