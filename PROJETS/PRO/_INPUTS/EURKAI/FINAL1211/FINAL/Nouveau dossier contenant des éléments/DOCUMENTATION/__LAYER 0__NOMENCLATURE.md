=============================================
1. NOMENCLATURE — SCOPE
=============================================

Object:NOMENCLATURE
  Description.FR = "Règles de nommage pour les objets, vecteurs, bundles, relations, méthodes et lineages ERK."

-- Objectif :
--   - garantir une cohérence globale des noms dans tout EUREKAI
--   - faciliter la récursivité (MetaSchema, Schema.deploy)
--   - permettre aux agents et outils de déduire le rôle d’un vecteur
--     uniquement à partir de son identifiant.


=============================================
2. NOMS D’OBJECTS & OBJECTTYPES
=============================================

------------------------------------------------
2.1 OBJECT
------------------------------------------------

Object:<Name>
  -- Représente une entité conceptuelle (User, Company, Unit, MetaFormula, etc.)

Examples:
  Object:MetaSchema
  Object:SchemaCatalog
  Object:ERKLanguage
  Object:Unit
  Object:MetaFormula

------------------------------------------------
2.2 OBJECTTYPE (SCHEMACATALOG)
------------------------------------------------

SchemaCatalog:ObjectType:<Domain>:<Name>
  ElementList:
    AttributeBundle = Vector:<Domain><Name>AttributeBundle
    RelationBundle  = Vector:<Domain><Name>RelationBundle
    MethodBundle    = Vector:<Domain><Name>MethodBundle
    RuleBundle      = Vector:<Domain><Name>RuleBundle

-- Exemple (déjà posé dans _SCHEMAS) : fileciteturn3file0

SchemaCatalog:ObjectType:Entity:User
  ElementList:
    AttributeBundle = Vector:EntityUserAttributeBundle
    RelationBundle  = Vector:EntityUserRelationBundle
    MethodBundle    = Vector:EntityUserMethodBundle
    RuleBundle      = Vector:EntityUserRuleBundle


=============================================
3. VECTEURS & BUNDLES
=============================================

------------------------------------------------
3.1 VECTEURS D’ATTRIBUTS / RELATIONS / METHODES / RÈGLES
------------------------------------------------

Vector:Attr.<ObjectName>.<AttributeName>
  Type           = AttributeDefinition
  Key            = "<AttributeName>"
  ResolverMethod = Vector:Method.Resolve.<ObjectName>.<AttributeName>

Vector:Rel.<ObjectName>.<RelationName>.<TargetObject>
  Type           = RelationDefinition

Vector:Method.<ObjectName>.<ActionName>
  Type           = Method

Vector:Rule.<ObjectName>.<RuleName>
  Type           = RuleDefinition

-- Exemple (issu du schéma Entity:User) : fileciteturn3file0

Vector:Attr.EntityUser.EntityName
  Type           = AttributeDefinition
  Key            = "EntityName"
  ResolverMethod = Vector:Method.Resolve.EntityUser.EntityName

------------------------------------------------
3.2 BUNDLES
------------------------------------------------

Vector:<ObjectName>AttributeBundle
  Type  = Bundle.Attribute
  Items = [ Vector:Attr.<ObjectName>.<Attribute1>, … ]

Vector:<ObjectName>RelationBundle
  Type  = Bundle.Relation
  Items = [ Vector:Rel.<ObjectName>.<RelationName>.<Target>, … ]

Vector:<ObjectName>MethodBundle
  Type  = Bundle.Method
  Items = [ Vector:Method.<ObjectName>.<ActionName>, … ]

Vector:<ObjectName>RuleBundle
  Type  = Bundle.Rule
  Items = [ Vector:Rule.<ObjectName>.<RuleName>, … ]

------------------------------------------------
3.3 SOUS-BUNDLES (INHERITED / INJECTED / OWNED)
------------------------------------------------

Pour chaque type de Bundle, trois sous-bundles peuvent être distingués :

Vector:<ObjectName>AttributeBundle:InheritedAttributeBundle
Vector:<ObjectName>AttributeBundle:InjectedAttributeBundle
Vector:<ObjectName>AttributeBundle:OwnedAttributeBundle

-- Idem pour RelationBundle, MethodBundle, RuleBundle.

