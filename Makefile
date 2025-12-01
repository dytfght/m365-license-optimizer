# ============================================
# M365 License Optimizer - Makefile (WSL Compatible)
# Version LOT4 - Compatible avec init.sql minimaliste
# ============================================

.PHONY: help setup start stop restart logs clean test status ps shell-db shell-redis backup restore

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
BACKUP_DIR := backups
BACKEND_DIR := backend
VENV := $(BACKEND_DIR)/venv

RUN_IN_VENV := cd $(BACKEND_DIR) && bash -c 'source venv/bin/activate && 

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
	@echo "$(GREEN)Database Operations:$(NC)"
	@echo "  make init-schema    - Initialize optimizer schema (first time only)"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make shell-redis    - Open Redis CLI"
	@echo "  make backup         - Backup PostgreSQL database"
	@echo "  make restore        - Restore PostgreSQL database"
	@echo "  make db-reset       - Reset database (drop and recreate)"
	@echo "  make db-status      - Show database schema status"
	@echo ""
	@echo "$(GREEN)Testing & Validation:$(NC)"
	@echo "  make test           - Run all tests"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make validate-schema - Validate database schema consistency"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint           - Run code linting"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Run type checking"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-all      - Remove containers and volumes"
	@echo ""

## setup: Interactive first-time setup
setup: check-docker
	@echo "$(BLUE)Starting interactive setup...$(NC)"
	@chmod +x scripts/quick-start.sh
	@./scripts/quick-start.sh

## setup-quick: Quick setup with default values (LOT4 compatible)
setup-quick: check-docker check-python
	@echo "$(BLUE)═══════════════════════════════════════$(NC)"
	@echo "$(BLUE) Quick Setup - LOT4 Compatible$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════$(NC)"
	@echo ""
	
	@# 1. Create .env if missing
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)📄 Creating .env from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created$(NC)"; \
		echo "$(RED)⚠  WARNING: Change passwords in .env before production!$(NC)"; \
	else \
		echo "$(GREEN)✓ .env already exists$(NC)"; \
	fi
	@echo ""
	
	@# 2. Setup Python backend
	@echo "$(YELLOW)🐍 Setting up Python environment...$(NC)"
	@make setup-backend
	@echo ""
	
	@# 3. Start infrastructure
	@echo "$(YELLOW)🚀 Starting infrastructure (PostgreSQL + Redis)...$(NC)"
	@$(COMPOSE) up -d db redis
	@echo "$(GREEN)✓ Containers started$(NC)"
	@echo ""
	
	@# 4. Wait for PostgreSQL
	@echo "$(YELLOW)⏳ Waiting for PostgreSQL to be ready...$(NC)"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		if docker exec $(POSTGRES_CONTAINER) pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) >/dev/null 2>&1; then \
			echo "$(GREEN)✓ PostgreSQL is ready$(NC)"; \
			break; \
		fi; \
		echo "   Attempt $$i/10..."; \
		sleep 2; \
	done
	@echo ""
	
	@# 5. Initialize schema
	@echo "$(YELLOW)🗄️  Initializing optimizer schema...$(NC)"
	@make init-schema
	@echo ""
	
	@# 6. Run migrations
	@echo "$(YELLOW)📊 Applying Alembic migrations...$(NC)"
	@make migrate
	@echo ""
	
	@# 7. Validate setup
	@echo "$(YELLOW)✔️  Validating setup...$(NC)"
	@make db-status
	@echo ""
	
	@echo "$(GREEN)═══════════════════════════════════════$(NC)"
	@echo "$(GREEN)✓ Quick setup complete!$(NC)"
	@echo "$(GREEN)═══════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Run 'make dev' to start the API in development mode"
	@echo "  • Run 'make test' to run all tests"
	@echo "  • Visit http://localhost:8000/docs for API documentation"

