# E2/8 — MODE IA ASSISTÉE (AGENTS IA CADRÉS PAR EUREKAI)

> **Version alignée sur E1/7 ALIGNED, D1 (GEVR Engine), D3 (Orchestrate)**

## Vue d'ensemble

Le Mode IA Assistée définit le cadre d'interaction entre des agents IA externes (ChatGPT, Claude, etc.) et le système EUREKAI. L'objectif est de **déléguer le travail répétitif** (complétion, génération, refactoring) tout en **préservant le contrôle stratégique et structurel** par l'humain et le noyau EUREKAI.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ZONE EXTERNE                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│   │   ChatGPT    │    │    Claude    │    │   Autre IA   │              │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│          │                   │                   │                       │
│          └───────────────────┼───────────────────┘                       │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      AI GATEWAY (E2) — Garde-Fous                        │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐               │
│  │ Authentication │ │ Rate Limiting  │ │ Intent Parsing │               │
│  └────────────────┘ └────────────────┘ └────────────────┘               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐               │
│  │ Mode Checker   │ │ Layer Enforcer │ │ AI Interceptor │               │
│  └────────────────┘ └────────────────┘ └────────────────┘               │
│                    ┌────────────────┐                                    │
│                    │  Audit Logger  │                                    │
│                    └────────────────┘                                    │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        SUPER LAYER (E1)                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Create   │ │  Read    │ │  Update  │ │  Delete  │ │ Evaluate │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                        ┌──────────────┐                                  │
│                        │ Orchestrate  │                                  │
│                        └──────────────┘                                  │
│                        ┌──────────────┐                                  │
│                        │ SuperRouter  │                                  │
│                        └──────────────┘                                  │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATE LAYER (D3)                                │
│         ScenarioCatalog → ScenarioSelector → OrchestrationPlan           │
│         RequestTypes: IDEA | ANALYZE | VALIDATE | TRANSFORM              │
│         + AI Scenarios: Scenario.AI.Suggest | Scenario.AI.AutoReview     │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      GEVR ENGINE (D1)                                    │
│              Get → Execute → Validate → Render                           │
│                       HandlerRegistry                                    │
│         + AI Handlers: ai_validate_layer | ai_create_suggestion          │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              ERK (B3) + MetaRelations (C3)                               │
│                       (Layer 0 = INTOUCHABLE)                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 1. PROFILS D'AGENTS IA

### 1.1 Définition d'un Agent IA EUREKAI

Un **Agent IA EUREKAI** est une instance d'IA externe (ChatGPT, Claude, ou autre) qui interagit avec le système EUREKAI selon des règles strictement définies.

```python
class AIAgentProfile:
    id: str                          # Identifiant unique de l'agent
    name: str                        # Nom lisible (ex: "Claude-Assistant-01")
    provider: str                    # "openai" | "anthropic" | "custom"
    mode: AIOperationMode            # Mode d'opération actif
    permissions: AIPermissions       # Matrice de permissions
    session_id: str | None           # Session active
    created_at: datetime
    last_active: datetime

class AIOperationMode:
    READ_ONLY = "read-only"          # Lecture seule
    SUGGEST_ONLY = "suggest-only"    # Propositions sans application
    AUTO_WITH_REVIEW = "auto-with-review"  # Application + diff obligatoire

class AIPermissions:
    # Permissions par SuperTool
    can_read: bool = True
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    can_evaluate: bool = True
    can_orchestrate: bool = False
    
    # Restrictions de scope
    allowed_bundles: list[str] = []  # Bundles accessibles (vide = tous Agence)
    denied_bundles: list[str] = ["core:*"]  # Toujours exclu: Core
    max_depth: int = 5               # Profondeur max dans le lineage
    
    # Restrictions d'opération
    require_dry_run: bool = True     # Force dry_run avant exécution
    require_human_approval: bool = True
    max_objects_per_operation: int = 10
```

### 1.2 Profils Prédéfinis

#### Profil: `AI_READER`

```python
AI_READER = AIAgentProfile(
    name="AI Reader",
    mode=AIOperationMode.READ_ONLY,
    permissions=AIPermissions(
        can_read=True,
        can_evaluate=True,
        can_create=False,
        can_update=False,
        can_delete=False,
        can_orchestrate=False,
        denied_bundles=["core:*"],
        require_human_approval=False  # Lecture = pas d'approbation
    )
)
```

**Cas d'usage:**
- Analyse de la structure d'un projet
- Audit de qualité
- Exploration pour comprendre le contexte
- Génération de rapports (lecture seule)

---

#### Profil: `AI_CONTRIBUTOR`

```python
AI_CONTRIBUTOR = AIAgentProfile(
    name="AI Contributor",
    mode=AIOperationMode.SUGGEST_ONLY,
    permissions=AIPermissions(
        can_read=True,
        can_evaluate=True,
        can_create=True,   # Via suggestion
        can_update=True,   # Via suggestion
        can_delete=False,  # Jamais
        can_orchestrate=False,
        denied_bundles=["core:*"],
        require_dry_run=True,
        require_human_approval=True,
        max_objects_per_operation=5
    )
)
```

**Cas d'usage:**
- Complétion de bundles incomplets
- Proposition de nouvelles tâches
- Suggestions de refactoring
- Génération de contenu (textes, descriptions)

---

#### Profil: `AI_AUTOMATOR`

```python
AI_AUTOMATOR = AIAgentProfile(
    name="AI Automator",
    mode=AIOperationMode.AUTO_WITH_REVIEW,
    permissions=AIPermissions(
        can_read=True,
        can_evaluate=True,
        can_create=True,
        can_update=True,
        can_delete=False,  # Jamais en automatique
        can_orchestrate=True,  # Peut composer des workflows
        denied_bundles=["core:*"],
        require_dry_run=True,
        require_human_approval=True,  # Diff avant commit
        max_objects_per_operation=20
    )
)
```

**Cas d'usage:**
- Workflows de génération de masse
- Refactoring automatisé avec validation
- Synchronisation de données externes
- Pipelines de traitement

---

### 1.3 Matrice des Interdictions Absolues

| Action | AI_READER | AI_CONTRIBUTOR | AI_AUTOMATOR | Justification |
|--------|-----------|----------------|--------------|---------------|
| Accès Layer 0 (Core) | ❌ | ❌ | ❌ | Protection structurelle |
| Suppression d'objets | ❌ | ❌ | ❌ | Irréversibilité |
| Modification MetaRules | ❌ | ❌ | ❌ | Gouvernance critique |
| Déploiement production | ❌ | ❌ | ❌ | Décision humaine |
| Création de profils IA | ❌ | ❌ | ❌ | Escalade interdite |
| Accès aux secrets | ❌ | ❌ | ❌ | Sécurité |
| Bypass du Gateway | ❌ | ❌ | ❌ | Architecture |

