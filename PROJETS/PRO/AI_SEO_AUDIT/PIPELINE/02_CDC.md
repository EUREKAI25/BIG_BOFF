# CDC — AI_SEO_AUDIT

> Cahier des Charges — Service d'audit et d'optimisation de la visibilité des entreprises dans les réponses IA

**Date** : 2026-02-11
**Version** : MVP Mono-IA
**Statut** : 🟡 En validation

---

## 1. Contexte et problématique

### 1.1 Contexte général

Les intelligences artificielles conversationnelles (ChatGPT, Claude, Gemini, Perplexity) sont devenues des intermédiaires directs de recommandation. Les utilisateurs leur posent des questions comme :
- "Meilleur restaurant français près de chez moi"
- "Agence web spécialisée en IA"
- "Coach sportif certifié à Paris"

**Différence fondamentale avec Google** :
- Pas de publicité (Google Ads)
- Pas de SEO classique (backlinks, PageRank)
- Critères propres aux IA : cohérence sémantique, signaux de crédibilité, structuration de l'information

### 1.2 Problématique

Les entreprises ne savent pas :
1. Si elles sont visibles dans les réponses IA
2. Pourquoi certains concurrents sont recommandés à leur place
3. Comment optimiser leur présence pour les IA

**Conséquence** : Elles risquent de perdre des clients qui utilisent les IA pour trouver des prestataires.

### 1.3 Opportunité

Créer un service d'audit automatisé permettant de :
- Mesurer objectivement la visibilité IA
- Identifier les écarts avec la concurrence
- Fournir des solutions actionnables

---

## 2. Objectifs du MVP

### 2.1 Scope MVP (Phase 1)

**Périmètre** :
- **1 seule IA** : ChatGPT (API OpenAI)
- **1 secteur test** : Restauration
- **1 langue** : Français
- **1 zone géographique** : Paris (extensible)

**Durée estimée** : 2-3 jours de développement

### 2.2 Objectifs mesurables

| Objectif | Critère de succès |
|---|---|
| Audit automatisé | Interroger ChatGPT avec 5-10 requêtes pertinentes par entreprise |
| Analyse comparative | Identifier 3-5 concurrents cités par ChatGPT |
| Diagnostic | Identifier 3 causes principales d'absence/faible visibilité |
| Interface fonctionnelle | Formulaire + résultats affichés en < 2 minutes |
| Coût par audit | < 0.50 EUR (appels API OpenAI) |

---

## 3. Fonctionnalités détaillées

### 3.1 F01 : Paramétrage audit

**Description** : Interface permettant de configurer l'audit.

**Champs requis** :
- Nom de l'entreprise (texte, 100 chars max)
- Secteur d'activité (liste déroulante prédéfinie)
- Zone géographique (texte ou sélection ville)
- Langue (FR par défaut, extensible)

**Champs optionnels** :
- Site web (URL, pour extraction automatique de contexte)
- Description courte (200 chars, sinon scraping site)

**Sortie** :
- Objet `AuditSession` créé en base de données
- ID d'audit généré (ex: `audit_20260211_001`)

### 3.2 F02 : Génération requêtes métier

**Description** : Génération automatique de requêtes pertinentes selon le secteur.

**Template secteur "Restauration"** :
```
- "Meilleur restaurant {type_cuisine} à {ville}"
- "Restaurant {type_cuisine} près de {quartier}"
- "Où manger {type_cuisine} à {ville} ?"
- "Restaurant {type_cuisine} recommandé à {ville}"
- "Bon restaurant {type_cuisine} {ville}"
```

**Variables dynamiques** :
- `{type_cuisine}` : français, italien, japonais, etc. (selon contexte entreprise)
- `{ville}` : Paris, Lyon, etc.
- `{quartier}` : Marais, Montmartre, etc. (si précisé)

**Sortie** :
- Liste de 5-10 requêtes générées
- Stockées dans `AuditSession.queries[]`

### 3.3 F03 : Interrogation ChatGPT

