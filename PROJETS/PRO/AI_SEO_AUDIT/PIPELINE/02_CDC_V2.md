# CDC — AI_SEO_AUDIT (V2 Ajusté)

> Outil de prospection commercial — Audit visibilité IA + Génération solutions + Guide mise en œuvre

**Date** : 2026-02-11
**Version** : V2 (ajusté selon feedback Nathalie)
**Statut** : 🟡 En validation

---

## 1. Positionnement et modèle économique

### 1.1 Positionnement

**AI_SEO_AUDIT n'est PAS un simple outil d'audit.**

C'est un **outil de prospection commercial automatisé** :
- **Attrape-client** : Audit gratuit/freemium (montre le problème)
- **Démonstration de valeur** : Solutions générées automatiquement (prouve qu'on sait résoudre)
- **Vente standardisée** : Package livrable à télécharger (client autonome)

### 1.2 Modèle économique

**Principe** : Automatisation totale + Scalabilité maximale

| Niveau | Offre | Prix indicatif | Contenu |
|---|---|---|---|
| **Freemium** | Audit limité | Gratuit | 3 requêtes, 1 IA, diagnostic basique |
| **Starter** | Audit complet | 49€ | 10 requêtes, 1 IA, solutions + guide |
| **Pro** | Multi-IA + Solutions | 149€ | 20 requêtes, 4 IA, solutions détaillées + maquettes |
| **Enterprise** | Audit étendu + Suivi | 299€/mois | Audit mensuel, évolution, solutions actualisées |

**Contraintes** :
- ❌ Pas d'offre individuelle (tout standardisé)
- ✅ Client se débrouille (guide détaillé fourni)
- ✅ Coût marginal faible (~0.50-2€ par audit selon niveau)
- ✅ Scalable internationalement

### 1.3 Stratégie de lancement

**Phase 1 : MVP Light (2-3 jours)**
- Version allégée pour tester le marché
- Freemium + Starter uniquement
- 1 IA (ChatGPT), 1 secteur (restauration)
- Landing page basique
- Pricing simple

**Phase 2 : Version solide (enchainement immédiat, 1-2 semaines)**
- Multi-IA (ChatGPT, Claude, Gemini, Perplexity)
- Multi-secteurs (templates)
- Solutions avancées + maquettes
- Landing page optimisée
- Pricing complet (4 niveaux)
- Multilingue (FR, EN, ES, DE, IT)

---

## 2. Objectifs du MVP Light

### 2.1 Scope MVP

**Périmètre réduit** :
- **1 seule IA** : ChatGPT (API OpenAI)
- **1 secteur test** : Restauration (extensible facilement)
- **1 langue** : Français (détection auto + redirection préparée)
- **2 offres** : Freemium (gratuit) + Starter (49€)
- **Landing page** : Simple, claire, convertissante
- **Solutions** : Light mais concrètes (exemples + guide)

**Durée estimée** : 2-3 jours de développement

### 2.2 Objectifs mesurables

| Objectif | Critère de succès MVP |
|---|---|
| Acquisition | 10 audits gratuits dans les 7 premiers jours |
| Conversion | 20% freemium → payant (2/10) |
| Temps audit | < 2 minutes |
| Coût marginal | < 0.50 EUR par audit gratuit |
| Satisfaction | Solutions jugées actionnables (feedback qualitatif) |

---

## 3. Fonctionnalités détaillées

### 3.1 F01 : Paramétrage audit

**Description** : Landing page + formulaire audit.

**Écran landing** :
- Titre accrocheur : *"Votre entreprise est-elle invisible pour ChatGPT ?"*
- Sous-titre : *"Découvrez gratuitement comment l'IA recommande vos concurrents à votre place"*
- CTA : *"Audit gratuit en 2 minutes"*
- Bénéfices :
  - ✓ Audit immédiat (< 2 min)
  - ✓ Comparaison avec vos concurrents
  - ✓ Solutions concrètes pour améliorer votre visibilité

**Formulaire** :
- Nom de l'entreprise (texte, 100 chars max)
- Secteur d'activité (liste déroulante : Restauration pour MVP)
- Ville (autocomplete sur villes FR)
- Email (pour recevoir résultats + relance commerciale)
- Site web (optionnel, pour scraping contexte)

**Sortie** :
- Objet `AuditSession` créé
- Email de confirmation envoyé
- Redirection vers page "Analyse en cours..." (progression bar animée)

---

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
- `{type_cuisine}` : détecté depuis site web ou description
- `{ville}` : fourni par formulaire
- `{quartier}` : extrait de l'adresse si fournie

**Nombre de requêtes** :
- Freemium : 3 requêtes
- Starter : 10 requêtes
- Pro : 20 requêtes

**Sortie** : Liste de requêtes stockées dans `AuditSession.queries[]`

---

### 3.3 F03 : Interrogation ChatGPT

**Description** : Appels API OpenAI pour chaque requête générée.

**Paramètres API** :
- Modèle : `gpt-4o-mini` (coût/qualité optimal)
- Température : 0.7 (cohérence + variation naturelle)
- Max tokens : 500 par réponse
- System prompt : *"Tu es un assistant de recommandation locale. Réponds de manière concise et factuelle. Si tu recommandes des restaurants, cite 3-5 établissements avec leurs points forts."*

**Gestion erreurs** :
- Retry automatique (max 3 tentatives si rate limit)
- Timeout : 30s par requête
- Fallback : marquer requête comme "échec" et continuer

**Sortie** : Réponses ChatGPT stockées dans `AuditSession.results[]`

---

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

**Sortie** : Objet `CompetitorAnalysis` avec métriques détaillées

---

### 3.5 F05 : Diagnostic automatisé

**Description** : Identifier les causes probables d'absence ou faible visibilité.

**Causes possibles** :
1. **Manque de présence en ligne** (pas de site, pas de profil Google)
2. **Informations incohérentes** (nom différent sur différents supports)
3. **Absence de signaux d'autorité** (pas d'avis clients, pas de presse)
4. **Manque de contexte sectoriel** (description vague, mots-clés absents)
5. **Zone géographique mal définie** (adresse imprécise)