## setup-backend: Setup Python backend environment
setup-backend: check-python
	@echo "$(BLUE)Setting up Python backend...$(NC)"
	@if [ -d "$(VENV)" ]; then \
		echo "$(GREEN)✓ Virtual environment already exists$(NC)"; \
		echo "$(YELLOW)Updating dependencies...$(NC)"; \
	else \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		cd $(BACKEND_DIR) && python3 -m venv venv || { \
			echo "$(RED)✗ Failed to create virtual environment$(NC)"; \
			echo ""; \
			echo "$(YELLOW)Install required packages:$(NC)"; \
			echo "  sudo apt-get update"; \
			echo "  sudo apt-get install python3 python3-pip python3-venv python3-dev"; \
			exit 1; \
		}; \
		if [ ! -f "$(VENV)/bin/activate" ]; then \
			echo "$(RED)✗ Virtual environment creation failed$(NC)"; \
			exit 1; \
		fi; \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	fi
	@echo "$(YELLOW)Upgrading pip...$(NC)"
	@$(RUN_IN_VENV) pip install --upgrade pip'
	@echo "$(YELLOW)Installing/updating dependencies...$(NC)"
	@$(RUN_IN_VENV) pip install -r requirements.txt'
	@echo "$(GREEN)✓ Backend setup complete$(NC)"

## init-schema: Initialize optimizer schema (LOT4 - first time only)
init-schema: check-env
	@echo "$(BLUE)Initializing optimizer schema...$(NC)"
	@# Check if schema already exists
	@SCHEMA_EXISTS=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='optimizer')"); \
	if [ "$$SCHEMA_EXISTS" = "t" ]; then \
		echo "$(GREEN)✓ Schema 'optimizer' already exists$(NC)"; \
	else \
		echo "$(YELLOW)Creating schema 'optimizer'...$(NC)"; \
		docker exec -i $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < docker/db/init.sql && \
		echo "$(GREEN)✓ Schema 'optimizer' created$(NC)" || { \
			echo "$(RED)✗ Failed to create schema$(NC)"; \
			exit 1; \
		}; \
	fi

## start: Start all services
start: check-env start-infra
	@echo "$(BLUE)Starting FastAPI backend...$(NC)"
	@make ensure-migrated
	@make start-api

## start-infra: Start only infrastructure services
start-infra: check-env
	@echo "$(BLUE)Starting infrastructure services...$(NC)"
	@$(COMPOSE) up -d db redis
	@echo "$(GREEN)✓ Infrastructure started$(NC)"
	@sleep 3
	@make status

## start-api: Start FastAPI backend server
start-api: check-venv
	@echo "$(BLUE)Starting FastAPI on http://localhost:8000$(NC)"
	@echo "$(YELLOW)Documentation: http://localhost:8000/docs$(NC)"
	@$(RUN_IN_VENV) uvicorn src.main:app --host 0.0.0.0 --port 8000'

## dev: Start backend in development mode
dev: start-infra ensure-migrated
	@echo "$(BLUE)Starting FastAPI in development mode...$(NC)"
	@echo "$(GREEN)✓ Auto-reload enabled$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Docs: http://localhost:8000/docs$(NC)"
	@$(RUN_IN_VENV) uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload'

## ensure-migrated: Ensure database schema is up to date (LOT4)
ensure-migrated: check-venv
	@echo "$(BLUE)Checking database migration status...$(NC)"
	@# Check if schema exists
	@SCHEMA_EXISTS=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='optimizer')"); \
	if [ "$$SCHEMA_EXISTS" != "t" ]; then \
		echo "$(YELLOW)Schema 'optimizer' not found, initializing...$(NC)"; \
		make init-schema; \
	fi
	@# Check if migrations are applied
	@ALEMBIC_TABLE=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')"); \
	if [ "$$ALEMBIC_TABLE" != "t" ]; then \
		echo "$(YELLOW)No migrations applied yet, running migrations...$(NC)"; \
		make migrate; \
	else \
		echo "$(GREEN)✓ Database schema is ready$(NC)"; \
	fi

## stop: Stop all services
stop:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(COMPOSE) stop
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart:
	@make stop
	@sleep 2
	@make start

## status: Show service status
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@$(COMPOSE) ps
	@echo ""
	@echo "$(BLUE)API Health Check:$(NC)"
	@curl -s http://localhost:8000/health 2>/dev/null | jq . || echo "$(RED)✗ API not responding$(NC)"

## ps: List running containers
ps:
	@$(COMPOSE) ps

## logs: Show all logs
logs:
	@$(COMPOSE) logs -f

## logs-db: Show PostgreSQL logs
logs-db:
	@$(COMPOSE) logs -f db

## logs-redis: Show Redis logs
logs-redis:
	@$(COMPOSE) logs -f redis

