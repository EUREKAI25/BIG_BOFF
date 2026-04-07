# Eurkai -- Object:Model:Template, Object:Placeholder, Object:Scalar

------------------------------------------------------------------------

# 1. Ontological Positioning

In Eurkai:

-   Everything is Object.
-   Structure (dict / ElementList) defines how objects exist.
-   IVC × DRO is a FractalView (a way of reading objects), not their
    existence.
-   No hardcoded values exist inside Objects (except manifest.element).

This document defines:

-   Object:Model:Template
-   Object:Placeholder
-   Object:Scalar family

------------------------------------------------------------------------

# 2. Object:Scalar

## 2.1 Definition

Scalars represent atomic value types.

They are not conceptual entities. They are primitive value carriers
wrapped in Object form.

Examples:

-   Object:Scalar:String
-   Object:Scalar:Int
-   Object:Scalar:Bool
-   Object:Scalar:Float
-   Object:Scalar:Date

A Scalar is:

-   atomic
-   non-recursive
-   encapsulated in dict form
-   subject to StructuralRule and SchemaRule of its container

Scalars are never "hardcoded literals" in production logic. They are
produced via methods or resolved via manifests.

------------------------------------------------------------------------

# 3. Object:Placeholder

## 3.1 Definition

Object:Placeholder represents a dynamic resolution slot.

It is not: - Structure - Template - Content

It is a resolution mechanism.

A Placeholder is an Object inserted in a structure that will be replaced
via resolution.

------------------------------------------------------------------------

## 3.2 Core Attributes

Minimal structure:

-   Placeholder.value
-   Placeholder.default
-   Placeholder.validate_rule_list

### Placeholder.value

Placeholder.value is a vector (method).

It is never a literal value.

Example conceptual form:

Vector:x_placeholder_value = Read.get(Context.project.title)

The value is obtained only through method execution.

### Placeholder.default

Mandatory. May be inherited or injected. Used if Placeholder.value
resolution fails.

### Placeholder.validate_rule_list

Contains validation rules specific to the placeholder.

Example: - NoTemplateCycleRule (for template selection)

------------------------------------------------------------------------

## 3.3 Resolution Model

Resolution is handled by Template.resolve (or SuperTool.resolve in
general).

Resolution steps:

1.  Traverse structure recursively.
2.  Detect Placeholder instances.
3.  Execute Placeholder.value via MRG.
4.  If failure → execute default.
5.  Replace Placeholder node with resolved Object/Scalar.
6.  Validate result using container rules.

Placeholder does not enforce structure. Container object rules enforce
conformity.

------------------------------------------------------------------------

# 4. Object:Model:Template

## 4.1 Definition

A Template is a model used to generate an Object instance.

Object:Model:Template

Template is recursive by nature: List → ElementList → element

A Template follows standard Object.structure rules.

------------------------------------------------------------------------

## 4.2 Attachment to ObjectType

Templates are attached via:

Object.template IN Object.attributelist (View.attributelist fractally)

There is no template.target field.

A Template is always associated with an ObjectType. Children inherit
template unless overridden.

------------------------------------------------------------------------

## 4.3 Creation Logic

When defining a Template:

1.  Define the first-level element type (PGCD).
2.  Define additions/overrides relative to parent.
3.  For each parameter (attribute_list, rule_list, methodset):
    -   If specificity exists due to this object → define a Rule.
    -   Otherwise trace lineage upward.

Templates may be instantiated first as instance templates. Promotion to
foundational template may occur later (optimization phase).

------------------------------------------------------------------------

## 4.4 Template Composition

Templates may contain placeholders referencing other templates
indirectly.

Example:

index_template: {head} {body}

body_template: {header} {container} {footer}

Placeholders do not directly equal templates. Resolution triggers
template instantiation.

Cycles are prevented by design-time selection constraints and validation
rules.

------------------------------------------------------------------------

## 4.5 No Hardcoded Values Rule

Inside Templates, Scenarios, Rules, Content:

No literal values exist.

All values are resolved dynamically via methods.

Exception: manifest.element contains absolute reference values.

------------------------------------------------------------------------

# 5. Canonical Resolution Model

SuperTool.resolve performs canonicalization.

All free writing forms are reduced to canonical internal representation.

Execution form consumed by MRG is what/how.

Resolution phases:

-   Canonicalize references
-   Resolve placeholders
-   Produce executable vectors
-   Send to MRG

------------------------------------------------------------------------

# 6. Structural Integrity

The structural fractal (List → ElementList) defines existence.

IVC × DRO defines FractalView only.

Templates operate strictly within structural fractal.

------------------------------------------------------------------------

# 7. Summary

Object:Scalar: Atomic value carrier.

Object:Placeholder: Dynamic resolution slot. Value defined via vector.
Default mandatory. No literal storage.

Object:Model:Template: Recursive generation model. Attached to
ObjectType. Inherited and overrideable. Contains placeholders. Produces
objects via resolution.

No hardcoded values (except manifest.element). All variability resolved
via methods. All execution passes through canonical resolution and MRG.

------------------------------------------------------------------------

End of Template / Placeholder / Scalar specification.
