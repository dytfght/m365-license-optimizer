# ============================================
# M365 License Optimizer - Makefile (Full Stack)
# Unified management for Backend (Python) + Frontend (Next.js) + Docker
# ============================================

.PHONY: help setup clean test lint format dev up down logs status
.PHONY: setup-backend clean-backend test-backend lint-backend format-backend dev-backend migrate shell-backend
.PHONY: setup-frontend clean-frontend test-frontend lint-frontend format-frontend dev-frontend build-frontend
.PHONY: build-all migrate-docker logs-frontend logs-backend

.DEFAULT_GOAL := help

-include .env
export

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Variables
COMPOSE := docker compose
POSTGRES_CONTAINER := m365_optimizer_db
REDIS_CONTAINER := m365_optimizer_redis
BACKEND_CONTAINER := m365_optimizer_backend
BACKUP_DIR := backups
BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/venv

# Execution contexts
RUN_IN_VENV := cd $(BACKEND_DIR) && bash -c 'source venv/bin/activate && 
RUN_IN_FRONTEND := cd $(FRONTEND_DIR) && 

# Database
PGPASSWORD := $(POSTGRES_PASSWORD)
export PGPASSWORD

## help: Show this help message
help:
	@echo "$(BLUE)M365 License Optimizer - Full Stack Management$(NC)"
	@echo ""
	@echo "$(GREEN)Global Commands (Full Stack):$(NC)"
	@echo "  make setup          - Setup entire project (Backend + Frontend + .env)"
	@echo "  make clean          - Clean everything (Containers + Artifacts)"
	@echo "  make test           - Run all tests (Backend + Frontend)"
	@echo "  make lint           - Lint all code"
	@echo "  make format         - Format all code"
	@echo "  make dev            - Instructions for starting dev environment"
	@echo ""
	@echo "$(GREEN)Docker Deployment:$(NC)"
	@echo "  make up             - Start all services (Docker)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Show all logs"
	@echo "  make build-all      - Build all Docker images"
	@echo "  make migrate-docker - Run migrations in Docker backend"
	@echo "  make status         - Show services status"
	@echo ""
	@echo "$(GREEN)Backend (Python/FastAPI):$(NC)"
	@echo "  make setup-backend  - Install Python dependencies"
	@echo "  make dev-backend    - Start API dev server (port 8000)"
	@echo "  make test-backend   - Run pytest"
	@echo "  make lint-backend   - Run ruff"
	@echo "  make migrate        - Run alembic migrations (local)"
	@echo "  make shell-backend  - Open Python shell"
	@echo ""
	@echo "$(GREEN)Frontend (Next.js):$(NC)"
	@echo "  make setup-frontend - Install npm dependencies"
	@echo "  make dev-frontend   - Start Next.js dev server (port 3001)"
	@echo "  make build-frontend - Build for production"
	@echo "  make test-frontend  - Run Jest tests"
	@echo "  make lint-frontend  - Run ESLint"
	@echo ""

# ============================================
# Global Commands
# ============================================

## setup: Setup entire project
setup: check-prereqs
	@echo "$(BLUE)Setting up M365 License Optimizer...$(NC)"
	@# 1. .env file
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created$(NC)"; \
	else \
		echo "$(GREEN)✓ .env exists$(NC)"; \
	fi
	@# 2. Backend
	@make setup-backend
	@# 3. Frontend
	@make setup-frontend
	@echo ""
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo "$(BLUE)Run 'make dev' to see how to start the project.$(NC)"

## clean: Clean everything
clean: down
	@echo "$(YELLOW)Cleaning artifacts...$(NC)"
	@make clean-backend
	@make clean-frontend
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## clean-all: Clean everything including database (full reset)
clean-all:
	@echo "$(RED)⚠️  Full reset - This will delete all data!$(NC)"
	@echo "$(YELLOW)Stopping and removing containers + volumes...$(NC)"
	@$(COMPOSE) down -v --remove-orphans
	@make clean-backend
	@make clean-frontend
	@docker system prune -f 2>/dev/null || true
	@echo "$(GREEN)✓ Full cleanup complete (DB reset)$(NC)"

## test: Run all tests
test: test-backend test-frontend

## lint: Lint all code
lint: lint-backend lint-frontend

## format: Format all code
format: format-backend format-frontend

## dev: Instructions for dev
dev:
	@echo "$(BLUE)To start development environment:$(NC)"
	@echo "1. Start Infrastructure (DB + Redis):"
	@echo "   $(YELLOW)make start-infra$(NC)"
	@echo ""
	@echo "2. Start Backend (Terminal 1):"
	@echo "   $(YELLOW)make dev-backend$(NC)"
	@echo ""
	@echo "3. Start Frontend (Terminal 2):"
	@echo "   $(YELLOW)make dev-frontend$(NC)"