---

## 2. MODES DE FONCTIONNEMENT

### 2.1 Mode `read-only`

```
┌─────────────────────────────────────────────────────────────┐
│                     MODE READ-ONLY                          │
│                                                             │
│  IA ──[SuperRead]──> EUREKAI ──[Data]──> IA                │
│  IA ──[SuperEvaluate]──> EUREKAI ──[Report]──> IA          │
│                                                             │
│  ❌ SuperCreate, SuperUpdate, SuperDelete, SuperOrchestrate │
└─────────────────────────────────────────────────────────────┘
```

**Comportement:**
- L'IA peut uniquement lire et évaluer
- Aucune modification de données
- Aucune validation humaine requise
- Logging minimal (accès uniquement)

**API disponible:**

```python
# Autorisé
Super.read(params)
Super.evaluate(params)

# Bloqué → AIPermissionError
Super.create(params)  # Raises: "Operation CREATE denied in READ_ONLY mode"
Super.update(params)  # Raises: "Operation UPDATE denied in READ_ONLY mode"
Super.delete(params)  # Raises: "Operation DELETE always denied for AI agents"
```

---

### 2.2 Mode `suggest-only`

```
┌─────────────────────────────────────────────────────────────┐
│                    MODE SUGGEST-ONLY                        │
│                                                             │
│  IA ──[Intent]──> Gateway                                  │
│                      │                                      │
│                      ▼                                      │
│              ┌──────────────┐                               │
│              │  Dry Run     │                               │
│              │  Obligatoire │                               │
│              └──────┬───────┘                               │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │  Suggestion  │──> File d'attente             │
│              │  Générée     │    validation humaine         │
│              └──────────────┘                               │
│                                                             │
│  ⏳ Attente validation → Humain accepte/refuse/modifie     │
└─────────────────────────────────────────────────────────────┘
```

**Comportement:**
- L'IA génère des **suggestions** (dry_run forcé)
- Chaque suggestion est mise en **file d'attente**
- Un humain doit **valider**, **refuser**, ou **modifier**
- L'IA reçoit le feedback après décision

**Structure d'une Suggestion:**

```python
class AISuggestion:
    id: str
    agent_id: str
    timestamp: datetime
    
    # Contexte
    intent: str                      # Ce que l'IA voulait faire
    reasoning: str                   # Pourquoi (optionnel)
    
    # Opération proposée
    operation: str                   # "create" | "update"
    super_tool_params: dict          # Paramètres complets
    dry_run_result: SuperResult      # Résultat du dry_run
    
    # Diff lisible
    diff: SuggestionDiff
    
    # Statut
    status: "pending" | "approved" | "rejected" | "modified"
    reviewed_by: str | None
    reviewed_at: datetime | None
    feedback: str | None

class SuggestionDiff:
    summary: str                     # Résumé en une ligne
    before: dict | None              # État avant (si update)
    after: dict                      # État après proposé
    changes: list[DiffEntry]         # Liste détaillée
    impact: ImpactAnalysis           # Objets impactés
```

---

### 2.3 Mode `auto-with-review`

```
┌─────────────────────────────────────────────────────────────┐
│                   MODE AUTO-WITH-REVIEW                     │
│                                                             │
│  IA ──[Intent]──> Gateway                                  │
│                      │                                      │
│                      ▼                                      │
│              ┌──────────────┐                               │
│              │  Dry Run     │                               │
│              └──────┬───────┘                               │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │  Exécution   │                               │
│              │  Réelle      │                               │
│              └──────┬───────┘                               │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │  Diff Généré │──> Notification immédiate     │
│              └──────┬───────┘                               │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │ Review Queue │──> Humain: commit/rollback    │
│              └──────────────┘                               │
│                                                             │
│  ⏳ Window de review (ex: 15min) avant commit définitif    │
└─────────────────────────────────────────────────────────────┘
```

**Comportement:**
- L'IA exécute réellement les opérations
- Un **diff complet** est généré automatiquement
- Les changements sont en état **"staged"** (non commités)
- Fenêtre de review configurable (défaut: 15 minutes)
- L'humain peut **commit**, **rollback**, ou **modifier**
- Auto-commit après expiration de la fenêtre (configurable)

**Structure d'un Review:**

```python
class AIAutoReview:
    id: str
    agent_id: str
    execution_id: str
    
    # Timing
    executed_at: datetime
    review_window: timedelta        # Fenêtre de review
    expires_at: datetime
    
    # Changements appliqués (staged)
    operations: list[ExecutedOperation]
    diff: CompleteDiff
    rollback_plan: RollbackPlan
    
    # Statut
    status: "pending_review" | "committed" | "rolled_back" | "modified"
    reviewed_by: str | None
    reviewed_at: datetime | None
    
class ExecutedOperation:
    super_tool: str
    params: dict
    result: SuperResult
    version_id: str                  # Pour rollback
    
class RollbackPlan:
    steps: list[RollbackStep]
    estimated_impact: int            # Nombre d'objets affectés
    reversible: bool                 # 100% réversible?
```

---

## 3. PROTOCOLES D'INTERACTION

### 3.1 Protocole Général

Toute interaction IA ↔ EUREKAI suit ce protocole:

```
┌─────────────────────────────────────────────────────────────┐
│                  PROTOCOLE D'INTERACTION                    │
│                                                             │
│  1. AUTHENTICATE                                            │
│     IA ──[Credentials]──> Gateway                          │
│     Gateway ──[Session + Profile]──> IA                    │
│                                                             │
│  2. DECLARE INTENT                                          │
│     IA ──[Intent JSON]──> Gateway                          │
│     Gateway ──[Validation + Mode]──> IA                    │
│                                                             │
│  3. EXECUTE (via SuperTools)                               │
│     IA ──[SuperTool Call]──> Gateway ──> Super Layer       │
│     Super Layer ──[Result]──> Gateway ──> IA               │
│                                                             │
│  4. AWAIT REVIEW (si applicable)                           │
│     Gateway ──[Review Request]──> Humain                   │
│     Humain ──[Decision]──> Gateway                         │
│     Gateway ──[Final Status]──> IA                         │
│                                                             │
│  5. CLOSE SESSION                                           │
│     IA ──[End]──> Gateway                                  │
│     Gateway ──[Summary + Logs]──> Audit                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Protocole: Complétion de Bundle

**Scénario:** L'IA doit compléter les champs manquants d'un projet.

```yaml
# STEP 1: Lecture du contexte
intent:
  action: "complete_bundle"
  target: "project:acme-site-vitrine"
  scope: "missing_fields"

# STEP 2: Appel SuperRead
call:
  tool: "SuperRead"
  params:
    id: "project:acme-site-vitrine"
    options:
      include_children: true
      view: "completion_audit"

