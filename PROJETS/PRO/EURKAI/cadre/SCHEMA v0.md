SCHEMA v0

--------------------------------
1. Position
--------------------------------

Schema est un attribut de Object.

Tout objet possède un schema.

--------------------------------
2. Rôle
--------------------------------

Schema cadre la structure de l’objet.

Il définit :
- quels éléments peuvent exister
- quels éléments doivent exister
- quelles règles permettent de vérifier la conformité structurelle

--------------------------------
3. Spécificités
--------------------------------

Schema.owned_element_list {
  field_list
  required_element_list
  validation_rule_list
}

--------------------------------
4. Sens
--------------------------------

field_list
- liste les fields du schema

required_element_list
- indique les éléments requis par ce schema

validation_rule_list
- porte les règles permettant de valider la conformité
  de l’objet à ce schema

--------------------------------
5. Règle courte
--------------------------------

Schema ne définit pas l’usage de l’objet.
Schema définit sa structure et les règles de validation de cette structure.