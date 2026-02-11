# __LAYER 0__METASCHEMA

(This file integrates inherited_bundle, injected_bundle, owned_bundle inside each Bundle.)

## DESCRIPTION
MetaSchema defines the canonical recursive structure of all ObjectTypes.

## ELEMENTLIST STRUCTURE
Each Plane (Identity, View, Context, Definition, Rule, Option) contains an ElementList:

ElementList:
  AttributeList:
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  RelationList:
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  MethodList:
    - inherited_bundle
    - injected_bundle
    - owned_bundle
  RuleList:
    - inherited_bundle
    - injected_bundle
    - owned_bundle

## BUNDLE SEMANTICS
inherited_bundle:
  Content inherited from parent ObjectTypes.

injected_bundle:
  Content injected dynamically (providers, environment, lineage-based injections).

owned_bundle:
  Content defined directly for the ObjectType.

## SCHEMACATALOG INTEGRATION
Each ObjectType deploys the MetaSchema by filling its Bundles with:
  AttributeBundle = {inherited / injected / owned}
  RelationBundle  = {inherited / injected / owned}
  MethodBundle    = {inherited / injected / owned}
  RuleBundle      = {inherited / injected / owned}

## JSON VIEW
{
  "MetaSchema": {
    "ElementList": {
      "AttributeList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "RelationList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "MethodList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      },
      "RuleList": {
        "inherited_bundle": [],
        "injected_bundle": [],
        "owned_bundle": []
      }
    }
  }
}
