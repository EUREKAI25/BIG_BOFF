# EURKAI — Architecture MVP (stable)

> Document de référence. Ne pas modifier sans validation.
> Date : 2026-03-16

---

## 1. Chaîne Product

```
Idea → Brief → CCharges → Spec → MVP → Product
```

- **Product** : tout objet produit par l'agence via ce pipeline (pas forcément public ou commercialisé)
- **CCharges** : étape obligatoire entre Brief et Spec — nom provisoire, sera stabilisé plus tard
- On peut s'arrêter à n'importe quelle étape (ex : livrer seulement CCharges)
- Chaque étape est un objet typé avec ses propres conditions de complétude

---

## 2. Noms validés

| Nom | Rôle |
|---|---|
| `Idea` | Point d'entrée — intention non structurée |
| `Brief` | Cadrage du problème et des objectifs |
| `CCharges` | Spécification fonctionnelle intermédiaire (nom provisoire) |
| `Spec` | Spécification technique complète |
| `MVP` | Livrable minimal fonctionnel |
| `Product` | Objet final produit par la chaîne |
| `conversational_module` | Module de conversation guidée (voir §3) |

Règles :
- Pas de pluriels
- `Requirement` non utilisé pour l'instant

---

## 3. conversational_module

Module indépendant, réutilisable, paramétrable.

**Paramètres injectés par le consommateur :**
- `system_prompt` — comportement de l'agent
- `checklist` — points à établir
- `output_schema` — structure JSON attendue en sortie

**Cas d'usage (non exhaustif) :**
- cadrage / brief produit
- onboarding client
- brainstorming
- prospection
- meeting structuré
- génération assistée

Le module ne connaît pas la chaîne Product. Il produit un JSON et s'arrête.

---

## 4. Structure minimale de Brief

```
Brief {
    summary            // Résumé en 1-2 phrases
    problem            // Problème à résoudre
    goal               // Objectif du projet
    user_goal          // Ce que l'utilisateur veut accomplir
    validation_criteria // Comment on sait que c'est réussi
    target_users       // Qui sont les utilisateurs
    value_proposition  // Pourquoi ce produit, pourquoi maintenant
}
```

Convention pour chaque élément :

```
element {
    definition   // Ce que c'est
    rules        // Contraintes / ce qui le rend valide
    options      // Variantes possibles (si applicable)
}
```

---

## 5. Règle d'arrêt de récursivité (MVP)

**Principe :** la complétude est évaluée par type d'objet, pas globalement.

### Brief — condition de complétude

Tous les champs suivants sont renseignés et non vides :
`summary`, `problem`, `goal`, `user_goal`, `validation_criteria`, `target_users`, `value_proposition`

### CCharges — condition de complétude

Les éléments suivants sont présents :
- liste des fonctionnalités (au moins MVP vs NEXT distingués)
- utilisateurs cibles confirmés
- contraintes identifiées (hébergement, budget, délai — même si "non précisé")
- stack ou type de produit validé

### Spec — condition de complétude

Les éléments suivants sont présents :
- architecture technique définie (composants, interfaces)
- schéma de données (même partiel)
- endpoints ou contrats d'interface listés
- critères d'acceptance par fonctionnalité MVP

**Règle d'arrêt :**
- on teste la complétude sur l'objet courant uniquement
- dès que le test passe → on livre et on s'arrête
- on ne teste pas les autres branches / étapes

---

## 6. Util

Un util est fonctionnellement traité comme un module au runtime.

Mais il reste catalogué explicitement comme util :

```json
{
  "type": "util"       // et non "family": "util"
}
```

- **Runtime** : importable et appelable comme un module
- **Catalogue** : distingué des modules — `type = util` obligatoire
- Un util n'a pas vocation à évoluer en module sans décision explicite

---

## 7. Fin de conversation

**Condition de complétude :** définie par le type d'objet (voir §5)

**Condition d'arrêt :**
> Le module s'arrête dès que le JSON attendu pour l'objet courant est complet et validé.

**Output livré :**
- le JSON de l'objet (Brief, CCharges, Spec, ou autre)
- sauvegardé à l'emplacement défini par le consommateur

**Ce qui n'appartient pas au module :**
- décider de la prochaine étape
- enchaîner sur l'étape suivante
- évaluer la complétude globale du projet

Le passage à l'étape suivante appartient au scénario global (orchestrateur ou décision humaine).
