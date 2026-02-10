# Tests de départ — T1 / T2 / T3 (Vue d’ensemble)

Objectif : voir Eurkai “bouger” pour la première fois, sans tout déployer, en testant le noyau logique et le cockpit.

---

## 🔹 T1 — Demo locale (JSON statique)

But :
- Vérifier que `object_fractal_tool_v4.html` affiche correctement un petit univers d’objets.

À faire :
1. Créer un fichier JSON d’exemple avec :
   - `Object`
   - `Object:Prompt`
   - `Object:Response`
   - 1–2 règles ERK associées (en texte pour l’instant)
2. Brancher ce JSON sur l’outil fractal (en local)
3. Tester :
   - sélection d’un objet
   - affichage de ses attributs / méthodes / règles
   - affichage visuel de l’héritage (lineage)

Validation :
- Tu vois l’arbre + la fractale pour 2–3 objets
- Tu peux naviguer entre eux sans erreur.

---

## 🔹 T2 — Backend mock (in-memory)

But :
- Remplacer le JSON statique par un backend léger (données en mémoire).

Endpoints minimalistes :
- `GET /objects`
- `GET /object/{id}`
- `POST /object` (création / mise à jour simulée)

À tester :
- Le cockpit lit la liste d’objets depuis le backend
- Quand tu ajoutes un objet dans l’interface, il apparaît dans l’arbre
- Pas encore de vraie base, juste un “faux serveur”.

Validation :
- Cycle base : créer → voir → modifier → voir → supprimer (si prévu).

---

## 🔹 T3 — 1 scénario GEVR minimal

But :
- Tester la boucle GEVR de bout en bout.

Exemple de scénario :
- “Créer un type d’objet + 2 enfants”

Étapes :
1. `GET` : l’état initial (aucun enfant)
2. `EXECUTE` : scène de création (Object:ChildA, Object:ChildB)
3. `VALIDATE` : vérification simple (noms non vides)
4. `RENDER` : renvoi du nouvel état à l’interface

À faire :
- Implémenter ce scénario dans le backend mock
- Ajouter un bouton dans le cockpit “Exécuter scénario test”
- Observer la mise à jour de l’arbre + de la fractale

Validation :
- Avant : seulement `Object`
- Après : `Object:ChildA` et `Object:ChildB` apparaissent, avec héritage correct.

---

Une fois T1/T2/T3 validés :
- tu as une première vision concrète du système
- tu peux commencer à ajouter toi-même :
  - de nouveaux objets
  - de nouvelles règles ERK
  - de nouveaux scénarios
  via le cockpit, de manière progressive et contrôlée.
