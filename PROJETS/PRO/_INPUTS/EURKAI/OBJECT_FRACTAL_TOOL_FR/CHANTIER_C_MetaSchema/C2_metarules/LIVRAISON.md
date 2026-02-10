# LIVRAISON C2/2 — MetaRules de Structure

## ✅ CHECKLIST DE VALIDATION

- [x] Les MetaRules couvrent les invariants fondamentaux d'EUREKAI
- [x] Une fonction d'audit global permet de lister les violations de structure
- [x] Chaque violation est clairement reliée à l'objet et à la règle concernée
- [x] Plusieurs exemples + cas de test fournis pour valider le système

---

## 📦 Fichiers Livrés

| Fichier | Description |
|---------|-------------|
| `metarules_engine.py` | Module principal avec toutes les règles et le moteur |
| `test_metarules.py` | Tests exhaustifs et exemples exécutables |
| `MetaRulesAuditPanel.jsx` | Composant React pour intégration cockpit |

---

## 🎯 Architecture du Système

### Formalisme ERK-like

Les MetaRules utilisent une syntaxe proche d'ERK :

```
FOR <scope>: <action> <target> [condition]

Exemples:
  FOR ALL: require attribute 'id' non-empty
  FOR ObjectType.IDENTITY: require method 'prompt' for type Agent
  FOR Core:Agent:*: require relation 'inherits_from' Core:Agent
  FOR ALL: forbid cycle in lineage
```

### Hiérarchie des Classes

```
MetaRule (ABC)
├── RequireId          # Identity
├── RequireName        # Identity
├── RequireType        # Identity
├── UniqueId           # Identity
├── RequireLineage     # Structure
├── NoCycleInLineage   # Structure
├── LineageMatchesParent    # Structure
├── MaxDepth           # Structure
├── OrphanWarning      # Structure
├── RequireAttribute   # Bundle (paramétrable)
├── RequireMethodForAgent   # Bundle
├── RequireRelationDependsOn # Relation
├── LineageSegmentsExist    # Consistency
└── TypeConsistencyInHierarchy # Consistency
```

### Niveaux de Sévérité

| Niveau | Icon | Usage |
|--------|------|-------|
| `CRITICAL` | 🔴 | Bloquant pour déploiement |
| `ERROR` | 🟠 | Doit être corrigé |
| `WARNING` | 🟡 | À surveiller |
| `INFO` | 🔵 | Information seulement |

---

## 📊 API de Vérification

### Interface Principale

```python
from metarules_engine import check_metarules, MetaRuleEngine

# API simplifiée
result = check_metarules(store)
# → { ok: bool, errors: [...], stats: {...} }

# API complète avec contrôle
engine = MetaRuleEngine()
engine.add_rule(MyCustomRule())
engine.disable_rule('orphan_warning')
result = engine.check_all(store)
```

### Structure de Retour

```python
{
    "ok": False,                    # True si aucune CRITICAL/ERROR
    "errors": [
        {
            "ruleId": "require_id",
            "ruleName": "ID Obligatoire",
            "objectId": "broken_obj",
            "objectLineage": "Core:Broken",
            "severity": "critical",
            "message": "L'objet n'a pas d'identifiant",
            "suggestion": "Définir un id unique",
            "context": {}
        }
    ],
    "stats": {
        "objects_checked": 10,
        "rules_applied": 9,
        "total_violations": 3,
        "critical": 1,
        "errors": 1,
        "warnings": 1,
        "info": 0
    },
    "timestamp": "2025-12-01T09:20:42"
}
```

---

## 🧪 Résultats des Tests

```
✅ Test 1: Store valide       → Aucune erreur critique/error
✅ Test 2: ID manquant        → Détection CRITICAL
✅ Test 3: Cycles             → Détection des boucles parent
✅ Test 4: Orphelins          → Warning pour profondeur > 1
✅ Test 5: Lineage/Parent     → Incohérence détectée
✅ Test 6: Types IVC×DRO      → Incompatibilité signalée
✅ Test 7: Agent method       → 'prompt' obligatoire vérifié
✅ Test 8: Règle custom       → Extension fonctionnelle
✅ Test 9: Enable/Disable     → Contrôle des règles OK
✅ Test 10: Export ERK        → Format lisible généré

Total: 10/10 tests passés
```

---

## 📏 Catalogue des MetaRules par Défaut

### Identité (IDENTITY)

