# E1/7 — SPÉCIFICATION DES SUPERTOOLS CENTRAUX

## Vue d'ensemble

Les SuperTools constituent l'API haut niveau d'EUREKAI, servant d'interface unifiée pour les humains (via UI) et les agents IA. Ils encapsulent les opérations transversales tout en respectant strictement la machinerie sous-jacente (GEVR, ERK, MetaRules).

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPER LAYER                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Create  │ │  Read   │ │ Update  │ │ Delete  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│  ┌────┴───────────┴───────────┴───────────┴────┐           │
│  │              SuperRouter                     │           │
│  └────┬───────────┬───────────┬───────────┬────┘           │
│       │           │           │           │                 │
│  ┌────┴────┐ ┌────┴────┐                                   │
│  │Evaluate │ │Orchestr.│                                   │
│  └─────────┘ └─────────┘                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     GEVR PIPELINE                           │
│         Get → Execute → Validate → Render                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ERK + MetaRules (Enforcement)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. SUPERCREATE

### 1.1 Rôle

SuperCreate est responsable de la **création d'objets fractals** dans EUREKAI. Il gère la génération d'identifiants uniques, l'établissement des lineages, et l'intégration dans les bundles appropriés.

### 1.2 Responsabilités

- Génération d'UUID conformes au schéma fractal
- Résolution et validation du parent (lineage)
- Application des templates selon le type d'objet
- Enregistrement dans le catalogue approprié (Core/Agence)
- Déclenchement des hooks post-création

### 1.3 Ce qu'il NE fait PAS

- Modification d'objets existants (→ SuperUpdate)
- Validation métier complexe (→ SuperEvaluate)
- Orchestration multi-étapes (→ SuperOrchestrate)
- Gestion des transactions distribuées

### 1.4 Signature

```python
class SuperCreateParams:
    type: ObjectType           # Type de l'objet (Project, Task, Asset, etc.)
    parent_id: str | None      # ID du parent dans le lineage
    bundle_id: str | None      # Bundle cible (auto-résolu si absent)
    data: dict                 # Payload de l'objet
    options: CreateOptions     # Options: dry_run, skip_hooks, etc.

class CreateOptions:
    dry_run: bool = False      # Simulation sans persistance
    skip_hooks: bool = False   # Bypass des hooks (Layer 1 requis)
    template: str | None       # Template à appliquer
    validate_only: bool = False

class SuperCreateResult:
    success: bool
    object_id: str | None
    object: FractalObject | None
    lineage: list[str]         # Chemin complet dans l'arbre
    warnings: list[str]
    errors: list[str]

def Super.create(params: SuperCreateParams) -> SuperCreateResult
```

### 1.5 Déroulé interne (GEVR)

```
SUPERCREATE(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Résoudre le contexte:
     - Identifier le bundle cible (Core vs Agence)
     - Charger le schéma du type demandé
     - Résoudre le parent_id en objet parent
     
  2. Préparer les données:
     - Appliquer le template si spécifié
     - Merger avec les valeurs par défaut du type
     - Générer l'UUID via ERK.generate_id()

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Construire l'objet fractal:
     - Instancier FractalObject avec IVC (Identity, View, Context)
     - Établir le DRO (Definition, Rule, Option)
     - Attacher au lineage parent
     
  4. Appliquer les MetaRules:
     - Vérifier les contraintes de structure
     - Valider les permissions (Layer 0/1)
     - Exécuter les règles de propagation

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  5. Validation ERK:
     - Schema validation (type, required fields)
     - Referential integrity (parent exists, bundle valid)
     - Business rules (quotas, naming, uniqueness)
     
  6. Si dry_run ou validate_only:
     - Retourner le résultat sans persistance

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  7. Persister:
     - Écrire dans le catalogue
     - Indexer pour la recherche
     - Mettre à jour les caches
     
  8. Post-création:
     - Exécuter les hooks (si non skip_hooks)
     - Émettre les événements
     - Logger l'opération
     
  9. RETURN SuperCreateResult
```

### 1.6 Exemples d'utilisation

```python
# Exemple 1: Création simple d'un projet
result = Super.create(SuperCreateParams(
    type=ObjectType.PROJECT,
    parent_id="agence:clients:acme",
    data={
        "name": "Site Vitrine ACME",
        "description": "Refonte complète du site corporate",
        "deadline": "2025-06-30",
        "tags": ["web", "corporate", "priority-high"]
    }
))

# Exemple 2: Création avec template
result = Super.create(SuperCreateParams(
    type=ObjectType.TASK,
    parent_id="project:acme-site-vitrine",
    data={
        "name": "Maquettes Desktop",
        "assignee": "agent:designer-01"
    },
    options=CreateOptions(
        template="task:design-ux"
    )
))

# Exemple 3: Dry run pour validation
result = Super.create(SuperCreateParams(
    type=ObjectType.ASSET,
    parent_id="project:acme-site-vitrine:assets",
    data={
        "name": "Logo ACME v2",
        "file_path": "/uploads/logo-acme-v2.svg"
    },
    options=CreateOptions(dry_run=True)
))
if result.success:
    print("Validation OK, prêt à créer")
```

---

## 2. SUPERREAD

### 2.1 Rôle