# STEP 3: Appel SuperEvaluate
call:
  tool: "SuperEvaluate"
  params:
    target:
      id: "project:acme-site-vitrine"
    evaluators: ["completeness"]
    options:
      include_recommendations: true

# STEP 4: Génération des suggestions
# (L'IA analyse les champs manquants et propose des valeurs)

# STEP 5: Appel SuperUpdate (dry_run obligatoire)
call:
  tool: "SuperUpdate"
  params:
    id: "project:acme-site-vitrine"
    changes:
      set:
        description: "Refonte complète du site vitrine ACME Corp..."
        target_audience: "B2B - PME industrielles"
        success_metrics: ["temps_chargement < 2s", "conversion > 3%"]
    options:
      dry_run: true  # OBLIGATOIRE en suggest-only

# STEP 6: Suggestion mise en queue
result:
  type: "suggestion"
  id: "sugg_abc123"
  status: "pending_human_review"
  diff:
    summary: "Complétion de 3 champs sur project:acme-site-vitrine"
    changes:
      - field: "description"
        before: null
        after: "Refonte complète du site vitrine ACME Corp..."
      - field: "target_audience"
        before: null
        after: "B2B - PME industrielles"
      - field: "success_metrics"
        before: []
        after: ["temps_chargement < 2s", "conversion > 3%"]
```

### 3.3 Protocole: Proposition de Structure

**Scénario:** L'IA propose une nouvelle arborescence de tâches.

```yaml
# STEP 1: Intent
intent:
  action: "propose_structure"
  context: "project:acme-site-vitrine"
  request: "Créer l'arborescence des tâches pour la phase UX/UI"

# STEP 2: Lecture du contexte existant
call:
  tool: "SuperRead"
  params:
    id: "project:acme-site-vitrine"
    options:
      include_children: true
      view: "structure"

# STEP 3: Génération du plan (interne à l'IA)
# L'IA génère un plan structuré...

# STEP 4: Soumission du plan pour validation
plan:
  type: "structure_proposal"
  parent: "project:acme-site-vitrine"
  proposed_objects:
    - type: "TaskGroup"
      name: "Phase UX Research"
      children:
        - type: "Task"
          name: "Audit ergonomique existant"
          estimated_hours: 8
        - type: "Task"
          name: "Interviews utilisateurs"
          estimated_hours: 16
    - type: "TaskGroup"
      name: "Phase UI Design"
      children:
        - type: "Task"
          name: "Maquettes wireframe"
          estimated_hours: 24
        - type: "Task"
          name: "Design system"
          estimated_hours: 16

# STEP 5: Attente validation humaine
# L'humain reçoit le plan et peut:
# - Approuver tel quel → Exécution via SuperOrchestrate
# - Modifier → Ajustements puis approbation
# - Refuser → Feedback à l'IA

# STEP 6: Si approuvé, exécution via workflow
call:
  tool: "SuperOrchestrate"
  params:
    workflow:
      name: "create_task_structure"
      steps:
        - id: "create_ux_group"
          action: "create"
          params:
            type: "TaskGroup"
            parent_id: "project:acme-site-vitrine"
            data:
              name: "Phase UX Research"
        - id: "create_audit_task"
          action: "create"
          params:
            type: "Task"
            parent_id: "{{outputs.create_ux_group.object_id}}"
            data:
              name: "Audit ergonomique existant"
              estimated_hours: 8
          depends_on: ["create_ux_group"]
        # ... autres étapes
```

### 3.4 Protocole: Refactoring avec Review

**Scénario:** L'IA propose un refactoring de la nomenclature (mode auto-with-review).

```yaml
# STEP 1: Intent
intent:
  action: "refactor"
  type: "naming_convention"
  scope: "bundle:agence:projects"
  pattern:
    from: "snake_case"
    to: "kebab-case"

# STEP 2: Analyse de l'impact
call:
  tool: "SuperRead"
  params:
    query:
      type: "Project"
      filters:
        bundle: "agence"
      limit: 100

# STEP 3: Dry run des modifications
call:
  tool: "SuperUpdate"
  params:
    batch:
      - id: "project:old_project_name"
        changes:
          rename: "old-project-name"
      - id: "project:another_old_name"
        changes:
          rename: "another-old-name"
    options:
      dry_run: true

# STEP 4: Exécution réelle (mode auto)
call:
  tool: "SuperUpdate"
  params:
    # ... mêmes params
    options:
      dry_run: false
      create_version: true  # Snapshot pour rollback

# STEP 5: Diff généré automatiquement
review:
  id: "review_xyz789"
  status: "pending_review"
  expires_at: "2025-06-01T15:30:00Z"
  diff:
    summary: "Renommage de 47 projets (snake_case → kebab-case)"
    objects_modified: 47
    sample:
      - before: "project:old_project_name"
        after: "project:old-project-name"
      - before: "project:another_old_name"
        after: "project:another-old-name"
  rollback:
    available: true
    command: "Super.orchestrate(rollback_plan)"

# STEP 6: Décision humaine
# - commit → Changements définitifs
# - rollback → Restauration des versions
# - modify → Corrections manuelles + commit
```

---

## 4. GATEWAY IA (GARDE-FOUS)

### 4.1 Architecture du Gateway

```python
class AIGateway:
    """
    Point d'entrée unique pour toutes les interactions IA → EUREKAI.
    Applique les garde-fous et le logging.
    """
    
    def __init__(self):
        self.auth_service = AIAuthService()
        self.rate_limiter = AIRateLimiter()
        self.intent_parser = AIIntentParser()
        self.mode_checker = AIModeChecker()
        self.layer_enforcer = LayerEnforcer()
        self.audit_logger = AIAuditLogger()
        self.suggestion_queue = SuggestionQueue()
        self.review_queue = ReviewQueue()
    
    async def process_request(
        self,
        agent_id: str,
        request: AIRequest
    ) -> AIResponse:
        """Pipeline de traitement d'une requête IA."""
        
        # 1. Authentification
        session = await self.auth_service.validate(agent_id, request.token)
        if not session:
            return AIResponse.error("AUTH_FAILED", "Invalid credentials")
        
        # 2. Rate limiting
        if not await self.rate_limiter.allow(agent_id):
            return AIResponse.error("RATE_LIMITED", "Too many requests")
        
        # 3. Parsing de l'intent
        intent = await self.intent_parser.parse(request)
        
        # 4. Vérification du mode
        mode_check = await self.mode_checker.check(session.profile, intent)
        if not mode_check.allowed:
            return AIResponse.error("MODE_DENIED", mode_check.reason)
        
        # 5. Vérification Layer (CRITIQUE)
        layer_check = await self.layer_enforcer.check(intent)
        if not layer_check.allowed:
            await self.audit_logger.log_violation(agent_id, intent, layer_check)
            return AIResponse.error("LAYER_VIOLATION", 
                "Access to Core (Layer 0) is forbidden for AI agents")
        
        # 6. Exécution selon le mode
        result = await self._execute_by_mode(session, intent)
        
        # 7. Logging
        await self.audit_logger.log_operation(agent_id, intent, result)
        
        return result
