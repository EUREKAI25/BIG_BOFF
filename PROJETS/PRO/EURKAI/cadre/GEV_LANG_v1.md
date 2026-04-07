GEV — Generic Entity Vocabulary
Spécification de référence v1
Date : 2026-04-02
Mise à jour : 2026-04-02
Statut : STABLE — source de vérité unique

Sources : Eurkai_L0_Conventions_v1.md, ARCHITECTURE_OBJECTS.md, ERK_LANG_v1.md
Règle : en cas de conflit avec une autre source, ce document prime pour tout ce qui concerne
        la syntaxe GEV et la compilation GEV → JSON.

// Les commentaires GEV commencent par // (ligne) ou /* */ (bloc)
// GEV est le langage de DÉFINITION des objets EURKAI.
// JSON est le langage de PERSISTANCE (catalog).
// On écrit en GEV, on exécute en JSON. Comme TypeScript → JavaScript.


================================
1. RÔLE ET PÉRIMÈTRE
================================

// GEV définit les objets, leurs attributs, leurs schémas, leurs règles.
// ERK définit les expressions, conditions, hooks, cycles d'exécution.
// FORMULAS définit les briques atomiques de condition utilisées dans les règles.

// Ces trois langages sont complémentaires et non-redondants :
//   GEV    = quoi (structure, définition, hiérarchie)
//   ERK    = comment (exécution, règles, lifecycle)
//   FORMULAS = conditions (briques atomiques booléennes)

// Un fichier GEV a l'extension .gev
// Les labels (valeurs texte traduisibles) ont l'extension .l.gev
// La cible compilée est un fichier JSON (catalog entry ou catalog list)


================================
2. OPÉRATEURS FONDAMENTAUX
================================

:    Séparateur de lineage (héritage implicite, gauche → droite)
.    Séparateur objet/attribut
@    Instance         User@nathalie_admin
#    Tag              Category#Object:Scenario
&    Alias            MaintenanceValidate&Scenario@main
$    Règle            $HasName IN Object:Page
>    Méthode          Object:Agent>CreateFrom
?    Optionnel        temperature? IN Object:Agent:AttributeList
IN   Appartenance     temperature IN Object:Agent:AttributeList
=    Affectation      .description = "..."
//   Commentaire ligne
/* */ Commentaire bloc


================================
3. DÉCLARATION D'OBJET
================================

// Forme complète :

Object:Entity:User:
  .description = "Utilisateur du système"
  .version = "1.0"
  .automated = false

// Le : terminal indique une déclaration.
// Les ancêtres sont créés implicitement s'ils n'existent pas encore.
// Les attributs non déclarés sont hérités de Object (racine).

// Compilation → JSON (catalog_object_list) :
// {
//   "object_ident": "User",
//   "object_lineage": "Object:Entity:User",
//   "object_description": "Utilisateur du système",
//   "object_version": "1.0",
//   "object_automated": false,
//   "object_schema": "ObjectSchema"   // par défaut
// }


================================
4. DÉCLARATION D'ATTRIBUT
================================

// 4.1 Attribut dans une AttributeList

temperature IN Object:Agent:AttributeList
  .type = number
  .required = false
  .default = 0.7
  .description = "Température de génération IA"

// 4.2 Attribut optionnel — marqueur ?
// ? équivaut à .required = false. Plus concis en prise de notes rapide.

temperature? IN Object:Agent:AttributeList
  .type = number
  .default = 0.7

// 4.3 Syntaxe courte (attribut simple)

Object:Agent.temperature = 0.7

// 4.4 Sous-paramètres (indentation supplémentaire)
// Autorisé (pour un dev, pratique en prise de notes rapide).
// Déconseillé en production : lisibilité moindre.

temperature IN Object:Agent:AttributeList
  .type = number
    .min = 0
    .max = 2
  .default = 0.7