## migrations: Create new Alembic migration
migrations: check-venv
	@echo "$(BLUE)Creating new migration...$(NC)"
	@read -p "Migration message: " MSG; \
	$(RUN_IN_VENV) alembic revision --autogenerate -m "$$MSG"'
	@echo "$(GREEN)✓ Migration created$(NC)"
	@echo "$(YELLOW)⚠  Review the generated migration file before applying!$(NC)"

## migrate: Apply all pending migrations (LOT4 safe)
migrate: check-venv
	@echo "$(BLUE)Applying database migrations...$(NC)"
	@# Ensure schema exists first
	@make init-schema
	@# Apply migrations
	@$(RUN_IN_VENV) alembic upgrade head' && \
		echo "$(GREEN)✓ Migrations applied$(NC)" || { \
		echo "$(RED)✗ Migration failed$(NC)"; \
		echo "$(YELLOW)Check if database is accessible and schema is initialized$(NC)"; \
		exit 1; \
	}

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
	@echo "$(BLUE)Opening PostgreSQL shell (schema: optimizer)...$(NC)"
	@echo "$(YELLOW)Tip: Use \\q to exit$(NC)"
	@docker exec -it $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SET search_path TO optimizer, public;"
	@docker exec -it $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

## shell-redis: Open Redis CLI
shell-redis:
	@echo "$(BLUE)Opening Redis CLI...$(NC)"
	@if [ -f .env ]; then \
		. ./.env && docker exec -it $(REDIS_CONTAINER) redis-cli -a $$REDIS_PASSWORD; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

## db-reset: Reset database (LOT4 compatible)
db-reset: check-env
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " CONFIRM; \
	if [ "$$CONFIRM" = "y" ] || [ "$$CONFIRM" = "Y" ]; then \
		echo "$(YELLOW)Resetting database...$(NC)"; \
		docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "DROP DATABASE IF EXISTS $(POSTGRES_DB);"; \
		docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d postgres -c "CREATE DATABASE $(POSTGRES_DB);"; \
		echo "$(GREEN)✓ Database dropped and recreated$(NC)"; \
		echo "$(YELLOW)Initializing schema...$(NC)"; \
		make init-schema; \
		echo "$(YELLOW)Applying migrations...$(NC)"; \
		make migrate; \
		echo "$(GREEN)✓ Database reset complete$(NC)"; \
	else \
		echo "$(GREEN)Cancelled$(NC)"; \
	fi

## db-status: Show database schema status (LOT4)
db-status: check-env
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo "$(BLUE) Database Schema Status$(NC)"
	@echo "$(BLUE)════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Schemas:$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c \
		"SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('public', 'optimizer') ORDER BY schema_name;"
	@echo ""
	@echo "$(YELLOW)Tables in 'optimizer' schema:$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c \
		"SELECT tablename FROM pg_tables WHERE schemaname='optimizer' ORDER BY tablename;" || echo "$(RED)No tables found$(NC)"
	@echo ""
	@echo "$(YELLOW)Tables in 'public' schema (should only be alembic_version):$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c \
		"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;" || echo "$(GREEN)None (expected)$(NC)"
	@echo ""
	@echo "$(YELLOW)Current Alembic version:$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "$(RED)No migrations applied yet$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════$(NC)"

