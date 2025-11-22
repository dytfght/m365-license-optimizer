# ============================================
# M365 License Optimizer - Makefile (WSL Compatible)
# ============================================
# Simplifies common development tasks
# ============================================

.PHONY: help setup start stop restart logs clean test status ps shell-db shell-redis backup restore

# Default target
.DEFAULT_GOAL := help

# Load environment variables from .env file
-include .env
export

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Variables
COMPOSE := docker compose
POSTGRES_CONTAINER := m365_optimizer_db
REDIS_CONTAINER := m365_optimizer_redis
BACKUP_DIR := backups
BACKEND_DIR := backend
VENV := $(BACKEND_DIR)/venv

# WSL-compatible: Use bash to run commands in venv context
RUN_IN_VENV := cd $(BACKEND_DIR) && bash -c 'source venv/bin/activate && 

# PostgreSQL connection variables from .env
PGPASSWORD := $(POSTGRES_PASSWORD)
export PGPASSWORD

## help: Show this help message
help:
	@echo "$(BLUE)M365 License Optimizer - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make setup          - First time setup (interactive)"
	@echo "  make setup-quick    - Quick setup with defaults"
	@echo "  make setup-backend  - Setup Python backend environment"
	@echo ""
	@echo "$(GREEN)Service Management:$(NC)"
	@echo "  make start          - Start all services (DB + Redis + Backend API)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make start-infra    - Start only infrastructure (DB + Redis)"
	@echo "  make start-api      - Start only FastAPI backend"
	@echo "  make status         - Show service status"
	@echo "  make ps             - List running containers"
	@echo ""
	@echo "$(GREEN)Backend Development:$(NC)"
	@echo "  make dev            - Start backend in development mode (auto-reload)"
	@echo "  make migrations     - Create new Alembic migration"
	@echo "  make migrate        - Apply Alembic migrations"
	@echo "  make migrate-down   - Rollback last migration"
	@echo "  make shell-backend  - Open Python shell with app context"
	@echo ""
	@echo "$(GREEN)Logs & Monitoring:$(NC)"
	@echo "  make logs           - Show all logs (follow)"
	@echo "  make logs-db        - Show PostgreSQL logs"
	@echo "  make logs-redis     - Show Redis logs"
	@echo "  make logs-api       - Show FastAPI logs"
	@echo ""
	@echo "$(GREEN)Database Operations:$(NC)"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make shell-redis    - Open Redis CLI"
	@echo "  make backup         - Backup PostgreSQL database"
	@echo "  make restore        - Restore PostgreSQL database"
	@echo "  make db-reset       - Reset database (drop and recreate)"
	@echo ""
	@echo "$(GREEN)Testing & Validation:$(NC)"
	@echo "  make test           - Run all tests (infrastructure + backend)"
	@echo "  make test-infrastructure - Run infrastructure tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-lot2      - Run Lot 2 specific tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make test-db        - Test PostgreSQL connection"
	@echo "  make test-redis     - Test Redis connection"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint           - Run code linting (ruff)"
	@echo "  make format         - Format code (black + isort)"
	@echo "  make type-check     - Run type checking (mypy)"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-all      - Remove containers and volumes"
	@echo "  make clean-data     - Remove all data (dangerous!)"
	@echo "  make clean-backend  - Clean Python cache and artifacts"
	@echo ""

## setup: Interactive first-time setup
setup: check-docker
	@echo "$(BLUE)Starting interactive setup...$(NC)"
	@chmod +x scripts/quick-start.sh
	@./scripts/quick-start.sh
	@make setup-backend

## setup-quick: Quick setup with default values
setup-quick: check-docker
	@echo "$(BLUE)Quick setup...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created. Please edit passwords!$(NC)"; \
	fi
	@make setup-backend
	@$(COMPOSE) up -d
	@echo "$(GREEN)✓ Infrastructure started$(NC)"
	@sleep 5
	@make migrate
	@make status

## setup-backend: Setup Python backend environment
setup-backend: check-python
	@echo "$(BLUE)Setting up Python backend...$(NC)"
	@# Supprimer venv existant s'il est corrompu
	@if [ -d "$(VENV)" ]; then \
		echo "$(YELLOW)Removing existing virtual environment...$(NC)"; \
		rm -rf $(VENV); \
	fi
	@# Créer le venv
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	@cd $(BACKEND_DIR) && python3 -m venv venv || { \
		echo "$(RED)✗ Failed to create virtual environment$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Required packages:$(NC)"; \
		echo "  sudo apt-get update"; \
		echo "  sudo apt-get install python3 python3-pip python3-venv python3-dev"; \
		exit 1; \
	}
	@# Vérifier que le venv est fonctionnel
	@if [ ! -f "$(VENV)/bin/activate" ]; then \
		echo "$(RED)✗ Virtual environment creation failed$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@# Upgrade pip
	@echo "$(YELLOW)Upgrading pip...$(NC)"
	@$(RUN_IN_VENV) pip install --upgrade pip'
	@# Installer les dépendances
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@$(RUN_IN_VENV) pip install -r requirements.txt'
	@echo "$(GREEN)✓ Backend setup complete$(NC)"