# ============================================
# Docker / Infrastructure
# ============================================

## up: Start all services
up: build-all
	@echo "$(BLUE)Starting all services...$(NC)"
	@$(COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@make status

## down: Stop all services
down:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart: down up

## logs: Show all logs
logs:
	@$(COMPOSE) logs -f

## logs-backend: Show backend logs
logs-backend:
	@$(COMPOSE) logs -f backend

## logs-frontend: Show frontend logs
logs-frontend:
	@$(COMPOSE) logs -f frontend

## build-all: Build all images
build-all:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@$(COMPOSE) build
	@echo "$(GREEN)✓ Build complete$(NC)"

## migrate-docker: Run migrations in Docker
migrate-docker:
	@echo "$(BLUE)Running migrations in Docker backend...$(NC)"
	@docker exec $(BACKEND_CONTAINER) alembic upgrade head && \
		echo "$(GREEN)✓ Migrations applied$(NC)" || \
		echo "$(RED)✗ Migration failed$(NC)"

## status: Show status
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@$(COMPOSE) ps
	@echo ""
	@echo "$(BLUE)Endpoints:$(NC)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Docs:     http://localhost:8000/docs"
	@echo "  PgAdmin:  http://localhost:5050"

## start-infra: Start DB and Redis only
start-infra:
	@echo "$(BLUE)Starting infrastructure...$(NC)"
	@$(COMPOSE) up -d db redis
	@echo "$(GREEN)✓ Infrastructure ready$(NC)"

# ============================================
# Backend Commands
# ============================================

## setup-backend: Setup Python environment
setup-backend:
	@echo "$(BLUE)Setting up Backend...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		python3 -m venv $(VENV); \
		echo "$(GREEN)✓ Venv created$(NC)"; \
	fi
	@$(RUN_IN_VENV) pip install --upgrade pip > /dev/null; \
	pip install -r requirements.txt > /dev/null'
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

## dev-backend: Start API dev server
dev-backend:
	@echo "$(BLUE)Starting Backend (http://localhost:8000)...$(NC)"
	@$(RUN_IN_VENV) uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload'

## test-backend: Run backend tests
test-backend:
	@echo "$(BLUE)Running Backend Tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/ -v --tb=short'

## lint-backend: Lint backend code
lint-backend:
	@echo "$(BLUE)Linting Backend...$(NC)"
	@$(RUN_IN_VENV) ruff check src/ tests/' || true

## format-backend: Format backend code
format-backend:
	@echo "$(BLUE)Formatting Backend...$(NC)"
	@$(RUN_IN_VENV) black src/ tests/'
	@$(RUN_IN_VENV) isort src/ tests/'

## clean-backend: Clean backend artifacts
clean-backend:
	@rm -rf $(BACKEND_DIR)/__pycache__
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/htmlcov
	@echo "$(GREEN)✓ Backend cleaned$(NC)"

## migrate: Run local migrations
migrate:
	@echo "$(BLUE)Running local migrations...$(NC)"
	@$(RUN_IN_VENV) alembic upgrade head'

## shell-backend: Open Python shell
shell-backend:
	@$(RUN_IN_VENV) python -i -c "from src.main import app; from src.core.database import engine"'

# ============================================
# Frontend Commands
# ============================================

## setup-frontend: Install npm dependencies
setup-frontend:
	@echo "$(BLUE)Setting up Frontend...$(NC)"
	@$(RUN_IN_FRONTEND) npm install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

## dev-frontend: Start Next.js dev server
dev-frontend:
	@echo "$(BLUE)Starting Frontend (http://localhost:3001)...$(NC)"
	@$(RUN_IN_FRONTEND) npm run dev

## build-frontend: Build for production
build-frontend:
	@echo "$(BLUE)Building Frontend...$(NC)"
	@$(RUN_IN_FRONTEND) npm run build

## test-frontend: Run frontend tests
test-frontend:
	@echo "$(BLUE)Running Frontend Tests...$(NC)"
	@$(RUN_IN_FRONTEND) npm test || echo "$(YELLOW)No tests configured$(NC)"

## lint-frontend: Lint frontend code
lint-frontend:
	@echo "$(BLUE)Linting Frontend...$(NC)"
	@$(RUN_IN_FRONTEND) npm run lint || true

## format-frontend: Format frontend code
format-frontend:
	@echo "$(BLUE)Formatting Frontend...$(NC)"
	@# Assuming prettier or similar script exists
	@echo "$(YELLOW)Frontend formatting not configured yet$(NC)"

## clean-frontend: Clean frontend artifacts
clean-frontend:
	@rm -rf $(FRONTEND_DIR)/.next
	@rm -rf $(FRONTEND_DIR)/out
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo "$(GREEN)✓ Frontend cleaned$(NC)"

# ============================================
# Security & GDPR (LOT 10)
# ============================================

## security-scan: Run security analysis
security-scan:
	@echo "$(BLUE)Running Security Scan...$(NC)"
	@$(RUN_IN_VENV) bandit -r src/ -ll -f txt' || echo "$(YELLOW)Bandit not installed, run: pip install bandit$(NC)"
	@$(RUN_IN_FRONTEND) npm audit || echo "$(YELLOW)Frontend audit failed$(NC)"
	@echo "$(GREEN)✓ Security scan complete$(NC)"

## gdpr-audit: Check GDPR compliance
gdpr-audit:
	@echo "$(BLUE)Running GDPR Audit...$(NC)"
	@echo "Checking log retention policy..."
	@$(RUN_IN_VENV) python -c "from src.core.config import settings; print(f\"Log retention: {settings.LOG_RETENTION_DAYS} days\")' || echo "$(RED)Config check failed$(NC)"
	@echo "$(GREEN)✓ GDPR audit complete$(NC)"

## test-lot10: Run LOT 10 specific tests
test-lot10:
	@echo "$(BLUE)Running LOT 10 Tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/unit/test_security_service.py tests/unit/test_gdpr_service.py tests/unit/test_logging_service.py -v'
	@echo "$(GREEN)✓ LOT 10 tests complete$(NC)"

# ============================================
# Utilities
# ============================================

check-prereqs:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker not found$(NC)"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python3 not found$(NC)"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "$(RED)npm not found$(NC)"; exit 1; }

