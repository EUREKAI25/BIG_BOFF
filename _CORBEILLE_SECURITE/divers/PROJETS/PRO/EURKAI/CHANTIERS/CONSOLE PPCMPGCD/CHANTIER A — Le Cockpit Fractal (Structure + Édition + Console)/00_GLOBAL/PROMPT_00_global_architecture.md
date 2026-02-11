# PROMPT 00 — Architecture globale (FR)

Tu es une IA développeuse. Ta mission est de concevoir l’architecture d’un outil web interne appelé **Object Fractal Tool**.

Lis attentivement :
- `SPEC_00_overview.md`
- `SPEC_00_metaschema_and_rules.md` (même si certaines sections restent TODO).

Contexte :
- L’outil manipule des **ObjectTypes** structurés par un MetaSchema fractal.
- Chaque objet est un Bundle, et chaque objet `X` possède un `XFractal` qui décrit :
  - attributs,
  - méthodes secondaires,
  - règles ERK,
  - relations,
  en les distinguant entre **owned**, **inherited**, **injected**.
- Les lineages obéissent à une nomenclature stricte validée par une regex.
- Les données doivent être stockées en JSON pour la V1.
- Le front doit être une application HTML/JS simple (type single-page).

Tâches :
1. Proposer une **architecture technique** simple mais modulaire :
   - Structures de données JSON pour représenter :
     - ObjectTypes,
     - lineages,
     - tags / catégories,
     - alias,
     - schémas de Bundles,
     - XFractal.
   - Composants UI principaux :
     - Explorateur de lineages (arbre),
     - Vue fractale,
     - Sidebar tags/catégories/alias,
     - Éditeur de schémas,
     - Console de test.
2. Expliquer comment les étapes 01, 02, 03, 04 s’insèrent dans cette architecture.
3. Décrire comment les modifications UI (drag & drop, édition de schémas, ajout de tags…) mettent à jour le JSON.

Output attendu :
- Un document d’architecture clair (sections : Données, Composants UI, Flux de mise à jour, Extensibilité).
- Pas d’implémentation complète ici, seulement le plan structuré.