```

### 4.2 Layer Enforcer

```python
class LayerEnforcer:
    """
    Garde-fou CRITIQUE: empêche tout accès IA au Layer 0.
    """
    
    LAYER_0_PATTERNS = [
        "core:*",
        "metarule:*",
        "schema:*",
        "security:*",
        "config:system:*",
    ]
    
    FORBIDDEN_OPERATIONS = [
        ("delete", "*"),           # Suppression toujours interdite
        ("update", "metarule:*"),  # MetaRules intouchables
        ("create", "core:*"),      # Création dans Core interdite
    ]
    
    def check(self, intent: AIIntent) -> LayerCheckResult:
        """Vérifie si l'intent respecte les restrictions de Layer."""
        
        # Vérification des patterns Layer 0
        for target in intent.targets:
            for pattern in self.LAYER_0_PATTERNS:
                if self._matches(target, pattern):
                    return LayerCheckResult(
                        allowed=False,
                        reason=f"Target '{target}' is in protected Layer 0",
                        violation_type="LAYER_0_ACCESS"
                    )
        
        # Vérification des opérations interdites
        for (op, pattern) in self.FORBIDDEN_OPERATIONS:
            if intent.operation == op:
                for target in intent.targets:
                    if self._matches(target, pattern):
                        return LayerCheckResult(
                            allowed=False,
                            reason=f"Operation '{op}' forbidden on '{target}'",
                            violation_type="FORBIDDEN_OPERATION"
                        )
        
        return LayerCheckResult(allowed=True)
    
    def _matches(self, target: str, pattern: str) -> bool:
        """Match avec wildcards."""
        if pattern.endswith("*"):
            return target.startswith(pattern[:-1])
        return target == pattern
```

### 4.3 Audit Logger

```python
class AIAuditLogger:
    """
    Logging complet de toutes les interactions IA.
    Traçabilité totale pour audit et debugging.
    """
    
    async def log_operation(
        self,
        agent_id: str,
        intent: AIIntent,
        result: AIResponse
    ) -> str:
        """Log une opération normale."""
        
        log_entry = AIAuditLog(
            id=generate_uuid(),
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            
            # Intent
            operation=intent.operation,
            targets=intent.targets,
            params_hash=hash_params(intent.params),  # Hash, pas les données
            
            # Résultat
            success=result.success,
            status=result.status,
            objects_affected=result.affected_count,
            
            # Contexte
            session_id=intent.session_id,
            mode=intent.mode,
            dry_run=intent.dry_run,
            
            # Review (si applicable)
            suggestion_id=result.suggestion_id,
            review_id=result.review_id
        )
        
        await self.store.save(log_entry)
        return log_entry.id
    
    async def log_violation(
        self,
        agent_id: str,
        intent: AIIntent,
        check_result: LayerCheckResult
    ) -> str:
        """Log une tentative de violation (CRITIQUE)."""
        
        violation_log = AIViolationLog(
            id=generate_uuid(),
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            severity="CRITICAL",
            
            # Détails de la violation
            violation_type=check_result.violation_type,
            attempted_operation=intent.operation,
            attempted_targets=intent.targets,
            blocked_reason=check_result.reason,
            
            # Contexte complet pour investigation
            full_intent=intent.to_dict(),  # Capture complète
            
            # Alerting
            alert_sent=True,
            alert_channels=["email:admin", "slack:security"]
        )
        
        await self.store.save(violation_log)
        await self.alerter.send_critical_alert(violation_log)
        
        return violation_log.id
```

---

## 5. EXEMPLES DE SESSIONS

### 5.1 Session: Analyse de Projet (read-only)

```
═══════════════════════════════════════════════════════════════
SESSION: AI_READER analyse le projet ACME
═══════════════════════════════════════════════════════════════

[14:00:00] IA → Gateway: AUTHENTICATE
{
  "agent_id": "claude-reader-01",
  "token": "eyJ...",
  "requested_mode": "read-only"
}

[14:00:00] Gateway → IA: SESSION_CREATED
{
  "session_id": "sess_abc123",
  "profile": "AI_READER",
  "mode": "read-only",
  "expires_at": "2025-06-01T15:00:00Z"
}

───────────────────────────────────────────────────────────────

[14:00:05] IA → Gateway: SUPER_READ
{
  "tool": "SuperRead",
  "params": {
    "id": "project:acme-site-vitrine",
    "options": {
      "include_children": true,
      "view": "detailed"
    }
  }
}

[14:00:06] Gateway → IA: RESULT
{
  "success": true,
  "data": {
    "id": "project:acme-site-vitrine",
    "name": "Site Vitrine ACME",
    "status": "in_progress",
    "progress": 35,
    "children": [
      {"id": "task:maquettes-desktop", "status": "done"},
      {"id": "task:integration", "status": "pending"},
      ...
    ]
  }
}

───────────────────────────────────────────────────────────────

[14:00:10] IA → Gateway: SUPER_EVALUATE
{
  "tool": "SuperEvaluate",
  "params": {
    "target": {"id": "project:acme-site-vitrine"},
    "evaluators": ["completeness", "consistency"],
    "options": {"include_recommendations": true}
  }
}

[14:00:12] Gateway → IA: RESULT
{
  "success": true,
  "overall_score": 0.72,
  "issues": [
    {
      "severity": "warning",
      "code": "MISSING_FIELD",
      "message": "description is empty",
      "location": "project:acme-site-vitrine.description"
    }
  ],
  "recommendations": [
    "Add project description to improve clarity",
    "Define success_metrics for better tracking"
  ]
}

───────────────────────────────────────────────────────────────

[14:00:15] IA → Gateway: END_SESSION
{
  "session_id": "sess_abc123"
}

[14:00:15] Gateway → IA: SESSION_CLOSED
{
  "summary": {
    "operations": 2,
    "reads": 2,
    "writes": 0,
    "duration": "15s"
  }
}

═══════════════════════════════════════════════════════════════
AUDIT LOG: Session sess_abc123 completed (read-only, no mutations)
═══════════════════════════════════════════════════════════════
```

### 5.2 Session: Complétion avec Suggestion (suggest-only)

```
═══════════════════════════════════════════════════════════════
SESSION: AI_CONTRIBUTOR complète le projet ACME
═══════════════════════════════════════════════════════════════