**Description** : Appels API OpenAI pour chaque requête générée.

**Paramètres API** :
- Modèle : `gpt-4o-mini` (compromis coût/qualité)
- Température : 0.7 (cohérence avec variation)
- Max tokens : 500 par réponse
- System prompt : "Tu es un assistant de recommandation. Réponds de manière concise et factuelle."

**Gestion erreurs** :
- Retry automatique (max 3 tentatives si rate limit)
- Timeout : 30s par requête
- Fallback : marquer requête comme "échec" si 3 échecs

**Sortie** :
- Réponses ChatGPT stockées dans `AuditSession.results[]`
- Timestamp, tokens utilisés, coût estimé

### 3.4 F04 : Extraction mentions

**Description** : Parser les réponses pour extraire les entreprises mentionnées.

**Méthode d'extraction** :
- Recherche du nom de l'entreprise cible (exact match + variations)
- Extraction noms d'entreprises concurrentes (patterns : "Restaurant X", "Chez Y", etc.)
- Position relative (1er cité, 2e cité, pas cité)

**Indicateurs calculés** :
- **Taux de mention** : % de requêtes où l'entreprise est citée
- **Position moyenne** : rang moyen quand citée (1er, 2e, 3e, etc.)
- **Concurrents identifiés** : liste des autres entreprises citées
- **Fréquence concurrents** : combien de fois chaque concurrent est cité

**Sortie** :
- Objet `CompetitorAnalysis` avec métriques détaillées

### 3.5 F05 : Diagnostic automatisé

**Description** : Identifier les causes probables d'absence ou faible visibilité.

**Causes possibles** :
1. **Manque de présence en ligne** : pas de site web, pas de profil Google, etc.
2. **Informations incohérentes** : nom différent sur différents supports
3. **Absence de signaux d'autorité** : pas d'avis clients, pas de presse, etc.
4. **Manque de contexte sectoriel** : description trop vague, mots-clés absents
5. **Zone géographique mal définie** : adresse imprécise, quartier non mentionné

**Méthode de diagnostic** :
- Règles heuristiques basées sur patterns observés
- Score de confiance pour chaque cause (0-100%)
- Priorisation des causes (top 3)

**Sortie** :
- Liste de 3 causes principales avec recommandations

### 3.6 F06 : Affichage résultats

**Description** : Interface web affichant les résultats de l'audit.

**Sections affichées** :
1. **Score global** : 0-100 (basé sur taux mention + position)
2. **Visibilité par requête** : tableau (requête, cité oui/non, position, concurrents)
3. **Concurrents principaux** : top 5 avec fréquence
4. **Diagnostic** : 3 causes + recommandations
5. **Coût audit** : montant en EUR (transparence)

