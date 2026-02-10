# Réponse pour l’IA de G2 — Clarifications & Directives

Tu as demandé les éléments suivants pour finaliser G2/10 :

- MetaRules — structure des règles à valider  
- Scénarios GEVR — format Get / Execute / Validate / Render  
- SuperTools — catalogue minimal  
- Exemple de fractale (structure type d’un objet)

Voici **exactement ce dont tu as besoin pour avancer**, dans un format stable, cohérent avec A→G, et suffisamment précis pour alimenter les générateurs de tests.

---

# 1. MetaRules — Structure officielle

Les **MetaRules** dans EURKAI sont des objets = bundles composés de :

- **ruleId** : identifiant unique (vector)
- **appliesTo** : *ObjectType* ou *lineage* ciblé  
- **condition** : expression ERK (lecture seule)
- **effect** : classification ou action logique, *jamais* destructive  
- **severity** : `info | warn | error | critical`
- **category** : `structure | relation | coherency | scenario | module | security`
- **message** : texte humain décrivant la règle

Format :

```
MetaRule = {
  ruleId: Vector,
  appliesTo: ObjectType | Lineage | Tag,
  condition: erk_expression,
  effect: meta_effect,
  severity: level,
  category: group,
  message: string
}
```

Les MetaRules ne modifient jamais la fractale.  
Elles **signalent**, **classifient**, **évaluent**, **informent**, mais n’agissent pas.

---

# 2. Scénarios GEVR — Format structurel

Un scénario GEVR est un **pipeline fractal** :

```
Scenario = {
  scenarioId: Vector,
  description: string,
  steps: [
    {
      id: stepId,
      action: get | execute | validate | render,
      target: Vector | ObjectType,
      input: {
        ... paramètres
      },
      conditions: [ erk_conditions ],
      outputs: [ expected_vectors_or_states ]
    }
  ]
}
```

Rappel du cycle **G–E–V–R** :

- **GET** : charger un objet, un module, un fragment, une dépendance  
- **EXECUTE** : appliquer une méthode système ou agent  
- **VALIDATE** : vérifier MetaRules, MetaRelations, structure, cohérences  
- **RENDER** : produire un résultat (log, rapport, fragment, diff, module)

Les scénarios de tests G2 doivent tester :

- la cohérence du pipeline  
- la satisfaction ou non des conditions  
- la remontée correcte des erreurs / warnings  
- la stabilité du cycle sur données incomplètes ou contradictoires  

---

# 3. SuperTools — Catalogue minimal (phase A→G)

Voici la version officielle minimale, suffisante pour la génération des tests G2 :

```
SuperTools = {
  SuperRead:    read(objectVector) -> objectBundle
  SuperQuery:   query(criteria) -> list[Vectors]
  SuperCreate:  create(spec) -> newVector
  SuperUpdate:  update(vector, patch) -> updatedVector
  SuperDelete:  delete(vector) -> confirmation
  SuperEvaluate: evaluate(ruleSet, target) -> report
  SuperExecute: call(methodVector, inputs) -> outputBundle
}
```

Contraintes fondamentales :

- Aucun SuperTool ne peut modifier la fractale sans passer par **SuperCreate / SuperUpdate / SuperDelete**.
- SuperEvaluate ne modifie jamais : read-only + rapports.
- SuperExecute est contrôlé : toutes les méthodes sont des “safe methods”.
- Les tests G2 doivent inclure :
  - tests d’erreurs intentionnelles
  - tests de non-regression : impossible de bypasser SuperTools

---

# 4. Exemple de fractale — Structure type d’un objet

Voici un **exemple réaliste** d’un objet tel que visible par la fractale (XFractal) :

```
Object = {
  vector: Object:Page.Landing.MainHero,
  lineage: [
    Object,
    Object:Page,
    Object:Page.Landing,
    Object:Page.Landing.MainHero
  ],

  bundles: {
    attributes: {
      title: "string:required",
      theme: "colorSet:optional",
      layout: "layoutType"
    },

    methods: {
      render: Method:RenderPageHero,
      validate: Method:ValidateModule,
      suggestModules: Method:SuggestFromTags
    },

    rules: [
      Rule:PageMustHaveLayout,
      Rule:HeroMustHaveTitle,
      Rule:ThemeMustRespectPalette
    ],

    relations: {
      depends_on: [
        Module:HeroLayout,
        Module:TypographySet
      ],
      related_to: [
        Object:Site.Project.Homepage
      ],
      inherits_from: [
        Object:Page
      ]
    },

    tags: [ "ui", "hero", "landing", "critical-module" ]
  }
}
```

---

# 5. Conclusion — Quelle option choisir ?

Avec les informations ci-dessus, tu peux travailler en **mode aligné**.

Tu disposes maintenant :
- des MetaRules,
- du format GEVR,
- des SuperTools,
- d’un exemple fractal solide.

Tu peux lancer la génération des tests G2.