## validate-schema: Validate database schema consistency (LOT4)
validate-schema: check-env
	@echo "$(BLUE)Validating database schema...$(NC)"
	@echo ""
	@# Check optimizer schema exists
	@SCHEMA_EXISTS=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='optimizer')"); \
	if [ "$$SCHEMA_EXISTS" = "t" ]; then \
		echo "$(GREEN)✓ Schema 'optimizer' exists$(NC)"; \
	else \
		echo "$(RED)✗ Schema 'optimizer' NOT found$(NC)"; \
		exit 1; \
	fi
	@# Check no business tables in public
	@PUBLIC_TABLES=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT COUNT(*) FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version'"); \
	if [ "$$PUBLIC_TABLES" = "0" ]; then \
		echo "$(GREEN)✓ No business tables in 'public' schema$(NC)"; \
	else \
		echo "$(RED)✗ Found $$PUBLIC_TABLES unexpected table(s) in 'public' schema$(NC)"; \
		docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c \
			"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename != 'alembic_version'"; \
		exit 1; \
	fi
	@# Count optimizer tables
	@OPTIMIZER_TABLES=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT COUNT(*) FROM pg_tables WHERE schemaname='optimizer'"); \
	echo "$(GREEN)✓ Found $$OPTIMIZER_TABLES table(s) in 'optimizer' schema$(NC)"
	@# Check Alembic version
	@ALEMBIC_VERSION=$$(docker exec $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -tAc \
		"SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "none"); \
	if [ "$$ALEMBIC_VERSION" != "none" ]; then \
		echo "$(GREEN)✓ Alembic version: $$ALEMBIC_VERSION$(NC)"; \
	else \
		echo "$(RED)✗ No Alembic version found$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(GREEN)✓ Schema validation passed!$(NC)"

## test: Run all tests
test: check-venv
	@echo "$(BLUE)Running all tests...$(NC)"
	@# Tests run on the default database (m365_optimizer)
	@# Each test creates/drops the optimizer schema for isolation
	@$(RUN_IN_VENV) pytest tests/ -v --tb=short'

## test-serial: Run tests sequentially to avoid concurrency issues
test-serial: check-venv
	@echo "$(BLUE)Running tests sequentially...$(NC)"
	@# Prepare test environment
	@docker exec m365_optimizer_db psql -U admin -d postgres -c "DROP DATABASE IF EXISTS m365_optimizer_test;" 2>/dev/null || true
	@docker exec m365_optimizer_db psql -U admin -d postgres -c "CREATE DATABASE m365_optimizer_test;" 2>/dev/null || true
	@# Force sequential execution to avoid database conflicts
	@$(RUN_IN_VENV) pytest tests/ -v --tb=short --dist=no -n 0 --disable-warnings'

## test-unit: Run unit tests only
test-unit: check-venv
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/unit/ -v --tb=short'

## test-integration: Run integration tests only
test-integration: check-venv
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(RUN_IN_VENV) pytest tests/integration/ -v --tb=short'

## test-coverage: Run tests with coverage report
test-coverage: check-venv
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(RUN_IN_VENV) pytest tests/ --cov=src --cov-report=html --cov-report=term-missing'
	@echo "$(GREEN)✓ Coverage report: $(BACKEND_DIR)/htmlcov/index.html$(NC)"

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

## backup: Backup PostgreSQL database
backup: check-env
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker exec $(POSTGRES_CONTAINER) pg_dump -U $(POSTGRES_USER) $(POSTGRES_DB) > $(BACKUP_DIR)/$(POSTGRES_DB)_$$TIMESTAMP.sql && \
	echo "$(GREEN)✓ Backup: $(BACKUP_DIR)/$(POSTGRES_DB)_$$TIMESTAMP.sql$(NC)"

## restore: Restore PostgreSQL database
restore: check-env
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -lh $(BACKUP_DIR)/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Backup filename: " BACKUP_FILE; \
	if [ -f "$(BACKUP_DIR)/$$BACKUP_FILE" ]; then \
		docker exec -i $(POSTGRES_CONTAINER) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < $(BACKUP_DIR)/$$BACKUP_FILE && \
		echo "$(GREEN)✓ Restore completed$(NC)"; \
	else \
		echo "$(RED)Backup file not found$(NC)"; \
	fi

## clean: Stop and remove containers
clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@$(COMPOSE) down
	@pkill -f "uvicorn src.main:app" 2>/dev/null || true
	@echo "$(GREEN)✓ Containers removed$(NC)"

## clean-all: Remove containers and volumes
clean-all:
	@echo "$(RED)WARNING: This will remove all data!$(NC)"
	@read -p "Continue? (y/N): " CONFIRM; \
	if [ "$$CONFIRM" = "y" ]; then \
		$(COMPOSE) down -v && \
		echo "$(GREEN)✓ All removed$(NC)"; \
	fi

## clean-backend: Clean Python artifacts
clean-backend:
	@echo "$(YELLOW)Cleaning Python artifacts...$(NC)"
	@find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BACKEND_DIR)/htmlcov $(BACKEND_DIR)/.coverage
	@echo "$(GREEN)✓ Cleaned$(NC)"

# Hidden checks
.PHONY: check-env check-docker check-venv check-python

check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker not found$(NC)"; exit 1; }

check-python:
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python3 not found$(NC)"; exit 1; }

check-env:
	@if [ ! -f .env ]; then echo "$(RED).env not found. Run 'make setup'$(NC)"; exit 1; fi

check-venv: check-env
	@if [ ! -d "$(VENV)" ]; then echo "$(RED)venv not found. Run 'make setup-backend'$(NC)"; exit 1; fi


