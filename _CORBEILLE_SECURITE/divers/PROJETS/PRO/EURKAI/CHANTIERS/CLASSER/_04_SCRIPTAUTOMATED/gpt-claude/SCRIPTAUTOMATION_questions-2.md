# SCRIPTAUTOMATION — Questions pour compléter le cahier des charges

## Questions critiques pour démarrer le développement

### 1. ARCHITECTURE ET CONVENTIONS

#### 1.1 Structure `builder_state`
- Quelle est la structure exacte de l'objet `builder_state` ?
- Quels sont tous les champs attendus (brief, function_name, language, constraints, context, paths, etc.) ?
- Format JSON exact attendu ?

#### 1.2 Fonction `report_actions`
- Quelle est la signature exacte de `report_actions()` ?
- Quels paramètres accepte-t-elle ?
- Format des logs produits ?
- Où sont stockés les logs ?

#### 1.3 Conventions de docstring
- Format exact attendu pour les docstrings ?
- Sections obligatoires (Args, Returns, Raises, Examples, etc.) ?
- Exemple concret d'une docstring conforme ?

#### 1.4 Conventions de métadonnées
- Structure exacte des métadonnées à générer ?
- Champs obligatoires (version, author, date, dependencies, etc.) ?
- Format (JSON, YAML, dict Python) ?

### 2. INTÉGRATION IA

