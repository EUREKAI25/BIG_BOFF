# OBJECT
Tout est objet 
# ATTRIBUTE
Object :
  .list = ElementList 

Attribute:DefinitionAttribute
:createdBy.create IN this.create.afterhooklist 
:createdAt.create IN
:updatedBy.update IN this.update.afterhooklist 
:updatedAt.update IN this.update.afterhooklist 
.automated = true
¨∏
DefinitionAttribute IN AttributeList
AttributeList IN ElementList

# SCHEMA∏
Tout objet contient ObjectList (généré automatiquement)
# METHOD¨
Toute fonction est methode d'objet
Toute méthode est assortie de sa liste de hooks qui seront exécuutés par la MRG
# SCENARIO
## CREATE
ObjectCreate -> hookafter=[ObjectAliasCreate, CreateByAttributeCreate, CreatedAtAttributeCreate]
ObjectUpdate -> hookafter=[UpdatedByAttributeUpdate, UpdatedAtAttributeUpdate]
# ALIAS
## AUTOMATED
Tout linéage permet son alias virtuel : lineage sans ponctuation
## MANUAL
# LOG
BeforeHookExecute -> hookbefore = [Log]
AfterHookExecute -> hookbefore = [Log]
# LINEAGE
.regex hérité de System rempli par schema

