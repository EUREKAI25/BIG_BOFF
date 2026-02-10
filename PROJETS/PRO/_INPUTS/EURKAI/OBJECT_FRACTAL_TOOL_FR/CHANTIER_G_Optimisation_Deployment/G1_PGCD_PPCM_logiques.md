
# PROMPT G1/9 — PGCD/PPCM logiques (optimisation structurelle)

## CONTEXTE

Le système EURKAI est maintenant capable de :
- décrire, analyser et exécuter des projets,
- exporter et booter des projets concrets.

Tu dois maintenant exploiter tes intuitions **PGCD / PPCM** pour :

- factoriser le cœur commun (PGCD logique),
- identifier le set minimal de méthodes / règles couvrant plusieurs cas (PPCM logique).

Il s’agit d’outils d’**optimisation structurelle**.

## CE QUE TU AS EN INPUT

- La fractale complète (post-déploiement).
- Les MetaRules et MetaRelations (C2/2, C3/3).
- Des projets multiples (potentiellement similaires ou apparentés).

## CE QUE TU DOIS PRODUIRE

1. Une définition opérationnelle :

   - PGCD logique = ce qui est commun à un ensemble d’objets / scénarios,
   - PPCM logique = le plus petit ensemble de méthodes / règles permettant de couvrir les besoins d’un ensemble de cas.

2. Des **outils d’analyse**, par ex. :

   - `computeLogicalPGCD(objects[]) -> coreDefinition`
   - `computeLogicalPPCM(methodSets[]) -> minimalMethodSet`

3. Des exemples :

   - groupe de scénarios → PGCD = tronc commun,
   - groupe de types d’agents → PPCM = méthodes strictement nécessaires.

## CONTRAINTES

- Ces outils doivent :
  - rester analytiques / suggestifs (ne pas modifier directement la fractale),
  - fournir des résultats interprétables par un humain.

## FORMAT DE SORTIE

Ta réponse doit inclure :

1. La définition précise du PGCD/PPCM logiques pour EURKAI.
2. La description des fonctions d’analyse.
3. Des exemples de cas concrets (avec input/output).
4. Des cas de test.

## CHECKLIST DE VALIDATION

- [ ] Les notions PGCD/PPCM sont clairement opérationnalisées dans le contexte EURKAI.
- [ ] Des fonctions d’analyse sont définies de manière exploitable.
- [ ] Tu as fourni des exemples + cas de test.