SuperRead est le point d'accès unifié pour la **lecture d'objets fractals**. Il gère les requêtes simples (par ID) et complexes (recherche, filtrage, traversée de graphe).

### 2.2 Responsabilités

- Récupération d'objets par ID ou chemin
- Requêtes de recherche avec filtres
- Traversée de lineage (ascendants/descendants)
- Résolution des références et liens
- Application des vues (View du IVC)

### 2.3 Ce qu'il NE fait PAS

- Modification des données (→ SuperUpdate)
- Évaluation qualitative (→ SuperEvaluate)
- Agrégations statistiques complexes (→ scénario dédié)

### 2.4 Signature

```python
class SuperReadParams:
    # Mode de lecture (un seul actif)
    id: str | None             # Lecture par ID
    path: str | None           # Lecture par chemin fractal
    query: QuerySpec | None    # Recherche avancée
    
    # Options
    options: ReadOptions

class QuerySpec:
    type: ObjectType | None    # Filtrer par type
    filters: dict              # Conditions {"field": "value"}
    search: str | None         # Recherche textuelle
    lineage: LineageQuery | None
    limit: int = 50
    offset: int = 0
    sort: list[SortSpec] = []

class LineageQuery:
    root_id: str               # Point de départ
    direction: "up" | "down" | "both"
    depth: int = -1            # -1 = illimité
    include_root: bool = True

class ReadOptions:
    view: str = "default"      # Vue à appliquer
    include_children: bool = False
    include_parent: bool = False
    resolve_refs: bool = True  # Résoudre les références
    fields: list[str] | None   # Projection (None = tous)

class SuperReadResult:
    success: bool
    data: FractalObject | list[FractalObject] | None
    total_count: int | None    # Pour les requêtes paginées
    lineage: list[str] | None
    errors: list[str]

def Super.read(params: SuperReadParams) -> SuperReadResult
```

### 2.5 Déroulé interne (GEVR)

```
SUPERREAD(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Analyser le mode de lecture:
     - Si id: mode direct
     - Si path: résoudre le chemin en ID
     - Si query: préparer la requête
     
  2. Vérifier les permissions:
     - Identifier le contexte appelant
     - Valider l'accès (Layer 0/1)
     - Appliquer les filtres de visibilité

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Exécuter la lecture:
     - Mode direct: fetch depuis le catalogue
     - Mode query: exécuter la recherche indexée
     - Mode lineage: traverser l'arbre
     
  4. Résoudre les références:
     - Si resolve_refs: charger les objets liés
     - Construire le graphe de relations

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  5. Vérifier l'intégrité:
     - Objets trouvés existent et sont valides
     - Références résolues correctement
     - Pas de données corrompues

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  6. Appliquer la vue:
     - Sélectionner les champs (projection)
     - Formater selon la vue demandée
     - Masquer les données sensibles si nécessaire
     
  7. Enrichir si demandé:
     - Ajouter children/parent
     - Ajouter lineage complet
     
  8. RETURN SuperReadResult
```

### 2.6 Exemples d'utilisation

```python
# Exemple 1: Lecture directe par ID
result = Super.read(SuperReadParams(
    id="project:acme-site-vitrine"
))
project = result.data

# Exemple 2: Lecture avec enfants
result = Super.read(SuperReadParams(
    id="project:acme-site-vitrine",
    options=ReadOptions(
        include_children=True,
        view="dashboard"
    )
))

# Exemple 3: Recherche avec filtres
result = Super.read(SuperReadParams(
    query=QuerySpec(
        type=ObjectType.TASK,
        filters={
            "status": "in_progress",
            "assignee": "agent:designer-01"
        },
        sort=[SortSpec(field="deadline", order="asc")]
    )
))

# Exemple 4: Traversée de lineage
result = Super.read(SuperReadParams(
    query=QuerySpec(
        lineage=LineageQuery(
            root_id="project:acme-site-vitrine",
            direction="down",
            depth=3
        )
    )
))
```

---

## 3. SUPERUPDATE

### 3.1 Rôle

SuperUpdate gère la **modification d'objets fractals existants**. Il assure la cohérence des mises à jour, la gestion des versions, et la propagation des changements.

### 3.2 Responsabilités

- Mise à jour partielle ou complète d'objets
- Gestion des versions et historique
- Propagation des changements dans le lineage
- Déplacement d'objets (re-parenting)
- Mise à jour en masse (batch)

### 3.3 Ce qu'il NE fait PAS

- Création d'objets (→ SuperCreate)
- Suppression d'objets (→ SuperDelete)
- Fusion/merge complexe de conflits

### 3.4 Signature

```python
class SuperUpdateParams:
    id: str                    # ID de l'objet à modifier
    changes: UpdateChanges     # Modifications à appliquer
    options: UpdateOptions

class UpdateChanges:
    # Mise à jour des données
    set: dict | None           # {"field": "new_value"}
    unset: list[str] | None    # Champs à supprimer
    push: dict | None          # Ajouter à un array {"tags": "new-tag"}
    pull: dict | None          # Retirer d'un array
    
    # Opérations structurelles
    move_to: str | None        # Nouveau parent_id
    rename: str | None         # Nouveau nom

class UpdateOptions:
    dry_run: bool = False
    skip_hooks: bool = False
    create_version: bool = True  # Créer un snapshot
    propagate: bool = True       # Propager aux enfants si applicable
    merge_strategy: "replace" | "deep_merge" = "replace"

class SuperUpdateResult:
    success: bool
    object: FractalObject | None
    version_id: str | None     # ID de la version créée
    changes_applied: dict      # Résumé des changements
    propagated_to: list[str]   # IDs des objets impactés
    warnings: list[str]
    errors: list[str]

def Super.update(params: SuperUpdateParams) -> SuperUpdateResult
```

