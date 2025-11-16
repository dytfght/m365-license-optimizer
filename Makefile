# ============================================
# M365 License Optimizer - Makefile
# ============================================
# Simplifies common development tasks
# ============================================

.PHONY: help setup start stop restart logs clean test status ps shell-db shell-redis backup restore

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Variables
COMPOSE := docker compose
POSTGRES_CONTAINER := m365_optimizer_db
REDIS_CONTAINER := m365_optimizer_redis
BACKUP_DIR := backups

## help: Show this help message
help:
	@echo "$(BLUE)M365 License Optimizer - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make setup          - First time setup (interactive)"
	@echo "  make setup-quick    - Quick setup with defaults"
	@echo ""
	@echo "$(GREEN)Service Management:$(NC)"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make status         - Show service status"
	@echo "  make ps             - List running containers"
	@echo ""
	@echo "$(GREEN)Logs & Monitoring:$(NC)"
	@echo "  make logs           - Show all logs (follow)"
	@echo "  make logs-db        - Show PostgreSQL logs"
	@echo "  make logs-redis     - Show Redis logs"
	@echo ""
	@echo "$(GREEN)Database Operations:$(NC)"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make shell-redis    - Open Redis CLI"
	@echo "  make backup         - Backup PostgreSQL database"
	@echo "  make restore        - Restore PostgreSQL database"
	@echo ""
	@echo "$(GREEN)Testing & Validation:$(NC)"
	@echo "  make test           - Run infrastructure tests"
	@echo "  make test-db        - Test PostgreSQL connection"
	@echo "  make test-redis     - Test Redis connection"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean          - Stop and remove containers"
	@echo "  make clean-all      - Remove containers and volumes"
	@echo "  make clean-data     - Remove all data (dangerous!)"
	@echo ""

## setup: Interactive first-time setup
setup:
	@echo "$(BLUE)Starting interactive setup...$(NC)"
	@chmod +x scripts/quick-start.sh
	@./scripts/quick-start.sh

## setup-quick: Quick setup with default values
setup-quick:
	@echo "$(BLUE)Quick setup...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created. Please edit passwords!$(NC)"; \
	fi
	@$(COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@sleep 5
	@make status

## start: Start all services
start:
	@echo "$(BLUE)Starting services...$(NC)"
	@$(COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@make status

## stop: Stop all services
stop:
	@echo "$(YELLOW)Stopping services...$(NC)"
	@$(COMPOSE) stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart:
	@echo "$(YELLOW)Restarting services...$(NC)"
	@$(COMPOSE) restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

## status: Show service status
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@$(COMPOSE) ps
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

## shell-db: Open PostgreSQL shell
shell-db:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	@echo "$(YELLOW)Tip: Use \\q to exit$(NC)"
	@docker exec -it $(POSTGRES_CONTAINER) psql -U admin -d m365_optimizer

## shell-redis: Open Redis CLI
shell-redis:
	@echo "$(BLUE)Opening Redis CLI...$(NC)"
	@echo "$(YELLOW)Tip: Use 'exit' to quit$(NC)"
	@if [ -f .env ]; then \
		. ./.env && docker exec -it $(REDIS_CONTAINER) redis-cli -a $$REDIS_PASSWORD; \
	else \
		echo "$(RED).env file not found$(NC)"; \
	fi

## test: Run infrastructure tests
test:
	@echo "$(BLUE)Running tests...$(NC)"
	@chmod +x scripts/test-infrastructure.sh
	@./scripts/test-infrastructure.sh

## test-db: Test PostgreSQL connection
test-db:
	@echo "$(BLUE)Testing PostgreSQL connection...$(NC)"
	@docker exec $(POSTGRES_CONTAINER) pg_isready -U admin && \
		echo "$(GREEN)✓ PostgreSQL is ready$(NC)" || \
		echo "$(RED)✗ PostgreSQL is not ready$(NC)"
	@docker exec $(POSTGRES_CONTAINER) psql -U admin -d m365_optimizer -c "SELECT COUNT(*) as tenant_count FROM optimizer.tenant_clients;" 2>/dev/null && \
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

## backup: Backup PostgreSQL database
backup:
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker exec $(POSTGRES_CONTAINER) pg_dump -U admin m365_optimizer > $(BACKUP_DIR)/m365_optimizer_$$TIMESTAMP.sql && \
	echo "$(GREEN)✓ Backup created: $(BACKUP_DIR)/m365_optimizer_$$TIMESTAMP.sql$(NC)" || \
	echo "$(RED)✗ Backup failed$(NC)"

## restore: Restore PostgreSQL database
restore:
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -lh $(BACKUP_DIR)/*.sql 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Enter backup filename: " BACKUP_FILE; \
	if [ -f "$(BACKUP_DIR)/$$BACKUP_FILE" ]; then \
		echo "$(BLUE)Restoring from $$BACKUP_FILE...$(NC)"; \
		docker exec -i $(POSTGRES_CONTAINER) psql -U admin -d m365_optimizer < $(BACKUP_DIR)/$$BACKUP_FILE && \
		echo "$(GREEN)✓ Restore completed$(NC)" || \
		echo "$(RED)✗ Restore failed$(NC)"; \
	else \
		echo "$(RED)Backup file not found$(NC)"; \
	fi

## clean: Stop and remove containers (keeps volumes)
clean:
	@echo "$(YELLOW)Cleaning up containers...$(NC)"
	@$(COMPOSE) down
	@echo "$(GREEN)✓ Containers removed (data preserved)$(NC)"

## clean-all: Remove containers and volumes
clean-all:
	@echo "$(YELLOW)WARNING: This will remove all data!$(NC)"
	@read -p "Are you sure? (y/N): " CONFIRM; \
	if [ "$$CONFIRM" = "y" ] || [ "$$CONFIRM" = "Y" ]; then \
		$(COMPOSE) down -v && \
		echo "$(GREEN)✓ All containers and volumes removed$(NC)"; \
	else \
		echo "$(GREEN)Cancelled$(NC)"; \
	fi

## clean-data: Remove all data (very dangerous!)
clean-data:
	@echo "$(RED)DANGER: This will permanently delete ALL data!$(NC)"
	@echo "$(YELLOW)This includes all databases, Redis cache, and backups!$(NC)"
	@read -p "Type 'DELETE' to confirm: " CONFIRM; \
	if [ "$$CONFIRM" = "DELETE" ]; then \
		$(COMPOSE) down -v --rmi all && \
		rm -rf $(BACKUP_DIR) && \
		echo "$(GREEN)✓ Everything removed$(NC)"; \
	else \
		echo "$(GREEN)Cancelled (nothing deleted)$(NC)"; \
	fi

# Hidden targets (not shown in help)
.PHONY: check-env
check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "$(YELLOW)Run 'make setup' first$(NC)"; \
		exit 1; \
	fi
