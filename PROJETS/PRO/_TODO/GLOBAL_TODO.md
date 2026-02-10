# EURKAI
## GLOBAL 
### CODE
recursive_motor
methode centrale (applique n'importe quelle méthhode)
metaschema
methodes globales
methodes secondaires (related_to global)
scenario
recursive_template
script pr modulariser fonctions / transformer en méthode puis recbdd (scenario cron maintenance : scan - check functions / methods)
#### TREE
object 
entity > user, company > provider > aiprovider, agent > aiagent 
team
api > externalapi, internalapi
scenario > step (element_of scenario)
bundle > attributebundle, stepbundle, relationbundle, methodbundle, teambundle, 
template > recursive_template > htmltemplate, classtemplate > pyclasstemplate, phpclasstemplate, reacttemplate, apitemplate
cron
tag> category
#### CATALOGS
functions + relations method_of - attributs div
### OBJECTS
### IDENT
format
### METHODS
global_method, secondary_method :
create, read, update, delete, engage, execute
### WEBSITE
create
déploiement récursif suivant arborescence
### TREE
Tree:<ident> depends_on Product:<ident>
### DOM
Dom:<ident> depends_on Website:<ident>
### DOMNODES
Object:DomNodeType inherits_from Object:NodeType

### TEMPLATE
modèle
moteur résursif
on charge projet actif (agence)
- elements : si bundle, loop sinon direct (ex header : objet header avec elements menus qui comporte home_menu qui comporte links (bundle) qui comporte elements). chaque élément de dom (related_to Dom:pagedom) a aussi un bundle DOMNode comportant id, class, data
### FUNCTIONS
#### RECURSIVE MOTOR
### ORDER
de haut en bas ou l'inverse tree_asc, tree_desc
### BOOTSRAP
liste db à partir du catalogue donc installer 
le choix de db doit permettre la config (host)
mongodb config ?
le choix d'un modèle ia doit déclencher un div de config secretkey
menu admin global (ajouter un fichier externe pr navigation ok)
### CATALOG
### CRONS
#### OPTIMISATION
mettre à jour liste des db + schemas
## PROJECTS
### AGENCE
### EXNIHILO
### SUBLYM
### CRADOS
## RULES
Object:Rule 
DefaultAttribute:RuleDefaultAttribute 
Bundle.RuleDefaultAttributeBundle related_to Domain:Rule 
Bundle.RuleDefaultAttributeBundle depends_on DefaultAttribute

Rule:StepRule related_to Step element_of RuleDefaultAttributeBundle
Rule:LogicRule element_of RuleDefaultAttributeBundle
Rule:SystemRule element_of RuleDefaultAttributeBundle
Rule.AttributeBundle

ValidateRule:Schema element_of ValidateRuleBundle <!-- ? -->
ValidateRule:Format element_of ValidateRuleBundle <!-- ? -->
Function:Has inputs: required (objecttype), optional(quantity) 
has(<objecttype>, <quantity>int null) : il y a (x) <objecttype>liés à cet objet par l'alias <objecttype>_of
Object:Tag 
Tag:Category
Schema:TagSchema <!-- une catégorie ne peut pas avoir d'enfants >
Category: Measure
Schema:CategorySchema <!-- une catégorie peut avoir des enfants >
## OBJECTS

#### PassiveObject
tous les objets passive ont un ident automatique  <objecttype>_<objectslug>
#### ActiveObject 
tous les objets active ont un ident automatique <objecttype>_<objectslug>:<parambundle>_<outputbundle> 
#### ReactiveObject
tous les objets reactive ont un ident automatique <objectslug>_<objecttype>_<version>:<parambundle>

#### All
Object:Rule depends_on Object <!-- et tant qu'on ne l'a pas utilisée ? obligatoire ? -->
Object:Dimension depends_on Plane
DimensionBundle:DefinitionBundle depends_on DROPlane 
DimensionBundle:RuleBundle depends_on DROPlane
DimensionBundle:OptionBundle depends_on DROPlane
DimensionBundle:IdentityRuleBundle depends_on IVCPlane
DimensionBundle:ViewRuleBundle depends_on IVCPlane
DimensionBundle:ContextRuleBundle depends_on IVCPlane
Dimension:DimensionDefinition element_of Planeset <!-- ? -->
Dimension:DimensionRule element_of Planeset <!-- ? -->
Dimension:DimensionOption element_of Planeset <!-- ? -->
Dimension:DimensionIdentity element_of Planeset <!-- ? -->
Dimension:DimensionView element_of Planeset <!-- ? -->
Dimension:DimensionContext element_of Planeset <!-- ? -->
Vector:Planeset depends_on Fractal
Bundle:BundlePlaneset
Rule:PlanesetRule <!-- ? -->
Planeset:TransversalPlaneset element_of BundlePlaneset 
Planeset:ExternalPlaneset element_of BundlePlaneset 
RuleBundle:FormatRule element_of 
RuleBundle:ValidationRule
Measure:Quantity related_to Unit depends_on Attribute  <!-- optional à créer ? tous les attributs sont required par défaut -->
Measure:Amount related_to Currency depends_on Attribute  <!-- optional à créer ? tous les attributs sont required par défaut -->
Object:Unit
Unit:Currency related_to country <!-- nom ? -->
Measure:Volume related_to Unit depends_on Attribute  <!-- categorie à créer ? -->
Measure:Weight related_to Unit depends_on Attribute  <!-- categorie à créer ? -->
Measure:Size related_to Unit depends_on Attribute 

Object:Label
Label:FRLabel
Label:ENLabel
Label:DELabel
Label:ITLabel
Label:ESLabel
Label:POLabel
FRLabel:FRLabel_<objecttype>_<version>
ENLabel:ENLabel_<objecttype>_<version>
DELabel:DELabel_<objecttype>_<version>
ITLabel:ITLabel_<objecttype>_<version>
ESLabel:ESLabel_<objecttype>_<version>
POLabel:POLabel_<objecttype>_<version>
Object:Document
Object:Adress
Adress:URL
Adress:path
URL:Endpoint
Object:File related_to Directory <!-- ? -->
Object:Directory 
Object:Bootstrap related_to Execute

Structure:Bundle depends_on Object 
Object:Structure <!-- transversal - comment on fait ? -->
Structure:List related_to IDPlane 
Structure:Table related_to IDPlane 
Structure:Fractal related_to IDPlane 

Object:Attribute depends_on Object
Object:AttributeBundle related_to IDPlane
Attribute:Name depends_on Attribute element_of AttributeBundle 
Attribute:Ident depends_on Attribute element_of AttributeBundle
Attribute:Question depends_on Attribute element_of AttributeBundle
Attribute:Description depends_on Attribute element_of AttributeBundle
Resource:Template element_of AttributeBundle
Resource:Schema depends_on Attribute element_of AttributeBundle
Object:Relation depends_on Object 
Object:RelationBundle related_to IDPlane  <!-- c'est ça ? -->
Relation:ExtendsOn depends_on Relation element_of RelationBundle
Relation:RelatedTo depends_on Relation element_of RelationBundle
Relation:InheritsFrom depends_on Relation element_of RelationBundle
Relation:DependsOn depends_on Relation element_of RelationBundle
Relation:ElementOf depends_on Relation element_of RelationBundle
Relation:InstanceOf depends_on Relation element_of RelationBundle

Object:CapacityBundle related_to CDPlane

Object:MethodBundle related_to CDPlane
Object:Plane depends_on Fractal
Plane:IDPlane
Plane:IRPlane
Plane:IOPlane
Plane:VDPlane
Plane:VRPlane
Plane:VOPlane
Plane:CDPlane
Plane:CRPlane
Plane:COPlane

Object:Function
Function:Method
Method:GlobalMethod
Method:CentralMethod
CentralMethod:Create
CentralMethod:Read
CentralMethod:Execute
CentralMethod:Engage
CentralMethod:Update
CentralMethod:Delete
Method:SecondaryMethod depends_on CentralMethod 
SecondaryMethod:Install related_to Execute <!-- c'est ça ? -->
InstallMethod:BootstrapInstall
Object:Project
Bundle:StepBundle depends_on Project
Step:GetStep element_of StepBundle
Step:ExecuteStep element_of StepBundle
Step:ValidateStep element_of StepBundle
Step:RenderStep element_of StepBundle
Schema:ProjectSchema : has(StepBundle) get
Schema:StepSchema related_to Loop
Object:Behavior
Behavior:Loop
Attribute:LoopAttribute
LoopAttribute:Fallback ?
Tag:Automation
Object:Hook depends_on Method
Hook:Before
Hook:After
Hook:OnFailure
Object:Alias
Relation:AliasOf depends_on Relation
############        DOM à revoir        ########
Structure:DOM
Schema:DOMSchema 
Attribute:DOMNode related_to DOMSchema
Attribute:NodeAttribute
NodeAttribute:Id
NodeAttribute:Class
NodeAttribute:Style depends_on CSS
Attribute:StyleAttribute
StyleAttribute:CSS depends_on NodeAttribute
StyleAttribute:SCSS depends_on Product  <!-- ou project >
Schema:SCSSSchema
Attribute:SCSSAttribute
Bundle:SCSSAttributeBundle  
? element_of SCSSAttributeBundle <!--à compléter >
Object:Color
Color:Hexacolor
Color:RVBColor
Bundle:SCSSolorBundle
Bundle:SCSSFontBundle
Object:Font
Font:Webfont
Font:TTFFont
Attribute:FontAttribute depends_on Font 
Unit:FontSizeUnit
FontSizeUnit:EM
FontSizeUnit:Pixels
FontSizeUnit:Pct
FontAttribute:FontColor 
FontAttribute:FontWeight
FontAttribute:FontSize related_to FontSizeUnit <!-- ? -->
Webfont:GoogleWebfont related_to WebFontProvider
Entity:Provider
Provider:WebFontProvider
Provider:AIProvider
Bundle:NodeAttributeBundle
NodeAttributeBundle:ClassBundle element_of Class <!-- à revoir -->
Bundle:DOMNodeBundle
DOMNodeBundle:Head
DOMNodeBundle:Header <!-- optional -->
DOMNodeBundle:SectionBundle
DOMNodeBundle:Footer <!-- optional -->
DOMNodeBundle:Modal <!-- optional -->
DOMNodeBundle:Sidebar <!-- optional -->

Object:Product depends_on Project
Product:DigitalProduct
Product:PhygitalProduct
Product:PhysicaProduct
DigitalProduct:Website
Structure:WebsiteStructure
WebsiteStructure:OnePageProduct
Website:LandingPage related_to OnePageProduct
Website:Blog
DigitalProduct:WebPlatform
Website:Ecommerce <--organisation ? -->
WebPlatform:Marketplace
Structure:Singleton
Object:Format
Format:SystemFormat
SystemFormat:JSON
SystemFormat:PHP
SystemFormat:React
SystemFormat:Python
SystemFormat:Javascript
SystemFormat:VueJS
SystemFormat:Node
SystemFormat:HTML
Format:CoreFormat
CoreFormat:List
CoreFormat:Dict
CoreFormat:List


# install agence
## install pages
### template recursif
### catalogue page
### get depuis bdd
#### fonction get
##### fonction globale all
##### fonction get
###### fonction getbdd

# convertir code
## accès depuis vecteur
### catalogue vecteurs
### schema global
## modulariser fonctions
## convertir fonctions
### -> méthodes
### catalogue fonctions

# Remplace le chemin par un de tes PDF
PDF="/Users/nathalie/Dropbox/PROJETS/EX NIHILO/phase 1/chantiers/ressources litteraires/oeuvres/Le-Petit-Prince.pdf"
pdftotext "$PDF" - | head -n 30


STRATEGY RECURSIVE DESCENDANTE
À chaque niveau on définit 
- tous les types d'objets dont a besoin l'objet en cours pour exister (structurel et compositioonnel ex object:Vector et Attribute:Name) chacun donne lieu à un Bundle <objecttype>Bundle
- Les éléments dont chaque bundle sera composé doivent être créés et liés au bundle par **element_of**
- on affecte chaque bundle à un emplacement / domaine dde la fractale, qui doit préexister
- à chaque objet qu'on crée on doit se demander s'il y a des spécificités à ajouter pour qu'elles complètent / remplacent celles dont on hérite, en s'appuyant sur les questions <objecttype>.QuestionBundle

revenons à la base. On cherche à poser le schema de Object, l'objet fondamental du system, qui dispose d'attributes, de methods et de rules qui lui sont associées. 
On a donc besoin de ces objets : **Attribute**, **Rule**, **Method**
Chaque élément est composé de Bundles donc on a besoin de l'objet **bundle** (qui est un type de structure dons l'objet **Structure** est nécessaire) et de ses enfants automatiquement générés (Bundle::<objecttype>Bundle) qui va rassembler tous les objets liés par la relation **element_of** à l'objet <objecttype>Bundle. Ca suppose que l'objet Relation:element_of préexiste et fonc globalement l'objet **Relation** + ses enfants (related_to, element_of, depends_on et inherit_from) mais il faut aussi créer l'objet **Rule**
Enfin, pour fonctionner, nous avons besoin des objets **Entity:Agent**, donc **Entity**, **AImodel** donc **Entity:Company:Provider:AIProvider** et **APIKey:AIAPIKey**, **Prompt**  
AttributeBundle est composé de :
Bundle:DefaultAttributeBundle depends_on DefaultAttribute
Bundle:InjectedAttributeBundle depends_on InjectedAttribute<!-- attributs des objets transversaux ayant l'objet en cours dans leur scope>

Object:Rule
défini par les attributs spécifiques LogicRule, SystemRule et StepRule donc il faut créer Attribu
Rule:LogicRule 
Rule:SystemRule
Rule:StepRule related_to Step

Object:Method

Object:Scope

Object:Attribute
Les attributs peuvent être obligatoires mais pas obligatoirement définis  
Attribute:DefaultAttribute
DefaultAttribute:Question
DefaultAttribute:Description
DefaultAttribute:Example
Attribute:InjectedAttribute

TextContent:Prompt 
Prompt:<method>Prompt
Content:TextContent
Object:Content

Object:Context element_of PromptAttributeBundle
Object:Resource element_of PromptAttributeBundle
Object:Role element_of PromptAttributeBundle

Vector > Plane > Dimension  enfants