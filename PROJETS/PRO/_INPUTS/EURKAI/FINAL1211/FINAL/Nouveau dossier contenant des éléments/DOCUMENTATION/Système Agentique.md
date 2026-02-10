# EUREKAI — Système Agentique
## Prompts Modulaires, Teams et Fine-tuning

---

# PARTIE 1 : PROMPT MODULAIRE RÉCURSIF

## 1.1 Principe

Le prompt est assemblé comme un template, du plus général au plus spécifique.
Chaque objet peut définir ses propres fragments de prompt qui s'injectent dans la chaîne.
Le résultat est similaire à l'exécution d'un script — l'agent ne décide pas, il exécute.
La suite dépend du `hookAfter`, pas de l'agent.

```
HÉRITAGE (top-down)
═══════════════════

Object
└── prompt.context = "EUREKAI System"
    │
    └── Entity
        └── prompt.context = "{{parent.prompt.context}} | Entity layer"
            │
            └── Schema
                └── prompt.context = "{{parent.prompt.context}} | Schema module"
                    │
                    └── Schema:UserAuth
                        └── prompt.context = (hérite) + "Authentication system"
```

## 1.2 Fragments de Prompt

Chaque objet peut définir ces fragments (tous optionnels, hérités si absents) :

| Fragment | Description |
|----------|-------------|
| `prompt.context` | Contexte général, environnement |
| `prompt.role` | Rôle assigné à l'agent |
| `prompt.personality` | Traits de personnalité, ton |
| `prompt.goal` | Objectif précis de la tâche |
| `prompt.constraints` | Contraintes à respecter |
| `prompt.format` | Format de sortie attendu |
| `prompt.examples` | Exemples few-shot |
| `prompt.forbidden` | Ce qui est interdit |

## 1.3 Placeholders

Tous les objets exposés sont disponibles via leur lineage ou alias.

### Syntaxe

```
{{lineage}}                          Objet par lineage complet
{{alias}}                            Objet par alias défini
{{Object:Entity:Client.name}}        Accès attribut direct
{{client.facture.list}}              Navigation relationnelle
{{parent.prompt.context}}            Héritage du parent
{{self.name}}                        Objet courant
{{project.config.locale}}            Configuration projet
{{method().result}}                  Résultat d'une méthode
```

### Objets disponibles

```
{{self}}          Objet courant
{{parent}}        Objet parent direct
{{root}}          Racine de la hiérarchie
{{project}}       Projet en cours
{{agent}}         Agent assigné à la tâche
{{input}}         Données d'entrée
{{context}}       Contexte d'exécution
{{config}}        Configuration système
```

## 1.4 Assemblage du Prompt

```
┌─────────────────────────────────────────────────────────────┐
│                    OBJET CIBLE                              │
│                 (ex: Schema:UserAuth)                       │
│                                                             │
│  .method = generateSchema                                   │
│  .prompt.goal = "Générer le schéma {{self.name}}"          │
│  .hookAfter = ValidateSchema                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  1. COLLECT                                 │
│                                                             │
│  Remonter la hiérarchie, collecter tous les fragments      │
│  de prompt (context, role, personality, goal...)            │
│  Résoudre l'héritage (si absent → prendre du parent)       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. RESOLVE                                 │
│                                                             │
│  Résoudre tous les {{placeholders}}                        │
│  Injecter les données des objets exposés                   │
│  Évaluer les expressions                                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. ASSEMBLE                                │
│                                                             │
│  Assembler le prompt final dans l'ordre:                   │
│  context → role → personality → goal →                     │
│  constraints → format → examples → forbidden               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. EXECUTE                                 │
│                                                             │
│  Envoyer au LLM (comme un script)                          │
│  Parser la réponse selon format attendu                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  5. HOOK                                    │
│                                                             │
│  hookAfter → détermine la suite                            │
│  (pas l'agent qui décide)                                  │
└─────────────────────────────────────────────────────────────┘
```

