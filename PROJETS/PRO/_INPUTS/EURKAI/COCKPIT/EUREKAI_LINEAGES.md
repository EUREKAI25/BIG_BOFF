# EUREKAI — Arbre des Lignées (Lineages)

> Format: `Object:Parent:...:Child`
> Séparateur `:` = héritage vertical

---

## 🏛️ RACINE

```
Object
```

---

## 📐 STRUCTURES FRACTALES

```
Object:Structure
Object:Structure:Fractal
Object:Structure:Dimension
Object:Structure:Dimension:Identity
Object:Structure:Dimension:View
Object:Structure:Dimension:Context
Object:Structure:Triplet
Object:Structure:Triplet:Definition
Object:Structure:Triplet:Rules
Object:Structure:Triplet:Options
Object:Structure:Plane
Object:Structure:PlaneSet
Object:Structure:PlaneSet:GlobalPlaneSet
Object:Structure:PlaneSet:PrimaryPlaneSet
```

---

## 📦 BUNDLES & LISTES

```
Object:Structure:Bundle
Object:Structure:Bundle:BundleList
Object:Structure:Bundle:AttributeListBundle
Object:Structure:Bundle:MethodListBundle
Object:Structure:Bundle:RelationListBundle
Object:Structure:Bundle:RuleListBundle
Object:Structure:Bundle:StepListBundle
Object:Structure:Bundle:LoopListBundle
Object:Structure:ElementList
Object:Structure:ElementList:AttributeList
Object:Structure:ElementList:MethodList
Object:Structure:ElementList:RelationList
Object:Structure:ElementList:RuleList
```

---

## 🔤 ÉLÉMENTS (Element)

```
Object:Element
Object:Element:Attribute
Object:Element:Method
Object:Element:Relation
Object:Element:Rule
Object:Element:Step
Object:Element:Scenario
Object:Element:Connector
Object:Element:Input
Object:Element:Output
```

---

## ⚡ EXÉCUTION

### Fonctions & Steps

```
Object:Function
Object:Function:FunctionResult
Object:Function:FunctionSpec
Object:Element:Step:GetStep
Object:Element:Step:ExecuteStep
Object:Element:Step:ValidateStep
Object:Element:Step:RenderStep
```

### Méthodes Centrales (CRUDAE)

```
Object:Element:Method:CentralMethod
Object:Element:Method:CentralMethod:Create
Object:Element:Method:CentralMethod:Read
Object:Element:Method:CentralMethod:Update
Object:Element:Method:CentralMethod:Delete
Object:Element:Method:CentralMethod:Assemble
Object:Element:Method:CentralMethod:Execute
```

### Comportements & Loops

```
Object:Behavior
Object:Behavior:Loop
Object:Behavior:Loop:Parallel
Object:Behavior:Loop:Sequential
Object:Behavior:Loop:Conditional
```

---

## 📏 RÈGLES & VALIDATION

```
Object:Element:Rule:FormatRule
Object:Element:Rule:BehaviorRule
Object:Element:Rule:ResultRule
Object:Element:Rule:ValidationRule
Object:Validation
Object:Validation:Check
Object:Validation:Constraint
```

---

## 🔗 RELATIONS

```
Object:Element:Relation:InheritsFrom
Object:Element:Relation:DependsOn
Object:Element:Relation:RelatedTo
Object:Element:Relation:ElementOf
```

---

## 🎯 VECTEURS & CATALOGUES

```
Object:Vector
Object:Catalogue
Object:Triplet
```

---

## 🔄 HOOKS & ÉVÉNEMENTS

```
Object:Hook
Object:Hook:Before
Object:Hook:After
Object:Hook:Failure
Object:Event
Object:Event:Log
Object:Event:Diary
Object:Event:Trace
Object:Event:Signal
Object:Event:Signal:Info
Object:Event:Signal:Warning
Object:Event:Signal:Alert
```

---

## 🏢 ENTITÉS MÉTIER

### Agence & Gouvernance

```
Object:Entity
Object:Entity:Agency
Object:Entity:Direction
Object:Entity:Lab
Object:Entity:Intranet
```

### Projets & Travaux

```
Object:Entity:Project
Object:Entity:Project:Chantier
Object:Entity:Project:Pipeline
Object:Entity:Project:Task
```

### Interfaces & Composants

```
Object:Entity:Interface
Object:Entity:Interface:Page
Object:Entity:Interface:Component
Object:Entity:Interface:Template
Object:Entity:Interface:Template:MetaTemplate
```

---

## 🤖 AGENTS & PERMISSIONS

```
Object:Entity:Agent
Object:Entity:Agent:Role
Object:Permission
Object:Permission:PermissionCreate
Object:Permission:PermissionRead
Object:Permission:PermissionUpdate
Object:Permission:PermissionDelete
```

---

## 🧠 INTELLIGENCE ARTIFICIELLE

```
Object:Entity:AIProvider
Object:Entity:AIProvider:AIModel
Object:Entity:AIProvider:AIEngine
Object:Entity:Prompt
Object:Entity:Prompt:MetaPrompt
Object:Entity:Prompt:PromptTemplate
Object:Entity:SuperTool
Object:Entity:SuperTool:SuperScan
Object:Entity:SuperTool:SuperLoad
```

---

## 📊 DONNÉES & INDEXATION

```
Object:Index
Object:Index:ChatIndex
Object:Index:FunctionIndex
Object:Index:Catalogue
Object:Tag
Object:Tag:TagBundle
```

---

## 🔧 LAYERS

```
Object:Layer
```
> Note: FunctionalLayer, ConceptualLayer, StrategicLayer sont des valeurs de `layer_type`

---

## ⏰ SYSTÈME & MONITORING

```
Object:System
Object:System:Pulse
Object:System:Scheduler
Object:System:Cron
```

---

## 🚀 INFRASTRUCTURE

```
Object:Infrastructure
Object:Infrastructure:Deployment
Object:Infrastructure:Container
Object:Infrastructure:Storage
Object:Infrastructure:Backup
```

---

## 📋 RÉCAPITULATIF PAR PROFONDEUR

### Niveau 1 (enfants directs de Object)
```
Object:Structure
Object:Element
Object:Function
Object:Behavior
Object:Validation
Object:Vector
Object:Catalogue
Object:Triplet
Object:Hook
Object:Event
Object:Entity
Object:Permission
Object:Index
Object:Tag
Object:Layer
Object:System
Object:Infrastructure
```

### Niveau 2 (exemples)
```
Object:Structure:Fractal
Object:Structure:Bundle
Object:Element:Attribute
Object:Element:Method
Object:Entity:Agent
Object:Entity:Project
Object:Hook:Before
Object:Event:Signal
```

### Niveau 3+ (spécialisations)
```
Object:Element:Method:CentralMethod:Create
Object:Entity:Interface:Template:MetaTemplate
Object:Event:Signal:Warning
Object:Behavior:Loop:Parallel
```

---

*Document généré le 29 novembre 2025*