### 3.5 Déroulé interne (GEVR)

```
SUPERUPDATE(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Charger l'objet existant:
     - Fetch par ID
     - Vérifier existence
     - Acquérir un lock optimiste
     
  2. Préparer le contexte:
     - Charger le schéma du type
     - Identifier les règles de propagation
     - Calculer le delta

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Appliquer les changements:
     - SET: remplacer les valeurs
     - UNSET: supprimer les champs
     - PUSH/PULL: modifier les arrays
     - MOVE: détacher/rattacher au lineage
     
  4. Créer la version si demandé:
     - Snapshot de l'état précédent
     - Stocker avec timestamp et auteur

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  5. Valider le nouvel état:
     - Schema validation
     - Contraintes métier (MetaRules)
     - Intégrité référentielle (si MOVE)
     
  6. Si dry_run:
     - Retourner sans persister

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  7. Persister:
     - Écrire le nouvel état
     - Mettre à jour les index
     - Libérer le lock
     
  8. Propager si nécessaire:
     - Identifier les enfants impactés
     - Appliquer les règles de cascade
     
  9. Post-update:
     - Exécuter les hooks
     - Émettre les événements
     - Logger
     
  10. RETURN SuperUpdateResult
```

### 3.6 Exemples d'utilisation

```python
# Exemple 1: Mise à jour simple
result = Super.update(SuperUpdateParams(
    id="project:acme-site-vitrine",
    changes=UpdateChanges(
        set={
            "status": "in_progress",
            "progress": 35
        }
    )
))

# Exemple 2: Ajout de tags
result = Super.update(SuperUpdateParams(
    id="task:maquettes-desktop",
    changes=UpdateChanges(
        push={"tags": "validated"}
    )
))

# Exemple 3: Déplacement d'un objet
result = Super.update(SuperUpdateParams(
    id="task:maquettes-desktop",
    changes=UpdateChanges(
        move_to="project:acme-phase-2:tasks"
    ),
    options=UpdateOptions(
        create_version=True
    )
))

# Exemple 4: Mise à jour avec merge profond
result = Super.update(SuperUpdateParams(
    id="bundle:agence:config",
    changes=UpdateChanges(
        set={
            "settings.notifications.email": True,
            "settings.notifications.slack": False
        }
    ),
    options=UpdateOptions(
        merge_strategy="deep_merge"
    )
))
```

---

## 4. SUPERDELETE

### 4.1 Rôle

SuperDelete gère la **suppression d'objets fractals**. Il assure la cohérence du lineage, la gestion des dépendances, et propose différentes stratégies de suppression.

### 4.2 Responsabilités

- Suppression douce (soft delete) ou définitive (hard delete)
- Gestion des dépendances et références
- Stratégies de cascade ou d'orphanisation
- Archivage avant suppression
- Nettoyage des index et caches

### 4.3 Ce qu'il NE fait PAS

- Modification d'objets (→ SuperUpdate)
- Restauration d'objets supprimés (→ scénario dédié)
- Suppression de bundles Core (protection Layer 0)

### 4.4 Signature

```python
class SuperDeleteParams:
    id: str                    # ID de l'objet à supprimer
    options: DeleteOptions

class DeleteOptions:
    mode: "soft" | "hard" = "soft"
    strategy: DeleteStrategy = "cascade"
    dry_run: bool = False
    skip_hooks: bool = False
    archive: bool = True       # Archiver avant suppression hard
    force: bool = False        # Ignorer les warnings

class DeleteStrategy:
    CASCADE = "cascade"        # Supprimer les enfants
    ORPHAN = "orphan"          # Détacher les enfants (remonter au parent)
    PROTECT = "protect"        # Échouer si enfants existent
    NULLIFY = "nullify"        # Mettre les références à null

class SuperDeleteResult:
    success: bool
    deleted_ids: list[str]     # Tous les objets supprimés
    orphaned_ids: list[str]    # Objets détachés
    archive_id: str | None     # ID de l'archive créée
    blocked_by: list[str]      # Objets bloquant (si PROTECT)
    warnings: list[str]
    errors: list[str]

def Super.delete(params: SuperDeleteParams) -> SuperDeleteResult
```

### 4.5 Déroulé interne (GEVR)

