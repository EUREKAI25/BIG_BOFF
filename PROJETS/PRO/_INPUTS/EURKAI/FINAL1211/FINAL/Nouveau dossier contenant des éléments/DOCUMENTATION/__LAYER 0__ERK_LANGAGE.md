=============================================
1. ERK_LANGAGE — SCOPE
=============================================

Object:ERK_Language
  Description.FR = "Langage propriétaire de description du système EUREKAI (planes, element_list, lineage, requêtes)."

-- ERK sert à :
--   - décrire la structure du système (layers, planes, element_list)
--   - adresser les objets via un lineage hiérarchique
--   - exprimer des requêtes structurées sur les objets et leurs relations
--   - rester agnostique du runtime (Python, JS, etc.)


=============================================
2. PLANES & ELEMENT_LIST
=============================================

-- Les planes globaux sont ceux du MetaSchema : fileciteturn3file0

MetaSchema = {
  Identity.Plane(ElementList),
  View.Plane(ElementList),
  Context.Plane(ElementList),
  Definition.Plane(ElementList),
  Rule.Plane(ElementList),
  Option.Plane(ElementList)
}

metaSchema = Vector:GlobalPlaneList
GlobalPlane.List = { Vector:PlaneList }

------------------------------------------------
2.1 SYSTEM.ELEMENT_LIST
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

------------------------------------------------
2.2 ERK_LANGUAGE.ELEMENT_LIST
------------------------------------------------

erk_language.element_list = [
  MetaAlias,
  MetaQuery,
  MetaPlaceholder
] IN view.definition

------------------------------------------------
2.3 PATRON GÉNÉRIQUE ELEMENT_LIST
------------------------------------------------

<scope>.element_list = [
  <item_1> REQUIRED,
  <item_2>,
  <item_3> REQUIRED
] IN <plane>.definition

-- Mot-clés :
--   REQUIRED  : l’élément doit exister pour que le scope soit valide
--   IN        : indique dans quel plane / scope vit la liste


=============================================
3. LINEAGE
=============================================

-- Un lineage ERK est une chaîne hiérarchique de segments séparés par des points :

Example.Lineage.1 = html.body.container.section.module.front
Example.Lineage.2 = system.core.meta_core.security.rules_central_supertools

-- Règles :
--   - chaque segment est un identifiant logique (layer, objet, slot…)
--   - plus le lineage est long, plus on va vers le concret (config, instance)
--   - un lineage peut être partiel (pattern) ou complet (objet adressable)
--   - les requêtes peuvent utiliser des wildcards (*)


=============================================
4. REQUÊTES ERK
=============================================

------------------------------------------------
4.1 PATRON GLOBAL
------------------------------------------------

*.element_list.* ATTRIBUTE[class, id, data]

-- Signification :
--   - *.element_list.*  : tous les element_list de tous les scopes
--   - ATTRIBUTE[...]    : projection des attributs demandés

------------------------------------------------
4.2 PATRON RDF-LIKE
------------------------------------------------

<objecttype>_of <relation>(<filter>)

-- Exemple :
--   invoice_of sale(BETWEEN march 2025)

-- Ces patterns sont décrits par les objets MetaQuery et Query.


=============================================
5. OBJETS DE LANGAGE (SCHEMAS)
=============================================

------------------------------------------------
5.1 OBJECTTYPE:ERK:Language
------------------------------------------------

Object:ERKLanguage
  Description.FR = "Grammaire, lexique et patterns de requêtes ERK."

SchemaCatalog:ObjectType:ERK:Language
  ElementList:
    AttributeBundle = Vector:ERKLanguageAttributeBundle
    RelationBundle  = Vector:ERKLanguageRelationBundle
    MethodBundle    = Vector:ERKLanguageMethodBundle
    RuleBundle      = Vector:ERKLanguageRuleBundle

Vector:ERKLanguageAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.ERKLanguage.PlanesList,
    Vector:Attr.ERKLanguage.ReservedKeywords,
    Vector:Attr.ERKLanguage.LineagePattern,
    Vector:Attr.ERKLanguage.ElementListPattern,
    Vector:Attr.ERKLanguage.QueryPatterns
  ]