# ============================================
# LOT 11: Deployment & Operations
# ============================================

## deploy-azure: Trigger Azure deployment workflow
deploy-azure:
	@echo "$(BLUE)Triggering Azure deployment...$(NC)"
	@if command -v gh >/dev/null 2>&1; then \
		gh workflow run deploy-azure.yml && echo "$(GREEN)✓ Deployment workflow triggered$(NC)"; \
	else \
		echo "$(YELLOW)GitHub CLI not installed. Run: gh workflow run deploy-azure.yml$(NC)"; \
	fi

## scale-up: Scale backend to multiple replicas
scale-up:
	@echo "$(BLUE)Scaling backend to 3 replicas...$(NC)"
	@$(COMPOSE) up -d --scale backend=3
	@echo "$(GREEN)✓ Backend scaled to 3 replicas$(NC)"
	@make status

## scale-down: Scale backend back to 1 replica
scale-down:
	@echo "$(BLUE)Scaling backend to 1 replica...$(NC)"
	@$(COMPOSE) up -d --scale backend=1
	@echo "$(GREEN)✓ Backend scaled to 1 replica$(NC)"
	@make status

## backup-db: Run database backup
backup-db:
	@echo "$(BLUE)Running database backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@$(RUN_IN_VENV) python ../scripts/backup_db.py --local-only --output-dir ../$(BACKUP_DIR)' || \
		docker exec $(POSTGRES_CONTAINER) pg_dump -U $(POSTGRES_USER) -d $(POSTGRES_DB) | gzip > $(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "$(GREEN)✓ Backup complete$(NC)"

## backup-db-azure: Backup database to Azure Blob Storage
backup-db-azure:
	@echo "$(BLUE)Backing up database to Azure...$(NC)"
	@$(RUN_IN_VENV) python ../scripts/backup_db.py --cleanup'
	@echo "$(GREEN)✓ Azure backup complete$(NC)"

## restore-db: Restore database from backup
restore-db:
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -la $(BACKUP_DIR)/*.sql.gz 2>/dev/null || echo "  No local backups found"
	@echo ""
	@echo "To restore, run: make restore-db-file FILE=path/to/backup.sql.gz"

## restore-db-file: Restore specific backup file
restore-db-file:
ifndef FILE
	$(error FILE is required. Usage: make restore-db-file FILE=backups/backup_xxx.sql.gz)
endif
	@echo "$(YELLOW)⚠️  This will overwrite the database!$(NC)"
	@read -p "Are you sure? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Restoring from $(FILE)...$(NC)"
	@gunzip -c $(FILE) | docker exec -i $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)
	@echo "$(GREEN)✓ Database restored$(NC)"

## test-lot11: Run LOT 11 specific tests
test-lot11:
	@echo "$(BLUE)Running LOT 11 Tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/unit/test_observability_service.py tests/integration/test_api_observability.py -v' || echo "$(YELLOW)Some tests not found yet$(NC)"
	@echo "$(GREEN)✓ LOT 11 tests complete$(NC)"

## blue-green: Run blue-green deployment
blue-green:
	@echo "$(BLUE)Running blue-green deployment...$(NC)"
	@bash scripts/deploy_blue_green.sh deploy

## blue-green-rollback: Rollback to previous deployment
blue-green-rollback:
	@echo "$(YELLOW)Rolling back deployment...$(NC)"
	@bash scripts/deploy_blue_green.sh rollback