```
SUPERDELETE(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Charger l'objet cible:
     - Vérifier existence
     - Charger le lineage complet
     - Identifier toutes les dépendances
     
  2. Analyser l'impact:
     - Lister les enfants (depth=∞)
     - Lister les références entrantes
     - Calculer le coût de la suppression

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Vérifier les protections:
     - Layer 0: bloquer suppression Core
     - Layer 1: vérifier permissions
     - PROTECT: échouer si enfants
     
  4. Préparer la stratégie:
     - CASCADE: marquer les enfants pour suppression
     - ORPHAN: préparer le re-parenting
     - NULLIFY: identifier les refs à nettoyer

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  5. Valider la cohérence:
     - Pas de références non gérées
     - Pas de violation de contraintes
     - Archivage possible si demandé
     
  6. Si dry_run:
     - Retourner l'impact sans exécuter

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  7. Archiver si demandé:
     - Créer snapshot complet
     - Stocker avec métadonnées
     
  8. Exécuter la suppression:
     - Mode soft: marquer deleted_at
     - Mode hard: supprimer physiquement
     - Appliquer la stratégie aux enfants
     
  9. Nettoyer:
     - Mettre à jour les index
     - Invalider les caches
     - Nettoyer les références (si NULLIFY)
     
  10. Post-delete:
      - Exécuter les hooks
      - Émettre les événements
      - Logger
      
  11. RETURN SuperDeleteResult
```

### 4.6 Exemples d'utilisation

```python
# Exemple 1: Soft delete simple
result = Super.delete(SuperDeleteParams(
    id="task:maquettes-desktop"
))

# Exemple 2: Hard delete avec cascade
result = Super.delete(SuperDeleteParams(
    id="project:old-project",
    options=DeleteOptions(
        mode="hard",
        strategy="cascade",
        archive=True
    )
))

# Exemple 3: Suppression protégée (échoue si enfants)
result = Super.delete(SuperDeleteParams(
    id="bundle:client-acme",
    options=DeleteOptions(
        strategy="protect"
    )
))
if not result.success:
    print(f"Bloqué par: {result.blocked_by}")

# Exemple 4: Dry run pour analyse d'impact
result = Super.delete(SuperDeleteParams(
    id="project:big-project",
    options=DeleteOptions(
        strategy="cascade",
        dry_run=True
    )
))
print(f"Objets qui seraient supprimés: {len(result.deleted_ids)}")
```

---

## 5. SUPEREVALUATE

### 5.1 Rôle

SuperEvaluate est le moteur d'**évaluation qualitative** d'EUREKAI. Il permet d'auditer, scorer, et analyser les objets fractals selon des critères définis.

### 5.2 Responsabilités

- Évaluation de conformité (schéma, règles)
- Scoring multi-critères
- Audit de qualité (complétude, cohérence)
- Comparaison entre objets ou versions
- Génération de rapports d'évaluation

### 5.3 Ce qu'il NE fait PAS

- Modification des objets évalués (→ SuperUpdate)
- Correction automatique des problèmes
- Évaluation de code/assets (→ outils spécialisés)

### 5.4 Signature

```python
class SuperEvaluateParams:
    target: EvaluateTarget     # Quoi évaluer
    evaluators: list[str]      # Évaluateurs à appliquer
    options: EvaluateOptions

class EvaluateTarget:
    id: str | None             # Un objet spécifique
    ids: list[str] | None      # Plusieurs objets
    query: QuerySpec | None    # Résultat d'une requête
    scope: "object" | "subtree" | "bundle" = "object"

class EvaluateOptions:
    depth: int = 1             # Profondeur d'évaluation
    include_recommendations: bool = True
    compare_to: str | None     # ID pour comparaison
    threshold: float | None    # Score minimum acceptable
    format: "summary" | "detailed" | "report" = "summary"

# Évaluateurs disponibles
EVALUATORS = [
    "schema_compliance",       # Conformité au schéma
    "completeness",            # Taux de remplissage
    "consistency",             # Cohérence interne
    "freshness",               # Fraîcheur des données
    "connectivity",            # Qualité des liens
    "naming_convention",       # Respect des conventions
    "security_posture",        # Posture sécurité
    "performance_metrics",     # Métriques de perf
    "business_rules",          # Règles métier (MetaRules)
]

class SuperEvaluateResult:
    success: bool
    overall_score: float       # 0.0 - 1.0
    evaluations: dict[str, EvaluationDetail]
    issues: list[Issue]
    recommendations: list[Recommendation]
    comparison: ComparisonResult | None
    report: str | None         # Si format="report"

class EvaluationDetail:
    evaluator: str
    score: float
    passed: bool
    details: dict
    issues: list[Issue]

class Issue:
    severity: "critical" | "warning" | "info"
    code: str
    message: str
    location: str              # Path dans l'objet
    fix_hint: str | None

def Super.evaluate(params: SuperEvaluateParams) -> SuperEvaluateResult
```

### 5.5 Déroulé interne (GEVR)

```
SUPEREVALUATE(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Résoudre la cible:
     - Charger l'objet ou les objets
     - Si scope="subtree": charger les enfants
     - Si compare_to: charger l'objet de référence
     
  2. Charger les évaluateurs:
     - Résoudre les noms en instances
     - Vérifier la compatibilité avec le type
     - Préparer les contextes d'évaluation

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Exécuter chaque évaluateur:
     FOR each evaluator:
       - Analyser l'objet selon les critères
       - Calculer le score partiel
       - Collecter les issues
       
  4. Agréger les résultats:
     - Calculer le score global (moyenne pondérée)
     - Fusionner les issues
     - Dédupliquer

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  5. Vérifier le seuil:
     - Si threshold défini: comparer
     - Marquer passed/failed
     
  6. Effectuer la comparaison:
     - Si compare_to: calculer les différences
     - Identifier les régressions/améliorations

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  7. Générer les recommandations:
     - Analyser les issues
     - Proposer des corrections
     - Prioriser par impact
     
  8. Formater la sortie:
     - summary: scores + issues critiques
     - detailed: tout
     - report: document formaté
     
  9. RETURN SuperEvaluateResult
```

