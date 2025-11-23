#!/bin/bash

# ============================================
# M365 License Optimizer - Infrastructure Test Script
# ============================================
# This script validates that all infrastructure components
# are properly configured and running
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo "============================================"
    echo "$1"
    echo "============================================"
}

# Function to load environment variables
load_env() {
    if [ -f .env ]; then
        # Méthode robuste pour charger les variables d'environnement
        while IFS='=' read -r key value; do
            # Ignorer les lignes vides et les commentaires
            if [[ -n "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
                # Supprimer les espaces en début/fin
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs)
                
                # Supprimer les guillemets si présents
                value=$(echo "$value" | sed 's/^["'\'']\|["'\'']$//g')
                
                export "$key"="$value"
            fi
        done < .env
        
        print_success "Environment variables loaded"
    else
        print_error ".env file not found"
        exit 1
    fi
}

# Test Docker is running
test_docker() {
    print_header "Testing Docker"
    
    if docker info > /dev/null 2>&1; then
        print_success "Docker is running"
        DOCKER_VERSION=$(docker --version)
        print_info "Version: $DOCKER_VERSION"
    else
        print_error "Docker is not running or not installed"
        return 1
    fi
}

# Test Docker Compose
test_docker_compose() {
    print_header "Testing Docker Compose"
    
    if command -v docker-compose > /dev/null 2>&1; then
        print_success "Docker Compose is available"
        COMPOSE_VERSION=$(docker-compose --version)
        print_info "Version: $COMPOSE_VERSION"
    elif docker compose version > /dev/null 2>&1; then
        print_success "Docker Compose (plugin) is available"
        COMPOSE_VERSION=$(docker compose version)
        print_info "Version: $COMPOSE_VERSION"
    else
        print_error "Docker Compose is not installed"
        return 1
    fi
}

# Test containers are running
test_containers() {
    print_header "Testing Containers Status"
    
    CONTAINERS=("m365_optimizer_db" "m365_optimizer_redis" "m365_optimizer_pgadmin")
    
    for container in "${CONTAINERS[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            STATUS=$(docker inspect --format='{{.State.Status}}' $container)
            if [ "$STATUS" = "running" ]; then
                print_success "Container $container is running"
            else
                print_error "Container $container exists but is not running (status: $STATUS)"
            fi
        else
            print_error "Container $container is not running"
        fi
    done
}

# Test PostgreSQL connection
test_postgresql() {
    print_header "Testing PostgreSQL"
    
    # Vérifier que les variables sont définies
    if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
        print_error "POSTGRES_USER or POSTGRES_DB not defined in environment"
        return 1
    fi
    
    # Wait for PostgreSQL to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec m365_optimizer_db pg_isready -U $POSTGRES_USER > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL did not become ready in time"
            return 1
        fi
        sleep 1
    done
    
    # Test connection
    if docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "PostgreSQL connection successful"
    else
        print_error "PostgreSQL connection failed"
        return 1
    fi
    
    # Test schema exists
    SCHEMA_COUNT=$(docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'optimizer';" 2>/dev/null || echo "0")
    SCHEMA_COUNT=$(echo $SCHEMA_COUNT | tr -d ' ')
    if [ "$SCHEMA_COUNT" = "1" ]; then
        print_success "Schema 'optimizer' exists"
    else
        print_error "Schema 'optimizer' not found"
    fi
    
    # Test tables exist
    TABLE_COUNT=$(docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'optimizer';" 2>/dev/null || echo "0")
    TABLE_COUNT=$(echo $TABLE_COUNT | tr -d ' ')
    if [ "$TABLE_COUNT" -gt 0 ]; then
        print_success "Found $TABLE_COUNT tables in optimizer schema"
    else
        print_error "No tables found in optimizer schema"
    fi
    
    # Test sample data exists
    TENANT_COUNT=$(docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM optimizer.tenant_clients;" 2>/dev/null || echo "0")
    TENANT_COUNT=$(echo $TENANT_COUNT | tr -d ' ')
    if [ "$TENANT_COUNT" -ge 1 ]; then
        print_success "Sample tenant data exists ($TENANT_COUNT tenants)"
    else
        print_error "Sample tenant data not found"
    fi
}

# Test Redis connection
test_redis() {
    print_header "Testing Redis"
    
    # Vérifier que REDIS_PASSWORD est défini
    if [ -z "$REDIS_PASSWORD" ]; then
        print_error "REDIS_PASSWORD not defined in environment"
        return 1
    fi
    
    # Test connection with password
    if docker exec m365_optimizer_redis redis-cli -a $REDIS_PASSWORD PING 2>/dev/null | grep -q "PONG"; then
        print_success "Redis connection successful"
    else
        print_error "Redis connection failed"
        return 1
    fi
    
    # Test maxmemory-policy
    POLICY=$(docker exec m365_optimizer_redis redis-cli -a $REDIS_PASSWORD CONFIG GET maxmemory-policy 2>/dev/null | tail -n 1)
    if [ "$POLICY" = "allkeys-lru" ]; then
        print_success "Redis maxmemory-policy is correctly set to allkeys-lru"
    else
        print_error "Redis maxmemory-policy is $POLICY (expected: allkeys-lru)"
    fi
    
    # Test write/read
    TEST_KEY="test_$(date +%s)"
    docker exec m365_optimizer_redis redis-cli -a $REDIS_PASSWORD SET $TEST_KEY "test_value" > /dev/null 2>&1
    TEST_VALUE=$(docker exec m365_optimizer_redis redis-cli -a $REDIS_PASSWORD GET $TEST_KEY 2>/dev/null)
    if [ "$TEST_VALUE" = "test_value" ]; then
        print_success "Redis write/read test successful"
        docker exec m365_optimizer_redis redis-cli -a $REDIS_PASSWORD DEL $TEST_KEY > /dev/null 2>&1
    else
        print_error "Redis write/read test failed"
    fi
}

# Test data persistence
test_persistence() {
    print_header "Testing Data Persistence"
    
    print_info "Testing PostgreSQL persistence..."
    
    # Insert test data
    TEST_TENANT_ID="persistence-test-$(date +%s)"
    if docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "INSERT INTO optimizer.tenant_clients (id, tenant_id, name, country, default_language, onboarding_status) VALUES (gen_random_uuid(), '$TEST_TENANT_ID', 'Persistence Test', 'FR', 'fr-FR', 'pending') ON CONFLICT (tenant_id) DO NOTHING;" > /dev/null 2>&1; then
        print_success "Test data inserted"
    else
        print_error "Failed to insert test data"
        return 1
    fi
    
    # Verify data exists
    RESULT=$(docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c \
        "SELECT name FROM optimizer.tenant_clients WHERE tenant_id = '$TEST_TENANT_ID';" 2>/dev/null)
    
    if echo "$RESULT" | grep -q "Persistence Test"; then
        print_success "Test data can be retrieved"
    else
        print_error "Test data not found"
        return 1
    fi
    
    # Clean up test data
    docker exec m365_optimizer_db psql -U $POSTGRES_USER -d $POSTGRES_DB -c \
        "DELETE FROM optimizer.tenant_clients WHERE tenant_id = '$TEST_TENANT_ID';" \
        > /dev/null 2>&1
    
    print_info "Note: Full persistence test requires container restart"
    print_info "Run: docker-compose restart && sleep 5 && ./scripts/test-infrastructure.sh"
}

# Test volumes
test_volumes() {
    print_header "Testing Docker Volumes"
    
    VOLUMES=("m365-license-optimizer_postgres_data" "m365-license-optimizer_redis_data")
    
    for volume in "${VOLUMES[@]}"; do
        if docker volume inspect $volume > /dev/null 2>&1; then
            print_success "Volume $volume exists"
            
            # Get volume size
            MOUNTPOINT=$(docker volume inspect $volume --format='{{.Mountpoint}}' 2>/dev/null)
            if [ -n "$MOUNTPOINT" ]; then
                SIZE=$(du -sh "$MOUNTPOINT" 2>/dev/null | cut -f1 || echo "Unknown")
                print_info "Size: $SIZE"
            fi
        else
            print_error "Volume $volume not found"
        fi
    done
}

# Test network
test_network() {
    print_header "Testing Docker Network"
    
    if docker network inspect m365-license-optimizer_m365_network > /dev/null 2>&1; then
        print_success "Network m365_network exists"
        
        # Check connected containers
        CONNECTED=$(docker network inspect m365-license-optimizer_m365_network --format='{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)
        print_info "Connected containers: $CONNECTED"
    else
        print_error "Network m365_network not found"
    fi
}

# Test PgAdmin (optional)
test_pgadmin() {
    print_header "Testing PgAdmin (Optional)"
    
    if docker ps --format '{{.Names}}' | grep -q "^m365_optimizer_pgadmin$"; then
        print_success "PgAdmin container is running"
        print_info "Access at: http://localhost:5050"
        if [ -n "$PGADMIN_EMAIL" ]; then
            print_info "Email: $PGADMIN_EMAIL"
        fi
    else
        print_info "PgAdmin container not running (optional)"
    fi
}

# Print summary
print_summary() {
    print_header "Test Summary"
    
    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
    
    echo "Total tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        print_success "ALL TESTS PASSED! Infrastructure is ready."
        echo ""
        exit 0
    else
        echo ""
        print_error "SOME TESTS FAILED. Please review the output above."
        echo ""
        exit 1
    fi
}

# Main execution
main() {
    echo "============================================"
    echo "M365 License Optimizer - Infrastructure Tests"
    echo "============================================"
    
    load_env
    test_docker
    test_docker_compose
    test_containers
    test_postgresql
    test_redis
    test_volumes
    test_network
    test_persistence
    test_pgadmin
    print_summary
}

# Run main function
main
