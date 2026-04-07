SUPERMETHOD v0.1

--------------------------------
1. Position
--------------------------------

Method
→ SuperMethod
  → SuperGet
  → SuperExecute
  → SuperValidate
  → SuperRender

SuperMethod porte le comportement standard du supertool d’origine.
Il cadre la MRG.

--------------------------------
2. Rôle
--------------------------------

SuperMethod ne porte pas une logique métier spécifique.
Il porte une logique opératoire standard et agnostique.

Il sert à :
- parcourir what
- appliquer how
- faire circuler l’exécution
- produire un résultat exploitable

--------------------------------
3. Cœur MRG
--------------------------------

Le cœur réel de la MRG est :

scan_and_do

Rôle :
- parcourir what
- appliquer how
- tester les règles
- exécuter récursivement ce qui doit l’être
- retourner result

Formule courte :
scan_and_do(what, how) → result

--------------------------------
4. Règle générale
--------------------------------

- what = ce qui doit être parcouru / testé / exécuté
- how = méthode ou logique à appliquer
- scan_and_do ne porte pas de logique métier
- scan_and_do applique how à what
- scan_and_do est agnostique

--------------------------------
5. SuperGet
--------------------------------

Rôle :
- résoudre what
- résoudre les paramètres utiles
- résoudre / préparer what.how
- mettre what.how en état ready si applicable

Fonctions minimales :
- resolve_what
- resolve_how
- resolve_payload
- set_ready_status

--------------------------------
6. SuperExecute
--------------------------------

Rôle :
- appeler scan_and_do
- exécuter how sur what
- produire result

Fonctions minimales :
- scan_and_do
- collect_result

--------------------------------
7. SuperValidate
--------------------------------

Rôle :
- valider what en appliquant les méthodes de validation prévues
- tester l’intégralité des règles de what
- ne rien imposer de spécial à ValidationResult
- rester totalement agnostique

Lecture canonique :
- what = règle_list / contract / schema / objet à valider
- how = validation methods prévues

Fonctions minimales :
- resolve_validation_rule_list
- resolve_validation_method_list
- validate_object_vs_schema
- validate_object_vs_contract
- score_validation

--------------------------------
8. SuperRender
--------------------------------

Rôle :
- rendre le result exploitable
- produire une sortie standardisée et pluggable
- exposer brut / rendu / formaté selon le contexte

Fonctions minimales :
- render_raw_output
- render_standard_output
- map_output_format

--------------------------------
9. Exécution canonique
--------------------------------

run =
if get and execute :
  if validate then success else failure
after

Rappels :
- les failures précoces sont gérés au niveau de la méthode concernée
- run n’a pas à traiter les corrections locales
- how.execute.after[] = value.reset par défaut, sauf overwrite

--------------------------------
10. ValidationResult
--------------------------------

On n’impose rien de spécial à ValidationResult.

ValidationResult :
- reste agnostique
- reflète le test de what par how
- ne porte pas de logique additionnelle propre

--------------------------------
11. Génération d’objet
--------------------------------

On crée aussi un script de génération d’objet.

Rôle :
- prendre un schema
- prendre les paramètres d’objet
- appeler un agent IA
- produire l’instance attendue
- valider ensuite cette instance via SuperValidate

Principe :
generate_object_from_schema(schema, params, agent) → object

Règle :
- le prompt et les objets doivent être suffisamment bien définis
  pour minimiser les erreurs de génération

--------------------------------
12. Ordre de construction
--------------------------------

1. poser Schema
2. poser SuperMethod
3. poser scan_and_do
4. poser validator object_vs_schema
5. poser generate_object_from_schema
6. poser le catalogue minimal
7. enregistrer et valider les premiers objets
8. seulement ensuite créer EurkaiToolPage