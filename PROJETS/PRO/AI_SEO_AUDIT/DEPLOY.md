# 🚀 AI SEO Audit - Guide de Déploiement

## Quick Start Local

### 1. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec vos clés
# OPENAI_API_KEY=sk-...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
```

### 2. Démarrage Docker

```bash
# Démarrer tous les services
make docker-up

# Ou manuellement :
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### 3. Initialiser la base de données

```bash
# Créer les tables
make migrate

# Ou manuellement :
docker-compose exec api alembic upgrade head
```

### 4. Tester l'application

```bash
# Ouvrir dans le navigateur
open http://localhost:8000

# Tester l'API
curl http://localhost:8000/health

# Lancer les tests
make test
```

---

## Deploy Production

### Option 1 : Railway.app (Recommandé)

**1. Créer un compte sur [Railway.app](https://railway.app)**

**2. Installer Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

**3. Initialiser le projet**
```bash
railway init
railway link
```

**4. Ajouter PostgreSQL et Redis**
```bash
# Via l'interface Railway :
# - New Service → PostgreSQL
# - New Service → Redis
```

**5. Configurer les variables d'environnement**

Dans le dashboard Railway, ajouter :
```
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_...
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=https://votre-domaine.com
```

**6. Déployer**
```bash
railway up
```

**7. Configurer le domaine**
- Settings → Generate Domain
- Ou ajouter un domaine custom : Settings → Domains → Add Custom Domain

---

### Option 2 : Render.com

**1. Créer un compte sur [Render.com](https://render.com)**

**2. Créer les services**

**PostgreSQL:**
- New → PostgreSQL
- Name: ai-seo-postgres
- Plan: Free (ou Starter $7/mo)
- Copier l'Internal Database URL

**Redis:**
- New → Redis
- Name: ai-seo-redis
- Plan: Free
- Copier l'Internal Redis URL

**Web Service:**
- New → Web Service
- Connect to GitHub repo
- Name: ai-seo-audit
- Environment: Docker
- Plan: Starter ($7/mo)
- Advanced → Auto-Deploy: Yes

**3. Variables d'environnement (Web Service)**
```
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_...
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=[Internal PostgreSQL URL]
REDIS_URL=[Internal Redis URL]
CORS_ORIGINS=https://votre-domaine.onrender.com
```

**4. Deploy**
- Push to main → Auto-deploy

**5. Configurer le domaine**
- Settings → Custom Domain → Add Custom Domain

---

### Option 3 : Fly.io

**1. Installer flyctl**
```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

**2. Lancer l'app**
```bash
fly launch
```

**3. Ajouter PostgreSQL et Redis**
```bash
fly postgres create
fly redis create
```

**4. Configurer les secrets**
```bash
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set STRIPE_SECRET_KEY=sk_...
fly secrets set STRIPE_PUBLISHABLE_KEY=pk_...
```

**5. Déployer**
```bash
fly deploy
```

---

## Post-Déploiement

### 1. Configurer Stripe Webhook

Une fois l'app déployée :

1. Aller sur [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. "Add endpoint"
3. URL : `https://votre-domaine.com/api/payment/webhook`
4. Events à écouter :
   - `checkout.session.completed`
   - `charge.refunded`
5. Copier le webhook secret → Mettre à jour `STRIPE_WEBHOOK_SECRET`

### 2. Tester le flow complet

```bash
# 1. Créer un audit test
curl -X POST https://votre-domaine.com/api/audit/create \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Restaurant",
    "sector": "restaurant",
    "location": "Paris, France",
    "email": "test@example.com",
    "plan": "freemium",
    "language": "fr"
  }'

# 2. Vérifier le status
curl https://votre-domaine.com/health

# 3. Tester l'interface
open https://votre-domaine.com
```

### 3. Monitoring basique

**Logs :**
```bash
# Railway
railway logs

# Render
# Via dashboard Render → Logs

# Fly
fly logs
```

**Health Check :**
- Endpoint : `GET /health`
- Configurer un monitoring externe (UptimeRobot, Pingdom, etc.)

---

## Scaling

### Horizontal Scaling

**Railway / Render :**
- Dashboard → Settings → Replicas → Augmenter le nombre

**Fly :**
```bash
fly scale count 3
```

### Vertical Scaling

**Railway :**
- Dashboard → Settings → Resources → Upgrade Plan

**Render :**
- Dashboard → Settings → Instance Type → Upgrade

---

## Troubleshooting

### Problème : Database connection failed

```bash
# Vérifier la connexion DB
docker-compose exec api python -c "from src.database.session import engine; print(engine)"

# Vérifier que PostgreSQL tourne
docker-compose ps postgres
```

### Problème : Redis connection timeout

```bash
# Vérifier Redis
docker-compose exec redis redis-cli ping

# Doit retourner : PONG
```

### Problème : WeasyPrint PDF generation fails

```bash
# Vérifier que les dépendances système sont installées
docker-compose exec api dpkg -l | grep libpango
```

### Problème : OpenAI API errors

```bash
# Vérifier la clé API
docker-compose exec api python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Tester la connexion
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Sécurité Production

### 1. Variables d'environnement
- ✅ Jamais commiter `.env`
- ✅ Utiliser des secrets managers (Railway Secrets, Render Env Vars)
- ✅ Rotation régulière des clés API

### 2. HTTPS
- ✅ Toujours activer HTTPS (auto sur Railway/Render/Fly)
- ✅ Redirection HTTP → HTTPS automatique

### 3. CORS
- ✅ Limiter `CORS_ORIGINS` au domaine de production uniquement
- ✅ Pas de wildcard `*` en prod

### 4. Rate Limiting
- TODO : Ajouter rate limiting (FastAPI-Limiter)
- TODO : Ajouter protection DDoS (Cloudflare)

### 5. Database
- ✅ Backups automatiques (activés par défaut sur Railway/Render)
- ✅ SSL connections (activé par défaut)

---

## Budget Estimé

### MVP Testing (gratuit)
- Railway : Free tier (500h/mo)
- Render : Free tier
- Fly : Free tier
- **Total : 0€/mois**

### Production Light
- Railway Starter : $5/mo (app) + $5/mo (postgres)
- Render Starter : $7/mo (app) + $7/mo (postgres) + $1/mo (redis)
- **Total : ~$10-15/mois**

### Production Scaling
- Railway Pro : $20/mo (app) + $15/mo (postgres)
- OpenAI API : ~$20-50/mo (selon volume)
- **Total : ~$50-100/mois**

---

## Checklist Pre-Launch

- [ ] Tests E2E passent
- [ ] Variables d'env configurées
- [ ] Database migrée
- [ ] Stripe webhook configuré
- [ ] Domaine custom configuré
- [ ] HTTPS actif
- [ ] Monitoring en place
- [ ] Backups DB activés
- [ ] Logs accessibles
- [ ] Health check fonctionne

---

**Questions ?** → [Ouvrir une issue](https://github.com/...)
