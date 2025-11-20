# AYITI AI - Makefile for common tasks

.PHONY: help install dev prod build up down logs restart clean test init-kb backup health

# Default target
help:
	@echo "AYITI AI - Available Commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make install      - Install dependencies"
	@echo "    make dev          - Run development server"
	@echo "    make init-kb      - Initialize knowledge bases"
	@echo ""
	@echo "  Docker (Development):"
	@echo "    make build        - Build Docker images"
	@echo "    make up           - Start containers"
	@echo "    make down         - Stop containers"
	@echo "    make logs         - View logs"
	@echo "    make restart      - Restart containers"
	@echo ""
	@echo "  Docker (Production):"
	@echo "    make prod         - Deploy to production"
	@echo "    make prod-logs    - View production logs"
	@echo "    make prod-down    - Stop production"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make clean        - Clean temporary files"
	@echo "    make test         - Run tests"
	@echo "    make backup       - Backup vector database"
	@echo "    make health       - Check system health"
	@echo ""

# Installation
install:
	python3 -m venv ayiti_env
	./ayiti_env/bin/pip install --upgrade pip
	./ayiti_env/bin/pip install -r requirements.txt
	cp .env.example .env
	@echo "Installation complete! Edit .env and add your API keys."

# Development server
dev:
	./ayiti_env/bin/uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Initialize knowledge bases
init-kb:
	./ayiti_env/bin/python scripts/init_all_kb.py

# Docker - Development
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@make health

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart
	@make health

# Docker - Production
prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml build
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@make health
	@echo "Production deployment complete!"

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-restart:
	docker-compose -f docker-compose.prod.yml restart

# Maintenance
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "Cleaned temporary files"

test:
	./ayiti_env/bin/pytest tests/ -v

backup:
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf backups/vector_db_$$timestamp.tar.gz data/vector_db/; \
	echo "Backup created: backups/vector_db_$$timestamp.tar.gz"

health:
	@echo "Checking system health..."
	@curl -s http://localhost:8000/health | jq '.' || echo "Health check failed"
	@echo ""
	@curl -s http://localhost:8000/api/v1/stats/overview | jq '.performance.throughput' || echo "Stats unavailable"

# Database management
db-backup:
	@make backup

db-restore:
	@echo "Enter backup file name (e.g., vector_db_20240101_120000.tar.gz):"
	@read backup_file; \
	tar -xzf backups/$$backup_file -C data/

# Cache management
cache-clear:
	curl -X POST http://localhost:8000/api/v1/admin/cache/clear

cache-cleanup:
	curl -X POST http://localhost:8000/api/v1/admin/cache/cleanup

# Stats
stats:
	@echo "=== Cost Stats ==="
	@curl -s http://localhost:8000/api/v1/stats/cost | jq '.'
	@echo ""
	@echo "=== Cache Stats ==="
	@curl -s http://localhost:8000/api/v1/stats/cache | jq '.'
	@echo ""
	@echo "=== Performance Stats ==="
	@curl -s http://localhost:8000/api/v1/stats/performance | jq '.overall'

# Security
security-check:
	@echo "Running security checks..."
	./ayiti_env/bin/pip install safety bandit
	./ayiti_env/bin/safety check
	./ayiti_env/bin/bandit -r . -x ./ayiti_env,./tests

# Code quality
lint:
	./ayiti_env/bin/black .
	./ayiti_env/bin/ruff check . --fix

format:
	./ayiti_env/bin/black .

# Update dependencies
update-deps:
	./ayiti_env/bin/pip install --upgrade pip
	./ayiti_env/bin/pip install --upgrade -r requirements.txt