## start: Start all services (infrastructure + API)
start: check-env start-infra
	@echo "$(BLUE)Starting FastAPI backend...$(NC)"
	@make migrate
	@make start-api

## start-infra: Start only infrastructure services
start-infra: check-env
	@echo "$(BLUE)Starting infrastructure services...$(NC)"
	@$(COMPOSE) up -d
	@echo "$(GREEN)✓ Infrastructure started$(NC)"
	@sleep 3
	@make status

## start-api: Start FastAPI backend server
start-api: check-venv
	@echo "$(BLUE)Starting FastAPI on http://localhost:8000$(NC)"
	@echo "$(YELLOW)Documentation: http://localhost:8000/docs$(NC)"
	@$(RUN_IN_VENV) uvicorn src.main:app --host 0.0.0.0 --port 8000'

## dev: Start backend in development mode with auto-reload
dev: start-infra
	@echo "$(BLUE)Starting FastAPI in development mode...$(NC)"
	@echo "$(GREEN)✓ Auto-reload enabled$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Docs: http://localhost:8000/docs$(NC)"
	@$(RUN_IN_VENV) uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload'

## stop: Stop all services
stop:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(COMPOSE) stop
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart:
	@echo "$(YELLOW)Restarting services...$(NC)"
	@make stop
	@sleep 2
	@make start

## status: Show service status
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@$(COMPOSE) ps
	@echo ""
	@echo "$(BLUE)FastAPI Status:$(NC)"
	@curl -s http://localhost:8000/health 2>/dev/null || echo "$(RED)✗ API not responding$(NC)"
	@echo ""
	@echo "$(BLUE)Health Checks:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}" | grep m365_optimizer || true

## ps: List running containers
ps:
	@$(COMPOSE) ps

## logs: Show all logs (follow mode)
logs:
	@$(COMPOSE) logs -f

## logs-db: Show PostgreSQL logs
logs-db:
	@$(COMPOSE) logs -f db

## logs-redis: Show Redis logs
logs-redis:
	@$(COMPOSE) logs -f redis

## logs-api: Show FastAPI logs (if running in background)
logs-api:
	@tail -f $(BACKEND_DIR)/logs/api.log 2>/dev/null || echo "$(YELLOW)No log file found. API may be running in foreground.$(NC)"

## migrations: Create new Alembic migration
migrations: check-venv
	@echo "$(BLUE)Creating new migration...$(NC)"
	@read -p "Migration message: " MSG; \
	$(RUN_IN_VENV) alembic revision --autogenerate -m "$$MSG"'
	@echo "$(GREEN)✓ Migration created$(NC)"

## migrate: Apply all pending migrations
migrate: check-venv
	@echo "$(BLUE)Applying database migrations...$(NC)"
	@$(RUN_IN_VENV) alembic upgrade head'
	@echo "$(GREEN)✓ Migrations applied$(NC)"

## migrate-down: Rollback last migration
migrate-down: check-venv
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@$(RUN_IN_VENV) alembic downgrade -1'
	@echo "$(GREEN)✓ Migration rolled back$(NC)"

## shell-backend: Open Python shell with app context
shell-backend: check-venv
	@echo "$(BLUE)Opening Python shell...$(NC)"
	@$(RUN_IN_VENV) python -i -c "from src.main import app; from src.core.database import engine"'

## shell-db: Open PostgreSQL shell
shell-db: check-env
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	@echo "$(YELLOW)Tip: Use \\q to exit$(NC)"
	@echo "$(YELLOW)Connecting to: $(POSTGRES_DB) as $(POSTGRES_USER)@$(POSTGRES_HOST):$(POSTGRES_PORT)$(NC)"
	@docker exec -it $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

## shell-redis: Open Redis CLI
shell-redis:
	@echo "$(BLUE)Opening Redis CLI...$(NC)"
	@echo "$(YELLOW)Tip: Use 'exit' to quit$(NC)"
	@if [ -f .env ]; then \
		. ./.env && docker exec -it $(REDIS_CONTAINER) redis-cli -a $$REDIS_PASSWORD; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