#### 2.1 API et modèle
- Quelle API IA utiliser ? (OpenAI, Anthropic Claude, autre ?)
- Quel modèle spécifique ? (gpt-4, claude-3-opus, etc.)
- Y a-t-il une bibliothèque cliente déjà en place ?
- Gestion des clés API (variables d'environnement, fichier config) ?

#### 2.2 Structure des appels IA
- Format exact de l'appel à l'IA ?
- Paramètres (température, max_tokens, etc.) ?
- Gestion des erreurs API ?
- Système de retry en cas d'échec ?

#### 2.3 Parsing des réponses IA
- Les réponses IA sont-elles toujours en JSON valide ?
- Faut-il extraire le JSON d'un bloc markdown ?
- Gestion des réponses malformées ?

### 3. GESTION DES FICHIERS ET PATHS

#### 3.1 Structure des répertoires
- Arborescence exacte du projet ?
- Où stocker :
  - Les fonctions générées ?
  - Les tests générés ?
  - Les rapports ?
  - Les logs ?
  - Les métadonnées ?
  - Les fichiers temporaires ?

#### 3.2 Conventions de nommage
- Format exact des noms de fichiers générés ?
- Préfixes/suffixes obligatoires ?
- Gestion des conflits de noms ?

### 4. EXÉCUTION ET TESTS

#### 4.1 Framework de tests
- Quel framework utiliser ? (pytest, unittest, autre ?)
- Conventions de nommage des tests ?
- Structure des fichiers de tests ?
- Fixtures communes à utiliser ?

#### 4.2 Exécution des tests
- Comment exécuter les tests programmatiquement ?
- Format du rapport de tests attendu ?
- Extraction des erreurs (traceback, message, ligne) ?
- Gestion du timeout ?

#### 4.3 Critères de validation
- Seuils exacts de couverture de code ?
- Nombre minimum de tests requis ?
- Types de tests obligatoires (nominal, erreur, limite) ?

### 5. BOUCLE DE CORRECTION

#### 5.1 Critères d'arrêt
- Nombre maximum d'itérations de correction ?
- Critères de succès précis ?
- Que faire si la boucle ne converge pas ?

#### 5.2 Contexte de correction
- Quelles informations exactes fournir à l'IA pour la correction ?
- Format du rapport d'erreur à transmettre ?
- Historique des tentatives précédentes ?

### 6. CONTRAINTES ET CONTEXTE

#### 6.1 Fichier de contraintes
- Format exact du fichier de contraintes agence ?
- Où le trouver ?
- Structure du contenu ?

#### 6.2 Contexte de code existant
- Comment charger le contexte de code existant ?
- Quels fichiers inclure ?
- Format d'indexation ?
- Limite de taille du contexte ?

### 7. OUTPUTS ET RAPPORTS

#### 7.1 Rapport de validation
- Structure exacte du rapport de validation ?
- Sections obligatoires ?
- Format (Markdown, JSON, HTML) ?

#### 7.2 README généré
- Template du README à produire ?
- Sections obligatoires ?
- Niveau de détail attendu ?

### 8. GESTION DES ERREURS

#### 8.1 Erreurs récupérables
- Liste des erreurs à gérer en retry ?
- Stratégie de retry ?

#### 8.2 Erreurs fatales
- Quelles erreurs doivent arrêter le processus ?
- Format du rapport d'erreur fatal ?

### 9. DÉPENDANCES

#### 9.1 Bibliothèques Python
- Liste complète des dépendances externes ?
- Versions spécifiques requises ?
- Y a-t-il un fichier requirements.txt existant ?

#### 9.2 Outils externes
- Outils système requis (linters, formatters) ?
- Versions spécifiques ?

### 10. LISTE COMPLÈTE DES FONCTIONS

#### 10.1 Fonctions manquantes dans functions_list.md
Le document functions_list.md ne contient que la liste des TESTS, mais pas la liste des FONCTIONS elles-mêmes.

**Il me faut la liste complète avec pour chaque fonction :**
- Nom exact du fichier
- Signature complète (paramètres et types)
- Description du rôle
- Inputs attendus (structure exacte)
- Outputs produits (structure exacte)
- Dépendances (appels à d'autres fonctions)

**Exemple de format attendu :**
```
auto_function_builder_get_brief.py
---
def get_brief(builder_state: dict) -> dict:
    """
    Récupère et normalise le brief fourni par l'utilisateur.
    
    Args:
        builder_state: État global contenant au minimum {'brief_raw': str}
    
    Returns:
        dict: {'brief_normalized': str, 'brief_type': str, 'complexity': str}
    
    Raises:
        ValueError: Si le brief est vide ou invalide
    """
```

### 11. EXEMPLES CONCRETS

Pour faciliter la compréhension, j'ai besoin d'exemples concrets :

#### 11.1 Brief exemple
- Un exemple complet de brief d'entrée
- Ce qu'on attend comme fonction générée
- Les tests attendus pour cette fonction

#### 11.2 function_spec exemple
- Structure JSON complète d'un function_spec après analyse

#### 11.3 Squelette exemple
- Code d'un squelette de fonction conforme

#### 11.4 Métadonnées exemple
- Structure complète d'un fichier de métadonnées

### 12. TEMPLATE DE PROMPT IA

Le document mentionne un template dans la section 8, mais il indique :
```
{{ … le template complet est injecté ici … }}
```

**J'ai besoin du template complet et exact à utiliser pour :**
- analyze
- generate_code
- generate_tests
- fix_apply

Avec les variables à substituer clairement identifiées.

---

## Informations complémentaires utiles

### Priorités
1. Quelle est la priorité de développement ? (ordre des fonctions à coder en premier)
2. Y a-t-il des fonctions déjà existantes à réutiliser ?
3. Y a-t-il des modules EURKAI existants à importer ?

### Validation
1. Qui valide le code produit ?
2. Y a-t-il un processus de review ?
3. Critères d'acceptation précis ?

### Déploiement
1. Comment sera utilisé le système une fois développé ?
2. Interface CLI, API, autre ?
3. Environnement d'exécution (local, serveur, conteneur) ?

---

## Format de réponse attendu

Pour faciliter l'intégration de vos réponses, merci de fournir :

1. Un fichier **`SCRIPTAUTOMATION_architecture.json`** contenant :
   - Structure de builder_state
   - Conventions de nommage
   - Arborescence des répertoires

2. Un fichier **`SCRIPTAUTOMATION_functions_specs.md`** contenant :
   - Liste complète des fonctions avec signatures détaillées
   - Ordre de dépendances entre fonctions

3. Un fichier **`SCRIPTAUTOMATION_prompts_templates.md`** contenant :
   - Les 4 templates de prompts IA complets

4. Un fichier **`SCRIPTAUTOMATION_examples.json`** contenant :
   - Exemples concrets de brief, function_spec, métadonnées, etc.

5. Un fichier **`SCRIPTAUTOMATION_conventions.md`** contenant :
   - Format docstring exact
   - Format métadonnées exact
   - Règles de code (imports, logging, etc.)

---

**Une fois ces informations fournies, je pourrai générer l'intégralité du système AUTO FUNCTION BUILDER de façon cohérente et conforme à vos standards.**