**Méthode de diagnostic** :
- Règles heuristiques basées sur patterns observés
- Score de confiance pour chaque cause (0-100%)
- Priorisation des causes (top 3)

**Sortie** : Liste de 3 causes principales avec recommandations

---

### 3.6 F06 : Affichage résultats audit

**Description** : Interface web affichant les résultats de l'audit.

**Sections affichées** :

1. **Score global** (0-100)
   - Visuel : jauge colorée (rouge < 30, orange 30-60, vert > 60)
   - Message contextuel selon score

2. **Visibilité par requête**
   - Tableau : requête, cité oui/non, position, concurrents cités
   - Highlight : entreprise cliente vs concurrents

3. **Concurrents principaux**
   - Top 5 avec fréquence de citation
   - Graphique barres comparatives

4. **Diagnostic**
   - 3 causes principales avec icônes
   - Explication courte pour chaque cause

5. **CTA selon offre**
   - Freemium : *"Obtenez vos solutions personnalisées pour 49€"* → Upgrade Starter
   - Starter : Solutions affichées + *"Passez au Pro pour multi-IA et maquettes"*

---

### 3.7 F07 : Génération de solutions (NOUVEAU)

**Description** : Générer des solutions CONCRÈTES et PRÉCISES avec maquettes/exemples.

**Contenu généré** :

#### A. Contenus optimisés IA-first

**Exemple concret fourni** :

```markdown
### Description optimisée pour votre site

**AVANT** (actuel, si détecté) :
"Restaurant français traditionnel à Paris"

**APRÈS** (optimisé IA) :
"Restaurant français gastronomique au cœur du Marais (Paris 3e).
Spécialités : bœuf bourguignon maison, coq au vin, tarte tatin.
Chef étoilé Michelin 2019-2023. 120 avis Google 4.8/5.
Réservations recommandées."

**Pourquoi c'est mieux** :
✓ Localisation précise (quartier + arrondissement)
✓ Spécialités concrètes (mots-clés pertinents)
✓ Signaux d'autorité (étoile Michelin, avis Google)
✓ Action claire (réservations)
```