### 5.6 Exemples d'utilisation

```python
# Exemple 1: Évaluation simple
result = Super.evaluate(SuperEvaluateParams(
    target=EvaluateTarget(id="project:acme-site-vitrine"),
    evaluators=["completeness", "consistency"]
))
print(f"Score global: {result.overall_score:.2%}")

# Exemple 2: Audit complet avec recommandations
result = Super.evaluate(SuperEvaluateParams(
    target=EvaluateTarget(
        id="bundle:agence",
        scope="subtree"
    ),
    evaluators=[
        "schema_compliance",
        "completeness",
        "naming_convention",
        "business_rules"
    ],
    options=EvaluateOptions(
        depth=3,
        format="detailed"
    )
))
for issue in result.issues:
    if issue.severity == "critical":
        print(f"CRITICAL: {issue.message} at {issue.location}")

# Exemple 3: Comparaison de versions
result = Super.evaluate(SuperEvaluateParams(
    target=EvaluateTarget(id="project:acme-site-vitrine"),
    evaluators=["completeness", "consistency"],
    options=EvaluateOptions(
        compare_to="version:acme-site-vitrine:v1.0"
    )
))
if result.comparison.regressions:
    print("Régressions détectées!")

# Exemple 4: Validation avec seuil
result = Super.evaluate(SuperEvaluateParams(
    target=EvaluateTarget(id="deliverable:maquettes-final"),
    evaluators=["completeness", "quality"],
    options=EvaluateOptions(
        threshold=0.85
    )
))
if not result.success:
    print("Qualité insuffisante pour livraison")
```

---

## 6. SUPERORCHESTRATE

### 6.1 Rôle

SuperOrchestrate est le **chef d'orchestre** des opérations complexes. Il permet de composer et exécuter des workflows multi-étapes impliquant plusieurs SuperTools et scénarios GEVR.

### 6.2 Responsabilités

- Exécution de scénarios prédéfinis (D3)
- Composition de workflows custom
- Gestion des transactions multi-objets
- Coordination d'agents IA
- Gestion des erreurs et rollback

### 6.3 Ce qu'il NE fait PAS

- Opérations CRUD simples (→ autres SuperTools)
- Définition de nouveaux scénarios (→ config)
- Exécution de code arbitraire

### 6.4 Signature

```python
class SuperOrchestrateParams:
    scenario: str | None       # Scénario prédéfini (D3)
    workflow: Workflow | None  # Workflow custom
    context: dict              # Variables de contexte
    options: OrchestrateOptions

class Workflow:
    name: str
    steps: list[WorkflowStep]
    on_error: "rollback" | "continue" | "pause" = "rollback"
    timeout: int | None        # Secondes

class WorkflowStep:
    id: str
    action: str                # "create", "update", "evaluate", etc.
    params: dict               # Paramètres de l'action
    condition: str | None      # Expression conditionnelle
    depends_on: list[str] = [] # Étapes préalables
    on_success: str | None     # Étape suivante si succès
    on_failure: str | None     # Étape si échec
    retry: RetryConfig | None

class RetryConfig:
    max_attempts: int = 3
    delay: int = 1             # Secondes entre tentatives
    backoff: float = 2.0       # Multiplicateur

class OrchestrateOptions:
    dry_run: bool = False
    async_mode: bool = False   # Exécution asynchrone
    checkpoint: bool = True    # Sauvegarder l'état
    notify: list[str] = []     # Canaux de notification

class SuperOrchestrateResult:
    success: bool
    execution_id: str
    status: "completed" | "failed" | "partial" | "running"
    steps_completed: list[str]
    steps_failed: list[str]
    outputs: dict[str, any]    # Sorties de chaque étape
    rollback_applied: bool
    errors: list[str]

def Super.orchestrate(params: SuperOrchestrateParams) -> SuperOrchestrateResult
```

### 6.5 Déroulé interne (GEVR)

