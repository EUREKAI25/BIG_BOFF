# CONFIG OBJECT TYPES (Catalogues)
# À intégrer dans _SCHEMAS — version complète et conforme

SchemaCatalog:ObjectType:Config:Database
  ElementList:
    AttributeList:
      inherited_bundle = Vector:ConfigDatabaseAttributeBundle:Inherited
      injected_bundle  = Vector:ConfigDatabaseAttributeBundle:Injected
      owned_bundle     = Vector:ConfigDatabaseAttributeBundle:Owned

    RelationList:
      inherited_bundle = Vector:ConfigDatabaseRelationBundle:Inherited
      injected_bundle  = Vector:ConfigDatabaseRelationBundle:Injected
      owned_bundle     = Vector:ConfigDatabaseRelationBundle:Owned

    MethodList:
      inherited_bundle = Vector:ConfigDatabaseMethodBundle:Inherited
      injected_bundle  = Vector:ConfigDatabaseMethodBundle:Injected
      owned_bundle     = Vector:ConfigDatabaseMethodBundle:Owned

    RuleList:
      inherited_bundle = Vector:ConfigDatabaseRuleBundle:Inherited
      injected_bundle  = Vector:ConfigDatabaseRuleBundle:Injected
      owned_bundle     = Vector:ConfigDatabaseRuleBundle:Owned


SchemaCatalog:ObjectType:Config:AIProvider
  ElementList:
    AttributeList:
      inherited_bundle = Vector:ConfigAIProviderAttributeBundle:Inherited
      injected_bundle  = Vector:ConfigAIProviderAttributeBundle:Injected
      owned_bundle     = Vector:ConfigAIProviderAttributeBundle:Owned

    RelationList:
      inherited_bundle = Vector:ConfigAIProviderRelationBundle:Inherited
      injected_bundle  = Vector:ConfigAIProviderRelationBundle:Injected
      owned_bundle     = Vector:ConfigAIProviderRelationBundle:Owned

    MethodList:
      inherited_bundle = Vector:ConfigAIProviderMethodBundle:Inherited
      injected_bundle  = Vector:ConfigAIProviderMethodBundle:Injected
      owned_bundle     = Vector:ConfigAIProviderMethodBundle:Owned

    RuleList:
      inherited_bundle = Vector:ConfigAIProviderRuleBundle:Inherited
      injected_bundle  = Vector:ConfigAIProviderRuleBundle:Injected
      owned_bundle     = Vector:ConfigAIProviderRuleBundle:Owned


SchemaCatalog:ObjectType:Config:Hosting
  ElementList:
    AttributeList:
      inherited_bundle = Vector:ConfigHostingAttributeBundle:Inherited
      injected_bundle  = Vector:ConfigHostingAttributeBundle:Injected
      owned_bundle     = Vector:ConfigHostingAttributeBundle:Owned

    RelationList:
      inherited_bundle = Vector:ConfigHostingRelationBundle:Inherited
      injected_bundle  = Vector:ConfigHostingRelationBundle:Injected
      owned_bundle     = Vector:ConfigHostingRelationBundle:Owned

    MethodList:
      inherited_bundle = Vector:ConfigHostingMethodBundle:Inherited
      injected_bundle  = Vector:ConfigHostingMethodBundle:Injected
      owned_bundle     = Vector:ConfigHostingMethodBundle:Owned

    RuleList:
      inherited_bundle = Vector:ConfigHostingRuleBundle:Inherited
      injected_bundle  = Vector:ConfigHostingRuleBundle:Injected
      owned_bundle     = Vector:ConfigHostingRuleBundle:Owned


SchemaCatalog:ObjectType:Config:Admin
  ElementList:
    AttributeList:
      inherited_bundle = Vector:ConfigAdminAttributeBundle:Inherited
      injected_bundle  = Vector:ConfigAdminAttributeBundle:Injected
      owned_bundle     = Vector:ConfigAdminAttributeBundle:Owned

    RelationList:
      inherited_bundle = Vector:ConfigAdminRelationBundle:Inherited
      injected_bundle  = Vector:ConfigAdminRelationBundle:Injected
      owned_bundle     = Vector:ConfigAdminRelationBundle:Owned

    MethodList:
      inherited_bundle = Vector:ConfigAdminMethodBundle:Inherited
      injected_bundle  = Vector:ConfigAdminMethodBundle:Injected
      owned_bundle     = Vector:ConfigAdminMethodBundle:Owned

    RuleList:
      inherited_bundle = Vector:ConfigAdminRuleBundle:Inherited
      injected_bundle  = Vector:ConfigAdminRuleBundle:Injected
      owned_bundle     = Vector:ConfigAdminRuleBundle:Owned
