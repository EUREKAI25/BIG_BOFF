# BRIEF — AI SEO AUDIT

> Service d'audit et d'optimisation de la visibilité des entreprises dans les réponses des intelligences artificielles

**Date** : 2026-02-11
**Source** : `chatgpt_ai_seo_.json`
**Statut** : 💡 brief initial — validation requise

---

## 1. Contexte

Les intelligences artificielles conversationnelles (ChatGPT, Claude, Gemini, Perplexity, etc.) deviennent des intermédiaires directs de recommandation pour les utilisateurs :

- "bon restaurant près de chez moi"
- "meilleur coach pour X"
- "agence web fiable"

**Différence fondamentale avec Google** :
- Pas de priorisation publicitaire (Google Ads)
- Pas de SEO classique (backlinks, PageRank)
- Critères propres : cohérence sémantique, structuration de l'information, signaux de crédibilité, récurrence contextuelle, sources exploitables

**Conséquence** :
Des entreprises habituées à payer pour leur visibilité (Google Ads, SEO) peuvent être absentes ou sous-représentées dans les réponses IA, tandis que des concurrents moins exposés financièrement y apparaissent naturellement.

**Opportunité** : nouveau marché de référencement IA, complémentaire mais distinct du SEO classique.

---

## 2. Problématique

Les entreprises :
1. Ne savent pas si elles sont visibles/recommandées par les IA
2. Ne comprennent pas pourquoi certains concurrents le sont
3. N'ont aucun outil standard pour mesurer, comparer et corriger cette visibilité

**Besoin identifié** :
- Audit de visibilité IA
- Optimisation des signaux interprétés par les modèles IA
- Structuration de contenus et données compatibles IA

---

## 3. Objectif du projet

Créer un système **standardisé, automatisable et internationalisable** permettant :

1. **Auditer** la visibilité d'une entreprise dans les réponses des IA
2. **Identifier** les écarts avec les concurrents
3. **Générer** des solutions prêtes à intégrer pour améliorer cette visibilité
4. **Adapter** le process par secteur d'activité, langue et zone géographique

**Caractéristiques** :
- Scalable
- Majoritairement automatisé
- Basé sur des templates sectoriels
- Exploitable sans expertise technique côté client

---

## 4. Proposition de valeur

**Message central** :
> "Aujourd'hui, vos clients ne cherchent plus seulement sur Google.
> Les IA décident déjà qui recommander à votre place.
> Êtes-vous dans leurs réponses ?"

**Arguments** :
- Offre basée sur un **constat mesurable** (audit automatisé)
- Comparaison directe avec concurrents visibles vs invisibles
- Accent sur le **retard invisible**, pas sur la technique
- Solution **prête à intégrer** (pas de refonte lourde)

---

## 5. Périmètre fonctionnel

### 5.1 Audit IA

**Actions** :
- Interrogation de plusieurs IA (ChatGPT, Claude, Gemini, Perplexity) sur des requêtes métiers pertinentes
- Analyse de :
  - Présence / absence
  - Positionnement relatif
  - Concurrents cités
  - Types d'arguments ou signaux utilisés par l'IA
- Restitution synthétique et comparable

### 5.2 Diagnostic

**Identification des causes** d'absence ou de faible visibilité :
- Manque de structuration de l'information
- Incohérences sémantiques
- Absence de signaux d'autorité exploitables
- Déficit de contextualisation sectorielle ou locale

### 5.3 Génération de solutions

**Livrables** :
- Contenus optimisés IA-first
- Données structurées (JSON-LD, Schema.org)
- Recommandations éditoriales et informationnelles
- Blocs directement intégrables (site, profils, contenus)

---

## 6. Architecture EURKAI

### 6.1 Objets identifiés (préliminaire)

**Objets métier** :
- `AuditSession` (extends `domain.service.Audit`)
  - Attributs : company, sector, location, language, queries[], results[]
  - Méthodes : execute(), analyze(), compare()

- `AIProvider` (extends `interface.adapter.APIAdapter`)
  - Attributs : name, api_endpoint, model, rate_limit
  - Méthodes : query(), parse_response()

- `CompetitorAnalysis` (extends `domain.service.Analysis`)
  - Attributs : target_company, competitors[], visibility_scores[]
  - Méthodes : identify_gaps(), rank_competitors()