```
SUPERORCHESTRATE(params):

  # ══════════════════════════════════════════════════════════
  # GET PHASE
  # ══════════════════════════════════════════════════════════
  
  1. Résoudre le workflow:
     - Si scenario: charger depuis D3
     - Si workflow: valider la structure
     - Merger avec le contexte fourni
     
  2. Analyser les dépendances:
     - Construire le DAG des étapes
     - Identifier les parallélisations possibles
     - Calculer le chemin critique

  # ══════════════════════════════════════════════════════════
  # EXECUTE PHASE
  # ══════════════════════════════════════════════════════════
  
  3. Initialiser l'exécution:
     - Créer l'execution_id
     - Préparer le contexte partagé
     - Démarrer le checkpoint si activé
     
  4. Exécuter les étapes:
     FOR each step (ordre topologique):
       a. Vérifier les dépendances
       b. Évaluer la condition
       c. Si condition OK:
          - Appeler le SuperTool approprié
          - Gérer les retries si échec
          - Stocker l'output
       d. Mettre à jour le checkpoint
       e. Si échec et on_error="rollback":
          - Déclencher le rollback
          - BREAK
          
  5. Gérer les erreurs:
     - Collecter tous les échecs
     - Appliquer la stratégie on_error
     - Notifier si configuré

  # ══════════════════════════════════════════════════════════
  # VALIDATE PHASE
  # ══════════════════════════════════════════════════════════
  
  6. Valider le résultat global:
     - Toutes les étapes requises complétées?
     - État final cohérent?
     - Contraintes métier respectées?

  # ══════════════════════════════════════════════════════════
  # RENDER PHASE
  # ══════════════════════════════════════════════════════════
  
  7. Finaliser:
     - Calculer le statut final
     - Compiler les outputs
     - Nettoyer les ressources temporaires
     
  8. Post-orchestration:
     - Logger l'exécution complète
     - Envoyer les notifications
     - Mettre à jour les métriques
     
  9. RETURN SuperOrchestrateResult
```

### 6.6 Exemples d'utilisation

```python
# Exemple 1: Scénario prédéfini
result = Super.orchestrate(SuperOrchestrateParams(
    scenario="new_project_setup",
    context={
        "client_id": "client:acme",
        "project_name": "Site Vitrine 2025",
        "template": "web-standard"
    }
))

# Exemple 2: Workflow custom simple
result = Super.orchestrate(SuperOrchestrateParams(
    workflow=Workflow(
        name="create_and_evaluate",
        steps=[
            WorkflowStep(
                id="create",
                action="create",
                params={
                    "type": "Project",
                    "data": {"name": "{{project_name}}"}
                }
            ),
            WorkflowStep(
                id="evaluate",
                action="evaluate",
                params={
                    "target": "{{outputs.create.object_id}}",
                    "evaluators": ["completeness"]
                },
                depends_on=["create"]
            )
        ]
    ),
    context={"project_name": "Test Project"}
))

# Exemple 3: Workflow avec conditions et retry
result = Super.orchestrate(SuperOrchestrateParams(
    workflow=Workflow(
        name="conditional_update",
        steps=[
            WorkflowStep(
                id="check",
                action="evaluate",
                params={
                    "target": "project:acme",
                    "evaluators": ["completeness"]
                }
            ),
            WorkflowStep(
                id="update",
                action="update",
                params={
                    "id": "project:acme",
                    "changes": {"status": "validated"}
                },
                condition="{{outputs.check.overall_score}} >= 0.8",
                depends_on=["check"],
                retry=RetryConfig(max_attempts=2)
            ),
            WorkflowStep(
                id="flag",
                action="update",
                params={
                    "id": "project:acme",
                    "changes": {"needs_review": True}
                },
                condition="{{outputs.check.overall_score}} < 0.8",
                depends_on=["check"]
            )
        ],
        on_error="continue"
    ),
    context={}
))

# Exemple 4: Exécution asynchrone avec notifications
result = Super.orchestrate(SuperOrchestrateParams(
    scenario="full_project_audit",
    context={"bundle_id": "agence:clients"},
    options=OrchestrateOptions(
        async_mode=True,
        notify=["slack:ops-channel", "email:admin@agency.com"]
    )
))
print(f"Exécution lancée: {result.execution_id}")
```

---

## 7. API UNIFIÉE

### 7.1 Interface Super

```python
class Super:
    """
    Point d'entrée unique pour tous les SuperTools.
    Singleton accessible globalement.
    """
    
    @staticmethod
    def create(params: SuperCreateParams) -> SuperCreateResult:
        """Créer un nouvel objet fractal."""
        return SuperCreateHandler.execute(params)
    
    @staticmethod
    def read(params: SuperReadParams) -> SuperReadResult:
        """Lire un ou plusieurs objets fractals."""
        return SuperReadHandler.execute(params)
    
    @staticmethod
    def update(params: SuperUpdateParams) -> SuperUpdateResult:
        """Mettre à jour un objet fractal."""
        return SuperUpdateHandler.execute(params)
    
    @staticmethod
    def delete(params: SuperDeleteParams) -> SuperDeleteResult:
        """Supprimer un objet fractal."""
        return SuperDeleteHandler.execute(params)
    
    @staticmethod
    def evaluate(params: SuperEvaluateParams) -> SuperEvaluateResult:
        """Évaluer la qualité d'objets fractals."""
        return SuperEvaluateHandler.execute(params)
    
    @staticmethod
    def orchestrate(params: SuperOrchestrateParams) -> SuperOrchestrateResult:
        """Orchestrer un workflow multi-étapes."""
        return SuperOrchestrateHandler.execute(params)
```

### 7.2 Raccourcis syntaxiques

```python
# Raccourcis pour les opérations courantes

# Lecture rapide
obj = Super.read(id="project:acme").data

# Création minimale
result = Super.create(type=ObjectType.TASK, data={"name": "New Task"})

# Mise à jour inline
Super.update(id="task:123", set={"status": "done"})

# Évaluation rapide
score = Super.evaluate(id="project:acme").overall_score
```

### 7.3 Chaînage