// Types supportés :
// string / str     chaîne (défaut)
// int              entier
// number           nombre décimal
// bool             booléen
// date             date ISO
// json             objet JSON
// lineage          référence à un objet GEV
// hex_color        couleur hexadécimale (#rrggbb)
// list             liste d'items
// object           dict structuré


================================
5. DÉCLARATION DE SCHÉMA
================================

// Un schéma définit des containers et types, jamais des valeurs directes (ERK règle 13).

Schema:UserSchema:
  .for = Object:Entity:User
  .required:
    user_ident    AND(EXISTS(user_ident), IS_NOT_EMPTY(user_ident))
    user_email    AND(EXISTS(user_email), MATCHES_REGEX(user_email, "^[^@]+@[^@]+$"))

// Compilation → JSON (catalog_schema_list) :
// {
//   "schema_ident": "UserSchema",
//   "object_schema": "SchemaSchema",
//   "schema_required_element_list": {
//     "user_ident":  { "rule_condition": "AND(EXISTS(user_ident), IS_NOT_EMPTY(user_ident))" },
//     "user_email":  { "rule_condition": "AND(EXISTS(user_email), MATCHES_REGEX(...))" }
//   },
//   "schema_validation_rule_list": {}
// }

// Note : les conditions de schéma utilisent les FORMULAS (voir FORMULAS_v1.md)


================================
6. DÉCLARATION DE RÈGLE
================================

// Forme complète — une règle appartient à la RuleList d'un objet.

HasName IN Object:Page:RuleList
  .type = validation
  .condition = AND(EXISTS(name), IS_NOT_EMPTY(name))
  .severity = error
  .message = "Le champ name est requis"
  .scope = *

// Forme courte avec $ :
$HasName IN Object:Page

// $ est le marqueur de règle. Équivaut à HasName IN Object:Page:RuleList.
// Les attributs (.type, .condition, etc.) s'ajoutent en indentation si besoin.

// .severity : error | warning | info
// .scope : * (tous) | null (non précisé) | valeur explicite
// .condition : FORMULAS (voir FORMULAS_v1.md)

// Compilation → JSON (catalog_rule_list ou object_rule_list) :
// {
//   "rule_ident": "HasName",
//   "rule_object": "Object:Page",
//   "rule_type": "validation",
//   "rule_condition": "AND(EXISTS(name), IS_NOT_EMPTY(name))",
//   "rule_severity": "error",
//   "rule_message": "Le champ name est requis",
//   "rule_scope": "*"
// }


================================
7. DÉCLARATION DE MÉTHODE
================================

// Forme complète :

CreateFrom IN Object:Agent:MethodList
  .type = secondary
  .parent = Create
  .params = [source]
  .description = "Crée un agent depuis une source"

// .type : central | secondary | supermethod | utility

// Forme courte avec > :
Object:Agent>CreateFrom

// > indique une méthode. Équivaut à CreateFrom IN Object:Agent:MethodList.
// Les deux formes sont acceptées. .method: reste aussi valide (ERK hérité).

// Compilation → JSON (object_method_list) :
// {
//   "method_ident": "CreateFrom",
//   "method_object": "Object:Agent",
//   "method_type": "secondary",
//   "method_parent": "Create",
//   "method_input": "[source]",
//   "method_description": "Crée un agent depuis une source"
// }


================================
8. INSTANCE
================================

// Une instance est un objet concret d'un type donné.
// Elle est adressée par @ : <Type>@<slug>

User@nathalie_admin:
  .user_ident = "nathalie_admin"
  .user_email = "nathalie@eurkai.com"
  .user_role  = Object:Entity:Agent

// Compilation → JSON (instance, hors catalog_object_list) :
// {
//   "object_ident": "nathalie_admin",
//   "object_lineage": "Object:Entity:User",
//   "user_ident": "nathalie_admin",
//   "user_email": "nathalie@eurkai.com",
//   "user_role": "Object:Entity:Agent"
// }

// Les instances ne vont PAS dans catalog_object_list (qui contient les archetypes).
// Elles vont dans la couche storage appropriée.


================================
9. LABELS (.l.gev)
================================

