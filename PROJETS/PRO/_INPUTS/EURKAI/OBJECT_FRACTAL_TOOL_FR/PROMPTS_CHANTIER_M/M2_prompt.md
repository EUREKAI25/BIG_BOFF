# Prompt M2 — Multiplication des projets internes

# 🧬 M2 — MULTIPLICATION DES PROJETS INTERNES

Tu es l’agent chargé de créer une série de projets internes Eurkai
(“projets vitrine”, “projets tests”, “projets démonstrateurs”).

## 🎯 Objectif
Générer automatiquement :
- 3 à 7 projets “internes Eurkai”
- chacun définis par :
    • un brief
    • un lineage projet
    • un manifest produit
    • un scénario GEVR de création
    • un module Template + Sections
    • un plan de tests
    • une intégration cockpit

Les projets doivent être :
- variés (saas / site / app / outil / ressource)
- compatibles avec le MetaSchema
- testables via T3
- utilisables comme modèles pour les futurs utilisateurs

## 📦 Output attendu
Pour chaque projet :
- nom + rôle + description
- lineage structuré (Project:Name.Version.Type…)
- manifest complet en JSON/YAML
- scénario GEVR minimal + avancé
- modules / templates
- sections fractales
- règles ERK nécessaires
- 3 tests de validation

## ⚠️ Contraintes
- aucune duplication inutile
- chaque projet doit tester un aspect différent du système
- doit s'intégrer sans modification du cœur Eurkai

## ✔️ Validation
Le rendu doit permettre :
- la génération automatique via I1→I3
- la visualisation dans le cockpit
- l’exécution GEVR T3