```python
# Les résultats peuvent être chaînés via orchestrate
# ou via des patterns fonctionnels

# Pattern Pipeline (via orchestrate)
Super.orchestrate(workflow=Workflow(
    steps=[
        WorkflowStep(id="create", action="create", ...),
        WorkflowStep(id="evaluate", action="evaluate", depends_on=["create"], ...),
        WorkflowStep(id="notify", action="notify", depends_on=["evaluate"], ...)
    ]
))
```

---

## 8. LIEN SUPERTOOLS ↔ SCÉNARIOS GEVR

### 8.1 Mapping

| SuperTool       | Scénarios GEVR typiques                    |
|-----------------|-------------------------------------------|
| SuperCreate     | D1-CREATE, D1-GENERATE, D1-IMPORT         |
| SuperRead       | D1-FETCH, D1-SEARCH, D1-TRAVERSE          |
| SuperUpdate     | D1-MODIFY, D1-MERGE, D1-MOVE              |
| SuperDelete     | D1-REMOVE, D1-ARCHIVE, D1-PURGE           |
| SuperEvaluate   | D2-AUDIT, D2-SCORE, D2-COMPARE            |
| SuperOrchestrate| D3-* (tous les scénarios orchestrés)      |

### 8.2 Invocation des scénarios

```python
# SuperCreate invoque le scénario approprié selon le type
def SuperCreateHandler.execute(params):
    # Déterminer le scénario
    if params.options.template:
        scenario = "D1-GENERATE-FROM-TEMPLATE"
    elif is_import_data(params.data):
        scenario = "D1-IMPORT"
    else:
        scenario = "D1-CREATE-STANDARD"
    
    # Déléguer au moteur GEVR
    return GEVR.run(scenario, params)
```

---

## 9. CAS DE TEST

### 9.1 Tests simples

```python
# TEST-001: Création basique
def test_create_simple():
    result = Super.create(SuperCreateParams(
        type=ObjectType.TASK,
        data={"name": "Test Task"}
    ))
    assert result.success
    assert result.object_id is not None
    assert result.object.data["name"] == "Test Task"

# TEST-002: Lecture par ID
def test_read_by_id():
    # Setup
    create_result = Super.create(...)
    
    # Test
    result = Super.read(SuperReadParams(
        id=create_result.object_id
    ))
    assert result.success
    assert result.data.id == create_result.object_id

# TEST-003: Mise à jour partielle
def test_update_partial():
    # Setup
    obj_id = create_test_object()
    
    # Test
    result = Super.update(SuperUpdateParams(
        id=obj_id,
        changes=UpdateChanges(set={"status": "updated"})
    ))
    assert result.success
    assert result.object.data["status"] == "updated"

# TEST-004: Suppression soft
def test_delete_soft():
    # Setup
    obj_id = create_test_object()
    
    # Test
    result = Super.delete(SuperDeleteParams(id=obj_id))
    assert result.success
    
    # Vérifier que l'objet existe encore mais marqué supprimé
    read_result = Super.read(SuperReadParams(id=obj_id))
    assert read_result.data.deleted_at is not None
```

### 9.2 Tests complexes

```python
# TEST-101: Création avec lineage complet
def test_create_with_lineage():
    # Créer une hiérarchie
    bundle = Super.create(type=ObjectType.BUNDLE, data={"name": "Test Bundle"})
    project = Super.create(
        type=ObjectType.PROJECT,
        parent_id=bundle.object_id,
        data={"name": "Test Project"}
    )
    task = Super.create(
        type=ObjectType.TASK,
        parent_id=project.object_id,
        data={"name": "Test Task"}
    )
    
    # Vérifier le lineage
    assert task.lineage == [bundle.object_id, project.object_id, task.object_id]

# TEST-102: Recherche avec filtres multiples
def test_search_complex():
    # Setup: créer plusieurs objets
    for i in range(10):
        Super.create(
            type=ObjectType.TASK,
            data={
                "name": f"Task {i}",
                "status": "pending" if i % 2 == 0 else "done",
                "priority": i
            }
        )
    
    # Test: filtrer et trier
    result = Super.read(SuperReadParams(
        query=QuerySpec(
            type=ObjectType.TASK,
            filters={"status": "pending"},
            sort=[SortSpec(field="priority", order="desc")],
            limit=3
        )
    ))
    assert len(result.data) == 3
    assert all(t.data["status"] == "pending" for t in result.data)
    assert result.data[0].data["priority"] > result.data[1].data["priority"]

# TEST-103: Cascade delete
def test_cascade_delete():
    # Setup: créer une hiérarchie
    project = Super.create(type=ObjectType.PROJECT, data={"name": "P"})
    tasks = [
        Super.create(type=ObjectType.TASK, parent_id=project.object_id, data={"name": f"T{i}"})
        for i in range(5)
    ]
    
    # Test: supprimer le projet en cascade
    result = Super.delete(SuperDeleteParams(
        id=project.object_id,
        options=DeleteOptions(strategy="cascade")
    ))
    
    assert result.success
    assert len(result.deleted_ids) == 6  # 1 project + 5 tasks
    
    # Vérifier que tout est supprimé
    for task in tasks:
        read = Super.read(SuperReadParams(id=task.object_id))
        assert read.data.deleted_at is not None

# TEST-104: Évaluation multi-critères
def test_evaluate_multi():
    # Setup
    project = Super.create(
        type=ObjectType.PROJECT,
        data={
            "name": "Test",
            "description": "",  # Incomplet
            "deadline": None    # Manquant
        }
    )
    
    # Test
    result = Super.evaluate(SuperEvaluateParams(
        target=EvaluateTarget(id=project.object_id),
        evaluators=["completeness", "schema_compliance"]
    ))
    
    assert result.success
    assert result.overall_score < 1.0  # Pas parfait
    assert any(i.code == "MISSING_FIELD" for i in result.issues)
    assert len(result.recommendations) > 0

# TEST-105: Workflow orchestré
def test_orchestrate_workflow():
    result = Super.orchestrate(SuperOrchestrateParams(
        workflow=Workflow(
            name="test_flow",
            steps=[
                WorkflowStep(
                    id="step1",
                    action="create",
                    params={"type": "Task", "data": {"name": "Created"}}
                ),
                WorkflowStep(
                    id="step2",
                    action="update",
                    params={
                        "id": "{{outputs.step1.object_id}}",
                        "changes": {"set": {"status": "processed"}}
                    },
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    id="step3",
                    action="evaluate",
                    params={
                        "target": "{{outputs.step1.object_id}}",
                        "evaluators": ["completeness"]
                    },
                    depends_on=["step2"]
                )
            ]
        ),
        context={}
    ))
    
    assert result.success
    assert result.status == "completed"
    assert len(result.steps_completed) == 3
```