**Maquette fournie** :
- Capture d'écran annotée de comment ça s'affichera sur le site
- Snippet HTML prêt à copier-coller

#### B. Données structurées (JSON-LD)

**Exemple concret fourni** :

```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "Nom du restaurant",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Rue Example",
    "addressLocality": "Paris",
    "postalCode": "75003",
    "addressCountry": "FR"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "48.8606",
    "longitude": "2.3522"
  },
  "servesCuisine": "French",
  "priceRange": "€€",
  "telephone": "+33123456789",
  "url": "https://example.com",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "120"
  }
}
```

**Instructions** : *"Copiez ce code et collez-le dans la section `<head>` de votre site web, entre des balises `<script type="application/ld+json">`"*

**Maquette fournie** :
- Capture d'écran de où coller le code dans WordPress, Wix, ou code HTML brut

#### C. Recommandations éditoriales

**Format** : Liste à puces concrète et actionnable

Exemple :
```
✅ Ajoutez une page "Menus" avec vos plats signature
✅ Créez un profil Google My Business (lien direct fourni)
✅ Demandez à 10 clients satisfaits de laisser un avis Google
✅ Publiez 1 article de blog par mois sur vos spécialités
✅ Ajoutez vos horaires et coordonnées sur toutes vos pages
```

#### D. Exemples de résultats attendus

**Maquette "Avant/Après"** :

- **AVANT** : Capture d'écran simulée de la réponse ChatGPT actuelle (entreprise absente)
- **APRÈS** : Capture d'écran simulée de la réponse ChatGPT idéale (entreprise citée en 1er)

**Texte** :
*"Voici ce que ChatGPT pourrait répondre après application de nos recommandations..."*

---

### 3.8 F08 : Guide de mise en œuvre (NOUVEAU)

**Description** : Guide PDF téléchargeable pour mise en œuvre autonome.

**Structure du guide** (8-12 pages) :

#### Page 1 : Sommaire
- Checklist rapide (3 min de lecture)
- Étapes détaillées (30 min de lecture)