[14:30:00] IA → Gateway: AUTHENTICATE
{
  "agent_id": "claude-contributor-01",
  "requested_mode": "suggest-only"
}

[14:30:00] Gateway → IA: SESSION_CREATED
{
  "session_id": "sess_def456",
  "profile": "AI_CONTRIBUTOR",
  "mode": "suggest-only"
}

───────────────────────────────────────────────────────────────

[14:30:05] IA → Gateway: INTENT
{
  "action": "complete_missing_fields",
  "target": "project:acme-site-vitrine"
}

[14:30:05] Gateway → IA: INTENT_ACCEPTED
{
  "intent_id": "int_xyz",
  "requires": ["read", "suggest"],
  "mode_enforced": "suggest-only"
}

───────────────────────────────────────────────────────────────

[14:30:10] IA → Gateway: SUPER_READ
{ ... lecture du projet ... }

[14:30:11] Gateway → IA: RESULT
{ ... données projet + champs manquants identifiés ... }

───────────────────────────────────────────────────────────────

[14:30:20] IA → Gateway: SUPER_UPDATE (suggestion)
{
  "tool": "SuperUpdate",
  "params": {
    "id": "project:acme-site-vitrine",
    "changes": {
      "set": {
        "description": "Refonte complète du site vitrine ACME Corp. 
                        Objectif: moderniser l'image de marque et 
                        améliorer la conversion des visiteurs B2B.",
        "target_audience": "PME industrielles - Décideurs et acheteurs",
        "success_metrics": [
          "Temps de chargement < 2s",
          "Taux de conversion > 3%",
          "Taux de rebond < 40%"
        ]
      }
    },
    "options": {
      "dry_run": true
    }
  },
  "reasoning": "Based on project name 'Site Vitrine ACME' and existing 
                tasks (maquettes, integration), I inferred this is a 
                B2B corporate website redesign project."
}

[14:30:21] Gateway → IA: SUGGESTION_CREATED
{
  "suggestion_id": "sugg_ghi789",
  "status": "pending_human_review",
  "dry_run_result": {
    "would_modify": 3,
    "fields": ["description", "target_audience", "success_metrics"]
  },
  "diff": {
    "before": {
      "description": null,
      "target_audience": null,
      "success_metrics": []
    },
    "after": {
      "description": "Refonte complète du site vitrine...",
      "target_audience": "PME industrielles...",
      "success_metrics": ["Temps de chargement < 2s", ...]
    }
  },
  "message": "Suggestion created. Awaiting human review."
}

───────────────────────────────────────────────────────────────

[14:45:00] HUMAIN → Gateway: REVIEW_DECISION
{
  "suggestion_id": "sugg_ghi789",
  "decision": "approved",
  "modifications": {
    "success_metrics": [
      "Temps de chargement < 2s",
      "Taux de conversion > 2.5%",  // Modifié par l'humain
      "Taux de rebond < 45%"         // Modifié par l'humain
    ]
  },
  "feedback": "Good analysis, but conversion and bounce rate 
               targets were too aggressive for B2B."
}

[14:45:01] Gateway → IA: SUGGESTION_APPLIED
{
  "suggestion_id": "sugg_ghi789",
  "status": "approved_with_modifications",
  "applied_at": "2025-06-01T14:45:01Z",
  "feedback": "Good analysis, but conversion and bounce rate 
               targets were too aggressive for B2B."
}

═══════════════════════════════════════════════════════════════
AUDIT LOG: Suggestion sugg_ghi789 approved (modified) by user:nathalie
═══════════════════════════════════════════════════════════════
```

### 5.3 Session: Tentative de Violation (bloquée)

```
═══════════════════════════════════════════════════════════════
SESSION: AI_CONTRIBUTOR tente d'accéder au Core (VIOLATION)
═══════════════════════════════════════════════════════════════

[15:00:00] IA → Gateway: AUTHENTICATE
{
  "agent_id": "claude-contributor-01",
  "requested_mode": "suggest-only"
}

[15:00:00] Gateway → IA: SESSION_CREATED
{
  "session_id": "sess_jkl012",
  "profile": "AI_CONTRIBUTOR",
  "mode": "suggest-only"
}

───────────────────────────────────────────────────────────────

[15:00:10] IA → Gateway: SUPER_READ (tentative Layer 0)
{
  "tool": "SuperRead",
  "params": {
    "id": "core:metarules:naming-convention"
  }
}

[15:00:10] Gateway → IA: ERROR (LAYER_VIOLATION)
{
  "error": "LAYER_VIOLATION",
  "code": "E403_LAYER_0_ACCESS",
  "message": "Access to Core (Layer 0) is forbidden for AI agents. 
              Target 'core:metarules:naming-convention' is protected.",
  "severity": "CRITICAL",
  "logged": true,
  "alert_sent": true
}

───────────────────────────────────────────────────────────────

[15:00:15] IA → Gateway: SUPER_UPDATE (tentative modification MetaRule)
{
  "tool": "SuperUpdate",
  "params": {
    "id": "metarule:object-naming",
    "changes": {
      "set": {
        "pattern": ".*"  // Tentative de désactiver la règle
      }
    }
  }
}

[15:00:15] Gateway → IA: ERROR (FORBIDDEN_OPERATION)
{
  "error": "FORBIDDEN_OPERATION",
  "code": "E403_METARULE_PROTECTED",
  "message": "Operation 'update' is absolutely forbidden on MetaRules. 
              This is a structural protection that cannot be bypassed.",
  "severity": "CRITICAL",
  "logged": true,
  "alert_sent": true,
  "session_impact": "Session flagged for review. 
                     Multiple violations may result in suspension."
}

───────────────────────────────────────────────────────────────

[15:00:20] Gateway → IA: SESSION_WARNING
{
  "warning": "Your session has accumulated 2 CRITICAL violations. 
              Further violations will result in automatic session 
              termination and agent review.",
  "violations_count": 2,
  "max_allowed": 3
}

═══════════════════════════════════════════════════════════════
SECURITY ALERT: Agent claude-contributor-01 attempted Layer 0 access
                Violations logged: violation_001, violation_002
                Admin notified: email:nathalie, slack:security
