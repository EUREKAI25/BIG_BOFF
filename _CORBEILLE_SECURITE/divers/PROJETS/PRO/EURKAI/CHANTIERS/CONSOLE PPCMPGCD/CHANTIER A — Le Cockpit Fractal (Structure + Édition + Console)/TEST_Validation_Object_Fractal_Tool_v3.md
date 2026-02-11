# Object Fractal Tool v3 — Plan de tests & Validation

## Vue d'ensemble

Ce document liste les tests à effectuer pour valider chaque étape ainsi que le fonctionnement global de l'outil.

---

## Étape 01 — Explorateur de lineages

### T01.1 — Affichage de l'arbre
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Arbre initial | Ouvrir l'outil | Voir `Object` avec enfants `Core`, `Entity`, `Schema` dépliés | ☐ |
| Hiérarchie complète | Déplier `Object:Entity` | Voir `Agent`, `Resource` | ☐ |
| Déplier Agent | Cliquer sur chevron | Voir `AIAgent`, `HumanAgent` | ☐ |

### T01.2 — Sélection
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Sélection simple | Cliquer sur `Entity` | Nœud surligné, vue fractale mise à jour | ☐ |
| Changement sélection | Cliquer sur `Agent` | Nouvelle sélection, fractale mise à jour | ☐ |

### T01.3 — Création d'ObjectTypes
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer racine | Saisir `Foo` + Entrée | `Foo` apparaît comme racine | ☐ |
| Créer enfant existant | Saisir `Object:Entity:User` + Entrée | `User` créé sous `Object:Entity` | ☐ |
| Créer chaîne complète | Saisir `Bar:Baz:Qux` + Entrée | 3 objets créés, toast "3 ObjectType(s) créé(s)" | ☐ |
| Rattachement | Saisir `Entity:Test` + Entrée | Modal "Rattacher à Object:Entity ?" | ☐ |
| Rattachement accepté | Confirmer le modal | `Test` créé sous `Object:Entity` | ☐ |
| Rattachement refusé | Annuler le modal | `Entity:Test` créé comme nouvelle branche | ☐ |
| Validation lineage | Saisir `invalid-name` | Input rouge, toast "Lineage invalide" | ☐ |

### T01.4 — Re-parenting (drag & drop)
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Déplacer objet | Drag `Resource` sur `Core` | `Resource` devient `Object:Core:Resource` | ☐ |
| Blocage circulaire | Drag `Entity` sur `Agent` | Toast "Impossible de déplacer sous un descendant" | ☐ |

### T01.5 — Suppression
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Supprimer feuille | Bouton 🗑 sur `HumanAgent` | Modal de confirmation, suppression | ☐ |
| Supprimer avec enfants | Bouton 🗑 sur `Agent` | Modal listant enfants, suppression cascade | ☐ |
| Supprimer avec relations | Bouton 🗑 sur objet avec relations entrantes | Modal listant relations, nettoyage | ☐ |

---

## Étape 02 — Tags, catégories, alias

### T02.1 — Gestion des tags
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer tag | Saisir `test-tag` + Entrée dans sidebar | Tag apparaît dans la liste | ☐ |
| Supprimer tag | Clic droit → Supprimer | Tag supprimé, retiré des objets | ☐ |
| Toggle catégorie | Clic droit → Catégorie | Style changé (background coloré) | ☐ |

### T02.2 — Attribution de tags
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Via bouton + | Clic `+` sur nœud → sélectionner tag | Tag ajouté, points colorés visibles | ☐ |
| Via drag & drop (arbre) | Drag tag sur nœud arbre | Tag ajouté | ☐ |
| Via drag & drop (carte) | Drag tag sur carte fractale | Tag ajouté | ☐ |
| Retirer tag | Clic `×` sur tag dans carte | Tag retiré | ☐ |

### T02.3 — Alias
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer alias | Saisir nom dans input alias + Entrée | Alias créé, affiché dans carte | ☐ |
| Supprimer alias | Clic `×` sur alias | Alias supprimé | ☐ |

---

## Étape 03 — Éditeur de schémas

### T03.1 — Ajout d'attributs
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Ouvrir formulaire | Clic `+ Attribut` | Formulaire inline apparaît | ☐ |
| Créer attribut | Remplir nom="test", type="string" + Enregistrer | Attribut vert ajouté | ☐ |
| Attribut required | Cocher "required" | Attribut créé avec required=true | ☐ |
| Doublon | Créer attribut avec nom existant | Toast "existe déjà" | ☐ |

### T03.2 — Ajout de méthodes
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer méthode | `+ Méthode`, nom="doSomething", signature="(): void" | Méthode verte ajoutée | ☐ |

### T03.3 — Ajout de relations
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer relation | `+ Relation`, type="depends_on", target="Object:Core" | Relation ajoutée | ☐ |
| Relation vers inexistant | Target="Inexistant" | Créée mais marquée ⚠ dans vecteurs | ☐ |

### T03.4 — Ajout de règles
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Créer règle enable | Condition="this.x != null", action="enable", target="this.y" | Règle ajoutée | ☐ |
| Créer règle require | action="require" | Règle affichée | ☐ |
| Créer règle kill | action="kill" | Règle affichée | ☐ |

### T03.5 — Édition et suppression
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Éditer attribut | Clic sur attribut owned | Formulaire pré-rempli | ☐ |
| Modifier et sauver | Changer type + Enregistrer | Modification appliquée | ☐ |
| Supprimer élément | Clic `×` sur élément owned | Élément supprimé | ☐ |