- `OptimizationRecommendation` (extends `domain.product.Deliverable`)
  - Attributs : type, priority, content, integration_guide
  - Méthodes : generate(), validate(), export()

**Objets système** :
- `SectorTemplate` (extends `config.template.Template`)
  - Attributs : sector_id, queries_patterns[], signals_priorités[]
  - Méthodes : customize(), generate_queries()

**Objets flow** :
- `AuditProcess` (extends `flow.process.Process`)
  - Étapes : collect → analyze → diagnose → generate → deliver
  - Orchestration : ORCHESTRATOR → AGENTS (audit/analyze/generate) → VALIDATOR

### 6.2 Modules réutilisables (potentiels)

- **Module API_AGGREGATOR** : orchestration multi-API (ChatGPT, Claude, Gemini)
- **Module SEMANTIC_ANALYZER** : analyse cohérence sémantique
- **Module COMPETITOR_TRACKER** : suivi concurrence automatisé
- **Module CONTENT_GENERATOR** : génération contenus optimisés IA

### 6.3 Architecture fractale

```
ORCHESTRATOR (AuditOrchestrator)
  ├─ AGENT_AUDIT (collecte données multi-IA)
  ├─ AGENT_ANALYZE (diagnostic écarts)
  ├─ AGENT_GENERATE (solutions optimisées)
  └─ VALIDATOR (conformité MANIFEST)
```

Cette structure se répète à chaque étape (ex: AGENT_AUDIT → sous-orchestration par IA).

---

## 7. Front — Attentes

**Interface utilisateur** :
- Simple et guidée (pas de jargon SEO)
- Paramétrage minimal :
  - Nom entreprise
  - Secteur d'activité (liste prédéfinie)
  - Zone géographique
  - Langue
- Visualisation claire :
  - Score de visibilité IA (0-100)
  - Graphique comparatif avec concurrents
  - Liste des écarts identifiés
  - Recommandations priorisées

**Pages prévues** :
1. Onboarding / paramétrage
2. Dashboard résultats audit
3. Détail diagnostic (par IA)
4. Solutions proposées (téléchargeables)
5. Suivi historique (évolution dans le temps)

---

## 8. Back — Attentes

**Moteur d'audit IA multi-modèles** :
- Connexions API : ChatGPT, Claude, Gemini, Perplexity
- Rate limiting et gestion quotas
- Parallélisation des requêtes (optimisation temps)

**Orchestration automatisée** :
- Tests et analyses automatiques
- Génération dynamique :
  - Diagnostics
  - Recommandations
  - Livrables (HTML, JSON, PDF)

**Architecture modulaire** :
- Templates sectoriels (restauration, coaching, agence web, etc.)
- Adaptation linguistique (FR, EN, ES, DE)
- Internationalisation native (contexte culturel)

**Capacité à grande échelle** :
- Base de données relationnelle (PostgreSQL)
- Cache résultats (Redis)
- Queue jobs (audit en arrière-plan)
- Stockage S3 pour livrables

---

## 9. Logique économique

**Process reproductible** :
- Coût marginal faible par audit (~0.50-1€ en API calls)
- Prix moyen standardisé : 49-99€ par audit (secteur/étendue)
- Upsell naturel : solutions correctives + suivi mensuel

**Adaptation par secteur** :
- Templates pré-configurés
- Pas de refonte du système
- Scalabilité internationale immédiate

**Acquisition clients** :
- Audit massif automatisé (identifier prospects)
- Offre freemium : audit limité gratuit (1 IA, 3 requêtes)
- Conversion : audit complet + solutions

---

## 10. Internationalisation & Scalabilité

**Multi-langues** :
- FR, EN, ES, DE, IT (phase 1)
- Interface traduite (i18n)
- Queries adaptées par langue/culture
- Résultats localisés

**Multi-secteurs** :
- Templates sectoriels pré-créés :
  - Restauration
  - Coaching / Conseil
  - Agences (web, com, marketing)
  - E-commerce
  - Services B2B
- Extensible : nouveau secteur = nouveau template (pas de code)

**Multi-géo** :
- Contexte local intégré (ex: "près de Paris" vs "near London")
- Signaux d'autorité locaux (ex: avis Google My Business)

---

## 11. Standards & Contraintes EURKAI