// Les valeurs texte traduisibles et les constantes nommées vivent dans .l.gev
// Un schema ne référence jamais une valeur directe — il pointe vers un label ou un vecteur.

/* Fichier : palette_presets.l.gev */
editorial_luxury:
  .primary   = "#2a1f14"
  .secondary = "#c8b078"
  .accent    = "#a08840"

tech_minimal:
  .primary   = "#1a73e8"
  .secondary = "#5f6368"
  .accent    = "#1a73e8"

// Référence depuis un objet GEV :
Object:Design:Palette.preset = editorial_luxury


================================
10. RELATIONS
================================

// Relations explicites (en complément du lineage implicite) :

Object:Agent depends_on Object:Role
Object:Agent related_to Object:Context
Object:Schema scope_of Object:Entity:User

// Relations canoniques :
// inherits_from   héritage structurel (implicite via lineage)
// depends_on      dépendance fonctionnelle
// related_to      association sémantique
// scope_of        périmètre d'application


================================
11. COMPILATION GEV → JSON
================================

// Un fichier .gev peut décrire N objets, schémas, règles, méthodes.
// Le compilateur GEV → JSON produit les entrées correspondantes dans le catalog.

// Règles de compilation :
// 1. Chaque déclaration Object:X:Y:          → entrée dans catalog_object_list
// 2. Chaque déclaration Schema:XSchema:      → entrée dans catalog_schema_list
// 3. Chaque RuleName IN X:RuleList           → entrée dans catalog_rule_list
// 4. Chaque $RuleName IN X                   → idem (forme courte)
// 5. Chaque attr IN X:AttributeList          → champ dans object_elementlist.object_base_list
// 6. Chaque attr? IN X:AttributeList         → idem, required = false
// 7. Chaque instance X@slug:                 → couche storage (pas le catalog)
// 8. Object:X>MethodName                     → entrée dans object_method_list
// 9. Les commentaires (// et /* */) sont ignorés
// 10. L'indentation est significative (2 ou 4 espaces)
//     Sous-indentation (param de param) : autorisée, ignorée par le compilateur

// Le compilateur est scenario_compile_gev (à créer).
// Le catalog JSON reste la source d'exécution.
// Le .gev est la source d'édition (plus lisible, versionnable, diffable).


================================
12. EXEMPLE COMPLET — OBJET EURKAI EN GEV
================================

// Déclaration de l'archetype Palette et de son schema

Object:Design:Palette:
  .description = "Palette de couleurs WCAG AA garantie. Produite par color_palette depuis un VisualIntent."
  .version = "1.0"
  .automated = true

  palette_primary    IN Object:Design:Palette:AttributeList
    .type = hex_color

  palette_secondary  IN Object:Design:Palette:AttributeList
    .type = hex_color

  palette_accent     IN Object:Design:Palette:AttributeList
    .type = hex_color

  palette_background IN Object:Design:Palette:AttributeList
    .type = hex_color

  palette_text_primary IN Object:Design:Palette:AttributeList
    .type = hex_color

  /* optionnels */
  palette_surface?   IN Object:Design:Palette:AttributeList
    .type = hex_color

Schema:PaletteSchema:
  .for = Object:Design:Palette
  .required:
    object_ident         AND(EXISTS(object_ident), IS_NOT_EMPTY(object_ident))
    object_lineage       AND(EXISTS(object_lineage), STARTS_WITH(object_lineage, "Object:Design:Palette"))
    palette_primary      AND(EXISTS(palette_primary), IS_NOT_EMPTY(palette_primary))
    palette_secondary    AND(EXISTS(palette_secondary), IS_NOT_EMPTY(palette_secondary))
    palette_accent       AND(EXISTS(palette_accent), IS_NOT_EMPTY(palette_accent))
    palette_background   AND(EXISTS(palette_background), IS_NOT_EMPTY(palette_background))
    palette_text_primary AND(EXISTS(palette_text_primary), IS_NOT_EMPTY(palette_text_primary))
