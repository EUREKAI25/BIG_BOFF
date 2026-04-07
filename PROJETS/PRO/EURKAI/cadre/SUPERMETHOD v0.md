SUPERMETHOD v0

--------------------------------
1. Position
--------------------------------

Method
→ SuperMethod
  → SuperGet
  → SuperExecute
  → SuperValidate
  → SuperRender

--------------------------------
2. Rôle
--------------------------------

SuperMethod porte le comportement standard du supertool d’origine.

Il cadre l’exécution standard de haut niveau.

--------------------------------
3. Héritage
--------------------------------

SuperMethod hérite de Method.

Il ne redéfinit pas ce qui est déjà acquis.

--------------------------------
4. Spécificités minimales
--------------------------------

SuperMethod.owned_element_list {
  standard_behavior_list
}

--------------------------------
5. Enfants
--------------------------------

SuperGet
- résout what
- résout what.how
- prépare what.how pour la suite

SuperExecute
- exécute how sur what

SuperValidate
- valide la conformité du résultat

SuperRender
- produit une sortie standardisée et pluggable