**Actions possibles** :
- Télécharger rapport (JSON pour l'instant)
- Relancer audit (button "Refaire")
- Partager résultats (copier lien, pour plus tard)

---

## 4. Architecture technique

### 4.1 Stack validée

| Couche | Technologie | Justification |
|---|---|---|
| **Backend** | Python 3.12+ | Conforme projets EURKAI, ecosystem ML riche |
| **Framework web** | Flask ou FastAPI | Flask = simple, FastAPI = async + validation Pydantic |
| **Base de données** | PostgreSQL 15+ | Relationnel robuste, JSON support |
| **Cache** | Redis 7+ | Cache résultats, rate limiting |
| **Frontend** | HTML/CSS/JS vanilla | Simplicité MVP, pas de framework lourd |

**Recommandation** : FastAPI pour MVP (validation auto, docs auto, async ready).

### 4.2 Architecture de base

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   FastAPI       │
│  (server.py)    │
├─────────────────┤
│ Routes:         │
│ POST /audit     │
│ GET /results/:id│
└────────┬────────┘
         │
    ┌────┴─────┬──────────┐
    ↓          ↓          ↓
┌─────────┐ ┌──────┐ ┌────────┐
│PostgreSQL│ │Redis │ │OpenAI  │
│ (audits) │ │(cache│ │  API   │
└──────────┘ └──────┘ └────────┘
```

### 4.3 Base de données

**Tables principales** :

```sql
-- Audits (sessions d'audit)
CREATE TABLE audits (
    id SERIAL PRIMARY KEY,
    audit_id VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    website VARCHAR(500),
    description TEXT,
    queries JSONB NOT NULL,
    results JSONB NOT NULL,
    metrics JSONB NOT NULL,
    cost_eur DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Competitors (concurrents identifiés)
CREATE TABLE competitors (
    id SERIAL PRIMARY KEY,
    audit_id VARCHAR(50) REFERENCES audits(audit_id),
    competitor_name VARCHAR(200) NOT NULL,
    mention_count INT NOT NULL,
    avg_position DECIMAL(3,1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Diagnoses (diagnostics générés)
CREATE TABLE diagnoses (
    id SERIAL PRIMARY KEY,
    audit_id VARCHAR(50) REFERENCES audits(audit_id),
    cause VARCHAR(200) NOT NULL,
    confidence INT CHECK (confidence BETWEEN 0 AND 100),
    recommendation TEXT NOT NULL,
    priority INT CHECK (priority BETWEEN 1 AND 3),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.4 Endpoints API

| Endpoint | Méthode | Description | Body / Params |
|---|---|---|---|
| `/api/audit` | POST | Lancer un audit | `{company, sector, location, website?, description?}` |
| `/api/audit/:id` | GET | Récupérer résultats | `:id` = audit_id |
| `/api/stats` | GET | Statistiques globales | - |

---

## 5. Conformité EURKAI

### 5.1 Objets EURKAI identifiés

**Objets métier** :
- `AuditSession` (extends `domain.service.Audit`)
- `AIProvider` (extends `interface.adapter.APIAdapter`)
- `CompetitorAnalysis` (extends `domain.service.Analysis`)
- `Diagnosis` (extends `domain.product.Deliverable`)

**Objets système** :
- `SectorTemplate` (extends `config.template.Template`)

**Objets flow** :
- `AuditProcess` (extends `flow.process.Process`)

### 5.2 Modules réutilisables

Modules EURKAI potentiels à créer :
- **Module API_AGGREGATOR** : orchestration multi-API IA (extensible Phase 2)
- **Module SEMANTIC_ANALYZER** : analyse cohérence sémantique
- **Module COMPETITOR_TRACKER** : suivi concurrence

Ces modules seront créés **si réutilisables** dans d'autres projets EURKAI.

### 5.3 Architecture fractale

```
ORCHESTRATOR (AuditOrchestrator)
  ├─ AGENT_QUERY (génère requêtes)
  ├─ AGENT_FETCH (appelle ChatGPT)
  ├─ AGENT_ANALYZE (extrait mentions)
  ├─ AGENT_DIAGNOSE (identifie causes)
  └─ VALIDATOR (conformité résultats)
```

---

## 6. Contraintes et limites MVP

### 6.1 Contraintes techniques

| Contrainte | Impact | Mitigation |
|---|---|---|
| Rate limiting OpenAI | Max 10 000 req/min (tier 1) | Cache + queue si volume élevé |
| Coût API | ~0.30-0.50 EUR par audit | Limiter à 10 requêtes/audit MVP |
| Parsing imprécis | Faux positifs/négatifs | Validation manuelle premiers audits |
| Variabilité IA | Réponses différentes même query | Moyenne sur 2-3 runs (Phase 2) |

### 6.2 Limites MVP

**Ce que le MVP NE fait PAS** :
- ❌ Multi-IA (seulement ChatGPT)
- ❌ Multi-secteurs (seulement restauration)
- ❌ Multi-langues (seulement FR)
- ❌ Génération solutions automatiques (diagnostic uniquement)
- ❌ Suivi historique évolution
- ❌ Authentification utilisateurs
- ❌ Paiement intégré

**Ces fonctionnalités seront ajoutées en Phase 2+**.

---

## 7. Critères de validation MVP

### 7.1 Critères fonctionnels

- [ ] Formulaire paramétrage fonctionnel (5 champs)
- [ ] Génération automatique de 5-10 requêtes pertinentes
- [ ] Appels ChatGPT réussis (> 90% de succès)
- [ ] Extraction mentions avec précision > 80%
- [ ] Affichage résultats complet en < 2 minutes
- [ ] Diagnostic avec 3 causes + recommandations

### 7.2 Critères techniques

- [ ] Code conforme standards EURKAI (objets, héritage)
- [ ] Base de données PostgreSQL opérationnelle
- [ ] Tests unitaires (coverage > 70%)
- [ ] Documentation API (FastAPI auto-docs)
- [ ] Logs structurés (debug, info, error)

### 7.3 Critères business

- [ ] Coût audit < 0.50 EUR
- [ ] Temps audit < 2 minutes
- [ ] Résultats actionnables (3 recommandations claires)
- [ ] Potentiel d'upsell identifié (Phase 2+)

---

## 8. Risques et dépendances

### 8.1 Risques techniques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Rate limiting OpenAI | Moyenne | Moyen | Cache + retry logic |
| Parsing imprécis | Haute | Moyen | Validation manuelle + amélioration itérative |
| Changement API OpenAI | Faible | Fort | Abstraction adapter, monitoring |
| Variabilité réponses IA | Haute | Faible | Moyenne sur runs multiples (Phase 2) |

### 8.2 Dépendances externes

- **OpenAI API** : service critique, pas de fallback MVP
- **PostgreSQL** : local OK, production nécessitera hébergement
- **Redis** : optionnel MVP, recommandé production

---

## 9. Planning et jalons

### 9.1 Découpage tâches MVP

| Tâche | Durée | Dépendances |
|---|---|---|
| Setup environnement (venv, deps) | 0.5h | - |
| Setup DB PostgreSQL + tables | 0.5h | - |
| Endpoint POST /api/audit | 1h | Setup DB |
| Génération requêtes secteur | 1h | - |
| Intégration OpenAI API | 1.5h | - |
| Extraction mentions | 2h | Intégration OpenAI |
| Diagnostic automatisé | 1.5h | Extraction mentions |
| Endpoint GET /api/audit/:id | 0.5h | - |
| Frontend formulaire | 1h | - |
| Frontend affichage résultats | 1.5h | - |
| Tests unitaires | 1.5h | Tous endpoints |
| Documentation | 0.5h | - |

**Total estimé** : 13h (soit ~2 jours effectifs)

### 9.2 Jalons

1. **J0 (maintenant)** : CDC validé ✓
2. **J0+1h** : SPECS générées, objets EURKAI validés
3. **J0+4h** : Backend fonctionnel (API + DB)
4. **J0+6h** : Frontend basique
5. **J1** : MVP complet fonctionnel
6. **J2** : Tests + validation + déploiement local

---

## 10. Évolutions futures (post-MVP)

### Phase 2 : Multi-IA (1 semaine)
- Intégration Claude, Gemini, Perplexity
- Comparaison inter-IA
- Score agrégé

### Phase 3 : Solutions automatisées (2 semaines)
- Génération contenus optimisés
- Données structurées (JSON-LD)
- Export livrables (PDF professionnel)

### Phase 4 : Internationalisation (1 semaine)
- Multi-langues (EN, ES, DE)
- Multi-géo (adaptation locale)

### Phase 5 : Scalabilité (1 semaine)
- Queue jobs (Celery + Redis)
- Dashboard admin
- Suivi historique

---

## 11. Validation et signatures

**Statut CDC** : 🟡 En attente validation Nathalie

**Prochaine étape** : Génération SPECS (architecture détaillée, objets EURKAI, code)

**À valider** :
- [ ] Fonctionnalités décrites OK ?
- [ ] Architecture technique validée ?
- [ ] Critères de succès MVP réalistes ?
- [ ] Planning 2-3 jours faisable ?
- [ ] Précisions ou ajustements nécessaires ?