## 1.5 Hooks

Trois hooks seulement :

| Hook | Déclencheur |
|------|-------------|
| `before` | Avant exécution de la méthode |
| `after` | Après exécution (succès) |
| `failure` | En cas d'échec |

Les événements spécifiques (onDisagree, onTimeout, onConsensus...) sont gérés par des **Triggers**.

## 1.6 Triggers

```
Trigger:OnDisagree
├── event = disagree
├── condition = consensus < 0.5
└── action = Meeting.escalate(human)

Trigger:OnTimeout
├── event = timeout  
├── condition = duration > maxDuration
└── action = Meeting.forceSynthesis()

Trigger:OnConsensus
├── event = consensus
├── condition = consensus >= 0.7
└── action = Meeting.proceed(implementation)

Trigger:OnHumanJoin
├── event = participantJoin
├── condition = participant.type = human
└── action = Meeting.pause() + Meeting.welcome()
```

## 1.7 Exemple Complet

```
# Définition de l'objet

Schema:UserAuth
├── .name = UserAuth
├── .method = generateSchema
├── .prompt.context = "{{parent.prompt.context}}"
├── .prompt.goal = "Générer le schéma d'authentification avec:"
│   ├── "- Tables: {{self.tables.list}}"
│   ├── "- Relations: {{self.relations.list}}"
│   └── "- Contraintes: {{self.constraints.list}}"
├── .prompt.format = "JSON avec clés: tables, indexes, constraints"
├── .prompt.constraints = "Nommage snake_case, UUID pour PKs"
├── .hookBefore = ValidateInput
├── .hookAfter = ValidateSchema
├── .hookFailure = NotifyAdmin
└── .output = schema.json


# Prompt assemblé (après résolution)

CONTEXT:
EUREKAI System | Entity layer | Schema module | Authentication system

ROLE:
Tu es un architecte base de données senior.

GOAL:
Générer le schéma d'authentification avec:
- Tables: users, sessions, permissions, roles
- Relations: users->sessions, users->roles, roles->permissions
- Contraintes: email unique, session expire 24h

FORMAT:
JSON avec clés: tables, indexes, constraints

CONSTRAINTS:
Nommage snake_case, UUID pour PKs
```

---

# PARTIE 2 : TEAMS D'AGENTS

## 2.1 Principe

Chaque agent est potentiellement une team, même à une seule entité.
Le type d'organisation dépend de la complexité et est défini par le **StrategistAgent**.

## 2.2 Types d'organisation

| Type | Agents | Moderator | Usage |
|------|--------|-----------|-------|
| SOLO | 1 | Non | Tâches simples, exécution directe |
| PAIR | 2 | Non | Validation croisée, ping-pong |
| TEAM | 3-5 | Oui (Orchestrator) | Discussion, consensus |
| COUNCIL | 6+ | Oui (Orchestrator + Reviewer) | Décisions critiques, réunions structurées |

## 2.3 StrategistAgent

Le StrategistAgent définit la composition de la team selon le schéma/projet/tâche.
Il détermine les compétences requises et le niveau d'expertise.

```
StrategistAgent
├── input = Schema | Project | Task
├── method = defineTeamComposition
└── output = TeamStrategy
    ├── requiredRole = [list of roles]
    ├── expertiseLevel = {role: level}
    ├── organizationType = solo | pair | team | council
    ├── moderatorRequired = true | false
    └── humanParticipation = none | observe | intervene | participate | chair
```

### Exemple: Projet complexe

```
Input: Schema:EcommerceCheckout

StrategistAgent.output:
├── requiredRole
│   ├── architect (senior) — structure globale
│   ├── security (senior) — paiement sensible
│   ├── ux (mid) — parcours utilisateur
│   ├── performance (mid) — rapidité checkout
│   └── qa (junior) — validation
├── organizationType = council
├── moderatorRequired = true
└── humanParticipation = intervene
```