Vector:ERKLanguageRelationBundle
  Type  = Bundle.Relation
  Items = [
    Vector:Rel.ERKLanguage.Uses.MetaGrammar,
    Vector:Rel.ERKLanguage.Uses.Lexique,
    Vector:Rel.ERKLanguage.Defines.MetaQuery,
    Vector:Rel.ERKLanguage.Defines.Query
  ]

Vector:ERKLanguageMethodBundle
  Type  = Bundle.Method
  Items = [
    Vector:Method.ERKLanguage.ParseLine,
    Vector:Method.ERKLanguage.ParseFile,
    Vector:Method.ERKLanguage.ExtractLineage,
    Vector:Method.ERKLanguage.ExtractElementList,
    Vector:Method.ERKLanguage.BuildQuery
  ]

Vector:ERKLanguageRuleBundle
  Type  = Bundle.Rule
  Items = [
    Vector:Rule.ERKLanguage.ValidIdentifier,
    Vector:Rule.ERKLanguage.ValidLineage,
    Vector:Rule.ERKLanguage.ValidElementList,
    Vector:Rule.ERKLanguage.ValidQuery
  ]


------------------------------------------------
5.2 OBJECTTYPE:ERK:MetaGrammar
------------------------------------------------

Object:MetaGrammar
  Description.FR = "Structure d’une règle syntaxique ERK."

SchemaCatalog:ObjectType:ERK:MetaGrammar
  ElementList:
    AttributeBundle = Vector:MetaGrammarAttributeBundle
    RelationBundle  = Vector:MetaGrammarRelationBundle
    MethodBundle    = Vector:MetaGrammarMethodBundle
    RuleBundle      = Vector:MetaGrammarRuleBundle

Vector:MetaGrammarAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.MetaGrammar.Name,
    Vector:Attr.MetaGrammar.Pattern,
    Vector:Attr.MetaGrammar.Examples
  ]


------------------------------------------------
5.3 OBJECTTYPE:ERK:Lexique
------------------------------------------------

Object:Lexique
  Description.FR = "Mots réservés, opérateurs et patterns ERK."

SchemaCatalog:ObjectType:ERK:Lexique
  ElementList:
    AttributeBundle = Vector:LexiqueAttributeBundle
    RelationBundle  = Vector:LexiqueRelationBundle
    MethodBundle    = Vector:LexiqueMethodBundle,
    RuleBundle      = Vector:LexiqueRuleBundle

Vector:LexiqueAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.Lexique.KeywordList,
    Vector:Attr.Lexique.OperatorList,
    Vector:Attr.Lexique.PatternList
  ]


------------------------------------------------
5.4 OBJECTTYPE:ERK:MetaQuery & ERK:Query
------------------------------------------------

Object:MetaQuery
  Description.FR = "Type de requête ERK (pattern, slots, domaine)."

SchemaCatalog:ObjectType:ERK:MetaQuery
  ElementList:
    AttributeBundle = Vector:MetaQueryAttributeBundle
    RelationBundle  = Vector:MetaQueryRelationBundle
    MethodBundle    = Vector:MetaQueryMethodBundle
    RuleBundle      = Vector:MetaQueryRuleBundle

Vector:MetaQueryAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.MetaQuery.Pattern,
    Vector:Attr.MetaQuery.Slots,
    Vector:Attr.MetaQuery.TargetUniverse
  ]

------------------------------------------------

Object:Query
  Description.FR = "Instance concrète d’une requête ERK."

SchemaCatalog:ObjectType:ERK:Query
  ElementList:
    AttributeBundle = Vector:QueryAttributeBundle
    RelationBundle  = Vector:QueryRelationBundle
    MethodBundle    = Vector:QueryMethodBundle
    RuleBundle      = Vector:QueryRuleBundle

Vector:QueryAttributeBundle
  Type  = Bundle.Attribute
  Items = [
    Vector:Attr.Query.MetaQueryRef,
    Vector:Attr.Query.Parameters,
    Vector:Attr.Query.TargetScope
  ]


=============================================
6. POSITIONNEMENT LAYERS
=============================================

Layer0.ERK_Language.Scope =
  CORE & MRG — définition du langage et de ses objets de base.

LayerERKLanguage.Scope =
  Implémentations détaillées (fichiers .erk, tooling, mapping VSCode, etc.).
