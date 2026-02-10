# CHANTIER 11 — DEPLOY (Déploiement)

⚠️ **CE PROJET N'UTILISE PAS EUREKAI**

---

## OBJECTIF
Scripts et configuration pour déployer Web2App en production.

## PRÉREQUIS
- C09 API
- C10 Frontend

## LIVRABLES

```
deploy/
├── docker-compose.yml      # Orchestration
├── docker-compose.prod.yml # Override prod
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── .env.example
└── scripts/
    ├── build.sh
    ├── deploy.sh
    └── backup.sh
```

---

## DOCKER COMPOSE

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: web2app-backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    volumes:
      - ./generated:/app/generated
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: web2app-frontend
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

  # Redis pour les jobs (optionnel)
  redis:
    image: redis:alpine
    container_name: web2app-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

---

## DOCKERFILES

### Dockerfile.backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Installer Playwright
RUN pip install playwright && playwright install chromium --with-deps

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Dossiers
RUN mkdir -p /app/generated /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.frontend

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

---

## SCRIPTS

### scripts/build.sh

```bash
#!/bin/bash
set -e

echo "🔨 Building Web2App..."

# Backend
echo "Building backend..."
docker build -t web2app-backend -f Dockerfile.backend ./backend

# Frontend
echo "Building frontend..."
docker build -t web2app-frontend -f Dockerfile.frontend ./frontend

echo "✅ Build complete"
```

### scripts/deploy.sh

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Web2App..."

# Vérifier .env
if [ ! -f .env ]; then
    echo "❌ .env file missing"
    exit 1
fi

# Pull latest
git pull

# Build
./scripts/build.sh

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "✅ Deployed!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
```

---

## .env.example

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Environment
ENVIRONMENT=production

# URLs
FRONTEND_URL=https://web2app.example.com
API_URL=https://api.web2app.example.com

# Redis (optionnel)
REDIS_URL=redis://redis:6379
```

---

## MAKEFILE

```makefile
.PHONY: help build up down logs deploy

help:
	@echo "Web2App Commands"
	@echo "  make build   Build images"
	@echo "  make up      Start services"
	@echo "  make down    Stop services"
	@echo "  make logs    View logs"
	@echo "  make deploy  Full deploy"

build:
	./scripts/build.sh

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

deploy:
	./scripts/deploy.sh
```

---

## LIVRABLES

```
deploy/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── nginx.conf
├── .env.example
├── Makefile
└── scripts/
    ├── build.sh
    └── deploy.sh
```

## CRITÈRES DE VALIDATION

- [ ] docker-compose up lance tout
- [ ] Frontend accessible :3000
- [ ] Backend accessible :8000
- [ ] Health checks passent
- [ ] Volumes persistants

## TEMPS ESTIMÉ
2 heures
