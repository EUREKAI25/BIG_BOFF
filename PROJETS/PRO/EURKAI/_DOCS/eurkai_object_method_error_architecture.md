# Eurkai -- Object / Methods / Error Architecture (Consolidated)

## 1. Object -- Foundational Principles

### 1.1 Object is the root of everything

All entities in Eurkai inherit (directly or indirectly) from `Object`.

There are no exceptions.

------------------------------------------------------------------------

### 1.2 Universal Structure Rule

All Objects are structurally `dict`.

-   `Object.structure = dict`
-   Even atomic objects are dict.
-   Lists are represented as dict (ordered or not).

There is no primitive List type outside Object.

------------------------------------------------------------------------

### 1.3 Recursivity

All Objects are recursive.

A list is conceptually an `ElementList`: - `ElementList` is an Object. -
It contains Objects. - These Objects may themselves contain
ElementLists.

Recursion is universal and uniform.

------------------------------------------------------------------------

### 1.4 PGCD Creation Logic

Creation is top-down.

When creating an Object: 1. Define its highest-level elements (PGCD). 2.
Descend recursively until atomic level.

This ensures structural clarity before parameter specification.

------------------------------------------------------------------------

## 2. Get / Read / GetCreate -- Execution Model

### 2.1 Method Hierarchy

-   `Read` is a central method.
-   `Get` is a secondary method of `Read`.
-   `Scenario:GetCreate` is a secondary method of `Orchestrate`.

Get is NOT an alias. GetCreate is NOT central.

------------------------------------------------------------------------

### 2.2 SuperTool Execution Model

All executions pass through the MRG (Méthode Récursive Globale).

The SuperTool: - Always orchestrates execution via MRG. - Retrieves the
active secondary method. - Executes its `resolve`. - Sends `(what, how)`
vectors to MRG.

Resolve belongs to the method itself: - `Object.resolve` -
`CentralMethod.resolve` - `SecondaryMethod.resolve`

SuperTool does not contain resolve logic. It executes resolve defined by
the method.

------------------------------------------------------------------------

### 2.3 GetCreate Logic

Inside `Orchestrate.getcreate`:

1.  `Read.get` is executed.
2.  If object is found → return object.
3.  If `!get` → an error is returned.
4.  `FailureHook` handles creation:
    -   `Create.generate`
    -   `Create.register`
5.  Object is returned.

Absence of object is handled through FailureScenario.

------------------------------------------------------------------------

## 3. Result Contract

All methods return:

    Result = {
      success: bool,
      output: dict,
      datas: dict,
      trace_id,
      message,
      error
    }

`success=false` means execution did not complete normally.

------------------------------------------------------------------------

## 4. Error Architecture

### 4.1 Error Object Types

Two families:

#### Object:Error:ResultError

Controlled business-level failure.

Examples: - EmptyResult - ValidationError - ConflictResult -
PolicyDeniedResult

#### Object:Error:SystemError

Technical / infrastructure failure.

Examples: - TimeoutSystemError - NetworkSystemError -
PermissionSystemError - StorageSystemError - RuntimeSystemError

------------------------------------------------------------------------

### 4.2 Failure Scenarios

Dedicated scenarios:

-   `Scenario:FailureScenario:ResultError`
-   `Scenario:FailureScenario:SystemError`

ResultError may trigger deterministic actions (e.g., creation).
SystemError triggers retry/escalation.

------------------------------------------------------------------------

## 5. Fundamental vs Specific (Modules)

Fundamental is not binary. It is a gradient of reusability.

### 5.1 Module Levels

-   MetaModule (abstract pattern)
-   Domain Module (e.g., RestaurantReservationModule)
-   Module Instance (e.g., RestaurantReservationModule.instance.brand_x)

Promotion from instance to fundamental is handled by:

-   Optimization Tasks
-   Cron-based optimization

Promotion is NOT synchronous with creation.

------------------------------------------------------------------------

## 6. Tags & Library

### 6.1 Tag Storage

Real definition: `<object>.elementlist.attributelist.taglist`

Fractal reading view: `Context.Definition.element_list`

------------------------------------------------------------------------

### 6.2 Library

Library is not a system. Library = `Tag:Category`.

Category differs from Tag by allowing children.

------------------------------------------------------------------------

## 7. Parent Relationships

Parent module is derived from tree structure:

    RestaurantReservationModule.parent =
    RestaurantReservationModule.treelist.parentlist[0]

No independent parent field.

------------------------------------------------------------------------

## 8. Optimization Policy

When repeated option patterns appear across instances:

-   Create `OptimizationTask`
-   Cron processes optimization later
-   Possible promotion to new fundamental module

Pipeline remains non-blocking.

------------------------------------------------------------------------

## 9. Creation & Validation Questions

CreateQuestions belong to the attribute level, not centralized globally.

Schema defines how to collect them.

ValidateQuestions used only during creation validation phase (e.g.,
highest conceptual level verification).

They are not persistent runtime validators.

------------------------------------------------------------------------

## 10. Summary of Fixed Decisions

-   SuperTool always executes via MRG.
-   Resolve belongs to method (no adapter concept).
-   GetCreate is secondary of Orchestrate.
-   Get is secondary of Read.
-   Absence of object produces ResultError.
-   Error families clearly separated.
-   FailureScenarios are mandatory and typed.
-   Promotion of modules handled by optimization tasks.
-   Library implemented via Tag:Category.
-   Parent derived from treelist.
-   Questions live on attributes.

------------------------------------------------------------------------

End of consolidated specification.