═══════════════════════════════════════════════════════════════
```

---

## 6. CAS DE TEST

### 6.1 Tests: Agent Discipliné

```python
class TestDisciplinedAgent:
    """Tests pour un agent IA qui respecte les règles."""
    
    def test_read_only_respects_mode(self):
        """Un AI_READER ne peut que lire."""
        agent = create_agent(profile=AI_READER)
        session = gateway.authenticate(agent)
        
        # Lecture OK
        result = gateway.process(session, SuperRead(id="project:test"))
        assert result.success
        
        # Évaluation OK
        result = gateway.process(session, SuperEvaluate(target={"id": "project:test"}))
        assert result.success
        
        # Création BLOQUÉE
        result = gateway.process(session, SuperCreate(type="Task", data={}))
        assert not result.success
        assert result.error.code == "MODE_DENIED"
    
    def test_suggest_only_creates_suggestions(self):
        """Un AI_CONTRIBUTOR crée des suggestions, pas des objets."""
        agent = create_agent(profile=AI_CONTRIBUTOR)
        session = gateway.authenticate(agent)
        
        result = gateway.process(session, SuperUpdate(
            id="project:test",
            changes={"set": {"name": "New Name"}},
            options={"dry_run": True}
        ))
        
        assert result.success
        assert result.type == "suggestion"
        assert result.suggestion_id is not None
        assert result.status == "pending_human_review"
        
        # Vérifier que l'objet N'A PAS été modifié
        obj = Super.read(id="project:test")
        assert obj.data.name != "New Name"
    
    def test_auto_with_review_creates_staged_changes(self):
        """Un AI_AUTOMATOR crée des changements staged."""
        agent = create_agent(profile=AI_AUTOMATOR)
        session = gateway.authenticate(agent)
        
        result = gateway.process(session, SuperUpdate(
            id="project:test",
            changes={"set": {"status": "completed"}},
            options={"dry_run": False}
        ))
        
        assert result.success
        assert result.type == "review"
        assert result.review_id is not None
        assert result.status == "pending_review"
        assert result.rollback_available == True
        
        # L'objet EST modifié mais en état "staged"
        obj = Super.read(id="project:test")
        assert obj.data.status == "completed"
        assert obj.meta.staged == True
        assert obj.meta.staged_by == session.agent_id
```

### 6.2 Tests: Agent Qui Teste les Limites

```python
class TestBoundaryAgent:
    """Tests pour un agent qui tente de contourner les règles."""
    
    def test_layer_0_access_blocked(self):
        """Tout accès Layer 0 est bloqué."""
        agent = create_agent(profile=AI_AUTOMATOR)  # Profil le plus permissif
        session = gateway.authenticate(agent)
        
        # Tentative de lecture Core
        result = gateway.process(session, SuperRead(id="core:schemas:task"))
        assert not result.success
        assert result.error.code == "E403_LAYER_0_ACCESS"
        
        # Vérifier l'alerte
        assert security_alerts.count() == 1
        assert security_alerts.last().severity == "CRITICAL"
    
    def test_delete_always_blocked(self):
        """La suppression est TOUJOURS bloquée pour les IA."""
        agent = create_agent(profile=AI_AUTOMATOR)
        session = gateway.authenticate(agent)
        
        result = gateway.process(session, SuperDelete(id="project:test"))
        
        assert not result.success
        assert result.error.code == "E403_DELETE_FORBIDDEN"
        assert "AI agents cannot delete objects" in result.error.message
    
    def test_metarule_modification_blocked(self):
        """Les MetaRules sont intouchables."""
        agent = create_agent(profile=AI_AUTOMATOR)
        session = gateway.authenticate(agent)
        
        result = gateway.process(session, SuperUpdate(
            id="metarule:naming-convention",
            changes={"set": {"enabled": False}}
        ))
        
        assert not result.success
        assert result.error.code == "E403_METARULE_PROTECTED"
    
    def test_forced_execution_blocked(self):
        """Impossible de forcer l'exécution sans dry_run."""
        agent = create_agent(profile=AI_CONTRIBUTOR)
        session = gateway.authenticate(agent)
        
        # Tentative de bypass du dry_run
        result = gateway.process(session, SuperUpdate(
            id="project:test",
            changes={"set": {"name": "Hacked"}},
            options={"dry_run": False}  # Tentative
        ))
        
        # Le Gateway force dry_run=True pour suggest-only
        assert result.success
        assert result.type == "suggestion"  # Pas d'exécution réelle
        assert result.dry_run_enforced == True
    
    def test_rate_limiting_enforced(self):
        """Le rate limiting protège contre l'abus."""
        agent = create_agent(profile=AI_READER)
        session = gateway.authenticate(agent)
        
        # Burst de requêtes
        for i in range(100):
            result = gateway.process(session, SuperRead(id=f"project:test-{i}"))
            if not result.success and result.error.code == "E429_RATE_LIMITED":
                break
        
        # Rate limiting déclenché avant 100 requêtes
        assert i < 100
        assert result.error.code == "E429_RATE_LIMITED"
    
    def test_session_suspension_after_violations(self):
        """Trop de violations = session suspendue."""
        agent = create_agent(profile=AI_CONTRIBUTOR)
        session = gateway.authenticate(agent)
        
        # 3 tentatives de violation
        for _ in range(3):
            gateway.process(session, SuperRead(id="core:secrets"))
        
        # La 4ème requête échoue (session suspendue)
        result = gateway.process(session, SuperRead(id="project:test"))  # Légal
        
        assert not result.success
        assert result.error.code == "E403_SESSION_SUSPENDED"
        assert "Multiple security violations" in result.error.message