### Exemple: Tâche simple

```
Input: Schema:SimpleContactForm

StrategistAgent.output:
├── requiredRole
│   └── generator (junior)
├── organizationType = solo
├── moderatorRequired = false
└── humanParticipation = none
```

## 2.4 Réunions Live

Niveaux de participation humaine :

| Level | Mode | Description |
|-------|------|-------------|
| 0 | AUTO | Agents seuls, humain reçoit le résultat |
| 1 | OBSERVE | Humain voit la discussion (read-only) |
| 2 | INTERVENE | Humain peut interrompre, poser des questions |
| 3 | PARTICIPATE | Humain participe avec droit de parole |
| 4 | CHAIR | Humain préside, donne la parole, tranche |

### Exemple de réunion

```
Meeting:OptimizePerformance
├── type = council
├── topic = "Optimiser vitesse sans perdre qualité graphique"
├── participant
│   ├── ArchitectAgent (pertinence: infra)
│   ├── DesignAgent (pertinence: graphique)
│   ├── PerformanceAgent (pertinence: vitesse)
│   └── Client:Jean (human, level=participate)
├── moderator = OrchestratorAgent
├── rule
│   ├── speakingOrder = byRelevance
│   ├── maxSpeakTime = 60s
│   ├── minPauseBetween = 5s
│   └── consensusRequired = 0.7
├── trigger
│   ├── Trigger:OnDisagree
│   ├── Trigger:OnTimeout
│   └── Trigger:OnConsensus
└── output = Decision:OptimizeStrategy
```

### Interface conceptuelle

```
┌─────────────────────────────────────────────────────────┐
│  🎙️ Réunion: Optimiser Performance        [En cours]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ArchitectAgent (parle):                                │
│  "Je propose de mettre en cache les assets statiques    │
│   côté CDN, ça réduirait de 40% le temps de charge..."  │
│                                                         │
│  ──────────────────────────────────────────────────────│
│                                                         │
│  File d'attente:                                        │
│  1. DesignAgent (pertinence: 0.9)                       │
│  2. Client:Jean (demande parole)                        │
│  3. PerformanceAgent (pertinence: 0.7)                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [🖐️ Demander parole] [⏸️ Pause] [📝 Note] [✋ Stop]   │
└─────────────────────────────────────────────────────────┘
```

---

# PARTIE 3 : FINE-TUNING

## 3.1 Quand fine-tuner ?

### Cas où le fine-tuning est pertinent

| Cas | Exemple | Raison |
|-----|---------|--------|
| Expertise technique pointue | SecurityAgent sur CVE, OWASP | Subtilités que le prompt ne capture pas |
| Style/ton très spécifique | CopywriterAgent:LuxuryBrand | Cohérence de marque sur milliers de contenus |
| Domaine métier fermé | LegalAgent:DroitFrançais | Jurisprudence, terminologie spécifique |
| Format propriétaire strict | CodeGenerator:COBOL | Conventions legacy mal connues du modèle |
| Volume + cohérence | TranslatorAgent:TechnicalDocs | 100,000 pages avec glossaire strict |

### Cas où le prompt suffit

| Cas | Exemple |
|-----|---------|
| Connaissance générale | ArchitectAgent standard |
| Rôle de coordination | OrchestratorAgent |
| Génération standard | GeneratorAgent:Website |
| Validation/review | ReviewerAgent |
| Planification | PlannerAgent |

## 3.2 Matrice de décision

| Critère | Prompt seul | Fine-tune |
|---------|-------------|-----------|
| Connaissance générale | ✅ | ❌ |
| Domaine très spécialisé | ❌ | ✅ |
| Style/ton unique | ⚠️ | ✅ |
| Format standard | ✅ | ❌ |
| Format propriétaire strict | ❌ | ✅ |
| Volume faible (<1000/mois) | ✅ | ❌ |
| Volume élevé (>10,000/mois) | ⚠️ | ✅ |
| Évolution fréquente | ✅ | ❌ |
| Stabilité long terme | ⚠️ | ✅ |
| Budget limité | ✅ | ❌ |
| Qualité critique | ⚠️ | ✅ |

