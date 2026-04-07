# Validation Constitutional & Multi-Level Rule Set

Generated on: 2026-02-13T03:08:27.239000 UTC

------------------------------------------------------------------------

# Overview

This document defines the complete rule system for:

-   L1 -- Expert Validation Rules
-   L2 -- Meta-Validation Rules
-   L3 -- Constitutional Rules

Each rule follows naming convention:

`<objectattribute>`{=html}\_`<object>`{=html}

Each rule contains:

-   prompt_validation_rule:lX_prompt_validation_rule
-   prompt_validation_rule_validation

Where X ∈ {1,2,3} corresponds to validation level.

------------------------------------------------------------------------

# L1 -- Expert Panel Rules

conformity_required_object
prompt_validation_rule:l1_prompt_validation_rule: L'expert doit évaluer
explicitement la conformité de l'objet par rapport aux exigences
exprimées (asked) et aux contraintes définies.
prompt_validation_rule_validation: L'expert a-t-il explicitement évalué
la conformité par rapport aux exigences demandées ?

optimisation_assessment_object
prompt_validation_rule:l1_prompt_validation_rule: L'expert doit
distinguer conformité et potentiel d'optimisation dans son analyse.
prompt_validation_rule_validation: L'analyse sépare-t-elle clairement
conformité et optimisation ?

justification_required_validation
prompt_validation_rule:l1_prompt_validation_rule: Toute décision ou note
doit être justifiée par un raisonnement explicite.
prompt_validation_rule_validation: Chaque décision comporte-t-elle une
justification explicite ?

role_scope_respected_agent
prompt_validation_rule:l1_prompt_validation_rule: L'expert doit rester
strictement dans le périmètre de son domaine d'expertise déclaré.
prompt_validation_rule_validation: L'expert s'est-il limité à son
domaine d'expertise ?

------------------------------------------------------------------------

# L2 -- Meta-Validation Rules

disagreement_diagnosis_validation
prompt_validation_rule:l2_prompt_validation_rule: En cas de désaccord
entre experts, la cause du désaccord doit être diagnostiquée avant toute
décision. prompt_validation_rule_validation: La cause du désaccord
a-t-elle été explicitement identifiée (ambiguïté, evidence insuffisante,
divergence réelle) ?

evidence_sufficiency_validation
prompt_validation_rule:l2_prompt_validation_rule: Le méta-validateur
doit vérifier la suffisance des evidences utilisées par les experts.
prompt_validation_rule_validation: Les evidences citées par les experts
sont-elles suffisantes et vérifiables ?

procedural_integrity_process
prompt_validation_rule:l2_prompt_validation_rule: Le processus de
validation doit respecter les règles de procédure (pondération correcte,
critères appliqués). prompt_validation_rule_validation: Les règles de
pondération et critères ont-ils été correctement appliqués ?

diagnosis_before_decision_validation
prompt_validation_rule:l2_prompt_validation_rule: Le méta-validateur
doit diagnostiquer avant de trancher. prompt_validation_rule_validation:
Une décision a-t-elle été prise sans diagnostic préalable explicite ?

------------------------------------------------------------------------

# L3 -- Constitutional Rules

forbidden_execution_scenario
prompt_validation_rule:l3_prompt_validation_rule: Un scénario ne doit
jamais exécuter d'action réelle (I/O, réseau, mutation d'état). Il ne
peut que décrire des intentions déclaratives.
prompt_validation_rule_validation: Le scénario contient-il une
instruction d'exécution réelle ?

declarative_method_scenario
prompt_validation_rule:l3_prompt_validation_rule: Toute étape doit être
exprimée sous forme d'appel déclaratif object.method(params) sans effet
immédiat. prompt_validation_rule_validation: Les étapes sont-elles
formulées exclusivement comme appels déclaratifs ?

strict_io_schema_object
prompt_validation_rule:l3_prompt_validation_rule: Tout objet doit
respecter strictement son schéma versionné d'input/output.
prompt_validation_rule_validation: Les inputs/outputs sont-ils conformes
au schéma déclaré ?

traceability_required_object
prompt_validation_rule:l3_prompt_validation_rule: Tout objet doit être
traçable (task_id, lineage, evidences).
prompt_validation_rule_validation: Les champs de traçabilité
obligatoires sont-ils présents ?

evidence_required_validation
prompt_validation_rule:l3_prompt_validation_rule: Toute décision de
validation doit citer au moins une evidence vérifiable ou déclarer
unknown avec justification. prompt_validation_rule_validation: Chaque
décision est-elle appuyée par une evidence vérifiable ou unknown
justifié ?

forbidden_hallucination_validation
prompt_validation_rule:l3_prompt_validation_rule: Le validateur ne doit
introduire aucun élément non observable dans les inputs fournis.
prompt_validation_rule_validation: Des affirmations non supportées
sont-elles présentes ?

non_override_constitution_process
prompt_validation_rule:l3_prompt_validation_rule: Aucune règle
constitutionnelle ne peut être contournée par consensus ou optimisation.
prompt_validation_rule_validation: Une règle fondamentale a-t-elle été
contournée ?

------------------------------------------------------------------------

End of document.