### T03.6 — Héritage dynamique
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Propagation | Ajouter attr "foo" à `Object:Entity` | Visible en bleu sur `Agent`, `AIAgent`, etc. | ☐ |
| Source affichée | Regarder attr hérité | `← Object:Entity` affiché | ☐ |

### T03.7 — Catalogue
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Instancier | Clic "Instancier pour le catalogue" | Instance créée avec ID | ☐ |
| Supprimer instance | Clic `×` sur instance | Instance supprimée | ☐ |

---

## Étape 04 — Vue fractale & Console

### T04.1 — Vue fractale
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Chaîne d'héritage | Sélectionner `AIAgent` | Voir Object → Entity → Agent → AIAgent | ☐ |
| Profondeur limitée | Slider à 2 | Seulement 2 niveaux, bouton "Voir plus" | ☐ |
| Augmenter profondeur | Clic "Voir plus" | 3 niveaux supplémentaires | ☐ |

### T04.2 — Navigation
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Clic carte ancêtre | Clic sur carte `Entity` | Sélection change vers Entity | ☐ |
| Hover carte ancêtre | Survol carte non-courante | Bordure bleue, hint "cliquer pour naviguer" | ☐ |
| Clic relation | Clic sur vecteur sortant | Navigation vers cible | ☐ |
| Clic enfant | Clic sur chip enfant | Navigation vers enfant | ☐ |

### T04.3 — Console de test (inline)
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Expression valide | `Object:Entity.create({name:"x"})` + Run | JSON avec success:true, result.id | ☐ |
| Navigation résultat | `.create({}).result.id` | Affiche uniquement l'ID | ☐ |
| Méthode inexistante | `Object.foo()` | Erreur + liste méthodes disponibles | ☐ |
| Objet inexistant | `Foo.bar()` | Erreur "ObjectType non trouvé" | ☐ |
| Syntaxe invalide | `invalid` | Erreur "Format attendu" | ☐ |

### T04.4 — Onglet Console
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Sync sélection | Sélectionner `Agent` puis onglet Console | Input pré-rempli avec `Object:Entity:Agent` | ☐ |
| Liste méthodes | Saisir lineage valide | Chips méthodes affichés | ☐ |
| Clic méthode | Cliquer sur chip `execute` | Expression pré-remplie | ☐ |
| Historique | Exécuter plusieurs commandes | Historique visible | ☐ |
| Replay historique | Cliquer sur item historique | Commande rejouée | ☐ |

### T04.5 — Onglet JSON
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Affichage | Aller sur onglet JSON | JSON formaté visible | ☐ |
| Objet sélectionné | Avec sélection active | `_selected` en premier | ☐ |
| Copier | Clic "Copier" | Toast "copié", contenu dans presse-papier | ☐ |
| Télécharger | Clic "Télécharger" | Fichier .json téléchargé | ☐ |
| Importer | Clic "Importer" + fichier valide | Données chargées, UI mise à jour | ☐ |

---

## Tests globaux

### TG.1 — Intégrité des données
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Cohérence après éditions | Multiples ajouts/suppressions | Pas d'erreur console, données cohérentes | ☐ |
| Export après éditions | Modifier puis exporter JSON | JSON contient toutes les modifications | ☐ |
| Import restaure état | Exporter, recharger, importer | État restauré identique | ☐ |

### TG.2 — Performance
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Beaucoup d'objets | Créer 50+ objets | UI reste fluide | ☐ |
| Arbre profond | Créer chaîne de 10 niveaux | Affichage correct | ☐ |

### TG.3 — UX
| Test | Action | Résultat attendu | ✓ |
|------|--------|------------------|---|
| Feedback utilisateur | Chaque action | Toast approprié | ☐ |
| États vides | Aucune sélection | Message "Sélectionnez un ObjectType" | ☐ |
| Responsive | Redimensionner fenêtre | Layout s'adapte (min-width respectés) | ☐ |

---

## Checklist de validation finale

### Étape 01 — Explorateur ☐
- [ ] Arbre affiché correctement
- [ ] Création d'objets (simple, chaîne, rattachement)
- [ ] Re-parenting par drag & drop
- [ ] Suppression avec gestion dépendances

### Étape 02 — Tags ☐
- [ ] Création/suppression de tags
- [ ] Attribution via bouton + et drag & drop
- [ ] Catégories fonctionnelles
- [ ] Alias créés et supprimés

### Étape 03 — Schémas ☐
- [ ] Ajout attributs/méthodes/relations/règles
- [ ] Édition inline
- [ ] Suppression d'éléments
- [ ] Héritage dynamique propagé
- [ ] Catalogue (instanciation)

### Étape 04 — Fractale & Console ☐
- [ ] Vue fractale complète avec sources
- [ ] Navigation par clic (ancêtres, relations, enfants)
- [ ] Contrôle de profondeur
- [ ] Console mock fonctionnelle
- [ ] Onglets Console et JSON opérationnels

### Global ☐
- [ ] Pas d'erreurs console
- [ ] Export/Import JSON fonctionnel
- [ ] UI cohérente et réactive
- [ ] Toasts de feedback appropriés

---

## Notes de test

**Date :** _______________

**Testeur :** _______________

**Version :** v3

**Observations :**

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

**Bugs identifiés :**

| # | Description | Sévérité | Étape |
|---|-------------|----------|-------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Statut final :** ☐ Validé  ☐ À corriger
