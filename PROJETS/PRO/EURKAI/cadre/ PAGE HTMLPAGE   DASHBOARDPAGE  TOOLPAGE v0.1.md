PAGE / HTMLPAGE / DASHBOARDPAGE / TOOLPAGE v0

--------------------------------
1. Page
--------------------------------

Page est un objet.

Page ne définit pas directement :
- format
- view
- template

Page impose leur présence via schema / contract.

Page.required_element_list {
  format
  view
  template
  layout
  component_list
}

Règles :

- layout est requis
- layout possède une valeur par défaut
- cette valeur par défaut peut être portée par :
  - template
  - XPage
  - Layout lui-même

- Page impose que ses components portent les tags
  cohérents avec le type de page

Forme simplifiée de règle :

Page.component_list.component.tag_list
must match Page.type.ident
or Page.tag_list

Remarque :
- on utilise ici les tags plutôt que category
- cela suffit pour filtrer / valider la nature des composants


--------------------------------
2. Structure
--------------------------------

Structure
├── DOMStructure
└── HTMLStructure

Règles :

- DOMStructure est un objet distinct
- HTMLStructure hérite directement de Structure
- HTMLStructure n’hérite pas de DOMStructure
- DOMStructure peut utiliser HTMLStructure comme paramètre
  si nécessaire, sans ambiguïté d’héritage

Remarque :
- le scope de ces objets devra être défini précisément plus tard


--------------------------------
3. HTMLPage
--------------------------------

Page
→ HTMLPage

Rôle :
- Page rendue en HTML

Spécificités minimales :

HTMLPage.required_element_list {
  html_structure
  css_reference_list
  script_reference_list
}

Contraintes :

- html_structure = HTMLStructure
- css_reference_list porte les références de style
- script_reference_list porte les références de comportement

Remarque :
- format et template restent requis via Page
- HTMLPage n’en redéfinit pas la structure
- HTMLPage peut en contraindre la nature


--------------------------------
4. DashboardPage
--------------------------------

HTMLPage
→ DashboardPage

Justification :
- DashboardPage est justifié par une spécificité owned
  de mission / goal / type dominant

Mission dominante :
- lecture synthétique
- état système
- action transverse

Conséquence :
- cette mission dominante pourra influer plus tard sur :
  - attributs
  - méthodes
  - règles
  - hooks
  - validate.afterhook
  - comportements de monitoring

Spécificités minimales :

DashboardPage.required_element_list {
  dashboard_goal
}

Remarque :
- DashboardPage ne se justifie pas par une structure HTML radicalement différente
- il se justifie par sa mission dominante


--------------------------------
5. ToolPage
--------------------------------

DashboardPage
→ ToolPage

ToolPage est un sous-type spécialisé de DashboardPage.

Mission dominante :
- manipulation
- test
- debug
- exécution assistée
- inspection de pipeline / méthode / endpoint / playground

Règle de constitution :

ToolPage.component_list.component.tag_list
must match ToolPage.type.ident
or ToolPage.tag_list

Conséquence :
- les composants de ToolPage doivent être taggés de façon cohérente avec ToolPage
- ex :
  - tool
  - endpoint
  - playground
  - validator
  - raw_view
  - preview_view

Remarque :
- ToolPage spécialise DashboardPage par restriction / orientation
  de ses composants
- pas nécessairement par une structure différente


--------------------------------
6. Instance prévue
--------------------------------

DashboardPage:ToolPage@EurkaiToolPage

Remarque :
- ToolPage = type
- EurkaiToolPage = instance


--------------------------------
7. Notes importantes
--------------------------------

- Un objet peut être justifié par une spécificité owned
  de mission / goal / type dominant.
- Cela vaut notamment pour :
  - DashboardPage
  - ToolPage
  - PipelineScenario
- Les nuances exactes de paramétrage induites par cette justification
  seront précisées plus tard.

- Pipeline pourra plus tard porter par exemple :
  - mvp_presence
  - execution_level

- En MVP :
  - données de test / démo
  - complexité réduite
- En preprod / prod :
  - exigences plus fortes