| ID | Nom | Sévérité | Description |
|----|-----|----------|-------------|
| `require_id` | ID Obligatoire | 🔴 CRITICAL | Tout objet doit avoir un id non vide |
| `require_name` | Name Obligatoire | 🟠 ERROR | Tout objet doit avoir un nom |
| `require_type` | Type IVC×DRO | 🟡 WARNING | Le type ne doit pas être UNKNOWN |
| `unique_id` | Unicité ID | 🔴 CRITICAL | Pas de doublons d'ID |

### Structure (STRUCTURE)

| ID | Nom | Sévérité | Description |
|----|-----|----------|-------------|
| `require_lineage` | Lineage Obligatoire | 🟠 ERROR | Lineage non vide |
| `no_cycle_lineage` | Pas de Cycle | 🔴 CRITICAL | Aucun cycle dans la chaîne parent |
| `lineage_matches_parent` | Cohérence Lineage | 🟠 ERROR | Lineage doit commencer par celui du parent |
| `max_depth` | Profondeur Max | 🟡 WARNING | Limite de 10 niveaux par défaut |
| `orphan_warning` | Orphelins | 🟡 WARNING | Signale les objets sans parent (depth > 1) |

### Cohérence (CONSISTENCY)

| ID | Nom | Sévérité | Description |
|----|-----|----------|-------------|
| `type_consistency_hierarchy` | Types Cohérents | 🔵 INFO | Vérifie compatibilité type parent/enfant |
| `lineage_segments_exist` | Segments Valides | 🟡 WARNING | Chaque segment du lineage doit exister |

---

## 🚀 Extensibilité

### Créer une Règle Personnalisée

```python
from metarules_engine import MetaRule, RuleCategory, Severity

class RequireVersion(MetaRule):
    """Tout objet doit avoir un attribut version."""
    
    id = "require_version"
    name = "Version Obligatoire"
    description = "require attribute 'version' in metadata"
    category = RuleCategory.BUNDLE
    default_severity = Severity.WARNING
    scope = "Core:*"  # Seulement pour Core:*
    
    def check(self, obj, store):
        if "version" not in obj.metadata:
            return [self.create_violation(
                obj,
                "Pas de version définie",
                suggestion="Ajouter metadata['version'] = '1.0.0'"
            )]
        return []

# Utilisation
engine.add_rule(RequireVersion())
```

### Scope Patterns

```python
# Tous les objets
scope = "ALL"

# Par type IVC×DRO
scope = ObjectType.IDENTITY

# Par pattern de lineage (regex)
scope = "Core:Agent:*"      # Tous sous Core:Agent
scope = "Agency:Project:.*" # Regex complet
```

---

## 🔌 Intégration Cockpit

### Props du Composant React

```jsx
<MetaRulesAuditPanel
  auditResult={auditResult}      // Résultat de check_metarules()
  rules={rulesList}              // Liste des règles (list_rules())
  onRunAudit={handleRunAudit}    // Callback pour relancer
  onToggleRule={handleToggle}    // Activer/désactiver une règle
  onObjectClick={handleClick}    // Navigation vers l'objet
  onExport={handleExport}        // Export du rapport
/>
```

### Fonctionnalités UI

- ✅ Statut global OK/FAILED avec timestamp
- ✅ Statistiques par sévérité
- ✅ Filtrage par sévérité et recherche textuelle
- ✅ Détail de chaque violation avec suggestion
- ✅ Liste des règles avec toggle on/off
- ✅ Export du rapport

---

## 📝 Notes d'Implémentation

- C2/2 est en **lecture seule** : détection uniquement, pas de modification automatique
- Les règles sont **composables** : on peut en activer/désactiver à la volée
- L'audit est **efficace** : une seule passe sur tous les objets
- Les violations incluent un **contexte** pour debug avancé
- Le système est **compatible C1/1** : utilise les mêmes structures FractalObject

---

## 🔗 Liens avec C1/1

Le système C2/2 s'intègre naturellement avec C1/1 (Lineages Assistés) :

1. `OrphanWarning` détecte les orphelins
2. Le message de violation suggère d'utiliser C1/1
3. L'UI peut proposer un lien vers le panneau de suggestions

```python
# Workflow typique
result = engine.check_all(store)

for v in result.filter_by_rule('orphan_warning'):
    # Proposer les suggestions C1/1
    suggestions = suggest_parents(v.object_id, store)
```