-- Sémantique :
--   Inherited : contenu hérité d’un parent (ligne d’héritage)
--   Injected  : contenu injecté dynamiquement par les classes transversales
--   Owned     : contenu propre à l’ObjectType.


=============================================
4. METHODES & SCHEMA.DEPLOY
=============================================

------------------------------------------------
4.1 NOMMAGE DES METHODES
------------------------------------------------

Method:<ObjectName>.<ActionName>
Vector:Method.<ObjectName>.<ActionName>

-- Exemples :
--   Method:Schema.deploy
--   Method:EntityUser.Create
--   Method:ERKLanguage.ParseLine

------------------------------------------------
4.2 METHOD:SCHEMA.DEPLOY (RAPPEL)
------------------------------------------------

Method:Schema.deploy(ObjectTypeIdent) =
  Vector:SchemaDeploy(ObjectTypeIdent)

Vector:SchemaDeploy(ObjectTypeIdent)
  Description.FR = "Déploie le schéma d’un ObjectType à partir du MetaSchema + SchemaCatalog."

  Input.ObjectTypeIdent = ObjectTypeIdent

  Step:GET
    CatalogEntry          = SchemaCatalog:ObjectType:<ObjectTypeIdent>
    AttributeBundleVector = CatalogEntry.ElementList.AttributeBundle
    RelationBundleVector  = CatalogEntry.ElementList.RelationBundle
    MethodBundleVector    = CatalogEntry.ElementList.MethodBundle
    RuleBundleVector      = CatalogEntry.ElementList.RuleBundle

  Step:EXECUTE
    DeployedSchema =
      Schema:<ObjectTypeIdent>
        ElementList:
          AttributeList = AttributeBundleVector
          RelationList  = RelationBundleVector
          MethodList    = MethodBundleVector
          RuleList      = RuleBundleVector

-- Le vecteur de sortie suit la convention :

Vector:Schema.ObjectType(<ObjectTypeIdent>)
  Type           = SchemaReference
  ObjectType     = <ObjectTypeIdent>
  Source.Meta    = MetaSchema
  Source.Catalog = SchemaCatalog:ObjectType:<ObjectTypeIdent>


=============================================
5. LINEAGE & SYSTEM.ELEMENT_LIST
=============================================

------------------------------------------------
5.1 PATRON LINEAGE
------------------------------------------------

Lineage.Pattern =
  <root>.<layer>.<family>.<subfamily>.<object>.<slot>...

Examples:
  html.body.container.section.module.front
  system.core.meta_core.security.rules_central_supertools

-- Règles :
--   - <root>       : domaine global (html, system, library, etc.)
--   - <layer>      : layer logique (core, meta_core, security, library…)
--   - <family>...  : familles d’objets, sous-domaines, etc.
--   - <slot>       : zone précise (front, admin, api…)

------------------------------------------------
5.2 SYSTEM.ELEMENT_LIST
------------------------------------------------

system.element_list = [
  core REQUIRED,
  meta_core REQUIRED,
  security REQUIRED,
  rules_central_supertools REQUIRED,
  secondary_methods REQUIRED,
  library REQUIRED,
  entities REQUIRED,
  agency REQUIRED,
  ai REQUIRED,
  erk_language REQUIRED
] IN system.definition

-- Ces noms constituent la nomenclature canonique des layers du système.


=============================================
6. RÉSUMÉ DES RÈGLES
=============================================

Rule.Nomenclature.ObjectName:
  Object names MUST start with an uppercase letter
  and use CamelCase for composite names.

Rule.Nomenclature.VectorPrefix:
  Vector identifiers MUST start with one of:
    Attr., Rel., Method., Rule., Schema., etc.

Rule.Nomenclature.BundleName:
  Bundle names MUST follow the pattern:
    <ObjectName><Kind>Bundle[:Qualifier]
  where Kind ∈ {Attribute, Relation, Method, Rule}
        Qualifier ∈ {Inherited, Injected, Owned} (optionnel)

Rule.Nomenclature.ObjectType:
  ObjectType identifiers MUST follow:
    <Domain>:<Name> (ex: Entity:User, Formula:MetaFormula, ERK:Language)

Rule.Nomenclature.Lineage:
  Lineage paths MUST be dot-separated segments,
  from global scope to local slot.