```

### 6.3 Tests: Workflow Complet

```python
class TestCompleteWorkflow:
    """Tests de workflows complets IA ↔ EUREKAI ↔ Humain."""
    
    def test_suggestion_approval_workflow(self):
        """Workflow complet: suggestion → review → approval → apply."""
        
        # PHASE 1: L'IA crée une suggestion
        agent = create_agent(profile=AI_CONTRIBUTOR)
        session = gateway.authenticate(agent)
        
        suggestion_result = gateway.process(session, SuperUpdate(
            id="project:acme",
            changes={"set": {"description": "New description by AI"}},
            options={"dry_run": True}
        ))
        
        assert suggestion_result.type == "suggestion"
        suggestion_id = suggestion_result.suggestion_id
        
        # PHASE 2: L'humain review et approuve
        human_decision = human_gateway.review(
            suggestion_id=suggestion_id,
            decision="approved",
            feedback="Looks good"
        )
        
        assert human_decision.success
        assert human_decision.status == "approved"
        
        # PHASE 3: Vérifier que le changement est appliqué
        obj = Super.read(id="project:acme")
        assert obj.data.description == "New description by AI"
        
        # PHASE 4: Vérifier le feedback à l'IA
        feedback = gateway.get_suggestion_status(session, suggestion_id)
        assert feedback.status == "approved"
        assert feedback.feedback == "Looks good"
    
    def test_suggestion_rejection_workflow(self):
        """Workflow: suggestion → review → rejection → feedback."""
        
        agent = create_agent(profile=AI_CONTRIBUTOR)
        session = gateway.authenticate(agent)
        
        suggestion_result = gateway.process(session, SuperCreate(
            type="Task",
            parent_id="project:acme",
            data={"name": "Unnecessary Task", "priority": 999}
        ))
        
        suggestion_id = suggestion_result.suggestion_id
        
        # L'humain rejette
        human_decision = human_gateway.review(
            suggestion_id=suggestion_id,
            decision="rejected",
            feedback="Priority 999 is unrealistic. Task not needed."
        )
        
        # Vérifier que l'objet N'A PAS été créé
        result = Super.read(query={"name": "Unnecessary Task"})
        assert len(result.data) == 0
        
        # L'IA reçoit le feedback
        feedback = gateway.get_suggestion_status(session, suggestion_id)
        assert feedback.status == "rejected"
        assert "Priority 999 is unrealistic" in feedback.feedback
    
    def test_auto_review_rollback_workflow(self):
        """Workflow auto: execute → review → rollback."""
        
        agent = create_agent(profile=AI_AUTOMATOR)
        session = gateway.authenticate(agent)
        
        # PHASE 1: L'IA exécute un changement
        review_result = gateway.process(session, SuperUpdate(
            id="project:acme",
            changes={"set": {"status": "cancelled"}}  # Changement risqué
        ))
        
        review_id = review_result.review_id
        assert review_result.status == "pending_review"
        
        # L'objet EST modifié (staged)
        obj = Super.read(id="project:acme")
        assert obj.data.status == "cancelled"
        
        # PHASE 2: L'humain rollback
        human_decision = human_gateway.review(
            review_id=review_id,
            decision="rollback",
            reason="Accidental status change, project is active"
        )
        
        assert human_decision.success
        assert human_decision.rollback_applied == True
        
        # PHASE 3: Vérifier le rollback
        obj = Super.read(id="project:acme")
        assert obj.data.status != "cancelled"  # Restauré
        
        # Vérifier le log
        audit = audit_log.get_by_review(review_id)
        assert audit.final_status == "rolled_back"
        assert audit.rollback_by == "user:nathalie"
```

---

## 7. CONFIGURATION ET DÉPLOIEMENT

### 7.1 Configuration des Profils

```yaml
# config/ai_profiles.yaml

profiles:
  AI_READER:
    mode: "read-only"
    permissions:
      can_read: true
      can_evaluate: true
      can_create: false
      can_update: false
      can_delete: false
      can_orchestrate: false
    restrictions:
      denied_bundles: ["core:*"]
      require_human_approval: false
    rate_limits:
      requests_per_minute: 60
      requests_per_hour: 500

  AI_CONTRIBUTOR:
    mode: "suggest-only"
    permissions:
      can_read: true
      can_evaluate: true
      can_create: true
      can_update: true
      can_delete: false
      can_orchestrate: false
    restrictions:
      denied_bundles: ["core:*"]
      require_dry_run: true
      require_human_approval: true
      max_objects_per_operation: 5
    rate_limits:
      requests_per_minute: 30
      suggestions_per_hour: 20

  AI_AUTOMATOR:
    mode: "auto-with-review"
    permissions:
      can_read: true
      can_evaluate: true
      can_create: true
      can_update: true
      can_delete: false
      can_orchestrate: true
    restrictions:
      denied_bundles: ["core:*"]
      require_dry_run: true
      require_human_approval: true
      max_objects_per_operation: 20
    review:
      window_minutes: 15
      auto_commit_on_expiry: false
    rate_limits:
      requests_per_minute: 20
      operations_per_hour: 50
```

### 7.2 Configuration de Sécurité

```yaml
# config/ai_security.yaml

security:
  # Protections Layer 0 (IMMUABLE)
  layer_0_protection:
    enabled: true  # Ne peut JAMAIS être désactivé
    protected_patterns:
      - "core:*"
      - "metarule:*"
      - "schema:*"
      - "security:*"
      - "config:system:*"
  
  # Opérations interdites
  forbidden_operations:
    - operation: "delete"
      target: "*"
      reason: "AI agents cannot delete objects"
    - operation: "update"
      target: "metarule:*"
      reason: "MetaRules are structurally protected"
    - operation: "create"
      target: "core:*"
      reason: "Core objects cannot be created by AI"
  
  # Gestion des violations
  violations:
    max_per_session: 3
    action_on_max: "suspend_session"
    alert_on_first: true
    alert_channels:
      - "email:admin@eurekai.io"
      - "slack:security-alerts"
  
  # Audit
  audit:
    log_all_operations: true
    log_params_hash: true      # Hash des params, pas les données
    retention_days: 365
    export_format: "json"

---

## 8. CHECKLIST DE VALIDATION

- [x] **Mode IA assistée défini clairement**
  - Trois profils: AI_READER, AI_CONTRIBUTOR, AI_AUTOMATOR
  - Trois modes: read-only, suggest-only, auto-with-review
  - Matrice de permissions explicite

- [x] **Actions IA passent uniquement par les SuperTools**
  - Gateway IA comme point d'entrée unique
  - Mapping direct: Intent → SuperTool Call
  - Pas d'accès direct à GEVR/ERK/MetaRules

- [x] **Garde-fous de sécurité**
  - Layer Enforcer: protection absolue du Core (Layer 0)
  - Suppression interdite pour tous les agents IA
  - MetaRules intouchables
  - Rate limiting par profil
  - Suspension automatique après violations

- [x] **Traçabilité complète**
  - AIAuditLogger pour toutes les opérations
  - AIViolationLog pour les tentatives interdites
  - Alertes automatiques en cas de violation critique

- [x] **Exemples fournis**
  - Session read-only (analyse)
  - Session suggest-only (complétion avec validation)
  - Session avec violation (blocage et alerte)

- [x] **Cas de test**
  - Agent discipliné (respect des modes)
  - Agent qui teste les limites (violations bloquées)
  - Workflows complets (suggestion → review → apply/rollback)

- [x] **Protocoles d'interaction documentés**
  - Protocole général (5 étapes)
  - Protocole complétion de bundle
  - Protocole proposition de structure
  - Protocole refactoring avec review

- [x] **Configuration déployable**
  - Fichiers YAML pour profils et sécurité
  - Paramètres ajustables (rate limits, review window, etc.)
  - Protection Layer 0 non désactivable

---

## 9. INTÉGRATION AVEC E1/7 ALIGNED (GEVR/D3)

### 9.1 Architecture d'intégration

