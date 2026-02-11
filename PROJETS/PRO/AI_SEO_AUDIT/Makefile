.PHONY: help install dev test clean docker-up docker-down migrate db-upgrade db-downgrade

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

dev: ## Run development server
	.venv/bin/uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	.venv/bin/pytest tests/ -v --cov=src

clean: ## Clean cache and temp files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

migrate: ## Create new migration
	.venv/bin/alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Run migrations (upgrade)
	.venv/bin/alembic upgrade head

db-downgrade: ## Rollback migration
	.venv/bin/alembic downgrade -1

db-reset: ## Reset database (drop all + recreate)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 3
	.venv/bin/alembic upgrade head

format: ## Format code with black
	.venv/bin/black src/ tests/

lint: ## Lint code with flake8
	.venv/bin/flake8 src/ tests/

type-check: ## Type check with mypy
	.venv/bin/mypy src/
