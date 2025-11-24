#!/bin/bash
# ============================================
# M365 License Optimizer - Quick Start Script
# Version LOT4 - Compatible avec init.sql minimaliste
# ============================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
    __  __ _____  __ _____   _     _
   |  \/  |___ / / /_| ____| | |   (_) ___ ___ _ __  ___  ___
   | |\/| | |_ \| '_ \___ \  | |   | |/ __/ _ \ '_ \/ __|/ _ \
   | |  | |___) | (_) |__) | | |___| | (_|  __/ | | \__ \  __/
   |_|  |_|____/ \___/____/  |_____|_|\___\___|_| |_|___/\___|

    ___        _   _           _
   / _ \ _ __ | |_(_)_ __ ___ (_)_______ _ __
  | | | | '_ \| __| | '_ ` _ \| |_  / _ \ '__|
  | |_| | |_) | |_| | | | | | | |/ /  __/ |
   \___/| .__/ \__|_|_| |_| |_|_/___\___|_|
        |_|

Version 1.0 LOT4 - Quick Start Setup
EOF
echo -e "${NC}"

# ============================================
# Prerequisites Check
# ============================================
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    echo "Please install Python 3.11+: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi
echo -e "${GREEN}✓ Python3 found${NC}"

# ============================================
# Directory Structure
# ============================================
echo ""
echo "Creating directory structure..."
mkdir -p docker/db logs backups
echo -e "${GREEN}✓ Directories created${NC}"

# ============================================
# Environment Setup
# ============================================
echo ""
echo "Setting up environment variables..."

if [ -f .env ]; then
    echo -e "${BLUE}ℹ .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ $overwrite =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo "Keeping existing .env file"
    fi
else
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
fi

# ============================================
# Docker Services
# ============================================
echo ""
echo "Starting Docker services..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start Docker services${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Services started${NC}"

# ============================================
# Wait for Services
# ============================================
echo ""
echo "Waiting for services to be ready..."

# Wait for PostgreSQL
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec m365_optimizer_db pg_isready -U admin -d m365_optimizer &> /dev/null; then
        echo -e "${GREEN}PostgreSQL: Ready${NC}"
        break
    fi
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}PostgreSQL: Timeout${NC}"
        exit 1
    fi
    sleep 2
done

# Wait for Redis
if docker exec m365_optimizer_redis redis-cli -a changeme PING &> /dev/null; then
    echo -e "${GREEN}Redis: Ready${NC}"
else
    echo -e "${RED}Redis: Not responding${NC}"
    exit 1
fi

# ============================================
# Backend Setup (LOT4 - AVANT les tests)
# ============================================
echo ""
echo -e "${BLUE}Setting up Python backend...${NC}"

cd backend

# Check if venv exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    echo "Updating dependencies..."
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    if [ ! -f "venv/bin/activate" ]; then
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv and install dependencies
echo "Installing/updating dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend setup complete${NC}"

# ============================================
# Initialize Schema (LOT4)
# ============================================
echo ""
echo -e "${BLUE}Initializing database schema...${NC}"

cd ..

# Check if schema already exists
SCHEMA_EXISTS=$(docker exec m365_optimizer_db psql -U admin -d m365_optimizer -tAc \
    "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='optimizer')")

if [ "$SCHEMA_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ Schema 'optimizer' already exists${NC}"
else
    echo "Creating schema 'optimizer'..."
    docker exec -i m365_optimizer_db psql -U admin -d m365_optimizer < docker/db/init.sql
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to initialize schema${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Schema 'optimizer' created${NC}"
fi

# ============================================
# Apply Migrations (LOT4 - CRITIQUE)
# ============================================
echo ""
echo -e "${BLUE}Applying database migrations...${NC}"

cd backend
source venv/bin/activate

# Check if migrations exist
MIGRATION_COUNT=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)

if [ "$MIGRATION_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ No migrations found${NC}"
    echo -e "${YELLOW}You need to create an initial migration:${NC}"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  alembic revision --autogenerate -m 'LOT4 - Initial schema'"
    echo "  alembic upgrade head"
else
    echo "Applying $MIGRATION_COUNT migration(s)..."
    alembic upgrade head
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Migration failed${NC}"
        echo -e "${YELLOW}Check your database connection and migration files${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Migrations applied successfully${NC}"
fi

cd ..

# ============================================
# Verify Database State
# ============================================
echo ""
echo -e "${BLUE}Verifying database state...${NC}"

# Count tables in optimizer schema
TABLE_COUNT=$(docker exec m365_optimizer_db psql -U admin -d m365_optimizer -tAc \
    "SELECT COUNT(*) FROM pg_tables WHERE schemaname='optimizer'")

echo "Tables in 'optimizer' schema: $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Database schema is ready${NC}"
else
    echo -e "${YELLOW}⚠ No tables found in optimizer schema${NC}"
    echo -e "${YELLOW}This is expected if no migrations have been created yet${NC}"
fi

# ============================================
# Infrastructure Tests (LOT4 - APRÈS migrations)
# ============================================
echo ""
echo "Running infrastructure tests..."
echo ""

if [ -f "scripts/test-infrastructure.sh" ]; then
    chmod +x scripts/test-infrastructure.sh
    ./scripts/test-infrastructure.sh
    TEST_EXIT_CODE=$?
else
    echo -e "${YELLOW}⚠ Infrastructure test script not found${NC}"
    TEST_EXIT_CODE=0
fi

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${GREEN}Services running:${NC}"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo "  • PgAdmin: http://localhost:5050"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Start the API: ${YELLOW}make dev${NC}"
echo "  2. Access docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo "  3. Run tests: ${YELLOW}make test${NC}"
echo ""

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Remember to create your initial migration:${NC}"
    echo "  ${YELLOW}cd backend && source venv/bin/activate${NC}"
    echo "  ${YELLOW}alembic revision --autogenerate -m 'LOT4 - Initial schema'${NC}"
    echo "  ${YELLOW}alembic upgrade head${NC}"
    echo ""
fi

echo -e "${GREEN}View logs: ${YELLOW}make logs${NC}"
echo -e "${GREEN}Stop services: ${YELLOW}make stop${NC}"
echo ""

# Exit with test result code
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${YELLOW}⚠ Some infrastructure tests failed${NC}"
    echo -e "${YELLOW}This may be expected if migrations haven't been created yet${NC}"
fi

exit 0
