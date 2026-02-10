# EUREKAI — Système de Méta-Tests & Auto-Debug Fractal

## Module G2/10 — Documentation Complète

---

## 1. Hiérarchie de Tests

Le système implémente **4 niveaux de tests** alignés sur l'architecture fractale :

### Niveau 1 : STRUCTURE (MetaRules)

Valide que les objets respectent les règles structurelles définies.

```
StructureTestGenerator
├─ Évalue chaque MetaRule sur les objets matchants
├─ Conditions ERK : has_attribute, has_method, has_tag, lineage_includes
└─ Produit : TestResult par paire (rule, object)
```

**Catégories couvertes :** `structure`, `coherency`, `security`

### Niveau 2 : RELATIONS (MetaRelations)

Vérifie la cohérence des liens entre objets.

```
RelationTestGenerator
├─ Tests de cardinalité (1, 0..1, 1..*, *)
├─ Tests de validité des cibles (existent-elles ?)
└─ Tests de symétrie (relations bidirectionnelles)
```

**Catégories couvertes :** `relation`

### Niveau 3 : SCÉNARIOS (GEVR)

Teste les pipelines Get-Execute-Validate-Render.

```
ScenarioTestGenerator
├─ Cohérence du pipeline (chaînage entrées/sorties)
├─ Validité des étapes individuelles
└─ Validité de la séquence GEVR
```

**Catégories couvertes :** `scenario`

### Niveau 4 : INTÉGRATION (SuperTools)

Tests end-to-end via le catalogue d'outils.

```
IntegrationTestGenerator
├─ Disponibilité des SuperTools
├─ Contrôle des mutations (sécurité)
└─ Gestion des erreurs intentionnelles
```

**Catégories couvertes :** `module`, `security`

---

## 2. API : `runMetaTests`

### Signature

```python
def runMetaTests(
    scope: TestScope = TestScope.FULL,
    target: Optional[str] = None,
    categories: Optional[List[TestCategory]] = None,
    tags: Optional[List[str]] = None,
    fail_fast: bool = False
) -> TestReport
```

### Paramètres

| Paramètre | Type | Description |
|-----------|------|-------------|
| `scope` | `TestScope` | Portée : FULL, PROJECT, MODULE, OBJECT, LINEAGE |
| `target` | `str` | Cible spécifique (vecteur ou pattern) |
| `categories` | `List[TestCategory]` | Filtrer par catégories |
| `tags` | `List[str]` | Filtrer par tags |
| `fail_fast` | `bool` | Arrêter au premier échec critique |

### Valeurs de Scope

```python
class TestScope(Enum):
    FULL = "full"           # Tout le système
    PROJECT = "project"     # Un projet (préfixe)
    MODULE = "module"       # Un module (contient)
    OBJECT = "object"       # Un objet exact
    LINEAGE = "lineage"     # Une lignée d'objets
```

### Exemples d'utilisation

```python
# Test complet du système
report = engine.runMetaTests()

# Test d'un objet spécifique
report = engine.runMetaTests(
    scope=TestScope.OBJECT,
    target="Object:Page.Landing.MainHero"
)

# Tests de structure uniquement
report = engine.runMetaTests(
    categories=[TestCategory.STRUCTURE]
)

# Tests avec tag "critical-module"
report = engine.runMetaTests(
    tags=["critical-module"]
)

# Fail-fast sur erreurs critiques
report = engine.runMetaTests(fail_fast=True)
```

---

## 3. Exemples de Rapports

### Rapport Console (summary)

```
======================================================================
RAPPORT DE TESTS — TR-FB17029B
======================================================================
Scope: full
Durée: 0.00s

RÉSULTATS: 36/39 passés (92.3%)
├─ Passés   : 36
├─ Échoués  : 3
├─ Erreurs  : 0
└─ Ignorés  : 0

⚠️  ÉCHECS CRITIQUES:
  • [REL-TGT-xxx] Cible Module:TypographySet inexistante

PAR CATÉGORIE:
  structure: 3/3
  relation: 11/13
  coherency: 1/2
  scenario: 12/12
  module: 8/8
  security: 1/1
======================================================================
```

### Rapport JSON (extrait)

```json
{
  "report_id": "TR-FB17029B",
  "scope": "full",
  "scope_target": null,
  "started_at": "2025-12-01T11:37:00.473419",
  "completed_at": "2025-12-01T11:37:00.473776",
  "summary": {
    "total": 39,
    "passed": 36,
    "failed": 3,
    "errors": 0,
    "skipped": 0,
    "success_rate": 0.923
  },
  "results": [
    {
      "test_id": "STRUCT-Rule:PageMustHaveLayout",
      "test_name": "Toute page doit avoir un layout",
      "category": "structure",
      "status": "passed",
      "severity": "error",
      "message": "OK: Toute page doit avoir un layout",
      "details": {
        "rule_id": "Rule:PageMustHaveLayout",
        "object": "Object:Page",
        "condition": "has_attribute('layout')",
        "evaluation_result": true
      },
      "duration_ms": 0.005,
      "timestamp": "2025-12-01T11:37:00.473620"
    }
  ]
}
```