## db-reset: Reset database (drop and recreate)
db-reset: check-env
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " CONFIRM; \
	if [ "$$CONFIRM" = "y" ] || [ "$$CONFIRM" = "Y" ]; then \
		echo "$(YELLOW)Resetting database...$(NC)"; \
		docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "DROP DATABASE IF EXISTS $(POSTGRES_DB);"; \
		docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "CREATE DATABASE $(POSTGRES_DB);"; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
		make migrate; \
	else \
		echo "$(GREEN)Cancelled$(NC)"; \
	fi

## test: Run all tests
test: check-test-env
	@echo "$(BLUE)Running all tests...$(NC)"
	@make test-infrastructure
	@make test-backend

## test-backend: Run all backend tests
test-backend: check-venv
	@echo "$(BLUE)Running backend tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/ -v --tb=short'

## test-unit: Run unit tests only
test-unit: check-venv
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/unit/ -v --tb=short -m unit'

## test-integration: Run integration tests only
test-integration: check-venv
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/integration/ -v --tb=short'

## test-lot2: Run Lot 2 specific tests
test-lot2: check-venv
	@echo "$(BLUE)Running Lot 2 tests (Tenant & User Management)...$(NC)"
	@echo ""
	@echo "$(YELLOW)Test Coverage:$(NC)"
	@echo "  - Tenant CRUD operations"
	@echo "  - User synchronization"
	@echo "  - License assignments"
	@echo "  - Microsoft Graph integration (mocked)"
	@echo ""
	@$(RUN_IN_VENV) pytest \
		tests/unit/test_models.py \
		tests/unit/test_repositories.py \
		tests/integration/test_api_tenants.py \
		tests/integration/test_graph_integration.py \
		-v --tb=short'

## test-coverage: Run tests with coverage report
test-coverage: check-venv
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(RUN_IN_VENV) pytest tests/ --cov=src --cov-report=html --cov-report=term-missing'
	@echo "$(GREEN)✓ Coverage report generated: $(BACKEND_DIR)/htmlcov/index.html$(NC)"

## test-infrastructure: Run infrastructure tests
test-infrastructure:
	@echo "$(BLUE)Running infrastructure tests...$(NC)"
	@chmod +x scripts/test-infrastructure.sh
	@./scripts/test-infrastructure.sh

## test-db: Test PostgreSQL connection
test-db: check-env
	@echo "$(BLUE)Testing PostgreSQL connection...$(NC)"
	@echo "$(YELLOW)Database: $(POSTGRES_DB)$(NC)"
	@echo "$(YELLOW)User: $(POSTGRES_USER)$(NC)"
	@echo "$(YELLOW)Host: $(POSTGRES_HOST):$(POSTGRES_PORT)$(NC)"
	@docker exec $(POSTGRES_CONTAINER) pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) && \
		echo "$(GREEN)✓ PostgreSQL is ready$(NC)" || \
		echo "$(RED)✗ PostgreSQL is not ready$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null && \
		echo "$(GREEN)✓ Database query successful$(NC)" || \
		echo "$(RED)✗ Database query failed$(NC)"

## test-redis: Test Redis connection
test-redis:
	@echo "$(BLUE)Testing Redis connection...$(NC)"
	@if [ -f .env ]; then \
		. ./.env && \
		docker exec $(REDIS_CONTAINER) redis-cli -a $$REDIS_PASSWORD PING 2>/dev/null | grep -q PONG && \
		echo "$(GREEN)✓ Redis is responding$(NC)" || \
		echo "$(RED)✗ Redis is not responding$(NC)"; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

## lint: Run code linting
lint: check-venv
	@echo "$(BLUE)Running linters...$(NC)"
	@$(RUN_IN_VENV) ruff check src/ tests/' || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

## format: Format code
format: check-venv
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(RUN_IN_VENV) black src/ tests/'
	@$(RUN_IN_VENV) isort src/ tests/'
	@echo "$(GREEN)✓ Code formatted$(NC)"

## type-check: Run type checking
type-check: check-venv
	@echo "$(BLUE)Running type checker...$(NC)"
	@$(RUN_IN_VENV) mypy src/' || true
	@echo "$(GREEN)✓ Type checking complete$(NC)"