## 3.3 Stratégie recommandée

### Phase 1 : Prompt seul (maintenant)

```
├── Tous les agents en prompt engineering
├── Tester, itérer, valider les rôles
└── Collecter des données de qualité (inputs/outputs)
```

### Phase 2 : Fine-tune sélectif (quand stable)

```
├── Identifier les agents qui peinent
├── Collecter 500-2000 exemples gold
└── Fine-tune uniquement sur les cas critiques
```

### Phase 3 : Fine-tune par client (scale)

```
├── Chaque client majeur a ses agents personnalisés
├── Base EUREKAI + couche client fine-tunée
└── Modèle hybride : base générale + spécialisation
```

## 3.4 Exemples de fine-tuning

### SecurityAgent

```
Fine-tune sur:
├── CVE database (vulnérabilités connues)
├── OWASP guidelines
├── Patterns de code vulnérable
├── Audits de sécurité réels (anonymisés)
└── ~2000 exemples

Résultat attendu:
├── Détection de failles subtiles
├── Recommandations contextuelles
└── Conformité aux standards
```

### LegalAgent:DroitFrançais

```
Fine-tune sur:
├── Jurisprudence française
├── Codes (civil, commerce, travail)
├── Décisions de justice
├── Modèles de contrats validés
└── ~5000 exemples

Résultat attendu:
├── Terminologie juridique précise
├── Références aux articles de loi
└── Structure conforme aux usages
```

### CopywriterAgent:LuxuryBrand

```
Fine-tune sur:
├── Corpus existant de la marque
├── Ton éditorial validé par le client
├── Termes interdits / obligatoires
├── Exemples approuvés
└── ~1000 exemples

Résultat attendu:
├── Voix de marque cohérente
├── Respect du territoire sémantique
└── Adaptation automatique au support
```

---

# PARTIE 4 : RÉSUMÉ

## Architecture globale

```
┌─────────────────────────────────────────────────────────────┐
│                        EUREKAI                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OBJETS                                                     │
│  ├── Chaque objet peut avoir ses fragments de prompt        │
│  ├── Héritage automatique du parent                         │
│  └── Placeholders résolus dynamiquement                     │
│                                                             │
│  MÉTHODES                                                   │
│  ├── Appartiennent aux objets (pas aux agents)              │
│  ├── Définissent le goal et le format                       │
│  └── Hooks: before / after / failure                        │
│                                                             │
│  AGENTS                                                     │
│  ├── Exécutent les méthodes (comme un script)               │
│  ├── Ne décident pas de la suite (hookAfter)                │
│  ├── Peuvent être en team (solo/pair/team/council)          │
│  └── Organisation définie par StrategistAgent               │
│                                                             │
│  PROMPTS                                                    │
│  ├── Assemblés par héritage (top-down)                      │
│  ├── Fragments: context, role, personality, goal...         │
│  ├── Placeholders: {{object.attr}}, {{method().result}}     │
│  └── Fine-tuning optionnel pour cas spécifiques             │
│                                                             │
│  TRIGGERS                                                   │
│  ├── Événements spécifiques (disagree, timeout, consensus)  │
│  └── Actions automatiques                                   │
│                                                             │
│  RÉUNIONS LIVE                                              │
│  ├── Participation humaine (observe → chair)                │
│  ├── Modération par OrchestratorAgent                       │
│  └── Consensus et prise de décision                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Changelog

- **v1.0** (2024-12-12) : Version initiale
  - Prompt modulaire récursif
  - Teams d'agents
  - Stratégie de fine-tuning
  - Réunions live