### 9.3 Tests d'erreur

```python
# TEST-201: Création avec parent invalide
def test_create_invalid_parent():
    result = Super.create(SuperCreateParams(
        type=ObjectType.TASK,
        parent_id="nonexistent:id",
        data={"name": "Test"}
    ))
    
    assert not result.success
    assert "PARENT_NOT_FOUND" in [e.code for e in result.errors]

# TEST-202: Suppression protégée avec enfants
def test_delete_protected():
    # Setup
    parent = Super.create(type=ObjectType.PROJECT, data={"name": "P"})
    child = Super.create(type=ObjectType.TASK, parent_id=parent.object_id, data={"name": "T"})
    
    # Test
    result = Super.delete(SuperDeleteParams(
        id=parent.object_id,
        options=DeleteOptions(strategy="protect")
    ))
    
    assert not result.success
    assert child.object_id in result.blocked_by

# TEST-203: Mise à jour avec violation de schéma
def test_update_schema_violation():
    # Setup
    obj = Super.create(type=ObjectType.TASK, data={"name": "Test", "priority": 1})
    
    # Test: priority doit être un int
    result = Super.update(SuperUpdateParams(
        id=obj.object_id,
        changes=UpdateChanges(set={"priority": "high"})  # String au lieu d'int
    ))
    
    assert not result.success
    assert "SCHEMA_VIOLATION" in [e.code for e in result.errors]

# TEST-204: Lecture d'objet supprimé
def test_read_deleted():
    # Setup
    obj = Super.create(type=ObjectType.TASK, data={"name": "Test"})
    Super.delete(SuperDeleteParams(id=obj.object_id, options=DeleteOptions(mode="hard")))
    
    # Test
    result = Super.read(SuperReadParams(id=obj.object_id))
    
    assert not result.success
    assert "OBJECT_NOT_FOUND" in [e.code for e in result.errors]

# TEST-205: Orchestration avec rollback
def test_orchestrate_rollback():
    # Un workflow qui échoue à la deuxième étape
    result = Super.orchestrate(SuperOrchestrateParams(
        workflow=Workflow(
            name="failing_flow",
            steps=[
                WorkflowStep(
                    id="step1",
                    action="create",
                    params={"type": "Task", "data": {"name": "Will be rolled back"}}
                ),
                WorkflowStep(
                    id="step2",
                    action="update",
                    params={"id": "nonexistent:id", "changes": {}},  # Va échouer
                    depends_on=["step1"]
                )
            ],
            on_error="rollback"
        ),
        context={}
    ))
    
    assert not result.success
    assert result.rollback_applied
    assert "step1" in result.steps_completed
    assert "step2" in result.steps_failed
    
    # Vérifier que step1 a été rollback
    created_id = result.outputs["step1"]["object_id"]
    read = Super.read(SuperReadParams(id=created_id))
    assert not read.success or read.data.deleted_at is not None
```

---

## 10. CHECKLIST DE VALIDATION

- [x] Tous les SuperTools centraux sont définis de manière claire et cohérente
- [x] Chacun a une signature et une responsabilité bien délimitées
- [x] Les SuperTools utilisent la machinerie GEVR / ERK / MetaRules, pas l'inverse
- [x] Exemples fournis pour chacun
- [x] Cas de test: appels simples
- [x] Cas de test: appels complexes
- [x] Cas de test: erreurs gérées
- [x] API unifiée avec interface Super
- [x] Lien SuperTools ↔ Scénarios GEVR documenté
- [x] Séparation Core/Agence respectée (Layer 0/1)
- [x] Options dry_run disponibles partout
- [x] Gestion des versions intégrée (SuperUpdate)
- [x] Stratégies de suppression multiples (SuperDelete)
- [x] Évaluateurs extensibles (SuperEvaluate)
- [x] Workflows composables (SuperOrchestrate)