**Conformité obligatoire** :
- [x] Tous les objets héritent d'`Object` (ident, created_at, version, parent, validate(), test())
- [x] Architecture fractale (orchestrateur → agents → validator)
- [x] Atome = function (une fonction fait UNE chose)
- [x] Method = import function (flexibilité, interchangeabilité)
- [x] Scenario = orchestration (ne fait rien lui-même)
- [x] Modules réutilisables extraits dans `EURKAI/MODULES/`

**Catalogue** :
- Enregistrer objets dans `catalogs/domain/service/` (AuditSession, Analysis)
- Enregistrer adapters dans `catalogs/interface/adapter/` (AIProvider)
- Instances dans `instances/domain/service/` (audits concrets)

---

## 12. Étapes de développement

### Phase 1 : MVP Mono-IA (2-3 jours)
- [x] Audit ChatGPT uniquement
- [x] 1 secteur test (restauration)
- [x] 1 langue (FR)
- [x] Interface basique (formulaire + résultats)
- [x] Backend : API ChatGPT + analyse simple

### Phase 2 : Multi-IA (1 semaine)
- [ ] Intégration Claude, Gemini, Perplexity
- [ ] Comparaison inter-IA (score agrégé)
- [ ] Templates sectoriels (3-5 secteurs)

### Phase 3 : Solutions automatisées (2 semaines)
- [ ] Génération contenus optimisés
- [ ] Données structurées (JSON-LD)
- [ ] Recommandations éditoriales
- [ ] Export livrables (PDF, JSON)

### Phase 4 : Internationalisation (1 semaine)
- [ ] Multi-langues (EN, ES, DE)
- [ ] Multi-géo (contexte local)
- [ ] Adaptation culturelle

### Phase 5 : Scalabilité (1 semaine)
- [ ] Queue jobs (audit en arrière-plan)
- [ ] Cache résultats
- [ ] Dashboard admin
- [ ] Suivi historique

---

## 13. Risques & Contraintes

**Technique** :
- Rate limiting API IA (gérer quotas, fallback)
- Variabilité réponses IA (même query → résultats différents)
- Coût API IA si volume élevé (prévoir cache agressif)

**Juridique** :
- Terms of Service des API IA (vérifier autorisations)
- Scraping vs API officielle (privilégier API)
- RGPD : données entreprises (minimiser stockage)

**Marché** :
- Éducation marché nécessaire (nouveau concept)
- Concurrence potentielle si succès (barrière à l'entrée faible)
- Évolution rapide IA (adaptation continue requise)

---

## 14. Finalité

Mettre en place une **nouvelle couche de référencement**, spécifique aux intelligences artificielles, complémentaire mais indépendante du SEO classique, reposant sur :
- Audits mesurables
- Corrections concrètes
- Industrialisation
- Internationalisation

**Vision long terme** : devenir le standard de facto pour l'optimisation de la visibilité IA, comme Moz/Ahrefs/SEMrush le sont pour le SEO classique.

---

## 15. Prochaines étapes

1. **Validation brief** par Nathalie
2. **Création projet structuré** : `PROJETS/PRO/AI_SEO_AUDIT/`
3. **CDC** (Cahier des Charges) : fonctionnalités détaillées
4. **SPECS** : architecture technique, objets EURKAI, API, stack
5. **BUILD** : MVP Phase 1 (mono-IA, 1 secteur)
6. **DEPLOY** : GitHub + environnement test
7. **Tests utilisateurs** : 5-10 entreprises pilotes
8. **Itération** : améliorations selon feedback

---

## Métadonnées

**Nom projet** : `AI_SEO_AUDIT`
**Emplacement prévu** : `/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/AI_SEO_AUDIT/`
**Stack envisagée** : Python (backend), Flask/FastAPI, PostgreSQL, Redis, HTML/CSS/JS (frontend)
**Modules EURKAI** : API_AGGREGATOR, SEMANTIC_ANALYZER, COMPETITOR_TRACKER, CONTENT_GENERATOR
**Agents EURKAI** : ORCHESTRATOR (AuditOrchestrator), AGENT_AUDIT, AGENT_ANALYZE, AGENT_GENERATE, VALIDATOR

**Durée estimée MVP** : 2-3 jours
**Durée estimée v1 complète** : 4-6 semaines
**Coût API estimé par audit** : 0.50-1.00€
**Prix de vente envisagé** : 49-99€ par audit complet