Le Mode IA s'intègre **au-dessus** du SuperRouter, interceptant les appels avant qu'ils n'atteignent GEVR :

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI GATEWAY (E2)                                 │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐          │
│  │ Authentication │ │ Layer Enforcer │ │ Mode Checker   │          │
│  └────────────────┘ └────────────────┘ └────────────────┘          │
│                              │                                      │
│                    ┌─────────┴─────────┐                           │
│                    │   AI Interceptor  │                           │
│                    │   (dry_run, log)  │                           │
│                    └─────────┬─────────┘                           │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SUPER LAYER (E1)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │  Create  │ │   Read   │ │  Update  │ │  Delete  │               │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘               │
│       └────────────┴─────┬──────┴────────────┘                      │
│                    ┌─────┴─────┐                                    │
│                    │  Super    │                                    │
│                    │  Router   │                                    │
│                    └─────┬─────┘                                    │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATE LAYER (D3)                           │
│         ScenarioCatalog → ScenarioSelector → OrchestrationPlan      │
│         RequestTypes: IDEA, ANALYZE, VALIDATE, TRANSFORM            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GEVR ENGINE (D1)                               │
│              Get → Execute → Validate → Render                      │
│                    HandlerRegistry                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 AI Interceptor

```python
class AIInterceptor:
    """
    Intercepte les appels SuperTools pour appliquer les règles IA.
    S'insère entre AI Gateway et Super Layer.
    """
    
    def intercept(
        self,
        session: AISession,
        super_call: SuperToolCall
    ) -> InterceptResult:
        """
        Intercepte et modifie un appel SuperTool selon le mode IA.
        """
        
        # 1. Bloquer les opérations interdites
        if super_call.tool == "SuperDelete":
            return InterceptResult.blocked("DELETE_FORBIDDEN")
        
        # 2. Forcer dry_run en suggest-only
        if session.mode == AIOperationMode.SUGGEST_ONLY:
            if super_call.tool in ["SuperCreate", "SuperUpdate"]:
                super_call.params["dry_run"] = True  # FORCÉ
        
        # 3. Ajouter le contexte IA au scénario GEVR
        super_call.params["_ai_context"] = {
            "agent_id": session.agent_id,
            "mode": session.mode.value,
            "session_id": session.id
        }
        
        return InterceptResult.allow(super_call)
```

### 9.3 Scénarios GEVR pour l'IA

De nouveaux scénarios sont ajoutés au ScenarioCatalog pour les opérations IA :

```python
# Ajout au ScenarioCatalog (D3)
AI_SCENARIOS = {
    "Scenario.AI.Suggest": ScenarioCatalogEntry(
        id="Scenario.AI.Suggest",
        name="AI Suggestion",
        description="Création d'une suggestion IA avec validation différée",
        request_types=[RequestType.IDEA, RequestType.TRANSFORM],
        requires_human_approval=True
    ),
    
    "Scenario.AI.AutoReview": ScenarioCatalogEntry(
        id="Scenario.AI.AutoReview",
        name="AI Auto with Review",
        description="Exécution IA avec fenêtre de review",
        request_types=[RequestType.TRANSFORM, RequestType.ENRICH],
        requires_human_approval=True,
        review_window_minutes=15
    ),
    
    "Scenario.AI.Audit": ScenarioCatalogEntry(
        id="Scenario.AI.Audit",
        name="AI Audit Trail",
        description="Logging complet des actions IA",
        request_types=[RequestType.ANALYZE],
        always_log=True
    )
}
```

### 9.4 Mapping SuperTools ↔ Modes IA ↔ D3

| SuperTool | Scénario GEVR | AI_READER | AI_CONTRIBUTOR | AI_AUTOMATOR |
|-----------|---------------|-----------|----------------|--------------|
| SuperCreate | Scenario.Create | ❌ | ✅ (→ Scenario.AI.Suggest) | ✅ (→ Scenario.AI.AutoReview) |
| SuperRead | Scenario.Read | ✅ | ✅ | ✅ |
| SuperUpdate | Scenario.Update | ❌ | ✅ (→ Scenario.AI.Suggest) | ✅ (→ Scenario.AI.AutoReview) |
| SuperDelete | Scenario.Delete | ❌ | ❌ | ❌ |
| SuperEvaluate | Scenario.AnalyzeObject | ✅ | ✅ | ✅ |
| SuperOrchestrate | Via D3 Orchestrate | ❌ | ❌ | ✅ (→ Scenario.AI.AutoReview) |

### 9.5 Résultats enrichis pour traçabilité IA

```python
@dataclass
class AIEnrichedResult:
    """Résultat SuperTool enrichi pour le contexte IA."""
    
    # Résultat standard
    super_result: SuperCreateResult | SuperReadResult | ...
    
    # Contexte GEVR (pour traçabilité)
    gevr_result: ScenarioResult
    scenario_id: str
    
    # Contexte IA
    ai_context: AIContext
    suggestion_id: str | None = None
    review_id: str | None = None
    
    # Audit
    logged_at: datetime
    log_id: str

@dataclass 
class AIContext:
    agent_id: str
    mode: AIOperationMode
    session_id: str
    dry_run_enforced: bool
    human_approval_required: bool
```

### 9.6 Handlers IA dans HandlerRegistry

```python
def handler_ai_validate_layer(params: Dict, context: ExecutionContext) -> Any:
    """GET: Vérifie que l'IA n'accède pas au Layer 0."""
    target_id = params.get("id") or params.get("parent_id")
    
    if target_id and target_id.startswith(("core:", "metarule:", "schema:")):
        raise AILayerViolation(
            f"AI access to Layer 0 forbidden: {target_id}"
        )
    
    return {"layer_check": "passed"}


def handler_ai_create_suggestion(params: Dict, context: ExecutionContext) -> Any:
    """RENDER: Crée une suggestion au lieu de persister."""
    dry_run = params.get("dry_run", False)
    ai_context = params.get("_ai_context", {})
    
    if ai_context.get("mode") == "suggest-only" or dry_run:
        obj = context.get("object")
        suggestion = SuggestionQueue.create(
            agent_id=ai_context.get("agent_id"),
            operation="create",
            params=params,
            preview=obj
        )
        return {
            "type": "suggestion",
            "suggestion_id": suggestion.id,
            "preview": obj,
            "status": "pending_human_review"
        }
    
    # Mode auto: persister + créer review
    return handler_persist_object(params, context)


def register_ai_handlers(engine: GEVREngine):
    """Enregistre les handlers spécifiques IA."""
    engine.register_handler("ai_validate_layer", handler_ai_validate_layer, GEVRPhase.GET)
    engine.register_handler("ai_create_suggestion", handler_ai_create_suggestion, GEVRPhase.RENDER)
```

---

## 10. PROCHAINES ÉTAPES (E3+)

Cette spécification E2/8 établit le cadre. Les étapes suivantes pourraient inclure :

1. **E3: Interface de Review Humain** — UI pour valider/rejeter les suggestions
2. **E4: Feedback Loop IA** — Apprentissage à partir des décisions humaines
3. **E5: Monitoring Dashboard** — Tableau de bord des activités IA
4. **E6: Multi-Agent Coordination** — Orchestration de plusieurs agents IA