### Accès aux propriétés

```python
report.total            # Nombre total de tests
report.passed           # Nombre de tests passés
report.failed           # Nombre de tests échoués
report.success_rate     # Taux de succès (0.0 - 1.0)
report.critical_failures  # Liste des échecs critiques
report.by_category()    # Groupement par catégorie
report.summary()        # Résumé textuel
report.to_dict()        # Export dictionnaire (JSON-ready)
```

---

## 4. Cas de Test Fournis

### Tests de Structure

| Test ID | Description | Sévérité |
|---------|-------------|----------|
| `STRUCT-Rule:PageMustHaveLayout` | Toute page doit avoir un layout | ERROR |
| `STRUCT-Rule:HeroMustHaveTitle` | Tout hero doit avoir un titre | ERROR |
| `STRUCT-Rule:CriticalModuleMustHaveMethod` | Modules critiques → validate | CRITICAL |
| `STRUCT-Rule:InheritanceMustBeValid` | Héritage remonte jusqu'à Object | WARN |

### Tests de Relations

| Test ID Pattern | Description | Sévérité |
|-----------------|-------------|----------|
| `REL-CARD-*` | Vérification cardinalité | ERROR |
| `REL-TGT-*` | Validité des cibles | ERROR |

### Tests de Scénarios

| Test ID Pattern | Description | Sévérité |
|-----------------|-------------|----------|
| `GEVR-COH-*` | Cohérence du pipeline | WARN |
| `GEVR-STEP-*` | Exécution des étapes | ERROR |
| `GEVR-SEQ-*` | Validité séquence GEVR | WARN |

### Tests d'Intégration

| Test ID | Description | Sévérité |
|---------|-------------|----------|
| `INTEG-TOOL-SuperRead` | Disponibilité SuperRead | CRITICAL |
| `INTEG-TOOL-SuperQuery` | Disponibilité SuperQuery | CRITICAL |
| `INTEG-TOOL-SuperCreate` | Disponibilité SuperCreate | CRITICAL |
| `INTEG-TOOL-SuperUpdate` | Disponibilité SuperUpdate | CRITICAL |
| `INTEG-TOOL-SuperDelete` | Disponibilité SuperDelete | CRITICAL |
| `INTEG-TOOL-SuperEvaluate` | Disponibilité SuperEvaluate | CRITICAL |
| `INTEG-TOOL-SuperExecute` | Disponibilité SuperExecute | CRITICAL |
| `INTEG-SEC-MUTATION` | Contrôle des mutations | CRITICAL |
| `INTEG-ERR-READ-404` | Gestion erreur 404 | WARN |

---

## 5. Extension du Système

### Ajouter une MetaRule

```python
rule = MetaRule(
    rule_id=Vector("Rule:CustomRule"),
    applies_to="my-tag",  # ou ObjectType, Vector, List
    condition="has_attribute('required_field')",
    effect="classify:compliant",
    severity=Severity.ERROR,
    category=TestCategory.STRUCTURE,
    message="Description lisible"
)

engine.register_rules([rule])
```

### Ajouter un Scénario GEVR

```python
scenario = GEVRScenario(
    scenario_id=Vector("Scenario:MyScenario"),
    description="Description du pipeline",
    steps=[
        GEVRStep(
            step_id="S1-GET",
            action=GEVRAction.GET,
            target=Vector("Object:MyObject"),
            inputs={},
            conditions=[],
            expected_outputs=["bundle"]
        ),
        # ... autres étapes
    ],
    tags=["custom", "pipeline"]
)

engine.register_scenarios([scenario])
```

### Ajouter un Générateur Custom

```python
class MyCustomGenerator(TestGenerator):
    def generate(self, context: Dict[str, Any]) -> List[MetaTest]:
        tests = []
        # ... logique de génération
        return tests

engine.generators.append(MyCustomGenerator())
```

---

## 6. Checklist de Validation

- [x] **Niveaux de tests bien définis** : Structure, Relations, Scénarios, Intégration
- [x] **`runMetaTests` couvre ces niveaux** : via scope, categories, tags
- [x] **Exemples fournis** : rapports console et JSON
- [x] **Cas de test** : 9 tests d'intégration + génération dynamique
- [x] **Extensible** : générateurs custom, rules, scénarios
- [x] **Lisible** : rapports clairs, export JSON
- [x] **Fréquent** : exécution rapide (<1s sur fractale exemple)

---

## 7. Fichiers Livrés

| Fichier | Description |
|---------|-------------|
| `eurekai_meta_tests.py` | Module Python complet (~1500 lignes) |
| `G2_10_MetaTests_Documentation.md` | Cette documentation |

---

*Module G2/10 — EUREKAI System*