## backup: Backup PostgreSQL database
backup: check-env
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker exec $(POSTGRES_CONTAINER) pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > $(BACKUP_DIR)/$(POSTGRES_DB)_$$TIMESTAMP.sql && \
	echo "$(GREEN)✓ Backup created: $(BACKUP_DIR)/$(POSTGRES_DB)_$$TIMESTAMP.sql$(NC)" || \
	echo "$(RED)✗ Backup failed$(NC)"

## restore: Restore PostgreSQL database
restore: check-env
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -lh $(BACKUP_DIR)/*.sql 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Enter backup filename: " BACKUP_FILE; \
	if [ -f "$(BACKUP_DIR)/$$BACKUP_FILE" ]; then \
		echo "$(BLUE)Restoring from $$BACKUP_FILE...$(NC)"; \
		docker exec -i $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < $(BACKUP_DIR)/$$BACKUP_FILE && \
		echo "$(GREEN)✓ Restore completed$(NC)" || \
		echo "$(RED)✗ Restore failed$(NC)"; \
	else \
		echo "$(RED)Backup file not found$(NC)"; \
	fi

## clean: Stop and remove containers (keeps volumes)
clean:
	@echo "$(YELLOW)Cleaning up containers...$(NC)"
	@$(COMPOSE) down
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@echo "$(GREEN)✓ Containers removed (data preserved)$(NC)"

## clean-all: Remove containers and volumes
clean-all:
	@echo "$(YELLOW)WARNING: This will remove all data!$(NC)"
	@read -p "Are you sure? (y/N): " CONFIRM; \
	if [ "$$CONFIRM" = "y" ] || [ "$$CONFIRM" = "Y" ]; then \
		$(COMPOSE) down -v && \
		pkill -f "uvicorn src.main:app" 2>/dev/null || true && \
		echo "$(GREEN)✓ All containers and volumes removed$(NC)"; \
	else \
		echo "$(GREEN)Cancelled$(NC)"; \
	fi

## clean-backend: Clean Python cache and artifacts
clean-backend:
	@echo "$(YELLOW)Cleaning Python artifacts...$(NC)"
	@find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BACKEND_DIR)/htmlcov $(BACKEND_DIR)/.coverage
	@echo "$(GREEN)✓ Python artifacts cleaned$(NC)"

## clean-data: Remove all data (very dangerous!)
clean-data:
	@echo "$(RED)DANGER: This will permanently delete ALL data!$(NC)"
	@echo "$(YELLOW)This includes all databases, Redis cache, and backups!$(NC)"
	@read -p "Type 'DELETE' to confirm: " CONFIRM; \
	if [ "$$CONFIRM" = "DELETE" ]; then \
		$(COMPOSE) down -v --rmi all && \
		pkill -f "uvicorn src.main:app" 2>/dev/null || true && \
		rm -rf $(BACKUP_DIR) && \
		make clean-backend && \
		echo "$(GREEN)✓ Everything removed$(NC)"; \
	else \
		echo "$(GREEN)Cancelled (nothing deleted)$(NC)"; \
	fi

# Hidden targets (not shown in help)
.PHONY: check-env check-docker check-test-env check-venv check-python

check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Error: Docker not found$(NC)"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "$(RED)Error: Docker daemon not running$(NC)"; exit 1; }

check-python:
	@echo "$(BLUE)Checking Python environment...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { \
		echo "$(RED)✗ Python3 not found$(NC)"; \
		echo "$(YELLOW)Install: sudo apt-get install python3$(NC)"; \
		exit 1; \
	}
	@python3 -m pip --version >/dev/null 2>&1 || { \
		echo "$(RED)✗ pip module not found$(NC)"; \
		echo "$(YELLOW)Install: sudo apt-get install python3-pip$(NC)"; \
		exit 1; \
	}
	@python3 -c "import venv" 2>/dev/null || { \
		echo "$(RED)✗ venv module not found$(NC)"; \
		echo "$(YELLOW)Install: sudo apt-get install python3-venv$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✓ Python environment OK$(NC)"

check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "$(YELLOW)Run 'make setup' first$(NC)"; \
		exit 1; \
	fi

check-venv: check-env
	@if [ ! -d "$(VENV)" ] || [ ! -f "$(VENV)/bin/activate" ]; then \
		echo "$(RED)Error: Virtual environment not found or incomplete$(NC)"; \
		echo "$(YELLOW)Run 'make setup-backend' first$(NC)"; \
		exit 1; \
	fi

check-test-env: check-venv
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$(POSTGRES_DB)_test';" 2>/dev/null | grep -q 1 || \
	(echo "$(YELLOW)Creating test database...$(NC)" && \
	docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "CREATE DATABASE $(POSTGRES_DB)_test;")