#### Page 2-3 : Optimisation description
- Texte exact à copier
- Où le coller (screenshots annotés pour 5 plateformes : site web, Google My Business, Facebook, LinkedIn, Pages Jaunes)
- Validation (comment vérifier que c'est bien en place)

#### Page 4-5 : Données structurées JSON-LD
- Code exact à copier
- Tutoriel étape par étape :
  - WordPress (plugin Yoast SEO)
  - Wix (Custom Code)
  - Shopify (Theme liquid files)
  - HTML brut (balise `<script>`)
- Test de validation (Google Rich Results Test, lien direct)

#### Page 6-7 : Profil Google My Business
- Lien création profil : https://business.google.com
- Checklist complète :
  - ☐ Nom exact
  - ☐ Adresse complète
  - ☐ Téléphone
  - ☐ Horaires
  - ☐ Photos (min 10, checklist types de photos)
  - ☐ Description optimisée (texte fourni)
  - ☐ Catégorie principale + secondaires
  - ☐ Attributs (ex: "Réservation en ligne", "Wi-Fi gratuit")

#### Page 8-9 : Stratégie avis clients
- Pourquoi c'est important (impact IA)
- Comment demander (email template fourni)
- Quoi répondre (templates de réponses aux avis positifs/négatifs)

#### Page 10 : Vérification et suivi
- Checklist de contrôle (15 points à cocher)
- Timeline recommandée (J+1, J+7, J+30)
- Comment relancer un audit (lien direct vers formulaire)

#### Page 11-12 : FAQ + Support
- 10 questions fréquentes
- Lien vers support (si upgrade Pro/Enterprise)
- Upsell discret : *"Besoin d'aide ? Passez au niveau Pro pour un suivi personnalisé"*

**Format livrable** :
- PDF professionnel (branding AI_SEO_AUDIT)
- Téléchargement immédiat après paiement
- Envoi par email (backup)

---

### 3.9 F09 : Landing page + Pricing (NOUVEAU)

**Description** : Page d'accueil convertissante + page pricing multilingue.

#### A. Landing page

**Structure** :

1. **Hero section**
   - Titre : *"Votre entreprise est-elle invisible pour ChatGPT ?"*
   - Sous-titre : *"Des millions d'utilisateurs demandent des recommandations aux IA. Si vous n'apparaissez pas, vos concurrents prennent votre place."*
   - CTA primaire : *"Audit gratuit (2 min)"*
   - Preuve sociale : *"Déjà 127 entreprises auditées"* (compteur dynamique)

2. **Le problème** (section 2)
   - Capture d'écran réelle de ChatGPT recommandant des concurrents
   - Texte : *"Votre concurrent apparaît, mais pas vous. Pourquoi ?"*

3. **La solution** (section 3)
   - 3 blocs :
     - 🔍 Audit complet (visibilité actuelle)
     - 💡 Solutions concrètes (que faire)
     - 📄 Guide pratique (comment faire)

4. **Comment ça marche** (section 4)
   - 3 étapes visuelles :
     1. Formulaire (30 sec)
     2. Analyse automatique (2 min)
     3. Résultats + solutions (téléchargement immédiat)

5. **Pricing** (section 5)
   - Tableau comparatif 3 offres (Freemium, Starter, Pro)
   - Highlight sur Starter (offre phare)

6. **Témoignages** (section 6)
   - 3 témoignages fictifs mais réalistes (à remplacer par vrais après MVP)

7. **FAQ** (section 7)
   - 6 questions fréquentes

8. **Footer CTA**
   - *"Commencez votre audit gratuit maintenant"*
   - Formulaire direct dans la page

#### B. Pricing multilingue

**Gestion langues** :
- Détection automatique langue navigateur (`navigator.language`)
- Redirection : `.com?l=fr`, `.com?l=en`, `.com?l=es`, etc.
- Pas de sélecteur visible (transparent pour l'utilisateur)
- Langues MVP : FR uniquement
- Langues Phase 2 : EN, ES, DE, IT

**Tableau pricing** :

| | Freemium | Starter | Pro |
|---|---|---|---|
| **Prix** | Gratuit | 49€ | 149€ |
| **Requêtes** | 3 | 10 | 20 |
| **IA** | 1 (ChatGPT) | 1 (ChatGPT) | 4 (All) |
| **Diagnostic** | ✓ Basique | ✓ Détaillé | ✓✓ Avancé |
| **Solutions** | ✗ | ✓ Concrètes | ✓✓ + Maquettes |
| **Guide PDF** | ✗ | ✓ Standard | ✓✓ Premium |
| **Support** | ✗ | Email | Prioritaire |
| **CTA** | *Commencer* | *Acheter* | *Acheter* |

**Paiement** :
- Stripe (cartes bancaires internationales)
- PayPal (backup)
- Confirmation immédiate par email + lien téléchargement

---

## 4. Architecture technique

### 4.1 Stack validée

| Couche | Technologie | Justification |
|---|---|---|
| **Backend** | Python 3.12+ | Conforme EURKAI, ML ecosystem |
| **Framework web** | FastAPI | Async, validation Pydantic, docs auto |
| **Base de données** | PostgreSQL 15+ | Relationnel robuste, JSON support |
| **Cache** | Redis 7+ | Cache résultats, rate limiting |
| **Frontend** | HTML/CSS/JS vanilla | Simplicité MVP, pas de framework lourd |
| **Paiement** | Stripe | Standard industrie, intégration simple |
| **Email** | SendGrid ou Brevo | Transactionnel + marketing |
| **Génération PDF** | WeasyPrint | Python native, HTML→PDF |

### 4.2 Architecture de base

```
┌─────────────────┐
│  Landing Page   │
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
│ POST /payment   │
│ GET /download   │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬─────────┬────────┐
    ↓          ↓          ↓         ↓        ↓
┌────────┐ ┌──────┐ ┌────────┐ ┌──────┐ ┌──────┐
│Postgres│ │Redis │ │OpenAI  │ │Stripe│ │Brevo │
│(audits)│ │(cache│ │  API   │ │(pay) │ │(mail)│
└────────┘ └──────┘ └────────┘ └──────┘ └──────┘
```

### 4.3 Base de données

**Tables principales** :

```sql
-- Audits (sessions d'audit)
CREATE TABLE audits (
    id SERIAL PRIMARY KEY,
    audit_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(200) NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    website VARCHAR(500),
    plan VARCHAR(20) NOT NULL, -- 'freemium', 'starter', 'pro'
    queries JSONB NOT NULL,
    results JSONB NOT NULL,
    metrics JSONB NOT NULL,
    solutions JSONB, -- null pour freemium
    cost_eur DECIMAL(10,4),
    paid BOOLEAN DEFAULT FALSE,
    payment_id VARCHAR(100),
    guide_downloaded BOOLEAN DEFAULT FALSE,
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

-- Payments (paiements Stripe)
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(100) UNIQUE NOT NULL,
    audit_id VARCHAR(50) REFERENCES audits(audit_id),
    amount_eur DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'pending', 'succeeded', 'failed'
    stripe_session_id VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.4 Endpoints API

| Endpoint | Méthode | Description | Body / Params |
|---|---|---|---|
| `/` | GET | Landing page | - |
| `/pricing` | GET | Page pricing | - |
| `/api/audit` | POST | Lancer un audit | `{email, company, sector, location, website?, plan}` |
| `/api/audit/:id` | GET | Récupérer résultats | `:id` = audit_id |
| `/api/payment/create` | POST | Créer session Stripe | `{audit_id, plan}` |
| `/api/payment/success` | GET | Callback Stripe succès | `?session_id=xxx` |
| `/api/download/:id` | GET | Télécharger guide PDF | `:id` = audit_id (si payé) |
| `/api/stats` | GET | Statistiques globales | - (admin) |

---

## 5. Conformité EURKAI

### 5.1 Objets EURKAI identifiés

**Objets métier** :
- `AuditSession` (extends `domain.service.Audit`)
- `AIProvider` (extends `interface.adapter.APIAdapter`)
- `CompetitorAnalysis` (extends `domain.service.Analysis`)
- `Diagnosis` (extends `domain.product.Deliverable`)
- `Solution` (extends `domain.product.Deliverable`) — NOUVEAU
- `Guide` (extends `domain.product.Document`) — NOUVEAU

**Objets système** :
- `SectorTemplate` (extends `config.template.Template`)
- `PricingPlan` (extends `config.pricing.Plan`) — NOUVEAU

**Objets flow** :
- `AuditProcess` (extends `flow.process.Process`)
- `PaymentProcess` (extends `flow.process.Process`) — NOUVEAU

### 5.2 Modules réutilisables

Modules EURKAI potentiels à créer :
- **Module API_AGGREGATOR** : orchestration multi-API IA (extensible Phase 2)
- **Module SEMANTIC_ANALYZER** : analyse cohérence sémantique
- **Module COMPETITOR_TRACKER** : suivi concurrence
- **Module CONTENT_GENERATOR** : génération contenus optimisés IA — NOUVEAU
- **Module PDF_GENERATOR** : génération guides PDF — NOUVEAU
- **Module PAYMENT_PROCESSOR** : intégration Stripe réutilisable — NOUVEAU

### 5.3 Architecture fractale

```
ORCHESTRATOR (AuditOrchestrator)
  ├─ AGENT_QUERY (génère requêtes)
  ├─ AGENT_FETCH (appelle ChatGPT)
  ├─ AGENT_ANALYZE (extrait mentions)
  ├─ AGENT_DIAGNOSE (identifie causes)
  ├─ AGENT_SOLVE (génère solutions) — NOUVEAU
  ├─ AGENT_GUIDE (génère PDF) — NOUVEAU
  └─ VALIDATOR (conformité résultats)
```

---

## 6. Contraintes et limites MVP Light

### 6.1 Contraintes techniques

| Contrainte | Impact | Mitigation |
|---|---|---|
| Rate limiting OpenAI | Max 10 000 req/min | Cache agressif + queue |
| Coût API | ~0.30-0.50 EUR/audit | Limiter requêtes freemium (3) |
| Génération PDF | ~2-3 sec par guide | Async + cache templates |
| Paiement Stripe | Frais 1.5% + 0.25€ | Intégré dans pricing |

### 6.2 Limites MVP Light

**Ce que le MVP NE fait PAS** :
- ❌ Multi-IA (seulement ChatGPT) → Phase 2
- ❌ Multi-secteurs (seulement restauration) → Phase 2
- ❌ Multi-langues (seulement FR) → Phase 2
- ❌ Maquettes visuelles avancées (exemples texte uniquement) → Phase 2
- ❌ Suivi historique évolution → Phase 2
- ❌ Authentification utilisateurs (audit = one-shot) → Phase 2
- ❌ Implémentation automatique (guide manuel uniquement) → Phase 2+

**Ces fonctionnalités seront ajoutées en Phase 2 (version solide)**.

---

## 7. Critères de validation MVP Light

### 7.1 Critères fonctionnels

- [ ] Landing page fonctionnelle et convertissante
- [ ] Formulaire audit opérationnel (3 plans)
- [ ] Génération automatique de 3-10 requêtes pertinentes
- [ ] Appels ChatGPT réussis (> 90% de succès)
- [ ] Extraction mentions avec précision > 75%
- [ ] Affichage résultats complet en < 2 minutes
- [ ] Diagnostic avec 3 causes + recommandations
- [ ] Génération solutions concrètes (contenus + JSON-LD + recommandations)
- [ ] Guide PDF téléchargeable (8-12 pages)
- [ ] Paiement Stripe fonctionnel (Starter 49€)

### 7.2 Critères techniques

- [ ] Code conforme standards EURKAI (objets, héritage)
- [ ] Base de données PostgreSQL opérationnelle
- [ ] Tests unitaires (coverage > 60% MVP)
- [ ] Documentation API (FastAPI auto-docs)
- [ ] Logs structurés (debug, info, error)
- [ ] Déploiement local opérationnel

### 7.3 Critères business

- [ ] Coût audit freemium < 0.50 EUR
- [ ] Temps audit < 2 minutes
- [ ] Conversion freemium→Starter > 10% (objectif 20%)
- [ ] Solutions jugées actionnables (feedback qualitatif)
- [ ] Guide PDF jugé utile (feedback qualitatif)

---

## 8. Planning et jalons MVP Light

### 8.1 Découpage tâches MVP Light

| Tâche | Durée | Dépendances |
|---|---|---|
| Setup environnement (venv, deps) | 0.5h | - |
| Setup DB PostgreSQL + tables | 0.5h | - |
| Landing page HTML/CSS | 2h | - |
| Formulaire audit (3 plans) | 1h | Landing page |
| Endpoint POST /api/audit | 1h | Setup DB |
| Génération requêtes secteur | 1h | - |
| Intégration OpenAI API | 1.5h | - |
| Extraction mentions | 2h | Intégration OpenAI |
| Diagnostic automatisé | 1.5h | Extraction mentions |
| **Génération solutions (F07)** | 3h | Diagnostic |
| **Génération guide PDF (F08)** | 2.5h | Génération solutions |
| Intégration Stripe | 2h | - |
| Endpoint GET /api/audit/:id | 0.5h | - |
| Endpoint POST /api/payment/create | 1h | Intégration Stripe |
| Endpoint GET /api/download/:id | 1h | Génération PDF |
| Page résultats | 2h | - |
| Tests unitaires | 2h | Tous endpoints |
| Documentation | 0.5h | - |

**Total estimé** : 24h (soit ~3 jours effectifs)

### 8.2 Jalons

1. **J0 (maintenant)** : CDC V2 validé ✓
2. **J0+2h** : SPECS générées, objets EURKAI validés
3. **J0+6h** : Backend API + DB opérationnel
4. **J0+10h** : Landing page + formulaire
5. **J1** : Génération solutions + guide PDF
6. **J2** : Intégration paiement + tests
7. **J2 fin** : Déploiement local + validation
8. **J3** : Mise en ligne (Vercel/Netlify) + premiers tests utilisateurs

---

## 9. Évolutions Phase 2 (version solide)

### 9.1 Multi-IA (1 semaine)
- Intégration Claude, Gemini, Perplexity
- Comparaison inter-IA (tableau de bord)
- Score agrégé (moyenne pondérée)
- Plan Pro opérationnel (4 IA)

### 9.2 Multi-secteurs (3 jours)
- Templates sectoriels : restauration, coaching, agence web, e-commerce, services B2B
- Requêtes spécifiques par secteur
- Exemples et maquettes adaptés

### 9.3 Solutions avancées (1 semaine)
- Maquettes visuelles (captures d'écran annotées)
- Exemples de pages optimisées (HTML complet)
- Contenus rédactionnels (articles de blog, posts réseaux sociaux)
- Stratégie éditoriale (planning 3 mois)

### 9.4 Internationalisation (1 semaine)
- Multi-langues : FR, EN, ES, DE, IT
- Détection automatique langue user
- Redirection .com?l=XX
- Traduction complète (landing, guide, emails)
- Adaptation culturelle (exemples locaux)

### 9.5 Scalabilité (1 semaine)
- Queue jobs (Celery + Redis) pour audits en arrière-plan
- Dashboard admin (stats, monitoring)
- Suivi historique (évolution score dans le temps)
- Plan Enterprise opérationnel (suivi mensuel)
- API publique (webhooks pour intégrations tierces)

---

## 10. Risques et dépendances

### 10.1 Risques techniques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Rate limiting OpenAI | Moyenne | Moyen | Cache + queue + retry |
| Parsing imprécis | Haute | Moyen | Validation manuelle premiers audits + amélioration itérative |
| Génération PDF lente | Faible | Faible | Async + cache templates |
| Fraude paiement | Faible | Moyen | Stripe Radar (détection fraude) |

### 10.2 Risques business

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Faible conversion freemium→payant | Moyenne | Fort | A/B testing pricing + amélioration solutions |
| Concurrence rapide | Moyenne | Moyen | Lancement rapide + fidélisation clients |
| Marché pas prêt | Faible | Fort | MVP test marché rapide, pivot si nécessaire |

### 10.3 Dépendances externes

- **OpenAI API** : service critique, pas de fallback MVP (Phase 2 multi-IA = fallback)
- **Stripe** : paiement critique, PayPal backup Phase 2
- **PostgreSQL** : local MVP, hébergement cloud Phase 2 (Heroku/AWS)
- **Redis** : optionnel MVP, recommandé production

---

## 11. Validation et prochaines étapes

**Statut CDC V2** : 🟡 En attente validation Nathalie

**Changements V1 → V2** :
- ✅ Positionnement : outil de prospection commercial (pas simple audit)
- ✅ F07 : Génération solutions concrètes avec exemples et maquettes
- ✅ F08 : Guide PDF mise en œuvre détaillé (8-12 pages)
- ✅ F09 : Landing page + pricing multilingue
- ✅ Modèle économique : 3 plans (freemium, starter, pro)
- ✅ Stratégie : MVP light test marché → enchainement immédiat version solide
- ✅ Principes : automatisation totale, scalabilité, pas d'offre individuelle

**Prochaine étape** : Génération SPECS (architecture détaillée, objets EURKAI, code)

**Questions pour validation** :
1. Le positionnement "outil de prospection" est-il clair ?
2. Les solutions générées (F07) sont-elles assez concrètes ?
3. Le guide PDF (F08) contient-il assez de détails ?
4. Le pricing (49€ Starter, 149€ Pro) te semble-t-il cohérent ?
5. La stratégie MVP light → version solide est-elle OK ?
6. Autres ajustements nécessaires ?
